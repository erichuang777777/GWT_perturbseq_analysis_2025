"""Data contracts shared across module boundaries (architecture refactor Phase 0).

A contract here is a column/field list plus a validator -- not a class
hierarchy. Any card-building implementation that produces a DataFrame
satisfying ``card_schema.validate_cards`` can be swapped in for
``build_target_cards.build_cards_frame`` without any downstream consumer
(``calibration.py``, ``readiness_engine.py``, ``generate_target_report.py``,
the API, the dashboard) needing to change. See
``docs/architecture_refactor_plan.md`` §4.2.
"""

from __future__ import annotations

from . import card_schema

__all__ = ["card_schema"]
