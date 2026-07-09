# UI 原型雙輪複查報告

**日期：** 2026-07-08 · **範圍：** Entry A Rank Board + Entry B Risk×Evidence 兩互動原型
**方法：** 每輪由獨立 subagent 對照 UI 規格逐項檢查規格符合度 + 資料正確性

## 第一輪：規格符合度 + 資料正確性
- **data_correct：** True
- **Entry A verdict：** minor
- **Entry B verdict：** accept
- **必修：** Entry A 排名指標下拉缺規格所列『可成藥性』選項（底層 15/85 標的有真實 Open Targets tractability 值）。
- **修正：** 下拉新增 `druggability_tractability` 選項，null 沉底。

## 第二輪：確認修正 + 最終驗收
- **fix_confirmed：** True · **no_regression：** True
- **entry_a_pass：** True · **entry_b_pass：** True
- **data_honest：** True（Entry A 85 列、Entry B 15 列全部逐欄對上底層 artifact，0 mismatch）
- **new_issues：** []

## 最終結論
兩原型 PASS，可作為 demo 交付。Entry A 第一輪必修已修正：#metric 下拉現含 6 個選項並包括『可成藥性 (druggability_tractability)』；排序 val(d)=v==null?-1:v 使 70 個 null 值沉底，且各指標真實最小值(druggability 2.0、其餘 ≥0.41)皆 >-1，無誤沉底。修正未破壞既有功能——context-specific 預設(state.metric=ctx_specific_de)、⚠泛效應 caveat、lollipop、模組 filter(TCR/SAGA/Mediator)、gate 與條件 toggle、抽屜(openDrawer)皆完好。資料誠實性通過:Entry A 85 列全部逐欄對上排名 artifact(0 mismatch)，Entry B 15 列全部對上風險 artifact(0 mismatch)，無捏造。(a) Entry A breadth caveat 誠實——實測 breadth 排名將 TADA2B(#1，ctx #69)、SENP5(#4，ctx #35)等 SAGA 泛效應基因推高，標題⚠與說明如實反映。(b) Entry B 責任邊界到位——常駐 disclaimer topbar、『驗證未完成 Demo 原型·前端模擬閘門流程，不含真實憑證核驗』、病人上傳明示為 session-only 模擬、全程反覆聲明『族群層假設，非病人層預測』與『不構成對特定病人的醫療建議』。無新問題引入。
