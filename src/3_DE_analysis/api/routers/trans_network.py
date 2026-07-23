"""Trans-effect breadth / hub endpoints (development plan P1-H).

Descriptive-only. Serves the precomputed ``trans_network_breadth`` overlay (built
from the in-repo signed DE table ``full_signed_DE``): how many downstream genes a
target's knockdown significantly moves (its out-degree in the KD -> DEG graph), a
dual-use master-regulator/broad-effect signal. See ``trans_network.py`` for method
and honesty constraints (``unknown != 0``; NOT the readiness ``broad_effect`` red
flag; distinct from the card's ``n_total_de_genes``).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

import trans_network

router = APIRouter(tags=["Trans-effect breadth (research use)"])


@router.get(
    "/api/trans_network/{gene}/neighborhood",
    summary="Top-N signed downstream edges of a target's knockdown (ego-network, descriptive)",
)
def get_neighborhood(
    gene: str,
    top_n: int = Query(default=12, ge=1, le=100),
    condition: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    """The strongest downstream genes a knockdown moves, with sign — the data for
    an ego-network "what does knocking this down touch?" view (plan P3-I).

    `unknown != 0`: a target with no significant downstream edge returns
    ``measured: false``, never a fabricated empty-because-zero. Descriptive only.
    """
    return trans_network.neighborhood_for_target(gene, top_n=top_n, condition=condition)


@router.get(
    "/api/trans_network/from_upload/{import_id}",
    summary="Trans-effect breadth on a user-uploaded screen (bring-your-own-data)",
)
def get_breadth_from_upload(import_id: str, gene: Optional[str] = Query(default=None)) -> Dict[str, Any]:
    """Compute trans-effect breadth + hub concentration from a user's OWN signed-DE
    upload (a signed_de_evidence import) — the P1 "accept any perturb-seq dataset"
    path. Pass ``gene`` for a single target's breadth row. Descriptive; unknown != 0."""
    from api import deps
    from signed_de_io import read_signed_de_table
    from upload.import_manager import read_import

    try:
        meta = read_import(deps.CACHE_ROOT, import_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"import_id not found: {import_id}")
    if meta.get("source_type") != "signed_de_evidence":
        raise HTTPException(status_code=400, detail=f"import {import_id} is {meta.get('source_type')}, not signed_de_evidence")
    source_path = Path(meta["source_path"])
    deps._assert_allowed_input_path(source_path)
    try:
        signed_de, notes = read_signed_de_table(source_path)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    out = trans_network.breadth_report_from_frame(signed_de, gene=gene)
    out["upload"] = {"import_id": import_id, **notes}
    return out


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
