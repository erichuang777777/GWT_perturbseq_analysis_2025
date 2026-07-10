"""Disease x drug evidence-matching endpoint (docs/frontend_design.md §5.2).

Thin wrapper around ``evidence.external_cache.match_disease_drug_evidence`` --
that function is already fully implemented but was never exposed via any API
route or UI. Answers "does this gene have a known drug, and has that drug
actually been trialled for this specific disease" as two separate, checkable
facts -- never collapsed into a single score, and never a treatment
recommendation (see that function's own docstring for the full honesty
contract, including why a nonzero drug count for the gene can still carry
zero trials for the disease asked about).

This makes LIVE calls to Open Targets GraphQL + ClinicalTrials.gov at request
time (unlike ``/api/evidence/{gene}``, which only ever reads a pre-fetched,
offline-batched snapshot) because the disease name is an open-ended query
parameter, not a fixed per-gene value that a snapshot cache can key on. The
function itself never fabricates on failure -- a network error or an
unresolved gene returns ``{"available": False, "reason": ...}``, which this
route passes through unmodified.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Query

from evidence.external_cache import match_disease_drug_evidence

router = APIRouter(tags=["Clinical evidence (research use)"])


@router.get("/api/disease-drug-evidence")
def get_disease_drug_evidence(
    gene: str,
    disease: str,
    max_drugs: int = Query(default=10, ge=1, le=50),
) -> Dict[str, Any]:
    return match_disease_drug_evidence(gene, disease, max_drugs=max_drugs)
