# MODULE ISOLATION POLICY — Perturbase Platform

**Repository:** `erichuang777777/GWT_perturbseq_analysis_2025`
**Purpose:** Let a developer build or adjust **one module in isolation** (`針對單一模組開發或是調整`) without breaking the others. For every module below: **purpose → INPUT contract → OUTPUT contract → shared dependencies → ISOLATION RULE** (which directory to edit, which script/test to run, which output to re-validate).
**Grounded in the real repo tree** (inspected via GitHub API). Modules the task JSON listed but that do **not** exist on `main` are flagged in the Appendix rather than invented.

---

## 0. The one rule that makes isolation work

Every module talks to its neighbours **only through file/API artifacts with a fixed schema**, never by importing another module's internals. The pipeline is a **linear artifact chain** (`raw → curated → processed → statistical → visualization → animation → dashboard`) plus three **downstream consumers** (`signed_de_application`, `level4_external_validation`, `publication_figures`). If your edit keeps a module's **OUTPUT contract** (filename + schema + row semantics) byte-stable under the canonical checksum, nothing downstream can break — regardless of how you rewrote the internals.

**Contract authority (non-negotiable, the arbiter of "did I break it"):**
- Stage checksums / shapes: `docs/mvp-research/pipeline/reproducibility_audit/` (`parity_01_02.csv`, `parity_03.csv`, `stats_parity_report.md`, `third_party_verification.md`) and `docs/mvp-research/pipeline/_validation/cross_validation_results.csv`.
- Dashboard/API behaviour: `tests/` (pytest) + `src/3_DE_analysis/contracts/card_schema.py`.
- Live human-readable numbers (read-only collector, decides nothing): `scripts/validate_pipeline.py` → `make validate-pipeline`.

---

## 1. Pipeline stage modules (`docs/mvp-research/pipeline/`)

The seven stages are **documentation + data modules**: each stage folder holds a `README_0N_*.md` (the derivation spec) and a `data/` folder (the produced artifact). The **executable** transforms live in `src/` (see Module 8). Stage isolation = edit the stage's transform, regenerate that stage's `data/*.csv`, re-validate against its pinned checksum, leave every other stage folder untouched.

### 1.1 `01_raw` — Raw (single source of truth)
- **Purpose:** hold the unmodified GWT DE statistics; no cleaning, no computation.
- **INPUT contract:** external only — GWT bioRxiv supplementary table, public S3 `genome-scale-tcell-perturb-seq`. No upstream module.
- **OUTPUT contract:** `01_raw/data/DE_stats.suppl_table.csv` = **33,983 rows × 16 cols**, MD5 `f5cf2e070bc8a2fb2ce0c584b3277c4c` (16-column dictionary pinned in `README_01_raw.md`). Also `sgrna_library_metadata.suppl_table.csv`, `sample_metadata.suppl_table.csv`.
- **Shared dependencies:** none (leaf input).
- **ISOLATION RULE:** treat as **frozen**. Only edit to swap the source table; if you do, re-hash and update the MD5 in `README_01_raw.md`, then **every** downstream checksum must be re-pinned. Re-validate: `reproducibility_audit/parity_01_02.csv`.

### 1.2 `02_curated` — Curated (type-normalise + gate flags)
- **Purpose:** keep all 33,983 rows; standardise bools, add `passes_gate` + `logDE`. Add columns only — never drop/dedupe rows.
- **INPUT contract:** `01_raw/data/DE_stats.suppl_table.csv` (33,983 × 16).
- **OUTPUT contract:** `02_curated/data/curated_targets.csv` = **33,983 × 18** (16 raw + `passes_gate`, `logDE`); canonical MD5 `7b8fbe8caebbbb5fedcfea53d55059e3`. `passes_gate = (n_cells_target>=200) & ontarget_significant & (~offtarget_flag) & (n_total_de_genes>=50)`; `logDE = log10(n_total_de_genes+1)`.
- **Shared dependencies:** raw schema (upstream).
- **ISOLATION RULE:** edit only the curated transform + `README_02_curated.md`. Regenerate `curated_targets.csv`; confirm still 33,983 rows and canonical MD5 unchanged (or re-pin deliberately). Re-validate: `reproducibility_audit/parity_01_02_report.md` + R×Python parity. Do **not** touch `03/04` — they re-derive from this file.

