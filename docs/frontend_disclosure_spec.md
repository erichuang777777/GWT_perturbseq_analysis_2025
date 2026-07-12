# 前端揭露規格 Frontend Disclosure Spec(交付前端)

> **目的**:把「資料來源 / 演算法 / 參考文獻 / 版本 / 限制 / 免責」等說明,正確、清楚地在前端 portal 揭露。本頁是交給前端的**單一規格**:①現況(已做好、別重做)②缺口 ③每項該揭露什麼、放哪、來源檔 ④靜態匯出模型怎麼供給內容 ⑤UI 規則 ⑥還需準備的其他文件。
>
> **前端現況**:React + Vite portal(`frontend/webserver/`),讀預先匯出的 `public/real-dataset.json`(由 `scripts/export_real_data.py` 產生);views:`Home / Explorer / Dossier / Compare / Clinical / Figures / ApiDocs`。**只有 `/upload` 打即時 API**,其餘為靜態瀏覽。
> **內容單一真相來源**:`docs/provenance_registry.csv`(資料來源×演算法×參考,79 列)、`docs/technical_methods.md`、`docs/data_dictionary.md`、`docs/concept_dictionary.md`。前端應**渲染這些**,不要另寫一套數字。

---

## 1. 現況:已揭露良好,請勿重做

前端已正確落實揭露**原則**(維持即可):

- **`unknown ≠ 0`**:各 view 無資料時顯示 `unknown` + 覆蓋說明,絕不補 0(`Dossier`/`Clinical`/`Compare` 已實作)。
- **每個數字附來源**:如 gnomAD `src: sources/target_tool_cache/_overlays/…`、Open Targets/CT/PubMed 標註(`Clinical.tsx`)。
- **研究用免責**:`Home`「Research use only — not clinical software」、`Clinical`「Evidence lookup — not a clinical decision tool」。
- **descriptive-vs-decision 分離**:Footer 標語;`Dossier` 明載「readiness call 由規則引擎計算,不隨權重改變」。
- **版本戳記**:Footer/Header 顯示 `DATA_VERSION`(hover 顯示 `SOURCE_VERSION`)。
- **Ensembl 主鍵、概念模組未指派時顯示 unknown**、**ApiDocs view** 已存在。

---

## 2. 缺口(需補)

| # | 缺口 | 位置 |
|---|---|---|
| G1 | **Footer 三個死連結**:`Data dictionary` / `Provenance` / `Bulk download` 都是 `href="#"` | `components/Footer.tsx` |
| G2 | **沒有整合的 Methods & Provenance 頁**:方法/資料來源/演算法/參考/版本目前散在 tooltip,無單一揭露頁 | 缺 view |
| G3 | **匯出無 top-level `meta` 區塊**:engine/dataset/schema/kd 版本、`generated_at`、覆蓋率、免責語目前寫死在 TS,非由 `export_real_data.py` 匯出 | `scripts/export_real_data.py` |
| G4 | **外部資料 attribution / 授權未揭露**:Open Targets / ChEMBL / gnomAD / GTEx / Reactome / STRING / ClinicalTrials / PubMed 的引用與授權 | 缺 |
| G5 | **限制 / descope 未揭露**:上傳路徑技術債、情境專一 heuristic、SCEPTRE/Mixscape 替代、細胞層級未跑真實資料 | 缺 |
| G6 | **證據覆蓋誠實聲明**:深層外部證據僅 21 個基因有(其餘留空非 0),應有全域說明而非只逐欄 | 缺全域 banner |

---

## 3. 該揭露什麼、放哪、來源檔

