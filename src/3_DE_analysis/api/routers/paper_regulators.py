"""Endpoint surfacing the source paper's OWN nominated regulators (verbatim).

Descriptive-only. Serves `metadata/suppl_tables/*_regulator_coefficients.csv` — the paper's
polarization / aging regulator nominations — keyed by gene. Not recomputed, never a readiness
input. See `paper_regulators.py` for provenance and honesty constraints (`unknown != 0`).
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

import paper_regulators

router = APIRouter(tags=["Concept profile (demo)"])


@router.get(
    "/api/paper_regulators/{gene}",
    summary="The source paper's own nominated polarization/aging regulators for a gene (verbatim, descriptive)",
)
def get_paper_regulators(gene: str) -> Dict[str, Any]:
    """Is this target one of the paper's own nominated polarization / aging regulators?

    Surfaces the paper's regulator-coefficient tables as-is: per signature × context,
    `coef_rank` (0–1 percentile; higher = more strongly nominated), signed `coef_mean`, and
    the paper's own `known_regulator` flag (False = a *novel* nomination). Top nominations
    are real master regulators (e.g. GATA3 → polarization rank 1.0, known).

    `unknown != 0`: a gene the paper did not nominate returns `nominations: []`, never a
    fabricated 0-coefficient row. This is the paper's own output made queryable — not a
    recomputation of its models, and not a readiness input.
    """
    return paper_regulators.regulators_for_target(gene)
