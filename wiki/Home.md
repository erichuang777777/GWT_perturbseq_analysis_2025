# CD4 Perturb-seq 標靶探索工具平台 — 專案 Wiki

> 本 Wiki 以繁體中文撰寫,內容全部對應 repo 內真實存在的程式與資料檔案,不含臆測數字。

CD4 Perturb-seq 標靶探索工具是一套建立在 **Marson lab CD4 T 細胞 Perturb-seq 篩選資料**(bioRxiv `10.64898/2025.12.23.696273v1`)之上的藥物標靶優先排序平台。它把大規模 CRISPRi 擾動的差異表現(DE)結果,轉換成研究者可以直接判讀的「標靶卡片」(target card),並給出一個可辯護的 **推進 / 驗證 / 觀察 / 降級**(advance / validate / watchlist / deprioritize)決策。

## 這個平台在做什麼

| 能力 | 對應模組 | 一句話說明 |
|---|---|---|
| 標靶卡片建構 | `src/3_DE_analysis/build_target_cards.py` | 把 DE 統計 + guide 敲低效率彙整成每個「標靶 × 條件」一列的卡片,含 1–4 級證據強度 |
| 就緒度引擎 | `src/3_DE_analysis/readiness_engine.py` | 12 個領域評分 → R0–R5 階段 → 決策呼叫,含紅旗覆蓋(essential / broad-effect / off-target 等) |
| 校準harness | `src/3_DE_analysis/calibration.py` | 用正對照(TCR 近端基因)與負對照(kd 無法測量群)驗證排序是否recover已知生物學 |
| 外部證據層 | `src/3_DE_analysis/external_evidence_cache.py` | ClinicalTrials.gov / PubMed / Open Targets 的離線快照,附 `fetched_at` 版本戳記 |
| 疾病轉譯 | `src/3_DE_analysis/disease_translator.py` | 把標靶卡片對接到 13 個自體免疫適應症的基因關聯(Open Targets 匯出) |
| 基因識別與搜尋 | `gene_identifier_resolver.py` / `gene_search.py` | 以 Ensembl gene ID 為主鍵的別名解析 + difflib 模糊搜尋 |
| 研究者資料上傳 | `import_manager.py` + API | 暫存優先(staging-first)的上傳流程,含欄位對應精靈與合併到卡片 |
| API / 前端 | `api/app.py`(FastAPI, 13 routers)/ `frontend/webserver/`(React + Vite static portal) | 對外服務與互動介面(舊版 Streamlit 儀表板已由 React portal 取代) |
| 細胞層級延伸 | `src/9_cell_integration/perturbation_response_analysis.py` | h5ad 回應者/逃逸者分類、CD4 program 評分(程式完成,尚待真實資料執行) |

## 設計原則(貫穿全平台)

1. **`unknown` ≠ `0`** — 任何尚未建置的證據領域一律回傳明確的 `"unknown"`,絕不悄悄給 0 分。
2. **紅旗覆蓋** — 不論統計多強,essential / broad-effect / off-target / 方向不明 / 批次混淆 / 敲低無法確認都會封頂決策。
3. **CRISPRi ≠ 藥理學** — 體外 CD4 情境的注意事項始終顯示在卡片上。
4. **上傳資料隔離** — 使用者上傳的資料集永遠命名空間隔離(`usr_` 前綴),絕不混入 GWT 參考集。
5. **可重現與版本化** — 每個資料集都帶四層版本(`engine_version` / `dataset_version` / `schema_version` / `signature_set_version`)。

## Wiki 頁面導覽

- **[介紹(本頁)](Home)** — 平台是什麼、能力總覽、設計原則
- **[開發說明 Development Guide](Development-Guide)** — 給協同開發夥伴:現況、目標、快速上手、程式碼地圖、可接手的第一件事
- **[完整手冊 Manual](Manual)** — 引用文獻、數據來源、文件索引、commit 紀錄與完整 ASCII 架構圖,集中一頁
- **[架構與文件地圖 Map](Map)** — 一頁看懂入口站→wiki→docs→程式怎麼串,以及「我是誰該從哪讀」
- **[維護 Maintenance](Maintenance)** — 環境、測試、重建、快取與版本失效政策
- **[路線圖 Roadmap](Roadmap)** — 已完成的 Wave 1–6 與未來方向
- **[計劃 Plan](Plan)** — 實作計劃摘要與可執行的規格來源
- **[技術債 Tech-Debt](Tech-Debt)** — 已知的正確性問題、descope 與清理項目

## 權威文件對照(repo 內)

本 Wiki 是導覽層;真正的權威規格在 repo 的 `docs/` 底下:

- `docs/IMPLEMENTATION_PLAN.md` — 活的實作計劃(每個 Wave 的完成/驗證表)
- `docs/data_dictionary.md` — 每個產出欄位的逐欄定義
- `docs/technical_methods.md` — 技術方法與驗證說明(peer-review 等級,含正式參考文獻)
- `docs/figure_guide.md` — 圖表導讀(科研人員):把 codebase 圖表整理成正式閱讀路徑,含嵌入圖與判讀
- `docs/server_modules.md` — Server 模組參考:13 個 API router 的用途/端點/輸入輸出 + 概念層 M01–M20,集中一頁
- `docs/provenance_registry.md`(+ `.csv`)— 集中登錄表:資料來源 × 演算法 × 參考文獻,同一組固定欄位(79 列)
- `docs/researcher_guide/` — 研究人員導覽(單頁網站):科研人員如何判讀卡片/決策/校準與呼叫 API,並連向各權威文件
- `docs/de_and_baseline_spec.md` — NTC 基線與 DE 方法學
- `docs/data_governance_checklist.md` — 資料治理與授權檢查清單
- `docs/cache_and_versioning_policy.md` — 快取與版本失效政策
- `docs/external_overlay_integration_concept.md` — CellxGene 安全性 + 膜蛋白 overlay 整合概念
