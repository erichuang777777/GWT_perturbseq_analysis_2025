# 任務 A 交接紀錄 — sandbox 端已完成的準備工作

**對應手冊：** [`TASK_A_RUNBOOK_GB10.md`](TASK_A_RUNBOOK_GB10.md)（原始規格：假設要重跑 1.67TB 單細胞資料的三步 pipeline）

**最後更新：** 2026-07-10

---

## 🎯 重大進展：不需要重跑 1.67TB 原始資料

原始手冊假設任務 A 必須在 GB10 從頭跑三步 pipeline（pseudobulk → DESeq2 → merge），因為以為 repo 內只有聚合後的計數（`DE_stats.suppl_table.csv` 只有 `n_up_genes/n_down_genes`，沒有基因身分）。

**但實際檢查 S3 桶 `genome-scale-tcell-perturb-seq/marson2025_data/` 後發現：原始資料提供者已經把 per-target × gene 帶符號 DE 矩陣算好並公開了**——檔案 `GWCD4i.DE_stats.h5ad`（僅 **15.63 GB**，不是 1.67TB）：

- `obs` = 33,983 列（每個 target×culture_condition 一列，與 repo 現有 `DE_stats.suppl_table.csv` 的列完全對應）
- `var` = 10,282 個基因
- `.layers` 含 `log_fc` / `p_value` / `adj_p_value` / `baseMean` / `lfcSE` / `zscore` —— **這正是手冊 Step 3 要產出的「帶符號、帶基因身分」矩陣**

也就是說，`TASK_A_RUNBOOK_GB10.md` 描述的三步 pipeline，Marson lab 自己已經跑過一次並公開結果。GB10 要做的不是重跑 DESeq2，**而是下載這一個檔案再萃取**。

## sandbox 端已完成的工作

### 1. 確認資料來源與 schema
讀取桶內的 `data_sharing_readme.md` 確認上述 schema（也一併下載進 repo，見下）。桶內除了 14 個原始 h5ad 外還有：
- `GWCD4i.DE_stats.h5ad`（15.63GB）— **本次任務唯一需要的核心檔**
- `GWCD4i.DE_stats.by_guide.h5mu`（29.4GB）、`GWCD4i.DE_stats.by_donors.h5mu`（16.8GB）— per-guide/per-donor-pair 顆粒度，可解鎖更細的 cross-guide/cross-donor 分析，但非本次任務必要，**故未下載**
- 幾個小的 suppl_tables CSV（各數 MB）

### 2. 找到「1,235 個通過 MVP 門檻標的」的名單
就在 repo 內：`docs/mvp-research/pipeline/03_processed/data/gate_passing_targets.csv`
- 2,131 列（target×condition），`passes_gate=True` 的唯一 `target_contrast`（Ensembl ID）= **1,235**，與手冊數字完全吻合
- 有 `target_contrast_gene_name` / `culture_condition` / `passes_gate` 等欄位可直接篩選

### 3. 頻寬優化（重要，若 GB10 也要抓 S3 請直接複用）
一開始用 **boto3** 匿名下載器（`download_s3_data.py`）測到吞吐見頂在 ~4.5MB/s（1/16/32 併發：0.9/3.1/4.5 MB/s，不隨併發線性成長）。用戶質疑這不合理後重新排查，發現：
- **不是網路頻寬的硬限制**，是 boto3 client 本身開銷大
- 改用裸 `requests` + HTTP Range header 做多段並發，同樣的沙盒環境可以拉到 **~15.5 MB/s**（24 併發時最佳；40 併發反而略降，見 `download_precomputed_DE.py` 內建的分析）
- 目標檔案從「全部 14 個 h5ad（1.67TB）」收斂成「只抓真正需要的 5 個小檔（~15.7GB）」，兩個優化疊加後，下載時間從**估計 4.4 天降到實測 21 分鐘**（`GWCD4i.DE_stats.h5ad` 15.6GB @ 12.8MB/s + 4 個小檔）

### 4. 下載與萃取工具（`src/3_DE_analysis/data_acquisition/`）

| 檔案 | 用途 |
|---|---|
| `download_precomputed_DE.py` | **本次實際使用的下載器**：只抓 `GWCD4i.DE_stats.h5ad` + 4 個小檔（suppl_tables + readme），用 requests + Range header 併發（24 workers），逐段直接 `seek()` 寫入磁碟對應位置（不在記憶體累積整檔——第一版曾把所有 chunk bytes 留在記憶體才寫檔，在只有 21GB 可用記憶體的環境下對 15.6GB 檔案有 OOM 風險，已修正）。 |
| `extract_gate_passing_signed_DE.py` | **已執行完成**：篩出 1,235 標的對應的 2,131 個 target×condition 列，抓出 `adj_p_value < 0.1` 的顯著 target×gene 配對，輸出長表到 `metadata/suppl_tables/gate_passing_signed_DE.suppl_table.csv.gz`。 |
| `download_s3_data.py` | 舊版全量下載器（boto3，較慢），**保留供 GB10 若真的需要全部 14 個原始 h5ad 時參考**（例如要做本 repo 尚未涵蓋的全新分析）。 |
| `check_download_progress.sh` | 進度監視腳本。 |

