# CD4 Target Discovery Portal — 4K demo script

## Recording specification

- Duration: exactly 3 minutes
- Resolution: native 4K UHD, 3840 × 2160
- Format: 16:9 browser walkthrough
- Narration: Traditional Chinese, recorded separately with the presenter’s own voice
- Subtitles: English sidecar subtitles
- Scientific boundary: research-use target prioritisation, not a clinical recommendation

## 敘事邏輯（給對稿與剪輯使用，不朗讀）

這支影片走一條單一論證鏈，不是功能羅列：

1. **問題（00:00–00:20）** — CD4⁺ T 細胞很重要，但篩選資料多不代表能找到藥。我們解決「證據整合耗時又零散」的問題。
2. **方法與核心發現（00:20–00:47）** — 兩條獨立漏斗交集出 5 個核心標靶；這是全片唯一要記住的數字。互動不改變證據，只改變檢視角度，是給評審看的誠實性訊號。
3. **證據深度（00:47–01:16）** — 從單一標靶到五個並排比較，展示每個結論都可以拆解到最底層數據。
4. **雙視角張力（01:16–01:40）** — 這是整個平台的新穎點：研究員最想要的標靶，常是臨床醫師最該警覺的。效應強 ≠ 安全 ≠ 有效。
5. **可重現性（01:40–02:43）** — 外部資料庫重現我們的數字，不是自說自話；管線公開、API 可重用。對 AI 產業評審的訊號是：這是工程化的科學工具，不是一次性 demo。
6. **收尾（02:43–03:00）** — Provenance／出處頁作結，呼應開場的「證據整合」承諾：每個結論都能追溯回源頭。

## 逐場旁白與字幕

### 00:00–00:10 · Home

**中文旁白：** CD4+ T 細胞驅動免疫反應，但一份篩選資料找不出能下藥的標靶。

**English subtitle:** CD4+ T cells drive immune regulation — but a screen alone can't tell you what's druggable.

### 00:10–00:20 · Home → Researcher

**中文旁白：** 我們整合 GWT 篩選資料與外部公開資料庫，建立一套可驗證的方法。

**English subtitle:** We joined the GWT screen with external public databases into one verifiable method.

### 00:20–00:32 · Target Explorer

**中文旁白：** 兩條獨立漏斗——安全評估與藥物可交付性——交集出五個核心標靶。

**English subtitle:** Two independent funnels — readiness and drug-deliverability — intersect on five core targets.

### 00:32–00:47 · Target Explorer interaction

**中文旁白：** 調整權重、重置、搜尋 PLCG1：排序即時反應權重變化，證據本身從不改變。

**English subtitle:** Adjust a weight, reset it, search PLCG1 — the ranking reacts live; the evidence never does.

### 00:47–01:03 · PLCG1 Dossier

**中文旁白：** 每個標靶都有專屬檔案：效應大小、下游廣度、跨供者穩健性，每一層證據都可回溯查核。

**English subtitle:** Every target has its own dossier — effect size, downstream breadth, cross-donor robustness, all inspectable.

### 01:03–01:16 · Core-5 Compare

**中文旁白：** 五個核心標靶並排比較，各自的證據強弱與臨床風險取捨一目了然。

**English subtitle:** Side by side, the five core targets show distinct evidence strength and risk trade-offs.

### 01:16–01:40 · Clinical Evidence

**中文旁白：** 切到臨床醫師視角：免疫概念模組、疾病關聯、藥物、族群遺傳學、病人表現比對——效應強不等於安全，也不等於臨床療效。

**English subtitle:** Switch to the clinician's view: concept, disease, drug, population genetics, expression — strong effect is neither safety nor clinical efficacy.

### 01:40–01:55 · Interactive Figures

**中文旁白：** 切換條件或閾值，圖表即時反應，確認每個結論都對情境敏感、經得起檢驗。

**English subtitle:** Change a condition or threshold — the figure updates live, proving context-sensitivity.

### 01:55–02:05 · Gallery — A7

**中文旁白：** Open Targets 55 個標靶核對成功，STRING 召回率吻合，HIV 篩選也對上了。

**English subtitle:** Open Targets re-verifies all 55, STRING recovers known partners, an HIV screen lines up too.

### 02:05–02:15 · Gallery — A12

**中文旁白：** 研究價值最高的標靶，往往正是臨床上最需警覺的。

**English subtitle:** The targets most valuable to researchers are often the ones clinicians must watch most closely.

### 02:15–02:25 · Gallery — A16

**中文旁白：** 從兩千兩百萬顆細胞到 7,249 個標靶，整個策展與分析管線在此呈現。

**English subtitle:** From 22M cells to 7,249 targets — the full curation and analysis pipeline, laid out.

### 02:25–02:43 · Gallery / Docs / API

**中文旁白：** 圖庫可供發表引用，文件說明操作方式，API 讓其他研究團隊直接重用我們累積的證據。

**English subtitle:** The gallery is publication-ready, the docs explain operation, and the API lets other teams reuse our evidence directly.

### 02:43–03:00 · Provenance

**中文旁白：** 最後回到出處頁：版本紀錄、資料涵蓋率、每一個結論背後的來源，全部可以逐一追溯。

**English subtitle:** We close on provenance — versions, coverage, and the source behind every conclusion, all traceable.

## 畫面操作原則

- 影片為單一論證鏈，不在畫面上逐一介紹所有功能。
- Weights 只改變 ranking，不改變 evidence call。
- Clinical Evidence 用快切連結雙視角，不在單頁停留過久。
- A7、A12、A16 使用大圖 modal，各保留 10 秒說明時間。
- 影片以 Provenance 收尾，最後兩秒停住不再操作。

## 配音前數字複核

- A7 圖上顯示 `52 / 55 targets present in the genome-wide CD4 screen library`；正式配音前應確認「all 55」的表述是否要改成 coverage 更精確的說法。
- A16 圖上呈現 `33,983 raw profiles → 1,235 unique targets`；`22M cells → 7,249 targets` 是較廣的平台資料脈絡，不是 A16 圖上直接畫出的 funnel。
