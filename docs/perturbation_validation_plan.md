# Perturbation Validation Plan — 證據盤點與驗證計劃

> **一頁回答兩個問題**:(1) 我們目前建立的證據**是否符合**擾動(perturbation)驗證的標準?(2) 沒有符合的部分,**要怎麼驗證 / 開發驗證計劃**?
>
> 本文件以既有的 **5 級驗證階梯**(`docs/mvp-research/level4_external_validation/LEVEL4_EXTERNAL_VALIDATION.md`)為骨架,逐級標註 **MET(已達成)/ PARTIAL(部分)/ GAP(缺口)**,每一格的數字都可回溯到 repo 內來源檔;缺口部分接續一份**可執行、依優先序排列**的驗證計劃。
>
> **一句話結論**:L1–L4(計算層)**實質達成**、校準通過;唯一的**根本缺口是 L5 濕實驗前瞻驗證**(從未做),外加 L4 的三個先天限制(關聯≠因果、外部篩選表型不匹配、n 小)與細胞層級真實資料尚未跑過。因此現階段證據支持「**優先排序哪些標靶進入濕實驗**」,但**不足以宣稱因果 / 治療效果**。

---

## 1. 評分準則(什麼叫「符合」)

擾動驗證不是單一門檻,而是一條**分級階梯**——一項宣稱只能強到「支持它的最高階梯」為止。

| 級別 | 它回答什麼問題 | 這是哪一種宣稱 |
|---|---|---|
| **L1 計算可重現** | 同輸入是否重算出同排序? | 工程正確性 |
| **L2 統計穩健** | 排序對重採樣/門檻/多重檢定是否穩定? | 統計可信度 |
| **L3 內部方向一致** | Perturb-seq 各臂的方向/符號是否一致? | 內部一致性 |
| **L4 正交計算驗證** | **獨立、不同來源**的公開資料是否交叉印證? | 外部佐證(corroborative) |
| **L5 濕實驗驗證** | top 標靶在前瞻實驗中是否真的改變 T 細胞活化表型? | **因果 / 治療**(confirmatory) |
| **校準** | 排序是否回復已知生物學、負對照是否被正確封頂? | 指標可信度 |

**「符合」的操作定義**:一個標靶要能被宣稱為「**經驗證(validated)**」而非「**經排序(prioritized)**」,必須跨過 **L5**;L1–L4 只讓它成為「**可信的濕實驗候選**」。

---

## 2. 證據盤點:我們目前到哪(逐級 MET / GAP)

| 級別 | 狀態 | 現有證據(數字皆可回溯) | 來源檔 |
|---|---|---|---|
| **L1 可重現** | ✅ **MET** | Golden-file 逐值比對 + known-answer 對真實 **33,983** 列回歸釘選;四層版本戳記 + 不可變 `dataset_id`;34 個測試檔。 | `tests/`、`technical_methods.md §4`、`REPRODUCIBILITY.md` |
| **L2 穩健** | ✅ **MET** | 排序穩定度 **Spearman r = 0.943**;且誠實揭露天真 top-50 vs 嚴格 top-50 僅 **13/50** 重疊(→ 需嚴格過濾)。多重檢定 FDR 控制。 | `technical_methods.md §4`、`de_and_baseline_spec.md §5` |
| **L3 內部方向一致** | ✅ **MET** | 逐條件符號(Rest/Stim8hr/Stim48hr)一致性檢查;正對照回復——Stim8hr 全部 **8 個** TCR/近端正對照落在 top decile。 | `LEVEL4…md §1`、`technical_methods.md §4` |
| **L4 正交計算** | 🟡 **PARTIAL(佐證,非確證)** | 三軌交叉印證,見 §2.1。有具體正訊號,但三個限制封頂其可宣稱範圍。 | `LEVEL4_EXTERNAL_VALIDATION.md` |
| **校準** | ✅ **MET** | **負對照**(`not_measurable`,4,774 列):**99.96%** 正確落 grade 1、**0%** 達 advance。**正對照排序 benchmark**:**AUROC = 0.85**(13 個 canonical positives vs 1,211;AP 0.47 = 44.7× random;Mann-Whitney p = 8.8e-06)。**21 基因正對照 panel**:20% 達嚴格 grade≥3,但 **93.1%** 未被 `deprioritize`。 | `technical_methods.md §4`、`reproducibility_audit/figure_registry.md` |
| **L5 濕實驗** | ❌ **GAP(從未做)** | **無**任何前瞻濕實驗資料。這是唯一的根本缺口。 | — |

### 2.1 L4 三軌現況(為何是「佐證」而非「確證」)

