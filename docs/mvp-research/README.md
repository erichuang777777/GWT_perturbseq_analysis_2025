# docs/mvp-research/ 交接總覽

**用途：** 這個資料夾是研究/規劃階段的產出,供雲端開發接手。本文件是索引 + 現況標記 + 合併指引,**每次新增檔案請同步更新本文件**,避免重複做已完成的事。

**最後更新：** 2026-07-07(對照 commit `f6511a45` 為止)

**本輪更新摘要：** 項目 C(`fetch_open_targets` 修正)、A(`match_disease_drug_evidence`)、D(Reactome/STRING 通路快取 + `drug_class` 分類)已在本 session 實作、本地驗證(全數測試通過)、推送完成。項目 B(`safety_overlay.py`)由雲端與本 session **並行**實作;雲端版本已接進 `readiness_engine.py`/`target_card_api.py`,保留該版本作為主實作。本 session 發現並修正了 `gtex_per_tissue.parquet` 的 schema 不符問題(雲端程式碼期望已聚合的 `ensembl_id`/`n_tissues_expressed`/`max_expression_outside_cd4_context` 表,原推送版本是未聚合的原始 per-tissue 表)—— 已覆蓋為正確聚合版本(9,718 基因,100% 對應到 ensembl_id),並刪除本 session 先前建立但未被任何程式碼引用的孤兒檔案 `candidate_genes_membrane.parquet`。

---

## 現況總表（依實作狀態排序）

| # | 檔案 | 內容 | 實作狀態 |
|---|---|---|---|
| 1 | `MVP_開發目標與資料簡報.md` | 一基底三系統架構、資料資源盤點、可行性證據 | 📄 規劃文件(架構已被後續 wiki/roadmap 採用) |
| 2 | `candidate_shortlist_top15.csv` | 15 個候選標的,含 broad_effect/immune_candidate 分類 | 📄 分析結果,供驗證用 |
| 3 | `data_resource_inventory.csv` | 20 項資料資源盤點(S3、連結器、in-repo overlay) | 📄 規劃文件 |
| 4 | `ENHANCEMENT_連結器加強建議.md` | 連結器實測發現：`fetch_open_targets` query 過淺、可補 safety_window/tractability | ⏳ **待實作**——`external_evidence_cache.py` 的 query 尚未修正 |
| 5 | `connector_enrichment_demo.csv` | 8 個候選標的的 tractability/genetic/gnomAD 富集實測 | 📄 驗證資料,佐證 C7 隔離正確性 |
| 6 | `MODULE3_病人層假設引擎_DEMO設計.md` | 模組三設計：群體假設引擎(part A)+ 疾病藥物證據匹配(part B) | ✅ part A 已實作 / ⏳ part B 待實作(見下) |
| 7 | `module3_population_hypothesis_demo.csv` | UK Biobank 群體 LoF 負荷效應 join 候選標的的實測結果 | ✅ 已成為 `population_hypothesis.py` 的驗證基準資料 |
| 8 | `module3_disease_drug_evidence_match_demo.json` | IL2RA×RA、PLCG1×SLE 的證據匹配實測(含 basiliximab 案例) | ⏳ **待實作**——對應函式 `match_disease_drug_evidence()` 尚未寫入 `disease_translator.py` |
| 9 | `ADC_LOCAL_DATA_INGESTION_SPEC.md` | 本地 ADC/CellxGene 資料 ingestion 規格,含識別碼系統核對結果 | ⏳ **待實作**——`safety_overlay.py` 尚未建立 |
| 10 | `adc_overlay_gwt_overlap_full.csv` | candidate_genes.parquet 與 GWT 標的的重疊表(5,588 基因,含膜蛋白/可成藥性欄位) | ✅ 可直接當 `safety_overlay.py` 的測試/種子資料 |
| 11 | `PATHWAY_DRUG_DATA_SOURCES_建議.md` | 通路分析(Reactome/STRING)+ 藥物開發(ChEMBL 機轉、drug_class 分類)建議 | ⏳ **待實作**——尚無對應程式碼 |

---

## 已確認的實作進度(雲端已完成,對照 commit)

