"""FastAPI app assembly (architecture refactor Phase 4, §4.1/§4.3④).

``target_card_api.py`` (990+ lines) used to define every route directly on
a single module-level ``app``. It is now split into one router per resource
area under ``api/routers/`` (build, cards, readiness, calibration, evidence,
disease, genes, population, imports, mechanism) + ``api/deps.py`` (shared
path/version constants, cached resolvers/overlays, generic per-dataset
helpers). This module's only job is assembly: create the ``FastAPI`` app,
import each router, and mount it.

Each router is imported inside its own ``try/except`` (see ``_load_router``
below) so one router's import failure (a missing optional dependency, a
bug introduced in one resource area) cannot prevent the rest of the API
from coming up -- the same "one broken edge doesn't take down the core"
principle as the readiness-engine decoupling in Phase 3, applied to the API
layer itself (§4.3④). ``GET /api/health`` reports per-capability
available/degraded status so a caller (or the dashboard) can tell exactly
which resource areas are up.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict

from fastapi import FastAPI

from api.deps import (  # noqa: F401 -- re-exported for target_card_api.py's back-compat shim
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
)

app = FastAPI(title="GWT Target Card API", version="0.1.0")

# name -> module path, one entry per resource area (§4.1). Match the actual
# endpoint groupings in the original target_card_api.py, not a forced exact
# match to the plan doc's illustrative router list.
_ROUTER_MODULES: Dict[str, str] = {
    "build": "api.routers.build",
    "cards": "api.routers.cards",
    "readiness": "api.routers.readiness",
    "calibration": "api.routers.calibration",
    "evidence": "api.routers.evidence",
    "disease": "api.routers.disease",
    "genes": "api.routers.genes",
    "population": "api.routers.population",
    "imports": "api.routers.imports",
    "mechanism": "api.routers.mechanism",
}

# name -> "available" | "degraded: <reason>". Populated below as each
# router is (attempted to be) loaded; read by GET /api/health.
_CAPABILITY_STATUS: Dict[str, str] = {}


def _load_router(name: str, module_path: str) -> None:
    """Import one router module and mount it, isolating any failure to this one entry.

    A bug or missing dependency in one resource area's router must not
    prevent every other router (or the app itself) from starting -- so this
    catches any exception, records it as this capability's degraded status,
    and moves on. The broad ``except Exception`` is deliberate here (this is
    exactly the "error boundary" the plan doc calls for, §4.3④), not
    sloppiness -- narrower exception types can't be enumerated up front
    across ten independently-maintained router modules.
    """
    try:
        module = importlib.import_module(module_path)
        app.include_router(module.router)
        _CAPABILITY_STATUS[name] = "available"
    except Exception as exc:  # noqa: BLE001 -- intentional broad error boundary, see docstring
        _CAPABILITY_STATUS[name] = f"degraded: {type(exc).__name__}: {exc}"


for _name, _module_path in _ROUTER_MODULES.items():
    _load_router(_name, _module_path)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    """Overall + per-capability (per-router) availability.

    ``status`` stays ``"ok"`` (the pre-Phase-4 response shape) when every
    router loaded cleanly, so existing callers checking only ``status``
    are unaffected; ``capabilities`` is new and purely additive.
    """
    overall = "ok" if all(v == "available" for v in _CAPABILITY_STATUS.values()) else "degraded"
    return {"status": overall, "capabilities": dict(_CAPABILITY_STATUS)}
