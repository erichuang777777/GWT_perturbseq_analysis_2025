"""Disease-signature reversal scoring — does knocking a target down push cells
AWAY from a disease state? (Development plan P0-K, the proposed system core.)

This is a direct generalization of ``signed_module_effect.py``. That module asks
"does knocking a target down activate or repress a curated *concept module*'s
program?" using the signed ``full_signed_DE`` table. Here we swap the fixed
concept-module seed genes for an **arbitrary disease signature** — a set of genes
that go UP and a set that go DOWN in the disease/contrast the user cares about
(responder vs non-responder, disease vs healthy, aged vs young, …) — and ask the
directional question that matters for a therapeutic hypothesis:

    Does knocking this target down move the disease-UP genes DOWN and the
    disease-DOWN genes UP (i.e. REVERSE the disease signature), or the opposite
    (WORSEN it)?

Method (descriptive, re-derivable, NEVER feeds a readiness call)
---------------------------------------------------------------
* A signature is ``{"up": {genes...}, "down": {genes...}}`` (build one from a DE
  table with ``signature_from_de_table``).
* ``full_signed_DE`` gives, per ``target × condition × downstream_gene``, the
  signed ``log_fc`` — the effect of **knocking the target down** (CRISPRi).
* For each signature gene hit downstream, its reversal contribution is
  ``-sign(disease_direction) * kd_log_fc``:
    - disease-UP gene driven DOWN on knockdown (kd_log_fc < 0)  -> +contribution (reverses)
    - disease-DOWN gene driven UP on knockdown (kd_log_fc > 0)  -> +contribution (reverses)
    - the opposite signs -> negative contribution (worsens)
  ``reversal_score`` is the mean contribution over the signature genes actually
  measured downstream of this perturbation.
* ``direction``: ``reverses_disease`` / ``worsens_disease`` / ``neutral`` using the
  same ``|.| >= 0.5`` band ``signed_module_effect`` uses for activator/repressor.

Honesty constraints (this repo's discipline — identical to signed_module_effect)
--------------------------------------------------------------------------------
* ``unknown != 0``: a ``target × condition`` with **no measured signature gene
  downstream** is simply ABSENT from the output — never a fabricated 0.
* ``n_signature_hit`` / ``n_signature_total`` travel with every score, so a
  1-gene mean is never mistaken for a well-supported one.
* Deterministic; never mutates cards; **never read by ``core/readiness.py`` or
  ``_stage()``** — this is a descriptive ranking axis, not a decision input.
* CRISPRi knockdown != pharmacologic inhibition, and a signature defined in a
  different cell context carries a context-mismatch caveat (surfaced in the API
  payload). A positive reversal score is a *hypothesis*, not a therapeutic claim.
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

import numpy as np
import pandas as pd

# repo root = two levels up from this file (src/3_DE_analysis/disease_reversal.py)
_ROOT = Path(__file__).resolve().parent.parent.parent
SIGNED_DE_GLOB = str(_ROOT / "metadata" / "suppl_tables" / "full_signed_DE" / "*.parquet")

# |reversal_score| below this is reported but called "neutral" rather than a
# confident reverses/worsens call. Same band as signed_module_effect's
# DIRECTION_MIN_ABS_LOGFC — documented, re-derivable, descriptive only.
DIRECTION_MIN_ABS_SCORE = 0.5

# Builtin disease/contrast signatures shipped in-repo (ROADMAP flagged these
# signature DE tables as present-but-unsurfaced). Each entry says how to read a
# signature out of its DE table. `gene_col` may be a symbol column or an ensembl
# id column that has a sibling `name_col` with the symbol.
_SUPPL = _ROOT / "metadata" / "suppl_tables"
BUILTIN_SIGNATURES: Dict[str, Dict[str, Any]] = {
    "th2_vs_th1_polarization": {
        "label": "Th2 vs Th1 polarization (Ota 2021)",
        "csv": _SUPPL / "Th2_Th1_polarization_signature_DE_results_full.suppl_table.csv",
        "gene_col": "variable",
        "lfc_col": "log_fc",
        "padj_col": "adj_p_value",
        # Large, well-powered contrast — a |log_fc| stringency filter is meaningful.
        "min_abs_lfc": 1.0,
    },
    "cd4t_aging": {
        "label": "CD4 T-cell aging (Yazar 2022 discovery)",
        "csv": _SUPPL / "CD4T_aging_signature_DE_results_full.suppl_table.csv",
        "gene_col": "gene_name",
        "lfc_col": "log_fc",
        "padj_col": "adj_p_value",
        # Aging effect sizes are small (99th pct |log_fc| ~= 0.13); a |log_fc| >= 1
        # filter would empty the signature. Select on significance + sign instead.
        "min_abs_lfc": 0.0,
    },
}

_CONDITION_ORDER = {"Rest": 0, "Stim8hr": 1, "Stim48hr": 2}


def _norm(gene: str) -> str:
    return str(gene).strip().upper()


def signature_from_de_table(
    df: pd.DataFrame,
    *,
    gene_col: str,
    lfc_col: str = "log_fc",
    padj_col: Optional[str] = "adj_p_value",
    min_abs_lfc: float = 1.0,
    max_padj: float = 0.05,
) -> Dict[str, Set[str]]:
    """Derive an ``{"up", "down"}`` disease signature from a DE table.

    A gene is UP if its ``lfc_col`` is >= ``min_abs_lfc`` (and, when ``padj_col``
    is given, passes ``max_padj``), DOWN if <= ``-min_abs_lfc``. Genes failing the
    thresholds are simply excluded — never forced into a side.
    """
    sub = df[[gene_col, lfc_col] + ([padj_col] if padj_col and padj_col in df.columns else [])].copy()
    sub = sub.dropna(subset=[gene_col, lfc_col])
    if padj_col and padj_col in sub.columns:
        sub = sub[pd.to_numeric(sub[padj_col], errors="coerce") <= max_padj]
    lfc = pd.to_numeric(sub[lfc_col], errors="coerce")
    up = {_norm(g) for g in sub.loc[lfc >= min_abs_lfc, gene_col]}
    down = {_norm(g) for g in sub.loc[lfc <= -min_abs_lfc, gene_col]}
    # A gene can't be both; if a table somehow lists a gene twice with opposite
    # signs, drop it from both sides rather than pick arbitrarily.
    both = up & down
    return {"up": up - both, "down": down - both}


def load_builtin_signature(signature_id: str, **thresholds: Any) -> Dict[str, Set[str]]:
    """Load one of ``BUILTIN_SIGNATURES`` as an ``{"up","down"}`` gene-set dict."""
    if signature_id not in BUILTIN_SIGNATURES:
        raise KeyError(f"unknown builtin signature {signature_id!r}; have {sorted(BUILTIN_SIGNATURES)}")
    spec = BUILTIN_SIGNATURES[signature_id]
    df = pd.read_csv(spec["csv"])
    gene_col = spec.get("gene_col", "variable")
    if gene_col not in df.columns:  # fall back to the plain variable column
        gene_col = "variable"
    kwargs = {"min_abs_lfc": spec.get("min_abs_lfc", 1.0)}
    kwargs.update(thresholds)  # explicit caller override wins
    return signature_from_de_table(
        df, gene_col=gene_col, lfc_col=spec.get("lfc_col", "log_fc"),
        padj_col=spec.get("padj_col", "adj_p_value"), **kwargs,
    )


def _signature_frame(signature: Dict[str, Iterable[str]]) -> pd.DataFrame:
    """Long frame: one row per signature gene with its disease ``direction`` (+1 up / -1 down)."""
    rows = []
    for g in signature.get("up", ()):  # disease-UP genes
        rows.append((_norm(g), 1))
    for g in signature.get("down", ()):  # disease-DOWN genes
        rows.append((_norm(g), -1))
    sig = pd.DataFrame(rows, columns=["downstream_gene", "disease_direction"])
    return sig.drop_duplicates(subset=["downstream_gene"])


def _direction(score: float) -> str:
    if pd.isna(score):
        return "unknown"
    if score >= DIRECTION_MIN_ABS_SCORE:
        return "reverses_disease"
    if score <= -DIRECTION_MIN_ABS_SCORE:
        return "worsens_disease"
    return "neutral"


def compute_reversal(signed_de: pd.DataFrame, signature: Dict[str, Iterable[str]]) -> pd.DataFrame:
    """Signed reversal effect of each perturbation on a disease signature.

    Returns one row per ``target × condition`` that has >= 1 measured signature
    gene downstream (never a fabricated 0-hit row). Columns:
    ``target_gene, culture_condition, n_signature_hit, n_signature_total,
    n_up_hit, n_down_hit, reversal_score, direction``.
    """
    cols = [
        "target_gene", "culture_condition", "n_signature_hit", "n_signature_total",
        "n_up_hit", "n_down_hit", "reversal_score", "direction",
    ]
    sig = _signature_frame(signature)
    n_total = int(sig.shape[0])
    if sig.empty or signed_de.empty:
        return pd.DataFrame(columns=cols)

    sd = signed_de.copy()
    sd["downstream_gene"] = sd["downstream_gene"].map(_norm)
    joined = sd.merge(sig, on="downstream_gene", how="inner")
    if joined.empty:
        return pd.DataFrame(columns=cols)

    # Per-hit reversal contribution: -sign(disease_direction) * kd_log_fc.
    joined["_contrib"] = -joined["disease_direction"] * pd.to_numeric(joined["log_fc"], errors="coerce")
    joined["_is_up"] = joined["disease_direction"] == 1

    agg = (
        joined.groupby(["target_gene", "culture_condition"], as_index=False)
        .agg(
            n_signature_hit=("_contrib", "size"),
            reversal_score=("_contrib", "mean"),
            n_up_hit=("_is_up", "sum"),
        )
    )
    agg["n_down_hit"] = agg["n_signature_hit"] - agg["n_up_hit"]
    agg["n_signature_total"] = n_total
    agg["reversal_score"] = agg["reversal_score"].astype(float).round(4)
    agg["direction"] = agg["reversal_score"].map(_direction)

    agg["_cond"] = agg["culture_condition"].map(_CONDITION_ORDER).fillna(9)
    agg = agg.sort_values(["reversal_score", "target_gene"], ascending=[False, True], kind="mergesort")
    agg = agg.drop(columns="_cond").reset_index(drop=True)
    return agg[cols].astype({"n_up_hit": int, "n_down_hit": int})


# ----------------------------- serving helpers ----------------------------- #
_SIGNED_CACHE: Dict[str, pd.DataFrame] = {}


def load_signed_de(glob_pattern: str = SIGNED_DE_GLOB) -> Optional[pd.DataFrame]:
    """Load (and cache) the full signed-DE table. Returns None if not present."""
    key = glob_pattern
    if key not in _SIGNED_CACHE:
        parts = sorted(glob.glob(glob_pattern))
        if not parts:
            return None
        _SIGNED_CACHE[key] = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    return _SIGNED_CACHE[key]


_CONTEXT_CAVEAT = (
    "CRISPRi knockdown != pharmacologic inhibition; a positive reversal score is a "
    "hypothesis, not a therapeutic claim. If the signature was defined in a cell "
    "context other than primary CD4 T cells, treat hits as context-mismatched. "
    "unknown != 0: target/condition pairs with no measured signature gene are absent, not zero."
)


def rank_reversal(
    signature: Dict[str, Iterable[str]],
    *,
    condition: Optional[str] = None,
    top: Optional[int] = None,
    min_hits: int = 3,
    glob_pattern: str = SIGNED_DE_GLOB,
    signed_de: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Rank all perturbations by disease-reversal for a signature. Honest empty when unavailable.

    ``min_hits`` drops rows whose score rests on fewer than that many measured
    signature genes BEFORE ranking — otherwise the head is dominated by 1-gene
    flukes. The applied value and how many rows it removed are reported in the
    payload (``min_hits`` / ``n_below_min_hits``), never silently hidden.

    ``signed_de`` lets a caller pass a ready table (e.g. a user's uploaded signed
    DE) directly, bypassing the in-repo file — the "run reversal on your own
    screen" path.
    """
    if signed_de is None:
        signed_de = load_signed_de(glob_pattern)
    if signed_de is None:
        return {"available": False, "reason": "full_signed_DE table not present", "results": []}
    if condition:
        signed_de = signed_de[signed_de["culture_condition"] == condition]
    result = compute_reversal(signed_de, signature)
    n_all = int(result.shape[0])
    result = result[result["n_signature_hit"] >= int(min_hits)]
    n_below = n_all - int(result.shape[0])
    if top is not None:
        result = result.head(int(top))
    return {
        "available": True,
        "n_signature_total": int(_signature_frame(signature).shape[0]),
        "condition": condition or "all",
        "min_hits": int(min_hits),
        "n_below_min_hits": n_below,
        "direction_convention": (
            "reversal_score > 0 => knockdown REVERSES the disease signature "
            "(drives disease-up genes down / disease-down genes up); < 0 => WORSENS it."
        ),
        "caveat": _CONTEXT_CAVEAT,
        "results": result.to_dict(orient="records"),
    }


