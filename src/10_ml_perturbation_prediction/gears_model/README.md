# GEARS 風格模型（GO 知識圖譜 + 圖神經網路）

**狀態：已完成——誠實負面結果，見 `../results/gears_benchmark_README.md`。**

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

**結論先講：也沒有打贏均值基線，而且在「顯著差異基因」子集上幾乎沒有訊號
（pearson_de=0.021）。完整結果與討論見 `../results/gears_benchmark_README.md`。**

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

## 執行紀錄

- [x] 確認官方 `cell-gears` 套件可裝、可 import（含 `torch` CPU 版 + `torch_geometric`）
- [x] 確認 GEARS 期待的資料 schema（`condition` 欄位格式、額外需要 `cell_type` 欄位）
- [x] 下載 `GWCD4i.pseudobulk_merged.h5ad`（41.5GB，過程中中斷 3 次才成功——
      見下方「下載中斷的教訓」）
- [x] `build_gears_dataset.py`：pseudobulk h5ad → 標準化（見下）→ 子抽樣
      2,000 基因 → GEARS 格式 AnnData（16,403 obs × 18,129 var）
- [x] 排查並修好五個環境相容性問題 + 一個資料標準化問題（見下方各節）
- [x] 訓練 10 epochs（CPU，92.4 分鐘）+ 官方評估流程
- [x] 誠實報告寫進 `../results/gears_benchmark_README.md`

## 下載中斷的教訓（給以後參考）

41.5GB 的 `GWCD4i.pseudobulk_merged.h5ad` 下載中斷了 3 次：一次 S3 偶發
503、兩次是背景任務在 ScheduleWakeup 觸發新一輪對話時被終止（懷疑是
Claude Code 這個 harness 把「track 起來的背景任務」跟對話回合的生命週期
綁在一起）。解法：
1. 下載器加了 chunk 級別的斷點續傳（`*.manifest.json` 記錄已完成的
   chunk 編號），中斷後不用整檔重下。
2. 改用 `setsid nohup ... &` + `disown` 讓下載程序變成真正脫離 session
   的孤兒程序，不再被 harness 的背景任務生命週期管理波及——這個改法
   之後下載順利跑完剩下的部分，證實了前述懷疑。訓練本身（92.4 分鐘）
   也是用同一招才能撐過多輪 ScheduleWakeup 而不中斷。
若之後还要抓其他大檔（例如 `GWCD4i.DE_stats.by_guide.h5mu` 29.4GB /
`by_donors.h5mu` 16.8GB），直接沿用這個 `setsid nohup` 模式。

## 記憶體限制：MAX_PERT_GENES 子抽樣（不是 skip_calc_de）

`PertData.new_data_process()` 對全量 11,287 個擾動基因（73,700 個擾動樣本）
做 `create_dataset_file()` 時，會把每個擾動 × 每個 replicate × 配對的控制組
細胞全部建成 PyG Data 物件、存進一個大 dict，最後一次性 `pickle.dump`——
不是流式寫入。在這台機器（119GB 記憶體，其中被其他長期服務佔用大半）上，
這一步實測把可用記憶體從 30GB 打到 <1.1GB，已被安全監控自動 kill 過。

**曾經嘗試 `skip_calc_de=True` 想繞開 scanpy 的 `rank_genes_groups_by_cov`
計算，但這個旗標其實不可選——`GEARS.__init__` 無條件讀取
`adata.uns['non_zeros_gene_idx']`（只有完整跑過 DE 計算才會產生），
`skip_calc_de=True` 反而讓模型初始化直接 `KeyError`。** 真正的解法是
`build_gears_dataset.py::MAX_PERT_GENES`：對擾動基因本身做子抽樣（子抽樣
到 2,000 個基因，保留全部 ctrl 樣本），把物件數量壓到安全範圍再走完整的
`new_data_process()`（含完整 DE 計算），讓 `pearson_de` 這個關鍵子指標
維持有意義（不是佔位值）。

## 資料標準化：原始 pseudobulk count 沒標準化會讓訓練發散

