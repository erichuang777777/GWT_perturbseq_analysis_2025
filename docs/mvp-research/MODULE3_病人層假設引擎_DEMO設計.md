# 模組三 Demo 設計：群體亞群假設引擎
### 定位：MVP 展示用，資料源＝公開去識別化群體統計（非真實病人）

**觸發需求：** 「協助病人製作預測模型或個人化醫療建議」的 demo 版本。
**資料源決定（使用者確認）：** 公開去識別化資料。
**核心邊界：** 這是「群體亞群統計假設」，不是「病人個體預測」。兩者的差異必須在介面上不可忽略地標示。

---

## 1. 為什麼是這個設計，不是別的

「病人層預測/個人化建議」若真的做，需要：病人個體的基因體資料、獨立臨床驗證、可能的 IRB — 這些都不在 MVP 展示範疇內（前次討論已定案：CRISPRi 敲低 ≠ 藥理干預，本工具不做臨床決策）。

但 repo 裡已經有**貨真價實、去識別化、群體層級**的人類遺傳資料可以立即使用：
- `src/8_lymphocyte_counts_LoF/input/Backman_LymphocyteCount_fullFeatures.per_gene_estimates.tsv` — UK Biobank exome-wide 罕見 LoF 變異負荷效應（18,543 基因,post_mean + 95% CI）
- `src/7_1k1k_analysis/` — OneK1K 人群 scRNA 資料（Yazar 2022,CD4 T 細胞）
- 疾病轉譯器已有的 Open Targets 遺傳關聯（7,528 列、13 適應症）

**設計原則：** 用「帶有此基因功能喪失變異的**人群**,某個臨床性狀平均會怎麼變」取代「這位**病人**該怎麼治療」。前者是可辯護的群體遺傳學陳述,後者需要臨床驗證。

---

## 2. 已驗證的原型（本地實跑,真實資料,非模擬）

把系統一候選標的清單 join 上 Backman 淋巴球計數負荷效應,產出「群體假設卡」:

| gene | post_mean | 95% CI | 假設陳述 |
|---|---|---|---|
| PLCG1 | +0.295 | [0.187, 0.407] | LoF 負荷攜帶者淋巴球計數顯著較高（CI 不含 0） |
| VAV1 | +0.070 | [0.011, 0.158] | 同上,效應較小但顯著 |
| SENP5 | +0.094 | [0.031, 0.176] | 顯著,但 SENP5 已被 C7 標為 broad_effect |
| TADA1 / PMVK | +0.049 | CI 邊緣不含 0 | 弱顯著 |
| 其餘 10 個標的 | — | CI 含 0 | 無法與零區分 — 誠實回報,不假裝有訊號 |

**這個結果本身有意義**：PLCG1（TCR 訊號傳遞關鍵分子）帶有 LoF 變異的人群,淋巴球計數確實有真實遺傳學上可測得的偏移 — 這是與 CD4 T 細胞篩選結果方向一致的獨立證據,不是巧合湊出來的demo數字。

見 `module3_population_hypothesis_demo.csv`。

---

## 3. Demo 模組的功能規格

### 3.1 一句話定義
> 輸入一個標的（或標的清單）,輸出「若某人群帶有此基因的功能喪失變異,已知哪些去識別化群體性狀會顯著偏移」— 一個**群體遺傳學假設**,附信賴區間與資料來源,而非病人層預測。

### 3.2 資料流
```
target_cards.csv (標的 × 條件)
        │
        ├─ join Backman burden estimates (Ensembl ID)  → 群體性狀偏移假設
        ├─ join Open Targets genetic_association score → 疾病關聯強度
        └─ join 1k1k CD4 表現分佈（選配,較重）        → 群體內表現變異範圍
        │
        ▼
population_hypothesis_card：
  { gene, trait, population_effect_estimate, ci_95,
    ci_excludes_zero, direction, disease_area,
    caveat: "population-level statistical association,
             not a patient-level prediction or treatment
             recommendation" }
```

### 3.3 介面護欄（必須,不是建議）
1. **每張卡片標頭固定顯示**：「群體統計假設 — 非病人預測」（呼應現有 CRISPRi≠藥理學 護欄的同一機制)。
2. **`ci_excludes_zero=False` 一律顯示「無法區分零效應」**,不做视觉上的模糊淡化。
3. **不接受任何個體層輸入**（沒有「輸入病人資料」的欄位）— 只能選標的,不能選「病人」。
4. **與 readiness engine 的既有欄位共用**：`human_genetic_support` 已經是 Open Targets 遺傳分數,這個新模組是同一個精神的延伸,用另一個真實資料源(Backman burden)補一個獨立驗證角度。

