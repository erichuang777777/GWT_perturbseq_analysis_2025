"""Signed module-effect endpoint — directional regulator → concept-module readout.

Descriptive-only. Serves the precomputed `signed_module_effect` overlay (built from
the in-repo signed DE table `full_signed_DE`, which carries per-downstream-gene
direction the aggregate card substrate does not). Never a readiness input. See
`signed_module_effect.py` for the method and honesty constraints (`unknown != 0`).
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

import signed_module_effect

router = APIRouter(tags=["Concept profile (demo)"])


@router.get(
    "/api/signed_module_effect/{gene}",
    summary="Signed directional effect of a perturbation on each CD4 concept module (descriptive)",
)
def get_signed_module_effect(gene: str) -> Dict[str, Any]:
    """Does knocking down this target ACTIVATE or REPRESS each concept module's program?

    Computed from the repo's signed DE table (`full_signed_DE`): the average signed
    `log_fc` of a module's seed (marker) genes among this target's downstream genes,
    per condition. CRISPRi convention — markers dropping on knockdown (`mean_logfc<0`)
    means the target normally *activates* that module.

    `unknown != 0`: module/condition pairs with no measured module-seed downstream gene
    are ABSENT from `modules`, never returned as 0. Coverage is sparse (only ~3,739 of
    the screened targets perturb any module marker measurably) — an honest property of
    the data. `n_downstream_hit` / `n_module_seed_total` travel with each score so a
    single-gene average is never mistaken for a well-supported one.

    Descriptive only: this is NOT a readiness input and does not reproduce the source
    paper's regulatory-network inference — it is a directional readout over the same
    screen (see `docs/KNOWN_LIMITATIONS.md` → "Scope & positioning").
    """
    return signed_module_effect.effects_for_target(gene)