第一次直接把 `GWCD4i.pseudobulk_merged.h5ad` 的原始 `.X`（pseudobulk UMI
count 加總，量級可到 169 萬）餵給 GEARS，訓練 loss 從 10^13 一路衝到
10^16——明顯發散，不是收斂中的正常震盪。GEARS 的損失函數/預設學習率是
照 log-normalize 過的表現量（典型範圍 0-10）調的。`build_gears_dataset.py`
補上標準流程的 `sc.pp.normalize_total` + `sc.pp.log1p` 後，同一個 batch
size/學習率下 loss 落在 1-3 的正常範圍並穩定收斂（10 epochs 後 train/val
Overall MSE 穩定在 0.055-0.062）。**這是資料準備的必要步驟，不是可有可無
的裝飾——沒有它，後面所有的訓練結果都毫無意義。**

## pandas/scipy/networkx 版本相容性問題（五個，全部在 `train_gears.py` 開頭修補）

`cell-gears`（作者最後更新應該是幾年前的環境版本）跟本機裝的新版
pandas 3.0.3 / scipy / networkx 有多處不相容，全部是舊版 API 被移除或
行為改變，不是我們自己程式碼的 bug：

1. **`series[0]` 整數索引**：`pertdata.py::create_cell_graph_dataset` 的
   `adata_.obs['condition_name'][0]` 期待「取第一列」，舊版 pandas 對
   非整數 label 的 Series 會自動退回位置索引，新版直接 `KeyError`。
   → 補回「整數 key 找不到對應 label 時退回 `.iloc`」的行為。
2. **`DataSplitter.split_data()` 回傳值解包**：`split="simulation_single"`
   時該函式只回傳一個 AnnData（非 2-tuple），但呼叫端無條件
   `adata, subgroup = DS.split_data(...)`，解包會炸
   `ValueError: too many values to unpack`。→ 改用 `split="simulation"`
   （官方更常用的路徑，回傳值正確匹配，我們的資料集只有單基因擾動、
   沒有 combo，這條路徑同樣適用）。
3. **categorical groupby-agg**：`prepare_split()` 對已被轉成 category
   dtype 的 `condition` 欄位做 `groupby('split').agg({'condition': lambda
   x: x})`，新版 pandas 嘗試把非純量的聚合結果轉回 Categorical dtype 失敗
   （`TypeError: unhashable type: 'Categorical'`）。→ 在呼叫
   `prepare_split()` 前把 `condition` 轉成純字串 dtype。
4. **`pandas.Series.nonzero()` 被移除**：`gears.py::GEARS.__init__` 直接用
   布林 Series 對 scipy sparse matrix 索引，scipy 內部呼叫
   `.nonzero()`，舊版 pandas Series 有這個方法、新版沒有。→ 補回
   `pd.Series.nonzero = lambda self: np.asarray(self).nonzero()`。
5. **GO 網路 groupby-apply 丟欄位**：`get_similarity_network()` 的 GO 分支
   做 `df.groupby('target').apply(...).reset_index(drop=True)`，新版
   pandas 的 groupby-apply 會把 'target' 這個分組欄位併掉，
   `reset_index(drop=True)` 又把它徹底丟棄，導致後面
   `nx.from_pandas_edgelist(..., target='target', ...)` 找不到欄位
   （`KeyError: 'target'`）。→ monkeypatch `gears.gears.get_similarity_network`
   （注意要 patch `gears.gears` 模組裡的綁定，不是 `gears.utils`——
   `from .utils import X` 在 import 當下就把參照複製過去了），把
   `reset_index(drop=True)` 改成 `reset_index()`（保留 'target' 欄位，
   多出的 'level_1' 欄位無害，`nx.from_pandas_edgelist` 只取指定欄位）。

## 護欄（同 `../README.md`）

- 只在 `../results/` 寫報告，絕不碰 production 路徑
- 誠實比較均值基線，打輸就老實報輸——這次真的輸了，且輸得比 GenePT
  基線更清楚（`pearson_de` 幾乎等於零）
- CPU-only 訓練（本機 GPU「GB10」的顯存被其他長期服務佔用，且 aarch64 平台
  的 CUDA torch 取得複雜，這個規模的 GNN 用 CPU 訓練是合理取捨，不是偷懶）
