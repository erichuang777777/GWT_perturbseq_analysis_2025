"""Population LoF-burden hypothesis endpoint (architecture refactor Phase 4, §4.1)."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter, Query

from api import deps
from evidence.population import CAVEAT_TEXT, build_population_hypothesis_card

router = APIRouter(tags=["population"])


@router.get("/api/population-hypothesis/{gene}")
def get_population_hypothesis(
    gene: str,
    trait: str = Query(default="lymphocyte_count"),
) -> Dict[str, Any]:
    """Module 3 part A: population LoF-burden hypothesis card for one gene.

    Read-only; joins the cached UK Biobank burden-estimate table (see
    evidence/population.py) against the gene's resolved Ensembl ID. Never a
    patient-level prediction -- every non-empty result carries the fixed
    ``caveat`` field verbatim.
    """
    resolver = deps._gene_resolver()
    resolution = resolver.resolve(gene)
    burden = deps._burden_estimates(trait)
    if not burden["available"]:
        return {"gene": gene, "trait": trait, "available": False, "reason": burden["reason"], "caveat": CAVEAT_TEXT}
    if not resolution["matched"]:
        return {
            "gene": gene,
            "trait": trait,
            "available": True,
            "matched": False,
            "reason": "gene not found in the local alias table",
            "caveat": CAVEAT_TEXT,
        }
    fake_cards = pd.DataFrame({"target": [resolution["canonical_symbol"]], "target_id": [resolution["ensembl_gene_id"]]})
    card = build_population_hypothesis_card(fake_cards, burden["estimates"], trait=trait)
    if card.empty:
        return {
            "gene": gene,
            "trait": trait,
            "available": True,
            "matched": True,
            "ensembl_gene_id": resolution["ensembl_gene_id"],
            "found_in_burden_table": False,
            "reason": f"no {trait} burden estimate for this gene in the local table",
            "caveat": CAVEAT_TEXT,
        }
    return {"available": True, "matched": True, "found_in_burden_table": True, **deps._json_object(card.iloc[0].to_dict())}
