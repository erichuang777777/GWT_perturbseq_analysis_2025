"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``resolve/cre.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from cre_schema import X``) so
existing callers -- notably ``tests/`` and ``target_card_api.py`` -- keep
working unchanged. Prefer importing from ``resolve.cre`` directly in new code.
"""

from __future__ import annotations

from resolve.cre import *  # noqa: F401,F403
from resolve.cre import (  # noqa: F401
    CRE_COLUMNS,
    VARIANT_CRE_LINK_COLUMNS,
    cre_for_gene,
    empty_cre_table,
    empty_variant_cre_link_table,
    load_cre_elements,
    load_variant_cre_links,
)
