# 概念詞典（Concept Dictionary）— CD4 T 細胞免疫概念模組 M01–M20

**狀態：** 正式文件（P1，`docs/compass_concept_integration_plan.md` §2A / §4 落地）· **語言：** 繁體中文 · **定位：** 探索性研究 demo — 非診斷、非治療建議、非療效預測

---

## 0. 這 20 個模組是什麼

這 20 個 CD4 T 細胞免疫概念模組（M01–M20）就是本工具的**概念瓶頸層（concept-bottleneck layer）**。它們定義於
`sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv`，欄位為
`module_id, module_name, category, seed_genes, primary_question, notes`；由
`src/3_DE_analysis/api/deps.py::_load_modules` / `_module_scores` 解析，把每個**標的**投影到這些概念（目前是 geneset overlap 計分）。

**與 COMPASS 的對照。** COMPASS（mims-harvard，*Nature Medicine* 2026，concept bottleneck transformer）的核心是：基因表現（15,672 基因）不直接餵給預測器，而是先投影到 **44 個生物學上有意義的免疫概念**，再由概念層產生可解釋輸出。本工具用**完全相同的中介層想法**：基因表現 → 一組有意義的免疫概念 → 可解釋的概念活化剖面。差別在於：

- **本工具是 CD4-specific 的 20 個概念**（適配本平台：CD4 T 細胞 Perturb-seq / CRISPRi 藥物標的探索），而非 COMPASS 的 **pan-cancer 44 個概念**。這是有意的範疇選擇——20 個概念覆蓋本平台真正做過擾動的 CD4 生物學（TCR 訊號、共刺激/檢查點、細胞激素軸、Th 分化、代謝、記憶/耗竭、細胞週期），不外推到本平台沒有資料的癌種或組織。
- 概念分數是 **seed-gene 表現彙總 / overlap**，可手算稽核，**無黑箱權重**。

**分類（`category`）。** 每個模組標為 `Upstream`（訊號起始/受體/近端傳導、可藥物調節的上游節點）或 `Downstream`（分化程式、轉錄輸出、表型程式）。此欄逐字取自 CSV。

---

## 1. 因果關係聲明（描述性 vs 決策性分離，全域適用）

**概念剖面是描述性的，永不進決策層。** 每個模組的概念活化分數/overlap 分數
**永不餵**（never feeds）`readiness_call` / `overall_readiness_stage` /
`statistical_evidence_grade`，也不進 `readiness_engine._stage()`。它僅供人類解讀
（「這個標的/樣本在哪些免疫概念上有訊號」），與本 repo 對
`safety_window_score` / `gnomad_constraint_flag`（見 `docs/data_dictionary.md`：
`_stage()`/`readiness_call` never depend on this column — it is descriptive only）
以及機制圖 `mechanism_graph`（Never feeds `readiness_call`/`overall_readiness_stage`/
`statistical_evidence_grade`）建立的**同一條「描述性 vs 決策性分離」原則**一致。

以下每個模組末的 **因果聲明** 都重申此點——這不是重複贅述，而是把該不變量寫死在每個概念旁，確保任何未來讀者或實作都不會把概念分數接進評分。

**誠實 fallback（`unknown != 0`）。** 概念/基因無資料時回 `unknown` + 覆蓋率，
**絕不補 0**。完全無重疊的概念回 `unknown`，不假裝有訊號。

**結構契約。** 本 CSV 的結構由 `src/3_DE_analysis/contracts/concept_schema.py::validate_concept_modules` 驗證（必要欄位齊全、`module_id` 不重複、每模組 ≥1 seed gene、`module_name` 不空）。

> 所有 seed genes 皆逐字取自上述 CSV，未新增、未刪減、未改寫。

---

## 2. 概念模組總覽

| module_id | module_name | category | #seed genes |
|---|---|---|---|
| M01 | TCR_Core_Receptor | Upstream | 6 |
| M02 | TCR_Proximal_Signaling | Upstream | 11 |
| M03 | Costimulation | Upstream | 7 |
| M04 | Checkpoint_Module | Upstream | 7 |
| M05 | IL2R_JAKSTAT | Upstream | 6 |
| M06 | IFN_Response | Upstream | 7 |
| M07 | Th1_Polarization | Downstream | 6 |
| M08 | Th2_Polarization | Downstream | 6 |
| M09 | Th17_Polarization | Downstream | 6 |
| M10 | Treg_Modulation | Downstream | 7（含重複 IKZF2） |
| M11 | NFkB_Axis | Downstream | 6 |
| M12 | AP1_NFAT_Activation | Downstream | 8 |
| M13 | PI3K_AKT_mTOR | Upstream | 5 |
| M14 | Metabolic_Switch | Downstream | 5 |
| M15 | Maturation_Memory_Trafficking | Downstream | 5 |
| M16 | Chemotaxis_Tissue_Infiltration | Downstream | 6 |
| M17 | Cytotoxic_Like_Differentiation | Downstream | 6 |
| M18 | Exhaustion_Escape | Downstream | 5 |
| M19 | Memory_Fate_Program | Downstream | 6 |
| M20 | Cell_Cycle_Proliferation | Downstream | 5 |

