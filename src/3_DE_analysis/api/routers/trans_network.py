"""Trans-effect breadth / hub endpoints (development plan P1-H).

Descriptive-only. Serves the precomputed ``trans_network_breadth`` overlay (built
from the in-repo signed DE table ``full_signed_DE``): how many downstream genes a
target's knockdown significantly moves (its out-degree in the KD -> DEG graph), a
dual-use master-regulator/broad-effect signal. See ``trans_network.py`` for method
and honesty constraints (``unknown != 0``; NOT the readiness ``broad_effect`` red
flag; distinct from the card's ``n_total_de_genes``).
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

import trans_network

router = APIRouter(tags=["Trans-effect breadth (research use)"])


@router.get(
    "/api/trans_network/summary",
    summary="Cohort hub concentration over the KD->DEG trans-graph (descriptive)",
)
def get_concentration_summary() -> Dict[str, Any]:
    """Gini coefficient + top-5% edge share of the trans-regulatory graph.

    The honest, reproducible form of "a small slice of regulators drives most of the
    trans-effect". Descriptive only. Honest ``available: false`` when the overlay
    hasn't been built.
    """
    return trans_network.concentration_summary()


@router.get(
    "/api/trans_network/{gene}",
    summary="Per-target trans-effect breadth / hub score (descriptive)",
)
def get_breadth_for_target(gene: str) -> Dict[str, Any]:
    """How many downstream genes does knocking this target down significantly move?

    Union out-degree across conditions + per-condition counts + cohort percentile,
    recomputed from ``full_signed_DE``. `unknown != 0`: a target with no significant
    downstream edge returns ``measured: false``, never breadth 0. High breadth is
    dual-use (importance AND broad-effect risk) but is NOT the readiness red flag —
    descriptive only.
    """
    return trans_network.breadth_for_target(gene)
