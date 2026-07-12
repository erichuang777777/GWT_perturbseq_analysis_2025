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
  ClinicalTrials.gov / PubMed snapshots (Open-Targets-vocabulary tractability, disease
  associations, Open-Targets-curated safety liabilities, clinical trials, literature) —
  fetched for 21 genes only (these three sources need live API calls; see "Widening the
  21-gene evidence cache" below for why the rest aren't fetched yet).
- `sources/target_tool_cache/_overlays/gnomad_v4.1_constraint_full.csv` — real gnomAD v4.1
  LOEUF/pLI, genome-wide (17,473 genes; MANE Select protein-coding transcripts, downloaded
  directly from gnomAD's public release bucket) — **94% of the 7,249 selected genes** have a
  real value here. Supersedes the older 16-gene `gnomad_constraint_seed.csv` for this export
  (that file is kept only because a backend test pins its exact values).
- `src/3_DE_analysis/evidence/safety_overlay.py`'s `load_membrane_tractability_overlay()` /
  `load_gtex_safety_overlay()` — real ADC-derived membrane/surface-protein/druggability overlay
  (`docs/mvp-research/adc_overlay_gwt_overlap_full.csv`, **50% of selected genes**) and real
  GTEx per-tissue expression-breadth overlay (`gtex_per_tissue.parquet`, **47% of selected
  genes**). Both are passed into `compute_readiness()` — it already accepted these parameters;
  this export previously never supplied them — which upgrades `tractability_score`/
  `tractability_modality` and adds a real `safety_window_score` + `composite_safety_liability`
  wherever the gene's Ensembl id is covered. The raw membrane-overlay flags are additionally
  surfaced as their own `membraneOverlay` field (Dossier's "Membrane / ADC overlay" card) — a
  different vocabulary than Open Targets' tractability buckets, so the two are never merged.
- `src/6_functional_interaction/results/disease_gene_associations_detailed.csv` — a real Open
  Targets genetic-association export already produced by prior repo research
  (`evidence/disease.py`), 13 autoimmune/inflammatory indications, **zero live fetch needed**.
  Merged into the same `diseases` field as the 21-gene live evidence cache above (same
  underlying data provider, same 0–1 score scale), deduplicated by disease name, each entry
  tagged with which of the two sources it came from — covers **1,266 of the 7,249 selected
  genes**, up from 15 before this file was wired in.
- `src/3_DE_analysis/evidence/population.py` (`load_burden_estimates`,
  `build_population_hypothesis_card`) + `src/8_lymphocyte_counts_LoF/input/
  Backman_LymphocyteCount_fullFeatures.per_gene_estimates.tsv` — real UK Biobank exome-wide
  rare-LoF-variant lymphocyte-count burden estimates (Backman et al. 2021), entirely local
  (**zero network calls**), registered in `evidence/registry.py` but never previously wired
  into this export. Covers **7,140 of the 7,249 selected genes (98.5%)** — a population-level
  statistical association ("if a population carries a LoF variant in this gene, does
  lymphocyte count shift on average"), independent of and complementary to gnomAD's constraint
  signal (gnomAD: population tolerance for losing the gene; this: the measured phenotypic
  consequence). Surfaced in Dossier's "Population genetics" card below the gnomAD panel.

**Target selection (7,249 genes):** every gene whose best-condition `statistical_evidence_grade`
is ≥ 2 (`MIN_GRADE` in the script), **union** every gene (any grade) whose primary-condition
`readiness_call` is `advance` or `watchlist` — a disclosed statistical threshold over the full
11,526-gene screen, not an arbitrary curation. Below `MIN_GRADE`, `deprioritize` calls (4,277 of
the remaining 4,290 lower-grade genes) are intentionally excluded; only the 13 lower-grade genes
that still call `watchlist` are added back in, alongside the 302 `advance` genes (already a
subset of the grade threshold). Every one of these 7,249 targets gets real statistics, a real
readiness call, and real concept-module membership (where applicable).

External-evidence coverage is **not uniform across panels** — each source was integrated on its
own real coverage, never padded to match another:

| Panel | Source | Coverage of the 7,249 selected genes |
|---|---|---|
| gnomAD LOEUF/pLI, constraint tier | gnomAD v4.1 genome-wide download | **94%** (6,834 genes) |
| Lymphocyte-count LoF burden | UK Biobank (Backman et al. 2021), local file | **98.5%** (7,140 genes) |
| Tractability score/modality, safety window, composite safety liability | ADC membrane overlay + GTEx overlay (both wired into `compute_readiness`) | **45–50%** (~3,300–3,600 genes) |
| Disease associations | 21-gene live Open Targets evidence cache **+** local 13-indication export, merged | **17.5%** (1,266 genes) |
| Open-Targets-vocabulary tractability flags, Open-Targets safety liabilities, clinical trials, literature | Open Targets / ClinicalTrials.gov / PubMed evidence cache | **21 genes** — these need live API calls per gene; see "Widening the 21-gene evidence cache" below |

Every panel honestly renders `unknown` / "no record indexed" / "gene not in the ADC × GWT
overlap overlay" wherever the gene isn't covered by that panel's specific source — never a
fabricated value, and never backfilled from a different panel's coverage. Gene "name" is
standard HGNC nomenclature (hand-verified) for the 21 evidence-cache genes; every other gene
displays its symbol as its name rather than a guessed full name.

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

Writes `public/real-dataset.json` (~24.4 MB / ~1.5 MB gzipped — see "Build" below for why this is
a runtime-fetched static asset rather than a JS import).

### Widening the 21-gene evidence cache (disease/trials/literature)

The Open Targets / ClinicalTrials.gov / PubMed evidence cache (`sources/target_tool_cache/_evidence/`)
still covers only 21 genes because, unlike the gnomAD/ADC/GTEx overlays above, widening it needs
live calls to three external APIs (no API key needed for any of them):

```bash
cd src/3_DE_analysis
python3 -m evidence.external_cache GENE1 GENE2 ... --cache-dir ../../sources/target_tool_cache/_evidence
```

This is the exact code path that already produced the current 21 genes — same honest
degrade-to-`unavailable` contract, safe to re-run. See
`docs/frontend_evidence_coverage_expansion_plan.md` for the full plan, including a suggested
Tier 1 batch (the 621 genes currently called `advance`/`validate` — the ones a user is most
likely to actually open) and why this step can't run inside every environment (some sandboxed
network policies block `clinicaltrials.gov` / `api.platform.opentargets.org` /
`eutils.ncbi.nlm.nih.gov`, verified with `curl` at the time that plan was written — run it
wherever those three domains are reachable, then commit the new `_evidence/*.json` files).

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
real dataset (~24.4 MB / ~1.5 MB gzipped at 7,249 genes) is **not** bundled into the JS — it's
fetched once at startup from `public/real-dataset.json` (see `src/data/dataset.ts`'s
`loadDataset()`, gated in `main.tsx` behind a small loading screen), which keeps the main JS
bundle itself at ~94 kB gzipped and lets the browser cache the data independently of app-code
deploys.

The **explorer table is virtualized** (`@tanstack/react-virtual`) — with 7,249 real targets,
only the rows scrolled into view are mounted as DOM nodes (~25–40 at a time regardless of list
length). The composite-priority weight sliders also throttle their store updates to one commit
per animation frame rather than one per native `input` event, so dragging a slider doesn't
trigger a full re-rank + re-render on every pixel of mouse movement.

## Stack

React 19 · TypeScript · Vite · Plotly (`plotly.js-dist-min`) · `@tanstack/react-virtual` ·
IBM Plex Sans/Mono (`@fontsource`). State lives in a small context store (`src/store/`) with
`cd4portal.*` `localStorage` persistence for weights, shortlist, and reviewer decisions.