| 軌 | 資料源 | 正訊號 | 為何只算佐證 |
|---|---|---|---|
| **A — 遺傳關聯(Open Targets/GWAS)** | Open Targets GraphQL(GWAS Catalog/UKB/FinnGen/ClinVar) | **26/55**(47%)帶免疫遺傳關聯,**22/55** 屬自體免疫/免疫缺陷;**TYK2 rank 11, GA 0.93 = deucravacitinib(已上市藥)標靶**——最強單一外部錨點。 | **關聯≠因果**;必需基因混淆;GWAS ascertainment bias;rank–GA ρ=0.26, p=0.20(n=26,非顯著方向趨勢)。 |
| **B — 蛋白交互網路回復(STRING)** | STRING API | 旗艦 TCR hub 從擾動資料重建已知夥伴網路:**VAV1 53/86=62%**、**CD3E 38/65=58%**、PLCG1 40%。 | **文獻偏差是主導混淆**:回復率隨基因被研究的多寡而增;novel 標靶(如 FOXN2 僅 1 個已知夥伴)低回復**不是反證**。只是網路一致性檢查,不涉治療價值。 |
| **C — 全基因體 CD4 CRISPR 篩選(GSE318876)** | GEO GSE318876 | **覆蓋高:52/55(95%)在篩選庫中** → 標靶是「正確細胞型(原代 CD4 T)裡真實、表現、有功能的基因」,非假影。 | **表型不匹配(核心限制)**:該篩選量的是 **HIV 感染**,不是 T 細胞活化;HIV-hit 富集為 null(p=0.535)且**這個 null 是預期的**,無法驗證活化排序。 |

**L4 誠實總評**:外部獨立資料**存在、可透過標準 API/accession 取得、且可用**;交出具體正訊號(TYK2 三線收斂、VAV1/CD3E 網路重建);但**關聯≠因果、表型不匹配、n=55 且文獻偏差**三個限制封頂——證據是 **corroborative(佐證),not confirmatory(非確證)**。

### 2.2 其他未閉合項(非階梯,但影響「證據強度」)

| 項目 | 現況 | 影響 |
|---|---|---|
| **細胞層級真實資料** | ❌ 未跑(全量 ~1.7 TiB > 沙盒磁碟);僅對 schema 忠實的**合成 fixture** 驗證(分類準確率 81.8%)。 | responder/escaper、細胞層異質性尚未在真實資料上確認——「對合成 fixture 驗證」≠「已處理真實資料」。 |
| **情境專一性(context-specificity)** | heuristic(§3.7),**非**交互作用檢定。 | 條件專一標靶的統計嚴謹度有上限。 |
| **上傳路徑 A.1/A.2** | ✅ 已解決(純上傳→`not_assessed`;`n_total_de_genes` 保留;二者有守護測試)。 | 無殘留缺口(列此以示已閉合)。 |

---

## 3. 缺口→驗證計劃(依優先序)

以下把 §2 的每個 **GAP / PARTIAL** 轉成一個**可執行工作包**,附**目的、方法、驗收準則(acceptance criteria)、產出**。原則:**先做能立刻做的計算強化(P1–P2),把濕實驗(P3)的候選名單與判準準備到「交鑰匙」狀態**;濕實驗需外部合作與經費,故先把設計凍結、把風險前置降到最低。

### P1 — 強化 L4:換上**表型匹配**的外部 CRISPR 篩選(可立即做,純計算)

- **缺口**:Track C 的 GSE318876 量的是 HIV 感染而非活化 → 表型不匹配。
- **方法**:改以**原代 T 細胞活化/增殖**表型的公開 CRISPR 篩選做交叉印證:
  - **Shifrut et al. 2018**(GEO **GSE119450**,原代人類 T 細胞 genome-wide CRISPR ko × TCR 刺激增殖/細胞激素篩選)。
  - **Schmidt et al. 2022 Science**(CRISPRa/i × IL-2/IFN-γ 調節子,原代 CD4/CD8;GEO **GSE190604** 系列)。
  - **Freimer et al. 2022**(trans-調控網路,原代 CD4)。
  - 對每個外部篩選:把我們的 signed ranking 與其 hit 分數做 rank–rank(Spearman)、AUROC(我們 top-N 是否富集於其 hit)、與方向一致性(activation-up/down 是否對齊)。
