"""Gene resolve/search/status/CRE endpoints (architecture refactor Phase 4, §4.1)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from api import deps
from resolve.cre import cre_for_gene, load_cre_elements, load_variant_cre_links
from resolve.resolver import result_status
from resolve.search import search_genes

router = APIRouter(tags=["genes"])


@router.get("/api/genes/resolve")
def resolve_gene(q: str = Query(..., description="gene symbol, alias, or Ensembl ID")) -> Dict[str, Any]:
    resolver = deps._gene_resolver()
    return resolver.resolve(q)


@router.post("/api/genes/resolve")
def resolve_genes_batch(queries: List[str]) -> List[Dict[str, Any]]:
    resolver = deps._gene_resolver()
    return resolver.resolve_many(queries)


@router.get("/api/genes/status")
def gene_result_status(
    q: str = Query(..., description="gene symbol, alias, or Ensembl ID"),
    dataset_id: Optional[str] = Query(default=None, description="built dataset to check; defaults to the raw reference DE table"),
) -> Dict[str, Any]:
    """Three-state (+has_effect) result status for any gene, per docs/de_and_baseline_spec.md.

    Without dataset_id, checks against the raw reference DE_stats table (always
    locally available) so a query never depends on a dataset having been built.
    """
    resolver = deps._gene_resolver()
    if dataset_id:
        out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
        if not out_csv.exists():
            raise HTTPException(status_code=404, detail="dataset_id not found")
        de_df = deps._load_cards(out_csv)
        source = f"dataset:{dataset_id}"
    elif deps.DEFAULT_DE.exists():
        de_df = pd.read_csv(deps.DEFAULT_DE)
        source = str(deps.DEFAULT_DE.relative_to(deps.ROOT))
    else:
        de_df = pd.DataFrame(columns=["target"])
        source = "unavailable"
    return {"source": source, **result_status(resolver, q, de_df)}


@router.get("/api/search")
def search_genes_endpoint(q: str = Query(..., min_length=1), limit: int = Query(default=10, ge=1, le=50)) -> Dict[str, Any]:
    resolver = deps._gene_resolver()
    return {"query": q, "results": search_genes(resolver, q, limit=limit)}


@router.get("/api/cre/{gene_query}")
def get_cre_for_gene(gene_query: str) -> Dict[str, Any]:
    """CRE (cis-regulatory element) links for a gene -- schema placeholder (B5).

    Honestly reports 'not loaded' (never fabricates elements) until a real
    CRE dataset is configured at CRE_ELEMENTS_PATH/VARIANT_CRE_LINKS_PATH.
    """
    resolver = deps._gene_resolver()
    resolution = resolver.resolve(gene_query)
    cre_result = load_cre_elements(deps.CRE_ELEMENTS_PATH if deps.CRE_ELEMENTS_PATH.exists() else None)
    variant_result = load_variant_cre_links(deps.VARIANT_CRE_LINKS_PATH if deps.VARIANT_CRE_LINKS_PATH.exists() else None)
    elements = cre_for_gene(resolution.get("ensembl_gene_id") or gene_query, cre_result) if resolution.get("matched") else []
    return {
        "gene_query": gene_query,
        "resolution": resolution,
        "cre_available": cre_result["available"],
        "cre_reason": cre_result["reason"],
        "variant_link_available": variant_result["available"],
        "variant_link_reason": variant_result["reason"],
        "elements": elements,
    }
