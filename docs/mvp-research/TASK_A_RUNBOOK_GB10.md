# 任務 A 執行手冊 — 在 GB10 跑（縮減版優先）

**目標：** 產出 per-target × gene 帶符號 DE 矩陣（repo 目前缺、解鎖最多下游的一項）。
**只能在有 OAK 單細胞資料 + 算力的環境跑** —— 你的 GB10 正是。sandbox 做不了（1.7TB 未掛載）。

---

## 為什麼先跑縮減版
全量 = 11,526 標的 × 3 條件 ≈ 34k 個全基因組 DE 對比。縮減版 = 只跑**通過 MVP 門檻的
1,235 個標的**（約 10% 算力），就能解鎖 signature_explorer 對「真正重要候選」的完整功能。
先驗證流程、拿到 80% 價值，再決定是否全量。

## 前置：拉全量資料到 GB10
單細胞 `.h5ad` 在 Stanford OAK：`/oak/stanford/groups/pritch/users/emma/data/GWT/`
（見 `DE_config_full.yaml` 的 `datadir`）。`src/utils.py::_convert_oak_path` 會把
`/oak/stanford/...` 轉成 `/mnt/oak/...`——在 GB10 上把 datadir 指到你 rsync 下來的本地路徑即可。

需要的檔：12 個單細胞 h5ad（D1-D4 × Rest/Stim8hr/Stim48hr，各 ~118-172GB，合計 ~1.7TB）
+ `metadata/sgRNA_library_curated.csv`。全部在公開 S3 桶 `genome-scale-tcell-perturb-seq`（匿名可讀）。

## 三步 pipeline（全在 src/3_DE_analysis/）

### Step 1 — make_pseudobulk（I/O 主導，數小時）
讀單細胞 h5ad，以 sc.get.aggregate(func='sum') 依 sample_id 聚合成 pseudobulk。
```bash
python make_pseudobulk.py aggregate <h5ad_file> \
    --sample_metadata_csv metadata/sample_metadata.csv \
    --condition_col culture_condition --sgrna_col guide_id
```
對 12 個 h5ad 各跑一次 `aggregate`（可平行），產出各 sample 的 pseudobulk。
**接著必須跑 make_pseudobulk.py 的第二個子命令 `merge`**（CLI 有兩個 subparser：
`aggregate` 與 `merge`——別跟 Step 3 的 merge_DE_results.py 搞混，那是合併 DE *結果*）：
```bash
# 把各 sample 的 pseudobulk 合併成 DE 輸入
python make_pseudobulk.py merge <sample_id> --DE_config DE_config_full.yaml
```
合併後才得到 Step 2 需要的 <experiment>_merged.DE_pseudobulk.h5ad（~44.6GB）。

### Step 2 — run_DE_chunk（CPU 主導，最貴的部分）
pertpy/PyDESeq2，design: `~ log10_n_cells + donor_id + target`。chunk_size=50。
```bash
# 縮減版：只跑 gate-passing 標的所在的 chunk
python run_DE_chunk.py --config DE_config_full.yaml \
    --test_chunk <chunk_id> --culture_condition Stim48hr --n_cpus <GB10核數>
```
**縮減做法：** 先從 gate-passing 的 1,235 個標的反查它們的 chunk id
（`DE_target2chunk.csv.gz`），只提交那些 chunk。1,235/50 ≈ 25 個 chunk × 3 條件 ≈ 75 個 job。
GB10 是單機多核——用 GNU parallel 或簡單 for 迴圈跑，一晚可完成。
（全量 = 11,526/50 ≈ 231 chunk × 3 ≈ 693 job，數天。）

### Step 3 — merge_DE_results（快）
```bash
python merge_DE_results.py --config DE_config_full.yaml --force_combine
```
合併成 target × gene 的 .h5ad signed DE 矩陣。

## 產出後如何放回 repo（遵守 PR #10 原則）
- **全量 .h5ad 不進 git**（太大）。只 commit 從中萃取的 shortlist / gate-passing 標的表
  + provenance（config hash、資料版本、fetched_at）。
- 跑完後 `pytest tests/ -q` 確認 golden-file 測試仍通過。
- 這份 signed DE 矩陣就是 signature_explorer.py 需要的 query signature 來源，
  也是 LINCS(F) 比對的我方 query（見 LINCS_ACQUISITION_任務F.md）。

## 時間估計總結
| | 縮減版（1,235 標的）| 全量（11,526）|
|---|---|---|
| Step 1 pseudobulk | 數小時（I/O）| 數小時（同，一次做完）|
| Step 2 DE | **一晚**（~75 job）| 一到數天（~693 job）|
| Step 3 merge | 分鐘 | 分鐘 |

沒有你 GB10 的確切核數/記憶體我只能給範圍；主要驅動因素是 Step 2 的平行度。
