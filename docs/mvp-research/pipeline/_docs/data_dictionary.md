# 資料字典彙整 — GWT CD4+ T Perturb-seq 標的探索 MVP

四層 pipeline：`01_raw → 02_curated → 03_processed → 04_statistical`。所有欄位皆從原始 DE 統計逐步衍生，數字可完全重現。

---

## 資料來源與驗證
| 項目 | 值 |
|---|---|
| 原始檔 | `DE_stats.suppl_table.csv`（33,983 × 16） |
| MD5 | `f5cf2e070bc8a2fb2ce0c584b3277c4c` |
| 來源 | GWT bioRxiv 論文 supplementary table |
| S3 桶 | `genome-scale-tcell-perturb-seq`（公開） |
| 資料性質 | 已聚合的差異表現（DE）統計，非原始 count |

---

## 01 raw — 原始 16 欄
| 欄名 | 型別 | 來源 | 說明 |
|---|---|---|---|
| `index` | str | raw | 列識別碼 `<ENSG>_<condition>` |
| `target_contrast_gene_name` | str | raw | 標的 HGNC symbol |
| `culture_condition` | str | raw | Rest / Stim8hr / Stim48hr |
| `target_contrast` | str | raw | 標的 Ensembl ID（唯一標的鍵） |
| `chunk` | int | raw | 批次／分塊編號 |
| `n_cells_target` | float | raw | 該標的細胞數 |
| `n_up_genes` | int | raw | 上調基因數 |
| `n_down_genes` | int | raw | 下調基因數 |
| `n_total_de_genes` | int | raw | DE 基因總數 |
| `ontarget_effect_size` | float | raw | 標的自身敲降效應量 |
| `ontarget_significant` | bool | raw | 標的敲降是否顯著 |
| `target_baseMean` | float | raw | 標的基礎平均表現 |
| `offtarget_flag` | bool | raw | 脫靶旗標 |
| `n_total_genes_category` | str | raw | DE 廣度類別 |
| `ontarget_effect_category` | str | raw | 效應類別 |
| `n_downstream` | int | raw | 下游受影響基因數 |

## 02 curated — 新增／變更欄（其餘同上）
| 欄名 | 型別 | 來源 | 如何衍生 |
|---|---|---|---|
| `ontarget_significant` | bool | raw | 標準化為真正 bool |
| `offtarget_flag` | bool | raw | 標準化為真正 bool |
| `passes_gate` | bool | 衍生 | `(n_cells_target>=200) & ontarget_significant & (~offtarget_flag) & (n_total_de_genes>=50)` |
| `logDE` | float | 衍生 | `log10(n_total_de_genes + 1)` |

輸出：`curated_targets.csv`（33,983 × 18）。

## 03 processed
| 檔案 | 結構 | 說明 |
|---|---|---|
| `effect_matrix.csv` | 11,526 × 4（1 個 index 欄 `target_contrast_gene_name` + 3 個條件值欄 Rest/Stim8hr/Stim48hr） | 標的 × 條件 的 `ontarget_effect_size` pivot |
| `de_matrix.csv` | 11,526 × 4（1 個 index 欄 `target_contrast_gene_name` + 3 個條件值欄 Rest/Stim8hr/Stim48hr） | 標的 × 條件 的 `n_total_de_genes` pivot |
| `gate_passing_targets.csv` | 2,131 × 18 | `passes_gate=True` 的子集 |

pivot 檔欄位：`target_contrast_gene_name`(index) + `Rest` / `Stim8hr` / `Stim48hr`（float，缺格 NaN）。

## 04 statistical
### summary_statistics.csv（`metric`, `value`）
n_rows=33983、n_unique_targets=11526、n_ontarget_significant=21216、n_offtarget_flag=2837、n_gate_passing_rows=2131、n_gate_passing_unique_targets=1235、count_Rest=11287、count_Stim8hr=11415、count_Stim48hr=11281、nde_median=2、nde_max=5920、effect_min≈-58.55、effect_median≈-6.30、effect_max≈7.09、ncells_median=539、corr_nde_ndownstream≈1.00、frac_logde_lt1≈0.756、set_significant_genelevel=7913。

### condition_stats.csv
| 欄名 | 型別 | 如何衍生 |
|---|---|---|
| `culture_condition` | str | 分組鍵 |
| `n_up_genes_sum` | int | 該條件 `n_up_genes` 加總 |
| `n_down_genes_sum` | int | 該條件 `n_down_genes` 加總 |
| `n_targets` | int | 該條件唯一標的數 |

---

## 參考文獻
- Zhu R., Dann E. *et al.* (2025) *Genome-scale perturb-seq in primary human CD4+ T cells.* bioRxiv.
