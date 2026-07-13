# EDA — 原始資料 · Raw data

> **本階段目標為何 · Stage goal**
>
> 凍結唯一的上游輸入,作為整條 in-repo pipeline 的可稽核起點。此階段**不重算**任何值——它就是 provider 交付的聚合 DESeq2 pseudobulk DE 統計(每 target×condition 一列)加樣本表。更上游(原始單細胞 ~1.67 TB、DE_stats h5ad 15.6 GB)只在 S3,離線不可重跑,故此層為「可稽核、不可重生成」。
> Freeze the sole upstream input as the auditable entry point; nothing here is recomputed. Everything before this file is S3-only and not re-runnable offline.

**輸入 · Inputs**
- (upstream, S3-only) GWCD4i.DE_stats.h5ad — 15.6 GB, not in repo

**重現指令 · Reproduce**: 不可離線重生成;md5 對 FREEZE_MANIFEST.csv 01_raw 稽核。See docs/REPRODUCIBILITY.md §8.

> `unknown != 0`: 缺失以 missingness% 呈現,類別分佈保留 `(missing)` 桶;NaN 不會被當成 0。

## DE_stats.suppl_table.csv

- **path**: `docs/mvp-research/pipeline/01_raw/data/DE_stats.suppl_table.csv`
- **shape** (parsed records): **33,983 rows × 16 cols**
- **md5**: `f5cf2e070bc8a2fb2ce0c584b3277c4c`  (cross-check FREEZE_MANIFEST.csv)

### Schema & missingness
| column | dtype | missing % | distinct |
|---|---|---|---|
| `index` | str | 0.0% | 33983 |
| `target_contrast_gene_name` | str | 0.0% | 11526 |
| `culture_condition` | str | 0.0% | 3 |
| `target_contrast` | str | 0.0% | 11526 |
| `chunk` | int64 | 0.0% | 681 |
| `n_cells_target` | float64 | 0.0% | 2060 |
| `n_up_genes` | int64 | 0.0% | 965 |
| `n_down_genes` | int64 | 0.0% | 747 |
| `n_total_de_genes` | int64 | 0.0% | 1279 |
| `ontarget_effect_size` | float64 | 0.0% | 28134 |
| `ontarget_significant` | bool | 0.0% | 2 |
| `target_baseMean` | float64 | 17.2% | 28133 |
| `offtarget_flag` | bool | 0.0% | 2 |
| `n_total_genes_category` | str | 0.0% | 4 |
| `ontarget_effect_category` | str | 0.0% | 3 |
| `n_downstream` | int64 | 0.0% | 1280 |

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

### Categorical / low-cardinality distributions
- **`culture_condition`**: `Stim8hr`=11415 · `Rest`=11287 · `Stim48hr`=11281
- **`ontarget_significant`**: `True`=21216 · `False`=12767
- **`offtarget_flag`**: `False`=31146 · `True`=2837
- **`n_total_genes_category`**: `2-10 DE genes`=13767 · `>10 DE genes`=7570 · `1 DE gene`=7420 · `no effect`=5226
- **`ontarget_effect_category`**: `on-target KD`=21216 · `no on-target KD`=12383 · `putative off-target`=384

## sample_metadata.suppl_table.csv

- **path**: `docs/mvp-research/pipeline/01_raw/data/sample_metadata.suppl_table.csv`
- **shape** (parsed records): **12 rows × 19 cols**
- **md5**: `b1d826797332b5640f35868fefadd105`  (cross-check FREEZE_MANIFEST.csv)

### Schema & missingness
| column | dtype | missing % | distinct |
|---|---|---|---|
| `Unnamed: 0` | int64 | 0.0% | 12 |
| `cell_sample_id` | str | 0.0% | 12 |
| `10xrun_id` | str | 0.0% | 2 |
| `donor_id` | str | 0.0% | 4 |
| `culture_condition` | str | 0.0% | 3 |
| `library_id` | str | 0.0% | 12 |
| `library_prep_kit` | str | 0.0% | 1 |
| `probe_hyb_loading` | str | 0.0% | 4 |
| `GEM_loading` | str | 0.0% | 1 |
| `sequencing_platform` | str | 0.0% | 1 |
| `age` | int64 | 0.0% | 4 |
| `sex` | str | 0.0% | 2 |
| `ethnicity` | str | 0.0% | 3 |
| `weight_kg` | int64 | 0.0% | 4 |
| `height_cm` | int64 | 0.0% | 2 |
| `smoker` | str | 0.0% | 1 |
| `blood_type` | str | 0.0% | 1 |
| `anticoagulant` | str | 0.0% | 1 |
| `harvest_date` | str | 0.0% | 3 |