### 1.3 `03_processed` — Processed (pivot + gate subset)
- **Purpose:** reshape long → target×condition matrices; extract the gate-passing working set.
- **INPUT contract:** `02_curated/data/curated_targets.csv` (33,983 × 18).
- **OUTPUT contract:** `effect_matrix.csv` (11,526 × 4, MD5 `dab5c0badeb31d4f3636644f04147d59`); `de_matrix.csv` (11,526 × 4, MD5 `6b2ed5e514ddb4fdc9fcc8c5ee284e6e`); `gate_passing_targets.csv` (2,131 × 18, MD5 `779e8746ec416096de860dbf9cc20480`). Condition columns always ordered `Rest → Stim8hr → Stim48hr`.
- **Shared dependencies:** curated schema.
- **ISOLATION RULE:** edit the pivot/subset transform + `README_03_processed.md`. Regenerate the three CSVs; re-validate against `reproducibility_audit/parity_03.csv` + `parity_03_report.md`. Column order and NaN-for-missing semantics are part of the contract — preserve them.

### 1.4 `04_statistical` — Statistical (global summary)
- **Purpose:** collapse the whole dataset into a KV summary + per-condition stats; this is the reproducibility acceptance point.
- **INPUT contract:** `02_curated/data/curated_targets.csv` (reads curated directly, **not** processed).
- **OUTPUT contract:** `summary_statistics.csv` (**18 metrics** × `{metric,value}`, canonical MD5 `4cebfd24630a6e5cae1c43b23b23dbf2`); `condition_stats.csv` (3 conditions). Every metric's `calc_logic` is pinned in `cross_validation_results.csv`.
- **Shared dependencies:** curated schema.
- **ISOLATION RULE:** edit the summary transform + `README_04_statistical.md`. This module is **R×Python cell-by-cell 0-mismatch**, so any edit must reproduce in **both** languages. Re-validate: `_validation/cross_validation_results.csv` (all 18 metrics PASS) + `stats_parity_report.md`. Adding a metric = append a row + extend both R and Python implementations + re-pin the checksum.

### 1.5 `05_visualization` — Visualization (render only)
- **Purpose:** turn stages 02–04 into figures + 3D structures; **produces no new statistics**.
- **INPUT contract:** `02_curated/curated_targets.csv` (per-row plots) + `03_processed/condition_stats` (condition-level). Read-only on upstream.
- **OUTPUT contract:** `05_visualization/refined_figures/*`; the 53-chart catalog `visualization/chart_catalog.csv`; `visualization/figures/gallery_1-5*.png`; `visualization/structures/*.cif` (15 AlphaFold). Registry: `reproducibility_audit/figure_registry.csv`/`.md`.
- **Shared dependencies:** curated + processed schemas; `figure_registry` as the figure manifest.
- **ISOLATION RULE:** edit under `05_visualization/` (and `docs/mvp-research/visualization/`) only. A figure change **cannot** alter any upstream number — if it did, you edited the wrong module. Re-validate: **visual audit** against `figure_registry`; keep every catalog figure ID listed.

### 1.6 `06_animation` — Animation (presentation, read-only)
- **Purpose:** final presentation layer; each GIF is a 1:1 timed reveal of one existing static figure. Writes back nothing.
- **INPUT contract:** stage 05 static figures + 02/03/04 data (read-only).
- **OUTPUT contract:** `06_animation/anim01-10.gif` (10 animations, 25 fps); `cover/cover_dual_perspective.mp4`+`.png`.
- **Shared dependencies:** stage-05 figure set.
- **ISOLATION RULE:** edit under `06_animation/` only. Each animation must map to an already-audited static figure; adding one requires its static counterpart to exist first. Re-validate: **visual audit** + `figure_registry` cross-reference.

