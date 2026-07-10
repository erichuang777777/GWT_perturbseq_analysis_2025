# Reproducibility Audit — Stage 01 → 02 (raw → curated)

**Subject:** CD4+ T-cell Perturb-seq curation stage.
**Question:** Can the curated stage output be independently recomputed from raw, and do R and Python give identical results?

## Inputs
- **RAW** `DE_stats.suppl_table.csv` — 33,983 rows × 16 columns (target × condition DE statistics).
- **Existing curated artifact** `curated_targets.csv` — 33,983 rows × 18 columns (raw + `passes_gate` + `logDE`).
- **Existing gate_passing artifact** `gate_passing_targets.csv` — 2,131 rows × 18 columns (gate-passing subset).

## Method
Two independent scripts recompute the stage from raw with **no shared code** and **no read** of the existing artifacts:
- `curated_recompute_py.py` (Python 3.11 / pandas)
- `curated_recompute_r.R` (R 4.5.3 / readr + dplyr)

### Curation logic (recomputed in both)
| Output column | Calc logic |
|---|---|
| `passes_gate` | `(n_cells_target >= 200) AND (ontarget_significant == True) AND (offtarget_flag == False) AND (n_total_de_genes >= 50)`; any NA term → False (NA-safe AND) |
| `logDE` | `log10(n_total_de_genes + 1)` |
| all 16 original columns | passed through unchanged |

**Curated targets** = gate-passing rows, deduplicated to unique `target_contrast` (keep-first).

## Results

### 1. Recompute counts (both languages, independently)
- Full table: **33,983 rows**
- `passes_gate == True`: **2,131 rows**
- Unique curated targets: **1,235** ✓ (matches expected)

### 2. Row-level / cell-level R ↔ Python parity (curated_targets, 1,235 rows)
- Rows matched on `target_contrast`: **1,235 / 1,235** (identical key sets)
- Cells compared: **20,995** (1,235 rows × 17 shared columns)
- **Cell mismatches: 0**
- Mismatching keys: **none**
- Numeric columns agree to within floating-point noise (max abs diff ≤ 7.1e-15 on `target_baseMean`, ≤ 4.4e-16 on `ontarget_effect_size`; all other columns exact).

**→ R and Python produce identical results (`r_equals_py = True`).**

### 3. Agreement with the existing artifacts (canonical-sorted md5)
| Comparison | md5-byte-identical | Value-identical (tol 1e-9) |
|---|---|---|
| Python vs existing `curated` artifact | ✅ `c4fd4f22…` = `c4fd4f22…` | ✅ |
| R vs existing `curated` artifact | ❌ `1741f3da…` ≠ `c4fd4f22…` | ✅ (0 mismatches) |
| Python vs existing `gate_passing` artifact | ✅ `f994bfd3…` = `f994bfd3…` | ✅ (0 mismatches) |
| R vs existing `gate_passing` artifact | ❌ `dc3be0b0…` ≠ `f994bfd3…` (same reason) | ✅ (0 mismatches) |

All four artifact comparisons above are computed explicitly and recorded as rows in `parity_01_02.csv` (`comparison` = `artifact_md5` / `artifact_value` for the full 33,983-row curated table, and `gate_passing_md5` / `gate_passing_value` for the 2,131-row gate-passing subset). The gate_passing subset (2,131 rows) was verified independently — not merely inferred from the curated result.

**Why R's md5 differs (serialization, not computation):** `readr::write_csv` renders numbers differently from the pandas writer that produced the original artifact:
- integer-valued floats: pandas wrote `686.0`, R writes `686` (33,983 cells);
- a handful of doubles differ in the last representable digit, e.g. `-27.52791250984742` (artifact) vs `-27.527912509847425` (R) — a ~1e-13 text-rounding difference (5 cells in `ontarget_effect_size`, 8 in `target_baseMean`).

Compared value-by-value with a 1e-9 tolerance, **R reproduces the existing artifact exactly (0 mismatches)**. Python reproduces it byte-for-byte because it shares the pandas serializer with the original pipeline.

## Verdict
- The stage output is **independently reproducible** from raw. ✅
- **R and Python agree at the value level, cell-for-cell** across all 1,235 curated targets. ✅
- Python reproduction is **byte-identical** to the shipped artifacts. ✅
- R reproduction is **value-identical**; its only divergence from the artifacts is CSV float-formatting, with no effect on any computed quantity. ✅

## Files
- `curated_recompute_py.py` — Python recompute script (reproducibility package)
- `curated_recompute_r.R` — R recompute script (reproducibility package)
- `parity_01_02.csv` — per-column parity table (n_compared, n_mismatch, max_abs_diff, exact_match, calc_logic)
- `parity_01_02_report.md` — this report
