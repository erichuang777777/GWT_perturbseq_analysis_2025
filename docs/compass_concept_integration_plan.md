# COMPASS 概念整合 + 個體樣本輸入探索模組（規劃）

**狀態：** 規劃(尚未實作) · **語言:** 繁體中文 · **對照:** `main` @ PR #7 合併後 · **定位:** 探索性 DEMO 產品,**非正式醫療軟體**

**觸發需求(使用者 2026-07 明確指示):**
1. 把 COMPASS(mims-harvard,*Nature Medicine* 2026,concept bottleneck transformer)的概念納入本工具。
2. **建立「接受個體病人層輸入」的功能**——明確推翻先前「不接受任何個體病人層輸入」的紅線。使用者確認:**這是探索性 demo,非正式醫療軟體**,因此這份概念要加進去。

---

## 0. 邊界宣告(最高優先,寫死在每個輸出與介面)

這個模組**不是**、且不會被呈現為:診斷工具、治療建議、療效預測、臨床決策支援。它是一個**探索性、假設產生用的研究 demo**。每一筆輸出、每一個介面畫面,都必須固定顯示:

> 探索性研究 demo — 非診斷、非治療建議、非療效預測。輸出為「透明的概念投影 + 假設性標的線索」,不可用於任何臨床或個人醫療決策。

此邊界由程式強制(caveat 欄位不可為空、介面標頭文字寫死不可關閉),不是靠使用者自律。與既有 `population_hypothesis.py::CAVEAT_TEXT`、`signature_explorer.py::CAVEAT_TEXT` 同一機制。

**與舊紅線的關係:** `docs/mvp-research/README.md` 與 `docs/data_governance_checklist.md` 舊有「不接受任何個體病人層輸入」條款,改寫為:「個體樣本輸入僅限本探索 demo 模組,且僅做**透明的概念投影**(基因表現向量 → 概念活化剖面),不做黑箱預測、不輸出診療建議、不儲存或外傳原始輸入」。改寫理由與範圍在本文件 §5 完整列出。

---

## 1. 為什麼「納入 COMPASS」大多是把既有基礎正式化

COMPASS 的核心是 **concept bottleneck**:基因表現(15,672 基因)不直接餵給預測器,而是先投影到 **44 個生物學上有意義的免疫概念**(免疫細胞狀態、腫瘤微環境交互、訊號通路),再由概念層產生預測與可解釋的「個人化反應圖(personalized response map)」。

**我們已經有這個雛形。** `sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv` 定義 **20 個 CD4 T 細胞免疫概念模組**(M01–M20),每個帶 seed genes:

| | | | |
|---|---|---|---|
| M01 TCR_Core_Receptor | M06 IFN_Response | M11 NFkB_Axis | M16 Chemotaxis_Tissue_Infiltration |
| M02 TCR_Proximal_Signaling | M07 Th1_Polarization | M12 AP1_NFAT_Activation | M17 Cytotoxic_Like_Differentiation |
| M03 Costimulation | M08 Th2_Polarization | M13 PI3K_AKT_mTOR | M18 Exhaustion_Escape |
| M04 Checkpoint_Module | M09 Th17_Polarization | M14 Metabolic_Switch | M19 Memory_Fate_Program |
| M05 IL2R_JAKSTAT | M10 Treg_Modulation | M15 Maturation_Memory_Trafficking | M20 Cell_Cycle_Proliferation |

現有 `GET /api/modules/{dataset_id}`(`api/deps.py::_module_scores`)已經把每個**標的**投影到這 20 個概念(目前是 geneset overlap 計分)。這**就是我們的 concept bottleneck 中介層**,只是:(a) 目前只從「標的」方向用,還沒從「個體樣本表現」方向用;(b) 沒有正式的概念詞典文件;(c) 沒有 COMPASS 式的歸因視覺化。

---

## 2. 三個要從 COMPASS 借鏡並落地的東西

### 2A. 概念詞典正式化(小、純文件+驗證)
把 20 個模組寫成正式 `docs/concept_dictionary.md`:每個概念的 seed gene 來源、生物學意義、**與 `readiness_call` 的因果關係聲明**(沿用既有「描述性 vs 決策性分離」原則——概念剖面是描述性,不進 `_stage()`)。加一個 `contracts/concept_schema.py` 驗證 seed CSV 結構。**零行為變更。**

