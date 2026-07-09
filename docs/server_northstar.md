# Server 終極目標(North-star)— data portal 化

**狀態:** 四個關鍵決策**已由使用者拍板(2026-07)** · 依確認的預設方向實作中 · **語言:** 繁體中文 · **日期:** 2026-07-08

**觸發需求(使用者 `/goal`):** 「優化這個 server,讓使用者好上手(UI friendly)、資料明確、且提供 API 讓其他人查資料。參考其他網站的 server 怎麼提供服務,我們也想做到相同。先制定終極目標,討論後再開始。」

**四個產品決策(使用者已拍板,全採推薦預設):**
1. **API 風格 = REST 做到一流**(不加 GraphQL)。→ OpenAPI 豐富化 + Swagger/ReDoc + 每筆回應帶 `X-API/Engine/Schema-Version` header。
2. **對外範圍 = 內部/受邀先行**(不做全公開)。→ 不建 auth/rate-limit 重工;維持 research-use-only、GWT dataset 授權未定的既有揭露。真正對外前再回來處理 license + auth。
3. **UI = 維持 Streamlit**(不改 React)。→ target dossier 頁 + onboarding intro。
4. **資料下載 = 要 bulk download**。→ `/api/exports/{id}` csv+json(json 帶 provenance)。

因四項皆採推薦預設,無需建 GraphQL / 公開級 auth / React;伺服器沿精簡路徑收斂。

---

## 1. 對標:其他 data portal 怎麼提供服務(實地看過)

| 平台 | UI | API | 關鍵做法 |
|---|---|---|---|
| **Open Targets Platform** | 實體中心 target/disease profile 頁,證據拆成模組化 widget,faceted 搜尋,互動視覺化 | **GraphQL** + 瀏覽器 playground,`/api` 文件 | 每個數字附來源;版本化 release;穩定 ID(Ensembl/EFO) |
| **Pharos**(NIH IDG) | target details 頁,靈活搜尋 + drill-down | **GraphQL** API + 文件 | 整合 100+ 資料源,可 query/filter/download |
| **cBioPortal** | 互動探索 UI | **REST + Swagger/OpenAPI**,可**自動生成任何語言的 client**,curl/Python/R 直接用 | UI 探索 ＋ API/flat-file 下載並存(重現性);client 套件(pyBioPortal / cBioPortalData) |

**共通模式(= 「做到相同」的清單):**
1. **實體中心頁**:一標的一頁,證據分模組區塊,每塊標來源+日期,可 drill-down。
2. **API 是一等公民**:GraphQL(欄位自選)或 REST + **Swagger/OpenAPI**(開箱互動 docs + client 自動生成)。
3. **資料明確 = provenance + 版本 + 穩定 ID + FAIR**。
4. **UI 探索 ＋ API/下載並存**。
5. **上手材料**:範例查詢、quickstart、client 套件。

*(API 通則:分頁/過濾、語意版本、rate-limit、auth(API key/OAuth);GraphQL playground 為標配。)*

---

## 2. 我們現在的落差(實測 repo,對照上面)

- FastAPI 只有 `title="GWT Target Card API", version="0.1.0"`——**無 OpenAPI tags/描述/範例/response model**,自帶 Swagger UI 陽春。→ **最大低垂果實**:豐富化 OpenAPI = 立刻專業互動 docs + client 自動生成,幾乎零重寫。
- ~30 endpoint / 11 router,但**無對外 API README / quickstart / 範例查詢 / client 片段**。
- **provenance / 版本 / `unknown≠0`** 資料裡有,但**沒有一致地放進每筆 API 回應**。
- 前端單檔 Streamlit dashboard——**無實體中心 target dossier 一頁式體驗**。
- 無 **auth / rate-limit / 對外部署 / 資料授權**故事(governance doc 已標 GWT dataset license 未定 → gate 對外公開)。
- 無 **bulk download / flat-file dump**(重現性)。

---

## 3. 終極目標(North-star)＋ 完成定義

> **把這個 server 從「內部能跑的分析工具」升級成一個外部研究者能自助上手的 CD4 T-cell 標的發現 data portal**,對標 Open Targets / Pharos / cBioPortal 的服務水準。

**支柱一 — UI friendly**：每標的一頁 target dossier(統計證據/穩健度/概念剖面/機制圖/安全窗/成藥性/外部證據/群體遺傳分區,每塊標來源+日期),faceted/typeahead 搜尋,互動視覺化,一致的可解釋徽章。
→ *完成 = 非開發者 30 秒內找到一個標的、看懂它為何 advance/watchlist。*

**支柱二 — 資料明確**：每筆輸出帶 provenance(source + fetched_at)+ data_version + `unknown≠0` 徽章 + 資料字典連結;穩定實體 ID;可下載。
→ *完成 = 任一數字都能一鍵溯源到來源與版本。*

**支柱三 — API 可查**：文件化公開 API(先把 REST 做一流:OpenAPI 加 tags/描述/範例/response schema → Swagger UI + ReDoc + client 自動生成),分頁/過濾/語意版本、穩定 ID、每筆回應帶 provenance,quickstart + 範例查詢 + client 片段。
→ *完成 = 外部開發者不用問我們,就能從 docs 頁跑出第一個查詢。*

**全程守既有紀律**:`unknown≠0`、descriptive-vs-decision 分離、never-fabricate、provenance 誠實。

---

## 4. 待拍板的四個關鍵決策(＋ 建議預設)

| 決策 | 選項 | **建議預設** | 理由 |
|---|---|---|---|
| **API 風格** | REST 一流 / 加 GraphQL / 兩者 | **REST 一流** | 零重寫、CP 最高(像 cBioPortal);GraphQL 留後續 |
| **UI 走向** | 強化 Streamlit / 正式 React / 先不動 | **強化 Streamlit** | 快、純 Python、不需前端工 |
| **對外範圍** | 內部/受邀 / 真正公開 | **內部/受邀先行** | 不需 auth/rate-limit 重工;GWT license 未定,公開前先釐清 |
| **資料下載** | bulk download / 不需要 | **要 bulk download** | 與 API 並存,利於重現(cBioPortal 模式) |

---

## 5. 分階段(依上面預設;對齊後才開工)

- **Phase 1 — OpenAPI 豐富化 + response provenance(最高 CP,決策無關、純上升)**:每 endpoint 加 tags/summary/description/範例 + Pydantic response model;把 `data_version`/`source`/`fetched_at`/`unknown≠0` 一致塞進回應;app 加 description/contact/license 區塊。→ 立刻得專業 Swagger UI + ReDoc,同時推進支柱二、三。**此步在四個決策的任何組合下都成立**,是安全的第一步。
- **Phase 2 — target dossier 頁**(支柱一):Streamlit 實體中心一頁式,證據分模組 + 來源徽章。
- **Phase 3 — 搜尋 + 資料明確徽章**:faceted/typeahead 搜尋;provenance/version/unknown 徽章元件。
- **Phase 4 — bulk download + API quickstart 文件**:flat-file dump 端點 + `docs/API.md`(範例查詢、curl/Python 片段)。
- **Phase 5(若選「真正公開」)**:auth/API key、rate-limit、資料授權條款、GWT license 釐清。

---

## 6. 風險 / 前置

- **GWT dataset 授權未定**(`docs/data_governance_checklist.md` §1):真正對外公開前必須釐清 license/DUA,否則不能對外散布原始表。這 gate 「對外範圍 = 真正公開」。
- UI 若選 React,需要前端技術棧 + 與後端 API 分離維護——工程量顯著大於強化 Streamlit。
