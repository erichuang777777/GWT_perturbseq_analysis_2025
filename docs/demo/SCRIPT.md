# CD4 Target Discovery Portal — 3-minute voice-over

This is the recording script. The “why it matters” notes are for preparation and are not spoken.

## 00:00–00:12 — Home

[Screenshot](screenshots/01-home.png)

**旁白：**「這是 CD4 Target Discovery Portal。同一套 Perturb-seq 證據提供研究者與臨床證據兩個入口，但不改變底層數據。」

**為什麼重要：**先建立 persona 與研究用途，避免誤讀成診療工具。

## 00:12–00:25 — Target Explorer

[Screenshot](screenshots/02-target-explorer.png)

**旁白：**「11,526 個量測基因中，7,249 個進入 Explorer。藍色 readiness 路徑得到 302 個 Advance；橘色 publication 路徑獨立得到 39 個已知 modality targets。」

**為什麼重要：**兩條漏斗是平行端點，不是 302 再縮成 39。

## 00:25–00:36 — PLCG1 dossier

[Screenshot](screenshots/03-target-dossier-plcg1.png)

**旁白：**「以 PLCG1 為例，dossier 展開分數組成、統計證據、readiness 理由與下一步驗證；call 不是黑箱排名。」

**為什麼重要：**每個決策都能被追問與稽核。

## 00:36–00:46 — Core-5 comparison

[Screenshot](screenshots/04-core5-compare.png)

**旁白：**「Core-5 可以並排比較。即使都在 TCR axis，readiness、robustness、安全性與族群 constraint 仍然不同。」

**為什麼重要：**揭露候選標的間的 trade-off，而非只看單一分數。

## 00:46–00:56 — Clinical scope

[Screenshot](screenshots/05-clinical-scope.png)

**旁白：**「Clinical evidence 先顯示使用邊界與風險分層：強 perturbation effect 不等於安全，也不等於臨床有效。」

**為什麼重要：**先說清楚 guardrails，才能正確解讀後續頁面。

## 00:56–01:08 — Clinical Core-5

[Screenshot](screenshots/06-clinical-core5.png)

**旁白：**「Core-5 是 15 個 primary-outcome genes 與 39 個已知 modality targets 的交集。矩陣集中呈現五個標的的每一層證據。」

**為什麼重要：**回答『為什麼是這五個』，而且能被重現。

## 01:08–01:18 — Concept profile

[Screenshot](screenshots/07-clinical-concept.png)

**旁白：**「M01 到 M20 依真實 seed-gene membership 組織免疫概念。它只做描述，不製造跨模組分數，也不影響 readiness。」

**為什麼重要：**保留生物學解釋力，但不把分類包裝成預測。

## 01:18–01:29 — Disease × drug evidence

[Screenshot](screenshots/08-clinical-disease-drug.png)

**旁白：**「疾病頁整合 Open Targets association、風險、臨床試驗與 readiness，用來安排研究 follow-up，不直接宣稱療效。」

**為什麼重要：**把疾病脈絡與風險放在同一個決策前畫面。

## 01:29–01:39 — Population genetics

[Screenshot](screenshots/09-clinical-popgen.png)

**旁白：**「Population genetics 以 LOEUF、pLI 與白話解釋補上真實人群的 loss-of-function constraint 視角。」

**為什麼重要：**為細胞擾動訊號增加人群安全線索。

## 01:39–01:52 — Expression comparison

[Screenshot](screenshots/10-clinical-expression-compare.png)

**旁白：**「去識別化 expression features 完全在瀏覽器內比對 reference，輸出 overlap、concepts 與 matched genes；它只產生假設，不推薦治療。」

**為什麼重要：**展示個體特徵如何安全連到群體層證據。

## 01:52–02:03 — Interactive figures

[Screenshot](screenshots/11-interactive-figures.png)

**旁白：**「互動圖可切換 culture condition 與 FDR threshold，檢查分析對脈絡和門檻的敏感性，而且不回寫決策。」

**為什麼重要：**互動用於檢查穩健性，不只是展示動畫。

## 02:03–02:14 — Figure & structure gallery

[Screenshot](screenshots/12-figure-gallery.png)

**旁白：**「Gallery 首先呈現 A7 外部驗證、A12 雙視角與 A16 整合分析，再依功能整理其餘圖表與 Core-5 structures。」

**為什麼重要：**把大量圖表組成可發表、可引用的科學敘事。

## 02:14–02:24 — Docs

[Screenshot](screenshots/13-docs.png)

**旁白：**「Docs 集中本機執行、Netlify 部署、資料版本、manuscript、supplementary EDA 與 known limitations。」

**為什麼重要：**讓專案可操作、可維護、可引用。

## 02:24–02:34 — REST API

[Screenshot](screenshots/14-api-docs.png)

**旁白：**「REST API 以版本化 static JSON 提供 targets、diseases 與 population-genetics records，沒有 silent recomputation。」

**為什麼重要：**讓 UI 與下游分析共用同一份證據。

## 02:34–02:46 — Overview

[Screenshot](screenshots/15-overview-deck.png)

**旁白：**「Overview 用四張 slide 濃縮 33,983 筆 DE rows、11,526 個 targets，以及從 target card 到 readiness engine 的決策鏈。」

**為什麼重要：**快速向主管、合作夥伴與 reviewer 交代規模與方法。

## 02:46–03:00 — Provenance and closing

[Screenshot](screenshots/16-provenance.png)

**旁白：**「最後，Provenance 公開版本、coverage、missingness 與完整 registry。我們不把 unknown 當成 zero，也不把 CRISPRi 當成藥效；每個結論都能被追溯與重現。」

**為什麼重要：**以科學可信度收尾，而不是只留下漂亮介面。
