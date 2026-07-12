# 說明文件總盤點 Documentation Index

> 全 repo 說明文件的**單一盤點**:按用途分組(前端展示 / pipeline 每階段+EDA / 程式各階段 / 權威規格 / 導覽 wiki / 研究 sources / 治理與揭露),每項附一句用途與**現況**(✅ 最新 · 🧊 已凍結+日期 · ⚠️ 需更新)。這頁本身也需隨新文件更新。
>
> **關鍵現況(2026-07)**:前端已是 **React + Vite static portal**(`frontend/webserver/`,非 Streamlit);pipeline 為**凍結的 7 階段**(md5 manifest,2026-07-10/11);`tests/` 現有 **34 個測試檔**;新增 `src/10_ml_perturbation_prediction/`。

---

## 1. 前端網頁展示用 Frontend-facing

### 1.1 Portal 內容資料(前端直接讀 `public/`)
| 檔案 | 用途 | 現況 |
|---|---|---|
| `frontend/webserver/public/real-dataset.json` | 標靶 + 概念模組資料(由 `scripts/export_real_data.py` 匯出;7,249 標的) | ✅ |
| `frontend/webserver/public/disclosure.json` | 版本/覆蓋/免責/原則/限制/attribution/概念層 | ✅ |
| `frontend/webserver/public/provenance_registry.csv` | 資料來源×演算法×參考(79 列)供 Provenance 頁渲染 | ✅ |

### 1.2 Portal 頁面(揭露呈現)
| 位置 | 用途 | 現況 |
|---|---|---|
| `src/views/Provenance.tsx` | Provenance/Methods 頁(渲染上面兩檔;Header/Footer 皆有入口) | ✅ 新增 |
| `src/views/ApiDocs.tsx` | REST API 文件頁 | ✅ |
| `docs/explainer/` | 🧬 科普導覽單頁網站(一般讀者) | ✅ |
| `docs/researcher_guide/` | 🔬 研究人員導覽單頁網站 | ✅ |

### 1.3 前端規格與對外文件
| 檔案 | 用途 | 現況 |
|---|---|---|
| `docs/FRONTEND_HANDOFF.md` | **前端交付清單(curated)**:portal 需要的最佳文件與資產,附「怎麼用/已做好/待做」 | ✅ |
| `docs/frontend_disclosure_spec.md` | 交付前端的揭露規格(放哪、來源檔、缺口) | ✅ |
| `docs/data_use_terms.md` | 對外資料使用與條款草稿 | ✅ |
| `docs/bulk_download_schema.md` | 下載檔欄位說明(null=unknown) | ✅ |
| `DATA_LICENSE.md` | 資料授權聲明 | ✅ |
| `docs/frontend_design.md` / `docs/frontend_fix_plan.md` / `docs/ux_flow_stepwise_plan.md` / `docs/ux_trust_fix_plan.md` | 前端設計 / 修正 / UX 流程計劃 | ⚠️ 部分含 Streamlit 舊描述,屬歷史計劃 |
| `frontend/README.md` / `frontend/webserver/README.md` | 前端架構與啟動(React portal) | ✅ |

---

## 2. Pipeline 每階段 + EDA(凍結 7 階段)

