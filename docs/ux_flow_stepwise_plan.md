# UX 流程逐步分析與開發計劃 — 生醫研究員 / 臨床醫師視角

**目的**(`/goal`):使用者體感「順序不太順暢」。這份文件把工具的實際使用流程拆成離散的「步驟」,
針對每一步驟,分別從**生醫研究員**與**臨床醫師**兩種角色檢視,標出目前程式碼中的具體落差
(附檔案:行號),並給出可執行的開發計劃。延續 `docs/ux_trust_fix_plan.md` 的紀律:
`unknown != 0`、descriptive/decision 牆、never-fabricate、additive-only、frontend isolation、
先跑全套 pytest 再 commit。

**與前一輪的關係**:上一個 PR(#32)已經解決「Step 0」與「Step 1 起點」——dossier headline 與
Overview 導覽。這份文件涵蓋的是**下一層**:使用者離開 Overview 之後,實際在各 tab 之間、
以及從一張表格「走到」標的完整檔案的路徑上,還卡在哪裡。

---

## 使用者實際會走過的步驟(依現況程式碼還原)

```
Step 0  App 進入 / Overview                          [已修正 PR #32]
Step 1  依角色選 tab                                  [tab 順序已修正 FE-2;深連結仍不一致]
Step 2  在探索型 tab 中篩選 → 看到一張表                [4 個 tab 都有表,但深連結覆蓋不一致]
Step 3  從表格「走到」該標的的完整檔案                  [Target Explorer 是唯一的例外,見下]
Step 4  Target Dossier 內部段落順序                    [headline 已修正;②-⑦ 順序仍是實作順序]
Step 5  離開(匯出 / 下一步行動)                        [跨 persona 的既有缺口,已在 Wave 3 追蹤]
```

---

## Step 2+3 — 探索表格 → 標的檔案的深連結不一致(本輪最大發現)

### 現況(逐一核對)

| Tab | 表格 | 是否有「開啟標的檔案 →」深連結 | 證據 |
|---|---|---|---|
| 整合 Triage | `tri_df` | ✅ 有(`_selectable_table_with_dossier_link`) | `target_card_dashboard.py:1110` |
| 免疫優先 Immune Priority | `ip_df` | ✅ 有 | `target_card_dashboard.py:1049` |
| Disease Translator(主表) | `disease_df` | ❌ 純 `st.dataframe`,選了也走不到哪 | `target_card_dashboard.py:965` |
| Disease Translator(遺傳雙證據) | `ds_df` | ❌ 純 `st.dataframe` | `target_card_dashboard.py:999`(已確認 `genetic_double_support.py:169` 每列都有 `target` 欄位,技術上可直接接) |
| Pathway + Clinical(module hit table) | `module_df` | ❌ 純 `st.dataframe` | `target_card_dashboard.py:889`(`/api/modules` 每列也有 `target` 欄位,已於 dossier 頁 `③` 驗證過) |
| Target Explorer | 無獨立深連結——**改成整段複製了一個舊版、較弱的 mini-dossier** | ⚠️ 見 Step 3 | `target_card_dashboard.py:748-870` |

### 問題(兩種角色都受影響,但受傷方式不同)

- **臨床醫師**:Disease Translator 通常是他們的**第一入口**(先想到疾病,再找標的)。但目前選到一個
  有希望的標的後,表格是死路——沒辦法一鍵跳到那個標的的完整檔案(含安全性、外部證據、下一步驗證)。
  使用者必須手動記下 gene symbol,離開這個 tab,再去 Target Dossier 頁面重新搜尋一次——這正是
  「順序不順暢」最直接的體感來源。
- **研究者**:Pathway + Clinical 的 module hit table 也是同樣的死路;而 Target Explorer(研究者最愛用
  的篩選工具)雖然「有」單一標的細節,但那是一份**獨立維護、較舊、較不嚴謹**的版本(見 Step 3),
  跟真正的 Target Dossier 不一致,等於同一個工具裡有兩套「標的檔案」,互相不同步。

### 修正方案

**2a. Disease Translator 兩張表 + Pathway+Clinical 的 module hit table 改用既有的
`_selectable_table_with_dossier_link`**(而非純 `st.dataframe`)。這是把 Triage / Immune Priority
已經驗證過的同一個共用函式,套用到另外 3 張表——**不是新邏輯,是消除不一致**。

- 檔案:`target_card_dashboard.py`
  - `render_disease()`:965 行的 `st.dataframe(disease_df, ...)` → `_selectable_table_with_dossier_link(disease_df, "disease_table")`
  - `render_disease()`:999 行的 `st.dataframe(ds_df, ...)` → `_selectable_table_with_dossier_link(ds_df, "double_support_table")`
  - `render_pathway_clinical()`:889 行的 `st.dataframe(module_df, ...)` → `_selectable_table_with_dossier_link(module_df, "module_table")`(需先確認 `module_df` 非空且含 `target` 欄位,函式本身已對空/缺欄位有防呆——見 `_selectable_table_with_dossier_link` 191-213 行的實作,選不到列時只顯示提示文字,不會炸)

### 風險 / 工作量
低。三處都是同型別替換(`st.dataframe` → 既有共用函式),函式本身已被 Triage/Immune Priority
使用並測試過,不需要改動任何後端或 API。主要風險是「表格沒有 `target` 欄位」時函式行為——已讀過
`_selectable_table_with_dossier_link` 原始碼,目標欄位缺失時只是不顯示按鈕(見 208 行
`target = str(disp.iloc[rows[0]].get("target", ""))`,`.get` 防呆),不會拋例外。

### 驗收測試
新增 source-text 斷言測試(比照 `test_overview_tab_has_persona_wayfinding_note` 的模式,因為這三個
render_*() 函式跟主 dashboard 一樣需要 live API 才能完整跑 AppTest):斷言
`render_disease()` 與 `render_pathway_clinical()` 的原始碼中,兩處/一處 `st.dataframe(disease_df`
與 `st.dataframe(ds_df` / `st.dataframe(module_df` 已被替換為
`_selectable_table_with_dossier_link(...)` 呼叫,防止未來又被改回死路表格。

---

## Step 3 — Target Explorer 的重複 mini-dossier(獨立、較舊、較不嚴謹)

### 現況
`render_target_explorer()`(`target_card_dashboard.py:703-870`)在使用者從篩選結果選一個標的後,
inline 顯示了一份完整的「單一標的深入頁」:grade/cells/DE genes 等 metric、readiness call、
external evidence(trials/literature/genetics)、`st.graphviz_chart` 機制圖。這實質上是**另一份
Target Dossier**,但:

1. **`unknown != 0` 紀律沒有落實**:755-765 行直接用 `st.metric(..., "NA")`,不是 `ui_chips.val_chip`/
   `is_unknown` 的灰色虛線 chip;一個真正的「未檢查」欄位在這裡跟字面上的字串 "NA" 沒有視覺區分,
   跟 dossier 頁面的紀律不一致。
2. **沒有 glossary、沒有 quick-answer headline、沒有結構限制 banner**——PR #30/#32 剛加到 dossier
   頁的三項修正,在這裡完全沒有,使用者從這裡看到的 `readiness_call`(782 行)是「裸」的字串,
   沒有「這代表什麼/不代表什麼」的說明。
3. **兩套實作分別維護,長期一定會分岔**(例如這次 PR #32 只改了 `pages/2`,Target Explorer 這份
   inline 版本完全沒被觸及)。

### 問題
研究者是 Target Explorer 的主要使用者(篩選器最細),但他們反而拿到**版本較舊、較不嚴謹**的單一
標的視圖——跟研究者最需要嚴謹判讀的角色定位相反。

### 修正方案(兩個選項,建議 A)

- **選項 A(建議,風險低)**:保留 748-773 行「篩選結果表 + 選標的 + 5 個快速 metric」(這部分快、
  有用,留著讓研究者不用離開 tab 就能粗看),但**移除 774-856 行整段重複的 Readiness / External
  evidence / Evidence graph**,改成一個「在完整標的檔案查看 Readiness、外部證據、機制圖 →」的
  `_selectable_table_with_dossier_link`-風格深連結按鈕。淨效果:少維護 ~80 行重複邏輯,同時修掉
  第 1 點的 chip 紀律問題(因為那段違規程式碼直接被刪除,不是修飾)。
- **選項 B(風險較高,不建議這輪做)**:把 774-856 行的邏輯也套用 `ui_chips` 的 chip 元件補齊
  紀律,讓兩份「標的視圖」都合規——但這樣仍然維護兩份會分岔的程式碼,治標不治本。

### 風險 / 工作量
中低。刪除程式碼本身風險低,但需要確認 748-773 行留下的快速 metric 區塊在移除後面的區塊時
仍然自成一體(不依賴後面才計算的變數)——已讀過程式碼,`readiness_rows`/`snapshot`/
`_evidence_graph` 都是各自獨立的區塊內變數,刪除不影響前面。

### 驗收測試
新增 source-text 測試:斷言 `render_target_explorer()` 的原始碼中**不再包含**
`st.graphviz_chart(_evidence_graph` 這個呼叫(regression lock,防止重複的機制圖 inline 版本回歸),
且包含深連結到 dossier 的呼叫。

---

## Step 4 — Target Dossier 內部段落順序(②-⑦)

### 現況
Quick-answer headline(PR #32)已經解決「答案要不要捲到底才看得到」的問題。但下面 ②-⑦ 的**細節
段落順序**仍是實作順序,不是使用者的推理順序:

```
② GWT 統計證據(原始統計)         — 研究者要,臨床醫師通常先跳過
②b 多軸描述性摘要                — 兩者都要,quick triage
③ CD4 概念剖面                   — 研究者要
④ 機制圖                         — 研究者要
⑤ 安全性與遺傳學                  — 臨床醫師優先關心
⑥ 成藥性                         — 兩者都要,偏臨床/轉譯
⑦ 外部證據(trials/literature)   — 臨床醫師優先關心
⑧ Readiness 判定 + 下一步         — 已有 headline 提前預告
```

### 問題
臨床醫師若真的要查證 headline 的結論(而非只看 headline 就走),得先滑過 ②③④(純研究向的統計/
機制細節)才能看到他們真正關心的 ⑤⑦。有了 headline 之後這已經不是「找不到答案」的阻塞級問題,
但仍然是「找細節慢」的問題。

### 修正方案(分析後的建議,本輪先不動,列為下一個 PR 的候選)
建議重新排序為:`②b 多軸摘要 → ⑦ 外部證據 → ⑤ 安全性/遺傳學 → ⑥ 成藥性 → ② GWT 統計證據 →
③ 概念剖面 → ④ 機制圖 → ⑧ 完整判定明細`。理由:前四段是「證據要不要信、能不能治療」(兩種角色
都想快速掃過,臨床醫師到此可以停下),後四段是「這個結論是怎麼算出來的」(研究者的稽核區,細節
最重)。

### 風險 / 工作量
**中**——這是本文件中風險最高的一項,原因不是邏輯複雜,而是**這是目前唯一需要真的搬動既有程式碼
順序**(而非單純插入)的步驟。每個段落各自呼叫自己的 API 並各自防呆(讀過整份檔案確認彼此無跨段
變數依賴),所以搬動本身安全,但既有測試(`test_dossier_page_shows_quick_answer_headline_before_
the_evidence_walkthrough` 斷言 headline 在 ② 之前)需要跟著更新斷言的相對順序,且應該新增
「⑦ 在 ② 之前」之類的順序鎖,避免未來又被悄悄改回去。

### 驗收測試
- 更新/新增 source-order 斷言:`⑦ 外部證據` 出現在 `② GWT 篩選證據` 之前。
- 確認既有的每段獨立 not-available 空狀態测试仍然全綠(順序改變不應該影響任何段落各自的防呆)。

---

## Step 5 — 離開(匯出 / 下一步行動)

檢查過 `render_export()`(894-927 行):CSV/JSON/HTML/MD 四種報表下載,對研究者足夠。既有的
4-persona 探索已經記錄「沒有 per-target 存檔/引用/PDF」這個缺口(`docs/ux_trust_fix_plan.md`
Wave 3 backlog),**這是功能缺口,不是順序問題**,故不重複規劃,只在此處交叉引用,避免這輪計畫
範圍蔓延。

---

## 建議實作順序

| 順序 | 項目 | 風險 | 為什麼先做 |
|---|---|---|---|
| 1 | Step 2/3:3 張表補上 `_selectable_table_with_dossier_link` | 低 | 純替換既有函式,立即消除「死路表格」,兩種角色都受益 |
| 2 | Step 3:Target Explorer 移除重複 mini-dossier,改深連結 | 中低 | 修掉 chip 紀律違規 + 兩套實作分岔的根因 |
| 3 | Step 4:dossier ②-⑦ 重新排序 | 中 | 風險最高(搬動既有段落),且 headline 已經緩解掉多數急迫性,可以放最後驗證更久 |

---

## 每一項都遵守的限制
`unknown != 0`;descriptive/decision 牆(所有改動都是呈現層/深連結,不碰
`readiness_call`/`overall_readiness_stage`/`_stage()`);never-fabricate;additive-only(step 2)/
明確標示為刪除重複程式碼而非功能刪減(step 3);frontend isolation;每次 commit 前跑全套 pytest。
