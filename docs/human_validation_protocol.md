# Human Validation Protocol — Phase 0 (raw data) → UI

**Status:** living protocol · **Purpose:** a stage-by-stage, human-signed validation of the CD4
Perturb-seq target-discovery toolkit, from the raw supplementary tables through to the Streamlit UI.

This protocol is a **human sign-off layer on top of** the toolkit's existing automated tests and
reference docs — it does **not** restate their formulas, thresholds, or pinned counts. For each check it
names the doc/test that *owns* the fact and asks a human to (a) confirm that owner is green/current and
(b) apply the judgment a machine cannot: is the value biologically plausible, is a column rightly
in/out, and how should a real discrepancy be adjudicated.

---

## §0 How to use this protocol

**Who signs:** a domain scientist (immunology / statistical genetics), not necessarily a coder.

**Each row is signed** `PASS` / `FAIL` / `N/A` + initials + date. The governing rule:

> A dimension already covered by a passing automated test is signed off by **confirming that test is
> green**, not by re-deriving it. This protocol adds the human-judgment layer (plausibility, rationale,
> discrepancy adjudication) that tests cannot carry.

**Bootstrap (run once, top to bottom):**

1. `make test` — the whole suite must be green. If any cited test fails, **stop**: the machine layer is
   broken and human sign-off on top of it is meaningless.
2. `make validate-pipeline` — runs `scripts/validate_pipeline.py`, a read-only collector that prints the
   live numbers this protocol references (active dataset + column count, `validate_cards` results, raw
   row counts, dtypes, thresholds, and auto-detected open-finding lines). **Keep this output open**; the
   checkboxes below refer to its blocks.

**The 7 validation dimensions** (each stage is checked against the relevant subset):

| ID | Dimension | Plain question |
|----|-----------|----------------|
| D1 | Data source | Is the on-disk file the source we think it is? |
| D2 | Fields | Are the expected columns present, correctly named? |
| D3 | Counts | Do row/entity counts match the documented expectation? |
| D4 | Raw vs computed | Is each field a passthrough of upstream data, or computed here (and by what rule)? |
| D5 | Inclusion/exclusion rationale | Why is each column in — or deliberately out? |
| D6 | Data types | Are dtypes correct (int/float/bool/str), no silent coercion? |
| D7 | Literature plausibility | Is the value consistent with published biology? (§7 register) |

**Active-dataset banner — record this FIRST (it gates everything):** the cache currently holds two
card datasets. Write down which one is the *canonical* one under test:

- `a6bba17b-f194-4a50-8cf8-96e03eededd6` — **39 columns, current `card_schema/v2`**, `validate_cards(
  strict=True)` passes, clean metadata paths. **This is the canonical dataset.**
