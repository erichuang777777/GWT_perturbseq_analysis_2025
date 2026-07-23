"""Self-falsification audit endpoint (Action 3).

Descriptive-only. Serves the "does the system reject its own darlings?" audit:
the hub-darling receipt (the fraction of the top trans-effect hubs the system's
own safety veto rejects, vs the low-breadth tail) plus the curated anchor cases
(a target the system should ADVANCE and one it should REJECT). See
``self_falsification.py`` for method and honesty constraints.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Query

import self_falsification

router = APIRouter(tags=["Self-falsification audit (research use)"])


@router.get(
    "/api/self_falsification",
    summary="Does the system reject its own darlings? (descriptive audit)",
)
def get_self_falsification(top_n: int = Query(default=50, ge=10, le=500)) -> Dict[str, Any]:
    """The most impressive-looking hits (biggest trans-effect hubs) vs the system's
    own safety veto — a reproducible 'kills its own darling, with receipts' audit,
    plus anchor cases with known right answers (including a known NO). Descriptive
    only; the veto lists are the readiness engine's real inputs, so the system is
    graded against itself."""
    return self_falsification.run_self_falsification(top_n=top_n)