- **驗收準則**:至少一個活化表型篩選出現**顯著正富集**(AUROC ≥ 0.65 且置換檢定 p < 0.05),且旗艦 hub(VAV1/CD3E/PLCG1/LCK/ZAP70)方向一致。**若為 null**,誠實記錄並縮小可宣稱範圍(不美化)。
- **產出**:`level4_external_validation/` 新增 `phenotype_matched_crosscheck.{csv,md}` + 一張 rank–rank/ROC 圖;更新 §2.1 Track C 補「表型匹配」續軌。

### P2 — 跑**細胞層級真實資料**的 responder/escaper(需 owner 機器,程式已就緒)

- **缺口**:目前僅合成 fixture(81.8%)。
- **方法**:依 `src/9_cell_integration/RUN_ON_REAL_DATA.md` 在 owner 自有機器(≥1.7 TiB)執行 PCA-差異均值軸 + 2-component GMM 的 responder/escaper 分類;輸出真實的細胞層異質性。
- **驗收準則**:真實資料分類準確率報告(對照合成 fixture 的 81.8%),旗艦標靶的 responder fraction 與 bulk DE 方向一致;結果寫回卡片為**描述性**欄位(不進決策,維持 unknown≠0)。
- **產出**:`src/9_cell_integration/` 真實資料 run 報告;卡片新增 responder overlay(標「descriptive, not part of the decision」)。

### P3 — **L5 濕實驗前瞻驗證計劃**(根本缺口;先凍結設計,turn-key 交付)

這是唯一能把「經排序」升級為「經驗證」的一級。設計先行,降低執行風險。

- **候選集(prioritize)**:以 **39 個 deliverable 標靶**(funnel 11,526 → 1,235 → 96 context-specific → **39 deliverable**)為第一批,並以 55-target validation shortlist 補充;第一輪先取 **10–15 個**(涵蓋:高信心旗艦如 VAV1/PLCG1、外部三線收斂如 TYK2、以及**novel 高排名但低文獻**如 FOXN2 以測「排序是否真的發現新生物學」)。
- **系統**:原代人類 CD4⁺ T 細胞,CRISPRi(對齊原始篩選模態)+ 平行 CRISPR-KO 做穩健性;每標靶 ≥2 sgRNA + NTC。
- **刺激臂**:對齊資料集——Rest / Stim 8hr / Stim 48hr(anti-CD3/CD28)。
- **讀出(readout)**:
  - 活化 marker:**CD25 / CD69**(流式)。
  - 效應細胞激素:**IL-2 / IFN-γ**(分泌 + 胞內染色)。
  - **增殖**(CellTrace 稀釋)。
  - Th 極化(Th1/Th2/Th17/Treg,對應概念層 M-modules)。
  - (加分)小型 targeted RNA panel 對照 Perturb-seq DE 方向。
- **對照**:
  - **陽性對照**:ZAP70 / LCK / CD3E(已知強效活化調控子,平台亦排前)。
  - **陰性對照**:housekeeping / 平台判定 `not_measurable` 或 deprioritize 的基因。
- **驗收準則(pre-registered)**:
  1. **方向一致性**:平台預測「activation-up」的標靶,敲低後 CD25/CD69/IL-2 顯著下降(反之亦然),**≥70% 候選**方向吻合。
  2. **陽性對照全中**、**陰性對照無效**(建立 assay 靈敏度/特異度)。
  3. **排序有效性**:高排名組的命中率顯著高於低排名組(卡方/趨勢檢定)。
  4. Novel 標靶(FOXN2 類)若命中 → 平台**發現新生物學**的直接證據;若不中 → 誠實回報並校正排序權重。
- **統計功效**:每標靶生物重複 n ≥ 3(捐贈者),依 CD25/IL-2 效應量做 power 計算(目標 80% power, α=0.05);先跑 pilot(陽性對照 + 3 標靶)定 assay 變異。
- **產出**:`docs/wetlab_L5_protocol.md`(pre-registration 級協定 + 候選名單 CSV + 判準表);可直接交外部合作 wet-lab 執行。

### P4 — 收尾 PARTIAL:情境專一性升級 + L4 限制持續揭露

- 把 context-specificity 從 heuristic 升級為**條件×擾動交互作用檢定**(如可行),或明確保留 heuristic 並在卡片標註信心上限。
- 前端 Provenance/disclosure 持續揭露 L4 三限制與 L5 缺口(現已在 `disclosure.json.limitations`),隨 P1–P3 進度更新狀態。

---

## 4. 優先序與現況一覽