| 檔案 | 用途 | 現況 |
|---|---|---|
| `docs/mvp-research/pipeline/EDA_INDEX.md` | 各階段 EDA 盤點總表(deterministic 產生) | 🧊 2026-07-11 |
| `docs/mvp-research/pipeline/STAGE_SUMMARY_AND_FREEZE.md` | 7 階段凍結報告(version_id + md5) | 🧊 2026-07-11 |
| `docs/mvp-research/pipeline/PIPELINE_LINEAGE.md` | 階段血緣(輸入→輸出) | ⚠️ 含 Streamlit 字樣(歷史);內容架構仍有效 |
| `01_raw/`(README + EDA) | 原始 DE 統計(33,983 列) | 🧊 |
| `02_curated/`(README + EDA) | 品質門檻(→2,131 列 / 1,235 標的) | 🧊 |
| `03_processed/`(README + EDA) | effect/de matrix pivots | 🧊 |
| `04_statistical/`(README + EDA_04a target cards + EDA_04b) | 標靶卡片(39 欄)+ 統計摘要 | 🧊 |
| `05_visualization/`(README + EDA + `REFINED_CATALOG_53.md`) | 53 張精修圖庫 | 🧊 |
| `06_animation/README.md` | 動畫展示層 | ✅ |
| `07_dashboard/README.md` | React portal 資料(`real-dataset.json`) | ✅ |
| `reproducibility_audit/`(`figure_registry.md` + parity/verification 4 檔) | 圖表譜系 + R/Python parity + 第三方重現 | ✅ |
| `closure_audit/`(5 檔:backend/frontend coverage、final closure、module isolation、data dict) | 收尾稽核 | ✅ |
| `_validation/`(cross_validation + opus_review round1/2) | 交叉驗證與 review | ✅ |
| `_docs/data_dictionary.md` · `_docs/stage_manifest.SUPERSEDED.md` | 階段資料字典(SUPERSEDED 為已汰換) | ⚠️ manifest 已標 SUPERSEDED |

> 其他 pipeline 子資料夾(`blindspot_fixes` / `context_specific` / `cover` / `delivery_decision` / `kinetics_avoid` / `methodological_validation` / `signed_de_application` / `ui_prototypes` / `level4_external_validation` / `perturbase_review`)各有 README/報告,屬 MVP 研究工作包,見各自資料夾。

---

## 3. 程式各階段 code README(`src/`)

| 階段 | README | 現況 |
|---|---|---|
| `src/1_preprocess/` | ✅ 有 | ✅ |
| `src/2_embedding/` | ✅ 有 | ✅ 已補 |
| `src/3_DE_analysis/`(工具主體) | ✅ 有 | ✅ |
| `src/4_polarization_signatures/` | ✅ 有 | ✅ 已補 |
| `src/5_cytokine_regulators/` | ✅ 有 | ✅ 已補 |
| `src/6_functional_interaction/` | ✅ 有 | ✅ 已補 |
| `src/7_1k1k_analysis/` | ✅ 有 | ✅ 已補 |
| `src/8_lymphocyte_counts_LoF/` | ✅ 有 | ✅ |
| `src/9_cell_integration/`(+ `RUN_ON_REAL_DATA.md`) | ✅ 有 | ✅ 程式就緒,真實資料委外 |
| `src/10_ml_perturbation_prediction/`(+ gears/results READMEs) | ✅ 有 | ✅ 新增(ML 擾動預測 benchmark) |

> 所有 `src/1–10` 階段皆有 README(`src/2/4/5/6/7` 已補上簡潔版)。論文圖對照見 `metadata/figure_map.md`。

---

## 4. 權威規格 Docs(逐字真相)

