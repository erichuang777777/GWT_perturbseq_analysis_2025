"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``core/readiness.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from readiness_engine import X``) so
existing callers -- notably ``tests/`` and ``target_card_api.py`` -- keep
working unchanged. Prefer importing from ``core.readiness`` directly in new
code.

Note (Phase 3): ``core/readiness.py`` no longer imports the evidence layer
directly -- see that module's docstring for the injected-evidence contract.
"""

from __future__ import annotations

from core.readiness import *  # noqa: F401,F403
from core.readiness import (  # noqa: F401
    CALL_ORDER,
    STAGE_TO_CALL,
    UNKNOWN,
    compute_readiness,
    load_overlays,
    readiness_summary,
)
