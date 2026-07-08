"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``resolve/search.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from gene_search import X``) so
existing callers -- notably ``tests/`` and ``target_card_api.py`` -- keep
working unchanged. Prefer importing from ``resolve.search`` directly in new
code.
"""

from __future__ import annotations

from resolve.search import *  # noqa: F401,F403
from resolve.search import MATCH_TYPE_RANK, search_genes  # noqa: F401