| 揭露項目 | 建議 UI 位置 | 來源檔(前端渲染此) | 現況 |
|---|---|---|---|
| 研究用免責(全域) | 常駐 Footer + Home/Clinical 橫幅 | 本頁 §7 免責文字 | ✅ 已有 |
| **資料來源清單** | Provenance 頁表格 | `provenance_registry.csv`(`category=data_source`,31 列) | ❌ G1/G2 |
| **演算法/方法清單** | Provenance/Methods 頁 | `provenance_registry.csv`(`category=algorithm`,20 列)+ `technical_methods.md` §3 | ❌ |
| **參考文獻** | References 頁 / Dossier 引用 | `provenance_registry.csv`(`category=reference`,28 列)+ `data/reference.ts` | 部分(reference.ts 有資料) |
| **版本 metadata** | Footer + Provenance 頁 | 匯出的 `meta`(見 §4) | 部分(僅 DATA_VERSION) |
| **外部資料 attribution/授權** | Provenance 頁「Attribution」段 | 本頁 §6 | ❌ G4 |
| **證據覆蓋率** | 全域 banner + Explorer 說明 | 匯出的 `meta.coverage` | ❌ G6 |
| **限制/descope** | Methods 頁「Limitations」段 | `technical_methods.md` §5 / 本頁 §5 摘要 | ❌ G5 |
| **概念層 M01–M20 說明** | Concept/Clinical 頁 | `concept_dictionary.md` / `data/moduleMeta.ts` | ✅ 已有 meta;需標「永不餵決策」 |
| **欄位定義(Data dictionary)** | Footer 連結目標 | `data_dictionary.md` | ❌ G1(死連結) |
| **REST API 文件** | ApiDocs view | 現有 | ✅ |

---

## 4. 靜態匯出模型下怎麼供給內容(給前端的具體做法)

**做法 A(建議,最省事):把 `docs/provenance_registry.csv` 複製進 `public/`,前端把它渲染成 Provenance 頁的表格。** 三個 `category` 直接對應三個分頁(資料來源 / 演算法 / 參考)。CSV 是機器可讀、固定 8 欄(`category,component,type,identifier,version,source_url_or_id,produced_by,notes`),`source_url_or_id` 內的 URL/PMID 可自動 linkify。

**做法 B:在 `export_real_data.py` 增一個 top-level `meta` 區塊**(補 G3),讓版本/覆蓋/免責由資料驅動而非寫死:

```jsonc
"meta": {
  "engine_version": "1.3.0",
  "dataset_version": "gwt_marson2025/bioRxiv-10.64898-2025.12.23.696273v1",
  "card_schema_version": "card_schema/v2",
  "kd_threshold_version": "kd_status/v2",
  "data_version": "<per-build MD5>",
  "generated_at": "<ISO8601,由 args 傳入,勿用 Date.now()>",
  "n_targets": 11526,
  "n_rows": 33983,
  "coverage": { "deep_external_evidence_genes": 21, "gnomad_constraint_genes": 16 },
  "disclaimer": "Research use only — not clinical software.",
  "provenance_csv": "provenance_registry.csv"
}
```

> 前端把 `meta.*` 綁到 Footer/Provenance 頁,`DATA_VERSION`/`SOURCE_VERSION` 改讀 `meta` 而非 TS 常數,即可補 G3。

**填死連結(補 G1)**:`Footer.tsx` 的 `Data dictionary` → Data dictionary 頁(渲染 `data_dictionary.md`);`Provenance` → 新 Provenance/Methods 頁;`Bulk download` → 直接下載 `real-dataset.json` +(可選)`provenance_registry.csv`,附 schema 說明。

---

## 5. Limitations / descope(揭露文字,可直接用)

> 摘自 `technical_methods.md` §5,前端可原文呈現:
- 上傳路徑已知技術債:`kd_status` 對純上傳資料、`n_total_de_genes` 對應遺失(Tech-Debt A.1/A.2)。
- 情境專一性(`condition_specificity_score`)為 **heuristic,非統計交互作用檢定**。
- signed module scoring 放棄(DE 無 per-gene 方向);SCEPTRE 用外部 hook、Mixscape 用 scikit-learn 替代(刻意)。
- 細胞層級真實資料未跑(~1.7 TiB);僅對合成 fixture 驗證。
- 深層外部證據僅 21 個基因有;其餘留空(非 0)。
- 平台無存取控制,`usr_` 命名僅防意外混料,非授權隔離。

---

## 6. 外部資料 attribution / 授權(公開前須揭露)

