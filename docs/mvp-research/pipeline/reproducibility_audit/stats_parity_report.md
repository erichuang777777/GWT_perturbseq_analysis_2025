# Stage 04 — Statistical Summary Reproducibility & R↔Python Parity Report

**Scope.** Independent third-party audit of the CD4+ T-cell Perturb-seq
statistical-summary stage. Two scripts recompute every summary statistic
directly from the raw DE supplementary table — one in Python 3.11
(`stats_recompute_py.py`), one in R 4.5.3 (`stats_recompute_r.R`) — with no
shared code and no dependency on the existing `summary_statistics` artifact.
Their outputs are then compared metric-by-metric.

## Inputs
- **Raw table:** `v11c6348b_DE_stats.suppl_table.csv` — 33,983 rows × 16 columns.
- **Reference (not used for computation, only cross-checked):** `v419a18fa_summary_statistics.csv` (18 metrics).

## Result — full parity

| | |
|---|---|
| Metrics compared | **24** |
| PASS | **24** |
| FAIL | **0** |
| CJK characters in outputs | **none** |

All 24 metrics agree between R and Python. Integer/count/median/extremum
metrics match **exactly** (abs_diff = 0). The two floating-point aggregates
that could differ by numerical path — `corr_nde_ndownstream` and
`frac_logde_lt1` — agree to machine precision: the only nonzero difference in
the entire table is `corr_nde_ndownstream` at **4.44e-16** (one ULP), far
below the `abs<1e-6` tolerance.

## Independent reproduction confirmed
All **18** metrics present in the pre-existing `summary_statistics` artifact
were reproduced from raw by both scripts with zero mismatch (tolerance 1e-6).
The recompute is therefore an independent confirmation of the original stage
output, not a re-read of it. Every expected value supplied for the audit
(n_rows=33983, n_unique_targets=11526, n_ontarget_significant=21216,
n_offtarget_flag=2837, gate_rows=2131, gate_targets=1235, condition counts
11287/11415/11281, nde_median=2, nde_max=5920, effect_min=-58.548,
effect_median=-6.305, effect_max=7.092, ncells_median=539, corr≈1.0,
frac_logde_lt1=0.756, set_sig=7913) was matched.

## Metrics (row-level parity)

Each row is one metric; parity is asserted per metric, not just on an
aggregate pass count.

| metric | R_value | Python_value | abs_diff | tolerance | result |
|---|---|---|---|---|---|
| n_rows | 33983 | 33983 | 0.00e+00 | 0 (exact integer) | PASS |
| n_unique_targets | 11526 | 11526 | 0.00e+00 | 0 (exact integer) | PASS |
| n_ontarget_significant | 21216 | 21216 | 0.00e+00 | 0 (exact integer) | PASS |
| n_offtarget_flag | 2837 | 2837 | 0.00e+00 | 0 (exact integer) | PASS |
| n_gate_passing_rows | 2131 | 2131 | 0.00e+00 | 0 (exact integer) | PASS |
| n_gate_passing_unique_targets | 1235 | 1235 | 0.00e+00 | 0 (exact integer) | PASS |
| count_Rest | 11287 | 11287 | 0.00e+00 | 0 (exact integer) | PASS |
| count_Stim8hr | 11415 | 11415 | 0.00e+00 | 0 (exact integer) | PASS |
| count_Stim48hr | 11281 | 11281 | 0.00e+00 | 0 (exact integer) | PASS |
| nde_median | 2 | 2 | 0.00e+00 | 0 (exact integer) | PASS |
| nde_max | 5920 | 5920 | 0.00e+00 | 0 (exact integer) | PASS |
| effect_min | -58.547976668913336 | -58.547976668913336 | 0.00e+00 | abs<1e-6 | PASS |
| effect_median | -6.30463745267495 | -6.30463745267495 | 0.00e+00 | abs<1e-6 | PASS |
| effect_max | 7.091937721582496 | 7.091937721582496 | 0.00e+00 | abs<1e-6 | PASS |
| ncells_median | 539 | 539 | 0.00e+00 | 0 (exact integer) | PASS |
| corr_nde_ndownstream | 0.9999984688704547 | 0.9999984688704552 | 4.44e-16 | abs<1e-6 | PASS |
| frac_logde_lt1 | 0.7561427772709884 | 0.7561427772709884 | 0.00e+00 | abs<1e-6 | PASS |
| set_significant_genelevel | 7913 | 7913 | 0.00e+00 | 0 (exact integer) | PASS |
| sum_up_Rest | 371945 | 371945 | 0.00e+00 | 0 (exact integer) | PASS |
| sum_down_Rest | 227402 | 227402 | 0.00e+00 | 0 (exact integer) | PASS |
| sum_up_Stim8hr | 506326 | 506326 | 0.00e+00 | 0 (exact integer) | PASS |
| sum_down_Stim8hr | 280429 | 280429 | 0.00e+00 | 0 (exact integer) | PASS |
| sum_up_Stim48hr | 392533 | 392533 | 0.00e+00 | 0 (exact integer) | PASS |
| sum_down_Stim48hr | 277789 | 277789 | 0.00e+00 | 0 (exact integer) | PASS |

## Notes on method choices
- **Gate rule** `n_cells_target>=200 & ontarget_significant & !offtarget_flag & n_total_de_genes>=50`, with NA→FALSE, applied identically in both languages.
- **Boolean normalisation** is defensive in both scripts (accepts native logical or "True"/"False" strings), so parity does not depend on CSV reader behaviour.
- **Extra rows** (`sum_up_*`, `sum_down_*`) extend the original 18 metrics with per-condition up/down DE-gene totals; these were not in the reference artifact but are recomputed and cross-validated here.
- **The 4.44e-16 difference** on the Pearson correlation reflects a different floating-point summation order between NumPy's `corrcoef` and R's `cor`; it is numerical noise, not a logic difference.

## Reproducibility package
- `stats_recompute_py.py` — Python recompute (argv: raw_csv, out_json).
- `stats_recompute_r.R` — R recompute (argv: raw_csv, out_json).
- `cross_validation_results_en.csv` — the 24-metric parity table (fully English).
- `stats_parity_report.md` — this report.

**Verdict: PASS.** The stage output is independently reproducible, and R and
Python produce identical results within stated tolerances.
