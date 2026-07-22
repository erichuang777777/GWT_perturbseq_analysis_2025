"""Deterministic, source-grounded testable-hypothesis generator (plan P2-C).

Turns a target's already-computed signals into one plain-language, **testable**
sentence + a suggested validation — so a card reads as an action, not just a row
of numbers. The plan explicitly prefers a deterministic template FIRST (an LLM
variant would be an offline, cached, clearly-labelled enrichment, never in the
compute path): this function is pure string assembly over inputs the system
already produces, so it is auditable and reproducible.

Inputs it composes (all pre-existing, none fabricated):
* ``signed_module_effect`` direction — does knocking the target down ACTIVATE or
  REPRESS a CD4 concept module's program, and which module most strongly.
* ``readiness``'s ``next_validation_step`` — the engine's own suggested experiment.
* ``pathway_axis`` — the target's pathway grouping, as a fallback framing.

Honesty constraints
-------------------
* ``unknown != 0``: with no signed module effect AND no next step, we say so
  ("insufficient signal for a directional hypothesis") rather than invent one.
* Every hypothesis is explicitly framed as a CRISPRi-knockdown *prediction to
  test*, never a therapeutic claim.
* Deterministic; never mutates cards; never read by ``core/readiness.py``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import signed_module_effect

# CRISPRi convention: mean_logfc < 0 => knockdown lowers the module's markers
# => the target normally ACTIVATES that module; > 0 => REPRESSES it. Knocking
# down an activator is predicted to DOWN-regulate the module program, and vice
# versa. (Mirrors signed_module_effect._direction's convention exactly.)
_PREDICTED_MODULE_EFFECT = {
    "activator": "down-regulate",
    "repressor": "up-regulate",
}


def _strongest_module(effects: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Pick the module/condition with the most confident directional call.

    Prefers rows with a confident direction (activator/repressor) and more
    supporting downstream hits; ties broken by |mean_logfc|.
    """
    directional = [e for e in effects if e.get("direction") in _PREDICTED_MODULE_EFFECT]
    if not directional:
        return None
    return max(
        directional,
        key=lambda e: (int(e.get("n_downstream_hit") or 0), abs(float(e.get("mean_logfc") or 0.0))),
    )


def build_hypothesis(
    gene: str,
    *,
    strongest: Optional[Dict[str, Any]] = None,
    next_validation_step: Optional[str] = None,
    pathway_axis: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble a testable-hypothesis payload from already-computed signals (pure)."""
    gene = str(gene).strip().upper()
    basis: List[str] = []
    text: Optional[str] = None

    if strongest is not None:
        direction = strongest.get("direction")
        predicted = _PREDICTED_MODULE_EFFECT.get(direction)
        module_name = str(strongest.get("module_name") or strongest.get("module_id") or "a CD4 module").replace("_", " ")
        condition = strongest.get("condition")
        if predicted:
            cond_clause = f" in {condition}" if condition else ""
            text = (
                f"Knocking down {gene} is predicted to {predicted} the {module_name} program{cond_clause} "
                f"(CRISPRi data indicate {gene} normally {'activates' if direction == 'activator' else 'represses'} it)."
            )
            basis.append(
                f"signed_module_effect: {direction} of {module_name}"
                f" (mean_logfc={strongest.get('mean_logfc')}, hits={strongest.get('n_downstream_hit')})"
            )
    elif pathway_axis and str(pathway_axis).lower() not in ("", "nan", "none", "unknown"):
        text = (
            f"{gene} sits on the {str(pathway_axis).replace('_', ' ')} axis; test whether its knockdown "
            f"shifts that program in primary CD4 T cells."
        )
        basis.append(f"pathway_axis={pathway_axis}")

    suggested = None
    if next_validation_step and str(next_validation_step).strip().lower() not in ("", "nan", "none"):
        suggested = str(next_validation_step).strip()
        basis.append("readiness.next_validation_step")

    available = text is not None or suggested is not None
    if not available:
        # unknown != 0: no directional signal and no engine next-step -> say so.
        return {
            "gene": gene,
            "available": False,
            "reason": "insufficient signal for a directional hypothesis (no measured module effect, no next step)",
        }

    return {
        "gene": gene,
        "available": True,
        "hypothesis": text,
        "suggested_validation": suggested,
        "basis": basis,
        "caveat": "A CRISPRi-knockdown prediction to test, not a therapeutic claim. Knockdown != pharmacologic inhibition.",
    }


def hypothesis_for_target(
    gene: str,
    *,
    next_validation_step: Optional[str] = None,
    pathway_axis: Optional[str] = None,
) -> Dict[str, Any]:
    """Serving helper: pull the strongest signed module effect for ``gene`` and build.

    ``next_validation_step`` / ``pathway_axis`` are passed in by the caller (the
    readiness/card layer already has them) so this stays decoupled from the
    readiness engine and the card frame.
    """
    profile = signed_module_effect.effects_for_target(gene)
    strongest = _strongest_module(profile.get("modules") or []) if profile.get("available") else None
    return build_hypothesis(
        gene,
        strongest=strongest,
        next_validation_step=next_validation_step,
        pathway_axis=pathway_axis,
    )
