# docs/mvp-research/ 交接總覽

**用途：** 這個資料夾是研究/規劃階段的產出,供雲端開發接手。本文件是索引 + 現況標記 + 合併指引,**每次新增檔案請同步更新本文件**,避免重複做已完成的事。

**最後更新：** 2026-07-07 · **狀態：全部 11 項已實作完成**(對照合併後的 `main` @ `bbc408a`,PR #3 已合併)

**本輪更新摘要：** 項目 A(`match_disease_drug_evidence`)、C(`fetch_open_targets` 修正)、D(Reactome/STRING 通路快取 + `drug_class` 分類)由本地 session 實作;項目 B(`safety_overlay.py`)由雲端與本地 session **並行**實作,雲端版本(`ebd97a48` 起)是主實作。本地 session 發現並修正 `gtex_per_tissue.parquet` 的 schema 不符問題(從未聚合的原始 per-tissue 表覆蓋為已聚合的 `(ensembl_id, gene_symbol, n_tissues_expressed, max_expression_outside_cd4_context)` 表,9,718 基因,排除 Blood/Spleen 等 CD4 情境組織,對應 ingestion 規格 §1 的情境反轉提醒);雲端於 `d13aed1` 對照這個聚合版本重寫 `safety_overlay.py` 的 GTEx 讀取邏輯(改回以 Ensembl ID 為 join key),重新驗證:CD3E → 21/30 off-context 組織、MED12 → 28/30、VAV1 確認不在表中 → `unknown`。全部測試已對照最終值更新並通過。**PR #3 已合併,本文件的「待實作」狀態已全部清空——後續 session 請勿因看到舊版本文件而重做這些項目。**

---

## 現況總表（全部完成）

| # | 檔案 | 內容 | 實作狀態 |
|---|---|---|---|
| 1 | `MVP_開發目標與資料簡報.md` | 一基底三系統架構、資料資源盤點、可行性證據 | 📄 規劃文件(架構已被後續 wiki/roadmap 採用) |
| 2 | `candidate_shortlist_top15.csv` | 15 個候選標的,含 broad_effect/immune_candidate 分類 | 📄 分析結果,供驗證用 |
| 3 | `data_resource_inventory.csv` | 20 項資料資源盤點(S3、連結器、in-repo overlay) | 📄 規劃文件 |
| 4 | `ENHANCEMENT_連結器加強建議.md` | 連結器實測發現：`fetch_open_targets` query 過淺、可補 safety_window/tractability | ✅ 已實作——`fetch_open_targets` 查詢已修正(見下方 commit 對照) |
| 5 | `connector_enrichment_demo.csv` | 8 個候選標的的 tractability/genetic/gnomAD 富集實測 | 📄 驗證資料,佐證 C7 隔離正確性 |
| 6 | `MODULE3_病人層假設引擎_DEMO設計.md` | 模組三設計：群體假設引擎(part A)+ 疾病藥物證據匹配(part B) | ✅ part A + part B 均已實作 |
| 7 | `module3_population_hypothesis_demo.csv` | UK Biobank 群體 LoF 負荷效應 join 候選標的的實測結果 | ✅ 已成為 `population_hypothesis.py` 的驗證基準資料 |
| 8 | `module3_disease_drug_evidence_match_demo.json` | IL2RA×RA、PLCG1×SLE 的證據匹配實測(含 basiliximab 案例) | ✅ 已實作——`match_disease_drug_evidence()` 已寫入 `external_evidence_cache.py` |
| 9 | `ADC_LOCAL_DATA_INGESTION_SPEC.md` | 本地 ADC/CellxGene 資料 ingestion 規格,含識別碼系統核對結果 | ✅ 已實作——`safety_overlay.py` 已建立並接進 `readiness_engine.py` |
| 10 | `adc_overlay_gwt_overlap_full.csv` | candidate_genes.parquet 與 GWT 標的的重疊表(5,588 基因,含膜蛋白/可成藥性欄位) | ✅ 是 `safety_overlay.py` 的實際 production 資料來源 |
| 11 | `PATHWAY_DRUG_DATA_SOURCES_建議.md` | 通路分析(Reactome/STRING)+ 藥物開發(ChEMBL 機轉、drug_class 分類)建議 | ✅ 已實作——`pathway_network_cache.py` |

---

## 實作進度總覽(對照 commit,依合併後的 main 歷史)

- **Tech-Debt A.1/A.2 上傳路徑缺陷修正**(`kd_status not_assessed` + `n_total_de_genes` 映射)
- **架構重構 Phase 0**：`config/` 單一來源、`contracts/card_schema.py`、dashboard 拆成獨立 `frontend/` package
- **模組三 part A**：`src/3_DE_analysis/population_hypothesis.py` + `tests/test_population_hypothesis.py`
- **模組三 part B**：`match_disease_drug_evidence()`(`external_evidence_cache.py`)+ `drug_class` 分類
- **`fetch_open_targets` 查詢修正**：改為真正查詢 tractability/genetics/safetyLiabilities,而非只做 entity search
- **`pathway_network_cache.py`**：Reactome + STRING 離線批次快取
- **`safety_overlay.py`**（§1.12,兩半都完成）：
  - 膜蛋白/可成藥性半：讀 `adc_overlay_gwt_overlap_full.csv`,升級 `tractability_modality`;在真實 33,983 列參考集驗證為純加分(267 個 readiness call 進步,0 退步)
  - GTEx 安全窗半：讀已聚合、排除 CD4 情境組織的 `gtex_per_tissue.parquet`,升級 `safety_window_score`;驗證 `safety_window_score` 與 `readiness_call`/`overall_readiness_stage` 因果無關(`_stage()` 從不吃 safety 參數)

**驗證方法：**
```bash
pytest tests/ -q   # 全套測試(52+ passing,network-dependent 測試會誠實 skip)
```

---

## 護欄提醒(所有已實作項目共用,供未來擴充參考)

- 每個新函式都有 `caveat`/`available: False` 的誠實 fallback,不因抓不到資料就跳過或猜測
- 不接受任何個體病人層輸入——所有模組三功能只做 gene-level 群體統計查表或證據匹配
- 藥物-標的配對若機轉方向與 CRISPRi 敲低方向衝突,必須標記,不含糊呈現
- `unknown` 永不悄悄變成 `0`——一個基因不在 overlay 裡代表「未檢查」,不是「不安全/不可成藥」
