# Known limitations (honest release register)

This is the consolidated, honest record of what this toolkit does **not** do well
or does not do at all, as of the release freeze. Recording limitations plainly is
a core value of this project (`unknown != 0`); nothing here is hidden or spun.
Per-stage caveats are also surfaced in the EDA reports (`docs/mvp-research/pipeline/EDA_INDEX.md`)
and the in-app research-use-only banner.

## Scope & positioning relative to the source paper

This toolkit is **not a reproduction or extension of the source paper's methodology**
(Zhu, Dann, …, Marson — bioRxiv `10.64898/2025.12.23.696273`, *"Genome-scale perturb-seq
in primary human CD4+ T cells maps context-specific regulators of T cell programs and
human immune traits"*). It is a **drug-target-prioritization translation layer** built on
top of the *same* screen data. Do not present it as validating, reproducing, or extending
the paper's scientific claims.

- **It does not re-derive the paper's gene-regulatory networks.** The paper's core
  contribution is *inferring* context-specific regulatory networks and nominating
  regulators (Th1/Th2 polarization, age-related phenotypes, autoimmune-risk pathways)
  from the raw single-cell perturbation signatures. That modeling is **not reimplemented
  here.** What looks like "pathways" in this tool is either (a) static, hand-curated
  concept-module membership (`concept_annotation.py`, M01–M20, **binary overlap** — the
  *aggregate* DE table that the cards are built from carries only up/down counts, no
  per-gene direction), or (b) **external** Reactome/STRING pathway graphs
  (`mechanism_graph`) annotated with this platform's evidence — not pathways derived from
  this screen.
  - **Partial exception (`signed_module_effect.py`, `GET /api/signed_module_effect/{gene}`):**
    a *directional* readout — "does knocking this target down activate or repress each
    concept module's program?" — IS now computed, but from a *different* in-repo table
    (`full_signed_DE`, which carries per-downstream-gene `log_fc`), not from the cards.
    It recovers known master regulators with the correct sign (GATA3→Th2, TBX21→Th1,
    FOXP3→Treg all score as activators). It is still **descriptive only** (never a
    readiness input), **sparse** (only ~3,739 targets perturb any module marker
    measurably; the rest are `unknown`, not 0), and is **not** a reproduction of the
    paper's regulatory-network inference — it is a directional overlay on the same screen.
- **It does not find genes beyond the paper's screen.** The target cards reprocess the
  *same* 11,526-gene, 4-donor screen — the gene universe is identical to the paper's, so
  there are no "additional" genes to discover. The ML tracks that *attempted* predictive
  discovery (`src/10_ml_perturbation_prediction/`: GenePT+Ridge, GEARS, T2 classifier,
  T1-rework) all honestly lost to, or failed to beat, simple baselines (see each track's
  README).
- **What it genuinely adds is an external translation layer** the paper's dataset does not
  contain: population genetics (UK Biobank LoF burden), disease/drug clinical evidence
  (Open Targets / ClinicalTrials.gov / PubMed), evolutionary constraint (gnomAD),
  tissue-expression breadth (GTEx, for on-target safety), and druggability / tractability.
  These overlays are real but mostly **sparse** (see the coverage figures throughout this
  doc; `unknown != 0`) — the tool's value is triage-support for a *different* goal
  (therapeutic target prioritization), reading the paper's data as its substrate.

## Resolved since the original review

- **Upload-path A.1 / A.2 (was "block before merge").** `kd_status/v2` now gives
  `not_assessed` (not `not_measurable`) for guide-less uploads, and
  `n_total_de_genes` survives the column-mapping wizard via the canonical upload
  schema + alias mapping. Guarded by
  `tests/test_empty_states.py::{test_guideless_upload_is_not_assessed_not_fabricated_not_measurable, test_mapped_upload_preserves_n_total_de_genes}`.
  See `wiki/Tech-Debt.md` A.1/A.2 (✅).

## Methodological limitations

- **Context-specificity is a heuristic**, not a rigorous condition×perturbation
  interaction test (`ctx_specific_de` is a difference-of-DE-counts ranking).
- **Strict grade 3/4 is a narrow gate** — it covers only ~20% of the 21-gene
  positive-control panel. Read it together with the readiness call, never alone.
- **Phenotype-matched external validation is null for the directionality ranking**
  (Track D). Run against activation-phenotype CRISPR screens (Schmidt 2022,
  Freimer 2022), the signed *directionality* ranking does not enrich among
  activation hits (AUROC 0.41–0.48, < 0.5) — different axis + essential-gene
  viability dropout. A *magnitude*-axis fair-version passes (AUROC 0.74–0.79)
  but is exploratory and carries a detectability confound, so **L4 stays
  `partial`**. See `docs/mvp-research/level4_external_validation/LEVEL4_EXTERNAL_VALIDATION.md` §5.
- **Explicit descope:** signed module scoring (the DE tables carry up/down counts,
  no per-gene direction, so a signed score would be fabricated — `/api/modules`
  stays binary-overlap); SCEPTRE not reimplemented (honest external R hook or
  graceful degradation); pertpy/Mixscape replaced by a documented scikit-learn
  stand-in (upstream `blitzgsea` build failure).

## Data / scale limitations

- **Cell-level real data not run.** The full single-cell layer (~1.67 TB) and the
  `DE_stats.h5ad` (15.6 GB) are S3-only and exceed the sandbox; the cell-integration
  path was validated only on a schema-faithful **synthetic fixture** (81.8%
  classification accuracy) — "validated on synthetic fixture" is a different claim
  from "processed the real data" (`src/9_cell_integration/RUN_ON_REAL_DATA.md`).
- **Upstream raw layer is auditable, not re-runnable** — everything before
  `01_raw/DE_stats.suppl_table.csv` needs the S3 data + SLURM/pertpy (see
  `docs/REPRODUCIBILITY.md` §8). Everything after it is in-repo reproducible and
  checked by `make freeze`.
- **`n_donors` is a permanent placeholder — always `NaN`.** Verified live on the
  canonical 39-col dataset: **0 / 33,983 rows** populated. This is `unknown`, not
  a broken join — no per-target donor-count source is wired in. Already flagged
  as OF-4 in `docs/human_validation_protocol.md` §9; listed here so it surfaces
  in the consolidated release register, not only the adjudication log.

## Product / deployment limitations

- **No multi-user or access control** — single-user file-cache; no auth,
  no per-user workspace.
- **Frontend is a static React portal** baked from a one-time
  `export_real_data.py` run; it does not call the live FastAPI backend at runtime.
  The live upload flow (`/api/imports/*`) exists in the backend but is surfaced
  only via a separate standalone tool, not the static portal (by design).
- **Stale build wiring (found during freeze, resolved):**
  - ✅ `Makefile` `dashboard`/`dev` targets used to launch the **removed** Streamlit
    app. Renamed `dashboard`→`web` (+ `install-dashboard`→`install-web`), now
    running the React `frontend/webserver/` Vite dev server; `make dev` runs the
    API + portal together. README, `src/3_DE_analysis/README.md`,
    `wiki/Maintenance.md`, `wiki/Development-Guide.md`, and
    `docs/mvp-research/closure_audit/MODULE_ISOLATION_POLICY.md` updated to
    match (the dated proposal doc `docs/ux_trust_fix_plan.md` is left as a
    historical record, not corrected retroactively).
  - ✅ `frontend/webserver/scripts/export_real_data.py` used to read the
    **legacy** 31-col dataset (`e7ecd8d5-…`). Switched to the canonical 39-col
    `a6bba17b` and regenerated `public/real-dataset.json` (+ its readiness/
    concept-annotation caches). Impact was real, not cosmetic: the legacy
    dataset was silently missing 2,325 `batch_confounded`, 1 `kd_not_measurable`,
    and 10 `kd_weak` red flags (columns absent from the 31-col schema) — the
    portal was under-reporting due-diligence caveats for ~32% of its targets.
    Gene selection, grades, and aggregate readiness-call distribution were
    unaffected (2,325 of those flags cap to `watchlist`, which those genes
    already were for other reasons).
  - ✅ `frontend/webserver/src/data/dataset.ts` was suspected of importing
    `./generated/real-dataset.json` vs. the committed `public/real-dataset.json`.
    Re-verified against the actual code: `dataset.ts` does a runtime `fetch()`
    from `BASE_URL` (Vite serves `public/` at the site root), which already
    correctly resolves to the committed file — this was a stale **comment** in
    `types.ts` (fixed), not a real build bug. `npm run build` confirmed clean
    both before and after.
- **Some external fetches are policy-blocked in the sandbox** (evidence overlay
  covers only the ~20 cache-covered genes; others stay `unknown`, never `0`).