### 1.7 `07_dashboard` — Dashboard (consumer, reads every layer)
- **Purpose:** integration/consumption layer; assembles 01–04 tables + evidence/pathway caches into interactive target cards. Produces no new science.
- **INPUT contract:** all upstream layer tables + `_evidence/*.json` + `_pathway/*.json` + external evidence. (Documented in `07_dashboard/README.md`; the executable backend/frontend are Modules 6 & 3.)
- **OUTPUT contract:** interactive cards via the FastAPI JSON contract (`card_schema.py`) — see Module 6/3.
- **ISOLATION RULE:** the stage-07 **doc** is edited here; the **runtime** is isolated in `src/3_DE_analysis/` (backend) and `frontend/` (UI) — see Modules 6 & 3 for the hard API boundary.

---

## 2. Downstream analysis modules (`docs/mvp-research/`)

### 2.1 `signed_de_application/` — Signed DE tracks
- **Purpose:** add gene-level **signed** directionality the count-only pipeline lacked (blindspot 3).
- **INPUT contract:** Marson-lab `GWCD4i.DE_stats.h5ad` (S3, 15.63 GB, extracted on GB10) — a **separate raw source**, not the 33,983-row table.
- **OUTPUT contract:** `signed_ranking_v2.csv` (10,851 genes, 28 cols); `downstream_enrichment_v2.csv`; `lincs_concordance.csv`; `signed_application_figure.png`; `part-000/001.parquet`; `gate_passing_signed_DE.csv.gz`. Coverage pinned in `GB10_SIGNED_DE_VALIDATION.md` (2,056,424 sig pairs; 10,273 downstream genes).
- **Shared dependencies:** producing script `perturbase_review/reproducibility/reproduce_signed_tracks.py`; dictionary `perturbase_review/reproducibility/DATA_DICTIONARY.md`; Reactome snapshot `reactome_pathway_snapshot.csv`.
- **ISOLATION RULE:** edit under `signed_de_application/` + `reproduce_signed_tracks.py`. Independent of stages 02–07 (different raw input) — you can rebuild signed tracks without touching the main pipeline. Re-validate: coverage counts vs source README (`GB10_SIGNED_DE_VALIDATION.md`) + the 30/34-spot-check audit in `MASTER_REVIEW_SUMMARY.md`. Known caveats (`directionality_class` legacy label; `expression_artifact_flag` non-recomputable) must stay documented.

### 2.2 `level4_external_validation/` — Orthogonal external validation
- **Purpose:** cross-check the signed ranking against independent public datasets (L4 of the 5-level ladder).
- **INPUT contract:** `signed_ranking_v2` (10,851 genes; 55-target shortlist) + external GWAS/Open Targets, STRING, GEO GSE318876.
- **OUTPUT contract:** `track_a_gwas_genetic_association.csv`; `track_b_string_partner_recovery.csv`; `track_c_gse318876_target_evidence.csv`; `validation_target_set.csv`; `level4_external_validation_figure.png`.
- **Shared dependencies:** `signed_ranking_v2.csv` (upstream); external public DBs.
- **ISOLATION RULE:** edit under `level4_external_validation/` only. Consumes signed output read-only; produces its own tracks — decoupled from stages 01–07. Re-validate: third-party recompute (15/15 numbers; live Open Targets re-query for TYK2/STAT3/CD3E). Keep the association-≠-causation limits stated.

### 2.3 `perturbase_review/` — Publication figures & review deliverables
- **Purpose:** curate publication-grade figures + the skeptical-review master summary.
- **INPUT contract:** stage-05 visualization + signed + level4 outputs.
- **OUTPUT contract:** `figures/figure1_flagship.png`, `figure_signed_level4.png`, `figure_target_validation.png`; `MASTER_REVIEW_SUMMARY.md`; `reproducibility/reproduction_report.md` + `DATA_DICTIONARY.md` + `reproduce_signed_tracks.py` + `reactome_pathway_snapshot.csv`; `branding/`, `clinical/drug_safety_overview.csv`, `literature/*.csv`.
- **Shared dependencies:** all upstream numeric outputs (already PASS at their own stages).
- **ISOLATION RULE:** edit under `perturbase_review/` only. Figures re-render from frozen upstream artifacts — never regenerate upstream numbers here. Re-validate: **Opus/skeptical review** (each product carries definition + script + result) + visual audit.

