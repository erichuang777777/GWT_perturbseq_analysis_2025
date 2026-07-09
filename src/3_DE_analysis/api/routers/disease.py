"""Disease-translation endpoints (architecture refactor Phase 4, §4.1)."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api import deps
from evidence.disease import list_diseases, translate_disease
from genetic_double_support import double_support

router = APIRouter(tags=["Disease"])


@router.get("/api/disease")
def get_diseases() -> Dict[str, Any]:
    associations = deps._disease_associations()
    return {
        "source": str(deps.DISEASE_ASSOCIATIONS_PATH.relative_to(deps.ROOT)) if deps.DISEASE_ASSOCIATIONS_PATH.exists() else None,
        "diseases": list_diseases(associations),
    }


@router.get("/api/disease/{disease_name}/targets/{dataset_id}")
def get_disease_targets(
    disease_name: str,
    dataset_id: str,
    min_grade: int = Query(default=2, ge=1, le=4),
    top_n: int = Query(default=50, ge=1, le=500),
) -> Dict[str, Any]:
    out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    cards = deps._normalize_cell_values(deps._load_cards(out_csv))
    associations = deps._disease_associations()

    readiness_csv = deps._dataset_path(dataset_id) / "readiness.csv"
    readiness_df = pd.read_csv(readiness_csv) if readiness_csv.exists() else None

    result = translate_disease(cards, disease_name, associations, readiness=readiness_df, min_grade=min_grade, top_n=top_n)
    return {"dataset_id": dataset_id, "disease_name": disease_name, **result}


@router.get("/api/genetic_double_support/{dataset_id}")
def get_genetic_double_support(
    dataset_id: str,
    min_grade: int = Query(default=2, ge=1, le=4),
    trait: str = Query(default="lymphocyte_count"),
) -> Dict[str, Any]:
    """Targets with BOTH disease genetic-association support (grade>=min_grade)
    and a population LoF-burden hypothesis whose 95% CI excludes zero.

    Additive, descriptive-only: nothing here feeds readiness. Each row carries
    the population caveat text verbatim (group-level, not patient-level).
    """
    out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    cards = deps._normalize_cell_values(deps._load_cards(out_csv))
    result = double_support(cards, min_grade=min_grade, trait=trait)
    return {"dataset_id": dataset_id, **result}
