"""Cross-check GWT targets against an independent CRISPR screen (Freimer et al. 2022).

`metadata/Freimer2022_Screen.csv` (PMID 36356142, DOI 10.1126/science.abn5647) has been sitting
in this repo since its initial commit, registered in `docs/provenance_registry.csv` with the
stated purpose "T-cell effector screen cross-check" — but no code ever actually performed that
cross-check (confirmed via `git log --all -S` across the full repo history; see
`docs/data_governance_checklist.md` §6). This module makes good on that stated intent.

Freimer et al. 2022 ran three independent FACS-sort CRISPR screens in primary human CD4 T cells,
each reading out a different Treg/IL-2-axis phenotype: IL2RA surface expression, IL2 secretion,
and CTLA4 surface expression. It is a ~1,350-gene subpool screen (not genome-scale) — the CSV
carries `neg|...` (negative-selection / depleted) and `pos|...` (positive-selection / enriched)
MAGeCK-style statistics (`score`, `p-value`, `fdr`, `rank`, `goodsgrna`, `lfc`) per gene per
screen.

This is a genuinely **independent** dataset — different lab, different assay (FACS-sort pooled
screen vs this repo's Perturb-seq), different readout (protein-level phenotype vs transcriptomic
signature) — so a GWT target also showing up as a significant hit here is real orthogonal
support, not a restatement of the same experiment.

Sanity anchors (asserted in the test): the CTLA4 screen's #1 positive-selection hit (by rank) is
CTLA4 itself (FDR 0.000413) — the screen recovers its own eponymous gene, a strong construct-
validity check. MED12 (a broad-effect/essential gene already flagged as such by this repo's own
`sources/broad_effect_genes.txt`) is a strong negative-selection hit across multiple screens here
too — independent corroboration of its non-specific, broadly essential character.

Honesty (repo discipline): descriptive only, never a readiness input. `unknown != 0` — a gene
outside Freimer's ~1,350-gene subpool is genuinely OUT OF SCREEN SCOPE, not "not a hit"; this is
returned as `available: True, hits: []` with an explicit scope note, never conflated with a
tested-and-negative result.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
FREIMER_CSV = _ROOT / "metadata" / "Freimer2022_Screen.csv"

SCREENS = ["IL2RA", "IL2", "CTLA4"]
SIGNIFICANT_FDR = 0.05
NON_TARGETING_ID = "Non-Targeting"

_CACHE: Dict[str, Optional[pd.DataFrame]] = {}
_LOADED = False


def _load() -> Optional[pd.DataFrame]:
    global _LOADED
    if _LOADED:
        return _CACHE.get("df")
    _LOADED = True
    if not FREIMER_CSV.exists():
        _CACHE["df"] = None
        return None
    df = pd.read_csv(FREIMER_CSV, low_memory=False)
    df = df[df["id"] != NON_TARGETING_ID].copy()  # the non-targeting control row is not a gene
    df["id"] = df["id"].astype(str).str.strip().str.upper()
    _CACHE["df"] = df
    return df


def n_genes_in_scope() -> Optional[int]:
    """How many genes Freimer's subpool actually screened (for honest scope disclosure)."""
    df = _load()
    return None if df is None else int(df["id"].nunique())


def freimer2022_crosscheck_for_target(gene: str) -> Dict[str, Any]:
    """Independent CRISPR-screen concordance for ``gene``. Honest empty when out of scope."""
    df = _load()
    if df is None:
        return {
            "gene": gene,
            "available": False,
            "reason": "Freimer2022_Screen.csv not present",
            "hits": [],
        }

    sub = df[df["id"] == str(gene).strip().upper()]
    in_scope = not sub.empty
    hits: List[Dict[str, Any]] = []
    for _, r in sub.iterrows():
        for direction in ("neg", "pos"):
            fdr = r.get(f"{direction}|fdr")
            if pd.isna(fdr):
                continue
            fdr = float(fdr)
            hits.append({
                "screen": r["screen"],
                "direction": "depleted" if direction == "neg" else "enriched",
                "fdr": fdr,
                "rank": None if pd.isna(r.get(f"{direction}|rank")) else int(r[f"{direction}|rank"]),
                "lfc": None if pd.isna(r.get(f"{direction}|lfc")) else float(r[f"{direction}|lfc"]),
                "goodsgrna": None if pd.isna(r.get(f"{direction}|goodsgrna")) else int(r[f"{direction}|goodsgrna"]),
                "significant": fdr < SIGNIFICANT_FDR,
            })
    # deterministic: significant first, then by ascending FDR
    hits.sort(key=lambda h: (not h["significant"], h["fdr"]))
    sig_hits = [h for h in hits if h["significant"]]

    return {
        "gene": gene,
        "available": True,
        "in_screen_scope": in_scope,
        "n_genes_in_scope": n_genes_in_scope(),
        "n_hits": len(hits),
        "n_significant": len(sig_hits),
        "significant_screens": sorted({h["screen"] for h in sig_hits}),
        "note": (
            "Independent CRISPR screen cross-check (Freimer et al. 2022, PMID 36356142) -- a "
            "different lab, assay (FACS-sort pooled screen, not Perturb-seq), and readout "
            "(IL2RA/IL2/CTLA4 protein phenotype, not transcriptomic signature) from this "
            "repo's own screen. significant = FDR < 0.05 in either the depleted (neg) or "
            f"enriched (pos) direction. This is a ~{n_genes_in_scope() or '?'}-gene subpool "
            "screen, not genome-scale: `in_screen_scope=False` means the gene was never "
            "tested here (out of scope), which is NOT the same as a tested-and-negative "
            "result. unknown != 0: absence from `hits` never means a fabricated non-hit. "
            "Descriptive only -- not a readiness input."
        ),
        "hits": hits,
    }


def is_loaded_ok() -> bool:
    return _load() is not None
