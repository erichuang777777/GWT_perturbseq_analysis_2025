# Frontend

This directory is an **independently developable, independently deployable** frontend area for the
CD4 Perturb-seq target-discovery toolkit. It is isolated from `src/3_DE_analysis/` (the backend) by a
hard rule:

> **Everything under `frontend/` may only talk to the backend through the FastAPI service's HTTP/JSON
> API.** No file here imports Python modules from `src/3_DE_analysis/`, reads its files directly, or
> assumes it runs in the same process. The API's request/response shapes are the only contract.

This means the frontend can be developed, tested, redesigned, or replaced with a different stack
entirely (React, Vue, plain static + fetch, another Streamlit rewrite, …) without touching backend code,
and vice versa — the backend can change its internals freely as long as the API's JSON contract holds.

## Current contents

| Path | What it is | Status |
|---|---|---|
| `webserver/` | React + TypeScript + Vite single-page app (the CD4 Target Discovery Portal). Researcher workspace (target explorer, dossier, compare, multi-reviewer decision layer), clinical-evidence lookup, an interactive Plotly figure atlas, and a REST API reference. Ported from the Claude Design prototype. The researcher/clinical side renders **real data** exported from this repo's own pipeline: real statistics + a real readiness call for **660 genes** (every gene at grade ≥ 3 or with an `advance` call, out of the full 11,526-gene screen), with deeper external evidence (disease associations, tractability, safety, clinical trials, literature, gnomAD) populated for the 21 genes that evidence cache covers and honestly `unknown` elsewhere — see `webserver/README.md` for exactly which files feed what. The figure atlas still renders illustrative demo data. | Working (real data; figure atlas still illustrative) |

The previous Streamlit dashboard (`dashboard/`) has been replaced by `webserver/`. To recover it,
check out any commit before this one.

### A note on the isolation rule above

`webserver/scripts/export_real_data.py` is an **offline, build-time export step**, not part of the
running frontend — it's invoked manually from the repo root (see `webserver/README.md`) and writes
a static JSON file the frontend imports at build time. The compiled frontend itself still never
imports `src/3_DE_analysis/` or touches the repo's data files at runtime; its only *runtime*
contract remains the API's HTTP/JSON shapes, same as before. Re-run the export script whenever the
underlying pipeline output changes.

## Running the webserver standalone

```bash
cd frontend/webserver
npm install
npm run dev          # http://localhost:5173 — real data baked in, no backend needed to browse it
```

To wire it to the live backend instead of the exported snapshot, start the FastAPI service and
replace the static import in `webserver/src/data/dataset.ts` with `fetch` calls against
`GWT_API_BASE` (see `webserver/README.md`):

```bash
# from repo root, in a separate terminal
uvicorn target_card_api:app --app-dir src/3_DE_analysis
```

The compiled frontend still never touches the repo's data files, `sources/`, or `metadata/`
directly at runtime — its only contract with the backend is the API's HTTP/JSON shapes.

## Adding a new frontend (or replacing this one)

1. Create a new subdirectory here (e.g. `frontend/web/`) with its own dependency manifest and README.
2. Talk only to the API's documented endpoints (see `src/3_DE_analysis/target_card_api.py`'s route
   definitions, or run the API and hit `/docs` for the live OpenAPI schema).
3. Do not import anything from `src/3_DE_analysis/` — if a piece of logic seems to need that, it belongs
   in a new API endpoint, not duplicated in the frontend.
4. Point it at `GWT_API_BASE` (or an equivalent env var) so it works against any backend instance
   (local dev, a teammate's instance, a future deployment) without code changes.

This keeps the isolation guarantee in `docs/architecture_refactor_plan.md` §2 ("dependency always points
inward") intact: nothing inside `src/3_DE_analysis/` ever depends on anything in `frontend/`, so a
frontend rewrite, a broken `npm install`, or an entirely different framework choice can never break card
building, scoring, or the API itself.
