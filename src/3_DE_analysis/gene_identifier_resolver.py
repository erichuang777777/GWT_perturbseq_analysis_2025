"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``resolve/resolver.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from gene_identifier_resolver import
X``) so existing callers -- notably ``tests/`` and ``gene_search.py``/
``target_card_api.py`` -- keep working unchanged. Prefer importing from
``resolve.resolver`` directly in new code.
"""

from __future__ import annotations

from resolve.resolver import *  # noqa: F401,F403
from resolve.resolver import (  # noqa: F401
    DEFAULT_LIBRARY_PATH,
    RESULT_STATUS_STATES,
    GeneResolver,
    build_alias_table,
    load_resolver,
    result_status,
)
