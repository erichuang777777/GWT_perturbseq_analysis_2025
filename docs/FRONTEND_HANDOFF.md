# 前端交付清單 Frontend Handoff

> **一頁交給前端**:portal 需要的最佳文件與資產,每項附「是什麼 / 路徑 / 前端怎麼用 / 狀態」。這是 **curated 精選**(全量盤點見 `documentation_index.md`)。
>
> **鐵則**:前端**不自己編數字**——所有數字/揭露都來自下方檔案。無資料一律顯示 `unknown` + 覆蓋說明,**永不補 0**。

## 0. TL;DR

Portal 讀 `public/` 三個檔就能揭露一切:`real-dataset.json`(資料)、`disclosure.json`(版本/免責/原則/限制/attribution)、`provenance_registry.csv`(來源×演算法×參考)。**Provenance 與 Overview 兩個頁面已內建**(Header/Footer 有入口);其餘就是把這些檔渲染出來。

---

## 1. 資料與內容檔(portal 直接 `fetch` `public/`)

| 檔案 | 是什麼 | 前端怎麼用 | 狀態 |
|---|---|---|---|
| `public/real-dataset.json` | 標的(7,249)+ 概念模組(M01–M20);由 `scripts/export_real_data.py` 匯出 | 主資料源(`data/dataset.ts` 已載入) | ✅ 已接 |
| `public/disclosure.json` | 版本、覆蓋率、免責、5 原則、限制、12 attribution、概念層說明 | 渲染於 Provenance 頁 + Footer 版本 | ✅ 已接 |
| `public/provenance_registry.csv` | 79 列:資料來源 × 演算法 × 參考(固定 8 欄) | Provenance 頁三分頁表格 | ✅ 已接 |
| `public/flagship/*.png` | 首頁兩張職業卡的旗艦圖 | Home hero | ✅ 已接 |

> 欄位結構與「null=unknown」規則見 `docs/bulk_download_schema.md`。

---

## 2. 前端規格與對外文件(讀/連即可)

| 檔案 | 用途 |
|---|---|
| `docs/frontend_disclosure_spec.md` | **揭露規格**:哪些要揭露、放哪、來源檔、缺口 G1–G6 |
| `docs/bulk_download_schema.md` | 下載檔逐欄說明(`real-dataset.json`/`disclosure.json`/CSV) |
| `docs/data_use_terms.md` · `DATA_LICENSE.md` | 對外條款 / 授權 |

---

## 3. 事實來源(渲染時「數字/定義從哪來」)

| 檔案 | 提供什麼 |
|---|---|
| `docs/data_dictionary.md` | 每個欄位逐欄定義(卡片/就緒度/證據欄位) |
| `docs/technical_methods.md` | 方法、校準數字、限制、**§8 正式參考文獻** |
| `docs/server_modules.md` | 13 個 API router 的端點/輸入輸出(給 ApiDocs 頁 / 未來即時串接) |
| `docs/concept_dictionary.md` | 概念模組 M01–M20(seed genes、「永不餵決策」不變量) |
| `docs/figure_guide.md` | 圖表判讀(若要在站內展示更多圖) |
| `docs/provenance_registry.csv` | 來源×演算法×參考的機器可讀總表 |

---

## 4. Portal 內已建好的(**別重做**)

| 位置 | 內容 |
|---|---|
| `views/Provenance.tsx` | 揭露頁:渲染 `disclosure.json` + `provenance_registry.csv`(版本/覆蓋/登錄表/原則/限制/概念層/attribution)。Header + Footer 有入口 |
| `views/Deck.tsx` | Overview:4 頁專案簡報(總覽/方法/成果/資訊圖表)。Header + Footer 有入口 |
| `views/ApiDocs.tsx` | REST API 文件頁 |
| `views/Home.tsx` | 兩張職業卡 + 旗艦圖 |
| 各 view(Clinical/Dossier/Compare…) | 已落實 `unknown≠0`、每個數字附來源、research-use 免責、descriptive-vs-decision |
| Footer | `Data dictionary`(→ GitHub)· `Provenance` · `Overview` · `REST API` · `Bulk download`(→ `real-dataset.json`)——**死連結已全部接好** |

---

## 5. 前端 TODO(尚未做)

1. `scripts/export_real_data.py` 補 top-level `meta` 區塊(版本/覆蓋/`generatedAt`),讓 Footer/Provenance 改讀資料驅動而非 TS 常數(細節見 `frontend_disclosure_spec.md` §4 做法 B)。
2. `Data dictionary` 目前連 GitHub;如要站內渲染,可把 `data_dictionary.md` 轉成頁面。
3. `Bulk download` 目前給 `real-dataset.json`;可再加 `provenance_registry.csv` 下載 + schema 頁。

---

## 6. UI 鐵則(必守)

`unknown ≠ 0` · 每個數字附 `source`(+外部證據 `fetched_at`)· research-use 免責常駐 · 概念層/機制圖標「描述性,不進決策」· 使用者調權重不改 `readiness_call`.

---

## 7. 引用與授權

引用主資料(Zhu & Dann 2025,bioRxiv `10.64898/2025.12.23.696273`)+ 外部來源 attribution(見 `disclosure.json.attribution` 或 `data_use_terms.md`)。**研究用,非臨床建議。**

---

> 全量文件盤點見 `docs/documentation_index.md`;逐字權威以各 `docs/` 檔與程式為準。
