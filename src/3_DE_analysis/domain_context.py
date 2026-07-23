"""Domain-context config — the CD4/immune assumptions, made overridable (P2).

The portal was built around CD4⁺ T-cell perturb-seq, so several places hard-code
immune-specific context. To accept ANY perturb-seq dataset, those assumptions must
be overridable per deployment WITHOUT changing the calibrated readiness engine.
This module centralizes them behind env-var overrides, each defaulting to the
existing CD4 behavior (so nothing changes unless a non-CD4 deployment opts in):

* ``GWT_PUBMED_CONTEXT``       — the literature-novelty query context
                                 (default ``"CD4 T cell"``). Threaded into
                                 ``fetch_pubmed_literature`` so a non-CD4 run
                                 measures novelty in ITS context, not CD4's.
* ``GWT_POSITIVE_CONTROLS``    — comma-separated positive-control genes
                                 (default: the in-repo TCR set). Effective set for
                                 consumers that want a domain-appropriate anchor.
* ``GWT_OFF_CONTEXT_TISSUES``  — tissues EXCLUDED from the "off-context expression"
                                 safety signal (default ``Blood,Spleen`` — the
                                 immune context). A non-immune screen sets its own.
* ``GWT_ENABLE_CONCEPT_MODULES`` — ``"0"`` disables the CD4 M01–M20 concept-module
                                 scoring for a non-CD4 dataset (they are curated CD4
                                 immune modules; the disease-reversal engine already
                                 accepts arbitrary user signatures instead).

Nothing here is read by the deterministic readiness engine's decision path; these
tune descriptive/evidence context, not the calibrated scoring.
"""

from __future__ import annotations

import os
from typing import Dict, List, Set

DEFAULT_PUBMED_CONTEXT = "CD4 T cell"
DEFAULT_OFF_CONTEXT_TISSUES = {"Blood", "Spleen"}


def _env_set(name: str) -> Set[str]:
    raw = os.environ.get(name, "")
    return {tok.strip() for tok in raw.split(",") if tok.strip()}


def pubmed_context() -> str:
    """Context string appended to the PubMed novelty query (default: CD4 T cell)."""
    return os.environ.get("GWT_PUBMED_CONTEXT") or DEFAULT_PUBMED_CONTEXT


def positive_controls() -> Set[str]:
    """Effective positive-control gene set (upper-cased). Env override, else the
    in-repo CD4 TCR set."""
    override = {g.upper() for g in _env_set("GWT_POSITIVE_CONTROLS")}
    if override:
        return override
    try:  # lazy import — core.cards pulls pandas
        from core.cards import POSITIVE_CONTROLS

        return {g.upper() for g in POSITIVE_CONTROLS}
    except Exception:  # noqa: BLE001 — never fail on an import edge
        return set()


def off_context_tissues() -> Set[str]:
    """Tissues excluded from the off-context expression safety signal (default:
    the immune context Blood/Spleen)."""
    override = _env_set("GWT_OFF_CONTEXT_TISSUES")
    return override or set(DEFAULT_OFF_CONTEXT_TISSUES)


def concept_modules_enabled() -> bool:
    """Whether the CD4 M01–M20 concept-module scoring applies to this dataset.

    Default on (CD4). A non-CD4 deployment sets ``GWT_ENABLE_CONCEPT_MODULES=0``;
    the disease-reversal engine's arbitrary user signatures replace the fixed
    modules for other cell types.
    """
    return os.environ.get("GWT_ENABLE_CONCEPT_MODULES", "1").strip().lower() not in {"0", "false", "no"}


def describe() -> Dict[str, object]:
    """Effective domain context (for transparency / the /api/domain_context route)."""
    pc: List[str] = sorted(positive_controls())
    return {
        "pubmed_context": pubmed_context(),
        "positive_controls_count": len(pc),
        "positive_controls_sample": pc[:12],
        "off_context_tissues": sorted(off_context_tissues()),
        "concept_modules_enabled": concept_modules_enabled(),
        "note": "CD4/immune defaults; override via GWT_PUBMED_CONTEXT / GWT_POSITIVE_CONTROLS / "
                "GWT_OFF_CONTEXT_TISSUES / GWT_ENABLE_CONCEPT_MODULES to accept a non-CD4 dataset. "
                "Descriptive context only — never changes the calibrated readiness decision path.",
    }
