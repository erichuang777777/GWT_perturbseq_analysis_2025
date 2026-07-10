# 全量 per-target × gene 帶符號 DE 長表

**產生方式：** `src/3_DE_analysis/data_acquisition/extract_full_signed_DE.py`，
從 `GWCD4i.DE_stats.h5ad`（Marson lab 公開於 S3，見
[`TASK_A_GB10_HANDOFF.md`](../../../docs/mvp-research/TASK_A_GB10_HANDOFF.md)）
萃取全部 33,983 個 target×condition 列的顯著 target×gene 配對。

與 [`gate_passing_signed_DE.suppl_table.csv.gz`](../gate_passing_signed_DE.suppl_table.csv.gz)
的差異：這裡是**全量**（所有標的，不限 1,235 個通過 MVP 門檻的），gate-passing
版本只是全量的子集（門檻標的因為篩選條件本身偏向「有大量顯著基因」，平均
每列顯著配對數遠高於全量平均）。

## Schema（兩份表一致）

| 欄位 | 說明 |
|---|---|
| `target_gene` | 被擾動的基因名稱 |
| `target_ensembl_id` | 被擾動基因的 Ensembl ID |
| `culture_condition` | Rest / Stim8hr / Stim48hr |
| `downstream_gene` | 顯著受影響的下游基因名稱 |
| `downstream_ensembl_id` | 下游基因的 Ensembl ID |
| `log_fc` | log2 fold change（DESeq2）|
| `adj_p_value` | FDR-adjusted p-value（< 0.1 才會出現在表中）|
| `baseMean` | 該基因的平均標準化表現量 |
| `zscore` | log_fc / lfcSE |

## 為何切成多個 part 檔

單一檔案（未切分）約 2,056,424 列，parquet(zstd) 壓縮後 ~75MB，已低於 GitHub
100MB 單檔限制，但仍切成兩個 part（依寫入順序切分，非依任何生物學意義的分組）
是為了保留安全邊際、也方便未來全量資料再擴充時不必大改流程。讀取時用
`pandas.read_parquet('metadata/suppl_tables/full_signed_DE/')`（讀整個目錄）
即可自動合併，不需手動處理 part 檔。

| 檔案 | 大小 |
|---|---|
| `part-000.parquet` | ~51.3MB |
| `part-001.parquet` | ~23.7MB |

## 覆蓋率

- 2,056,424 個顯著（adj_p_value < 0.1）target×gene 配對
- 10,851 個標的至少有 1 個顯著下游基因（全部 11,526 標的中，其餘無顯著命中——
  誠實反映在資料裡，不是缺漏）
- 10,273 個唯一下游基因身分
- 依條件：Stim8hr 786,755 / Stim48hr 670,322 / Rest 599,347 列