（`#seed genes` 為 CSV 中該模組 `seed_genes` 欄逗號分隔後的 token 數；M10 的 `IKZF2` 在 CSV 中出現兩次，此處逐字保留。）

---

## 3. 各模組詳目

### M01 · TCR_Core_Receptor — Upstream
- **Seed genes：** `CD3D,CD3E,CD3G,CD247,TRBC1,TRBC2`
- **primary_question：** CD4 TCR 起始訊號是否可重塑活化阈值
- **notes / 生物學意義：** 與 ZAP70/LCK/LAT 串接成一組檢驗。TCR 核心受體複合體，活化訊號的最上游起始點。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M02 · TCR_Proximal_Signaling — Upstream
- **Seed genes：** `LCK,FYN,ZAP70,LAT,LCP2,PLCG1,ITK,VAV1,CARD11,BCL10,MALT1`
- **primary_question：** TCR 下游早期信號是否可被可視為可藥物調節節點
- **notes / 生物學意義：** 適合用 Rest 與 Stim 比較。TCR 近端信號傳導鏈，可藥物調節節點密集。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M03 · Costimulation — Upstream
- **Seed genes：** `CD28,ICOS,GRB2,PIK3R1,TRAT1,CD80,CD86`
- **primary_question：** 共刺激是否造成增殖/活化程式重配
- **notes / 生物學意義：** 需與 CD28 blockade/agonist context 交叉驗證。共刺激軸決定活化/增殖程式重配。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M04 · Checkpoint_Module — Upstream
- **Seed genes：** `CTLA4,PDCD1,TIGIT,LAG3,ICOS,CD40,CD40LG`
- **primary_question：** 抑制軸是否顯示可逆/可增強訊號
- **notes / 生物學意義：** 免疫抑制與活化平衡判斷。抑制性檢查點軸，可逆/可增強訊號評估。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M05 · IL2R_JAKSTAT — Upstream
- **Seed genes：** `IL2RA,IL2RB,JAK1,JAK3,STAT5A,STAT5B`
- **primary_question：** IL-2 存活與增殖回路是否被 perturbation 重置
- **notes / 生物學意義：** 可關聯 Treg/effector 分流。IL-2 受體 / JAK-STAT 存活與增殖回路。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M06 · IFN_Response — Upstream
- **Seed genes：** `IFNAR1,IFNAR2,IFNGR1,IFNGR2,STAT1,IRF1,IRF9`
- **primary_question：** 炎症型刺激反應敏感性是否放大/抑制
- **notes / 生物學意義：** 對抗病毒與發炎疾病研究有參考價值。干擾素反應軸（I/II 型受體 + STAT1/IRF）。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M07 · Th1_Polarization — Downstream
- **Seed genes：** `TBX21,IFNG,IRF1,EOMES,STAT4,CXCR3`
- **primary_question：** 是否推動 Th1-like transcriptomic shift
- **notes / 生物學意義：** 與刺激條件耦合後再解讀。Th1 分化主控轉錄程式。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M08 · Th2_Polarization — Downstream
- **Seed genes：** `GATA3,IL4,IL13,IL4R,STAT6,IRF4`
- **primary_question：** 是否推動 Th2-like 偏轉
- **notes / 生物學意義：** 避免與炎症共發生混淆。Th2 分化主控轉錄程式（GATA3/STAT6 軸 + IL4/IL13 效應）。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M09 · Th17_Polarization — Downstream
- **Seed genes：** `RORC,IL17A,IL17F,IL23R,STAT3,CCR6`
- **primary_question：** 是否推動 Th17-like 炎症程式
- **notes / 生物學意義：** 常見於慢性發炎自體免疫背景。Th17 分化程式（RORC/STAT3 軸 + IL17 效應）。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M10 · Treg_Modulation — Downstream
- **Seed genes：** `FOXP3,IKZF2,CTLA4,IL2RA,TGFB1,TGFB2,IKZF2`
- **primary_question：** 是否改變耐受/抑制軸
- **notes / 生物學意義：** 需搭配 protein layer 驗證。調節性 T 細胞耐受/抑制程式。（`IKZF2` 在 CSV 中逐字出現兩次，此處保留原樣。）
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M11 · NFkB_Axis — Downstream
- **Seed genes：** `NFKB1,RELA,IKBKB,TRAF2,TNFRSF1A,REL`
- **primary_question：** 是否改變先天/炎症訊號放大
- **notes / 生物學意義：** 與細胞壓力/死亡訊號可能耦合，需注意假訊號。NF-κB 炎症訊號放大軸。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M12 · AP1_NFAT_Activation — Downstream
- **Seed genes：** `FOS,JUN,FOSB,FOSL2,NR4A1,NR4A2,NFATC1,NFATC2`
- **primary_question：** 即時活化早期反應是否同步偏移
- **notes / 生物學意義：** 可作為 perturbation directionality sanity check。AP-1 / NFAT 即時早期活化反應。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M13 · PI3K_AKT_mTOR — Upstream
- **Seed genes：** `PIK3CD,PIK3R1,MTOR,RPTOR,AKT1`
- **primary_question：** 代謝與增殖訊號是否被改寫
- **notes / 生物學意義：** 與細胞週期/細胞量偏差同時追蹤。PI3K-AKT-mTOR 代謝/增殖訊號軸。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M14 · Metabolic_Switch — Downstream
- **Seed genes：** `MYC,SLC2A1,HIF1A,CCND3,RPS6KB1`
- **primary_question：** 代謝重編程是否跟活化一致
- **notes / 生物學意義：** 需配合條件特異性分層。活化伴隨的代謝重編程（MYC/HIF1A/糖解）。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M15 · Maturation_Memory_Trafficking — Downstream
- **Seed genes：** `CCR7,SELL,LTB,S1PR1,IL7R`
- **primary_question：** 是否保留 naive/memory 歸巢輪廓
- **notes / 生物學意義：** 易受刺激時間長短影響。naive/記憶歸巢與淋巴組織定位程式。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M16 · Chemotaxis_Tissue_Infiltration — Downstream
- **Seed genes：** `CXCR3,CXCR4,CCR5,CCR6,XCL1,XCL2`
- **primary_question：** 是否改變遷移/組織定位相關程式
- **notes / 生物學意義：** 若有外部環境資料可做配對驗證。趨化/組織浸潤相關程式。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M17 · Cytotoxic_Like_Differentiation — Downstream
- **Seed genes：** `GZMB,PRF1,NKG7,FAS,FASLG,IFNG`
- **primary_question：** 是否偏向 effector-like 或非典型細胞毒程式
- **notes / 生物學意義：** 通常需蛋白與功能 assay 補強。CD4 非典型細胞毒 / effector-like 程式。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M18 · Exhaustion_Escape — Downstream
- **Seed genes：** `PDCD1,HAVCR2,LAG3,TOX,ENTPD1`
- **primary_question：** 長時間刺激下是否出現耗竭或可逆壓制訊號
- **notes / 生物學意義：** 用於 safety 和療效窗口評估。T 細胞耗竭 / 逃逸程式（TOX 驅動 + 抑制受體）。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M19 · Memory_Fate_Program — Downstream
- **Seed genes：** `TCF7,BCL11B,RUNX3,BACH2,SMARCA4,ARID1A`
- **primary_question：** 命運可塑性與穩定性是否改變
- **notes / 生物學意義：** 適合做 long-term follow-up biomarker。記憶命運/可塑性轉錄與染色質程式。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

### M20 · Cell_Cycle_Proliferation — Downstream
- **Seed genes：** `MKI67,TOP2A,MCM7,PCNA,TYMS`
- **primary_question：** 是否主要驅動增殖效應而非特異 immune pathway
- **notes / 生物學意義：** 高分數需排除非特異增殖背景。細胞週期/增殖標記程式（作為非特異增殖 sanity check）。
- **因果聲明：** 本概念的活化剖面為描述性，永不餵 `readiness_call` / `overall_readiness_stage` / `statistical_evidence_grade`，不進 `_stage()`。

---

## 4. 版本與來源

- **概念集來源：** `sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv`（20 模組，M01–M20）。
- **解析程式：** `src/3_DE_analysis/api/deps.py::_load_modules` / `_module_scores`（本 P1 未更動任何解析或計分邏輯，零行為變更）。
- **結構驗證：** `src/3_DE_analysis/contracts/concept_schema.py::validate_concept_modules`。
- **未來（列為按需，本輪不做）：** COMPASS 式的個體樣本 → 概念投影（P2）、概念剖面 waterfall 視覺化（P4）、以及 `baselines/` 目錄下的系統化多 baseline 比較（見 `docs/compass_concept_integration_plan.md` §2C）。
