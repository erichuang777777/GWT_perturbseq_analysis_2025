"""Self-false-positive audit endpoint (ported from "Bench to Biobank" #123).

Descriptive-only. Serves the phenome-breadth specificity flag — the one of
Bench2Biobank's three self-false-positive sub-checks computable from data the
portal already has (the Level-4 track-A GWAS re-check). The MHC-region and
nearest-gene sub-checks are returned as explicit ``measured: false`` stubs
(``unknown != 0``), never faked. This is a false-positive-RISK band for a human;
it never feeds the readiness call. See ``false_positive_audit.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

import false_positive_audit as fpa

router = APIRouter(tags=["False-positive audit (research use)"])

_ROOT = Path(__file__).resolve().parents[4]  # routers -> api -> 3_DE_analysis -> src -> repo root
_TRACK_A = _ROOT / "docs" / "mvp-research" / "level4_external_validation" / "track_a_gwas_genetic_association.csv"


def _rows() -> List[Dict[str, Any]]:
    if not _TRACK_A.exists():
        raise HTTPException(status_code=503, detail="track-A GWAS table not present in this checkout")
    import pandas as pd

    df = pd.read_csv(_TRACK_A)
    out = []
    for _, r in df.iterrows():
        audit = fpa.audit_gwas_row(r.to_dict())
        out.append({"target": r.get("target_gene"), "ensembl": r.get("target_ensembl_id"), **audit})
    return out


@router.get("/api/false_positive_audit", summary="Phenome-breadth self-false-positive audit over the GWAS-validated targets")
def audit_all() -> Dict[str, Any]:
    """Per-target phenome-breadth specificity flag. Descriptive; `unknown != 0`
    (a target with no GWAS row is simply absent here — not a clean pass). The
    MHC-region and nearest-gene sub-checks are honest `measured: false` stubs."""
    rows = _rows()
    elevated = [r["target"] for r in rows if r.get("elevated_fp_risk") is True]
    return {
        "source": "Level-4 track-A Open Targets GWAS re-check",
        "n_targets": len(rows),
        "n_elevated_fp_risk": len(elevated),
        "elevated_fp_risk_targets": elevated,
        "note": "phenome-breadth is 1 of Bench2Biobank's 3 self-FP checks; MHC-region + nearest-gene need data the cards don't carry (see per-target measured:false stubs). Never a readiness input.",
        "targets": rows,
    }


@router.get("/api/false_positive_audit/{target}", summary="Phenome-breadth self-false-positive audit for one target")
def audit_target(target: str) -> Dict[str, Any]:
    key = target.strip().upper()
    hits = [r for r in _rows() if str(r.get("target", "")).upper() == key]
    if not hits:
        raise HTTPException(status_code=404, detail=f"target {target!r} not in the GWAS-validated set (phenome breadth unmeasured)")
    return hits[0]
