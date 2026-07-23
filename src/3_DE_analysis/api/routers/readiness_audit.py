"""Readiness faithfulness-audit + evidence-class endpoints (ported from
Predictability Audit #261 + PerturbGate #155).

Descriptive-only. Re-derives each readiness call's red-flag cap and reports whether
the stated call is internally consistent with it, and assigns each target a typed
evidence class. Never changes a call. See ``readiness_selfcheck.py`` /
``evidence_class.py``.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

import evidence_class
import readiness_selfcheck
from api import deps


router = APIRouter(tags=["Readiness audit (research use)"])


def _readiness_rows(dataset_id: str) -> List[Dict[str, Any]]:
    job_dir = deps._dataset_path(dataset_id)
    rc = job_dir / "readiness.csv"
    if not rc.exists():
        raise HTTPException(status_code=404, detail="readiness.csv not found for dataset; build readiness first")
    import pandas as pd

    df = pd.read_csv(rc)
    rows = []
    for _, r in df.iterrows():
        flags = r.get("red_flag_override")
        red = [] if (flags is None or str(flags) in ("nan", "none", "")) else str(flags).split(";")
        rows.append({
            "target": r.get("target"),
            "call": r.get("readiness_call"),
            "red_flags": red,
            "has_external_evidence": bool(r.get("has_external_evidence")) if "has_external_evidence" in df.columns else False,
        })
    return rows


@router.get("/api/readiness_audit/{dataset_id}", summary="Faithfulness self-check of readiness calls (descriptive)")
def readiness_audit(dataset_id: str) -> Dict[str, Any]:
    """Every readiness call re-derived from its red-flag cap and checked for
    internal consistency (a call may not exceed the cap its flags impose), plus a
    typed evidence class per target."""
    rows = _readiness_rows(dataset_id)
    audit = readiness_selfcheck.audit_calls(rows)
    classes = [
        {"target": r["target"], **evidence_class.classify(
            r["call"], has_external_evidence=r["has_external_evidence"], red_flags=r["red_flags"])}
        for r in rows
    ]
    return {"dataset_id": dataset_id, "faithfulness": audit, "evidence_classes": classes}
