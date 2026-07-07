# DE and NTC Baseline Specification

**Status:** documentation-only, describing computations already performed upstream in the GWT dataset
release; this toolkit does not recompute DE or NTC baselines, it consumes and interprets them.
**Why this exists:** every effect size, every DE call, and every knockdown-confidence judgment this
toolkit surfaces is relative to a non-targeting-control (NTC) baseline. If that baseline's composition
and the DE methodology aren't stated precisely, none of the numbers are comparable or citable. This
was flagged as a P0 documentation gap in an external technical review of a related planning document
(2026-07-07) and is addressed here directly against the real, already-in-repo data facts.

## 1. NTC (non-targeting control) baseline composition

Source: `metadata/data_sharing_readme.md` ("Guide knockdown efficiency" and "Cell-level data" sections).

- **Guide-level NTC pool** (`guide_kd_efficiency.suppl_table.csv`): for each `(perturbed_gene_id,
  culture_condition)` pair, `ntc_mean_expr`/`ntc_std_expr`/`ntc_n` are computed from **non-targeting
  control cells within that same culture_condition** — confirmed empirically in this repo: `ntc_mean_expr`
  is invariant across every guide within a `(perturbed_gene_id, culture_condition)` group (0 of 37,578
  groups show more than one distinct value), meaning the NTC pool used for a given target's knockdown
  test is condition-matched, not donor-matched to that specific guide's cells individually.
- **`guide_type` in cell-level data** (`D{n}_{condition}.assigned_guide.h5ad`): cells are labeled
  `"targeting"` or `"non-targeting"` per cell; a cell with more than one detected guide is labeled
  `"multi-guide"` in `guide_id` and should be excluded from both target and control pools (see
  `src/9_cell_integration/perturbation_response_analysis.py::guide_assignment_qc`).
- **Per-sample/lane summary** (`QC_summaries_per_sample_lane.csv`): reports `NTC single sgRNA` and
  `targeting single sgRNA` counts per library/lane, confirming the NTC and targeting populations are
  tracked as parallel, comparably-sized pools at the same processing granularity (not a single global
  NTC pool reused unchanged across every comparison).

## 2. Effect size definition

Source: `metadata/data_sharing_readme.md` ("Differential expression results" / `GWCD4i.DE_stats.h5ad`
layers) and `DE_stats.suppl_table.csv` columns.

- DE is called with **DESeq2** on pseudobulk aggregates (`layers`: `log_fc`, `p_value`, `adj_p_value`,
  `baseMean`, `lfcSE`, `zscore` in the DE_stats h5ad).
- **Pseudobulk aggregation unit**: `guide x donor x culture_condition` (per the pseudobulk-level h5ad
  schema, `GWCD4i.pseudobulk_merged.h5ad`, whose `.obs` is one row per `(guide_id, donor_id,
  culture_condition)` combination with `n_cells` cells summed into it).
- **Minimum-cell / inclusion gating**: the pseudobulk schema carries explicit boolean flags
  (`keep_min_cells`, `keep_effective_guides`, `keep_total_counts`, `keep_for_DE`, `keep_test_genes`) —
  a pseudobulk sample is only used for DE if `keep_for_DE == True`. This toolkit's own
  `min_cells`/`min_de_genes` gates (`build_target_cards.py`) are a *second*, coarser filter applied on
  top of whatever passed the upstream `keep_for_DE` gate — they do not replace it.
- **On-target effect size** (`ontarget_effect_size` in `DE_stats.suppl_table.csv`): the DESeq2 log2FC
  of the target gene itself, in the target's own knockdown contrast vs the condition-matched NTC
  pseudobulk baseline described in §1.
- **`ontarget_significant`**: whether that on-target log2FC clears the DE FDR threshold (10%, per
  `n_up_genes`/`n_down_genes` definition below) in the direction expected for knockdown.
- **FDR threshold used for `n_up_genes`/`n_down_genes`/`n_total_de_genes`**: **10% FDR** (stated
  explicitly in `metadata/data_sharing_readme.md`: "Count of significantly upregulated/downregulated
  genes (10% FDR)"). This is the single FDR threshold used consistently across the DE_stats table.

## 3. Knockdown (KD) assessment — the `guide_kd_efficiency.suppl_table.csv` test

- **Test**: Welch's t-test comparing a guide's cells' log-normalized target expression against the
  condition-matched NTC pool's log-normalized target expression (`t_statistic`, `p_value`,
  `adj_p_value` in `guide_kd_efficiency.suppl_table.csv`).
- **`signif_knockdown`**: `adj_p_value < 0.1 AND t_statistic < 0` (i.e., BH-FDR-significant AND in the
  knockdown direction — a significant *increase* in expression is not counted as "signif_knockdown").
