"""Backward-compatibility shim (architecture refactor Phase 2).

The real implementation moved to ``evidence/external_cache.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from external_evidence_cache import
X`` / ``import external_evidence_cache as eec``) so existing callers --
notably ``tests/test_disease_drug_evidence.py``, which reaches into the
private ``_open_targets_resolve_ensembl_id`` helper via module-attribute
access -- keep working unchanged. Prefer importing from
``evidence.external_cache`` directly in new code.
"""

from __future__ import annotations

from evidence.external_cache import *  # noqa: F401,F403

# Explicit re-export of underscore-prefixed helpers: `from module import *`
# never pulls in leading-underscore names, but tests access some of these via
# `import external_evidence_cache as eec; eec._name(...)` module-attribute
# access, which requires the name to actually exist in this shim's namespace.
from evidence.external_cache import (  # noqa: F401
    _cache_path,
    _clinicaltrials_count_for_drug,
    _drug_class,
    _is_stale,
    _now,
    _open_targets_known_drugs,
    _open_targets_resolve_ensembl_id,
    _unavailable,
)
