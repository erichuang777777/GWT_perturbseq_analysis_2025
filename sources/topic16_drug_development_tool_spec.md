# CD4 Perturb-seq 藥物開發輔助工具：技術規格（MVP to v1）

## 目標

建立一個「能夠把 GWT perturb-seq 結果轉成藥物研發決策輸出的平台」，核心輸出不是只做排序，而是輸出可追蹤、可審計的 `target-card`（含統計信心、條件特異性、外部證據、臨床類比與風險提醒）。

## 為什麼這樣做

- 避免把 `DE` 當成唯一證據。
- 讓每個 target 都有可重複驗證的欄位：`replicate-pass / consistency / limitation / next-experiment`。
- 提供可直接支援你後續 in vivo / 功能驗證規劃。

## 目前可直接落地的最小可行版本（MVP）

先用 CSV/summary tables，不用一次吃進 1.6TB h5ad。

- 輸入：`DE_stats.suppl_table.csv`、`guide_kd_efficiency.suppl_table.csv`、`sgrna_library_metadata.suppl_table.csv`
- 輸出：`target cards` + `program score` + `優先驗證清單`
- 參考實作：`src/3_DE_analysis/build_target_cards.py`

## 系統架構（建議）

1) Ingestion Layer（輸入）
- 讀取 local suppl tables、optional 外部快取表
- 負責欄位標準化與版本管理
- 最小 schema：
  - `dataset_id`
  - `source_file`
  - `sha256`
  - `updated_at`

2) Evidence Layer（證據）
- 主要計算 target-condition 的:
  - `n_cells_target`, `n_total_de_genes`, `ontarget_significant`, `offtarget_flag`
  - `crossdonor_correlation_mean`, `crossguide_correlation`
  - guide KD summary（`guide_signif_ratio`, `guide_fdr_min`）
- 直接對應到規格檔：
  - `target-card_specification.md`

3) Biology Mapping Layer（生物語義）
- 對齊 CD4 程式集合：
  - `topic15_cd4_tcell_upstream_downstream_seed_modules.csv`
  - `topic15_cd4_tcell_upstream_downstream_framework.md`
- 輸出 `pathway_axis` 與 module hit list

4) Clinical Risk Layer（臨床風險）
- 成功/失敗臨床軸 overlay
  - 來源：`topic05_successful_drug_benchmarks.csv`、臨床試驗資料
- 產生：
  - `nearest_success_drug`
  - `nearest_failure_or_warning`

5) Decision Layer（決策）
- 規則引擎輸出一欄位：`statistical_evidence_grade`（1~4）
- 過濾/降階欄位：`score_cap_reason`（如 low_cells/weak_replicability/high_offtarget）

6) Reporting Layer（報表）
- target ranking、watchlist、watchlist 解除條件、follow-up 實驗建議
- 支援 CSV/JSON/HTML 三格式輸出

## 建議 API/Service（後續做為 web 工具）

後端 API（FastAPI）建議 endpoint：

- `POST /api/upload/local-tables`
  - 上傳/更新 `DE_stats`、`guide_kd`、`library metadata`
  - 回傳 `dataset_id`
- `POST /api/run/target-card`
  - 呼叫統一 job，產生 target cards
  - 參數：`min_cells`, `min_de`, `enforce_replicability`
- `GET /api/targets/{dataset_id}`
  - 查詢 target card 清單，支援排序與篩選
- `GET /api/targets/{dataset_id}/{target_id}`
  - 查 target 詳細檔案（統計、pathway、臨床類比、limitation）
- `GET /api/modules/{dataset_id}`
  - 查上游/下游模組得分
- `GET /api/exports/{dataset_id}`
  - 匯出 CSV/JSON/簡報摘要

## 資料表建議 Schema（簡化）

### `target_card`
- `dataset_id` (PK)
- `target_id`
- `condition`
- `target_gene`
- `n_cells_target`
- `n_guides`
- `n_donors`
- `n_total_de_genes`
- `n_up_de_genes`
- `n_down_de_genes`
- `ontarget_significant`
- `offtarget_flag`
- `crossdonor_correlation_mean`
- `crossguide_correlation`
- `replicate_pass_flag`
- `pathway_axis`
- `condition_specificity_score`
- `clinical_axis`
- `nearest_success_drug`
- `nearest_failure_or_warning`
- `statistical_evidence_grade`
- `score_cap_reason`
- `created_at`

### `target_module_score`
- `dataset_id`
- `target_id`
- `condition`
- `module_id`
- `module_score`
- `module_delta_vs_rest`
- `direction`

### `evidence_event`
- `dataset_id`
- `target_id`
- `condition`
- `stage`（statistical/biological/clinical）
- `status`（pass/warn/fail）
- `message`

## 前端畫面建議（MVP）

1. `Dashboard`
- 顯示 Top-100 target、Grade 分布、資料品質快照

2. `Target Explorer`
- 篩選條件：
  - condition
  - grade
  - pathway axis
  - score_cap_reason
- drill-down 展示 target-card 全欄位

3. `Program Explorer`
- 對每個 target 畫 module profile（雷達/棒狀）
- 切換 seed module 群組（TCR/Th1/Th17/Treg…）

4. `Clinical Context`
- 成功軸 / 失敗警訊對照
- 自動標示安全性注意（如 T-cell overactivation 風險）

## 開發里程碑（建議）

### 第 1 週：可執行 MVP（CSV-first）
- 對接 `build_target_cards.py` 成 API
- 提供 target card API + CSV 匯出
- 加入 score cap reason + 排序

### 第 2 週：決策可視化
- 建立 dashboard（Streamlit）
- 加入條件篩選、目標 drill-down、模組映射
- 接上 limitation 表：顯示 `topic15_limitation_future_work_audit_table.md` 對應註記

### 第 3 週：外部 evidence overlay
- 接 Open Targets/ChEMBL/DGIdb 快取
- 加入臨床軸與 warning 標籤
- 輸出實驗建議清單（KD 驗證 / 蛋白 / cytokine / 功能 assay）

### 第 4~6 週：h5ad 升級
- 加入 replicate-aware 統計、pseudobulk model
- 支援 cell-level 補充：pathway activity、responder 分析

## 安全與風險控制

- 不把單一統計結果直接視為可開發決策
- 對每一個高分 target 必須有 `validation_plan`
- `score_cap_reason` 不可空；若為 `none` 必須有正向證據 2 級以上
- 外部 API 來源需快取版本；避免日期漂移改變結果

## 立即可做的 3 個交付（現在就能開始）

1. 跑一版 target cards（命令在 `topic14_target_card_specification.md`）  
2. 把 `topic15 seed modules` 輸入 `build_target_cards` 的下游分析（按 module 產生 module scores）  
3. 建一個最小 Streamlit 頁面，展示 Top-100、watchlist、watchlist 解除條件

## 既有檔案對映

- 規格文件：`sources/topic14_target_card_specification.md`
- target-card 實作腳本：`src/3_DE_analysis/build_target_cards.py`
- 生物模組：`sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv`
- 上游框架：`sources/topic15_cd4_tcell_upstream_downstream_framework.md`
- Limitation 稽核：`sources/topic15_limitation_future_work_audit_table.md`
- 方法總結：`sources/topic14_scrna_biostatistics_validation_methods.md`

