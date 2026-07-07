# 路線圖 Roadmap

本頁摘要已完成的開發波次(Wave)與未來方向。權威狀態表在 `docs/IMPLEMENTATION_PLAN.md`。

## 已完成的波次

### Wave 1 — 基礎(PR #1,已合併)
- 可 import 的 `build_cards_frame()` 重構(從 subprocess 改為 in-process)
- 真實的 `batch_sensitivity_flag`(取代 stub):只有 `Stim48hr` 被標記
- 就緒度引擎(R1–R3):12 領域 → R0–R5 → 決策
- 欄位對應精靈 + 上傳合併迴圈(暫存 → 核准 → 合併 → 卡片)
- 儀表板串接

### Wave 2 — 小型、離線可驗證
- **C7 broad-effect 隔離**:239 個染色質/轉錄機器基因(Mediator/SAGA/HAT-HDAC/SWI-SNF 等)加上 `broad_effect` 紅旗,封頂在 watchlist。修正 MED12/CREBBP/KDM1A/SGF29 原本會 advance 的問題。
- 本機 druggability/safety overlay 欄位(`druggable_class` / `tractability_modality` / `safety_note`)
- 校準 harness(正對照recovery、藥物軸富集、排序穩定度)

### Wave 3 — 外部證據 + provenance
- 外部證據層(ClinicalTrials.gov / PubMed / Open Targets 快取優先 fetcher);9 個基因以真實證據種入
- provenance footer(engine_version / built_at / data_version / dataset_version)
- **誠實 descope**:§1.5 signed module scoring 因為 `DE_stats` 只有 up/down 計數、沒有 per-gene 方向而放棄 — signed 分數會是捏造的

### Wave 4 — 疾病轉譯
- 疾病轉譯器:對接 repo 內既有的 Open Targets 基因關聯匯出(7,528 列、13 適應症),不需新 fetch
- **§1.8 多人/Supabase 持久化明確 deprioritized**(專案負責人決定),未佈署任何雲端基礎設施

### Wave 5 — 儀表板視覺化
- QC funnel 圖(重現 EDA 嚴格過濾級聯;`n_total_de_genes>=50` 階段恰為 4,182 列)
- 全資料集 cross-guide vs cross-donor 散點圖
- per-target 證據組成圖

### 細胞層級(h5ad)延伸(§1.9)— 程式完成,真實資料執行待辦
- 位於 `src/9_cell_integration/`,含 guide 指派 QC、Mixscape 式回應者/逃逸者分類(scikit-learn 重寫)、誠實的 SCEPTRE 外部 hook、CD4 program 評分,以及回接標靶卡片欄位的橋接。
- 對schema一致的合成 fixture 驗證,分類準確率 **81.8%**。
- **硬限制**:真實資料集 1.68 TiB(最小單檔約 131 GiB)超過沙盒 29 GiB 可用磁碟,因此真實資料執行委由專案負責人在自己機器進行(見 `src/9_cell_integration/RUN_ON_REAL_DATA.md`)。**未宣稱已跑過真實資料。**

### Wave 6 — 平台級 backlog(B1/B2/B5/B6/C3/C4/C5/C6)
- **B1** 基因識別解析(Ensembl 主鍵 + 真實別名表,344/12,654 基因有設計時/curated 符號差異)
- **B2** 三態 `result_status`(not_in_library / not_expressed / no_significant_effect / has_effect)
- **B5** CRE schema 佔位(空但有效的資料契約,repo 內無 CRE 資料)
- **B6** difflib 別名容錯搜尋(不引入資料庫基礎設施)
- **C3** 29 個自動化測試
- **C4** 資料字典
- **C5/C6** 資料治理檢查清單 + 快取/版本失效政策

## 未來方向(尚未排程)

### §1.10 v2 假設產生器(guarded、optional)
Signature-to-compound(LINCS/CMap)、機制圖、擾動預測(**先對 baseline 做 benchmark;永不餵入 readiness 決策**)、組合探索器(僅供研究)。目前未開始;在 §1.9 之後負責人的請求被導向平台級 backlog(Wave 6),此項讓路。

### §1.12 安全性 + 膜蛋白/tractability overlay(概念,卡在真實資料)
專案負責人有兩份資料:(a) CellxGene 基於的基因安全性驗證結果、(b) 內部膜蛋白資料庫(motif length、expression、TCGA/GTEx,原為 ADC 標靶探索建立)。兩者正好對應 `readiness_engine.py` 目前幾乎全為 `"unknown"` 的兩個領域:`safety_window_score` 與 `tractability_modality`。完整設計(schema 草圖、對應到哪個函式、卡住的開放問題)在 `docs/external_overlay_integration_concept.md`。**尚未排程**,等真實檔案/欄位確定後才動手。

### 多人平台化(§1.8,已 deprioritized)
從 file-cache 移到 Supabase/Postgres + auth + per-user workspace。目前是單人/file-cache 研究用途;若多位研究者需要隔離工作區再重啟。**目前平台沒有存取控制**,`usr_` 命名空間只防止意外混料,不是授權隔離。
