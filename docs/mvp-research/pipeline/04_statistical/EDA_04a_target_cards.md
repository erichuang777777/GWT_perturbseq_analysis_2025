# EDA — 初步結果 · Target cards (canonical 39-col)

> **本階段目標為何 · Stage goal**
>
> 把統計證據組裝成決策就緒的 target cards(39 欄:效應/顯著性/敲低狀態/穩健性/等級/藥理與疾病 overlay)。這是使用者實際看到的產品資料;kd_status 遵守 unknown≠0(not_assessed vs not_measurable)。
> Assemble per-target-per-condition decision-ready cards (the canonical 39-col product).

**輸入 · Inputs**
- metadata/suppl_tables/DE_stats.suppl_table.csv
- metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv
- metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv

**重現指令 · Reproduce**: cd src/3_DE_analysis && python build_target_cards.py --de-stats ... --output ...  (see docs/REPRODUCIBILITY.md §6.4)

> `unknown != 0`: 缺失以 missingness% 呈現,類別分佈保留 `(missing)` 桶;NaN 不會被當成 0。

## target_cards.csv (a6bba17b, canonical)

- **path**: `sources/target_tool_cache/a6bba17b-f194-4a50-8cf8-96e03eededd6/target_cards.csv`
- **shape** (parsed records): **33,983 rows × 39 cols**
- **md5**: `400c21fa7fa382de56c9f5578cf72ecb`  (cross-check FREEZE_MANIFEST.csv)

### Schema & missingness
| column | dtype | missing % | distinct |
|---|---|---|---|
| `target` | object | 0.0% | 11526 |
| `condition` | object | 0.0% | 3 |
| `target_id` | object | 0.0% | 11526 |
| `n_cells_target` | float64 | 0.0% | 2060 |
| `n_guides` | int64 | 0.0% | 4 |
| `n_total_de_genes` | int64 | 0.0% | 1279 |
| `n_up_genes` | int64 | 0.0% | 965 |
| `n_down_genes` | int64 | 0.0% | 747 |
| `ontarget_effect_size` | float64 | 0.0% | 28134 |
| `ontarget_significant` | bool | 0.0% | 2 |
| `offtarget_flag` | bool | 0.0% | 2 |
| `median_logFC` | float64 | 0.0% | 28134 |
| `max_abs_logFC` | float64 | 0.0% | 28134 |
| `fdr_min` | float64 | 0.9% | 7427 |
| `crossdonor_correlation_mean` | float64 | 85.9% | 4774 |
| `crossdonor_correlation_min` | float64 | 85.9% | 4770 |
| `crossguide_correlation` | float64 | 91.2% | 2994 |
| `replicate_pass_flag` | bool | 0.0% | 2 |
| `batch_sensitivity_flag` | object | 0.0% | 3 |
| `guide_signif_ratio` | float64 | 0.0% | 5 |
| `guide_fdr_min` | float64 | 0.9% | 7427 |
| `guide_t_abs_median` | float64 | 0.9% | 32081 |
| `positive_control_similarity` | int64 | 0.0% | 2 |
| `pathway_axis` | object | 0.0% | 11 |
| `condition_specificity_score` | float64 | 0.0% | 6140 |
| `condition_specificity_zscore` | float64 | 0.0% | 2136 |
| `effect_direction_flip_flag` | bool | 0.0% | 2 |
| `clinical_axis` | object | 0.0% | 8 |
| `nearest_success_drug` | object | 99.9% | 6 |
| `nearest_failure_or_warning` | float64 | 100.0% | 0 |
| `target_baseline_expression` | float64 | 0.9% | 32081 |
| `kd_status` | object | 0.0% | 4 |
| `kd_threshold_version` | object | 0.0% | 1 |
| `statistical_evidence_grade` | int64 | 0.0% | 4 |
| `score_cap_reason` | object | 0.0% | 186 |
| `n_donors` | float64 | 100.0% | 0 |
| `druggable_class` | object | 86.5% | 9 |
| `tractability_modality` | object | 86.5% | 4 |
| `safety_note` | object | 82.6% | 9 |