### 2B. 個人化反應圖 / target-card waterfall(中,視覺化)
COMPASS 對每個病人畫「基因表現 → 概念貢獻 → 預測」的歸因圖,並點名是哪些概念在拖累(例:non-responder 身上的 TGFβ 訊號、CD4T 功能失調)。這正好對應本 repo plan mode 已規劃、但尚未實作的 `target_card_waterfall`。落地為:一個把「概念活化剖面」畫成有序 bar/waterfall 的呈現(遵循 `metadata/figure_palettes.yaml` + `dataviz` skill 配色)。標的層與(新的)個體層共用同一視覺化元件。

### 2C. 系統化多 baseline 比較(中,擴充既有 A3)
COMPASS 把 22 個已發表方法收成可插拔 baseline 逐一比較。我們剛完成的 A3 `perturbation_prediction_benchmark.py` 目前只比一個 baseline(平均效應)。**本輪先不擴充**,只在概念詞典裡標注「未來可比照建 `baselines/` 目錄」。列為按需。

---

## 3. 新模組:個體樣本輸入 → 概念剖面 → 標的假設(COMPASS-analog,誠實可支撐版)

**核心對照:** COMPASS 吃「病人腫瘤轉錄體 → 44 概念 → 反應預測」。我們吃「一個 CD4 樣本的基因表現向量 → 20 概念活化剖面 → 連到本平台 CRISPRi 篩過、會調節這些概念的候選標的」。

**關鍵誠實界線:** 我們**有**真實的 concept modules 與 CRISPRi 擾動知識;我們**沒有**「病人層縱向治療結果標籤」。因此本模組做**可透明檢視的概念投影 + 假設性標的連結**(全部可解釋、可稽核),**不做**需要標籤資料訓練的反應分類器(那會逼我們捏造/外借標籤,違反 never-fabricate)。COMPASS 式的「反應/不反應二元預測」列為 §6 明確資料受阻、不做。

### 3.1 輸入契約
- `sample_expression`: 一個 `{gene_symbol: expression_value}` 的個體樣本表現向量(bulk 或 pseudobulk CD4 RNA-seq;TPM/normalized counts 皆可,單位在 caveat 標明)。
- 不需要、也不接受任何個人識別欄位(姓名/病歷號/日期)。介面只吃一個表現表,不吃身分。
- 缺基因 → 該概念以可用基因子集計分並回報覆蓋率;完全無重疊 → 該概念 `unknown`,**絕不補 0**。

### 3.2 處理流程(全部可解釋,無黑箱)
```
sample_expression (個體基因表現向量)
      │
      ├─ 投影到 20 個概念模組(每概念:樣本在該模組 seed genes 上的
      │   標準化表現彙總 → 概念活化分數 + 覆蓋率)         → concept activation profile
      │
      ├─ 對每個「異常」概念(相對參考分佈偏高/偏低),查本平台
      │   target_cards + readiness:哪些篩過的 CRISPRi 標的會調節此概念,
      │   方向為何(用既有 module_score / signed DE 方向)      → 假設性標的線索
      │
      └─ 概念剖面 waterfall 視覺化(2B)                    → personalized concept map
      │
      ▼
individual_concept_report:
  { concept_profile: [{module_id, module_name, activation, coverage, direction}],
    connected_target_hypotheses: [{gene, module_id, screen_direction, readiness_call, caveat}],
    caveat: "探索性研究 demo — 非診斷/非治療/非療效預測 ...",
    provenance: {concept_set_version, screen_data_version, computed_at} }
```

### 3.3 為什麼這是可辯護的 demo
- **透明**:概念分數是 seed-gene 表現彙總,不是黑箱權重;每個數字都可手算稽核。
- **誠實 fallback**:概念/基因無資料 → `unknown` + 覆蓋率,不假裝有訊號。
- **不越界**:輸出是「概念剖面 + 假設性標的線索」,不是診斷、不是用藥、不是劑量、不是預後。
- **不儲存原始輸入**:個體表現向量只在 request 記憶體內運算,不落地寫檔、不進快取、不外傳(與 `external_evidence_cache` 只快取「基因層公開證據」明確區分)。
- **描述性,不進決策層**:概念剖面**不餵** `readiness_call`/`overall_readiness_stage`/`statistical_evidence_grade`(同 gnomAD/機制圖/signature 的既有原則)。

