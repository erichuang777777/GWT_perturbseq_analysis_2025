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

# --- OpenAPI metadata (data-portal north-star, Phase 1: decision-invariant docs
# enrichment; see docs/server_northstar.md §5). This ONLY improves the /docs +
# /redoc pages and the generated OpenAPI schema -- it changes no response body,
# so no API consumer's payload shape changes. It commits to none of the four
# open product decisions (REST-vs-GraphQL / UI / external scope / bulk download).
API_DESCRIPTION = """\
Programmatic access to the CD4 T-cell Perturb-seq **target-discovery** toolkit:
prioritized target cards, readiness calls, CD4 immune concept profiles,
mechanism graphs, safety/tractability overlays, and integrated external
evidence, built from a CRISPRi knockdown screen in primary human CD4+ T cells.

**This is a research / hypothesis-generating tool, NOT clinical software.**
It does not output diagnosis, treatment, dose, or efficacy predictions.

Data discipline reflected in every response:
* `unknown` != `0` — a missing evidence domain is reported as `unknown`, never
  silently scored 0.
* Descriptive evidence (safety/genetics/concept/mechanism overlays) is kept
  causally separate from the final `readiness_call` / `overall_readiness_stage`.
* Provenance and version fields accompany built datasets (`data_version`,
  `engine_version`, `schema_version`); external evidence carries `fetched_at`.

See `GET /api/health` for per-capability availability. Interactive docs live at
`/docs` (Swagger UI) and `/redoc` (ReDoc)."""

# Tag groups organize the ~30 endpoints in /docs + /redoc by resource area.
OPENAPI_TAGS = [
    {"name": "System", "description": "Health and per-capability availability."},
    {"name": "Build", "description": "Mint/build target-card datasets from the reference screen or an upload."},
    {"name": "Target cards", "description": "Target cards, dataset summaries, per-target detail, CD4 concept module scores, search, and exports."},
    {"name": "Readiness", "description": "Readiness calls (advance/validate/watchlist/deprioritize), R0-R3 stages, red-flag overrides, and next-validation-step."},
    {"name": "Calibration", "description": "Calibration of statistical grades against the clinical benchmark axis."},
    {"name": "External evidence", "description": "Cached ClinicalTrials.gov / PubMed / bioRxiv / Open Targets evidence per gene (offline batch-fetched, TTL-cached)."},
    {"name": "Disease", "description": "Disease-name translation and disease -> associated-target lookups."},
    {"name": "Genes", "description": "Alias-tolerant gene resolution to stable Ensembl IDs and three-state query status."},
    {"name": "Population genetics", "description": "UK Biobank rare loss-of-function burden hypotheses (population-level, with confidence intervals) -- not patient-level predictions."},
    {"name": "Uploads", "description": "Staging-first researcher dataset upload: column-mapping wizard, preview, approve, merge-to-cards."},
    {"name": "Mechanism graph", "description": "Target-centered Reactome pathway + STRING interaction graph, overlaid with this platform's own evidence (descriptive only)."},
    {"name": "Concept profile (demo)", "description": "Exploratory individual-sample concept projection onto the 20 CD4 immune concept modules. Research demo, NOT medical software; request-only, never persisted."},
    {"name": "Clinical evidence (research use)", "description": "Disease x drug evidence-matching: whether a gene has a known drug, and whether that drug has actually been trialled for a specific disease. Evidence-matching only, NOT a treatment recommendation; live-queried (Open Targets + ClinicalTrials.gov), never persisted."},
    {"name": "Meta", "description": "Coverage-at-a-glance for the sparse descriptive overlays (gnomAD/GTEx/disease-association/LINCS), computed from the loaded reference tables at request time -- never a number copied from documentation."},
]

app = FastAPI(
    title="GWT Target Card API",
    version="0.2.0",
    summary="CD4 T-cell Perturb-seq target-discovery data API (research use only).",
    description=API_DESCRIPTION,
    openapi_tags=OPENAPI_TAGS,
    contact={"name": "GWT Perturb-seq target toolkit", "url": "https://github.com/erichuang777777/GWT_perturbseq_analysis_2025"},
    license_info={"name": "Toolkit code: MIT (see LICENSE). Underlying GWT dataset: license TBD -- internal-research-use-only until confirmed (see docs/data_governance_checklist.md)."},
)


@app.middleware("http")
async def _stamp_version_headers(request, call_next):
    """Attach engine/schema/API version provenance to EVERY response as headers
    (north-star 支柱二 資料明確). Headers are the idiomatic, non-breaking way to
    expose response metadata in a REST API (the user-confirmed API style): they
    reach every endpoint -- including the bare-list responses whose JSON body
    can't gain a provenance key without a breaking envelope change -- without
    altering any existing response body. A consumer can read what release served
    any call; the per-dataset metadata.json stays authoritative per build.
    """
    response = await call_next(request)
    response.headers["X-API-Version"] = app.version
    response.headers["X-Engine-Version"] = str(ENGINE_VERSION)
    response.headers["X-Schema-Version"] = str(CARD_SCHEMA_VERSION)
    return response


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
    "upload_ui": "api.routers.upload_ui",
    "mechanism": "api.routers.mechanism",
    "individual_concept": "api.routers.individual_concept",
    "signed_module_effect": "api.routers.signed_module_effect",
    "disease_drug": "api.routers.disease_drug",
    "meta": "api.routers.meta",
}

# Each router declares its own OpenAPI tag (a pretty group name) on its
# APIRouter(tags=[...]); those tags are described in OPENAPI_TAGS above so
# /docs + /redoc render one titled, documented group per resource area.

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
        app.include_router(module.router)  # each router sets its own OpenAPI tag (see _ROUTER_TAGS)
        _CAPABILITY_STATUS[name] = "available"
    except Exception as exc:  # noqa: BLE001 -- intentional broad error boundary, see docstring
        _CAPABILITY_STATUS[name] = f"degraded: {type(exc).__name__}: {exc}"


for _name, _module_path in _ROUTER_MODULES.items():
    _load_router(_name, _module_path)


@app.get("/api/health", tags=["System"], summary="Overall status, per-capability availability, and engine/schema versions")
def health() -> Dict[str, Any]:
    """Overall + per-capability (per-router) availability, plus API/engine versions.

    ``status`` stays ``"ok"`` (the pre-Phase-4 response shape) when every
    router loaded cleanly, so existing callers checking only ``status``
    are unaffected; ``capabilities`` and ``versions`` are purely additive.

    ``versions`` surfaces the same provenance fields stamped on every built
    dataset -- so an API consumer can tell which engine/schema/dataset release
    they are querying against without building a dataset first (north-star
    支柱二 資料明確 / 支柱三 API 可查, ``docs/server_northstar.md``). These are
    server-wide defaults; a specific dataset's ``metadata.json`` remains the
    authoritative per-build record.
    """
    overall = "ok" if all(v == "available" for v in _CAPABILITY_STATUS.values()) else "degraded"
    return {
        "status": overall,
        "capabilities": dict(_CAPABILITY_STATUS),
        "versions": {
            "api": app.version,
            "engine_version": ENGINE_VERSION,
            "dataset_version": DATASET_VERSION,
            "schema_version": CARD_SCHEMA_VERSION,
        },
    }
