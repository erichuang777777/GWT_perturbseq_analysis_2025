# Known limitations (honest release register)

This is the consolidated, honest record of what this toolkit does **not** do well
or does not do at all, as of the release freeze. Recording limitations plainly is
a core value of this project (`unknown != 0`); nothing here is hidden or spun.
Per-stage caveats are also surfaced in the EDA reports (`docs/mvp-research/pipeline/EDA_INDEX.md`)
and the in-app research-use-only banner.

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

## Product / deployment limitations

- **No multi-user or access control** — single-user file-cache; no auth,
  no per-user workspace.
- **Frontend is a static React portal** baked from a one-time
  `export_real_data.py` run; it does not call the live FastAPI backend at runtime.
  The live upload flow (`/api/imports/*`) exists in the backend but is surfaced
  only via a separate standalone tool, not the static portal (by design).
- **Stale build wiring (found during freeze, not yet fixed):**
  - `Makefile` `dashboard`/`dev` targets still launch the **removed** Streamlit
    app (`frontend/dashboard/target_card_dashboard.py`); they fail on current
    `main` (the frontend is now `frontend/webserver/`, React+Vite).
  - `frontend/webserver/scripts/export_real_data.py` reads the **legacy** 31-col
    dataset (`e7ecd8d5-…`) rather than the canonical 39-col `a6bba17b`; the
    committed portal export therefore predates the v2 columns.
  - `frontend/webserver/src/data/dataset.ts` imports `./generated/real-dataset.json`
    while the committed artifact lives at `public/real-dataset.json` — confirm the
    build copies/points correctly from a clean checkout.
  These are tracked here and in `docs/ROADMAP.md`; they belong to the frontend /
  upload workstream, not the data-freeze.
- **Some external fetches are policy-blocked in the sandbox** (evidence overlay
  covers only the ~20 cache-covered genes; others stay `unknown`, never `0`).
