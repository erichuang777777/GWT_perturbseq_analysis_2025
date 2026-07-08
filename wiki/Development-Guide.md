# 開發說明 Development Guide（協同開發指南）

> 這頁是給**一起開發的夥伴**看的入口文件:用最短時間搞懂「這專案在做什麼、現在到哪、目標是什麼、我可以從哪動手」。內容全部對應 repo 內真實檔案,無臆測數字。深入細節時再往各專頁與 `docs/` 走。

## 0. 30 秒認識這個專案

我們在 **Marson lab CD4 T 細胞 genome-scale Perturb-seq 篩選資料**(bioRxiv `10.64898/2025.12.23.696273v1`)之上,建一套**藥物標靶優先排序工具**:把大規模 CRISPRi 擾動的差異表現(DE)結果,轉成研究者能直接判讀的「標靶卡片(target card)」,並給出可辯護的 **推進 / 驗證 / 觀察 / 降級**(advance / validate / watchlist / deprioritize)決策。

- 想看完整能力總覽與設計原則 → **[介紹 Home](Home)**
- 想看逐塊的規格與驗收 → repo 的 `docs/IMPLEMENTATION_PLAN.md`(活的權威計劃)

## 1. 現況一覽(進度快照)

已完成並經離線驗證的開發波次(權威狀態表在 `docs/IMPLEMENTATION_PLAN.md`,摘要在 **[路線圖 Roadmap](Roadmap)**):

| 波次 | 內容 | 狀態 |
|---|---|---|
| Wave 1 | 可 import 的卡片建構、就緒度引擎(R0–R5)、上傳合併迴圈、儀表板串接 | ✅ 已完成 |
| Wave 2 | broad-effect 隔離(239 基因)、druggability/safety overlay、校準 harness | ✅ 已完成 |
| Wave 3 | 外部證據層(ClinicalTrials/PubMed/Open Targets 快取優先)、provenance footer | ✅ 已完成 |
| Wave 4 | 疾病轉譯器(13 適應症、7,528 列 Open Targets 關聯) | ✅ 已完成 |
| Wave 5 | 儀表板視覺化(QC funnel、cross-guide/donor 散點、證據組成圖) | ✅ 已完成 |
| Wave 6 | 平台級 backlog:基因識別解析、三態 result_status、CRE schema 佔位、模糊搜尋、測試、資料字典、治理/版本政策 | ✅ 已完成 |
| 細胞層級(h5ad)延伸 | guide QC、Mixscape 式回應者分類、CD4 program 評分 — **程式完成,真實資料執行待負責人自跑** | 🟡 程式就緒 |

**進行中 / 未排程**:v2 假設產生器(§1.10)、安全性+膜蛋白 overlay(§1.12,卡在真實資料)、多人平台化(§1.8,已 deprioritized)。細節見 **[路線圖 Roadmap](Roadmap)**。

**目前已知需優先處理的技術債**:上傳路徑的兩個正確性問題(`kd_status` 把「從未測量」當「測量失敗」、對應後遺失 `n_total_de_genes`)是合併前建議阻擋項 → 見 **[技術債 Tech-Debt](Tech-Debt)** A.1 / A.2。

## 2. 目標(我們往哪裡走)

- **近期**:把研究者「上傳自己的 DE → 拿到標靶卡片與決策」這條路走順、走對(修 Tech-Debt A.1/A.2 是關鍵)。
- **中期**:讓 `readiness_engine.py` 兩個目前幾乎全 `unknown` 的領域(`safety_window_score`、`tractability_modality`)接上真實 overlay 資料(§1.12 概念已寫在 `docs/external_overlay_integration_concept.md`)。
- **North-star**:朝一個可對外服務的資料入口/API 前進(`docs/server_northstar.md`)。
- **貫穿目標(不可退讓的護欄)**:見下方 §5 的五條設計原則。

