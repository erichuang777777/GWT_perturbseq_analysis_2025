"""Mechanism-graph endpoint (architecture refactor Phase 4, §4.1)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api import deps
from evidence.mechanism_graph import build_mechanism_graph

router = APIRouter(tags=["Mechanism graph"])


@router.get("/api/mechanism-graph/{gene}")
def get_mechanism_graph(
    gene: str,
    dataset_id: Optional[str] = Query(
        default=None,
        description="built dataset to overlay cards/readiness evidence from; omit for the bare pathway/network graph",
    ),
) -> Dict[str, Any]:
    """A2: target-centered mechanism graph (Reactome pathway membership + STRING
    interaction partners), optionally overlaid with this platform's own evidence.

    Read-only; reads evidence/pathway_cache.py's cached snapshot
    (evidence/mechanism_graph.py never fetches live) and, if ``dataset_id``
    is supplied, that dataset's built ``target_cards.csv``/``readiness.csv``
    to enrich each gene node. Purely descriptive -- never feeds
    ``readiness_call``/``overall_readiness_stage``.
    """
    resolver = deps._gene_resolver()
    resolution = resolver.resolve(gene)
    lookup_gene = resolution["canonical_symbol"] if resolution.get("matched") else gene

    cards_df = None
    readiness_df = None
    if dataset_id:
        out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
        if not out_csv.exists():
            raise HTTPException(status_code=404, detail="dataset_id not found")
        cards_df = deps._normalize_cell_values(deps._load_cards(out_csv))
        readiness_csv = deps._dataset_path(dataset_id) / "readiness.csv"
        readiness_df = pd.read_csv(readiness_csv) if readiness_csv.exists() else None

    # deps.PATHWAY_CACHE_DIR is read via module-attribute access (not
    # `from api.deps import PATHWAY_CACHE_DIR`) so a test/config override of
    # deps.PATHWAY_CACHE_DIR is honored at request time -- see api/deps.py's
    # module docstring.
    graph = build_mechanism_graph(lookup_gene, deps.PATHWAY_CACHE_DIR, cards=cards_df, readiness=readiness_df)
    return {"gene_query": gene, "resolution": resolution, "dataset_id": dataset_id, **graph}
