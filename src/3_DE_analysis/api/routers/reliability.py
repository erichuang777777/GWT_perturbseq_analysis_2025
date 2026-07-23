"""Reliability / confidence endpoints (ported from G-perturb #133).

Descriptive-only. Serves a per-target 0-1 reliability coefficient (R_dep) computed
from card fields the portal already has (crossguide_correlation +
crossdonor_correlation_mean) — a confidence band beside the readiness call, never
folded into it. See ``reliability.py``.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

import reliability
from api import deps

router = APIRouter(tags=["Reliability (research use)"])


def _rows(dataset_id: str) -> List[Dict[str, Any]]:
    out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    df = deps._normalize_cell_values(deps._load_cards(out_csv))
    recs = []
    for _, r in df.iterrows():
        rel = reliability.reliability_for_card(
            r.get("crossguide_correlation"), r.get("crossdonor_correlation_mean"),
            r.get("ontarget_effect_size"),
        )
        recs.append({"target": r.get("target"), "condition": r.get("condition"), **rel})
    return recs


@router.get("/api/reliability/{dataset_id}", summary="Per-target reliability (R_dep) confidence over a dataset")
def reliability_dataset(dataset_id: str) -> Dict[str, Any]:
    """Reliability-weighted confidence for every card. Descriptive; unknown != 0
    (unmeasured cross-guide/donor correlation -> r_dep null, never 0)."""
    return {"dataset_id": dataset_id, "targets": _rows(dataset_id)}


@router.get("/api/reliability/{dataset_id}/{target}", summary="Per-target reliability (R_dep) confidence")
def reliability_target(dataset_id: str, target: str) -> Dict[str, Any]:
    hits = [r for r in _rows(dataset_id) if str(r.get("target", "")).upper() == target.strip().upper()]
    if not hits:
        raise HTTPException(status_code=404, detail=f"target {target!r} not found")
    return {"dataset_id": dataset_id, "target": target.strip().upper(), "by_condition": hits}