規格與排序的權威來源:`docs/IMPLEMENTATION_PLAN.md` 與 **[計劃 Plan](Plan)**。

## 3. 快速上手(15 分鐘)

```bash
# 1. 建環境(conda)
conda env create -f environment.yaml
conda activate gwt-env

# 2. 跑測試(先裝 pytest;真實資料測試在缺 metadata/suppl_tables/*.csv 時會 skip 而非 fail)
pip install -q pytest
python -m pytest tests/ -q

# 3. 啟動後端 API(FastAPI;新路徑,或用相容 shim target_card_api:app)
uvicorn api.app:app --app-dir src/3_DE_analysis
# 健康檢查:GET /api/health 會逐能力回報 available/degraded

# 4. 啟動前端儀表板(獨立套件,只透過 HTTP/JSON 跟 API 溝通)
pip install -r frontend/dashboard/requirements.txt
GWT_API_BASE=http://127.0.0.1:8000 streamlit run frontend/dashboard/target_card_dashboard.py
```

重建 GWT 參考標靶卡片的完整指令與快取/版本規則,見 **[維護 Maintenance](Maintenance)**。

## 4. 程式碼地圖(東西放哪)

| 路徑 | 是什麼 |
|---|---|
| `src/1_preprocess/` … `src/8_lymphocyte_counts_LoF/` | 論文原始分析流程(preprocess → embedding → DE → 訊號 → 調控子 → 交互作用 → 1k1k → LoF) |
| `src/3_DE_analysis/` | **標靶探索工具主體**(見下表細分) |
| `src/9_cell_integration/` | 細胞層級(h5ad)延伸;真實資料執行說明在 `RUN_ON_REAL_DATA.md` |
| `docs/` | **權威規格與計劃**(IMPLEMENTATION_PLAN、data_dictionary、各 spec/policy) |
| `frontend/` | 獨立可部署的前端(目前是 Streamlit 儀表板),只走 API |
| `tests/` | 18 個測試檔(golden-file / join-integrity / known-answer / empty-state 等) |
| `metadata/` | 樣本與實驗 metadata、config、基因註釋、supplementary tables |
| `sources/` | 研究/證據快照與快取(含 `broad_effect_genes.txt`、target_tool_cache) |
| `wiki/` | 本 Wiki 的原始 Markdown(對應 `.wiki.git`) |

`src/3_DE_analysis/` 內部(架構重構後已分層):

| 子路徑 | 職責 |
|---|---|
| `build_target_cards.py` | 從 DE 統計 + guide 敲低效率彙整卡片 |
| `readiness_engine.py` | 12 領域評分 → R0–R5 → 決策,含紅旗覆蓋 |
| `calibration.py` | 正/負對照校準 harness |
| `external_evidence_cache.py` | ClinicalTrials/PubMed/Open Targets 快取優先 fetcher |
| `disease_translator`(見 routers)/ `population_hypothesis.py` | 疾病轉譯與族群 LoF 假設 |
| `api/`(`app.py` + `routers/` + `deps.py`) | FastAPI 組裝:每個資源區一個 router,單一 router import 失敗不會拖垮整個 API |
| `resolve/`(`resolver.py`/`search.py`/`cre.py`) | 基因識別解析(Ensembl 主鍵)、模糊搜尋、CRE schema |
| `upload/import_manager.py` | 暫存優先的上傳流程與欄位對應 |
| `common/`(`coerce`/`degrade`/`timeutil`/`overlay_lookup`/`evidence_grading`) | 跨模組共用的型別轉換、優雅降級、時間戳、overlay 查表 |
| `config/`(`settings`/`thresholds`/`versions`) | 單一來源的設定、門檻常數、四層版本 |

## 5. 開發流程與慣例(請務必遵守)

