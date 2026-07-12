# PHASE / MODULE MAP — Perturbase Platform (unified v2)

**Repository:** erichuang777777/GWT_perturbseq_analysis_2025 · **main HEAD:** 0522a2df · **generated:** 2026-07-12
**Purpose:** top-level navigation — where each phase lives, how many modules it holds, how it is frozen, and how to edit ONE module in isolation without contaminating another phase.
**Grounded in the live repo tree** (GitHub API @ 0522a2df). Every prior "does not exist / 404" claim was re-checked against this HEAD; corrections in the Appendix.

## The phases

| Phase | Category | Modules | Files frozen | Isolation track |
|---|---|---|---|---|
| **P0_shared_infra** | shared dependency | 1 | 53 | 共用層 |
| **P1_data_aggregation** | data aggregation | 5 | 126 | 資料與前處理 |
| **P2_preprocessing** | pre-processing | 7 | 46 | 資料與前處理 |
| **P3_statistics** | statistics | 15 | 312 | 統計與分析 |
| **P4_figure_visualization** | figure and visualization | 6 | 101 | 視覺化與圖表 |
| **P5_informative_figure_server** | informative figure and server | 5 | 358 | 視覺化與圖表 |
| **P6_frontend_devops** | frontend and devops maps | 4 | 39 | 前端/devops/文檔/限制 |
| **P7_documentation** | documentation | 42 | 57 | 前端/devops/文檔/限制 |
| **P8_readme_reference** | readme and reference | 8 | 83 | 前端/devops/文檔/限制 |
| **P9_limitation** | limitation | 4 | 4 | 前端/devops/文檔/限制 |

**Totals:** 10 phases (9 taxonomy phases + P0 shared-infra layer) · 97 modules · 1179 files frozen (every repo file except the manifest itself, which cannot freeze its own hash).

## Freeze model (one recipe, whole repo)
Each module's freeze value = `sha256( sorted( per-file git-blob-sha1 ) )` over the files it exclusively owns (`freeze_kind = module_blob_sha256`). File ownership is a **disjoint partition**: every repo file belongs to exactly one module (longest-matching-directory-prefix wins). Content-addressed and path-stable — editing any file changes **only its module's** value; no other module can move. Pinned in `FREEZE_MANIFEST_UNIFIED.csv`. Generator and verifier are the same script (`scripts/validate_freeze_unified.py`), so the manifest reproduces 100% by construction.

## How to edit ONE module in isolation
1. Open `MODULE_ISOLATION_POLICY_v2.md`, find the phase/module; note its INPUT/OUTPUT contract + `validation_authority`.
2. Edit only its directory. Never import another module's internals — read its published artifact instead.
3. Regenerate that module's output; re-validate against its authority (pinned MD5 / R×Python parity / pytest+card_schema / visual audit).
4. Run the contamination guard — it fails if ANY other module's freeze value moved:
   ```
   make validate-freeze                                          # verify all
   python scripts/validate_freeze_unified.py --isolation P4_figure_visualization::viz_pipeline_05
   ```
   Only your edited module may drift; a moved value elsewhere = cross-phase contamination, and the check names the leaked module. Enforced in CI by `tests/test_freeze_unified.py` (verify + disjoint + total).
5. If you changed an OUTPUT contract on purpose, re-pin with `--freeze` and update its golden test in the same change.

## Appendix — stale-claim corrections (surfaced by this audit, deduplicated by topic)
The previous pipeline-only policy carried claims stale at HEAD 0522a2df. All four tracks re-verified against the live tree; unique corrections:
1. MODULE_ISOLATION_POLICY.md Appendix claims docs/mvp-research/perturbase_frontend/ is 404/non-existent — STALE: it EXISTS at HEAD 0522a2df with 146 files (figure_scripts/ + figures_en/, incl. A6/A7/A15 validation figures). Freeze of that dir belongs to the frontend/figures phase; corrected existence only.
2. MODULE_ISOLATION_POLICY §1 quotes older MD5s for curated_targets.csv (7b8fbe8c…), effect_matrix.csv (dab5c0ba…), de_matrix.csv (6b2ed5e5…), gate_passing_targets.csv (779e8746…) — SUPERSEDED by FREEZE_MANIFEST.csv pins (5346cdd6…, dfb61e0c…, 3e6c0352…, 5efd16de…), all of which re-verify byte-stable at HEAD.
3. Task map says backend has 42 FastAPI endpoints — real count is 47 route handlers across 19 routers in src/3_DE_analysis/api/ (12 cards, 8 imports, 5 genes, ...). Registered the true 47.
4. 06_animation output contract lists anim01-10.gif + cover mp4/png, but NO binary animation assets are committed on main (only README.md) — frozen AS-IS (doc contract only).
5. Task-map hint of a Streamlit frontend is stale; frontend/README.md at HEAD confirms production frontend is the React/TS/Vite webserver/ SPA (Streamlit dashboard/ retired). P6 reflects React tree.
6. FREEZE_MANIFEST.csv pins only pipeline/data artifacts (01_raw..overlays) — zero rows overlap P6-P9, so no data-file MD5 pin was reused or contradicted; all P6-P9 freeze values freshly computed from HEAD 0522a2df.
7. Policy §1.4 cites summary_statistics.csv canonical MD5 4cebfd24630a6e5cae1c43b23b23dbf2 (column-alphabetised canonical form used by third-party recompute) — distinct from the committed-file byte md5 f562a9c49313142dc238931c8a5d3b67. Both valid; manifest pins the file-byte md5 to match FREEZE_MANIFEST.csv.
