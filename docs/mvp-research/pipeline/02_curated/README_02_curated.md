# 02 · Curated 層 — 清理與衍生欄位

## 這一層是什麼
清理層。在**保留全部 33,983 列**的前提下，將布林欄標準化、加上 MVP 篩選門檻旗標與衍生特徵，讓下游分析可直接使用。此層不刪列、不去重，只增欄。

## 輸入
- `01_raw/DE_stats.suppl_table.csv`（33,983 × 16）

## 如何 curated（轉換步驟）
1. **布林欄標準化**：將 `ontarget_significant`、`offtarget_flag` 統一轉為真正的 Python `bool`（防止字串 "True"/"False" 或 0/1 混入）。
2. **加 `passes_gate` 欄（MVP 品質門檻）**，四條件同時成立才為 True：
   - `n_cells_target >= 200`（細胞數足夠）
   - `ontarget_significant == True`（標的確實被顯著敲降）
   - `offtarget_flag == False`（無脫靶疑慮）
   - `n_total_de_genes >= 50`（下游擾動足夠廣，具生物意義）
3. **加 `logDE` 欄** ＝ `log10(n_total_de_genes + 1)`，將重尾的 DE 廣度壓縮成近似常態尺度，利於視覺化與建模。

## 輸出
- **`curated_targets.csv`**：33,983 列 × 18 欄（原 16 欄 + `passes_gate` + `logDE`）。

## 輸出欄位字典（僅列衍生／變更欄）
| 欄名 | 型別 | 來源 | 如何衍生 |
|---|---|---|---|
| `ontarget_significant` | bool | raw | 型別標準化為真正 bool |
| `offtarget_flag` | bool | raw | 型別標準化為真正 bool |
| `passes_gate` | bool | 衍生 | `(n_cells_target>=200) & ontarget_significant & (~offtarget_flag) & (n_total_de_genes>=50)` |
| `logDE` | float | 衍生 | `log10(n_total_de_genes + 1)` |

（其餘 14 欄同 `01_raw/README.md`。）

## 結果意義與描述
- 全體 33,983 列中，**21,216 列** 標的敲降統計顯著、**2,837 列** 帶脫靶旗標。
- 套用四合一門檻後，**2,131 列** 通過（對應 **1,235 個唯一標的**）——這是 MVP 標的探索的高信心候選集，僅佔全體約 6.3%。
- `logDE < 1`（即 DE 基因數 ≤ 8）的列佔 **75.6%**，反映絕大多數敲降只造成小幅轉錄擾動，門檻篩選有其必要。

## 使用資料與參考文獻
- 上游：`01_raw`（GWT bioRxiv supplementary table，S3 `genome-scale-tcell-perturb-seq`，MD5 `f5cf2e070bc8a2fb2ce0c584b3277c4c`）。
- Zhu R., Dann E. *et al.* (2025) *Genome-scale perturb-seq in primary human CD4+ T cells.* bioRxiv.