**Git 流程**
- 每個工作切自己的分支(慣例 `claude/<主題>-<id>` 或 `feature/<主題>`),**不要直接推 `main`**。
- PR 一律先開 **draft**;若 repo 有 PR 模板則照模板填。
- 合併前測試要綠燈:`python -m pytest tests/ -q`。

**五條設計原則(貫穿全平台,PR review 會盯)**
1. **`unknown` ≠ `0`** — 未建置的證據領域一律回明確 `"unknown"`,絕不悄悄給 0 分。
2. **紅旗覆蓋** — 不論統計多強,essential / broad-effect / off-target / 方向不明 / 批次混淆 / 敲低未確認都會封頂決策。
3. **CRISPRi ≠ 藥理學** — 體外 CD4 情境注意事項始終顯示在卡片上。
4. **上傳資料隔離** — 使用者上傳永遠命名空間隔離(`usr_` 前綴),絕不混入 GWT 參考集。
5. **可重現與版本化** — 每個資料集帶四層版本(`engine` / `dataset` / `schema` / `signature_set`),provenance 是欄位不是註腳。

**誠實文化**
- 卡在資料/環境限制時,**明確 descope 並記錄**(見 Tech-Debt §D),不要用捏造的數字或天真重寫來假裝完成。「對合成 fixture 驗證過」與「已跑過真實資料」是不同宣稱,不要混用。

## 6. 想接手?從這裡開始(good first tasks)

依影響力排序(細節、檔案:行號都在 **[技術債 Tech-Debt](Tech-Debt)**):

1. 🔴 **Tech-Debt A.1** — `_kd_status` 區分「NaN 基線(從未測量)」與「已測量低於 floor」,讓純上傳資料不被誤判為敲低失敗(違反 repo 自己的治理原則,建議優先)。
2. 🟡 **Tech-Debt A.2** — 把 `n_total_de_genes` 加入 canonical 上傳 schema,讓欄位對應精靈能傳遞它。
3. 🟡 **Tech-Debt A.3–A.5** — 寫死條件名、readiness 新鮮度檢查、格式錯誤 guide 表靜默退化。
4. ⚪ **效能/重用**(Tech-Debt B/C)— 34k 列的逐列 apply 向量化、每請求重讀 CSV 加快取、消除重複輔助函式。

不確定某項該怎麼做時,先在 Issue 或 PR 討論,不要擅自做大重構。

## 7. 權威文件在哪(source of truth)

Wiki 是導覽層;真正逐字的權威在 `docs/`:

- `docs/IMPLEMENTATION_PLAN.md` — 活的實作計劃(每個 Wave 的完成/驗證表)
- `docs/DRUG_DISCOVERY_TOOL_DEVELOPMENT_PLAN.md` — 策略層(為什麼做、功能面)
- `docs/data_dictionary.md` — 每個產出欄位的逐欄定義
- `docs/de_and_baseline_spec.md` — NTC 基線與 DE 方法學
- `docs/data_governance_checklist.md` — 資料治理與授權
- `docs/cache_and_versioning_policy.md` — 快取與版本失效政策
- `docs/external_overlay_integration_concept.md` — 安全性 + 膜蛋白 overlay 整合概念
- `docs/server_northstar.md` — 對外服務/資料入口的 north-star

## 8. 分工與溝通

- 有問題或要認領工作:在本 repo 開 [Issue](https://github.com/erichuang777777/GWT_perturbseq_analysis_2025/issues) 討論並認領。
- 進度與目標:以 `docs/IMPLEMENTATION_PLAN.md` 為準,本頁與 [Roadmap](Roadmap)/[Plan](Plan) 提供導覽視角。
- 原始資料/科學問題聯絡窗口見主 repo `README.md` 的 Contact 段落。

---

> 讀完這頁,建議接著看:**[介紹 Home](Home)** → **[路線圖 Roadmap](Roadmap)** → **[計劃 Plan](Plan)** → **[技術債 Tech-Debt](Tech-Debt)** → **[維護 Maintenance](Maintenance)**。