### 2.4 `visualization/` (`docs/mvp-research/visualization/`) — Chart catalog & interactive prototypes
- **Purpose:** the design-side catalog: bilingual chart catalog, interactive/3D HTML prototypes, AlphaFold `.cif` structures. Sibling to stage `05_visualization` (design specs vs pipeline render).
- **INPUT contract:** upstream stage data (read-only), consumed for illustrative/prototype rendering.
- **OUTPUT contract:** `chart_catalog.csv` (53 charts), `interactivity_spec.csv`, `STAGE1/2/3_*` HTML+MD, `figures/*.png`, `structures/*.cif`.
- **ISOLATION RULE:** edit under `docs/mvp-research/visualization/` only; pure presentation — cannot affect any pipeline number. Re-validate: visual audit + `chart_catalog.csv` completeness.

---

## 3. Code / runtime modules (`src/`, `frontend/`, `scripts/`, `tests/`)

### 3.1 `src/` — Core pipeline & analysis code (executable transforms)
- **Purpose:** the numbered analysis stages (`1_preprocess` … `10_ml_perturbation_prediction`) plus `src/3_DE_analysis/` which holds the DE engine **and** the dashboard backend (`target_card_api.py`, `target_card_dashboard.py`, `contracts/`, `core/`, `api/`).
- **INPUT contract:** raw/curated data files per stage README; `src/3_DE_analysis/config/*.yaml` for DE runs.
- **OUTPUT contract:** the pipeline `data/*.csv` artifacts (Modules 1.1–1.4) + card JSON per `contracts/card_schema.py`.
- **Shared dependencies:** `src/utils.py`; each subfolder's own `requirements.txt` (`3_DE_analysis`, `10_ml_...`); `environment.yaml` (heavy scanpy/pertpy stack).
- **ISOLATION RULE:** each `src/N_*` subfolder is self-contained — edit one numbered stage without importing siblings. For a stage transform, edit `src/N_*/…`, regenerate that stage's `data/`, re-validate its pinned checksum (Modules 1.x). Do not cross-import between numbered folders; share only via written artifacts. Re-validate: `pytest` (for `3_DE_analysis`) + the stage checksum.

### 3.2 `src/3_DE_analysis/` (backend API) — FastAPI service
- **Purpose:** read-only REST backend that serves target cards to the frontend.
- **INPUT contract:** upstream layer tables + evidence/pathway caches (read-only).
- **OUTPUT contract:** **HTTP/JSON API** whose request/response shapes are pinned by `contracts/card_schema.py` and `tests/test_api_openapi.py`. This JSON contract is the single boundary to the frontend.
- **Shared dependencies:** `requirements.txt`; `contracts/`.
- **ISOLATION RULE:** you may change backend internals freely **as long as the JSON contract holds**. Edit `src/3_DE_analysis/`; run `make api`; re-validate with `pytest` (`test_api_openapi`, `test_triage_target_api`, `test_exports_provenance`, `test_join_integrity`, golden-file tests vs `tests/fixtures/golden_*.csv`).

### 3.3 `frontend/` — Dashboard UI (independently deployable)
- **Purpose:** the CD4 Target Discovery Portal (`frontend/webserver/`, React+TS+Vite SPA; a prior Streamlit `dashboard/` was replaced).
- **INPUT contract:** **FastAPI HTTP/JSON only.** Hard rule (from `frontend/README.md`): nothing under `frontend/` imports `src/3_DE_analysis/` modules, reads its files, or shares its process. The API JSON is the *only* contract.
- **OUTPUT contract:** rendered UI + the runtime-fetched ~18 MB dataset (real data for 7,249 genes); no data written back into the pipeline.
- **Shared dependencies:** `webserver/package.json`. (The portal itself takes no API base URL — it fetches its static `public/real-dataset.json`; the separate live upload tool at `/upload` is served directly by the API, same origin, no env var needed.)
- **ISOLATION RULE:** the strongest isolation in the repo — frontend can be rewritten in any stack without touching backend, and vice versa, provided the JSON contract holds. Edit `frontend/webserver/`; run `make web` (or `cd frontend/webserver && npm run dev`); re-validate `pytest tests/test_empty_states.py`, `test_upload_ui.py` (the live upload tool, which does talk to the API).

