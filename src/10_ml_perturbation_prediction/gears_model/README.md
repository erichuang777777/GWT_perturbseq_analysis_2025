# GEARS 風格模型（GO 知識圖譜 + 圖神經網路）

**狀態：進行中——見下方「目前進度」。**

## 為什麼要做這個（相對於 `../genept_baseline/` 的定位）

`genept_baseline/` 已經誠實驗證：用完全不依賴目標基因自身實驗數據的通用文字
嵌入（GenePT）去預測下游 profile，打不過均值基線——這與 2025-2026 年文獻
共識一致（見 `../results/genept_baseline_README.md`）。

GEARS（Roohani, Huang, Leskovec, *Nature Biotechnology* 2024）的核心假設不同：
它不是單純用「基因是什麼」的通用描述，而是用 **Gene Ontology 共同註解關係**
建一張基因-基因圖，讓模型能沿著「這個基因在功能上跟哪些已測試過的基因相近」
做訊息傳遞（graph convolution），希望比「一個全域均值」更貼近某個基因真正
會怎麼表現。這是文獻裡少數幾個聲稱能對**從未測試過的基因**做出有意義預測的
方法之一，值得誠實驗證是否對我們這個真實 CD4+ T 細胞 CRISPRi 資料集有效。

## 用官方套件，不是重寫

用 `pip install cell-gears`（原作者釋出的官方實作）+ `torch` (CPU 版) +
`torch_geometric`，而非自己重新實作 GNN——GEARS 的圖建構、負二項式損失、
不確定性估計等細節多，直接用官方實作比重寫可靠。

## 關鍵差異：這裡要用「原始表現量」，不是 DE 統計

`genept_baseline/` 直接吃 `GWCD4i.DE_stats.h5ad` 的 `log_fc` 層——已經是算好的
統計量。**GEARS 不是這樣運作**：它要學的是「控制組 pseudobulk profile + 擾動
基因身分 → 擾動後的 pseudobulk profile」，所以需要**真實的表現量矩陣**，不是
統計摘要。因此另外下載了 `GWCD4i.pseudobulk_merged.h5ad`（41.51GB，pseudobulk
層級，`obs` 有 `guide_type`/`perturbed_gene_name`/`culture_condition` 等欄位，
`.X` = 每個 pseudobulk 樣本的 UMI count 加總），透過
`build_gears_dataset.py` 轉成 GEARS 期待的格式（`.obs['condition']`：
控制組 = `"ctrl"`，單基因擾動 = `"{gene}+ctrl"`）。

## 目前進度

- [x] 確認官方 `cell-gears` 套件可裝、可 import（含 `torch` CPU 版 + `torch_geometric`）
- [x] 確認 GEARS 期待的資料 schema（`condition` 欄位格式）
- [ ] 下載 `GWCD4i.pseudobulk_merged.h5ad`（進行中，見
      `src/3_DE_analysis/data_acquisition/download_precomputed_DE.py`）
- [ ] `build_gears_dataset.py`：把 pseudobulk h5ad 轉成 GEARS 格式的 AnnData
- [ ] 跑 `PertData.new_data_process()`（會嘗試下載 Harvard Dataverse 上的預設
      GO 圖，若本沙盒對該網域也 403，則需改供自己建的 gene_set_path）
- [ ] 訓練 + 用 held-out 基因評估，跟 `genept_baseline` 與均值基線一起誠實比較
- [ ] 寫進 `../results/gears_benchmark_README.md`（不論結果好壞）

## 護欄（同 `../README.md`）

- 只在 `../results/` 寫報告，絕不碰 production 路徑
- 誠實比較均值基線，打輸就老實報輸
- CPU-only 訓練（本機 GPU「GB10」的顯存被其他長期服務佔用，且 aarch64 平台
  的 CUDA torch 取得複雜，這個規模的 GNN 用 CPU 訓練是合理取捨，不是偷懶）
