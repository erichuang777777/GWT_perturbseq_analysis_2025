# 維護 Maintenance

本頁說明如何在本機執行、測試、重建這個平台,以及快取與版本失效的維護規則。所有指令都對應 repo 內真實存在的檔案。

## 1. 環境與相依

- Python 3(pandas / numpy / scikit-learn / FastAPI / Streamlit)。
- 測試需要 `pytest`(`pip install -q pytest`)。
- 細胞層級延伸另需 `anndata` / `scanpy`;`pertpy` 在部分環境無法安裝(`blitzgsea` 建置失敗),因此 Mixscape 式分類是用 scikit-learn 直接重寫,這是刻意的替代,不是缺功能。
- **對外連線走 egress proxy**:ClinicalTrials.gov / PubMed E-utilities / Open Targets 在受限沙盒可能被政策封鎖,此時外部證據 fetcher 會回 `source_status: "unavailable"` 而非崩潰。

## 2. 執行服務

```bash
# API(FastAPI)
uvicorn target_card_api:app --app-dir src/3_DE_analysis

# 儀表板(Streamlit)— 注意:本沙盒未安裝 Streamlit,
# 儀表板變更僅經 py_compile / AST 驗證,未實際視覺渲染
streamlit run src/3_DE_analysis/target_card_dashboard.py
```

## 3. 重建 GWT 參考標靶卡片

```bash
python src/3_DE_analysis/build_target_cards.py \
  --de-stats     metadata/suppl_tables/DE_stats.suppl_table.csv \
  --guide-kd     metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv \
  --library-metadata metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv \
  --sample-metadata  metadata/suppl_tables/sample_metadata.suppl_table.csv \
  --output       sources/topic14_target_cards.csv
```

一次完整建構約 33,983 列;在參考機器上 build 約 15 秒、readiness 約 4 秒。

## 4. 測試

```bash
python -m pytest tests/ -q
```

目前 **29 個測試全過**,分為四類(見 `docs/IMPLEMENTATION_PLAN.md` §1.11):

- `test_golden_file.py` — 固定小輸入 → 逐值比對卡片產出(ZAP70/MED12/LOWEXPR1/NOEFFECT1 四種原型)
- `test_join_integrity.py` — guide→target 彙整列數、DE 列不增減、card→readiness 一對一連結
- `test_known_answer.py` — 對真實 33,983 列參考集做回歸釘選(EDA funnel 33,983 → 4,182 → 1,102;校準對照數字)
- `test_empty_states.py` — 四種 `result_status`、空資料集、缺欄位、缺檔案路徑

若某個 checkout 沒有 `metadata/suppl_tables/*.csv`,真實資料測試會 **skip 而非 fail**(`tests/conftest.py` 的 `real_data_available` fixture),測試套件仍會綠燈。

## 5. 快取與版本失效政策(權威:`docs/cache_and_versioning_policy.md`)

### 5.1 標靶卡片建構:每個 `dataset_id` 不可變

每次 `POST /api/build` 產生新的 `dataset_id`(UUID)並寫入新目錄,**不會原地覆寫**。沒有自動失效機制;只有明確再呼叫 build 才會重建。

**何時該重建:**
1. 任一上游 CSV(DE_stats / guide_kd / sgrna_library / sample_metadata / benchmark)在磁碟上變動 → `data_version` 指紋會不同。
2. `ENGINE_VERSION` 被 bump(scoring/readiness/calibration 邏輯變更)。
3. `CARD_SCHEMA_VERSION` 被 bump(`out_cols` 欄位增/刪/改名)。
4. 使用者上傳以不同欄位對應重新合併(這本來就會產生新的 `usr_...` dataset_id)。

**不會自動失效的**:舊 `dataset_id` 的 `target_cards.csv` 永遠維持建構當下的樣子,即使版本 bump 也不回溯重算 — 這是刻意的,好讓已分享的連結持續回傳相同數字。把舊 `dataset_id` 當作凍結快照,要新的就明確重建。

### 5.2 外部證據快取:以基因為單位的 TTL

- 預設 **30 天 TTL**(`TTL_SECONDS_DEFAULT = 30 * 24 * 3600`)。
- 過期由 `_is_stale` 判定(比對 `fetched_at`);過期會在下次 fetch 時重抓。
- 強制刷新:`build_evidence_for_gene(gene, force=True)` 或 `POST /api/evidence/build` 帶 `force=True`。
- 批次端點上限 `MAX_EVIDENCE_GENES = 50`,且走 `BackgroundTasks`,不阻塞請求執行緒。

### 5.3 本機靜態 overlay 清單:無 TTL、無自動刷新

`sources/broad_effect_genes.txt`、`metadata/gene_lists/*.tsv`、疾病關聯匯出都是每次程序啟動時從磁碟重讀。若未來從 live 來源重新產生,請比照 `external_evidence_cache.py` 加上 `fetched_at` + 來源版本戳記,並更新 `docs/data_governance_checklist.md` §3。

## 6. 快取目錄生命週期(`sources/target_tool_cache/`)

| 路徑樣式 | 內容 | Git 狀態 | 清理政策 |
|---|---|---|---|
| `<uuid>/`(GWT 參考建構) | 卡片 / 報告 / metadata | 預設 `.gitignore`(唯一刻意保留的 demo dataset 除外) | 無自動清理;手動刪除不再被連結引用的舊 `dataset_id` |
| `usr_*/` | 使用者上傳合併輸出 | `.gitignore` | 永不 commit;無多人存取控制,不要假設目錄命名等於隔離 |
| `imports/*/` | 暫存未核准的 import | `.gitignore` | 無自動過期 |
| `_evidence/<gene>.json` | 外部證據快照 | **有追蹤**(刻意種子資料) | 由 30 天 TTL 管理,非手動清理 |

## 7. 「這個數字還新嗎?」快速判斷

1. 看該 `dataset_id` 的 `metadata.json`:`engine_version` / `schema_version` / `dataset_version` / `data_version` / `built_at`。
2. 比對 `engine_version` / `schema_version` 與 `target_card_api.py` 目前的常數;不同就代表是舊的 scoring/欄位契約 → 重建。
3. 外部證據面板看該基因快照的 `fetched_at` 是否超過 30 天。
4. 靜態 overlay 清單今天沒有版本戳記 → 視為「與這個 repo checkout 一樣新」,需要精確時間就 `git log <file>`。