### 3.4 落地
- 新檔:`src/3_DE_analysis/individual_concept_profile.py`
  - `load_concept_modules()` — 讀 seed CSV,honest-fallback(可與 `deps._load_modules` 共用)。
  - `project_sample_onto_concepts(sample_expression, modules, reference=None) -> concept_profile`
  - `connect_concepts_to_screen_targets(concept_profile, target_cards, readiness) -> hypotheses`
  - `build_individual_concept_report(sample_expression, ...) -> dict`(含固定 caveat)
- API:`POST /api/individual-concept-profile`(接收表現表,回傳報告;request-only,不落地)。
- Dashboard:新 tab「個體概念剖面(探索 demo)」,標頭護欄寫死,waterfall 用 2B 元件。
- 測試:`tests/test_individual_concept_profile.py` — 用**真實** seed modules + 一個從 repo 內既有表現資料(如 `1k1k`/pseudobulk)取的真實樣本向量做投影正確性、覆蓋率、honest-fallback、caveat 存在、不落地(呼叫後 `_evidence`/cache 目錄無新檔)等測試。

---

## 4. 分階段

- **P1(概念詞典 + schema,2A):** `docs/concept_dictionary.md` + `contracts/concept_schema.py` + 驗證測試。零行為變更。
- **P2(個體概念投影核心,3):** `individual_concept_profile.py` + 測試(不含 API/UI)。
- **P3(API + 不落地保證):** `POST /api/individual-concept-profile` + request-only 稽核測試。
- **P4(waterfall 視覺化,2B):** dashboard tab + 共用視覺元件(標的層也套用)。
- **P5(護欄文件改寫,5):** 更新 README/governance/data_dictionary 的舊紅線。

---

## 5. 舊「不接受病人層輸入」紅線的改寫(逐條)

| 舊條款(位置) | 改寫後 |
|---|---|
| `mvp-research/README.md`:「不接受任何個體病人層輸入——所有模組三功能只做 gene-level 群體統計查表」 | 「模組三(群體假設)維持不吃個體輸入。**新增**個體概念剖面 demo 模組:吃單一樣本表現向量,僅做透明概念投影,不做診療/預測,不儲存原始輸入。」 |
| `data_governance_checklist.md`:病人資料相關條款 | 新增一節「個體樣本輸入(探索 demo)」:無識別欄位、request-only 不落地、輸出強制 caveat、非黑箱、非臨床用途。 |
| `population_hypothesis.py` 護欄 | 不動(它仍是群體層)。新模組有自己的 caveat。 |

---

## 6. 明確不做(避免 scope creep 與越界)

- **不做反應/不反應二元預測分類器**(COMPASS 核心):需要病人層治療結果標籤,repo 沒有、不該用合成資料假裝有。誠實列為資料受阻。
- **不輸出**診斷、用藥、劑量、預後、治療路徑。
- **不訓練**任何個體輸出的監督式模型。
- **不儲存/不外傳**任何個體樣本原始輸入。
- **不把**概念剖面接進 `readiness_call`/評分決策層。

---

## 7. 驗收

- P1:seed CSV 通過 `concept_schema` 驗證;20 概念全文件化。
- P2:對一個真實 CD4 樣本向量,Th2-偏移樣本在 M08(Th2_Polarization)概念活化明顯偏高、覆蓋率如實回報;完全無重疊的概念回 `unknown` 非 0。
- P3:呼叫 `POST /api/individual-concept-profile` 後,`sources/target_tool_cache/` 無任何新檔(不落地稽核測試通過)。
- P4:waterfall 正確呈現概念剖面,標頭 caveat 不可關閉。
- 全程:`py_compile` + 全套 `pytest` 綠;概念剖面不改任何既有 `readiness_call`/`overall_readiness_stage`(逐位元回歸測試)。

## 8. 共用護欄(每階段遵守)

- `unknown ≠ 0`;概念/基因無資料一律 honest-fallback。
- 描述性 vs 決策性分離:概念剖面不進 `_stage()`。
- 透明可稽核:概念分數必須可手算重現,無黑箱權重。
- 個體輸入 request-only,不落地、不外傳、無識別欄位。
- 每筆輸出強制帶「探索 demo,非診療」caveat。