- `e7ecd8d5-5463-43e3-9bf1-6e8a15d3e137` — **31 columns, legacy schema**, `validate_cards(strict=True)`
  FAILS (8 columns missing), metadata leaks Windows `D:\` paths. This is the git-tracked-but-stale
  reference — see **Open Finding OF-1** before using it for anything.

Active dataset under test: `________________________`  ▢ recorded — initials/date: `__________`

---

## §1 Stage 0 — Raw data (upstream, all passthrough)

**Scope:** `metadata/suppl_tables/*`, `sources/*`, `sources/target_tool_cache/_overlays/*`,
`src/6_functional_interaction/results/*`, `src/8_lymphocyte_counts_LoF/input/*`. Nothing here is
computed by this toolkit (D4 = **all raw**, confirm via `docs/data_dictionary.md` intro: "copied through
from a real upstream file").

**Authoritative references:** `docs/data_dictionary.md` §1 (raw-inputs table), `metadata/
data_sharing_readme.md` (the upstream dataset's own column schema — the authority for Stage-0 columns
and dtypes; do **not** re-document upstream columns, cite this), `docs/REPRODUCIBILITY.md` §6.2 (counts).

| # | File | D1 source | D3 count (expected) | Check | Sign |
|---|------|-----------|---------------------|-------|------|
| 1.1 | `DE_stats.suppl_table.csv` | data_dictionary §1 | **33,983** data rows | collector "Stage 0" block | |
| 1.2 | `guide_kd_efficiency.suppl_table.csv` | data_dictionary §1 | **73,765** | collector | |
| 1.3 | `sgrna_library_metadata.suppl_table.csv` | data_dictionary §1 | **31,109** (12,654 unique targets) | collector | |
| 1.4 | `sample_metadata.suppl_table.csv` | data_dictionary §1 | collector prints **12** — data_dictionary says 11; **adjudicate the off-by-one** (header handling vs real drift) | collector | |
| 1.5 | `disease_gene_associations_detailed.csv` | data_dictionary §1 | collector prints **7,527** data rows — data_dictionary/§1 says 7,528 (line vs row count); confirm **13 diseases** via `test_meta_coverage_api.py` | collector | |
| 1.6 | `gnomad_constraint_seed.csv` | data_dictionary §3 | **15** genes (seed only) | collector | |
| 1.7 | `gtex_per_tissue.parquet` | `test_safety_overlay.py` | **9,718** rows | test | |
| 1.8 | Backman UKB LoF TSVs (`src/8_lymphocyte_counts_LoF/input/`) | data_dictionary §1 | present; `ensg/post_mean/lower_95/upper_95` cols | open file | |

- **D2 fields / D6 dtypes:** for each raw file, confirm the expected key columns are present against
  `metadata/data_sharing_readme.md`; the collector prints the card dtypes downstream, but Stage-0 dtypes
  are the upstream file's own — spot-check that numeric columns parse as numeric.
- **D5 inclusion/exclusion:** which raw columns survive into cards is governed by §8 (Column
  Inclusion/Exclusion table). Here just confirm no *expected* raw input is missing.
- **D7 plausibility:** register rows tagged Stage 0 (LP-10, LP-13) — §7.
- **OF-3 (surface here):** the upstream GWT dataset **license is "not stated"** (`docs/
  data_governance_checklist.md` §1). This is a **blocking** open finding for any external release —
  record a ruling in §9.

▢ Stage 0 complete — initials/date: `__________`

---

## §2 Stage 1 — Target cards (`core/cards.py::build_cards_frame` → `target_cards.csv`)

**Scope:** the MIXED stage — ~18 raw/alias passthrough columns + ~17 computed. **Heaviest section.**

**Authoritative references:** `docs/data_dictionary.md` §2 (every column's type, meaning, and
raw-vs-computed derivation — the human does NOT re-derive, they confirm the doc's formula description is
still true), `config/thresholds.py` (the collector prints live values — check the doc against code, not
memory), `contracts/card_schema.py` (`CARD_COLUMNS`, `validate_cards`).

| Check | Dimension | How to verify | Sign |
|-------|-----------|---------------|------|
| 2.1 | D1/D2/D4 | Confirm `data_dictionary.md` §2 still describes each column's derivation (passthrough vs formula) correctly. Spot-check 3 computed columns against `core/scoring.py`. | |
| 2.2 | D4 (thresholds) | Confirm the collector's LIVE THRESHOLDS block matches what `data_dictionary.md` §2 assumes: `MIN_CELLS=200`, `MIN_DE_GENES=50`, `CROSSDONOR/GUIDE_MIN=0.2`, `_ROBUST=0.3`, `GUIDE_SIGNIF_RATIO_MIN=0.5`, `GUIDE_FDR_MAX_CONFIRMED=0.05`, `GUIDE_FDR_MAX_GRADE3=0.1`, `N_GUIDES_MIN_HIGH_GRADE=2`, `KD floor=0.001`. | |
| 2.3 | D3 | QC funnel via `tests/test_known_answer.py`: `all_rows==33,983` → `n_total_de_genes>=50 == 4,182` → `high_confidence_rows == 1,102`. Confirm the test is green. | |
| 2.4 | D3 | `tests/test_join_integrity.py`: `len(cards)==len(de_stats)`, unique `(target,condition)` pairs, no dropped/duplicated rows. | |
| 2.5 | D6 | Collector `validate_cards(strict=True)` error list is **empty on the active (39-col) dataset**. On the legacy 31-col dataset it reports 1 error — that is OF-1, not a Stage-1 failure of the canonical build. | |
| 2.6 | D6 | Eyeball the collector dtypes block: `n_cells_target` float64, `ontarget_significant`/`offtarget_flag`/`replicate_pass_flag` bool, `statistical_evidence_grade` int64, `target`/`condition`/`kd_status`/`score_cap_reason` object. Confirm no numeric column landed as object. | |
| 2.7 | D7 | Register rows LP-03…LP-09 (§7): grade distribution, control recovery, KD floor. | |

- **Golden anchors** (`tests/test_golden_file.py`, confirm green): ZAP70 positive control → `grade 4`,
  `kd confirmed`; MED12 broad-effect gene still `grade 4` at the statistical layer (the broad-effect cap
  lives downstream in readiness); low-expression gene → `kd_not_measurable` at the `0.001` floor.
- **Open findings surfaced here:** OF-1 (schema drift), OF-4 (`n_donors` always NaN — confirm honest
  placeholder, not a broken join), OF-5 (`nearest_failure_or_warning` always empty — confirm
  placeholder-by-design). See §8/§9.

▢ Stage 1 complete — initials/date: `__________`

---

## §3 Stage 2 — Readiness (`core/readiness.py::compute_readiness` → `readiness.csv`)

**Scope:** fully COMPUTED — 12 domain scores, `overall_readiness_stage` (R0–R3), `readiness_call`
(deprioritize/watchlist/validate/advance).

**Authoritative references:** `docs/data_dictionary.md` §3 (readiness frame), `tests/test_join_integrity.py`
(1:1 cards↔readiness), `tests/test_translation_capped_by.py`, `docs/data_governance_checklist.md`.

| Check | Dimension | How to verify | Sign |
|-------|-----------|---------------|------|
| 3.1 | **D4 — the #1 correctness property** | **Causal isolation:** every descriptive overlay (`safety_window_score`, `gnomad_*`, `genetic_support_*`, `composite_safety_liability`, `translation_capped_by`) must NEVER be read by `_stage()` / `_red_flags()` — so it cannot move the call/stage. Confirm `tests/test_translation_capped_by.py` (and the `*_inert_through_compute_readiness` tests in `test_safety_overlay.py` / `test_robust_ranking.py` / `test_triage_view.py`) are green. | |
| 3.2 | D2/D3 | 1:1 linkage cards↔readiness (`test_join_integrity.py`); 12 domains present per `data_dictionary.md` §3. | |
| 3.3 | D5 | **`unknown != 0`:** confirm no domain lacking an overlay defaults to 0 — a missing overlay is the literal string `"unknown"`. Cite `docs/data_governance_checklist.md` §3; spot-check a gene absent from the gnomAD seed shows `gnomad_constraint_flag = "unknown"`, not `"none"`. | |
| 3.4 | D7 | Register row LP-12 (§7): fraction of targets reaching R2/R3 should be *small* (most targets are not advanceable) — sanity, not a pinned count. | |

▢ Stage 2 complete — initials/date: `__________`

---

## §4 Stage 3 — Overlays / evidence (`evidence/*.py`, `common/overlay_lookup.py`)

**Scope:** MIXED — loaders are raw passthrough with an **honest-fallback contract** (`available: False`,
never a fabricated value); interpretation (LOEUF flag, safety window, composite liability) is computed.

**Authoritative references:** `tests/test_safety_overlay.py` (GTEx 9,718, membrane 5,588, gnomAD pins),
`tests/test_evidence_enrichment.py` (real gnomAD LOEUF), `tests/test_meta_coverage_api.py` (coverage).

| Check | Dimension | How to verify | Sign |
|-------|-----------|---------------|------|
| 4.1 | D1/D4 | Honest-fallback: a gene absent from an overlay → `"unknown"`, never fabricated. Confirm `test_safety_overlay.py` gene-absent → unknown-not-none is green. | |
| 4.2 | D3 (coverage) | `test_meta_coverage_api.py`: gnomAD **15/11,526**, GTEx **5,266/11,526 (45.7%)**, disease **1,977/11,526 across 13**, LINCS **4/15**. Confirm green. Cross-check live via `GET /api/meta/coverage/<active_dataset>`. | |
| 4.3 | D7 — **heaviest register work** | LOEUF plausibility (LP-01/LP-02), GTEx breadth (LP-15), disease-association sanity (LP-13), safety-liability composition. See §7. | |

▢ Stage 3 complete — initials/date: `__________`

---

## §5 Stage 4 — API (`src/3_DE_analysis/api/routers/*`)

**Scope:** passthrough + lazy readiness recompute-on-stale; version-stamp headers on every response.

**Authoritative references:** `docs/REPRODUCIBILITY.md` §6.3 (curls + expected output), `docs/API.md`,
`tests/test_triage_target_api.py`, `tests/test_api_openapi.py`.

| Check | Dimension | How to verify | Sign |
|-------|-----------|---------------|------|
| 5.1 | D1/D4 | `make api`, then hit a `REPRODUCIBILITY.md` §6.3 curl. Confirm version headers `X-Engine-Version` (1.3.0), `X-Schema-Version` (`card_schema/v2`). | |
| 5.2 | End-to-end tie | `GET /api/targets/<active>/ZAP70` returns `statistical_evidence_grade == 4` — ties the Stage-1 golden file to the served response (no transformation in the API layer). | |
| 5.3 | D2 | `test_api_openapi.py` green: every endpoint exactly one tag; research-use/not-clinical + `unknown != 0` surfaced in the OpenAPI description. | |
| 5.4 | D7 | N/A — the API introduces no new values, it serves Stage 1–3 outputs. | |

▢ Stage 4 complete — initials/date: `__________`

---

## §6 Stage 5 — UI (`frontend/dashboard/`, 13 pages + landing)

**Scope:** presentation only — no data transformation; every value arrives via `api_client.py` over
HTTP/JSON.

**Authoritative references:** `tests/test_dashboard_smoke.py`, `tests/test_ui_chips.py`,
`docs/concept_dictionary.md` (M01–M20 module labels).

| Check | Dimension | How to verify | Sign |
|-------|-----------|---------------|------|
| 6.1 | D4 (no silent transform) | Spot-check one value shown on a page equals the JSON it came from — e.g. ZAP70's grade chip on the dossier equals `/api/targets/.../ZAP70`'s `statistical_evidence_grade`; a coverage badge equals `/api/meta/coverage`. No silent rounding/relabel/fabrication. | |
| 6.2 | D6 (`unknown != 0`) | `test_ui_chips.py` green: an unmeasured field renders the grey 「未檢查」chip, a measured `0` renders as a value. | |
| 6.3 | D7 | Displayed literature-facing claims match sources: IL2RA/basiliximab indication text (LP-11), concept-module labels vs `concept_dictionary.md`. | |

▢ Stage 5 complete — initials/date: `__________`

---

## §7 Literature Plausibility Register

The core human-judgment task: for each value the toolkit surfaces, confirm it is consistent with
published biology and **fill the DOI/PMID slot yourself** (PubMed / gnomAD browser / GTEx portal /
DrugBank). Expectations below are phrased as *questions to verify* — none is an asserted number to
accept on faith.

> **Pre-verified this session** (marked ✅ VERIFIED, but still requires your final sign-off): rows the
> author confirmed against a live source during authoring. Everything else has a blank citation slot for
> you to fill. **No DOI/PMID appears here that was not actually retrieved.**

| ID | Stage | Value / claim in repo | Repo source | Published expectation to CHECK | Citation (DOI/PMID) | Plausible? | Sign |
|----|-------|------------------------|-------------|-------------------------------|---------------------|-----------|------|
| LP-01 | 3 | MED12 gnomAD LOEUF ≈ **0.0955** → loss-intolerant | `test_evidence_enrichment.py` | The toolkit's flag threshold is gnomAD **v4 LOEUF < 0.6** (NOT the v2.1.1-era 0.35 — see `data_dictionary.md` §3). Is MED12 constrained in the gnomAD v4 browser? | ☐ (gnomAD v4 browser: MED12) | ☐ | |
| LP-02 | 3 | CD3E LOEUF ≈ **0.7008** → `"none"` (not constrained) | `test_evidence_enrichment.py` | Does CD3E's v4 LOEUF really sit above 0.6? Cross-check the gnomAD v4 browser. | ☐ | ☐ | |
| LP-03 | 1 | ZAP70 = **grade 4**, KD confirmed, strong effect | `test_golden_file.py` | ZAP70 is a canonical TCR-proximal kinase; a strong CD4 phenotype (top hit) is expected. | ☐ | ☐ | |
| LP-04 | 1 | MED12 = broad/pleiotropic effect | `test_golden_file.py`, `sources/broad_effect_genes.txt` | Mediator-complex subunit ⇒ broad transcriptional effect expected. | ☐ | ☐ | |
| LP-05 | 1 | Positive-control recovery = **20/20 found** | `test_known_answer.py` | Recovery of curated positive controls should be near-complete for a trustworthy screen. | ☐ | ☐ | |
| LP-06 | 1 | Negative controls **≥95% grade 1** | `test_known_answer.py` | NTC/negative guides should overwhelmingly fail to score. | ☐ | ☐ | |
| LP-07 | 1 | QC funnel **33,983 → 4,182 (n_de≥50) → 1,102** high-confidence | `test_known_answer.py` | ~3–4% high-confidence yield — in line with genome-scale Perturb-seq hit rates? | ☐ | ☐ | |
| LP-08 | 1 | KD-not-measurable floor = **0.001** expression | `test_golden_file.py`, thresholds | Biological floor plausibility; no negative/>1 KD-fraction artifacts. | ☐ | ☐ | |
| LP-09 | 1 | `n_total_de_genes` distribution per target | DE_stats | Most perturbations yield modest DE counts, few broad outliers — long-tail shape expected. | ☐ | ☐ | |
| LP-10 | 0 | **3** conditions (Rest/Stim8hr/Stim48hr), **11,526** unique targets | `REPRODUCIBILITY.md` §6.2 | Consistent with a genome-scale CD4 Perturb-seq design? | ☐ | ☐ | |
| LP-11 | 5/UI | IL2RA drug **basiliximab** is trialled for transplant rejection, **not** rheumatoid arthritis | disease-drug-evidence page / `test_disease_drug_evidence.py` | **✅ VERIFIED this session (ClinicalTrials.gov):** basiliximab × "kidney transplant rejection" = **30 trials**; basiliximab × "rheumatoid arthritis" = **0 trials**. Confirms the toolkit's canonical honest-mismatch example. | ClinicalTrials.gov (e.g. NCT06087003, NCT05385432); basiliximab = anti-CD25/IL2RA mAb | ☐ (your sign-off) | |
| LP-12 | 3 | Robust-rank tiers **725 / 1,097 / 400** (default/lenient/strict) | `REPRODUCIBILITY.md` §6.2 | Monotonic (strict < default < lenient) and a plausible small fraction of 33,983? | ☐ | ☐ | |
| LP-13 | 0/3 | **13** autoimmune/inflammatory indications, **7,527** disease-gene rows | data_dictionary §1, `test_meta_coverage_api.py` | Association scores in [0,1]; known CD4 disease genes (IL2RA, PTPN22) present? | ☐ | ☐ | |
| LP-14 | 3 | Switches: **n_true_sign_flip=27**, **n_on_off_switch=215**, **double_support=161** | `REPRODUCIBILITY.md` §6.2 | True sign-flips should be rarer than on/off switches — ordering plausible? | ☐ | ☐ | |
| LP-15 | 3 | GTEx **9,718** genes, membrane proteins **5,588** | `test_safety_overlay.py` | Membrane fraction of the assayed proteome plausible; surface targets flagged for tractability? | ☐ | ☐ | |

**Note on genetic-support framing (context, not a register row):** `data_dictionary.md` §3 already cites
the literature basis for grading genetic support (Minikel, *Nature* 2024) and safety liability (Duffy,
*Sci Adv* 2020; Nat Rev Genet 2025). Confirm those citations resolve if you rely on the
`genetic_support_confidence` / `composite_safety_liability` tiers. (PMIDs left for you to fill — they
were not machine-retrieved this session.)

▢ Register complete — initials/date: `__________`

---

## §8 Column Inclusion / Exclusion Rationale

Seeded from `docs/data_dictionary.md` §2. This makes D5 (why a column is in or out) attestable. The
"included, computed/raw" rows are summarized — see the dictionary for full formulas. The **excluded /
placeholder / drift** rows are the ones needing human adjudication.

| Column | In cards? | Raw/computed | Rationale | Who decided (ref) |
|--------|-----------|--------------|-----------|-------------------|
| target, condition, target_id | ✅ | raw (renamed) | join keys / identity | data_dictionary §2 |
| n_cells_target, n_total/up/down_de_genes, ontarget_effect_size, ontarget_significant, offtarget_flag, crossdonor/guide correlations | ✅ | raw passthrough | core DE evidence | data_dictionary §2 |
| median_logFC, max_abs_logFC | ✅ | computed (alias of ontarget_effect_size) | convenience columns | data_dictionary §2 |
| n_guides, guide_signif_ratio, guide_fdr_min, guide_t_abs_median, fdr_min, target_baseline_expression | ✅ | computed (guide-table aggregates) | KD strength / robustness inputs | data_dictionary §2 |
| statistical_evidence_grade, score_cap_reason, kd_status, replicate_pass_flag, batch_sensitivity_flag, condition_specificity_score/zscore, effect_direction_flip_flag, pathway_axis, clinical_axis, positive_control_similarity | ✅ | computed | grading + QC + local overlays | data_dictionary §2, core/scoring.py |
| druggable_class, tractability_modality, safety_note | ✅ | computed (local gene-list membership) | tractability/safety annotations | data_dictionary §2 |
| **n_donors** | ✅ (always NaN) | placeholder | not derivable from DE_stats alone — honest placeholder, never imputed. **OF-4: confirm this is by-design.** | data_dictionary §2 / OF-4 |
| **nearest_failure_or_warning** | ✅ (always "") | placeholder | reserved, not yet populated by any source. **OF-5: confirm placeholder vs unimplemented.** | data_dictionary §2 / OF-5 |
| **8 v2 columns missing from the legacy dataset** (`kd_status`, `kd_threshold_version`, `druggable_class`, `tractability_modality`, `safety_note`, `condition_specificity_zscore`, `effect_direction_flip_flag`, `target_baseline_expression`) | ✅ in v2 / ❌ in legacy `e7ecd8d5` | computed | added in `card_schema/v2`. **OF-1: were these deliberately added, and should the legacy dataset be retired/regenerated?** | OF-1 |
| readiness/domain columns, module scores, evidence snapshot, CRE, mechanism graph | ❌ (not in cards) | served separately | kept out of the card table by design — see data_dictionary §3/§5/§6/§10 | data_dictionary |

▢ Rationale reviewed — initials/date: `__________`

---

## §9 Open Findings — adjudication log (pre-filled from real inspection)

| ID | Finding | Severity | Evidence | Human ruling | Owner | Date |
|----|---------|----------|----------|--------------|-------|------|
| **OF-1** | Schema drift: legacy `e7ecd8d5` has **31** cols; current `CARD_COLUMNS` declares **39**. `validate_cards(strict=True)` FAILS on the legacy file (8 cols missing: kd_status, kd_threshold_version, druggable_class, tractability_modality, safety_note, condition_specificity_zscore, effect_direction_flip_flag, target_baseline_expression). | **BLOCKING** | `make validate-pipeline` OF-1 line; `contracts/card_schema.py` | ✅ **RESOLVED** — `a6bba17b` (39-col) is the sole canonical dataset; `e7ecd8d5` marked DEPRECATED (`sources/target_tool_cache/e7ecd8d5-.../DEPRECATED.md`), flagged `deprecated:true` and sorted last by `GET /api/datasets` (`build.py::list_datasets`), retained only as a regression fixture. README quickstart already points to canonical. | Claude | 2026-07-11 |
| **OF-2** | `e7ecd8d5/metadata.json` leaks absolute Windows paths (`D:\…`) in `params.clinical_benchmark` + `output`, and has `params.max_rows:5` / `preview_limit:5` conflicting with the real 33,983-row output. (`a6bba17b` metadata has clean paths but `max_rows:200` — confirm no truncation either.) | High | collector OF-2 lines | ▢ Scrub/regenerate metadata; confirm no `max_rows` cap ever truncated shipped data. | | |
| **OF-3** | Upstream GWT dataset **license "not stated"**. | **BLOCKING (external release)** | `data_governance_checklist.md` §1 | ✅ **WAIVED for tool release** — the tool only reads the data locally and never re-publishes the raw GWT tables; documented in `DATA_LICENSE.md`. **Remains blocking** for any external redistribution of the raw data or publication use (confirm the dataset's own license/DUA first). | Claude | 2026-07-11 |
| **OF-4** | `n_donors` is always NaN. | Low | data_dictionary §2 | ✅ **Confirmed honest placeholder** — verified live on the canonical dataset: 0/33,983 rows populated (pandas count, not a broken join; no per-target donor-count source is wired in). Listed in `docs/KNOWN_LIMITATIONS.md`. | Claude | 2026-07-12 |
| **OF-5** | `nearest_failure_or_warning` is always "". | Low | data_dictionary §2 | ▢ Confirm placeholder-by-design vs unimplemented feature. | | |
| **OF-6** | Overlay coverage is sparse (gnomAD 15/11,526; LINCS 4/15). | Medium | `test_meta_coverage_api.py` | ▢ Confirm the UI discloses "absence ≠ negative" (the `unknown != 0` + coverage-badge work). | | |
| **OF-7** | Doc-vs-code path drift: `data_dictionary.md` still cites `build_target_cards.py::build_cards_frame` / `readiness_engine.py`; the live code is `core/cards.py` / `core/readiness.py` (`build_target_cards.py` is a back-compat shim). Also minor count drift (sample_metadata 11 vs 12; disease rows 7,528 vs 7,527; sgrna 31,109 vs 26,504). | Low | this protocol §1, §2 | ◐ **Counts fixed** (2026-07-11): `data_dictionary.md` now reads 26,504 / 7,527 / 12 (verified via pandas record counts). Code-path reference refresh still pending. | Claude | 2026-07-11 |

---

## §10 Sign-off roll-up

| Stage | Result | Signer | Date |
|-------|--------|--------|------|
| 0 Raw data | ☐ PASS / ☐ FAIL / ☐ N-A | | |
| 1 Target cards | ☐ PASS / ☐ FAIL / ☐ N-A | | |
| 2 Readiness | ☐ PASS / ☐ FAIL / ☐ N-A | | |
| 3 Overlays/evidence | ☐ PASS / ☐ FAIL / ☐ N-A | | |
| 4 API | ☐ PASS / ☐ FAIL / ☐ N-A | | |
| 5 UI | ☐ PASS / ☐ FAIL / ☐ N-A | | |
| Literature register (§7) | ☐ complete | | |
| Open findings (§9) | ☐ all adjudicated | | |

**Release gate:** the blocking findings (**OF-1** schema drift, **OF-3** license) must be resolved or
**explicitly waived with a recorded reason** before this pipeline is signed off for external release.

Overall recommendation: `________________________________________`  — signer/date: `__________`