**踩過的坑（`extract_gate_passing_signed_DE.py` 內有註解說明）：** `GWCD4i.DE_stats.h5ad` 的 `.X` 是刻意留空的 null dataset（真正資料都在 `.layers`），`anndata` 的 `adata[mask].to_memory()` 會嘗試一併 subset `.X` 而丟出 `"Empty datasets cannot be sliced"`。解法是跳過 anndata 的 subsetting，改用 `h5py` 直接對 `layers` group 做行索引讀取（`obs`/`var` 仍用 anndata 讀，因為那兩個一開始就是全量載入、不受影響）。

### 5. Python 環境
本沙盒沒有裝任何科學計算套件（無 numpy/pandas/h5py/anndata），且系統 pip 被鎖定（PEP 668 externally-managed）。建了一個本地 venv `.venv/`（已在 `.gitignore` 既有規則涵蓋範圍內，不進 git），內裝 `h5py numpy pandas scipy anndata`，只夠跑萃取腳本，**不是完整的 `environment.yaml` 環境**（少了 scanpy/pertpy/pydeseq2 等，因為這次不需要重跑 DESeq2）。

### 6. 產出結果（已萃取、已驗證可讀）

**(a) 門檻子集** `metadata/suppl_tables/gate_passing_signed_DE.suppl_table.csv.gz`：

- **1,067,181 列**，欄位：`target_gene, target_ensembl_id, culture_condition, downstream_gene, downstream_ensembl_id, log_fc, adj_p_value, baseMean, zscore`
- 涵蓋 **1,235 個標的 × 3 個培養條件 × 10,271 個下游基因身分**（僅保留 `adj_p_value < 0.1` 的顯著配對，否則全叉積會有 ~3,700 萬列）
- 未壓縮 130MB（超過 GitHub 100MB 硬限制），gzip 後 **48MB**，已加入 `.gitignore` 的例外規則（原本 `*.gz` 被全域忽略，見 `.gitignore` 的 `!metadata/suppl_tables/gate_passing_signed_DE.suppl_table.csv.gz`）
- 依 `culture_condition` 分布：Stim8hr 413,044 / Stim48hr 349,743 / Rest 304,394 列

**(b) 全量** `metadata/suppl_tables/full_signed_DE/`（`extract_full_signed_DE.py` 產出，用戶要求後追加）：

- 對全部 **33,983 個 target×condition 列**（= repo 現有 `DE_stats.suppl_table.csv` 的完整列數，涵蓋 ~11,526 個標的，不限門檻子集）做同樣的 `adj_p_value < 0.1` 篩選
- **2,056,424 列**顯著配對——比門檻子集的 16 倍列數預期少很多（門檻子集只有 1235/2131 個「效應強」的標的，全量包含大量弱效應/無效應標的，平均每列顯著命中數低很多，這是誠實反映生物學現實，不是萃取有誤）
- **10,851 個標的**至少有 1 個顯著下游基因（其餘標的無顯著命中，如實呈現，不補 0）
- 依 zstd 壓縮的 parquet 格式（比 csv.gz 再省 ~28%），因列數仍多，切成 2 個 part 檔（`part-000.parquet` 51.3MB + `part-001.parquet` 23.7MB，各自低於 GitHub 100MB 限制）——用 `pandas.read_parquet('metadata/suppl_tables/full_signed_DE/')` 讀整個目錄即自動合併，不需手動處理 part
- 全程 9 秒完成（h5py 分批讀取，每批 3,000 列，避開一次性載入全部 4 個 layer ~11GB 的記憶體風險）
- schema、覆蓋率細節見該目錄下 `README.md`

## GB10 接手檢查清單

1. **不需要 OAK 掛載、不需要重算 DESeq2** —— 全量與門檻子集皆已從公開的 `GWCD4i.DE_stats.h5ad` 萃取完成並提交進 repo。
2. 若要更細的 cross-guide / cross-donor 訊號（repo 現有 `guide_correlation_*` / `donor_correlation_*` 欄位背後的原始每 guide/每 donor-pair 數值）：才需要額外抓 `GWCD4i.DE_stats.by_guide.h5mu`（29.4GB）/ `GWCD4i.DE_stats.by_donors.h5mu`（16.8GB）——用同一套 `download_precomputed_DE.py` 的模式（改 `FILES` 清單）即可，預期速度同樣是分鐘級而非天級。
3. 萃取出的兩份長表就是 `signature_explorer.py` 需要的查詢 signature 來源（取代目前的單基因 proxy），也是 LINCS(F) 比對的我方 query。全量版可用於任意標的，門檻子集版聚焦在已驗證通過 MVP 門檻的 1,235 個。
4. 完成後跑 `pytest tests/ -q` 確認 golden-file 測試仍綠。

## 誠實記錄：這次沒做的事

- 沒有下載 14 個原始單細胞 h5ad（不需要——見上）
- 沒有跑手冊原本的 Step 1/2/3 pipeline（不需要——結果已經在 `GWCD4i.DE_stats.h5ad` 裡）
- 沒有處理 by_guide/by_donors 的細粒度資料（非本次任務範圍，見上方「GB10 接手檢查清單」第 2 點）
- 下載的原始 `GWCD4i.DE_stats.h5ad`（16GB）與其他小檔留在本地 `data/marson2025_data/`，**未進 git**（符合「大檔不進 repo」原則），下次要重跑萃取需要重新下載或改用 OAK 路徑
