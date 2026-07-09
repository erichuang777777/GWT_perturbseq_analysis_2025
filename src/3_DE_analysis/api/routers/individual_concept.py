"""Individual-sample concept-profile endpoint (COMPASS-analog, plan §3/P3).

``POST /api/individual-concept-profile`` accepts ONE sample's gene-expression
vector as a ``{gene: value}`` JSON map (no identifier fields), projects it
transparently onto the 20 CD4 immune concept modules, and returns the concept
activation profile + hypothesis-only screened-target clues.

**Request-only, no persistence (plan §3.3/§7-P3, CRITICAL):** the raw input
expression vector lives ONLY in this request's memory. It is never written to
``sources/target_tool_cache/`` (or anywhere), never cached, never logged to a
file. The handler builds no dataset directory and calls no persistence helper.
The only disk access is READ-ONLY: the static seed-module CSV, and -- if the
caller names an already-built ``dataset_id`` -- that dataset's existing
``target_cards.csv``/``readiness.csv`` (to attach hypotheses). No write path.

**Descriptive only:** nothing here feeds ``readiness_call`` /
``overall_readiness_stage`` -- it only reads them, same principle as the
mechanism-graph router.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
from fastapi import APIRouter, Body, Query

from api import deps
from upload.import_manager import utc_now

import individual_concept_profile as icp

router = APIRouter(tags=["Concept profile (demo)"])


@router.post("/api/individual-concept-profile")
def post_individual_concept_profile(
    sample_expression: Dict[str, float] = Body(
        ...,
        description=(
            "One sample's gene-expression vector as a {gene_symbol: value} map "
            "(TPM / normalized counts / signed z-scores). No identifier fields "
            "are accepted or expected. Request-only: never stored."
        ),
    ),
    dataset_id: Optional[str] = Query(
        default=None,
        description=(
            "Optional already-built dataset to source screened CRISPRi "
            "target->concept hypotheses from; omit for the concept profile alone."
        ),
    ),
) -> Dict[str, Any]:
    """Project one sample onto the 20 concepts and attach hypothesis-only clues.

    Read-only + request-only. ``computed_at`` is stamped HERE (via
    ``utc_now()``) and passed into the pure builder, which never calls the
    clock itself. The input ``sample_expression`` is not persisted.
    """
    modules = icp.load_concept_modules()

    target_cards: Optional[pd.DataFrame] = None
    readiness: Optional[pd.DataFrame] = None
    screen_data_version = "unavailable"
    if dataset_id:
        # Build the path directly (no _dataset_path(): that mkdir()s a
        # directory, which would be a write side effect). Read-only access to
        # already-built artifacts only.
        dataset_dir = deps.CACHE_ROOT / dataset_id
        cards_csv = dataset_dir / "target_cards.csv"
        readiness_csv = dataset_dir / "readiness.csv"
        if cards_csv.exists():
            target_cards = deps._normalize_cell_values(deps._load_cards(cards_csv))
        if readiness_csv.exists():
            readiness = pd.read_csv(readiness_csv)
        prov = deps._provenance_block(dataset_id)
        screen_data_version = (
            f"{dataset_id}@dataset_version={prov.get('dataset_version')};"
            f"schema={prov.get('schema_version')}"
            if prov
            else f"{dataset_id}@no-metadata"
        )

    report = icp.build_individual_concept_report(
        sample_expression,
        modules=modules,
        target_cards=target_cards,
        readiness=readiness,
        computed_at=utc_now(),
        screen_data_version=screen_data_version,
    )
    report["dataset_id"] = dataset_id
    return report
