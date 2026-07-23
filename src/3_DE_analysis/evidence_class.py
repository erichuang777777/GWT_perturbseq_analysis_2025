"""First-class evidence-class vocabulary + conservation invariants (ported from
PerturbGate #155).

PerturbGate's discipline: negatives are not filtered-away rows, they are TYPED
outputs, and the funnel obeys a conservation law. Two portable pieces:

1. A controlled vocabulary mapping the readiness call (+ evidence depth) to a
   typed ``evidence_class`` — so "why isn't this advanced" is a first-class,
   enumerable answer, not an absence.
2. Invariants enforced in code:
   * **funnel conservation** — for every stage,
     ``advanced + not_advanced + rejected + unresolved == entering``;
   * **depth honesty** — you may not label something a DEEP rejection without
     DEEP evidence.

This matches the portal's descriptive-vs-decision discipline (the class is
derived from the call, never the reverse) and ``unknown != 0`` (an unresolved
target is ``unresolved``, never silently a rejection).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Typed final classes, keyed to the readiness call. Mirrors PerturbGate's
# FINAL_EVIDENCE_CLASSES, mapped onto this portal's four-call vocabulary.
CALL_TO_CLASS = {
    "advance": "RETAINED_ADVANCE",
    "validate": "VETTED_VALIDATE",
    "watchlist": "EXPLORATORY_WATCHLIST",
    "deprioritize": "REJECTED_DEPRIORITIZE",
}
EVIDENCE_DEPTHS = ("screen_only", "shortlist_vetted", "deep")
FINAL_EVIDENCE_CLASSES = set(CALL_TO_CLASS.values()) | {"UNRESOLVED"}


def evidence_depth(has_external_evidence: bool, red_flags: Optional[List[str]]) -> str:
    """How deeply vetted is this call? screen-only vs external-corroborated (deep)."""
    if has_external_evidence:
        return "deep"
    if red_flags:  # a red flag is a shortlist-level vetting event
        return "shortlist_vetted"
    return "screen_only"


def classify(
    readiness_call: Optional[str],
    *,
    has_external_evidence: bool = False,
    red_flags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Map a readiness call to a typed evidence class + depth + reason.

    ``unknown != 0``: a null/unknown call is ``UNRESOLVED`` with depth
    ``screen_only`` — never coerced into a rejection.
    """
    call = (readiness_call or "").strip().lower()
    cls = CALL_TO_CLASS.get(call, "UNRESOLVED")
    depth = evidence_depth(has_external_evidence, red_flags)
    reason = None
    if cls == "REJECTED_DEPRIORITIZE":
        reason = ("red flags: " + ", ".join(red_flags)) if red_flags else "insufficient statistical evidence"
    elif cls in ("EXPLORATORY_WATCHLIST", "VETTED_VALIDATE") and red_flags:
        reason = "capped by: " + ", ".join(red_flags)
    return {"evidence_class": cls, "evidence_depth": depth, "reason": reason}


def check_funnel(stages: List[Dict[str, Any]]) -> List[str]:
    """Conservation check: per stage, entering == advanced+not_advanced+rejected+unresolved,
    and every stage names a source. Returns a list of problems (empty = valid)."""
    problems: List[str] = []
    for s in stages:
        name = s.get("name", "?")
        entering = s.get("entering")
        parts = [s.get(k, 0) for k in ("advanced", "not_advanced", "rejected", "unresolved")]
        if entering is None:
            problems.append(f"stage {name}: missing 'entering'")
            continue
        if sum(parts) != entering:
            problems.append(f"stage {name}: {'+'.join(str(p) for p in parts)}={sum(parts)} != entering {entering}")
        if not s.get("source_artifact"):
            problems.append(f"stage {name}: no source_artifact named")
    return problems


def check_depth_honesty(rows: List[Dict[str, Any]]) -> List[str]:
    """Depth honesty: a REJECTED_DEPRIORITIZE row claiming a 'deep' rejection must
    actually carry deep evidence. Returns problems (empty = valid)."""
    problems: List[str] = []
    for r in rows:
        cls = r.get("evidence_class")
        depth = r.get("evidence_depth")
        if cls not in FINAL_EVIDENCE_CLASSES:
            problems.append(f"{r.get('target','?')}: class {cls!r} outside vocabulary")
        if depth is not None and depth not in EVIDENCE_DEPTHS:
            problems.append(f"{r.get('target','?')}: depth {depth!r} outside {EVIDENCE_DEPTHS}")
        if r.get("claims_deep_rejection") and depth != "deep":
            problems.append(f"{r.get('target','?')}: claims a deep rejection but depth is {depth!r}")
    return problems
