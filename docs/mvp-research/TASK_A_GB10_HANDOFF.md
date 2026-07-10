# 任務 A 交接紀錄 — sandbox 端已完成的準備工作

**對應手冊：** [`TASK_A_RUNBOOK_GB10.md`](TASK_A_RUNBOOK_GB10.md)（完整規格、三步 pipeline、時間估計都在那份，本檔只記錄 sandbox 這邊做了什麼、發現了什麼、GB10 接手時該注意什麼）

**最後更新：** 2026-07-10

---

## 這份文件要解決什麼問題

`TASK_A_RUNBOOK_GB10.md` 原本假設 GB10 從 Stanford OAK 直接掛載讀資料。本次在 sandbox 端額外驗證了「改用公開 S3 桶（匿名可讀）取得同一批資料」這條路，把可重用的下載工具、配置與**一個重要的頻寬限制發現**留給 GB10 端執行者。

## 資料來源確認

實測 S3 桶 `genome-scale-tcell-perturb-seq` 下 `marson2025_data/` 前綴，取得與手冊一致的 14 個檔案：

| 檔案 | 大小 |
|---|---|
| D1/D2/D3/D4 × Rest/Stim8hr/Stim48hr（12 個）`*.assigned_guide.h5ad` | 各 110–161 GB |
| `GWCD4i.DE_stats.h5ad` | 15.63 GB |
| `GWCD4i.pseudobulk_merged.h5ad` | 41.51 GB |
| **合計** | **~1,673.8 GB (1.67 TB)** |

匿名讀取指令（免 AWS 憑證）：
```bash
aws s3 ls --no-sign-request s3://genome-scale-tcell-perturb-seq/marson2025_data/
```

## ⚠️ 關鍵發現：本 sandbox 對外頻寬有硬上限，GB10 需自行實測

在 sandbox 內對這個 S3 桶做了頻寬階梯測試（`GetObject` + `Range`，量測純下載吞吐，非 TCP 理論值）：

| 併發串流數 | 總吞吐 |
|---|---|
| 1 | 0.9 MB/s |
| 16 | 3.1 MB/s |
| 32 | 4.5 MB/s |

**吞吐不隨併發數線性增長，代表這是總頻寬帽（很可能是 sandbox 的 agent proxy 限速），不是單純連線延遲問題。** 以 ~4.5 MB/s 上限估算，下載全部 1.67 TB 需要 **~105 小時（4.4 天）**，不切實際，因此本 sandbox 只下載了驗證用的少量資料（見下），**沒有嘗試在此跑完整下載**。

**行動建議：** GB10 若走 S3 路徑（而非 OAK 直接掛載），請先用同樣的階梯測試法（見 `data_acquisition/download_s3_data.py` 內的邏輯，或自行起 1/16/32 併發各抓 100–500MB 量測）確認 GB10 自己的出口頻寬上限,再決定：
- 頻寬夠(例如 >100MB/s)→ 直接用本工具或 `aws s3 sync --no-sign-request` 全量拉取,數小時內可完成。
- 頻寬同樣受限 → 優先走 OAK 直接掛載（手冊原案），不要用 S3 當主路徑。

## sandbox 端已產出的可重用工具

都在 `src/3_DE_analysis/`：

| 檔案 | 用途 |
|---|---|
| `data_acquisition/download_s3_data.py` | 匿名 S3 並行下載器，**支援斷點續傳**（比對本地/遠端檔案大小，不重下已完成部分）。預設 `MAX_WORKERS=16`（sandbox 實測頻寬帽下的合理值；GB10 應依自己的頻寬階梯測試結果調整）。 |
| `data_acquisition/check_download_progress.sh` | 每 30 秒刷新一次的下載進度監視（總大小/檔案數/百分比/最近檔案）。 |
| `DE_config_local.yaml` | 對照 `DE_config_full.yaml` 的本地化版本：`datadir` 指向 repo 內 `data/marson2025_data/`（相對路徑，免改 `src/utils.py::_convert_oak_path`），其餘參數（`chunk_size=50`、`design_formula`、feature selection 門檻）與全量版一致，供縮減版 pipeline 直接使用。 |

用法（若 GB10 決定沿用 S3 路徑）：
```bash
cd src/3_DE_analysis/data_acquisition
python3 download_s3_data.py                    # 背景執行；可安全中斷/重啟，會自動續傳
bash check_download_progress.sh                # 另開一個 terminal 監看進度
```

下載目標目錄：repo 根目錄下的 `data/marson2025_data/`（已在 `.gitignore` 的 `**/*.h5ad` 規則涵蓋，**不會被 git 追蹤**，符合手冊「全量 `.h5ad` 不進 git」的原則）。

## sandbox 端這次實際做了什麼（誠實記錄，避免誤解為「已完成下載」）

- ✅ 確認 S3 桶內容與手冊描述一致（14 檔、~1.67TB）
- ✅ 寫好、測過斷點續傳下載器與監視腳本
- ✅ 產出本地化 `DE_config_local.yaml`
- ✅ 做了頻寬階梯測試，**發現 sandbox 出口頻寬 ~4.5MB/s 見頂**
- 🟡 背景下載程序仍在跑，抓取少量資料（個位數 GB 等級）作為腳本驗證用，**未完成、也不預期在合理時間內完成**——因為前述頻寬限制。這不是資料本身的問題，是這個沙盒環境的網路限制。
- ❌ 未執行三步 pipeline（Step 1–3）——需要完整資料才有意義，等 GB10 端資料到位後照 `TASK_A_RUNBOOK_GB10.md` 執行即可，本檔工具可直接複用或參考。

## GB10 接手時的檢查清單

1. 確認 OAK 直接掛載是否可用（`src/utils.py::_convert_oak_path` 原生支援），若可用優先用這條路，跳過 S3。
2. 若走 S3：跑一次頻寬階梯測試（1/16/32 併發），確認吞吐足夠後再 `download_s3_data.py` 全量跑，並依測得頻寬調整 `MAX_WORKERS`。
3. 資料就位後，把 `DE_config_local.yaml` 的 `datadir` 改成實際路徑（OAK 轉換路徑或本地資料夾），其餘沿用。
4. 照 `TASK_A_RUNBOOK_GB10.md` 的三步 pipeline 執行,先跑縮減版(1,235 gate-passing 標的,~25 chunk × 3 條件)。
5. 完成後只 commit 萃取表 + provenance,全量 `.h5ad` 留在原地,並跑 `pytest tests/ -q` 確認 golden-file 測試仍綠。
