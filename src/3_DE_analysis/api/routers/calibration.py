"""Calibration endpoint (architecture refactor Phase 4, §4.1)."""

from __future__ import annotations

import json
from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api import deps
from core.calibration import run_calibration

router = APIRouter(tags=["Calibration"])


@router.get("/api/calibration/{dataset_id}")
def get_calibration(dataset_id: str, refresh: bool = Query(default=False)) -> Dict[str, Any]:
    out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    calib_json = deps._dataset_path(dataset_id) / "calibration.json"
    if refresh or not calib_json.exists() or calib_json.stat().st_mtime < out_csv.stat().st_mtime:
        cards = deps._normalize_cell_values(deps._load_cards(out_csv))
        readiness_csv = deps._dataset_path(dataset_id) / "readiness.csv"
        readiness_df = pd.read_csv(readiness_csv) if readiness_csv.exists() else None
        report = run_calibration(cards, readiness=readiness_df)
        calib_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    else:
        report = json.loads(calib_json.read_text(encoding="utf-8"))
    return {"dataset_id": dataset_id, **report}
