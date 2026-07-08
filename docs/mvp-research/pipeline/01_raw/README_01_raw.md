# 01 · Raw 層 — 原始 DE 統計資料

## 這一層是什麼
本層存放**未經任何修改**的原始輸入資料，作為整條 pipeline 的唯一真實來源（single source of truth）。所有下游轉換皆從此檔案衍生，本層本身不做任何清理或運算。

## 輸入資料
- **檔名**：`DE_stats.suppl_table.csv`
- **維度**：33,983 列 × 16 欄
- **語意**：11,526 個基因標的（target）× 3 個培養條件（Rest / Stim8hr / Stim48hr）的**聚合差異表現（Differential Expression, DE）統計**。
- **重要說明**：這是**已經算好的聚合 DE 統計**，不是原始單細胞 count 矩陣。每一列代表「某個 CRISPR 敲降標的在某培養條件下」對轉錄組造成的整體擾動摘要。

## 資料來源與驗證
| 項目 | 值 |
|---|---|
| 原始檔 MD5 | `f5cf2e070bc8a2fb2ce0c584b3277c4c` |
| 來源 | GWT bioRxiv 論文之 supplementary table |
| 公開資料桶 | S3 bucket `genome-scale-tcell-perturb-seq` |

> MD5 已於載入時以程式重新計算並確認吻合，確保本層資料與論文原始附錄逐位元一致。

## 16 欄原始欄位字典
| 欄名 | 型別 | 意義 |
|---|---|---|
| `index` | str | 列識別碼，格式 `<ENSG>_<condition>` |
| `target_contrast_gene_name` | str | 標的基因的 HGNC symbol（如 A1BG） |
| `culture_condition` | str | 培養條件：`Rest` / `Stim8hr` / `Stim48hr` |
| `target_contrast` | str | 標的基因的 Ensembl gene ID（ENSG…），為唯一標的鍵 |
| `chunk` | int | 實驗批次／運算分塊編號 |
| `n_cells_target` | float | 該標的擾動下擷取到的細胞數 |
| `n_up_genes` | int | 顯著上調的基因數 |
| `n_down_genes` | int | 顯著下調的基因數 |
| `n_total_de_genes` | int | 顯著差異表現的基因總數（DE 廣度） |
| `ontarget_effect_size` | float | 對標的基因自身的敲降效應量（log2FC 類；負值＝有效敲降） |
| `ontarget_significant` | bool | 標的自身敲降是否統計顯著 |
| `target_baseMean` | float | 標的基因的基礎平均表現量（未擾動水準） |
| `offtarget_flag` | bool | 是否有脫靶疑慮 |
| `n_total_genes_category` | str | DE 廣度的類別標籤 |
| `ontarget_effect_category` | str | 標的效應的類別標籤 |
| `n_downstream` | int | 下游受影響的基因數 |

## 結果意義
本層保存論文附錄的原貌，供稽核與可重現性追溯之用。任何對數字有疑義時，都應回到本檔案重新核對。

## 使用資料與參考文獻
- Zhu R., Dann E. *et al.* (2025) *Genome-scale perturb-seq in primary human CD4+ T cells.* bioRxiv.
- 資料桶：公開 S3 `genome-scale-tcell-perturb-seq`。
