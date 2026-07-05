# Topic 9 - Current Data EDA Report

## Scope

This is a **summary-table EDA**, not a full single-cell EDA. The full cell-level `.h5ad` files are not local, so this report cannot assess per-cell QC, normalization, embeddings, guide assignment residuals, doublets, or model residuals.

The local EDA uses:

- `metadata/suppl_tables/sample_metadata.suppl_table.csv`
- `metadata/suppl_tables/DE_stats.suppl_table.csv`
- `metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv`
- `metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv`

Generated outputs are in `sources/topic09_eda_outputs/`.

## Data inventory

| Table | Rows | Key content |
|---|---:|---|
| sample metadata | 12 | donor, condition, run, library, donor demographics |
| DE stats | 33,983 | target-condition DE summaries and robustness fields |
| guide KD efficiency | 73,765 | guide-level knockdown statistics across conditions |
| sgRNA library metadata | 26,504 | guide design, target gene, nearby gene/off-target annotations |

The DE table covers 11,526 unique target genes across `Rest`, `Stim8hr`, and `Stim48hr`.

## Sample design

The experiment has 4 donors across 3 culture conditions:

- `Rest`
- `Stim8hr`
- `Stim48hr`

Donors are balanced across conditions, but the run structure is not fully balanced:

- `Rest`: split across `CD4i_R1` and `CD4i_R2`
- `Stim8hr`: split across `CD4i_R1` and `CD4i_R2`
- `Stim48hr`: entirely in `CD4i_R2`

This means `Stim48hr` condition-specific claims need a run/batch caveat.

## DE summary

DE effects are highly long-tailed:

| Condition | Rows | Targets | Median target cells | Median DE genes | Mean DE genes | On-target significant | Off-target flagged |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rest | 11,287 | 11,287 | 543 | 2 | 53.1 | 60.9% | 8.4% |
| Stim48hr | 11,281 | 11,281 | 548 | 2 | 59.4 | 63.8% | 8.0% |
| Stim8hr | 11,415 | 11,415 | 526 | 2 | 68.9 | 62.7% | 8.7% |

Interpretation:

- Most perturbations have small transcriptomic effects.
- A small high-impact tail drives the high mean.
- `Stim8hr` has the strongest high-DE tail, consistent with acute TCR/stimulation biology.

Category counts:

- Roughly 14-17% of rows show no effect.
- Roughly 22-23% of rows have `>10` DE genes.
- About 35-38% of rows have no on-target KD category, so DE breadth alone is not enough for prioritization.

## High-DE and robustness findings

Using `n_total_de_genes >= 50`:

- 4,182 high-DE target-condition rows.
- 1,368 Rest, 1,433 Stim8hr, 1,381 Stim48hr.
- Cross-donor metrics available for 3,910 rows, or 93.5%.
- Cross-guide metrics available for 2,520 rows, or 60.3%.
- Low cross-donor flag: 906 rows.
- Low cross-guide flag: 619 rows.
- Low-cell flag: 1,201 rows.

The high-DE subset is useful, but still needs robustness filtering.

## Minimal actionable filter

For a high-confidence local CSV candidate table, use:

```text
n_total_de_genes >= 50
ontarget_significant == True
offtarget_flag == False
n_cells_target >= 200
crossdonor_correlation_mean >= 0.2
crossguide_correlation >= 0.2
```

This stricter filter leaves about 1,208 high-confidence target-condition rows.

Suggested caveats:

- Missing `crossguide_correlation`: keep as biology candidate, not highest-confidence.
- `n_cells_target < 200`: low-cell caution.
- `crossdonor` or `crossguide < 0.2`: robustness caution.
- `Stim48hr-only` claim: add run/batch caveat.
- `offtarget_flag == True`: do not promote without follow-up.

## Top hit patterns

Strong expected T cell biology:

- `PLCG1`
- `CD247`
- `ITK`
- `CD3E`
- `LAT`
- `ZAP70`
- `LCP2`
- `VAV1`
- `BCL10`
- `PTPRC`
- `LCK`

These are useful positive biology signals, especially in `Stim8hr`. Some have low-cell or missing cross-guide caveats.

Broad/chromatin/essential-like effects:

- `TADA2B`
- `SGF29`
- `SUPT20H`
- `TADA1`
- `CCNC`
- `TAF13`
- `KDM1A`
- `NFRKB`
- `MED12`
- `CREBBP`
- `LEO1`
- `ELOB`
- `DENR`
- `TFAM`
- `ARNT`
- `ATP2A2`

These may be real and robust, but should not be interpreted as narrow immune pathway hits without essentiality, viability, and pathway checks.

Caution examples:

- Off-target flagged top hits: `TADA2B` in some conditions, `CD3D`, `CD3G`, `TAF6L`.
- Low guide robustness: `SENP5`, `BCAT2`, `LRBA`, `ATF7IP2`, `FITM2`, `SLC3A2`, `CALCOCO2`, `CHD7`.
- Low donor robustness: `UBXN1`, `DOP1B`, `EIF1AX`, `ZMYM2`.
- Low-cell caution: `ZAP70`, `LCP2`, `LCK`, `PGGT1B`, `SKIC8`.

There are 153 robust high-DE targets appearing across all three conditions. These should be prioritized for pan-condition pathway, druggability, essentiality, and off-target review.

## Generated outputs

Key files:

- `sources/topic09_eda_outputs/eda_summary.json`
- `sources/topic09_eda_outputs/eda_table_inventory.csv`
- `sources/topic09_eda_outputs/sample_by_run_condition.csv`
- `sources/topic09_eda_outputs/sample_by_donor_condition.csv`
- `sources/topic09_eda_outputs/de_summary_by_condition.csv`
- `sources/topic09_eda_outputs/top100_targets_by_total_de_genes.csv`
- `sources/topic09_eda_outputs/top100_targets_ontarget_no_offtarget.csv`
- `sources/topic09_eda_outputs/batch_robustness_risk_table_de50.csv`
- `sources/topic09_eda_outputs/hist_n_total_de_genes_by_condition.png`
- `sources/topic09_eda_outputs/scatter_crossdonor_vs_crossguide.png`
- `sources/topic09_eda_outputs/scatter_cells_vs_de_genes.png`

## Recommended next analyses

1. Build a high-confidence ranked hit table using the minimal filter above.
2. Separate pan-condition targets from condition-specific targets.
3. Separate TCR/proximal activation biology from broad chromatin/essential-like effects.
4. Join DE summaries to guide KD efficiency to test whether DE breadth tracks actual knockdown strength.
5. Add druggability and essentiality annotations from local gene class lists, DepMap/Open Targets/ChEMBL later.
6. Treat `Stim48hr` target claims as batch-sensitive unless supported by donor/guide robustness or external evidence.
7. Use full h5ad later for per-cell QC, UMAP/PCA, guide assignment diagnostics, Mixscape/SCEPTRE/pertpy, and cell-state-specific effects.
