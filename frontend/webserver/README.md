# CD4 Target Discovery Portal — web frontend

A React + TypeScript + Vite single-page app that presents the CD4 T-cell genome-scale
Perturb-seq target-discovery results as an interactive web server, for two personas:

- **Researcher workspace** — faceted target explorer with adjustable composite-priority
  weights, per-target dossier (real statistical evidence, concept-module membership, real
  tractability/disease/clinical-trial evidence, safety signals, population genetics, similar
  targets), multi-reviewer decision layer, and a side-by-side compare view.
- **Clinical-evidence lookup** — scope & guardrails, individual concept profile (M01–M20),
  disease × drug evidence match, and population-genetics constraint lookup.
- **Figure atlas** — 8 interactive Plotly figures (volcano, UMAP clustering, effect
  heatmap, cytokine regulators, Th1/Th2 polarization, GWAS enrichment, power, LoF burden).
  **This section still renders illustrative demo data** — see its in-app caption.
- **REST API reference.**

It replaces the previous Streamlit dashboard (`frontend/dashboard/`). Like that app, it is
an **independently developable, independently deployable** frontend — it must only ever talk
to the backend through the FastAPI service's HTTP/JSON API, never by importing backend Python.

## Data

The researcher/clinical side of the portal runs on **real data exported directly from this
repo's own pipeline** — not mock or illustrative values. `scripts/export_real_data.py` reads:

- `sources/target_tool_cache/<run-id>/target_cards.csv` — real per-target-per-condition
  statistics from the genome-scale CD4 Perturb-seq screen (effect size, FDR, DE gene counts,
  grade, cross-donor correlation, …).
- `src/3_DE_analysis/core/readiness.py` (`compute_readiness`) — the repo's own deterministic
  readiness engine, **run as-is, not reimplemented** — produces the real
  advance/validate/watchlist/deprioritize call, stage, red-flag overrides, rationale text and
  next-validation-step for every target.
- `src/3_DE_analysis/individual_concept_profile.py` (`load_concept_modules`) — the real M01–M20
  concept-module definitions and seed-gene membership.
- `src/3_DE_analysis/concept_annotation.py` (`annotate_targets`) — real "stimulation-gated"
  tagging.
- `sources/target_tool_cache/_evidence/<GENE>.json` — real, already-fetched Open Targets /
  ClinicalTrials.gov / PubMed snapshots (tractability, disease associations, safety
  liabilities, clinical trials, literature) — fetched for 21 genes only.
- `sources/target_tool_cache/_overlays/gnomad_constraint_seed.csv` — real gnomAD v4 LOEUF/pLI
  (16 genes).

**Target selection (7,236 genes):** every gene whose best-condition `statistical_evidence_grade`
is ≥ 2 (`MIN_GRADE` in the script), **union** every gene whose primary-condition
`readiness_call` is `advance` — a disclosed statistical threshold over the full 11,526-gene
screen, not an arbitrary curation (the 302 `advance` genes are, empirically, a subset of this
grade threshold here). Every one of these 7,236 targets gets real statistics, a real readiness
call, and real concept-module membership (where applicable). The deeper external-evidence
panels (disease associations, tractability flags, safety liabilities, clinical trials,
literature, gnomAD constraint) are populated only for the 21 genes the evidence cache covers —
the rest honestly render `unknown` / "no record indexed" in those panels rather than a
fabricated value. Gene "name" is standard HGNC nomenclature (hand-verified) for the 21
evidence-cache genes; every other gene displays its symbol as its name rather than a guessed
full name.

Anything a source didn't have is emitted as `null` / rendered as `unknown` — never a fabricated
value (see `unknown ≠ 0` below). The **figure atlas is the one section that still renders
synthetic, deterministically-generated series** — every figure's caption says so; a separate
effort is wiring that to real outputs.

Design discipline:

- **descriptive ≠ decision** — evidence and the human readiness call are kept separate; weights
  reorder your *view* of hypotheses, never the evidence or the rule-based readiness call.
- **unknown ≠ 0** — fields with no evidence read `unknown` with a coverage note, never a
  fabricated zero.
- every number carries a source/version stamp.

### Regenerating the dataset

```bash
# from the repo root
pip install pandas numpy pyyaml pyarrow
python3 frontend/webserver/scripts/export_real_data.py           # uses the cache if fresh
python3 frontend/webserver/scripts/export_real_data.py --force   # recompute readiness/annotation
```

`core.readiness.compute_readiness` and `concept_annotation.annotate_targets` run once over all
33,983 gene × condition rows (~15s) and are then **cached** to
`sources/target_tool_cache/_cache/{readiness_full,concept_annotated_full}.parquet` — committed
to the repo so nobody has to pay that recompute just to regenerate the frontend JSON. The cache
is trusted whenever it's newer than `target_cards.csv`; pass `--force` after changing
`readiness.py` / `concept_annotation.py` themselves.

Writes `public/real-dataset.json` (~18 MB / ~940 kB gzipped — see "Build" below for why this is
a runtime-fetched static asset rather than a JS import).

### Wiring to the live API (follow-up)

`src/data/dataset.ts`'s `loadDataset()` is the only seam: swap its `fetch('/real-dataset.json')`
for calls to the FastAPI endpoints under `src/3_DE_analysis/api/` (run the API and hit `/docs`
for the live OpenAPI schema) — ideally with server-side pagination/filtering given the target
count. The UI reads everything through the logic/selector layer in `src/lib/`, so only the data
layer needs to change. The figure atlas would separately need its synthetic generators
(`src/lib/drawFigure.ts`) replaced with the real notebook outputs.

## Develop

```bash
cd frontend/webserver
npm install
npm run dev        # http://localhost:5173
```

## Build

```bash
npm run build      # type-checks then emits a static bundle to dist/
npm run preview    # serve the production build locally
```

Plotly is code-split into a lazy chunk, so it only loads when the Figure atlas is opened. The
real dataset (~18 MB / ~940 kB gzipped at 7,236 genes) is **not** bundled into the JS — it's
fetched once at startup from `public/real-dataset.json` (see `src/data/dataset.ts`'s
`loadDataset()`, gated in `main.tsx` behind a small loading screen), which keeps the main JS
bundle itself at ~94 kB gzipped and lets the browser cache the data independently of app-code
deploys.

The **explorer table is virtualized** (`@tanstack/react-virtual`) — with 7,236 real targets,
only the rows scrolled into view are mounted as DOM nodes (~25–40 at a time regardless of list
length). The composite-priority weight sliders also throttle their store updates to one commit
per animation frame rather than one per native `input` event, so dragging a slider doesn't
trigger a full re-rank + re-render on every pixel of mouse movement.

## Stack

React 19 · TypeScript · Vite · Plotly (`plotly.js-dist-min`) · `@tanstack/react-virtual` ·
IBM Plex Sans/Mono (`@fontsource`). State lives in a small context store (`src/store/`) with
`cd4portal.*` `localStorage` persistence for weights, shortlist, and reviewer decisions.
