"""Single-cell-resolution off-context expression breadth, per gene (HPA).

`metadata/rna_single_cell_type_group.tsv.zip` (Human Protein Atlas, per-gene nCPM across 51
consensus single-cell "Cell type group" categories) sat unused in this repo since its initial
commit -- confirmed via full git-history search, see `docs/data_governance_checklist.md` §6.
Its sibling `rna_tissue_consensus.tsv.zip` (bulk-tissue version) WAS used, by
`src/6_functional_interaction/tissue_specificity.ipynb`, but that notebook never opened the
single-cell-resolution files.

This module surfaces `sources/target_tool_cache/_overlays/hpa_singlecell_breadth_seed.parquet`
(built by `data_acquisition/build_hpa_singlecell_breadth_overlay.py`) per gene: how many
off-context (non-"T-cells") HPA single-cell types express this gene, and the maximum expression
seen among them.

Relationship to the existing GTEx-based `safety_window_from_gtex`: this is an ADDITIONAL,
independent breadth signal at single-CELL-TYPE resolution rather than bulk-TISSUE resolution --
finer-grained for an immunology platform, since a tissue can look narrow in bulk while actually
containing several off-target immune cell populations only single-cell data resolves. It is
deliberately kept STANDALONE, not folded into `composite_safety_liability` (already
calibrated/tested on the two-way gnomAD+GTEx signal -- adding a third correlated breadth axis
without re-deriving the tier thresholds would silently shift every gene's tier).

Sanity anchors (asserted in the test, from the real committed overlay): CD3E's off-context max
is the NK-cells nCPM (137.0) -- its highest-expressing OTHER lymphoid population, since T-cells
itself (nCPM 424.7, its true peak) is excluded as on-context. FOXP3 is narrowly expressed even
off-context (~4.0 nCPM max), consistent with its Treg-restricted biology.

Honesty (repo discipline): descriptive only, never a readiness input. `unknown != 0` -- a gene
absent from the overlay, or the overlay being unavailable, returns `"unknown"`, never a
fabricated 0/narrow reading.
"""

from __future__ import annotations

from typing import Any, Dict

from common.overlay_lookup import UNKNOWN
from evidence.safety_overlay import load_hpa_singlecell_breadth_overlay

ON_CONTEXT_CELL_TYPE = "T-cells"


def hpa_singlecell_breadth_for_target(gene: str) -> Dict[str, Any]:
    """Off-context single-cell expression breadth for ``gene``. Honest unknown when uncovered."""
    overlay = load_hpa_singlecell_breadth_overlay()
    if not overlay.get("available"):
        return {
            "gene": gene,
            "available": False,
            "reason": overlay.get("reason"),
            "n_celltypes_expressed": UNKNOWN,
            "max_expression_outside_tcell_context": UNKNOWN,
        }

    table = overlay["table"]
    row = table[table["gene_symbol"].astype(str).str.upper() == str(gene).strip().upper()]
    if row.empty:
        return {
            "gene": gene,
            "available": True,
            "in_overlay": False,
            "n_celltypes_expressed": UNKNOWN,
            "max_expression_outside_tcell_context": UNKNOWN,
            "note": (
                "Gene absent from the HPA single-cell overlay -- unchecked, never coerced to "
                "narrow/0. Descriptive only, standalone from the existing GTEx-based "
                "safety_window_from_gtex signal -- not a readiness input."
            ),
        }

    r = row.iloc[0]
    return {
        "gene": gene,
        "available": True,
        "in_overlay": True,
        "n_celltypes_expressed": int(r["n_celltypes_expressed"]),
        "max_expression_outside_tcell_context": float(r["max_expression_outside_tcell_context"]),
        "note": (
            f"Count of the 50 non-{ON_CONTEXT_CELL_TYPE!r} HPA single-cell-type categories "
            "where this gene clears the expressed threshold (nCPM > 1.0), and the maximum "
            f"off-context expression among them. {ON_CONTEXT_CELL_TYPE!r} itself is excluded "
            "as this platform's own on-context signal (same philosophy as the GTEx overlay "
            "excluding Blood/Spleen) -- high T-cell expression is normal, expected biology "
            "here, not an off-target risk. Higher breadth/max = plausibly narrower safety "
            "window under systemic inhibition. Standalone signal, not folded into "
            "composite_safety_liability. Descriptive only -- not a readiness input."
        ),
    }
