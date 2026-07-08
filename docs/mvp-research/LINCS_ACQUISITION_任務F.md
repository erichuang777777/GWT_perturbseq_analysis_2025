# 任務 F — LINCS/CMap 取得管道（已建立，附誠實覆蓋限制）

**日期：** 2026-07-08 · 對照 PR #10 任務 F

## PR #10 的判斷更正
PR #10 說 F「資料不在 repo + 無免費 API」。**「無免費管道」不正確**——
所有 LINCS CMap L1000 資料都免費存放在 NCBI GEO（在 sandbox allowlist 內），
不需登入、不需付費 API。已實測下載成功。

## 資料來源（全部免費、GEO）
| Series | 內容 | 用途 |
|---|---|---|
| **GSE106127** | shRNA + CRISPR 基因擾動 L1000 signature（119,013 條）| **最相關**——基因敲低，同類型 |
| GSE92742 (Phase 1) | 化合物擾動 signature | 藥物 repurposing |
| GSE70138 (Phase 2) | 化合物擾動 signature | 藥物 repurposing |

關鍵檔（GSE106127 suppl/）：
- `GSE106127_sig_info.txt.gz` — signature→基因/細胞/類型 metadata
- `GSE106127_gene_info.txt.gz` — 978 landmark 基因
- `GSE106127_level_5_modz_n119013x978.gctx.gz` — moderated z-score（486MB，HDF5，用 `cmapPy` 讀）

## ★ 誠實覆蓋限制（實測，非臆測）— 使用前必讀

1. **細胞情境不符（最關鍵）：** GSE106127 的 15 個細胞株**全部是癌症細胞株**
   （A375/A549/MCF7/PC3/HEPG2/HT29/VCAP…），**零 T 細胞/淋巴細胞株**。
   我們的 perturb-seq 是原代 CD4+ T 細胞。跨情境 connectivity mapping 本質有偏差，
   任何 match 只能當弱假設，不能當確認。

2. **標的覆蓋率 = 4/15。** 有 LINCS signature 的基因：
   **PLCG1(24 條，免疫候選)**、SENP5(24，broad-effect)、CCNC(24，broad-effect)、PMVK(9，broad-effect)——全是 shRNA、癌症細胞株。
   5 個免疫候選中**只有 PLCG1 有覆蓋**；CD3E/LAT/CD247/VAV1 有 0 條（癌症細胞株不擾動這些基因）。
   → LINCS 覆蓋了一個排名最高的免疫標的（PLCG1，特別是它有 Angioedema 安全旗標），
   但對其餘 4 個免疫候選完全無法回答。

3. **Landmark 空間：** L1000 只直接量測 978 個 landmark 基因，其餘推斷。
   shortlist 沒有一個是 landmark——它們自己的敲低只在推斷空間讀出。
   （connectivity 用 978 基因的 response 向量，不阻塞計分，但解析度低於全轉錄組。）

## 結論
LINCS 是**輔助性、假設生成**的交叉參考，只覆蓋 4/15 個標的（PLCG1 是唯一被覆蓋的免疫候選，其餘 3 個為 broad-effect）。
**主要 query signature 必須來自任務 A**（在真實 CD4+ T 情境的每標的基因層 DE）。
**LINCS 不能取代 A。** 兩者關係：A 產出 query，LINCS 提供可比對的 reference。

## 已建立的檔案
- `lincs_reference_cache.py` — 取得 + 讀取 + connectivity 計分模組
- `lincs_demo_signatures_4genes.csv` — 4 個命中基因的真實 978-gene consensus z-score signature
- `lincs_shortlist_coverage.csv` — 15 基因逐一覆蓋狀態
- signature demo 已用真實 gctx 抽取驗證（如 PMVK 敲低強烈下調 EIF5，z=-4.7）
