"""Endpoint surfacing single-cell-resolution off-context expression breadth, per gene.

Descriptive-only, standalone from the existing GTEx-based safety_window signal. See
`hpa_singlecell_breadth.py` for provenance and honesty constraints (`unknown != 0`).
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

import hpa_singlecell_breadth

router = APIRouter(tags=["Concept profile (demo)"])


@router.get(
    "/api/hpa_singlecell_breadth/{gene}",
    summary="Single-cell-resolution off-context expression breadth for this gene (HPA, descriptive)",
)
def get_hpa_singlecell_breadth(gene: str) -> Dict[str, Any]:
    """How broadly is this gene expressed outside T-cell context, at single-cell-type resolution?

    Surfaces the Human Protein Atlas single-cell consensus atlas (51 cell-type categories) for
    this gene: `n_celltypes_expressed` (off-context categories clearing nCPM > 1.0) and
    `max_expression_outside_tcell_context`. `T-cells` itself is excluded as this platform's own
    on-context signal (same philosophy as the existing GTEx overlay excluding Blood/Spleen).

    This is an ADDITIONAL, independent breadth signal alongside the existing GTEx-based
    `safety_window_score` — finer-grained (single cell type vs bulk tissue) but deliberately
    NOT folded into `composite_safety_liability`, which stays on its calibrated two-way
    gnomAD+GTEx composite. `unknown != 0`: a gene absent from the overlay is unchecked, never
    coerced to narrow/0. Descriptive only — not a readiness input.
    """
    return hpa_singlecell_breadth.hpa_singlecell_breadth_for_target(gene)
