# EDA — 清理資料 · Curated

> **本階段目標為何 · Stage goal**
>
> 對 raw 施加 MVP 品質門檻並標準化欄位:加 `passes_gate`(n_cells≥200 且顯著且非脫靶且 DE≥50)、`logDE`,不丟列(全 33,983 列保留,只加註記)。
> Apply the MVP quality gate and standardise columns without dropping rows — annotate pass/fail rather than filter.

**輸入 · Inputs**
- 01_raw/data/DE_stats.suppl_table.csv

**重現指令 · Reproduce**: reproducibility_bundle_v2.tar.gz 內 curated_{py,r};R==Python 0 mismatch。

> `unknown != 0`: 缺失以 missingness% 呈現,類別分佈保留 `(missing)` 桶;NaN 不會被當成 0。

## curated_targets.csv

- **path**: `docs/mvp-research/pipeline/02_curated/data/curated_targets.csv`
- **shape** (parsed records): **33,983 rows × 18 cols**
- **md5**: `5346cdd6e27237cc59419101088dcc3b`  (cross-check FREEZE_MANIFEST.csv)

### Schema & missingness
| column | dtype | missing % | distinct |
|---|---|---|---|
| `index` | object | 0.0% | 33983 |
| `target_contrast_gene_name` | object | 0.0% | 11526 |
| `culture_condition` | object | 0.0% | 3 |
| `target_contrast` | object | 0.0% | 11526 |
| `chunk` | int64 | 0.0% | 681 |
| `n_cells_target` | float64 | 0.0% | 2060 |
| `n_up_genes` | int64 | 0.0% | 965 |
| `n_down_genes` | int64 | 0.0% | 747 |
| `n_total_de_genes` | int64 | 0.0% | 1279 |
| `ontarget_effect_size` | float64 | 0.0% | 28134 |
| `ontarget_significant` | bool | 0.0% | 2 |
| `target_baseMean` | float64 | 17.2% | 28133 |
| `offtarget_flag` | bool | 0.0% | 2 |
| `n_total_genes_category` | object | 0.0% | 4 |
| `ontarget_effect_category` | object | 0.0% | 3 |
| `n_downstream` | int64 | 0.0% | 1280 |
| `passes_gate` | bool | 0.0% | 2 |
| `logDE` | float64 | 0.0% | 1279 |

### Numeric summary
| column | count | missing % | min | median | max | mean |
|---|---|---|---|---|---|---|
| `chunk` | 33983 | 0.0% | 0 | 340 | 680 | 339.7 |
| `n_cells_target` | 33983 | 0.0% | 17 | 539 | 1.151e+04 | 603.5 |
| `n_up_genes` | 33983 | 0.0% | 0 | 1 | 4151 | 37.4 |
| `n_down_genes` | 33983 | 0.0% | 0 | 1 | 2434 | 23.12 |
| `n_total_de_genes` | 33983 | 0.0% | 0 | 2 | 5920 | 60.51 |
| `ontarget_effect_size` | 33983 | 0.0% | -58.55 | -6.305 | 7.092 | -7.941 |
| `target_baseMean` | 28133 | 17.2% | 0.09815 | 27.44 | 4397 | 54.8 |
| `n_downstream` | 33983 | 0.0% | 0 | 2 | 5919 | 59.89 |
| `logDE` | 33983 | 0.0% | 0 | 0.4771 | 3.772 | 0.757 |

### Categorical / low-cardinality distributions
- **`culture_condition`**: `Stim8hr`=11415 · `Rest`=11287 · `Stim48hr`=11281
- **`ontarget_significant`**: `True`=21216 · `False`=12767
- **`offtarget_flag`**: `False`=31146 · `True`=2837
- **`n_total_genes_category`**: `2-10 DE genes`=13767 · `>10 DE genes`=7570 · `1 DE gene`=7420 · `no effect`=5226
- **`ontarget_effect_category`**: `on-target KD`=21216 · `no on-target KD`=12383 · `putative off-target`=384
- **`passes_gate`**: `False`=31852 · `True`=2131

---
_Regenerate: `python scripts/generate_stage_eda.py`. Deterministic (no timestamp); guarded by `tests/test_generate_stage_eda.py`. Part of the release freeze — see `docs/mvp-research/pipeline/EDA_INDEX.md`._