### Numeric summary
| column | count | missing % | min | median | max | mean |
|---|---|---|---|---|---|---|
| `Unnamed: 0` | 12 | 0.0% | 0 | 5.5 | 11 | 5.5 |
| `age` | 12 | 0.0% | 22 | 26 | 34 | 27 |
| `weight_kg` | 12 | 0.0% | 58 | 71.5 | 87 | 72 |
| `height_cm` | 12 | 0.0% | 160 | 160 | 180 | 165 |

### Categorical / low-cardinality distributions
- **`cell_sample_id`**: `CD4i_R1_D1_Rest`=1 · `CD4i_R1_D1_Stim8hr`=1 · `CD4i_R1_D2_Rest`=1 · `CD4i_R1_D2_Stim8hr`=1 · `CD4i_R2_D1_Stim48hr`=1 · `CD4i_R2_D2_Stim48hr`=1 · `CD4i_R2_D3_Rest`=1 · `CD4i_R2_D3_Stim48hr`=1 · `CD4i_R2_D3_Stim8hr`=1 · `CD4i_R2_D4_Rest`=1 · `CD4i_R2_D4_Stim48hr`=1 · `CD4i_R2_D4_Stim8hr`=1
- **`10xrun_id`**: `CD4i_R2`=8 · `CD4i_R1`=4
- **`donor_id`**: `CE0006864`=3 · `CE0008162`=3 · `CE0008678`=3 · `CE0010866`=3
- **`culture_condition`**: `Rest`=4 · `Stim48hr`=4 · `Stim8hr`=4
- **`library_id`**: `CD4i_R1_D1_Rest_CD4i_R1_Ultima`=1 · `CD4i_R1_D1_Stim8hr_CD4i_R1_Ultima`=1 · `CD4i_R1_D2_Rest_CD4i_R1_Ultima`=1 · `CD4i_R1_D2_Stim8hr_CD4i_R1_Ultima`=1 · `CD4i_R2_D1_Stim48hr_CD4i_R2_Ultima`=1 · `CD4i_R2_D2_Stim48hr_CD4i_R2_Ultima`=1 · `CD4i_R2_D3_Rest_CD4i_R2_Ultima`=1 · `CD4i_R2_D3_Stim48hr_CD4i_R2_Ultima`=1 · `CD4i_R2_D3_Stim8hr_CD4i_R2_Ultima`=1 · `CD4i_R2_D4_Rest_CD4i_R2_Ultima`=1 · `CD4i_R2_D4_Stim48hr_CD4i_R2_Ultima`=1 · `CD4i_R2_D4_Stim8hr_CD4i_R2_Ultima`=1
- **`library_prep_kit`**: `GEMX_flex_v2`=12
- **`probe_hyb_loading`**: `2M cells/probe, 40uL GEX probe, BC001-004, CRISPR probe, CR001-004`=3 · `2M cells/probe, 40uL GEX probe, BC005-008, CRISPR probe, CR005-008`=3 · `2M cells/probe, 40uL GEX probe, BC009-012, CRISPR probe, CR009-012`=3 · `2M cells/probe, 40uL GEX probe, BC013-016, CRISPR probe, CR013-016`=3
- **`GEM_loading`**: `1M cells/GEM`=12
- **`sequencing_platform`**: `Ultima`=12
- **`sex`**: `Female`=9 · `Male`=3
- **`ethnicity`**: `African American`=6 · `Asian`=3 · `Hispanic`=3
- **`smoker`**: `No`=12
- **`blood_type`**: `O+`=12
- **`anticoagulant`**: `ACDA`=12
- **`harvest_date`**: `2/3/25`=6 · `1/28/25`=3 · `3/20/25`=3

---
_Regenerate: `python scripts/generate_stage_eda.py`. Deterministic (no timestamp); guarded by `tests/test_generate_stage_eda.py`. Part of the release freeze — see `docs/mvp-research/pipeline/EDA_INDEX.md`._
