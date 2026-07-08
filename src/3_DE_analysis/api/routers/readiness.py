"""Readiness endpoint (architecture refactor Phase 4, §4.1)."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api import deps
from core.readiness import compute_readiness, readiness_summary
from evidence.external_cache import load_snapshot as load_evidence_snapshot

router = APIRouter(tags=["readiness"])


@router.get("/api/readiness/{dataset_id}")
def get_readiness(dataset_id: str, refresh: bool = Query(default=False)) -> Dict[str, Any]:
    out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    readiness_csv = deps._dataset_path(dataset_id) / "readiness.csv"
    overlays = deps._overlays()
    stale = (
        refresh
        or not readiness_csv.exists()
        or readiness_csv.stat().st_mtime < out_csv.stat().st_mtime
        or readiness_csv.stat().st_mtime < deps._evidence_dir_mtime()
    )
    if stale:
        cards = deps._normalize_cell_values(deps._load_cards(out_csv))
        readiness = compute_readiness(
            cards,
            overlays=overlays,
            essentials=deps._essentials(),
            broad_effect_genes=deps._broad_effect_genes(),
            # architecture refactor Phase 3: core/readiness.py no longer
            # imports evidence.external_cache itself -- this API layer (which
            # already imports it for /api/evidence/*) builds the lookup
            # closure and injects it instead.
            evidence_lookup=lambda gene: load_evidence_snapshot(deps.EVIDENCE_CACHE_DIR, gene),
            membrane_overlay=deps._membrane_overlay(),
            gtex_overlay=deps._gtex_overlay(),
            gnomad_overlay=deps._gnomad_overlay(),
        )
        readiness.to_csv(readiness_csv, index=False)
    else:
        readiness = pd.read_csv(readiness_csv)
    return {
        "dataset_id": dataset_id,
        **readiness_summary(readiness, overlays=overlays),
        "readiness": deps._json_records(readiness),
    }
