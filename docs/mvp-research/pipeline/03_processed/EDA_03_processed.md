# EDA — 處理後資料 · Processed

> **本階段目標為何 · Stage goal**
>
> 把通過門檻的列 pivot 成 target×condition 矩陣(effect
> DE-count),並輸出 gate-passing 子集(2,131 列 → 1,235 unique targets),供下游統計與視覺化。
> Pivot gate-passing rows into target×condition matrices and emit the gate-passing subset for downstream stats.

**輸入 · Inputs**
- 02_curated/data/curated_targets.csv

**重現指令 · Reproduce**: reproducibility_bundle_v2.tar.gz 內 processed_{py,r};cell-level max diff 3.6e-15。

> `unknown != 0`: 缺失以 missingness% 呈現,類別分佈保留 `(missing)` 桶;NaN 不會被當成 0。

## effect_matrix.csv

- **path**: `docs/mvp-research/pipeline/03_processed/data/effect_matrix.csv`
- **shape** (parsed records): **11,526 rows × 4 cols**
- **md5**: `dfb61e0c3a65fe1e9efa22fb85260018`  (cross-check FREEZE_MANIFEST.csv)

### Schema & missingness
| column | dtype | missing % | distinct |
|---|---|---|---|
| `target_contrast_gene_name` | object | 0.0% | 11526 |
| `Rest` | float64 | 2.1% | 9354 |
| `Stim8hr` | float64 | 1.0% | 9442 |
| `Stim48hr` | float64 | 2.1% | 9340 |

### Numeric summary
| column | count | missing % | min | median | max | mean |
|---|---|---|---|---|---|---|
| `Rest` | 11287 | 2.1% | -58.55 | -5.923 | 2.482 | -7.42 |
| `Stim8hr` | 11415 | 1.0% | -51.47 | -6.488 | 7.092 | -8.184 |
| `Stim48hr` | 11281 | 2.1% | -54.9 | -6.529 | 3.227 | -8.217 |

### Categorical / low-cardinality distributions
_(no low-cardinality categorical columns)_

## de_matrix.csv

- **path**: `docs/mvp-research/pipeline/03_processed/data/de_matrix.csv`
- **shape** (parsed records): **11,526 rows × 4 cols**
- **md5**: `3e6c03522620d0575445fdda70bf3b08`  (cross-check FREEZE_MANIFEST.csv)

### Schema & missingness
| column | dtype | missing % | distinct |
|---|---|---|---|
| `target_contrast_gene_name` | object | 0.0% | 11526 |
| `Rest` | float64 | 2.1% | 685 |
| `Stim8hr` | float64 | 1.0% | 733 |
| `Stim48hr` | float64 | 2.1% | 718 |

### Numeric summary
| column | count | missing % | min | median | max | mean |
|---|---|---|---|---|---|---|
| `Rest` | 11287 | 2.1% | 0 | 2 | 4681 | 53.1 |
| `Stim8hr` | 11415 | 1.0% | 0 | 2 | 5920 | 68.92 |
| `Stim48hr` | 11281 | 2.1% | 0 | 2 | 5260 | 59.42 |

### Categorical / low-cardinality distributions
_(no low-cardinality categorical columns)_

## gate_passing_targets.csv

- **path**: `docs/mvp-research/pipeline/03_processed/data/gate_passing_targets.csv`
- **shape** (parsed records): **2,131 rows × 18 cols**
- **md5**: `5efd16dec06be518b3302609781f76e8`  (cross-check FREEZE_MANIFEST.csv)

### Schema & missingness
| column | dtype | missing % | distinct |
|---|---|---|---|
| `index` | object | 0.0% | 2131 |
| `target_contrast_gene_name` | object | 0.0% | 1235 |
| `culture_condition` | object | 0.0% | 3 |
| `target_contrast` | object | 0.0% | 1235 |
| `chunk` | int64 | 0.0% | 654 |
| `n_cells_target` | float64 | 0.0% | 934 |
| `n_up_genes` | int64 | 0.0% | 732 |
| `n_down_genes` | int64 | 0.0% | 603 |
| `n_total_de_genes` | int64 | 0.0% | 896 |
| `ontarget_effect_size` | float64 | 0.0% | 2131 |
| `ontarget_significant` | bool | 0.0% | 1 |
| `target_baseMean` | float64 | 0.0% | 2131 |
| `offtarget_flag` | bool | 0.0% | 1 |
| `n_total_genes_category` | object | 0.0% | 1 |
| `ontarget_effect_category` | object | 0.0% | 1 |
| `n_downstream` | int64 | 0.0% | 896 |
| `passes_gate` | bool | 0.0% | 1 |
| `logDE` | float64 | 0.0% | 896 |

### Numeric summary
| column | count | missing % | min | median | max | mean |
|---|---|---|---|---|---|---|
| `chunk` | 2131 | 0.0% | 0 | 335 | 680 | 335.2 |
| `n_cells_target` | 2131 | 0.0% | 200 | 496 | 1.151e+04 | 643.5 |
| `n_up_genes` | 2131 | 0.0% | 4 | 129 | 3833 | 304.2 |
| `n_down_genes` | 2131 | 0.0% | 1 | 77 | 1878 | 196.6 |
| `n_total_de_genes` | 2131 | 0.0% | 50 | 216 | 5711 | 500.8 |
| `ontarget_effect_size` | 2131 | 0.0% | -58.55 | -11.74 | -0.1175 | -13.3 |
| `target_baseMean` | 2131 | 0.0% | 0.1201 | 48.92 | 4325 | 79.59 |
| `n_downstream` | 2131 | 0.0% | 49 | 215 | 5710 | 499.8 |
| `logDE` | 2131 | 0.0% | 1.708 | 2.336 | 3.757 | 2.404 |

### Categorical / low-cardinality distributions
- **`culture_condition`**: `Rest`=712 · `Stim8hr`=711 · `Stim48hr`=708
- **`ontarget_significant`**: `True`=2131
- **`offtarget_flag`**: `False`=2131
- **`n_total_genes_category`**: `>10 DE genes`=2131
- **`ontarget_effect_category`**: `on-target KD`=2131
- **`passes_gate`**: `True`=2131

---
_Regenerate: `python scripts/generate_stage_eda.py`. Deterministic (no timestamp); guarded by `tests/test_generate_stage_eda.py`. Part of the release freeze — see `docs/mvp-research/pipeline/EDA_INDEX.md`._
