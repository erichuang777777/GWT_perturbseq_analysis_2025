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
| `dashboard/` | The existing Streamlit dashboard (`target_card_dashboard.py`), moved here from `src/3_DE_analysis/`. Talks to the API exclusively via `requests` + `GWT_API_BASE`. | Working, unchanged behavior — moved location only |

## Running the dashboard standalone

```bash
# 1. Start the backend API (from repo root)
uvicorn target_card_api:app --app-dir src/3_DE_analysis

# 2. In a separate terminal, install and run the frontend independently
pip install -r frontend/dashboard/requirements.txt
GWT_API_BASE=http://127.0.0.1:8000 streamlit run frontend/dashboard/target_card_dashboard.py
```

`GWT_API_BASE` defaults to `http://127.0.0.1:8000` if unset (see `target_card_dashboard.py`'s
`API_BASE` constant). Nothing else needs to be configured — this frontend never touches the repo's data
files, `sources/`, or `metadata/` directly.

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