### Numeric summary
| column | count | missing % | min | median | max | mean |
|---|---|---|---|---|---|---|
| `n_cells_target` | 33983 | 0.0% | 17 | 539 | 1.151e+04 | 603.5 |
| `n_guides` | 33983 | 0.0% | 0 | 2 | 3 | 1.955 |
| `n_total_de_genes` | 33983 | 0.0% | 0 | 2 | 5920 | 60.51 |
| `n_up_genes` | 33983 | 0.0% | 0 | 1 | 4151 | 37.4 |
| `n_down_genes` | 33983 | 0.0% | 0 | 1 | 2434 | 23.12 |
| `ontarget_effect_size` | 33983 | 0.0% | -58.55 | -6.305 | 7.092 | -7.941 |
| `median_logFC` | 33983 | 0.0% | -58.55 | -6.305 | 7.092 | -7.941 |
| `max_abs_logFC` | 33983 | 0.0% | 0 | 6.305 | 58.55 | 7.95 |
| `fdr_min` | 33673 | 0.9% | 1e-16 | 1e-16 | 1 | 0.1334 |
| `crossdonor_correlation_mean` | 4775 | 85.9% | -0.9973 | 0.4123 | 1 | 0.3706 |
| `crossdonor_correlation_min` | 4775 | 85.9% | -1 | 0.277 | 1 | 0.2426 |
| `crossguide_correlation` | 2994 | 91.2% | -0.9925 | 0.499 | 0.9999 | 0.4356 |
| `guide_signif_ratio` | 33983 | 0.0% | 0 | 1 | 1 | 0.7685 |
| `guide_fdr_min` | 33673 | 0.9% | 1e-16 | 1e-16 | 1 | 0.1334 |
| `guide_t_abs_median` | 33673 | 0.9% | 0 | 16.24 | 273.5 | 21.49 |
| `positive_control_similarity` | 33983 | 0.0% | 0 | 0 | 1 | 0.001442 |
| `condition_specificity_score` | 33983 | 0.0% | 0 | 0.2857 | 1 | 0.3193 |
| `condition_specificity_zscore` | 33983 | 0.0% | -0.2312 | -0.2092 | 20.24 | 6.691e-18 |
| `nearest_failure_or_warning` | 0 | 100.0% | — | — | — | — |
| `target_baseline_expression` | 33673 | 0.9% | 0 | 0.1864 | 4.785 | 0.3235 |
| `statistical_evidence_grade` | 33983 | 0.0% | 1 | 2 | 4 | 1.629 |
| `n_donors` | 0 | 100.0% | — | — | — | — |

### Categorical / low-cardinality distributions
- **`condition`**: `Stim8hr`=11415 · `Rest`=11287 · `Stim48hr`=11281
- **`ontarget_significant`**: `True`=21216 · `False`=12767
- **`offtarget_flag`**: `False`=31146 · `True`=2837
- **`replicate_pass_flag`**: `False`=32881 · `True`=1102
- **`batch_sensitivity_flag`**: `not_flagged`=22702 · `sensitive`=10108 · `confounded_but_robust`=1173
- **`pathway_axis`**: `unassigned`=33832 · `Cytokine_signaling`=28 · `TCR_core`=24 · `Costimulation`=21 · `Th17`=15 · `Th2`=15 · `Trafficking`=15 · `Exhaustion`=12 · `Th1`=12 · `Treg`=6 · `Cell_cycle`=3
- **`effect_direction_flip_flag`**: `False`=33247 · `True`=736
- **`clinical_axis`**: `unassigned`=33776 · `TCR/CD3 tolerance`=88 · `JAK/STAT cytokine signaling`=36 · `Direct CD4`=33 · `Calcineurin/NFAT`=21 · `S1P trafficking`=15 · `Costimulation blockade`=9 · `IL-2 / IL-2R`=5
- **`nearest_success_drug`**: (missing)=33947 · `abatacept; belatacept`=15 · `adalimumab; infliximab; etanercept; golimumab; certolizumab`=6 · `ibalizumab`=6 · `basiliximab; aldesleukin; denileukin diftitox`=3 · `fingolimod; ozanimod; etrasimod`=3 · `tacrolimus; cyclosporine`=3
- **`kd_status`**: `confirmed`=27882 · `not_measurable`=4774 · `weak`=1017 · `not_assessed`=310
- **`kd_threshold_version`**: `kd_status/v2`=33983
- **`druggable_class`**: (missing)=29391 · `enzymes`=1704 · `transporters`=910 · `kinases`=711 · `gpcr_union`=375 · `catalytic_receptors`=333 · `ion_channels`=299 · `nuclear_receptors`=137 · `gpi_anchored`=111 · `cytokine_receptors`=12
- **`tractability_modality`**: (missing)=29391 · `small molecule`=4136 · `small molecule / biologic`=333 · `antibody (surface)`=111 · `antibody / biologic`=12
- **`safety_note`**: (missing)=28077 · `clinvar_pathogenic_or_likely_pathogenic`=5576 · `immune_effector:Cytokine`=81 · `immune_effector:Receptor`=81 · `immune_effector:TF`=62 · `clinvar_pathogenic_or_likely_pathogenic;immune_effector:Receptor`=50 · `clinvar_pathogenic_or_likely_pathogenic;immune_effector:TF`=26 · `clinvar_pathogenic_or_likely_pathogenic;immune_effector:Cytokine`=24 · `clinvar_pathogenic_or_likely_pathogenic;immune_effector:Others`=3 · `immune_effector:Others`=3

---
_Regenerate: `python scripts/generate_stage_eda.py`. Deterministic (no timestamp); guarded by `tests/test_generate_stage_eda.py`. Part of the release freeze — see `docs/mvp-research/pipeline/EDA_INDEX.md`._
