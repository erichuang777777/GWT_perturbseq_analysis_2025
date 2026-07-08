"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``core/calibration.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from calibration import X``) so
existing callers -- notably ``tests/`` and ``target_card_api.py`` -- keep
working unchanged. Prefer importing from ``core.calibration`` directly in
new code.
"""

from __future__ import annotations

from core.calibration import *  # noqa: F401,F403
from core.calibration import (  # noqa: F401
    CONTROL_PANEL_POSITIVE_GENES,
    KNOWN_DRUG_AXES,
    TCR_PROXIMAL_GENES,
    control_panel_calibration,
    drug_axis_enrichment,
    positive_control_recovery,
    qc_funnel,
    rank_stability,
    run_calibration,
    write_report,
)
