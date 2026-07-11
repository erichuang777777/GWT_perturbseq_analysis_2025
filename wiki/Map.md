# 架構與文件地圖 Architecture & Docs Map

> 一頁看懂整個專案怎麼串起來:**入口導覽站 → Wiki 導覽層 → `docs/` 權威層 → 程式/資料**,以及「我是誰、該從哪讀」。

---

## 1. 文件地圖(從入口到權威)

```
                         ┌──────────────────── 入口導覽站(給人讀) ────────────────────┐
                         │                                                              │
                🧬 科普導覽 (docs/explainer/)                🔬 研究人員導覽 (docs/researcher_guide/)
                一般大眾:概念、為什麼重要                    科研人員:如何判讀/使用平台
                         │                                                              │
                         └───────────────────────────┬──────────────────────────────────┘
                                                      ▼
                    ┌──────────────────────── Wiki 導覽層(本 wiki) ───────────────────────┐
                    │  Home(介紹)· Development-Guide(開發說明)· Manual(完整手冊)         │
                    │  Map(本頁)· Maintenance · Roadmap · Plan · Tech-Debt                 │
                    └──────────────────────────────┬───────────────────────────────────────┘
                                                    ▼
                    ┌──────────────────────── docs/ 權威層(逐字規格) ─────────────────────┐
                    │  server_modules.md ── API 各模組/端點                                   │
                    │  technical_methods.md ── 方法、校準、限制、正式參考文獻                  │
                    │  figure_guide.md ── 圖表判讀(嵌真實圖 + 完整目錄)                      │
                    │  concept_dictionary.md ── 免疫概念模組 M01–M20                          │
                    │  data_dictionary.md · de_and_baseline_spec.md ── 欄位/DE 基線            │
                    │  cache_and_versioning_policy.md · data_governance_checklist.md          │
                    │  IMPLEMENTATION_PLAN.md ── 活的實作計劃(權威狀態)                      │
                    └──────────────────────────────┬───────────────────────────────────────┘
                                                    ▼
                    ┌──────────────────────── 程式與資料(ground truth) ───────────────────┐
                    │  src/3_DE_analysis/(工具主體)· src/1–9(論文流程 + 細胞層級)          │
                    │  metadata/suppl_tables/(DE_stats…)· sources/(證據快照/EDA/圖庫)       │
                    └──────────────────────────────────────────────────────────────────────┘
```

---

## 2. 系統架構(資料 → 決策 → 對外)

```
 原始 Perturb-seq 實驗 [公開資料]
   4 donors × 3 conditions × 2 runs → guide 指派 → pseudobulk → DESeq2 DE → 穩健性/敲低檢定
        │  supplementary tables(33,983 列 DE)
        ▼
 src/3_DE_analysis  ── build_target_cards → readiness_engine(12 領域→R0–R5→紅旗覆蓋)→ 決策
        │              + calibration · external_evidence · disease_translator · concept 層(M01–M20)
        ▼
 api/(FastAPI, 13 routers) ──HTTP/JSON──▶ frontend/(Streamlit 儀表板)
        │
        └─ upload/(usr_ 隔離的研究者上傳)
```

> 詳版 ASCII(端到端資料流、後端分層、就緒度決策流、repo 地圖)見 **[完整手冊 Manual](Manual)** §2。

---

## 3. 我是誰,該從哪讀

| 你是… | 建議入口 | 接著讀 |
|---|---|---|
| 第一次接觸、想懂概念 | 🧬 科普導覽 | [介紹 Home](Home) |
| 想用/判讀平台的研究者 | 🔬 研究人員導覽 | `server_modules` → `technical_methods` → `figure_guide` → `concept_dictionary` |
| 要一起開發 | [開發說明 Development-Guide](Development-Guide) | [技術債 Tech-Debt](Tech-Debt)、`architecture_refactor_plan` |
| 要跑/維護 | [維護 Maintenance](Maintenance) | `cache_and_versioning_policy` |
| 想看全貌與引用/數據來源 | [完整手冊 Manual](Manual) | `technical_methods`(參考文獻) |
| 想看進度與規劃 | [路線圖 Roadmap](Roadmap) · [計劃 Plan](Plan) | `IMPLEMENTATION_PLAN.md` |

---

## 4. 四份權威文件的分工(給研究者的閱讀動線)

```
server_modules.md  ─▶  technical_methods.md  ─▶  figure_guide.md  ─▶  concept_dictionary.md
（server 有什麼、       （方法/校準/限制/         （圖表怎麼讀、         （M01–M20 概念層
  怎麼呼叫)             正式參考文獻)             完整圖目錄)           細節)
```

> 本頁是地圖;任何數字/宣稱以 `docs/` 對應規格與程式為準。
