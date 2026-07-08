"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``evidence/mechanism_graph.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from mechanism_graph import X`` /
``import mechanism_graph as mg``) so existing callers -- notably
``tests/test_mechanism_graph.py`` and ``target_card_api.py`` -- keep working
unchanged. Prefer importing from ``evidence.mechanism_graph`` directly in
new code.
"""

from __future__ import annotations

from evidence.mechanism_graph import *  # noqa: F401,F403
from evidence.mechanism_graph import PathLike, build_mechanism_graph  # noqa: F401
