# API quickstart — GWT Target Card API

**Version:** 0.2.0 · **Style:** REST (JSON) · **Interactive docs:** `/docs` (Swagger UI) · `/redoc` (ReDoc)

> Research / hypothesis-generating tool — **NOT clinical software**. No diagnosis, treatment, dose, or
> efficacy output. This quickstart documents the **current REST API** as it exists today; auth,
> rate-limiting, versioning policy, GraphQL, and bulk-download packaging are north-star decisions still
> open (see `docs/server_northstar.md`).

## Conventions

- **Base URL:** wherever the FastAPI app is served (examples below use `$BASE`, e.g. `http://localhost:8000`).
- **Stable IDs:** genes resolve to Ensembl gene IDs; resolve a symbol/alias first if unsure (`/api/genes/resolve`).
- **`unknown` ≠ `0`:** a domain with no data is returned as `"unknown"`, never silently `0`.
- **Provenance:** built datasets carry `data_version` / `engine_version` / `schema_version`; external
  evidence carries `fetched_at`. Descriptive overlays (safety/genetics/concept/mechanism) never change
  the `readiness_call` / `overall_readiness_stage`.
- **Auth:** none today (internal / invited use). Do not expose publicly until the GWT dataset license is
  confirmed (`docs/data_governance_checklist.md`).

Check what's up first:

```bash
curl -s "$BASE/api/health"
# {"status":"ok","capabilities":{"build":"available", ... }}
```

## Endpoint groups

Browse the full, always-current list at `$BASE/docs`. The groups (OpenAPI tags):

| Group | What it serves |
|---|---|
| System | `/api/health` |
| Build | build/mint datasets; list datasets; build status |
| Target cards | cards, summaries, per-target detail, concept modules, search, exports, reports |
| Readiness | readiness calls, stages, red-flags, next-validation-step |
| Calibration | grade calibration vs the clinical benchmark axis |
| External evidence | cached ClinicalTrials / PubMed / bioRxiv / Open Targets per gene |
| Disease | disease translation, disease → targets |
| Genes | alias-tolerant gene resolution + three-state status |
| Population genetics | UK Biobank LoF burden hypotheses (population-level) |
| Uploads | researcher dataset upload → mapping → merge |
| Mechanism graph | Reactome + STRING target-centered graph |
| Concept profile (demo) | exploratory per-sample CD4 concept projection |

## Typical flow

### 1. Resolve / search a gene

```bash
curl -s "$BASE/api/genes/resolve?q=CD3E"
curl -s "$BASE/api/search?q=CD3&limit=10"
```

### 2. Find or build a dataset

```bash
curl -s "$BASE/api/datasets"                       # list existing built datasets
# Build a fresh one (see /docs for the RunRequest body schema, then):
curl -s -X POST "$BASE/api/run/target-card" -H 'content-type: application/json' -d '{ ... }'
curl -s "$BASE/api/status/<dataset_id>"            # poll build status
```

### 3. Explore a dataset's target cards

```bash
curl -s "$BASE/api/summary/<dataset_id>?top_n=50"
curl -s "$BASE/api/targets/<dataset_id>"                    # list cards
curl -s "$BASE/api/targets/<dataset_id>/<target_id>"       # one target's full detail
curl -s "$BASE/api/modules/<dataset_id>"                   # CD4 concept-module scores
curl -s "$BASE/api/readiness/<dataset_id>"                 # advance/validate/watchlist/deprioritize + reasons
```

### 4. Per-gene descriptive overlays (read-only, cached)

```bash
curl -s "$BASE/api/mechanism-graph/CD3E"                   # Reactome + STRING graph (+ evidence overlay)
curl -s "$BASE/api/population-hypothesis/PLCG1"            # UK Biobank LoF burden hypothesis
curl -s "$BASE/api/evidence/CD3E"                         # cached trials/literature/Open Targets
```

### 5. Export

```bash
curl -s "$BASE/api/exports/<dataset_id>?fmt=csv" -o cards.csv
```

## Python (`requests`)

```python
import requests

BASE = "http://localhost:8000"

# resolve a gene to its stable Ensembl ID
g = requests.get(f"{BASE}/api/genes/resolve", params={"q": "CD3E"}).json()

# pick a dataset and pull its readiness calls
datasets = requests.get(f"{BASE}/api/datasets").json()
dsid = datasets[0]["dataset_id"]
readiness = requests.get(f"{BASE}/api/readiness/{dsid}").json()

# a descriptive per-gene overlay (never feeds the readiness call)
mech = requests.get(f"{BASE}/api/mechanism-graph/CD3E").json()
```

## Notes for consumers

- Prefer resolving to Ensembl IDs before cross-referencing; symbols have aliases.
- Treat `"unknown"` as *not checked*, never as a negative/zero result.
- External-evidence endpoints are TTL-cached (30 days) and offline-batch-fetched — a gene not yet fetched
  returns an honest not-yet-available shape rather than blocking on a live fetch.
- The interactive `/docs` page is generated from the live app, so it is always the authoritative source
  for exact request/response schemas (including request bodies like `RunRequest` that are omitted here to
  avoid drift).
