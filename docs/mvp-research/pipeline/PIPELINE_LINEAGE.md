# GWT Perturb-seq 標的探索平台 — 主 Pipeline 譜系文件

**專案：** CD4 T 細胞 genome-scale Perturb-seq 標的發現 MVP
**建立日期：** 2026-07-08
**原始資料 MD5：** `f5cf2e070bc8a2fb2ce0c584b3277c4c`
**參考文獻：** Zhu R., Dann E. et al. (2025) *Genome-scale perturb-seq in primary human CD4+ T cells maps context-specific regulators of T cell programs and human immune traits.* bioRxiv
**資料來源：** 公開 S3 桶 `genome-scale-tcell-perturb-seq`（匿名可讀），論文 supplementary tables

---

## 總覽

本 pipeline 把已算好的聚合 DE 統計重整成七個明確階段，每階段有獨立的輸入、輸出、腳本、資料字典與意義說明。全流程經 **R↔Python 雙語交叉驗證**（18 項關鍵統計逐項比對，全數容差內吻合）與 **Opus 兩輪複查**（第一輪 0 fail / 3 warn，修正後第二輪 FINAL PASS，零新問題）。

```
01_raw → 02_curated → 03_processed → 04_statistical → 05_visualization → 06_animation → 07_dashboard
（原始）  （清理）      （分析就緒）    （統計摘要）      （靜態圖表）       （動畫）        （整合展示）
```

> **邊界說明：** 目前 `04_statistical` 層是 repo 現有的**聚合統計**（每標的 n_DE + 單一效應量）。真正的 per-gene 全基因組 signed DE 矩陣需等 GB10 跑完任務 A（見 `TASK_A_RUNBOOK_GB10.md`）才有——屆時可無縫擴充此層，pipeline 結構不變。

---

## 七階段完整對照

### 01_raw — 原始資料層
- **輸入：** 無（pipeline 起點）
- **輸出：** `DE_stats.suppl_table.csv`（33,983 列 × 16 欄 = 11,526 標的 × 3 條件）、`sample_metadata.suppl_table.csv`（12 樣本）
- **腳本：** 無轉換（原始快照）
- **意義：** 論文 supplementary 的聚合 DE 統計，每列是一個「標的×條件」的擾動結果摘要。
- **文件：** `01_raw/README_01_raw.md`

### 02_curated — 清理層
- **輸入：** `01_raw/DE_stats.suppl_table.csv`
- **輸出：** `curated_targets.csv`（33,983 列，加衍生欄 `passes_gate`、`logDE`，布林欄標準化）
- **轉換：** 布林標準化；`logDE = log10(n_total_de_genes+1)`；`passes_gate = (n_cells_target≥200) & ontarget_significant & (~offtarget_flag) & (n_total_de_genes≥50)`
- **意義：** 清理後可直接分析；MVP 門檻定義在此層落地。
- **關鍵數字：** ontarget_significant=21,216；offtarget_flag=2,837；passes_gate=2,131 列
- **文件：** `02_curated/README_02_curated.md`

### 03_processed — 分析就緒層
- **輸入：** `02_curated/curated_targets.csv`
- **輸出：** `effect_matrix.csv`（11,526×4：index + 3 條件效應量）、`de_matrix.csv`（11,526×4：index + 3 條件 n_DE）、`gate_passing_targets.csv`（2,131 列通過門檻）
- **轉換：** 標的×條件 pivot；門檻子集篩選
- **意義：** 矩陣形式供降維/相關/排名；gate 子集是 1,235 個獨特候選標的。
- **文件：** `03_processed/README_03_processed.md`

### 04_statistical — 統計摘要層
- **輸入：** `02_curated` + `03_processed`
- **輸出：** `summary_statistics.csv`（18 項全域 metric）、`condition_stats.csv`（每條件 n_up/n_down/標的數）
- **意義：** 全域統計摘要，供文件與圖表引用門檻線/標註。
- **關鍵數字：** count Rest/Stim8hr/Stim48hr=11,287/11,415/11,281；nde 中位=2 max=5,920；效應 min=−58.5；corr(n_DE, n_downstream)≈1.00（揭露冗餘）；logDE<1 佔 75.6%；基因層 significant=7,913
- **外加證據（15 基因）：** `_evidence/*.json`（OpenTargets/ClinicalTrials/PubMed）、`_pathway/*.json`（Reactome/STRING）、gnomAD LOEUF/pLI
- **文件：** `04_statistical/README_04_statistical.md`

### 05_visualization — 靜態圖表層
- **輸入：** 02_curated（逐標的圖）、03_processed（矩陣圖）、04_statistical（標註/門檻線）
- **輸出：** 53 張 2D 圖表目錄；15 個標的 AlphaFold `.cif` 結構（10 broad-effect + 5 immune 候選，每標的 1 個）；3D 互動 HTML
- **意義：** 低認知負荷呈現資料重點；封面圖為 R1 target 排名 lollipop。
- **文件：** `05_visualization/README.md`（含每張圖的資料來源、標題、從欄位寫的意義解說）

### 06_animation — 動畫層
- **輸入：** 02_curated（逐標的動畫）、03_processed（condition 動畫）、04_statistical（門檻/標註）
- **輸出：** 10 個 SaaS 風格動畫（25fps、ease-in-out 緩動、元素漸入）
- **意義：** 動態展示篩選漏斗、排名、方向性、3D 空間聚集。
- **文件：** `06_animation/README.md`

### 07_dashboard — 整合展示層
- **輸入：** 消費全部上游層（curated/processed/statistical + evidence/pathway）
- **輸出：** Streamlit `target_card_dashboard.py` + FastAPI `target_card_api.py`
- **意義：** pipeline 最下游，整合 target 排名、readiness 分級(R0–R5)、證據匹配、機制圖、安全 overlay。
- **文件：** `07_dashboard/README.md`

---

## 驗證與複查

| 項目 | 結果 | 檔案 |
|---|---|---|
| R↔Python 交叉驗證 | 18 項關鍵統計全數容差內吻合（整數精確相等、浮點 <1e-6）| `_validation/cross_validation_report.md` |
| Opus 第一輪複查 | 0 fail / 3 warn（皆文件描述層）| `_validation/opus_review_round1.md` |
| Opus 第二輪確認 | 3 warn 全解、零新問題、FINAL PASS | `_validation/opus_review_round2.md` |

**第一輪 3 個 warn 及修正：**
1. 05 參考文獻標題誤植 → 改為真實標題（未硬補未經查證的 DOI）
2. 06 逐標的動畫來源誤標 04_statistical（該檔僅 18 列全域 metric）→ 改為 02_curated，與 05 一致
3. pivot 維度 11,526×3 → 更正為 11,526×4（1 index + 3 條件欄），實測驗證

---

## 資料字典與階段清單
- `_docs/data_dictionary.md` — 全部欄位字典（欄名/型別/來源/如何衍生）
- `_docs/stage_manifest.csv` — 每項資產的階段歸屬清單
