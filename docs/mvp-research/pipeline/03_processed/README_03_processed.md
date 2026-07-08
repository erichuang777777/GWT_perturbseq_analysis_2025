# 03 · Processed 層 — 分析就緒資料

## 這一層是什麼
分析就緒層。把 curated 的長格式（long format）資料重整成標的×條件的**矩陣（pivot）**，並抽出通過門檻的候選集，方便直接餵入視覺化、聚類、降維與排序。

## 輸入
- `02_curated/curated_targets.csv`（33,983 × 18）

## 如何 processed（轉換步驟）
1. **`effect_matrix.csv`**：以 `target_contrast_gene_name` 為列、3 個條件為欄，值為 `ontarget_effect_size` 的 pivot。→ 11,526 × 4（1 個 index 欄 `target_contrast_gene_name` + 3 個條件值欄 Rest/Stim8hr/Stim48hr）。缺格（該標的在該條件無資料）為 NaN。
2. **`de_matrix.csv`**：同樣結構，值為 `n_total_de_genes`。→ 11,526 × 4（1 個 index 欄 `target_contrast_gene_name` + 3 個條件值欄 Rest/Stim8hr/Stim48hr）。
3. **`gate_passing_targets.csv`**：只保留 `passes_gate == True` 的列（2,131 列，18 欄），即高信心候選標的集。

> 條件欄一律照 `Rest → Stim8hr → Stim48hr` 的時間順序排列。

## 輸出欄位字典
### effect_matrix.csv / de_matrix.csv
| 欄名 | 型別 | 來源 | 如何衍生 |
|---|---|---|---|
| `target_contrast_gene_name` | str（index） | curated | pivot 列鍵 |
| `Rest` | float | curated | 該標的在 Rest 的 `ontarget_effect_size`（或 `n_total_de_genes`） |
| `Stim8hr` | float | curated | 同上，Stim8hr |
| `Stim48hr` | float | curated | 同上，Stim48hr |

### gate_passing_targets.csv
與 `02_curated/curated_targets.csv` 欄位完全相同（18 欄），僅列數縮減為 `passes_gate=True` 的 2,131 列。

## 結果意義與描述
- **effect_matrix / de_matrix**：讓每個標的的三時間點反應可橫向比較，直接支援「哪些標的的效應隨刺激時程變化」這類問題（如靜息 vs 刺激後才顯現的擾動）。
- **gate_passing_targets**：2,131 列 = 1,235 個唯一標的，是 MVP 排序與人工檢視的核心工作集。

## 使用資料與參考文獻
- 上游：`02_curated`。
- Zhu R., Dann E. *et al.* (2025) *Genome-scale perturb-seq in primary human CD4+ T cells.* bioRxiv.
- 資料桶：公開 S3 `genome-scale-tcell-perturb-seq`。