| 檔案 | 用途 | 現況 |
|---|---|---|
| `docs/IMPLEMENTATION_PLAN.md` | 活的實作計劃(Wave 完成/驗證) | ✅ |
| `docs/DRUG_DISCOVERY_TOOL_DEVELOPMENT_PLAN.md` | 策略層 | ⚠️ 含 Streamlit 歷史字樣 |
| `docs/technical_methods.md` | 方法/校準/限制/參考(peer-review 級) | ✅ |
| `docs/data_dictionary.md` | 每欄逐欄定義 | ✅ |
| `docs/de_and_baseline_spec.md` | NTC 基線與 DE 方法學 | ✅ |
| `docs/concept_dictionary.md` | 概念模組 M01–M20 | ✅ |
| `docs/server_modules.md` | 13 個 API router 參考 | ✅ |
| `docs/provenance_registry.md` / `.csv` | 資料來源×演算法×參考登錄表 | ✅ |
| `docs/figure_guide.md` | 圖表判讀路徑 | ✅ |
| `docs/cache_and_versioning_policy.md` | 快取與版本失效 | ✅ |
| `docs/data_governance_checklist.md` | 資料治理與授權 | ✅ |
| `docs/KNOWN_LIMITATIONS.md` | 已知限制 | ✅ |
| `docs/REPRODUCIBILITY.md` | 重現指引 | ✅ |
| `docs/ROADMAP.md` / `docs/next_phases_plan.md` / `docs/improvement_roadmap.md` | 路線圖/後續階段 | ✅ |
| `docs/architecture_refactor_plan.md` | 架構分層重構 | ✅ |
| `docs/compass_concept_integration_plan.md` | COMPASS 概念整合 | ✅ |
| `docs/external_overlay_integration_concept.md` | 安全+膜蛋白 overlay 概念 | ✅ |
| `docs/ml_feasibility_assessment.md` | ML 可行性評估(對應 src/10) | ✅ |
| `docs/human_validation_protocol.md` / `docs/external_qa_review_2026-07-10.md` | 人工驗證協定 / 外部 QA | ✅ |
| `docs/perturbation_validation_plan.md` | **擾動驗證盤點+計劃**:5 級階梯逐級 MET/GAP + 閉合缺口的優先序計劃(L5 濕實驗設計) | ✅ 新增 |
| `docs/validation_status.csv` / `docs/validation_report.md` | **一鍵驗證報告**(單一真相源):由 `src/3_DE_analysis/validation/run_all_validation.py` 產出,L4 數字即時重算、L1–L3/L5/校準為文件化常數(含來源檔) | ✅ 新增 |
| `docs/sandbox_blocked_tasks.md` / `docs/def_followup_plan.md` / `docs/server_northstar.md` | 沙盒受限 / 後續 / north-star | ✅ |

---

## 5. 導覽 Wiki(9 頁)+ 研究 sources + metadata

**Wiki**:`Home`(介紹)· `Development-Guide` · `Manual` · `Map` · `Maintenance` · `Roadmap` · `Plan` · `Tech-Debt` · `_Sidebar` / `README`。**現況**:✅,惟 §7 修正的舊字樣(見下)。

**sources/**:`topic01–16`(研究主題)· `topic09_eda_report.md`(摘要層 EDA)· `topic07_key_papers_and_pmids_summary.md`(引用)· `project_decision_log.md` · `project_roadmap.md` · `release_notes_m3_5_upload_import.md` · `csv_cell_roadmap_and_figures.md`。**現況**:✅(研究快照,時間性內容)。

**metadata/**:`README.md` · `data_sharing_readme.md`(逐欄定義)· `figure_map.md`(論文圖→腳本)· `suppl_tables/full_signed_DE/README.md`。**現況**:✅。

---

## 6. 需更新 / 待補(staleness watch)

| 項目 | 位置 | 動作 |
|---|---|---|
| 測試數 18 → **34** | `wiki/Development-Guide.md`、`wiki/Manual.md` | ✅ 本輪修正 |
| 前端 Streamlit → **React portal** | `wiki/Home.md`、`wiki/Manual.md`、`wiki/Maintenance.md`、`wiki/Map.md` | ✅ 本輪修正 |
| `src/2/4/5/6/7` 缺 README | `src/` | ✅ 已補(簡潔版) |
| 歷史文件含 Streamlit 字樣 | `docs/frontend_*`、`PIPELINE_LINEAGE`、mvp-research/visualization、closure_audit 等 | ⏸️ 保留(歷史計劃/稽核紀錄,非現況宣稱) |
| `_docs/stage_manifest.SUPERSEDED.md` | pipeline/_docs | ⏸️ 已標 SUPERSEDED |

> 原則:**面向使用者的現況描述**(wiki 導覽、frontend README、能力表)保持最新;**歷史計劃/稽核/research 快照**保留當時狀態,不追改(改寫會抹除紀錄)。

---

> 本索引隨新增文件更新。逐字權威以各 `docs/` 檔與程式為準;版本語意見 `cache_and_versioning_policy.md`。