前端揭露外部資料時應附引用與授權(**上線前請再確認各來源當前條款**):

| 來源 | 引用 | 授權(需查證) |
|---|---|---|
| Open Targets Platform | Ochoa et al. 2024, NAR (PMID 39657122) | 依 Open Targets 引用政策 |
| ChEMBL | PMID 37933841 | CC BY-SA 3.0 |
| gnomAD v4 | Karczewski et al. 2020 (PMID 32461654) | 免費使用,須引用 |
| GTEx | GTEx Consortium 2020 (PMID 32913098) | 依 GTEx 條款 |
| Reactome | PMID 34788843 | CC BY 4.0 |
| STRING v12 | PMID 36370105 | CC BY 4.0 |
| AlphaFold DB | Jumper 2021 (PMID 34265844) | CC BY 4.0 |
| ClinicalTrials.gov | NLM | 公眾領域(建議標註來源) |
| PubMed / PMC | NLM | 依 NLM 條款 |
| CELLxGENE Census | CZI (PMID 39607691) | 依 CZI 條款 |
| 主資料 GWT Perturb-seq | Zhu & Dann et al. 2025 (bioRxiv 10.64898/2025.12.23.696273) | 依論文/VCP 條款 |

---

## 7. 全域 UI 規則(必守;多數已實作)

1. **`unknown ≠ 0`**:任何無資料欄位顯示 `unknown` + 覆蓋說明,永不補 0/預設值。
2. **每個數字附來源**:數字旁或 tooltip 標其 `source` 與 `fetched_at`(外部證據)。
3. **研究用免責常駐**:全域 Footer + 進入 Clinical/Dossier 顯著位置;文案:「**Research use only — not clinical software.** 本工具輸出為研究用標靶優先排序,不診斷、不建議治療、不得用於病人管理。」
4. **descriptive-vs-decision 分離**:概念層(M01–M20)、機制圖、safety overlay 標明「**描述性,不進就緒度決策**」。
5. **權重可調不改證據**:使用者調 sub-score 權重只重排視圖,`readiness_call` 由規則引擎決定、不隨權重變。
6. **版本可見**:每個資料集/頁面顯示 `dataset_version` + `data_version` + `generated_at`。

---

## 8. 還需要準備的其他文件(答「還需要準備什麼」)

| 文件 | 用途 | 現況 / 我可代做 |
|---|---|---|
| **`public/provenance_registry.csv`** | Provenance 頁資料源(做法 A) | 複製 `docs/` 版即可;我可加匯出步驟 |
| **`public/disclosure.json`(或匯出 `meta` 區塊)** | 版本/覆蓋/免責/attribution 資料驅動(補 G3) | **我可代生成內容** |
| **Provenance / Methods / About view** | 填 Footer 死連結、整合揭露(補 G1/G2) | 前端實作;內容由本頁 §3–§6 供給 |
| **對外 Data-use / Terms 頁** | 授權與使用條款(補 G4) | 需你確認條款;我可起草 |
| **對外 LICENSE / 資料授權聲明** | portal 對外授權 | 依 repo `LICENSE` + 外部來源條款 |
| **Data dictionary 對外頁** | Footer 死連結目標 | 渲染 `docs/data_dictionary.md` |
| **Bulk download + schema 說明** | 下載 `real-dataset.json` 的欄位說明 | 我可寫 schema 文件 |
| **隱私/無個資聲明** | 揭露捐贈者去識別化 | `technical_methods.md` §2.4 已有,前端引用即可 |
| **CHANGELOG / 版本頁** | 版本沿革 | 可由 commit + versions.py 生成 |

---

> 一句話總結交給前端:**把 `docs/provenance_registry.csv` + `technical_methods.md` + `data_dictionary.md` 渲染成一個 Provenance/Methods 頁,填掉 Footer 三個死連結,並在 `export_real_data.py` 補一個 `meta` 版本/覆蓋區塊。** 揭露原則你們已做得很好,缺的是「集中揭露頁 + 版本/授權資料驅動」。
