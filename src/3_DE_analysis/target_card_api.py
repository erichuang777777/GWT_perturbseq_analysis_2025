"""Backward-compatibility shim (architecture refactor Phase 2).

The real FastAPI app implementation moved to ``api/app.py`` (see
``docs/architecture_refactor_plan.md`` §3/§5). This module re-exports it
under the original flat import path (``from target_card_api import X`` /
``import target_card_api as api``) so existing callers -- notably
``tests/test_mechanism_graph.py``, which builds a ``TestClient(api.app)`` --
keep working unchanged. Prefer importing from ``api.app`` directly in new
code.

Caveat (module-attribute mutation): a handful of module-level "constant"
attributes (e.g. ``PATHWAY_CACHE_DIR``) are only *read* correctly through
this shim -- they are NOT live-linked back to ``api.app``, so
``monkeypatch.setattr(target_card_api, "PATHWAY_CACHE_DIR", ...)`` would
silently have no effect on request handling (Python resolves a function's
bare global names against the module it was *defined* in, i.e. ``api.app``,
not wherever it's re-exported to). Test code that needs to override such a
value for one request must monkeypatch ``api.app`` (or the router's own
module once Phase 4 splits it out) directly, not this shim -- see
``tests/test_mechanism_graph.py::test_mechanism_graph_api_endpoint_reads_real_cache_dir``.
"""

from __future__ import annotations

from api.app import *  # noqa: F401,F403
from api.app import (  # noqa: F401
    CACHE_ROOT,
    CARD_SCHEMA_VERSION,
    CRE_ELEMENTS_PATH,
    DATASET_VERSION,
    DEFAULT_BENCH,
    DEFAULT_BROAD_EFFECT,
    DEFAULT_BUILD_SCRIPT,
    DEFAULT_DE,
    DEFAULT_ESSENTIALS,
    DEFAULT_GUIDE,
    DEFAULT_LIB,
    DEFAULT_SAMPLE_META,
    DISEASE_ASSOCIATIONS_PATH,
    ENGINE_VERSION,
    EVIDENCE_CACHE_DIR,
    GENE_LISTS_DIR,
    MAX_EVIDENCE_GENES,
    PATHWAY_CACHE_DIR,
    ROOT,
    SEED_MODULES,
    SRC,
    VARIANT_CRE_LINKS_PATH,
    app,
)
