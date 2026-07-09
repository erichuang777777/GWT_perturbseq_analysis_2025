# 前端修正計畫(FE-1 ~ FE-4)

**範圍**:只動 `frontend/`,不碰後端 API / readiness / 資料。**紀律**:descriptive-only、`unknown != 0` 呈現、provenance/caveat 保留不變;前端維持隔離(只走 HTTP/JSON)。
**環境事實(已核)**:Streamlit **1.59.0** → `st.query_params` / `st.switch_page` / `st.dataframe(selection_mode, on_select)` / `streamlit.testing.v1.AppTest` 皆可用。目前**無任何 query_params 使用**。
**日期**:2026-07-09 · **語言**:繁中 · **拍板**:FE-2 = **含 tab 重排**(使用者已確認)。

**可測性策略**:把邏輯抽成純函式做 pytest unit test;頁面用 `AppTest` headless 冒煙(`pages/2` 有 sample fallback 可離線跑)。全 pytest 綠才 commit。

---

## FE-4 — 前端邏輯正確性審查(先做,地基)
**問題**:多波 append 累積的小瑕疵。
**修正**:
1. `tabs[5]` 重複(L888 + L1018)→ 由 FE-2 的 render 函式化根治(雙證據併入 disease tab render)。
2. `concept_modules` 攤平統一走 `format_concept_chips(v)` 純 helper(非 list/None/缺欄不炸)。
3. 每個新 section 的 `available:False` / 空 payload / 例外一致走 `st.info` + 原因。
4. cache TTL 一致(新 helper `ttl=60`)。
**測試**:`format_concept_chips` unit test;`ast.parse` 冒煙。

## FE-3 — 共用徽章元件(FE-1 地基)
**問題**:`pages/2` 有整套純 chip helper(`_is_unknown`/`_val_chip`/`_flag_chip`/`_labeled`/`_provenance`/`_descriptive_note`/`_not_available`,L69-153),主 dashboard 卻用原始 `st.dataframe` dump。
**方法**:
1. 抽到新檔 `frontend/dashboard/ui_chips.py`(公開:`is_unknown`/`val_chip`/`flag_chip`/`labeled`/`provenance_line`/`descriptive_note`/`not_available`/`format_concept_chips`)。
2. `pages/2` 改 import(**行為逐字不變** — 硬約束,用 AppTest 鎖)。
3. 主 dashboard 新表格套 chip:`readiness_call` badge、`robustness_tier`(high/unresolved/low 三色)、安全窗、concept chips、統一「descriptive · unknown≠0」小標。
**測試**:`tests/test_ui_chips.py` 純函式(`is_unknown(None/'unknown'/0)`、`val_chip` unknown→「未檢查」、`format_concept_chips`);`pages/2` AppTest 冒煙。

## FE-1 — 清單→標的深鑽 deep-link(最高 UX)
**問題**:triage/immune/候選表是死表格,點 target 無法跳到已存在的 dossier 頁(`pages/2`,833 行),北極星 list→detail 斷了。
**方法**(Streamlit 1.59 原生):
1. 主 dashboard 表格改 `st.dataframe(..., selection_mode="single-row", on_select="rerun")`;偵測選取列 → 「**開啟標的檔案 →**」按鈕 → `st.query_params.update({"dataset_id":…,"target":…})` + `st.switch_page("pages/2_標的檔案_target_dossier.py")`。防無限 rerun:只在有選取且按鈕觸發時導頁。
2. `pages/2` 頂端加純函式 `resolve_initial_selection(query_params, session_state) -> (dataset_id|None, target|None)`:query param 有 target/dataset_id 時 seed `session_state["dossier_query"]`/`["dossier_dataset"]`,**僅在 session 尚未設**(不蓋使用者導覽)。
3. 套用:整合 Triage 表、免疫優先表、Overview Top candidates / Watchlist。
**測試**:`tests/test_dossier_nav.py` 對 `resolve_initial_selection` 純函式(有 param→回該 target;無→None;session 已設→不覆蓋);`pages/2` AppTest 帶 query param 冒煙。

## FE-2 — IA 重整 + tab 重排(含,使用者拍板)
**問題**:新描述性視圖散在 tab5/6/7;統一的整合 Triage 埋在第 7 tab;`tabs[5]` 分裂。
**方法**:把每個 tab body 抽成 `render_*()` 函式,再依新順序建 tabs 並呼叫。
- **現況 body 行界**:Overview 562-661、Target Explorer 662-830、Pathway+Clinical 831-849、Imports 850-852、Export 853-887、Disease Translator 888-929、Immune Priority 930-1017、雙證據(tabs[5]又)1018-1052、Triage 1053-1114。
- **抽成**:`render_overview`, `render_target_explorer`, `render_pathway_clinical`, `render_imports_tab`, `render_export`, `render_disease`(**併入雙證據**), `render_immune_priority`, `render_triage`;皆收 `dataset_id, summary, summary_payload` 等所需狀態為參數(避免依賴 module 全域順序)。
- **新 tab 順序(整合 Triage 為前門)**:`Overview → 整合 Triage → 免疫優先 → 疾病/雙證據 → Target Explorer → Pathway + Clinical → Imports → Export`。
- 根治 `tabs[5]` 重複(雙證據入 `render_disease`)。
**測試**:`pages`/主 app AppTest 冒煙(tab 數=8、標題順序、無例外)。**風險最高** → 抽函式時逐段搬移、每搬一段 `ast.parse` + AppTest。

---

## 相依與順序
**FE-4 → FE-3 → FE-1 → FE-2**。理由:FE-4 清地基;FE-3 給 FE-1 落地頁一致外觀且產出可測純函式;FE-1 最高 UX;FE-2 最後做大重構(前面穩了才動 tab 結構)。

## 打包
一個 draft PR、四組 commit(FE-4 / FE-3 / FE-1 / FE-2)。前端測試新增於 `tests/`。全 pytest 綠才 commit。

## 自我審核(對真實碼已核,VERDICT: SOUND)
- Streamlit 1.59 API 齊備 ✓;無現存 query_params ✓;chip helper 為純函式可安全抽取 ✓;`pages/2` 有 sample fallback 可離線 AppTest ✓;tab body 行界已確認 ✓。
- **風險**:(a) `st.dataframe(on_select="rerun")` 需正確處理 selection state 免無限 rerun → 只在按鈕觸發導頁;(b) 抽 chip 後 `pages/2` 行為需不變 → AppTest 鎖;(c) tab 重排跨全檔 → 逐段搬 + 每段驗;(d) AppTest 對需 API 的主 tab 可能因無 API 而降級 → 冒煙只斷言「不拋例外 / tab 標題在」,資料區塊允許 st.info。
