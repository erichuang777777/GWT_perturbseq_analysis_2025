"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``evidence/safety_overlay.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from safety_overlay import X``) so
existing callers -- notably ``tests/test_safety_overlay.py`` and
``target_card_api.py`` -- keep working unchanged. Prefer importing from
``evidence.safety_overlay`` directly in new code.
"""

from __future__ import annotations

from evidence.safety_overlay import *  # noqa: F401,F403
from evidence.safety_overlay import (  # noqa: F401
    BREADTH_BROAD_THRESHOLD,
    GNOMAD_REQUIRED_COLUMNS,
    GTEX_REQUIRED_COLUMNS,
    LOEUF_LOSS_INTOLERANT_THRESHOLD,
    MEMBRANE_OVERLAY_REQUIRED_COLUMNS,
    UNKNOWN,
    composite_safety_liability,
    gnomad_flag_from_constraint,
    load_gnomad_constraint_overlay,
    load_gtex_safety_overlay,
    load_membrane_tractability_overlay,
    safety_window_from_gtex,
    tractability_from_membrane_overlay,
)
