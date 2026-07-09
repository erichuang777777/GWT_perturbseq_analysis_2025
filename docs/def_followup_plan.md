# D / E / F 行動計畫 — 第二輪探索的落地規格

**觸發**:第二輪五路唯讀探索(整合 triage / 組合配對 / 機制圖網路位置 / 校準 / 疾病+族群)在真實資料上跑出的結論。本文件把其中三條「現有工具就能延伸、不需外部資料」的方向落成可執行規格,並附**自我對抗性審核**與修正。

**語言**:繁中 · **日期**:2026-07-09 · **基準**:`main` @ PR #21 合併後(116d4e7)

**貫穿紀律(每一項都必須守,與 PR #21 相同)**:
- `unknown != 0`(缺資料 → `None`/`unknown`,不補 0、不當「安全/通過」)
- **descriptive-vs-decision 分離**:新欄位/新 view 永不餵 `readiness_call` / `overall_readiness_stage` / `_stage()` / `statistical_evidence_grade`
- never-fabricate、additive-only(不改既有 response 既有欄位)、provenance 標記
- commit 前跑**全** pytest、draft PR
- 每個新模組都要有一個「把 view 的 df 丟進 `compute_readiness`,輸出與未加工版逐列相同」的 **inert 迴歸鎖**(證明新欄位不可能洩漏進決策)

---

## D — 穩健優先排序(filter-then-rank)【最高信任 CP】

### 問題根據(校準 Agent 實測)
- 排序**通過**生物學回收(陽性對照刺激下進 top decile、陰性對照壓制 99.96%、藥物軸富集 2–3.5×)。
- **但**照原始 `n_total_de_genes` 排的短名單**不穩健**:嚴格 replicate/batch/donor 過濾下 top-N 翻攪 **74–85%**;全 33,983 列中只有 **1,102(3%)**過 `replicate_pass_flag`。高原始-DE 列不成比例地不穩健。
- Spearman **0.943** 證明**過濾後的排序沒問題** → 修法就是 **filter-then-rank**,不是 rank-on-raw-DE。

### 既有現況(已核對,避免重工)
- `report/generate._top_candidates`(L59)**已**把 `replicate_pass_flag` 當第 2 sort key(grade 之後)。但這是**加權排序**,不是**過濾**——高 grade 但不 replicate-pass 的列仍會上榜。D 要做的是更強的**過濾優先**,且**不動** `_top_candidates`(那會改既有 summary 輸出)。
- cards 具備所有穩健欄位(已核):`replicate_pass_flag`、`batch_sensitivity_flag`、`crossdonor_correlation_mean`、`crossguide_correlation`、`n_cells_target`、`offtarget_flag`。

### 方法 — 新模組 `src/3_DE_analysis/robust_ranking.py`(read-only,純描述)
- **三態穩健分層**(不是二元,更誠實地守 `unknown != 0`):
  - `robustness_tier(cards_df) -> Series`,每列值 ∈ {`high_confidence`, `unresolved`, `low_confidence`}
  - `high_confidence` = 所有**可量測**的穩健檢查都通過:`replicate_pass_flag==True` AND `batch_sensitivity_flag=='not_flagged'` AND `offtarget_flag==False` AND `crossdonor_correlation_mean>=CROSS_MIN` AND `crossguide_correlation>=CROSS_MIN` AND `n_cells_target>=MIN_CELLS`
  - `unresolved` = 某些穩健欄位是 NaN(未量測)→ **不當 low、也不當 high**,誠實標未知(例:cross-donor 只有 14.1% 非空、cross-guide 只有 8.8%,大量列本就未量測)
  - `low_confidence` = 有可量測欄位但**未通過**
- **門檻寫死並文件化**(對齊校準 harness):`CROSS_MIN=0.2`、`MIN_CELLS=200`;另提供 `strict=True`(`CROSS_MIN=0.5`)。改門檻只改「被標成什麼 tier」,不改任何 call。
- **`batch_sensitivity_flag` 有三值(已實測):`not_flagged`(22,702)/`sensitive`(10,108)/`confounded_but_robust`(1,173)。** 預設 `high_confidence` 只收 `not_flagged`(保守,對齊校準);`confounded_but_robust` 雖名義「robust」但曾被 confound,預設**不**算 high_confidence,另留 `lenient=True` 選項納入它。
- **實測發現:`replicate_pass_flag==True` 就是綁死的閘**——它剛好 = 1,102 列,而加上 cross≥0.2/cells≥200/not-offtarget 後**仍是 1,102**(所有 replicate-pass 列本就滿足其餘條件)。所以 `high_confidence` 實質 ≈ replicate-passing;cross/cells/offtarget 是佐證性條件,保留供文件與 `strict` 用。
- `high_confidence_mask(cards_df, strict=False) -> bool Series`
- `robust_rank(cards_df, top_n=100, strict=False) -> {available, n_total, n_high_confidence, n_unresolved, returned, targets}`:**先過濾成 high_confidence,再**照 `(statistical_evidence_grade, n_total_de_genes, n_cells_target)` 排序、dedup 到 target。回傳時**明說** survivor 數(如「1,102 of 33,983 high-confidence」),把校準揭露的翻攪問題變透明。

### 對外
- **API**(additive 新端點):`GET /api/robust_ranked/{dataset_id}?strict=&top_n=` → filter-then-rank 短名單 + 三態計數。
- 選用:`GET /api/targets` 與 `GET /api/immune_ranked` 的回應**additive** 多帶一欄 `robustness_tier`(預設行為不變)。
- **Dashboard**:overview 或 immune priority tab 加「穩健優先」toggle,顯示 survivor 數與 tier chip。

### 紀律
`robustness_tier` 純描述,絕不進 readiness。`unresolved`(未量測)永不當通過或失敗。provenance:門檻值與 `strict` 旗標寫進回應。

### 測試 `tests/test_robust_ranking.py`
- 合成 cards(硬鎖):三態分類正確;NaN 穩健欄位 → `unresolved`(非 low、非 high)。
- 真資料(skipif gated):`high_confidence` 子集量級 ≈ 校準的 1,102(soft sanity 範圍);`robust_rank` 輸出 ⊆ high_confidence 列。
- **inert 鎖**:加 `robustness_tier` 後過 `compute_readiness` 逐列不變。

---

## E — 遺傳雙證據 endpoint(disease × population double-support)【最乾淨的新生物學】

### 問題根據(疾病+族群 Agent 實測)
- **161 個標的**同時是(a)某免疫適應症的 disease-associated top target(grade≥2)且(b)帶 UKB LoF 負荷 hypothesis 且 **95% CI 排除 0**。
- 最強:**IL23R**(6+ 適應症 top grade-4 關聯 + 族群 LoF [0.007, 0.121])= 全螢幕最佳雙證據;**SH2B3**(12/12 疾病)、**PTPN22**(11)覆蓋最廣。

### 既有現況(已核對)
- 疾病:`evidence/disease.py::load_disease_associations()`、`list_diseases()`、`translate_disease(cards, name, associations, min_grade, readiness)`。
  - **資料來源(自我審核已釐清):repo 內有兩個同名檔**——模組 `DEFAULT_ASSOCIATIONS_PATH` 正典載入 `src/6_functional_interaction/**results**/disease_gene_associations_detailed.csv`(7,527 列 / **13 疾病**,= 探索 Agent 用的那份);另有一份 `src/6_functional_interaction/**autoimmune_analysis**/...`(12,580 列 / 17 疾病)**不是**模組用的,E **不可**誤指它。
  - `load_disease_associations()` 載入時**已把 `gene_symbol` upper-case**(`.str.strip().str.upper()`)→ 與 cards 的 `target` join 前也要 upper-case。join key = **gene symbol**。
  - **cwd footgun(同 B 類):`DEFAULT_ASSOCIATIONS_PATH` 是 cwd 相對**(`Path("src/6_...")`)。E 從非 root 目錄跑會載到空表 → 靜默變 `available:False`。E **必須**傳明確/root-anchored 路徑(或走 `api/deps` 已解析的路徑),不能靠預設。
- 族群:`evidence/population.py::load_burden_estimates(trait='lymphocyte_count')` → `{available, estimates}`;`build_population_hypothesis_card(cards_df, burden_df, trait)` → 每列 `population_effect_estimate, lower_95, upper_95, ci_excludes_zero, direction, caveat`(`ci_excludes_zero = ~((lower<=0)&(upper>=0))`,L159)。join key = **Ensembl `target_id`**。每列固定帶 `caveat`(group-level 非病人層)。

### 方法 — 新模組 `src/3_DE_analysis/genetic_double_support.py`(read-only,**純組合既有兩模組**,不重寫)
- `double_support(cards_df, associations=None, burden=None, min_grade=2, trait='lymphocyte_count') -> dict`:
  1. **疾病側**:`load_disease_associations()`;把 cards **dedup 到 per-target 最高 grade**(Agent ⑤ 的「grade≥2 = 跨條件最佳 grade」語意);只留出現在 associations 且 per-target max grade≥min_grade 的 target。對每個 target 算:`n_diseases`(distinct 疾病數)、`diseases`(list)、`max_assoc`(最大 association_score)。
  2. **族群側**:`load_burden_estimates(trait)`;`build_population_hypothesis_card(cards, estimates, trait)`;只留 `ci_excludes_zero==True`。
  3. **交集**:同時滿足(1)(2)的 target。輸出每 target:`n_diseases, diseases, max_assoc, population_effect_estimate, ci=[lower,upper], direction, caveat`。照 `(n_diseases, max_assoc)` 排序。
- **Honest-fallback**:disease 表空 → `available:False`;`load_burden_estimates` unavailable → `available:False`。unknown≠0:只出現在單邊的 target **不**進雙證據清單(但可另列「單邊支持」供參,標明只有一種證據)。
- **join key 提醒**:族群 join by `target_id`(Ensembl)、疾病 join by `target`(symbol);兩者都在同一 cards frame,最後在 `target`(symbol)上交集。

### 對外
- **API**(additive 新端點):`GET /api/genetic_double_support/{dataset_id}?min_grade=&trait=` → ranked 清單,**逐列帶 population `caveat` 原文**。
- **Dashboard**:Disease Translator tab 加「遺傳雙證據」小節。

### 紀律
雙證據是**描述性標註**,不進 readiness。族群 `caveat`(population-level, not patient-level)逐列不可省。disease 關聯僅 `genetic_association` 型(GWAS 級,非實驗因果)——在 UI/回應標明。

### 測試 `tests/test_genetic_double_support.py`
- known-answer(gated 於真資料):**IL23R** 在清單內、`n_diseases>=6`、`ci_excludes_zero`;**SH2B3** `n_diseases==12`;**PTPN22** 在清單內。
- 負向:一個有疾病支持但 CI 含 0 的 target **不**在清單(排除邏輯正確)。
- honest-fallback:disease 或 population 檔缺 → `available:False`。
- 每列帶 `caveat`。

---

## F — 整合多軸 triage card(composite view)【大整合,依賴 D+E】

### 問題根據(整合 triage + 機制圖 Agent)
- 345 候選中只有 **6 個多軸贏家**(PIK3R1/PLCG1/CD3E/CD247/IL4R/ITK);只有 CD3E/CD247 有已證實有利安全窗;LAT 被安全軸正確降級。concept-lens 與 switch-lens 幾乎不重疊 → 值得一張把所有軸攤開的 composite 卡。

### 方法 — 新模組 `src/3_DE_analysis/triage_view.py`(read-only,**組合** concept_annotation + stimulation_switch_explorer + 安全 overlay + robust_ranking[D] + genetic_double_support[E] + 選用機制圖)
- `build_triage(cards_df, gnomad_overlay, gtex_overlay, membrane_overlay=None) -> DataFrame`,每 target 一列,additive 各軸(全描述性、各帶 provenance):
  - 免疫概念:`concept_modules`, `n_concept_modules`, `stimulation_gated`(來自 `concept_annotation`)
  - 開關:`switch_type`(來自 `stimulation_switch_explorer.list_switches`)
  - 安全:`gnomad_constraint_flag`(`gnomad_flag_from_constraint`)、`gtex_breadth`(`safety_window_from_gtex`)、`composite_safety_liability`(`composite_safety_liability`)——**只有 ~15 gnomAD 基因有值,其餘 `unknown`**
  - 成藥性:`druggable_class`, `tractability_modality`(cards 既有欄)
  - 穩健:`robustness_tier`(來自 D)
  - 遺傳雙證據:`double_support`(bool)、`n_diseases`(來自 E)
  - 機制圖網路位置(**選用、稀疏**):`reactome_pathways`/`string_degree`——**只有 15 個 `_pathway` 快照基因有值**,其餘 `unknown`;明確標為稀疏軸,不讓它主導排序
- `triage_rank(cards_df, weights=DEFAULT_WEIGHTS, top_n=100) -> dict`:透明多軸加權(權重寫死並文件化,可覆寫),`n_axes` = 正向命中的軸數;排序 `(total, n_axes, |effect|)`。**安全軸永不因 unknown 給分**(unknown 0 分;KNOWN-favorable 加分、KNOWN-high liability 扣分)。

### 對外
- **API**:`GET /api/triage/{dataset_id}?top_n=` → composite 短名單 + 每軸 provenance 區塊。回應大 → 一定分頁/top_n。
- **Dashboard**:「整合 triage」tab,一列一 target、各軸 chip(concept / gated / switch / safety / druggable / robustness / double-support)。

### 拆分(F 較大,建議兩段)
- **F1** = composite 資料模型 `build_triage` + `triage_rank` + API + 測試
- **F2** = dashboard tab

### 紀律
純 composite VIEW,絕不進 readiness。各軸 provenance(concept_set_version、gnomAD/GTEx source、pathway snapshot 版本)。稀疏軸(安全 15、機制圖 15)明確標 coverage,`unknown != 0`。

### 測試 `tests/test_triage_view.py`
- composite 完整性:各軸欄位齊備;多軸贏家(PIK3R1/PLCG1/CD3E/CD247/IL4R/ITK)近頂;LAT 因安全降級。
- **inert 鎖**:composite df 過 `compute_readiness` 逐列不變。
- unknown 逐軸正確(安全/機制圖大量 unknown,不當 0)。

---

## 相依與執行順序
- **D 獨立**(只碰 cards 既有欄)。
- **E 獨立**(組合 disease + population 兩既有模組)。
- **F 依賴 D(robust_ranking)與 E(genetic_double_support)** → 最後做。
- 順序:**D ∥ E(worktree 並行)→ F**。打包:D、E 可各自一個 draft PR(或合併成一個「第二輪落地」PR 分三組 commit);F 另開(它依賴 D/E 先落地)。
- 每步 commit 前跑全 pytest;draft PR。

## 完成定義
- 全 pytest 綠(含新 inert 鎖 + known-answer)。
- D:`/api/robust_ranked` 回 filter-then-rank 短名單 + 三態計數;`unresolved` 不當通過/失敗;readiness 逐列不變。
- E:`/api/genetic_double_support` 浮出 IL23R/SH2B3/PTPN22;逐列帶 population caveat;honest-fallback 正確。
- F:`/api/triage` 一列一 target 攤開全軸;6 個多軸贏家近頂、LAT 被安全降級;稀疏軸標 coverage;readiness 逐列不變。
- 三者皆 descriptive-only、provenance 標記、draft PR。

---

## 自我審核(對抗性,已對真實程式碼核對,VERDICT: SOUND-WITH-FIXES)

**已折入的修正:**
1. **D 的 batch flag**:實測有三值(`not_flagged`/`sensitive`/`confounded_but_robust`);預設 high_confidence 只收 `not_flagged`,`confounded_but_robust` 另留 `lenient` 選項。(已折入 D)
2. **D 的綁死閘**:`replicate_pass_flag==True` 剛好 = 1,102,且是 high_confidence 的實質決定條件(加其餘過濾仍 1,102)。cross/cells/offtarget 為佐證。(已折入 D)
3. **E 的資料來源歧義**:兩個同名 disease 檔;模組正典用 `results/`(13 疾病),**非** `autoimmune_analysis/`(17 疾病)。E 不可誤指。(已折入 E)
4. **E 的 join 大小寫**:`load_disease_associations` 已 upper-case `gene_symbol`;cards `target` join 前也要 upper。(已折入 E)
5. **E 的 cwd footgun**:disease 預設路徑 cwd 相對,E 必須傳 anchored 路徑或走 `deps`,否則靜默 `available:False`。(已折入 E)

**已核對正確(不需改):**
- D:cards 具備全部穩健欄位;`report/generate._top_candidates` 已用 replicate_pass 當第 2 sort key(D 走**更強的過濾**且不動它)。
- E:population `build_population_hypothesis_card` 回 `population_effect_estimate/lower_95/upper_95/ci_excludes_zero/direction/caveat`;burden 檔欄位 `ensg/post_mean/lower_95/upper_95` 實測存在;`ci_excludes_zero=~((lower<=0)&(upper>=0))`。兩份 burden 檔(LymphocyteCount + field86_unlabeled),trait 預設 `lymphocyte_count`。
- F:安全函式簽章 `gnomad_flag_from_constraint(ensembl,overlay)` / `safety_window_from_gtex(ensembl,overlay)` / `composite_safety_liability(gnomad_flag,safety_window)`;load 函式 `load_gnomad_constraint_overlay`/`load_gtex_safety_overlay`/`load_membrane_tractability_overlay` 皆存在。
- 相依 D∥E→F 正確;F import D/E 模組,故 D/E 需先落地。

**殘留風險(執行時注意,非阻斷):**
- F 回應體大(每 target × 多軸 + 每軸 provenance)→ 必須分頁/top_n,且 dashboard 表格要 lazy。
- F 的機制圖軸只有 15 基因、安全軸只有 15 基因 → 稀疏軸不可主導排序,UI 要標 coverage。
- E 的 disease 關聯只有 `genetic_association` 型(GWAS 級),非實驗因果;族群為 group-level——兩個 caveat 都要在回應/UI 顯示。
