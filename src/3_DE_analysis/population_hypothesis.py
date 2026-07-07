"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``evidence/population.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from population_hypothesis import
X``) so existing callers -- notably ``tests/test_population_hypothesis.py``
and ``target_card_api.py`` -- keep working unchanged. Prefer importing from
``evidence.population`` directly in new code.
"""

from __future__ import annotations

from evidence.population import *  # noqa: F401,F403
from evidence.population import (  # noqa: F401
    BURDEN_REQUIRED_COLUMNS,
    CAVEAT_TEXT,
    TRAIT_PATHS,
    build_population_hypothesis_card,
    empty_burden_table,
    load_burden_estimates,
)