| 優先 | 工作包 | 需要什麼 | 現在能不能做 | 閉合哪個缺口 |
|---|---|---|---|---|
| **P1** | 表型匹配外部篩選交叉印證 | 公開 GEO 資料 + 計算 | ✅ 立即(純計算) | L4 PARTIAL → 強化 |
| **P2** | 細胞層真實資料 responder/escaper | owner 機器 ≥1.7 TiB | ⏳ 委外執行(程式就緒) | 細胞層缺口 |
| **P3** | **L5 濕實驗前瞻驗證** | 外部 wet-lab + 經費 | 📋 設計先凍結(turn-key) | **L5 根本缺口** |
| **P4** | 情境專一性升級 + 持續揭露 | 計算 + 前端 | ✅ 漸進 | PARTIAL 收尾 |

---

## 5b. 執行軌(non-wet-lab)— 現在就做,提升工具鏈完整度

濕實驗(P3)暫緩。以下把**計算/工程可立即執行**的部分拆成三個互不重疊的工作包(disjoint files,可並行),每個都可在 sandbox 內驗證(pytest / `npm run build`),且**都不碰凍結的決策邏輯**(維持 causal isolation、unknown≠0、descriptive-vs-decision 不變量)。

| 工作包 | 交付 | 驗收 | 觸及範圍 |
|---|---|---|---|
| **WP1 — 表型匹配驗證 harness(P1)** | `docs/mvp-research/level4_external_validation/phenotype_matched_crosscheck.py`(對 `signed_ranking_v2.csv` × 外部活化表型篩選 hit 表計算 rank–rank Spearman / top-N AUROC / 方向一致性;外部表缺→誠實 SKIP 不捏造,沿用 `reproduce_signed_tracks.py` 的 assert-or-skip 模式)+ `track_d_*` 輸出 scaffold + `tests/test_phenotype_matched_crosscheck.py`(合成 fixture) | `pytest tests/test_phenotype_matched_crosscheck.py` 綠 | 新檔,不改既有程式 |
| **WP2 — 前端驗證揭露** | `disclosure.json` 新增 `validation` 區塊(5 級階梯狀態 + L4 三限制 + L5 缺口 + 連 `perturbation_validation_plan.md`);`Provenance.tsx` 新增「Validation ladder」段落渲染之;`doc_links` 加驗證計劃 | `npm run build` + oxlint 通過 | 僅前端 |
| **WP3 — 一鍵驗證報告 runner** | `src/3_DE_analysis/validation/run_all_validation.py`(串起既有 calibration / rank-stability / L4 檢查,缺資料則優雅 skip),輸出單一真相源 `validation_status.csv` + `validation_report.md`;登錄進 `documentation_index.md` | `pytest tests/test_run_all_validation.py` 綠 | 新 runner,唯讀既有函式 |

執行方式:以 sonnet subagent 並行執行三個工作包,各自只跑自己的驗證、**不做 git commit/push**;由主控整合、跑全套測試後統一提交。

## 5c. P1 實跑結果(ACTUAL RUN)— 誠實記錄:**未達標(null)**

WP1 harness 已**實際對真實資料跑過**(`run_activation_crosschecks.py`,對 `metadata/` 內快取的活化表型篩選)。**Shifrut 2018 無法在本 sandbox 跑**(未快取,且 NCBI/Cell 被網路政策封鎖 403);改跑三個已快取的活化篩選。**結果誠實記錄:未通過預先登記的驗收準則(AUROC ≥ 0.65, perm p < 0.05)。**

| 篩選(表型) | 模態 | n merged | 預登記 AUROC | perm p | 判定 |
|---|---|---:|---:|---:|---|
| Schmidt 2022 CD4⁺ IL2 | CRISPRi | 10,313 | **0.475** | 0.42 | ❌ 未達標(~0.5, 不顯著) |
| Schmidt 2022 CD8⁺ IFNG | CRISPRi | 10,313 | **0.435** | 0.031 | ❌ 顯著**低於** 0.5(反向) |
| Freimer 2022(IL2/IL2RA/CTLA4) | CRISPR-KO | 1,126 | **0.405** | 0.084 | ❌ 未達標 |

**但這個 null 是可解釋的,且另有一個弱正訊號**(皆為實算,非事後美化):

