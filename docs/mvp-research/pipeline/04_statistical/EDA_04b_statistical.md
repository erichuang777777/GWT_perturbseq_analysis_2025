# EDA — 統計檢定 · Statistical summaries + validation

> **本階段目標為何 · Stage goal**
>
> 彙整全域統計(門檻/分佈/條件別)與方法學驗證(known-regulator ranking AUROC 0.85、dropout 診斷、情境專一性 artifact vs true)。這是「檢定層」——把處理後資料轉成可判讀的統計宣稱。
> Aggregate global/per-condition statistics and the methodological-validation artifacts.

**輸入 · Inputs**
- 03_processed/*
- 04_results (target_cards)

**重現指令 · Reproduce**: summary/condition_stats 由 statistical_{py,r} 重算(24/24 parity PASS);benchmark_results 為凍結驗證輸出。

> `unknown != 0`: 缺失以 missingness% 呈現,類別分佈保留 `(missing)` 桶;NaN 不會被當成 0。

## summary_statistics.csv

- **path**: `docs/mvp-research/pipeline/04_statistical/data/summary_statistics.csv`
- **shape** (parsed records): **18 rows × 2 cols**
- **md5**: `f562a9c49313142dc238931c8a5d3b67`  (cross-check FREEZE_MANIFEST.csv)

### Schema & missingness
| column | dtype | missing % | distinct |
|---|---|---|---|
| `metric` | str | 0.0% | 18 |
| `value` | float64 | 0.0% | 18 |

### Numeric summary
| column | count | missing % | min | median | max | mean |
|---|---|---|---|---|---|---|
| `value` | 18 | 0.0% | -58.55 | 2484 | 3.398e+04 | 6735 |

### Categorical / low-cardinality distributions
- **`metric`**: `corr_nde_ndownstream`=1 · `count_Rest`=1 · `count_Stim48hr`=1 · `count_Stim8hr`=1 · `effect_max`=1 · `effect_median`=1 · `effect_min`=1 · `frac_logde_lt1`=1 · `n_gate_passing_rows`=1 · `n_gate_passing_unique_targets`=1 · `n_offtarget_flag`=1 · `n_ontarget_significant`=1 · `n_rows`=1 · `n_unique_targets`=1 · `ncells_median`=1 · (other)=3

## condition_stats.csv

- **path**: `docs/mvp-research/pipeline/04_statistical/data/condition_stats.csv`
- **shape** (parsed records): **3 rows × 4 cols**
- **md5**: `5ffe137dffe32da8f13f3660eb6c53cc`  (cross-check FREEZE_MANIFEST.csv)

### Schema & missingness
| column | dtype | missing % | distinct |
|---|---|---|---|
| `culture_condition` | str | 0.0% | 3 |
| `n_up_genes_sum` | int64 | 0.0% | 3 |
| `n_down_genes_sum` | int64 | 0.0% | 3 |
| `n_targets` | int64 | 0.0% | 3 |

### Numeric summary
| column | count | missing % | min | median | max | mean |
|---|---|---|---|---|---|---|
| `n_up_genes_sum` | 3 | 0.0% | 371945 | 3.925e+05 | 506326 | 4.236e+05 |
| `n_down_genes_sum` | 3 | 0.0% | 227402 | 2.778e+05 | 280429 | 2.619e+05 |
| `n_targets` | 3 | 0.0% | 11281 | 1.129e+04 | 11415 | 1.133e+04 |

### Categorical / low-cardinality distributions
- **`culture_condition`**: `Rest`=1 · `Stim48hr`=1 · `Stim8hr`=1

## benchmark_results.csv (AUROC 0.85 set)

- **path**: `docs/mvp-research/pipeline/methodological_validation/benchmark_results.csv`
- **shape** (parsed records): **1,225 rows × 4 cols**
- **md5**: `4de9797db02301404ea4fb3d7fff9dd5`  (cross-check FREEZE_MANIFEST.csv)

### Schema & missingness
| column | dtype | missing % | distinct |
|---|---|---|---|
| `gene` | str | 0.0% | 1225 |
| `ctx_rank` | int64 | 0.0% | 1225 |
| `ctx_specific_de` | float64 | 0.0% | 630 |
| `truth_class` | str | 0.0% | 3 |

### Numeric summary
| column | count | missing % | min | median | max | mean |
|---|---|---|---|---|---|---|
| `ctx_rank` | 1225 | 0.0% | 1 | 613 | 1225 | 613 |
| `ctx_specific_de` | 1225 | 0.0% | 2 | 191 | 5707 | 408.9 |

### Categorical / low-cardinality distributions
- **`truth_class`**: `rest`=1211 · `positive`=13 · `negative`=1

---
_Regenerate: `python scripts/generate_stage_eda.py`. Deterministic (no timestamp); guarded by `tests/test_generate_stage_eda.py`. Part of the release freeze — see `docs/mvp-research/pipeline/EDA_INDEX.md`._