- `6ed3001e` — 修 Tech-Debt A.1/A.2 上傳路徑缺陷(`kd_status not_assessed` + `n_total_de_genes` 映射)
- `e0988c95` — **模組三 part A**：`src/3_DE_analysis/population_hypothesis.py` + `tests/test_population_hypothesis.py` 已建立,直接對應本資料夾第 6/7 項的設計與驗證資料
- `6f789bdb` / `2e03622b` / `afc96ec7` — 架構重構 Phase 0：`config/` 單一來源、`contracts/card_schema.py`、dashboard 拆成獨立 `frontend/` package

**檢查 part A 是否完整實作的方法：**
```bash
python -c "from src._3_DE_analysis.population_hypothesis import build_population_hypothesis_card; help(build_population_hypothesis_card)"
pytest tests/test_population_hypothesis.py -v
```

---

## 待實作項目——合併與利用指引

### A. `match_disease_drug_evidence()`(模組三 part B)
**放哪：** `src/3_DE_analysis/disease_translator.py`(與現有疾病關聯函式同檔,共用 `_evidence` 快取機制)
**規格來源：** `MODULE3_病人層假設引擎_DEMO設計.md` §6 + `module3_disease_drug_evidence_match_demo.json`(真實驗證案例,可直接當 golden-file 測試)
**關鍵驗收點：** basiliximab 在 RA 查到 0 個試驗、在 kidney transplant 查到 111 個——這個「不隱藏藥物真實適應症」的行為必須保留,是護欄機制,不是 bug。
**依賴：** `mcp-clinical-genomics`(`open_targets_graphql`)+ `mcp-clinical-trials`(`search_trials`,注意 `intervention` 參數要填**藥名**不是基因名)

### B. `safety_overlay.py`(ADC/CellxGene overlay)
**放哪：** `src/3_DE_analysis/safety_overlay.py`(新檔,`cre_schema.py` 風格的 honest-fallback)
**規格來源：** `ADC_LOCAL_DATA_INGESTION_SPEC.md` §3(兩個 loader 函式簽名已定義)
**種子/測試資料：** `adc_overlay_gwt_overlap_full.csv`(5,588 基因,已含 `is_surface_protein`/`extracellular_length`/`is_druggable` 等欄位)
**注意事項：** 原始 15GB `adc_web_data`/155MB CellxGene zip **不在 repo 裡**,只有抽取後的小型重疊表;若要重新抽取或擴大覆蓋率,需要研究者本機重跑(路徑與腳本邏輯已在規格文件 §3 描述)。
**已解決的三個 blocker**(不需重新確認)：識別碼系統(Ensembl ID 雙邊都有)、資料型態(已算好的 verdict,非原始表現矩陣)、覆蓋率(49%,足夠)。

### C. `external_evidence_cache.py` 的 `fetch_open_targets` 查詢修正
**問題：** docstring 宣稱回傳 tractability/genetics/safety,但實際 GraphQL query 只做 entity search
**規格來源：** `ENHANCEMENT_連結器加強建議.md` §2
**驗收：** 修正後對 IL2RA/JAK1/CTLA4 等標的的查詢應回傳非空的 tractability buckets 與 genetics 分數(可比對 `connector_enrichment_demo.csv` 的既有實測值)

### D. Reactome/STRING 通路欄位 + ChEMBL 機轉護欄 + `drug_class` 分類
**規格來源：** `PATHWAY_DRUG_DATA_SOURCES_建議.md` §1-2,含優先序表
**驗收：** CD3E 應命中 Reactome「Downstream TCR signaling」,STRING 網路應連到 CD247/CD3D(已在規格文件內附實測數值,可直接當測試斷言)

---

## 合併順序建議

1. **C → A** 先修 `fetch_open_targets`,因為 A(疾病藥物證據匹配)的 genetics 分數品質依賴這個修正
2. **B** 可獨立平行進行(純本地 join,無外部依賴)
3. **D** 優先做 Reactome/STRING(小複雜度、已驗證),`drug_class` 分類可與 A 一起做(同一批 Open Targets 藥物資料)

## 護欄提醒(所有待實作項目共用)

- 每個新函式都要有 `caveat`/`available: False` 的誠實 fallback,不能因為抓不到資料就跳過或猜測
- 不接受任何個體病人層輸入——所有模組三功能只做 gene-level 群體統計查表或證據匹配
- 藥物-標的配對若機轉方向與 CRISPRi 敲低方向衝突,必須標記,不能含糊呈現
