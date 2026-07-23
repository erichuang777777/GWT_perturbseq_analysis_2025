"""Faithfulness self-check for readiness calls (ported from the CD4 Predictability
Audit #261).

#261's discipline: a verdict is trustworthy only if it can be RE-DERIVED from its
own committed inputs and matches. Their ``scorecard.run_audit`` re-computes each
pre-registered verdict from its score+threshold and self-checks it against the
stored verdict via a ``consistent`` flag.

Here we apply that to the readiness engine: given a stated readiness ``call`` and
its red-flag overrides, re-derive the CAP the red flags impose and verify the
stated call does not exceed it. A call of ``advance`` while carrying an
``essential_gene`` flag is internally inconsistent and gets flagged — a cheap,
deterministic audit that the engine's own rule was actually honored.

Mirrors ``core/readiness.py``'s CALL_ORDER + red-flag caps exactly (kept in sync
by ``tests/test_readiness_selfcheck.py``). Descriptive audit; never changes a call.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Order and caps mirror core/readiness.py (CALL_ORDER + _red_flags caps).
CALL_ORDER = ["deprioritize", "watchlist", "validate", "advance"]
RED_FLAG_CAP = {
    "essential_gene": "watchlist",
    "broad_effect": "watchlist",
    "high_offtarget": "watchlist",
    "kd_not_measurable": "watchlist",
    "uncertain_direction": "validate",
    "batch_confounded": "validate",
    "kd_weak": "validate",
}


def _idx(call: Optional[str]) -> Optional[int]:
    if not call:
        return None
    try:
        return CALL_ORDER.index(call.strip().lower())
    except ValueError:
        return None


def cap_from_red_flags(red_flags: Optional[List[str]]) -> str:
    """The most restrictive call the given red flags permit (advance if none apply)."""
    cap_idx = len(CALL_ORDER) - 1  # advance
    for f in red_flags or []:
        capped = RED_FLAG_CAP.get(str(f).strip().lower())
        if capped is not None:
            cap_idx = min(cap_idx, CALL_ORDER.index(capped))
    return CALL_ORDER[cap_idx]


def selfcheck_call(call: Optional[str], red_flags: Optional[List[str]]) -> Dict[str, Any]:
    """Is a readiness call consistent with its own red-flag caps?

    ``consistent`` is False when the stated call ranks ABOVE the cap its red flags
    impose (e.g. advance with an essential_gene flag). Unknown call -> not
    evaluable (unknown != 0), never silently 'consistent'.
    """
    ci = _idx(call)
    cap = cap_from_red_flags(red_flags)
    cap_idx = CALL_ORDER.index(cap)
    if ci is None:
        return {"consistent": None, "call": call, "implied_cap": cap,
                "reason": "call not recognized; not evaluable"}
    consistent = ci <= cap_idx
    return {
        "consistent": consistent,
        "call": CALL_ORDER[ci],
        "implied_cap": cap,
        "violated_flags": [f for f in (red_flags or [])
                           if f in RED_FLAG_CAP and CALL_ORDER.index(RED_FLAG_CAP[f]) < ci] if not consistent else [],
        "reason": None if consistent else f"call '{call}' exceeds cap '{cap}' implied by its red flags",
    }


def audit_calls(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Batch faithfulness audit over readiness rows (each {target, call, red_flags}).

    Returns the count and list of inconsistent targets — the analog of #261's
    'all probes reproduce' pass/fail.
    """
    inconsistent = []
    n_eval = 0
    for r in rows:
        res = selfcheck_call(r.get("call"), r.get("red_flags"))
        if res["consistent"] is None:
            continue
        n_eval += 1
        if not res["consistent"]:
            inconsistent.append({"target": r.get("target"), **res})
    return {
        "n_evaluated": n_eval,
        "n_inconsistent": len(inconsistent),
        "all_consistent": len(inconsistent) == 0 and n_eval > 0,
        "inconsistent": inconsistent,
    }