- **`high_confidence_no_effect_guides`**: a documented, pre-existing floor for whether knockdown is
  assessable at all — "non-significant knockdown, >10 cells with guide, target expression in NTCs
  >0.001." This toolkit's `kd_status` field (`build_target_cards.py::_kd_status`,
  `KD_NOT_MEASURABLE_EXPRESSION_FLOOR = 0.001`) reuses this exact, already-documented expression floor
  rather than inventing a new one — a target whose NTC baseline expression (`target_baseline_expression`,
  i.e. `ntc_mean_expr`) was **measured** and is at or below `0.001` is `kd_status = "not_measurable"`:
  the causal chain (knockdown -> downstream transcription change) cannot even be evaluated for it, which
  is a different failure mode from "measurable but not significantly knocked down" (`kd_status = "weak"`).
  A **fourth** state, `kd_status = "not_assessed"`, covers the case where baseline expression was never
  measured at all (NaN — e.g. a guide-less generic upload that had no NTC/guide table): this is
  genuinely *unknown*, not a measured failure, and is deliberately **not** penalized (the `unknown != 0`
  rule, `data_governance_checklist.md` §3). `KD_THRESHOLD_VERSION = "kd_status/v2"`.

## 4. What this toolkit adds on top (and what it doesn't)

This toolkit (`src/3_DE_analysis/*`) does not recompute DE, pseudobulk aggregation, or the NTC
knockdown t-test — those are upstream, already-validated computations from the GWT dataset release
(bioRxiv `10.64898/2025.12.23.696273v1`). What it adds:

- `kd_status` (confirmed/weak/not_measurable/not_assessed): a 4-state summary of the guide-level
  knockdown test above, gating whether downstream DE for that target-condition should be trusted at all
  (see `readiness_engine.py`'s `kd_not_measurable`/`kd_weak` red-flag overrides, which cap the readiness
  call — a target whose own knockdown can't be confirmed cannot be `advance`d regardless of how strong
  its downstream DE signal looks). `not_assessed` (no KD data at all) is not a red flag: it is unknown,
  not a measured failure, so it is not penalized — such rows are still bounded by the real robustness
  gates (no guide data caps the grade at 2).
- `statistical_evidence_grade` (1-4) and `score_cap_reason`: a coarser reproducibility gate on top of
  the upstream `keep_for_DE` flags (minimum cells, cross-donor/cross-guide correlation, off-target
  flag) — see `build_target_cards.py`.
- `condition_specificity_score` / `condition_specificity_zscore`: see the code comment in
  `build_target_cards.py` directly above where these are computed for an explicit statement that the
  ratio-based version is a heuristic, not a statistical interaction test, and why a rigorous
  condition x perturbation interaction test is out of scope without per-guide/per-cell modeling this
  toolkit does not have access to.

## 5. Calibration against known biology

`src/3_DE_analysis/calibration.py`'s `control_panel_calibration()` checks both directions against the
above gates on the real reference dataset:

- **Negative controls** (`kd_status == "not_measurable"`, 4,774 rows): **99.96%** correctly land at
  grade 1, **0%** incorrectly reach grade >=3, **0%** reach an `advance`/`validate` readiness call.
  (Row count is 4,774 rather than the earlier 5,084 because `kd_status/v2` reclassified the 310 rows
  with a *never-measured* NaN baseline as `not_assessed` — genuinely unknown — instead of lumping them
  into the measured-below-floor `not_measurable` population.)
- **Positive controls** (21-gene panel of well-established CD4 phenotypes — CD3D/E/G, CD28, ICOS,
  CTLA4, CD80/86, IL2RA, IL2RB, IL7R, LCK, ZAP70, JAK3, PTPN2, FOXP3, PTGER4, STAT5A/B, TNFRSF9): only
  **20%** reach the strict `statistical_evidence_grade >= 3` bar (which requires cross-donor AND
  cross-guide robustness with >=2 guides simultaneously, in a specific condition) — but **93.1%** are
  *not* `deprioritize`d by the readiness engine, which weighs pathway/biology knowledge alongside the
  strict statistical replication gate. This is a real, honest finding, not a target to be hidden or
  papered over: grade 3/4 is intentionally a narrow "everything about this specific condition-row lines
  up" bar, not a proxy for "is this a biologically real target." Loosening it just to make the positive
  control panel look better would be calibrating the metric to the answer rather than validating it —
  the more actionable interpretation is that `statistical_evidence_grade` and `readiness_call` answer
  different questions, and a low grade with a non-deprioritized readiness call is itself informative
  (see the per-target `score_cap_reason` for exactly why a given condition-row didn't clear grade 3/4).