1. **軸不同**:`signed_ranking_v2` 的 `primary_rank` 排的是**轉錄方向性(directionality)**(KO 後淨去抑制),把 repressor 型基因(FOXN2/MGA)排在最前;活化篩選的 top hits 是核心 TCR 機器(VAV1/CD3/STAT5B 等正向調控子)。兩者量的是**不同的量**,方向性排序對活化 hit 的全基因體富集本就接近 0.5。
2. **必需基因 dropout(我們自己已知的限制)**:Schmidt CD4 IL2 的 **top-50 hits 有 31 個根本不在我們的排序裡**(11 個是 Hart core-essential)——因為敲低核心活化機器會殺死細胞、在我們的 viability Perturb-seq 篩選中掉出門檻。這直接解釋了為何富集是 null。
3. **弱但高度顯著的正向 magnitude 一致性(post-hoc, 探索性)**:改用**足跡廣度 `n_hits`**(即 AUROC 0.85 校準所用的量,而非方向性)對篩選顯著度,Spearman rho = **+0.119 / +0.108 / +0.283**,p = **7e-34 / 6e-28 / 3e-22**。即「足跡大的標靶在獨立活化篩選裡確實較顯著」,只是效應弱。

**誠實結論**:phenotype-matched 外部驗證(Schmidt/Freimer)**沒有**在全基因體富集層次確證我們的**方向性排序**(這是真實的負面證據,**不上修 L4 狀態**);但存在一個弱正向的 magnitude 一致性,且 null 大部分由必需基因 dropout + 軸差異解釋。這正是**不進濕實驗就先用免費資料發現**的價值——它縮小了我們能宣稱的範圍,並指出若要 phenotype-matched 對齊,應對齊 magnitude 軸並處理 essential dropout。完整逐篩選數字見 `level4_external_validation/track_d_activation_crosschecks_combined.md`。

### 5c-bis. 公平版(對齊 magnitude 軸 + 排除 essential)— 次要探索性,**通過但有 confound**

依上面的指向,把 AUROC 的 score 從**方向性 `primary_rank`** 換成**足跡廣度 `n_hits`**(即 AUROC 0.85 校準所用的軸),並**排除 Hart core-essential**:

| 篩選 | 方向性 AUROC(預登記) | **magnitude AUROC(公平,排除 essential)** | perm p |
|---|---:|---:|---:|
| Schmidt CD4⁺ IL2 | 0.475 | **0.745** | 2e-4 |
| Schmidt CD8⁺ IFNG | 0.435 | **0.749** | 2e-4 |
| Freimer | 0.405 | **0.789** | 2e-4 |

**兩軸兩答案**:magnitude 軸**過關**(0.74–0.79,遠高於 0.65,perm p=2e-4,排除 essential 幾乎不變 → 不是必需基因假影)。即**平台的足跡強度訊號確實與獨立活化篩選對齊**(與內部校準一致);不對齊的是**方向性 re-ranking**(不同軸)。

**但這是次要、探索性結論,且有一個未除的 confound(誠實標註)**:
- **選軸在看到 null 之後**(post-hoc),嚴格上需在 held-out 篩選 pre-register 才算 clean pass。
- **偵測力/表現量 confound**:「我們足跡大」與「他們篩選顯著」**都**隨基因表現量/細胞數/統計檢定力上升——0.74–0.79 有一部分可能是**共同可偵測性**而非共同活化生物學;排除 essential 無法移除這個,乾淨版需再控 baseline expression/cell count。故此為 **corroborative-with-confound,不是乾淨勝利**,**仍不上修 L4 至 met**。

守護測試 `tests/test_activation_crosschecks.py` 鎖定:方向性 null(<0.65)+ magnitude 公平版過關(>0.65 且排除 essential 幾乎不變)。

> 產出:`run_activation_crosschecks.py`、`track_d_activation_crosschecks_combined.md`、`track_d_activation_crosschecks_summary.csv`、`track_d_phenotype_matched_crosscheck.{csv,md}`(canonical=Schmidt CD4 IL2);守護測試 `tests/test_activation_crosschecks.py`(鎖定 null 與弱正訊號兩個誠實發現)。

## 5. 一句話交代(給決策者)

> 我們的證據在**計算層(L1–L4)實質達成**、校準通過(AUROC 0.85、負對照 99.96%、r=0.943),並有 **TYK2 三線收斂**這種強外部錨點——足以**可信地排序哪些標靶值得投入濕實驗**。但**尚未跨過 L5**,因此**不能宣稱因果或治療效果**。閉合方式已排定:P1(表型匹配外部篩選,可立即做)、P2(細胞層真實資料,委外)、**P3(L5 濕實驗,設計已 turn-key,待合作與經費)**。這份計劃就是把「經排序」升級為「經驗證」的路線圖。

---

*本文件與 `LEVEL4_EXTERNAL_VALIDATION.md`(L4 逐軌細節)、`technical_methods.md §4`(校準數字)、`human_validation_protocol.md`(D1–D7 逐階段人工簽核)、`src/9_cell_integration/RUN_ON_REAL_DATA.md`(P2 執行手冊)互為引用。逐字權威以各來源檔與程式為準。*
