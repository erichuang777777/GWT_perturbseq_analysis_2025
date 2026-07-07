"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``evidence/pathway_cache.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from pathway_network_cache import X``
/ ``import pathway_network_cache as pnc``) so existing callers -- notably
``tests/test_pathway_network_cache.py`` and ``tests/test_mechanism_graph.py``,
which reach into the private ``_cache_path`` helper via module-attribute
access -- keep working unchanged. Prefer importing from
``evidence.pathway_cache`` directly in new code.
"""

from __future__ import annotations

from evidence.pathway_cache import *  # noqa: F401,F403

# Explicit re-export of underscore-prefixed helpers -- see
# external_evidence_cache.py's shim docstring for why this is necessary.
from evidence.pathway_cache import _cache_path, _is_stale, _now, _unavailable  # noqa: F401
