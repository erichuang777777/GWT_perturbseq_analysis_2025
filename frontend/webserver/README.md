# CD4 Target Discovery Portal — web frontend

A React + TypeScript + Vite single-page app that presents the CD4 T-cell genome-scale
Perturb-seq target-discovery results as an interactive web server, for two personas:

- **Researcher workspace** — faceted target explorer with adjustable composite-priority
  weights, per-target dossier (statistical evidence, immune-concept profile, tractability,
  KO perturbation signature, safety window, population genetics, similar targets),
  multi-reviewer decision layer, and a side-by-side compare view.
- **Clinical-evidence lookup** — scope & guardrails, individual concept profile (M01–M20),
  disease × drug evidence match, and population-genetics constraint lookup.
- **Figure atlas** — 8 interactive Plotly figures (volcano, UMAP clustering, effect
  heatmap, cytokine regulators, Th1/Th2 polarization, GWAS enrichment, power, LoF burden).
- **REST API reference.**

It replaces the previous Streamlit dashboard (`frontend/dashboard/`). Like that app, it is
an **independently developable, independently deployable** frontend — it must only ever talk
to the backend through the FastAPI service's HTTP/JSON API, never by importing backend Python.

## Data

This is a faithful port of the exported Claude Design prototype and currently runs on the
**deterministic mock dataset** baked into `src/data/` (15 real T-cell targets, the 20 concept
modules, drug/trial precedents, gnomAD constraint, and figure series). Nothing here calls the
live API yet.

Design discipline carried over from the prototype:

- **descriptive ≠ decision** — evidence and the human readiness call are kept separate; weights
  reorder your *view* of hypotheses, never the evidence or the rule-based readiness call.
- **unknown ≠ 0** — fields with no evidence read `unknown` with a coverage note, never a
  fabricated zero.
- every number carries a source/version stamp.

### Wiring to the real API (follow-up)

Swap the static modules in `src/data/` (`targets.ts`, `reference.ts`) and the deterministic
generators in `src/lib/` for `fetch` calls to the FastAPI endpoints under
`src/3_DE_analysis/api/` (run the API and hit `/docs` for the live OpenAPI schema). The UI reads
everything through the logic/selector layer, so only the data layer needs to change.

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

Plotly is code-split into a lazy chunk, so it only loads when the Figure atlas is opened; the
initial bundle is ~90 kB gzipped.

## Stack

React 19 · TypeScript · Vite · Plotly (`plotly.js-dist-min`) · IBM Plex Sans/Mono
(`@fontsource`). State lives in a small context store (`src/store/`) with `cd4portal.*`
`localStorage` persistence for weights, shortlist, and reviewer decisions.
