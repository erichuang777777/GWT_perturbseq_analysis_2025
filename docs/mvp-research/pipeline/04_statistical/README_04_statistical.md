# 04 · Statistical 層 — 統計摘要

## 這一層是什麼
統計摘要層。將全體資料濃縮成兩張表：一張跨全域的 key-value 摘要，一張逐條件的擾動方向統計。這些數字是整個 MVP 的「儀表板讀數」，也是可重現性的驗收點。

## 輸入
- `02_curated/curated_targets.csv`（含衍生欄）

## 輸出

### summary_statistics.csv（欄：`metric`, `value`）
| metric | value | 意義 |
|---|---|---|
| `n_rows` | 33983 | 總列數 |
| `n_unique_targets` | 11526 | 唯一標的數（依 `target_contrast` ENSG） |
| `n_ontarget_significant` | 21216 | 標的敲降顯著的列數 |
| `n_offtarget_flag` | 2837 | 帶脫靶旗標的列數 |
| `n_gate_passing_rows` | 2131 | 通過 MVP 門檻的列數 |
| `n_gate_passing_unique_targets` | 1235 | 通過門檻的唯一標的數 |
| `count_Rest` | 11287 | Rest 條件列數 |
| `count_Stim8hr` | 11415 | Stim8hr 條件列數 |
| `count_Stim48hr` | 11281 | Stim48hr 條件列數 |
| `nde_median` | 2 | DE 基因數中位數 |
| `nde_max` | 5920 | DE 基因數最大值 |
| `effect_min` | ≈ -58.55 | 最強敲降效應量 |
| `effect_median` | ≈ -6.30 | 效應量中位數 |
| `effect_max` | ≈ 7.09 | 效應量最大值 |
| `ncells_median` | 539 | 每標的細胞數中位數 |
| `corr_nde_ndownstream` | ≈ 1.00 | DE 基因數與下游基因數的相關係數 |
| `frac_logde_lt1` | ≈ 0.756 | `logDE < 1` 的列比例 |
| `set_significant_genelevel` | 7913 | 基因層次：任一條件顯著的獨特基因數 |

**衍生方式**：
- `set_significant_genelevel` ＝ 在 `ontarget_significant=True` 的列中，`target_contrast_gene_name` 的獨特值數目（把三條件收合到基因層次）。
- `corr_nde_ndownstream` ＝ `n_total_de_genes` 與 `n_downstream` 的 Pearson 相關（≈1.0 表兩者幾乎等價，`n_downstream` 可視為 DE 廣度的代理）。

### condition_stats.csv
| 欄名 | 型別 | 來源 | 如何衍生 |
|---|---|---|---|
| `culture_condition` | str | curated | 分組鍵 |
| `n_up_genes_sum` | int | 衍生 | 該條件 `n_up_genes` 加總 |
| `n_down_genes_sum` | int | 衍生 | 該條件 `n_down_genes` 加總 |
| `n_targets` | int | 衍生 | 該條件唯一標的數 |

實際值：

| 條件 | n_up_genes_sum | n_down_genes_sum | n_targets |
|---|---|---|---|
| Rest | 371,945 | 227,402 | 11,287 |
| Stim8hr | 506,326 | 280,429 | 11,415 |
| Stim48hr | 392,533 | 277,789 | 11,281 |

## 結果意義與描述
- 全域中位數 DE 基因數僅 2、`frac_logde_lt1 ≈ 0.756`——絕大多數敲降轉錄影響微弱，少數強效標的貢獻長尾（最大 5,920）。
- `Stim8hr` 的上調總量最高（506,326），顯示 T 細胞刺激早期（8 小時）轉錄活化最劇烈，符合活化動力學。
- `corr_nde_ndownstream ≈ 1.00`：`n_downstream` 與 `n_total_de_genes` 近乎共線，建模時應擇一避免共線性。
- 基因層次有 **7,913** 個獨特基因在至少一個條件下敲降顯著，是可探索標的的上界。

## 可重現性驗收
本層所有數字皆在生成腳本中以 `assert` 對照預期值，全部通過。任何數字偏移都會使 pipeline 失敗，確保與論文附錄一致。

## 使用資料與參考文獻
- 上游：`02_curated`。
- Zhu R., Dann E. *et al.* (2025) *Genome-scale perturb-seq in primary human CD4+ T cells.* bioRxiv.
- 資料桶：公開 S3 `genome-scale-tcell-perturb-seq`；原始 MD5 `f5cf2e070bc8a2fb2ce0c584b3277c4c`。