### 3.4 `scripts/` — Standalone read-only collector
- **Purpose:** `scripts/validate_pipeline.py` — read-only collector feeding `docs/human_validation_protocol.md`; prints live numbers, decides nothing, rebuilds nothing.
- **INPUT contract:** pipeline data files + `validate_cards` (read-only).
- **OUTPUT contract:** terminal report only (no files written).
- **ISOLATION RULE:** edit `scripts/validate_pipeline.py`; run `make validate-pipeline`; it is safe anytime and cannot mutate state. It is **not** the authority — `tests/` + `contracts/` are. Re-validate: `pytest tests/test_validate_pipeline_collector.py`.

### 3.5 `tests/` — Pytest suite (contract authority)
- **Purpose:** the correctness authority for backend + dashboard + data contracts.
- **INPUT contract:** repo code + `tests/fixtures/golden_*.csv` (golden DE stats / guide KD / library).
- **OUTPUT contract:** pass/fail; golden-file tests pin exact numeric expectations.
- **ISOLATION RULE:** when you change a module's contract deliberately, update the matching test + golden fixture in the **same** change so the authority tracks the intent. Run `pytest` (or `make test`); config `pytest.ini` (`testpaths = tests`).

---

## 4. Shared dependencies (cross-cutting — change with extra care)

| Shared item | Path | Used by | Rule |
|---|---|---|---|
| Env spec (heavy stack) | `environment.yaml` | all `src/` analysis | pin changes; a version bump can shift float formatting → re-run R×Python parity |
| Backend deps | `src/3_DE_analysis/requirements.txt` | backend, dashboard | keep in sync with `contracts/` |
| Card schema | `src/3_DE_analysis/contracts/card_schema.py` | backend ↔ frontend | the API contract; changing it is a cross-module change — update `tests/` + frontend together |
| Golden fixtures | `tests/fixtures/golden_*.csv` | pytest | changing a pinned number = deliberate contract change |
| Stage checksums | `reproducibility_audit/`, `_validation/cross_validation_results.csv` | stages 01–04 | the arbiter of "did I break a stage" |
| Common utils | `src/utils.py` | multiple `src/` stages | shared → edit conservatively; a change ripples across stages |

---

## 5. How to develop / adjust ONE module (the operational recipe)

For any single module, the loop is always the same three questions — **which directory, which script, which output to re-validate:**

1. **Locate the module** in §1–§3; note its INPUT and OUTPUT contract.
2. **Edit only its directory** (the "ISOLATION RULE" line names it). Never import another module's internals; if you need upstream data, read its **published artifact**.
3. **Regenerate that module's output** (run its transform / `make` target / build).
4. **Re-validate against that module's authority only:**
   - Stages 01–04 → the pinned canonical MD5 / parity report for that stage.
   - Stage 04 specifically → reproduce in **both** R and Python.
   - Visualization / animation / publication figures → visual audit vs `figure_registry` / catalog.
   - Backend / dashboard / frontend → `pytest` (+ golden fixtures) and the JSON `card_schema` contract.
   - signed / level4 → coverage-count / third-party recompute for that folder.
5. **Confirm no downstream checksum moved.** If an upstream OUTPUT contract changed on purpose, re-pin its checksum **and** the golden fixture / test in the same change, then re-validate the immediate downstream module only.

If steps 1–4 stay inside one directory and its output contract holds, the edit is isolated **by construction** — no other module can observe it.

---

## Appendix — Task-map entries reconciled against the real tree

- `docs/mvp-research/perturbase_frontend/` — **listed in the task module map but does NOT exist** on `main` (GitHub API returns 404). The live frontend module is `frontend/` (`frontend/webserver/`, React/TS SPA) — treated as Module 3.3. No `perturbase_frontend` module was invented.
- The task JSON's `frontend/: dashboard UI (streamlit pages)` is **stale**: the Streamlit `dashboard/` was replaced by the React `webserver/` SPA (per `frontend/README.md`). Policy reflects the current tree.
- `05_visualization` (pipeline render stage) and `docs/mvp-research/visualization/` (design catalog) are **two distinct modules** (Modules 1.5 and 2.4) — both real, kept separate.
