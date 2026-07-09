# UI 互動原型 — 兩入口

依 `UI_SPEC_two_entries.md` P0 優先序建置的兩個**真實資料驅動**互動 HTML 原型。

## entry_a_rank_board.html — 研究者：Target Evidence Explorer
- **排名指標切換（6 選項）**：預設 `Context-specific 差異 (Stim−Rest)`；另有效應廣度、效應量 context、最大效應量、遺傳約束 LOEUF、可成藥性 tractability。
- **常駐 Caveat 橫幅**：說明效應廣度排名的泛效應污染。
- Lollipop 三條件排名、模組 filter（TCR/SAGA/Mediator）、gate/條件 toggle、標的證據抽屜。
- **資料**：85 個 gate-passing 標的，真實 GWT DE 統計 + gnomAD LOEUF（71/85）+ Open Targets tractability（15/85）。切換 context-specific↔breadth 會實質重排（TCR 基因 vs SAGA 泛效應基因）。

## entry_b_risk_evidence.html — 臨床醫師：Patient Risk & Evidence Lookup
- **醫療專業身分驗證閘門**（第一屏，未過不顯示資料）。
- **常駐 disclaimer** + 上傳 demo（純 session 不儲存）+ **風險×證據雙軸散點**。
- PLCG1（Angioedema safety liability）、MED12（LOEUF 0.096 極 loss-intolerant）警示標出。
- **資料**：15 shortlist 基因，真實 gnomAD 約束 + Open Targets safety/tractability + 文獻計數。

## 品質
兩輪獨立複查（規格符合度 + 資料正確性），data_honest=True，0 mismatch，both PASS。詳見 `UI_PROTOTYPES_REVIEW.md`。

## 已知限制
- LOEUF 覆蓋 71/85 嵌入標的（14 個 gnomAD 無約束記錄；全 1,235 標的富集為後續工作，gnomAD API rate-limit）。
- Entry B 病人上傳為 demo 模擬，身分閘門為前端流程示意，非真實憑證核驗。
- 原型為 demo MVP，非臨床決策工具。
