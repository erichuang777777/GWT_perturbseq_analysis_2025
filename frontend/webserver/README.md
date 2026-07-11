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

**Target selection (660 genes):** every gene whose best-condition `statistical_evidence_grade`
is ≥ 3, **union** every gene whose primary-condition `readiness_call` is `advance` — a disclosed
statistical threshold over the full 11,526-gene screen, not an arbitrary curation (the 302
`advance` genes are, empirically, a subset of the 660 grade≥3 genes here). Every one of these
660 targets gets real statistics, a real readiness call, and real concept-module membership
(where applicable). The deeper external-evidence panels (disease associations, tractability
flags, safety liabilities, clinical trials, literature, gnomAD constraint) are populated only
for the 21 genes the evidence cache covers — the other ~640 honestly render `unknown` / "no
record indexed" in those panels rather than a fabricated value. Gene "name" is standard HGNC
nomenclature (hand-verified) for the 21 evidence-cache genes; every other gene displays its
symbol as its name rather than a guessed full name.

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
pip install pandas numpy pyyaml
python3 frontend/webserver/scripts/export_real_data.py
```

Writes `src/data/generated/real-dataset.json`, which `src/data/dataset.ts` imports directly.

### Wiring to the live API (follow-up)

`src/data/dataset.ts` is the only seam: swap its static JSON import for `fetch` calls to the
FastAPI endpoints under `src/3_DE_analysis/api/` (run the API and hit `/docs` for the live
OpenAPI schema). The UI reads everything through the logic/selector layer in `src/lib/`, so
only the data layer needs to change. The figure atlas would separately need its synthetic
generators (`src/lib/drawFigure.ts`) replaced with the real notebook outputs.

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
main bundle (including the ~1.7 MB / ~125 kB-gzipped real dataset) is ~190 kB gzipped.

## Stack

React 19 · TypeScript · Vite · Plotly (`plotly.js-dist-min`) · IBM Plex Sans/Mono
(`@fontsource`). State lives in a small context store (`src/store/`) with `cd4portal.*`
`localStorage` persistence for weights, shortlist, and reviewer decisions.
