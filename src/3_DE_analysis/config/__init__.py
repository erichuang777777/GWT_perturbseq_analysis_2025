"""Single source of truth for paths, numeric thresholds, and version strings (architecture refactor Phase 0).

Before this module existed, the same values were defined independently in
multiple files (e.g. the cross-donor/cross-guide correlation gates 0.2/0.3
were hardcoded separately in ``build_target_cards.py``, ``calibration.py``,
and ``readiness_engine.py`` -- see ``docs/architecture_refactor_plan.md``
§1). Every existing module still exposes its own constant with the same name
for backward compatibility (e.g. ``build_target_cards.KD_NOT_MEASURABLE_EXPRESSION_FLOOR``
still works), but now re-exports the value from here instead of defining it
independently, so there is exactly one place to change a threshold, a path,
or a version string.

This package is additive only: importing it does not change any computed
value or behavior. See ``docs/architecture_refactor_plan.md`` §5, Phase 0.
"""

from __future__ import annotations

from . import settings, thresholds, versions

__all__ = ["settings", "thresholds", "versions"]
