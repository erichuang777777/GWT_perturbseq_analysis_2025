# 三模組定位對照與雲端同步 — MODULE_ALIGNMENT

**狀態：** 定位釐清文件 · **對照：** `main` @ `a726ab03`（PR #7 已合併）· **語言：** 繁體中文

## 這份文件為什麼存在

本地 session（視覺化 + 模組討論）與雲端 session（`next_phases_plan.md` 指揮的 A/B/C 實作）平行開發。這份文件把**三大模組的定位**與**雲端已實作的檔案**釘在一起，避免兩邊規劃語彙分歧、避免重複造輪子。凡涉及開發規格，一律以 `docs/next_phases_plan.md` 為準；本文件只補「模組定位」這一層。

---

## 三大模組定位（本次討論釐清）

| | 模組一 Discover | 模組二 整合比較 | 模組三 治療反應/建議 |
|---|---|---|---|
| **一句話** | 用現有資料排名 target | 使用者上傳分子資料，比對到參考 | 臨床情境 → 證據強度 |
| **輸入** | GWT DE 統計 | 分子資料（scRNA / bulk / DE 表） | 臨床情境（診斷 + 已知藥物/標的） |
| **動作** | 排名 + readiness | 比對 / 定位（map onto reference） | 證據匹配 / 假設 |
| **輸出** | ranked target cards | 「你的資料落在參考的哪裡」 | 「這個標的-疾病配對證據多強」 |

**模組二與三為何不重複：** 模組二吃**分子資料**、輸出「落點」；模組三吃**臨床情境**、輸出「證據強度」。共用同一基底（target cards + readiness engine + provenance），但回答不同問題。

---

## 模組二：demo 版 vs 最終目標（對映雲端實作）

模組二的最終目標是**參考映射（reference mapping）**：把使用者的 scRNA 細胞投影到 GWT 的 CD4 細胞狀態參考，回答「你的細胞落在哪些狀態、哪些擾動訊號活躍」。這需要 cell-level 運算（雲端 1.7TB h5ad + scVI/scArches label transfer），是最終形態。

**Demo 版**用輕量的 signature scoring 展示「使用者資料 → 落在哪個訊號」這個動作的形狀——而雲端 PR #7 的 `signature_explorer.py` 正是這個 demo 版：

| 層 | 對映檔案 | 狀態 |
|---|---|---|
| Demo 版（signature connectivity） | `src/3_DE_analysis/signature_explorer.py`（A1a） | ✅ 已實作（PR #7） |
| — query signature 建構 | `build_query_signature()` | ✅ |
| — connectivity 演算法 | `connectivity_score()` / `score_target_against_reference()` | ✅ |
| — 參考 signature | `combined_Th2_vs_Th1_signature.csv`、`CD4T_aging_signature_*.csv` | ✅ repo 內 |
| 化合物比對（LINCS/CMap） | `match_reference_compounds()`（A1b） | ⏳ honest-stub（沙盒無法連 LINCS） |
| **最終版（cell-level reference mapping）** | 尚未建立 | 🎯 最終目標，需雲端 h5ad + scVI |

**升級點（關鍵）：** demo 版與最終版共用同一資料契約——「使用者樣本 → GWT 參考的落點 + 分數」。升級時換的是 `map_to_reference()` 的內部實作（signature scoring → scVI label transfer），**不換輸出 schema、不換前端**。這保證 demo 不是拋棄式的。

---

## 模組三：定位與雲端實作對映

模組三吃臨床情境，輸出證據強度與假設（非治療處方，維持研究用邊界）。對映雲端：

| 功能 | 對映檔案 | 狀態 |
|---|---|---|
| 疾病-藥物證據匹配 | `external_evidence_cache.py` 的 `match_disease_drug_evidence()` | ✅ 已實作 |
| 群體 LoF 負荷假設 | `population_hypothesis.py`（Backman UK Biobank） | ✅ 已實作 |
| 擾動預測 benchmark | `perturbation_prediction_benchmark.py`（A3） | ✅ 已實作（僅評測框架，不餵 readiness） |
| 機制圖 | `mechanism_graph.py`（A2） | ✅ 已實作 |

**A3 的定位要特別講清楚：** `perturbation_prediction_benchmark.py` **不是預測模型**，是「誠實比較預測方法 vs baseline 的評測框架」——用 Rest/Stim8hr/Stim48hr 三條件做 held-out（給兩個條件預測第三個），對比 baseline（用平均效應）。護欄：結果只進 benchmark 報告，絕不寫入 target_cards 或 readiness。這是模組三「預測」方向的**誠實起點**：先證明/證偽預測可行性，而非直接輸出病人層預測。

---

## 視覺化模組（本地 session 已交付，PR #7 已進 main）

`docs/mvp-research/visualization/` — 三階段：靜態圖表目錄（31 圖）、互動設計規格 + plotly 原型、3D（5 個 AlphaFold .cif + 3D 資料散點）。詳見 `VISUALIZATION_MODULE_設計文件.md`。

**建議補充的三張 target-排名專用圖**（文獻確認、尚未做）：
1. **擾動×擾動相關性聚類熱圖**（Replogle genome-scale Perturb-seq 招牌圖）— 需 pseudobulk 表現譜（雲端 44.6GB），看哪些 target 效應雷同。
2. **DE 基因 Jaccard 相似度熱圖**（FOXP3 論文）— 用現有 up/down 基因數可做近似版。
3. **雙向 hit score 排名**（cytokine 篩選）— 區分敲低後效應變強 vs 變弱。

---

## 兩邊同步狀態

- **main @ `a726ab03`**：三大模組核心 + A1a/A2/A3 + 架構重構 Phase 2-4 + 視覺化模組，全部已合併。
- **無 open PR**：目前兩邊同步，無待合併分支。
- **開發規格單一來源**：`docs/next_phases_plan.md`（三方向 A/B/C（A 再細分 A1–A4）+ 建議排序）。本文件只補模組定位層，不與之衝突。

## 共用護欄（與 next_phases_plan 一致）

- `unknown ≠ 0`：無資料 honest-fallback。
- 描述性 vs 決策性分離：signature/機制圖/預測 benchmark 都是描述性/探索性，不進 readiness `_stage()`。
- CRISPRi ≠ 藥理學；signature-to-compound、擾動預測輸出都是「假設+線索」，附方法學 caveat，非療效宣稱。
- 模組三維持研究用邊界：輸出證據強度與假設，非病人層治療處方。
