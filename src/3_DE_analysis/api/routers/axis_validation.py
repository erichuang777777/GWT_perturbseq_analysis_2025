"""Axis-validation endpoint (ported from "A Validated Th1/Th2 Target Map" #240).

Descriptive-only. Validate a scoring axis (a gene->score map) against an external
published ground-truth coefficient vector, and return a validated/exploratory
verdict — the "don't let a weak axis nominate" gate. Ground-truth references are
the source paper's own regulator-coefficient tables. See ``axis_validator.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import axis_validator

router = APIRouter(tags=["Axis validation (research use)"])

_ROOT = Path(__file__).resolve().parents[4]  # routers -> api -> 3_DE_analysis -> src -> repo root
_SUPPL = _ROOT / "metadata" / "suppl_tables"
# reference id -> (csv, signature filter, gene col, coef col)
_REFERENCES = {
    "polarization_ota": ("polarization_prediction_condition_comparison_regulator_coefficients.csv", "ota"),
    "polarization_activation": ("polarization_prediction_condition_comparison_regulator_coefficients.csv", "activation"),
    "aging": ("aging_prediction_condition_comparison_regulator_coefficients.csv", None),
}


class AxisRequest(BaseModel):
    axis_scores: Dict[str, float]
    reference: str = "polarization_ota"
    known_only: bool = False       # restrict ground truth to the paper's known_regulators


def _load_reference(ref: str):
    if ref not in _REFERENCES:
        raise HTTPException(status_code=404, detail=f"unknown reference {ref!r}; have {sorted(_REFERENCES)}")
    csv, sig = _REFERENCES[ref]
    path = _SUPPL / csv
    if not path.exists():
        raise HTTPException(status_code=503, detail=f"reference table not present in this checkout: {csv}")
    import pandas as pd

    df = pd.read_csv(path)
    if sig is not None and "signature" in df.columns:
        df = df[df["signature"] == sig]
    return df


@router.get("/api/axis_validation/references", summary="List available ground-truth references")
def list_references() -> Dict[str, Any]:
    out = []
    for ref, (csv, sig) in _REFERENCES.items():
        out.append({"id": ref, "table": csv, "signature": sig, "available": (_SUPPL / csv).exists()})
    return {"references": out}


@router.post("/api/axis_validation", summary="Validate a scoring axis vs a published-coefficient reference")
def validate(req: AxisRequest) -> Dict[str, Any]:
    """Correlate a submitted axis (gene->score) against the paper's own regulator
    coefficients; return validated/exploratory. `unknown != 0`: too few
    overlapping targets -> not_evaluable, never a fake pass."""
    df = _load_reference(req.reference)
    gt = df.groupby("regulator")["coef_mean"].mean().to_dict() if "coef_mean" in df.columns else {}
    if not gt:
        raise HTTPException(status_code=503, detail="reference has no coef_mean column")
    known = None
    if req.known_only and "known_regulators" in df.columns:
        known = set(df[df["known_regulators"] == True]["regulator"].astype(str))  # noqa: E712
    axis = {str(k).upper(): float(v) for k, v in req.axis_scores.items()}
    gtU = {str(k).upper(): float(v) for k, v in gt.items()}
    kU = {k.upper() for k in known} if known else None
    result = axis_validator.validate_axis(axis, gtU, known_set=kU)
    result["reference"] = req.reference
    return result