def reversal_for_target(
    gene: str,
    signature: Dict[str, Iterable[str]],
    *,
    glob_pattern: str = SIGNED_DE_GLOB,
) -> Dict[str, Any]:
    """Per-target reversal profile (all conditions) for the API. Honest empty when unknown."""
    signed_de = load_signed_de(glob_pattern)
    if signed_de is None:
        return {"gene": gene, "available": False, "reason": "full_signed_DE table not present", "conditions": []}
    sub = signed_de[signed_de["target_gene"].map(_norm) == _norm(gene)]
    result = compute_reversal(sub, signature)
    return {
        "gene": _norm(gene),
        "available": True,
        "n_signature_total": int(_signature_frame(signature).shape[0]),
        "n_condition_hits": int(result.shape[0]),
        "direction_convention": (
            "reversal_score > 0 => knockdown REVERSES the disease signature; < 0 => WORSENS it."
        ),
        "caveat": _CONTEXT_CAVEAT,
        "conditions": result.to_dict(orient="records"),
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Rank perturbations by disease-signature reversal.")
    ap.add_argument("--signature", default="th2_vs_th1_polarization", help="a BUILTIN_SIGNATURES id")
    ap.add_argument("--condition", default=None)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--min-hits", type=int, default=3)
    args = ap.parse_args(argv)

    sig = load_builtin_signature(args.signature)
    out = rank_reversal(sig, condition=args.condition, top=args.top, min_hits=args.min_hits)
    if not out["available"]:
        print(out["reason"])
        return 1
    print(f"signature={args.signature} up={len(sig['up'])} down={len(sig['down'])} condition={out['condition']} "
          f"(min_hits={out['min_hits']}, dropped {out['n_below_min_hits']} low-support rows)")
    for r in out["results"]:
        print(f"  {r['target_gene']:>12}  {r['culture_condition']:>8}  score={r['reversal_score']:+.3f}  "
              f"{r['direction']:>16}  (hits {r['n_signature_hit']}/{r['n_signature_total']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
