# Topic 8 - 資料有批次效應需要校正嗎

## Executive takeaways

Yes, assume the GWT CD4 Perturb-seq data has donor/run/library/lane nuisance structure. But do **not** apply a blanket batch correction to expression values for final target-card DE.

For this dataset, the default should be:

- Analyze `Rest`, `Stim8hr`, and `Stim48hr` separately for target cards.
- Use raw-count or pseudobulk count models for inferential DE.
- Include donor/sample/cell-count/technical covariates where estimable.
- Use guide-level and donor-level robustness as confidence evidence.
- Use Harmony/scVI/BBKNN/MNN mainly for embeddings, clustering, diagnostics, and sensitivity checks, not as the primary source of DE evidence.

Batch correction should modify confidence; it should not create the target effect.

## Local design observations

From local `sample_metadata.suppl_table.csv`:

- 12 biological donor-condition samples.
- 4 donors, each measured in `Rest`, `Stim8hr`, and `Stim48hr`.
- `Rest` and `Stim8hr` span `CD4i_R1` and `CD4i_R2` with donors nested in run.
- `Stim48hr` is all `CD4i_R2`.

From `DE_stats.suppl_table.csv`:

- 33,983 target-condition DE rows.
- `crossdonor_correlation_mean/min` available for 4,775 rows.
- `crossguide_correlation` available for 2,994 rows.
- These robustness fields are useful confidence flags, but not all targets have them.

From local DE config:

- The main DE model uses `~ log10_n_cells + donor_id + target`.
- This is consistent with a pseudobulk/covariate model strategy rather than expression-level batch correction.

## What to correct or model

| Factor | Recommendation | Reason |
|---|---|---|
| Donor | model/block donor; report cross-donor robustness | donor biology is real and relevant to clinical translation |
| Culture condition | do not correct away; analyze separately | Rest/Stim8hr/Stim48hr are biological activation states |
| 10x run / sequencing batch | use for QC and sensitivity where estimable | run effects are partly confounded with donor/condition |
| Library/lane | use for QC and h5ad-stage diagnostics | library can be sample-specific and may absorb real biology |
| Guide ID | do not treat only as nuisance | guide is perturbation evidence; use cross-guide consistency |
| Cell cycle/proliferation | score and report, do not regress out by default | proliferation may be true CD4 perturbation phenotype |
| Activation/cytokine programs | score and report, do not regress out by default | these are often the desired biology |
| Raw counts for DE | do not replace with integrated/corrected values | corrected expression can distort inferential effect sizes |

## CSV-first batch-risk analysis

Current local files can support a useful batch-risk report without h5ad:

1. Sample design/confounding matrix:
   - `donor_id x culture_condition x 10xrun_id x library_id x sequencing_platform x harvest_date`

2. Target-condition robustness table:
   - `target_contrast_gene_name`
   - `culture_condition`
   - `n_cells_target`
   - `n_total_de_genes`
   - `ontarget_effect_size`
   - `ontarget_significant`
   - `offtarget_flag`
   - `crossdonor_correlation_mean`
   - `crossdonor_correlation_min`
   - `crossguide_correlation`

3. Batch-risk flags:
   - strong DE but low donor robustness
   - strong DE but low guide concordance
   - low target-cell count
   - off-target flag
   - effect present only in a design-confounded condition
   - target rank unstable after filtering low-robustness rows

4. Plots/tables:
   - effect size vs cross-donor correlation
   - effect size vs cross-guide correlation
   - DE-gene count vs robustness
   - cell count vs robustness
   - target rank before/after robustness filters

CSV cannot correct expression-level batch effects. It can only triage risk and identify targets needing h5ad-level reanalysis.

## h5ad-stage batch diagnosis

The 12 cell-level h5ad files are needed for actual batch diagnosis:

- QC distributions by donor, condition, run, library, lane.
- guide UMI burden, guide multiplicity, cells per guide/target.
- NTC-only PCA/UMAP before and after correction.
- all-cell PCA/UMAP before and after correction.
- pseudobulk PCA labeled by donor, condition, run, perturbation.
- batch-mixing metrics: ASW/silhouette, LISI, kBET, graph connectivity.
- DE concordance: baseline pseudobulk model vs technical-covariate model vs correction sensitivity.
- Mixscape/pertpy non-responder or escaped perturbation checks.
- SCEPTRE or related calibrated perturbation-gene association tests.

## Correction strategy

Recommended comparison arms:

1. No correction: baseline retained for all analyses.
2. Pseudobulk/raw-count model: include donor and count/QC covariates; include technical covariates only where estimable.
3. Harmony/MNN/BBKNN: embedding and neighborhood sensitivity, preferably within condition.
4. scVI: latent representation from raw counts with technical batch as `batch_key`; handle donor/condition carefully as biological covariates.
5. ComBat/ComBat-seq: only for balanced pseudobulk sensitivity analyses; do not use when batch is confounded with donor, condition, or perturbation.

## What not to do

- Do not force `Rest`, `Stim8hr`, and `Stim48hr` into one corrected expression space for target effect inference.
- Do not regress out activation, cytokine, proliferation, or exhaustion programs by default.
- Do not correct away donor wholesale; donor robustness is evidence.
- Do not use batch-corrected expression or integrated embeddings as primary DE input.
- Do not trust targets that only become significant after aggressive correction unless raw-count/pseudobulk evidence and external biology agree.

## Impact on drug-readiness scoring

Batch/covariate analysis should feed target cards as confidence fields:

- Upgrade confidence when target direction is stable across donors/guides and reasonable correction strategies.
- Downgrade confidence when effect is driven by one donor, one guide, one run, one library, or low cell count.
- Cap readiness at `validate` or `watchlist` if batch-risk flags are strong.
- Preserve condition-specific effects when biologically meaningful; do not penalize a target solely for being Rest- or Stim-specific.

Suggested target-card fields:

```text
donor_n
donor_ids
run_coverage
n_cells_target
n_guides
guide_ids
guide_kd_efficiency
crossdonor_correlation_mean
crossdonor_correlation_min
crossguide_correlation
ontarget_effect_size
ontarget_significant
offtarget_flag
cell_cycle_signature_flag
activation_signature_flag
batch_caveat
correction_sensitivity_call
```

## Key references

- GWT CD4 Perturb-seq data/preprint: DOI `10.64898/2025.12.23.696273v1`.
- scRNA best practices: PMID `31217225`, DOI `10.15252/msb.20188746`.
- Batch correction benchmark: PMID `31948481`, DOI `10.1186/s13059-019-1850-9`.
- Atlas-level integration benchmark: PMID `34949812`, DOI `10.1038/s41592-021-01336-8`.
- scVI: PMID `30504886`, DOI `10.1038/s41592-018-0229-2`.
- Harmony: PMID `31740819`, DOI `10.1038/s41592-019-0619-0`.
- Pseudoreplication in single-cell studies: PMID `33531494`, DOI `10.1038/s41467-021-21038-1`.
- Replicate-aware single-cell DE / muscat: PMID `33257685`, DOI `10.1038/s41467-020-19894-4`.
- Single-cell DE shortcomings: PMID `40098192`, DOI `10.1186/s13059-025-03525-6`.
- Perturb-seq: PMID `27984732`, DOI `10.1016/j.cell.2016.11.038`.
- SCEPTRE: PMID `34930414`, DOI `10.1186/s13059-021-02545-2`.
- SCEPTRE low-MOI update: PMID `38760839`, DOI `10.1186/s13059-024-03254-2`.
- Mixscape/ECCITE-seq: PMID `33649593`, DOI `10.1038/s41588-021-00778-2`.