### 3.4 最小實作(MVP demo 範圍)
- 新檔案：`src/3_DE_analysis/population_hypothesis.py`
  - `load_burden_estimates(trait="lymphocyte_count") -> DataFrame`（讀 `8_lymphocyte_counts_LoF/input/*.tsv`,cache-first,沿用 `cre_schema.py` 的 honest-fallback 模式）
  - `build_population_hypothesis_card(target_cards_df, burden_df) -> DataFrame`（join + 信賴區間判讀,如上）
- API：`GET /api/population-hypothesis/{gene}` — 唯讀,回傳快取的 join 結果
- Dashboard：新 tab「群體假設(demo)」,標頭護欄文字寫死,不可由使用者關閉

---

## 4. 明確不做的事（避免 scope creep 回到紅線內）

- 不接受病人個體資料上傳到這個模組（那是模組二的範疇,且模組二本身也不做臨床決策）。
- 不輸出「建議劑量」「建議藥物」「治療路徑」— 只輸出「群體性狀統計偏移 + 信賴區間」。
- 不做病人分層 / 分群預測模型（regression on individual outcomes）— 只做 gene-level 群體統計查表。
- OneK1K/1k1k 的個體層 scRNA(若真的要用)僅用於**群體內表現變異範圍**展示,不做個體對應。

---

## 5. 交付物
- `MODULE3_病人層假設引擎_DEMO設計.md`（本文件）
- `module3_population_hypothesis_demo.csv` — 15 個候選標的的實測群體假設卡(真實 UK Biobank 統計)

---

## 6. 補充：疾病 × 已知藥物標的證據匹配（回應「病人已確診+已有藥物,如何協助治療決策」）

**觸發問題：** 當病人已確定疾病、且該疾病已有對應藥物時,能否預測療效或輔助治療決策？

**方法學定位（先講清楚）：** 真正的個體療效預測需要病人層縱向治療結果資料或功能性藥物敏感性檢測,這是目前資料資產拿不到、也不該用合成資料假裝有的部分。本工具能誠實支撐的是**證據匹配**,不是**療效預測模型**：給定「疾病 + 已知藥物標的」,回答「這個標的-藥物配對在此適應症的證據強度到哪個階段」與「已知藥物是否確實已在此適應症被驗證過」。

### 實測驗證（真實資料,本地實跑）

用 `mcp-clinical-genomics`(Open Targets)+ `mcp-clinical-trials`(ClinicalTrials.gov)串接:

| 標的 | 疾病 | Open Targets 已知/在研藥物數 | 藥物範例 | 誠實訊號 |
|---|---|---|---|---|
| IL2RA | rheumatoid arthritis | 7 | basiliximab(已核准,抗體)、denileukin diftitox(已核准) | 直接查 RA trials 為 0——basiliximab 的**真實核准適應症是腎移植抗排斥**,查 kidney transplant 立即找到 111 個試驗。系統誠實反映「這個藥沒在 RA 被驗證」,不會硬湊關聯。 |
| PLCG1 | systemic lupus erythematosus | 0 | 無 | Open Targets 沒有已知藥物,但疾病關聯查到「免疫失調/自體免疫/自體炎症」(分數 0.45)——誠實回報「有生物學關聯但無現成藥物」,不虛構藥物建議。 |

**這個結果本身示範了證據匹配該有的行為**：不會把「基因與疾病有關聯」錯誤推導成「藥物對這個病人有效」;藥物是否對某適應症有證據,與該藥物實際核准/試驗的適應症是分開查核的。

### 功能規格新增

- 新函式：`match_disease_drug_evidence(gene, disease) -> dict`
  - 查 Open Targets `target.drugAndClinicalCandidates` — 標的本身有哪些已知/在研藥物、各自臨床階段
  - 查 Open Targets `target.associatedDiseases` — 標的與該疾病的關聯分數(人類遺傳學支持)
  - 查 ClinicalTrials.gov `search_trials(condition=disease, intervention=drug_name)` — 對每個候選藥物,**用藥名而非基因名**查該藥是否真的在此適應症有試驗
  - 輸出固定包含 `caveat`: "evidence-matching only — not a treatment recommendation or efficacy prediction; verified drug-indication pairings must be confirmed against the drug label and a qualified physician"

### 護欄(與模組三其餘部分一致)
- 不輸出「建議此病人用藥」— 只輸出「此標的-藥物-適應症三元組的證據狀態」。
- 藥物在其他適應症的試驗記錄(如 basiliximab 在腎移植)必須完整呈現,不能因為與查詢疾病無關就隱藏——這正是避免誤導使用者「這個藥對這個病一定有用」的機制。
- 每筆匹配結果標註查詢時間與資料源版本(沿用 `external_evidence_cache.py` 的 `fetched_at`/`source_version` 格式)。

**交付物：** `module3_disease_drug_evidence_match_demo.json`
