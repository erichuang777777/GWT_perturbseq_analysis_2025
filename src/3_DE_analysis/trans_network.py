"""Trans-effect breadth / regulatory-hub scoring (development plan P1-H).

How many downstream genes does knocking a target down significantly move? That
count — the target's out-degree in the KD -> DEG trans-regulatory graph — is a
dual-use signal:

* high breadth = a **master-regulator** importance signal (a hub), AND
* high breadth = a **broad-effect safety** signal (knocking it down perturbs a
  large slice of the transcriptome — the same intuition behind the readiness
  engine's static ``broad_effect`` red flag).

This is the interactive, per-target version of the hub concentration the #234
"HumanCD4CoDEGNet" project reported (a small top slice of regulators driving most
trans-effect). We recompute it directly from the in-repo signed DE table
(``full_signed_DE``), which carries per-downstream-gene edges the aggregate card
substrate (``n_total_de_genes``) only summarizes as a count.

Method (descriptive, re-derivable, NEVER feeds a readiness call)
---------------------------------------------------------------
* An edge ``target -> downstream_gene`` counts when its ``adj_p_value <=`` the
  significance cut (``full_signed_DE`` is itself pre-filtered to ``adj_p_value
  <= 0.1``; we tighten to ``0.05`` by default).
* ``trans_effect_breadth`` = number of DISTINCT significant downstream genes
  across all conditions (the union out-degree). Per-condition counts travel too.
* ``breadth_percentile`` = the target's rank of ``trans_effect_breadth`` within
  the whole screened cohort, in [0, 1].
* Cohort concentration (``concentration_summary``) reports the Gini coefficient
  and the share of all trans-edges driven by the top 5% of targets — the honest,
  reproducible form of the "hubs dominate" observation.

Honesty constraints (this repo's discipline)
--------------------------------------------
* ``unknown != 0``: a target with no significant downstream edge in the table is
  ABSENT from the overlay, never a fabricated breadth-0 row.
* This breadth is computed from ``full_signed_DE`` at a stated padj cut and is
  DISTINCT from the card's ``n_total_de_genes`` (different table / threshold) —
  the two are not interchangeable and we never overwrite the card column.
* ``broad_effect_candidate`` is a DESCRIPTIVE high-breadth flag. It is NOT the
  readiness engine's ``broad_effect`` red flag and does not cap any readiness
  call. Wiring breadth into that red flag is an explicit, separate, versioned
  decision (see docs/portal_feature_adoption_plan.md §8).
* Deterministic; never mutates cards; never imported by ``core/readiness.py``.
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
SIGNED_DE_GLOB = str(_ROOT / "metadata" / "suppl_tables" / "full_signed_DE" / "*.parquet")
DEFAULT_OUTPUT = _ROOT / "sources" / "target_tool_cache" / "_overlays" / "trans_network_breadth.parquet"

DEFAULT_MAX_PADJ = 0.05
# A target at or above this breadth percentile is flagged a broad-effect CANDIDATE
# (descriptive only — NOT the readiness red flag). Documented + re-derivable.
BROAD_EFFECT_PERCENTILE = 0.95

_CONDITION_ORDER = {"Rest": 0, "Stim8hr": 1, "Stim48hr": 2}


def _gini(values: np.ndarray) -> float:
    """Gini coefficient of a non-negative 1-D array (0 = equal, ->1 = concentrated)."""
    v = np.sort(np.asarray(values, dtype=float))
    n = v.size
    if n == 0 or v.sum() == 0:
        return float("nan")
    idx = np.arange(1, n + 1)
    return float((2.0 * (idx * v).sum()) / (n * v.sum()) - (n + 1.0) / n)


def compute_breadth(signed_de: pd.DataFrame, *, max_padj: float = DEFAULT_MAX_PADJ) -> pd.DataFrame:
    """Per-target trans-effect breadth from the signed DE table.

    Returns one row per target with >= 1 significant downstream edge (never a
    fabricated 0-breadth row). Columns: ``target_gene, trans_effect_breadth,
    n_edges_total, breadth_rest, breadth_stim8hr, breadth_stim48hr,
    breadth_percentile, broad_effect_candidate``.
    """
    cols = [
        "target_gene", "trans_effect_breadth", "n_edges_total",
        "breadth_rest", "breadth_stim8hr", "breadth_stim48hr",
        "breadth_percentile", "broad_effect_candidate",
    ]
    if signed_de.empty:
        return pd.DataFrame(columns=cols)
    sd = signed_de.copy()
    sd = sd[pd.to_numeric(sd["adj_p_value"], errors="coerce") <= max_padj]
    if sd.empty:
        return pd.DataFrame(columns=cols)

    # union out-degree = distinct downstream genes moved across all conditions
    union = sd.groupby("target_gene")["downstream_gene"].nunique().rename("trans_effect_breadth")
    n_edges = sd.groupby("target_gene").size().rename("n_edges_total")

    # per-condition distinct downstream counts, pivoted to columns
    per_cond = (
        sd.groupby(["target_gene", "culture_condition"])["downstream_gene"].nunique().unstack(fill_value=0)
    )
    out = pd.concat([union, n_edges], axis=1).reset_index()
    for cond, col in (("Rest", "breadth_rest"), ("Stim8hr", "breadth_stim8hr"), ("Stim48hr", "breadth_stim48hr")):
        out[col] = out["target_gene"].map(per_cond[cond]) if cond in per_cond.columns else 0
        out[col] = out[col].fillna(0).astype(int)

    out["breadth_percentile"] = out["trans_effect_breadth"].rank(pct=True, method="average").round(4)
    out["broad_effect_candidate"] = out["breadth_percentile"] >= BROAD_EFFECT_PERCENTILE
    out = out.sort_values(["trans_effect_breadth", "target_gene"], ascending=[False, True], kind="mergesort")
    return out[cols].reset_index(drop=True)


def build(output: Path = DEFAULT_OUTPUT, *, max_padj: float = DEFAULT_MAX_PADJ) -> pd.DataFrame:
    parts = sorted(glob.glob(SIGNED_DE_GLOB))
    if not parts:
        raise FileNotFoundError(f"no signed-DE parquet parts found at {SIGNED_DE_GLOB}")
    signed_de = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    result = compute_breadth(signed_de, max_padj=max_padj)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(output, index=False)
    return result


# ----------------------------- serving helpers ----------------------------- #
_CACHE: Dict[str, pd.DataFrame] = {}


def load_breadth(path: Path = DEFAULT_OUTPUT) -> Optional[pd.DataFrame]:
    """Load the precomputed overlay (cached). Returns None if not built."""
    key = str(path)
    if key not in _CACHE:
        if not Path(path).exists():
            return None
        _CACHE[key] = pd.read_parquet(path)
    return _CACHE[key]


def breadth_for_target(gene: str, path: Path = DEFAULT_OUTPUT) -> Dict[str, Any]:
    """Per-target breadth for the API. Honest empty when unknown."""
    df = load_breadth(path)
    if df is None:
        return {"gene": gene, "available": False, "reason": "trans_network_breadth overlay not built"}
    sub = df[df["target_gene"].astype(str).str.upper() == str(gene).strip().upper()]
    if sub.empty:
        # unknown != 0: no significant downstream edge measured for this target.
        return {"gene": str(gene).strip().upper(), "available": True, "measured": False,
                "note": "no significant downstream trans-edge measured (unknown != 0, not breadth 0)"}
    r = sub.iloc[0]
    return {
        "gene": str(gene).strip().upper(),
        "available": True,
        "measured": True,
        "trans_effect_breadth": int(r["trans_effect_breadth"]),
        "n_edges_total": int(r["n_edges_total"]),
        "by_condition": {
            "Rest": int(r["breadth_rest"]),
            "Stim8hr": int(r["breadth_stim8hr"]),
            "Stim48hr": int(r["breadth_stim48hr"]),
        },
        "breadth_percentile": float(r["breadth_percentile"]),
        "broad_effect_candidate": bool(r["broad_effect_candidate"]),
        "interpretation": (
            "High breadth is dual-use: a master-regulator importance signal AND a broad-effect "
            "safety signal. Descriptive only — this does NOT set the readiness broad_effect red flag."
        ),
    }


_SIGNED_CACHE: Dict[str, pd.DataFrame] = {}


def _load_signed_de(glob_pattern: str = SIGNED_DE_GLOB) -> Optional[pd.DataFrame]:
    key = glob_pattern
    if key not in _SIGNED_CACHE:
        parts = sorted(glob.glob(glob_pattern))
        if not parts:
            return None
        _SIGNED_CACHE[key] = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    return _SIGNED_CACHE[key]


def neighborhood_for_target(
    gene: str,
    *,
    top_n: int = 12,
    condition: Optional[str] = None,
    max_padj: float = DEFAULT_MAX_PADJ,
    glob_pattern: str = SIGNED_DE_GLOB,
) -> Dict[str, Any]:
    """Top-N signed downstream edges of a target's knockdown, for an ego-network view.

    Returns the strongest (by |log_fc|) significant ``target -> downstream_gene``
    edges with sign, so a consumer can draw the "what does knocking this down
    move?" neighborhood (plan P3-I). Honest empty when the signed table is absent
    or the target has no significant edge (``unknown != 0``, never fabricated).
    """
    signed_de = _load_signed_de(glob_pattern)
    if signed_de is None:
        return {"gene": gene, "available": False, "reason": "full_signed_DE table not present", "edges": []}
    sub = signed_de[signed_de["target_gene"].astype(str).str.upper() == str(gene).strip().upper()].copy()
    sub = sub[pd.to_numeric(sub["adj_p_value"], errors="coerce") <= max_padj]
    if condition:
        sub = sub[sub["culture_condition"] == condition]
    if sub.empty:
        return {"gene": str(gene).strip().upper(), "available": True, "measured": False, "edges": [],
                "note": "no significant downstream edge measured (unknown != 0, not empty-because-zero)"}
    # de-dup a downstream gene to its strongest-|log_fc| condition, then take top-N
    sub["_abs"] = pd.to_numeric(sub["log_fc"], errors="coerce").abs()
    sub = sub.sort_values("_abs", ascending=False).drop_duplicates(subset=["downstream_gene"])
    top = sub.head(int(top_n))
    edges = [
        {
            "downstream_gene": r["downstream_gene"],
            "condition": r["culture_condition"],
            "log_fc": round(float(r["log_fc"]), 4),
            "direction": "up" if float(r["log_fc"]) > 0 else "down",
        }
        for _, r in top.iterrows()
    ]
    return {
        "gene": str(gene).strip().upper(),
        "available": True,
        "measured": True,
        "n_edges_shown": len(edges),
        "total_significant_downstream": int(sub.shape[0]),
        "direction_convention": "log_fc is the effect of KNOCKING THE TARGET DOWN; up = downstream gene rises on knockdown.",
        "edges": edges,
    }


def all_neighborhoods(
    *,
    top_n: int = 12,
    max_padj: float = DEFAULT_MAX_PADJ,
    glob_pattern: str = SIGNED_DE_GLOB,
) -> Dict[str, list]:
    """Precompute every target's top-N signed downstream edges in one pass.

    Efficient batch form for the static export (a single groupby, not one filter
    per gene). Returns ``{GENE: [edge, ...]}`` for targets with >= 1 significant
    edge; absent targets simply aren't keys (``unknown != 0``). Empty dict when
    the signed table isn't present.
    """
    signed_de = _load_signed_de(glob_pattern)
    if signed_de is None:
        return {}
    df = signed_de.copy()
    df = df[pd.to_numeric(df["adj_p_value"], errors="coerce") <= max_padj]
    if df.empty:
        return {}
    df["target_gene"] = df["target_gene"].astype(str).str.upper()
    df["_abs"] = pd.to_numeric(df["log_fc"], errors="coerce").abs()
    # strongest condition per (target, downstream), then top-N per target
    df = df.sort_values("_abs", ascending=False).drop_duplicates(subset=["target_gene", "downstream_gene"])
    out: Dict[str, list] = {}
    for gene, grp in df.groupby("target_gene", sort=False):
        top = grp.head(int(top_n))
        out[gene] = [
            {
                "downstream_gene": r["downstream_gene"],
                "condition": r["culture_condition"],
                "log_fc": round(float(r["log_fc"]), 4),
                "direction": "up" if float(r["log_fc"]) > 0 else "down",
            }
            for _, r in top.iterrows()
        ]
    return out


def concentration_summary(path: Path = DEFAULT_OUTPUT) -> Dict[str, Any]:
    """Cohort-level hub concentration (Gini + top-5% edge share). Honest empty when unbuilt."""
    df = load_breadth(path)
    if df is None:
        return {"available": False, "reason": "trans_network_breadth overlay not built"}
    edges = df["n_edges_total"].to_numpy()
    order = np.sort(edges)[::-1]
    k = max(1, int(np.ceil(len(order) * 0.05)))
    top5_share = float(order[:k].sum() / order.sum()) if order.sum() else float("nan")
    return {
        "available": True,
        "n_targets": int(df.shape[0]),
        "gini_trans_effect": round(_gini(edges), 4),
        "top5pct_edge_share": round(top5_share, 4),
        "note": "Hub concentration over the KD->DEG trans-graph, recomputed from full_signed_DE (descriptive).",
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Build the trans-effect breadth overlay from full_signed_DE.")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument("--max-padj", type=float, default=DEFAULT_MAX_PADJ)
    args = ap.parse_args(argv)
    result = build(args.output, max_padj=args.max_padj)
    summ = concentration_summary(args.output)
    print(f"wrote {len(result):,} targets -> {args.output}")
    print(f"  Gini={summ['gini_trans_effect']}  top-5% edge share={summ['top5pct_edge_share']}")
    print("  top hubs:")
    for _, r in result.head(8).iterrows():
        print(f"    {r['target_gene']:>12}  breadth={int(r['trans_effect_breadth']):>4}  pct={r['breadth_percentile']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
