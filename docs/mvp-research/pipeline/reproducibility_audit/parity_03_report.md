# STAGE 03 Reproducibility Audit — Processed Matrices (R vs Python vs Artifact)

## Scope
Independent recomputation of the two STAGE 03 processed matrices from the raw curated
DE supplementary table, in **R** and **Python separately**, then cell-level parity
comparison against each other and checksum comparison against the existing artifacts.

- **Raw input:** `v11c6348b_DE_stats.suppl_table.csv` (33,983 data rows; 11,526 targets x 3 conditions)
- **effect_matrix:** pivot(index=`target_contrast_gene_name`, columns=`culture_condition`, values=`ontarget_effect_size`)
- **de_matrix:** pivot(same index/columns, values=`n_total_de_genes`)
- **Conditions:** Rest, Stim48hr, Stim8hr (canonically sorted)

## Data integrity
- (target, condition) pairs are unique — pivot is well-defined (no aggregation).
- Raw **value columns** (`ontarget_effect_size`, `n_total_de_genes`) have 0 NA.
- **However**, the raw table has only 33,983 rows vs 11,526 x 3 = 34,578 possible
  (target, condition) combinations, so **595 combinations are absent** and become
  NaN after the pivot. Each matrix therefore contains **595 NA cells** (out of
  34,578). Downstream users must handle missing values in effect_matrix/de_matrix.

## Shapes (must match across all three sources)
| matrix | Python | R | Artifact |
|---|---|---|---|
| effect_matrix | 11526x4 | 11526x4 | 11526x4 |
| de_matrix | 11526x4 | 11526x4 | 11526x4 |

(Shape includes the index column; 11526 rows x 3 condition columns + 1 index = 4.)

## Cell-level parity (tolerance abs < 1e-9)
| matrix | comparison | cells compared | mismatches | max abs diff | NA pattern match |
|---|---|---|---|---|---|
| effect_matrix | R vs Python | 34,578 | 0 | 3.553e-15 | True |
| de_matrix | R vs Python | 34,578 | 0 | 0.000e+00 | True |
| effect_matrix | Python vs artifact | 34,578 | 0 | 0.000e+00 | True |
| de_matrix | Python vs artifact | 34,578 | 0 | 0.000e+00 | True |

(Cells compared = 11526 x 3 value cells = 34,578, excluding the index column.)

## Canonical-sort checksum vs existing artifact
- effect_matrix: MD5 match = **True**
- de_matrix: MD5 match = **True**

## Verdict
- **R == Python:** PASS — 0 cell mismatches in both matrices. The only numeric
  difference is a max abs diff of 3.55e-15 in effect_matrix,
  which is floating-point round-off well below the 1e-9 tolerance (R vs pandas
  CSV round-trip). de_matrix is bit-identical (integer counts).
- **NA-pattern agreement:** PASS — R, Python, and the artifact share the **exact
  same NA mask** (identical 595 NA cells per matrix, in the same positions). Note
  this is agreement of the *pattern*, not absence of NA: 595 cells per matrix ARE
  NA (absent target/condition combinations).
- **Python == existing artifact:** PASS — both matrices reproduce the stored
  artifacts exactly (checksum + 0 cell mismatch).
- **Shapes:** PASS — 11526x4 across Python, R, and artifact for both matrices.

STAGE 03 processed output is independently reproducible and R/Python-identical.
