"""Testable-hypothesis endpoint (development plan P2-C).

Descriptive-only. Assembles one plain-language, testable CRISPRi-knockdown
hypothesis + a suggested validation for a target, deterministically from the
target's signed module effect. No LLM in the request path. See ``hypothesis.py``
for the composition rules and honesty constraints.

Optional query params let a caller that already has them (e.g. the static export,
which holds the readiness frame in memory) pass in the readiness engine's
``next_validation_step`` and the card's ``pathway_axis`` to enrich the hypothesis;
omitted, the hypothesis rests on the signed module effect alone. This keeps the
endpoint decoupled from the readiness engine / card frame rather than reaching
into private dataset-loading internals.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Query

import hypothesis as hypothesis_mod

router = APIRouter(tags=["Concept profile (demo)"])


@router.get(
    "/api/hypothesis/{gene}",
    summary="Deterministic testable-hypothesis for a target (descriptive)",
)
def get_hypothesis(
    gene: str,
    next_validation_step: Optional[str] = Query(default=None),
    pathway_axis: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    """One testable CRISPRi-knockdown hypothesis + suggested validation, composed
    deterministically from the target's signed module effect (+ optional readiness
    next_validation_step / pathway axis when the caller supplies them).

    `unknown != 0`: reports ``available: false`` when there's no directional signal
    and no next step, rather than inventing a hypothesis. Descriptive only.
    """
    return hypothesis_mod.hypothesis_for_target(
        gene,
        next_validation_step=next_validation_step,
        pathway_axis=pathway_axis,
    )
