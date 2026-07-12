# Tier-2 計劃:Open Targets Genetics / GWAS Catalog 全量整合

> **狀態:計劃(尚未實作,範圍已拍板)**。本文件只規劃,不動任何程式碼/資料。
> 對應 `docs/ROADMAP.md` 「Better use of the paper's own in-repo data」段落最後一項:
> *「Full Open Targets Genetics / GWAS Catalog(Tier-2,aligns with the paper's autoimmune-GWAS emphasis):expand disease association beyond the current 13 curated indications / 17% coverage.」*
>
> **範圍已確認(2026-07-12)**:疾病範圍採**選項 2(擴大到 EFO 免疫疾病分支)**;新 overlay 與現有 13-disease 策展表**並存 + 資料分層標籤**;換環境後**先不規劃 Option B 降級**,直接照 Option A(bulk parquet)執行,連不上再回頭處理。

---

## 0. 一句話結論

現況疾病關聯只覆蓋 **13 個策展適應症 / 2,989 個基因(17.2%)**,資料來源是**一次性匯出的靜態 CSV**。Tier-2 的目標是把它擴大到**全基因組規模的 Open Targets genetic_association 證據**,但**這個環境目前無法連到 Open Targets 或 GWAS Catalog 的任何 host**(已實測,見 §2)——跟 gnomAD Tier-2 一開始的狀況相反(gnomAD 那次剛好這個環境有開放)。所以本文件把方案設計到「即插即用」:一旦你換到有網路權限的環境,直接照 §6 的步驟做,不用重新調查。

---

## 1. 現況盤點(這次規劃前重新核對過的真實數字)

### 1.1 現有的疾病關聯資料(`evidence/disease.py`)

- 檔案:`src/6_functional_interaction/results/disease_gene_associations_detailed.csv`
- **7,527 列、13 個適應症、2,989 個唯一基因**(實測,非文件推測)
- 13 個適應症清單:Crohn's disease、Hashimoto's thyroiditis、ankylosing spondylitis、asthma、autoimmune disease、celiac disease、inflammatory bowel disease、multiple sclerosis、psoriasis、rheumatoid arthritis、systemic lupus erythematosus、type 1 diabetes mellitus、ulcerative colitis
- 對 11,526 個標的的覆蓋率:**1,977 / 11,526 = 17.2%**(來自 `REPRODUCIBILITY.md` §3,與 `/api/meta/coverage` 一致)
- 這是**一次性靜態匯出**,不是即時查詢——`evidence/disease.py` docstring 明講:「No new external fetch is needed or performed here」
- 消費者:`api/routers/disease.py`(Disease Translator 頁面)、`genetic_double_support.py`(疾病 × 族群雙重支持)。**兩者皆為描述性,不影響 `readiness_call`/`overall_readiness_stage`**(已重新確認,見 §1.3)。

### 1.2 現有的即時 Open Targets 抓取(`evidence/external_cache.py`)

- `fetch_open_targets(gene)`:對單一基因跑 Open Targets GraphQL(`api.platform.opentargets.org/api/v4/graphql`),抓 `tractability` + `associatedDiseases`(含 `genetic_association` datatype score)+ `safetyLiabilities`
- 30 天 TTL、快照到 `sources/target_tool_cache/_evidence/<gene>.json`,**懶加載**(只有被查過的基因才有快照,沒有全量預抓)
- `common/evidence_grading.genetic_support_confidence_from_evidence()` 用這個快照算 `genetic_support_confidence`(strong/moderate/no_genetic_association/unknown)——**同樣明確不影響 `readiness_call`**(docstring:「never feeds `_stage()`/`readiness_call`」)
- 這條路徑技術上可行,但**逐基因 API 呼叫對 11,526 個標的不可行**(對照 gnomAD 的前車之鑑:`docs/mvp-research/pipeline/kinetics_avoid/EVIDENCE_COVERAGE.md` 記載「gnomAD LOEUF/pLI 只覆蓋 71/1,235(6%)——因為用 per-gene API 抓取,~8s/基因,1,235 個需 90 分鐘,被中止」)

### 1.3 決策安全性重新確認(這點很重要,先講清楚)

我重新追蹤了三個可能被 Tier-2 動到的訊號,確認**全部是描述性,沒有一個進 `readiness_call`**:

| 訊號 | 檔案 | 是否進決策 |
|---|---|---|
| `evidence/disease.py::translate_disease()` | Disease Translator 排序清單 | ❌ 純顯示,`readiness` 參數只是拿來一起顯示,不回寫 |
| `common/evidence_grading.genetic_support_confidence_from_evidence()` | 描述性 genetic support 分級 | ❌ docstring 明講不進 `_stage()` |
| `genetic_double_support.py` | 疾病×族群組合視圖 | ❌ docstring 明講「nothing here feeds readiness_call」 |

**唯一真的會進 `readiness_call` 的人類遺傳學訊號是 `core/readiness.py::_human_genetic()`**,但它讀的是完全不同的東西——`metadata/gene_lists/gwascatalog.tsv`(6,336 基因)+ `clinvar_path_likelypath.tsv`(3,078 基因)這兩份**存在-即-有**(presence-only)的基因清單,對 11,526 標的的聯集覆蓋率已經是 **44.1%(5,081 / 11,526)**,不是本次 Tier-2 要擴大的目標(它已經不算稀疏,且結構是 yes/no,不是逐疾病關聯)。

→ **結論:Tier-2 這次擴大的範圍全部是描述性 overlay,跟 gnomAD Tier-2 風險等級相同(不影響任何決策),不需要重跑校準(calibration harness)或動 golden-file 已知答案。**

---

## 2. 網路可達性實測(2026-07-12,本次規劃時測的,非假設)

跟 gnomAD Tier-2 一樣的紀律:先實測,不用訓練知識猜測。這次的結果跟 gnomAD 相反:

| Host | 結果 | 備註 |
|---|---|---|
| `storage.googleapis.com`(GCS,gnomAD 用的) | ✅ CONNECT 200 | 這個環境的 proxy 允許清單裡有 |
| `storage.googleapis.com/open-targets-data-releases/*` | ⚠️ Bucket 存在,但 list API 回 400 "requester pays, no user project provided" | 需要帶 GCP billing project 或改用 object-level GET(未逐一測完,見 §6 待驗證項) |
| `api.platform.opentargets.org`(現有程式碼用的 GraphQL) | ❌ 403(policy denial) | 連現有的逐基因抓取路徑在**這個環境**也打不通 |
| `platform.opentargets.org` / `downloads.opentargets.org` | ❌ 403(policy denial) | |
| `ftp.ebi.ac.uk`(GWAS Catalog / OT 官方 FTP 鏡像) | ❌ 403(policy denial) | |
| `www.google.com`(一般網站,對照組) | ❌ 403(policy denial) | 確認不是特定路徑問題,是 **host allowlist 策略**,只有少數 host(如 `storage.googleapis.com`)被放行 |

`$HTTPS_PROXY/__agentproxy/status` 的 `recentRelayFailures` 直接證實是 **"gateway answered 403 to CONNECT (policy denial or upstream failure)"**——policy 層級擋掉,不是暫時性網路問題。

**這與程式碼裡既有的歷史紀錄一致**(`safety_overlay.py` 舊 docstring:「the original sandbox had no egress to gnomAD, policy-blocked like Open Targets」)——Open Targets 在這個 sandbox 一直被擋,這次也不例外,即使 gnomAD 這次剛好開放了。

**結論:這個環境現在做不了 Tier-2 的任何一個選項**(§3 三個選項都需要目前被擋的 host)。跟你在 Tier-1/gnomAD 討論時說的「若不行我換個環境」一致——這次就是那個「不行」的狀況。

---

## 3. 資料來源選項比較

| | Option A(建議):OT Platform bulk parquet | Option B:沿用現有逐基因 GraphQL | Option C:直接解析 GWAS Catalog 原始關聯表 |
|---|---|---|---|
| Host 需求 | `storage.googleapis.com`(可能需 billing project,待驗證) | `api.platform.opentargets.org` | `ftp.ebi.ac.uk` 或 `www.ebi.ac.uk` |
| 覆蓋規模 | 全基因組、全疾病(單次下載) | 逐基因,11,526 次呼叫不可行 | 全量但需自行 SNP→gene mapping + LD/fine-mapping,OT 已經幫你做好這件事 |
| 與現有 schema 相容性 | 高(可映射成 `evidence/disease.py` 現有欄位) | 高(程式已存在,`fetch_open_targets` 已抓 `genetic_association_score`) | 低(需要重新建 gene mapping pipeline,等於重做 OT 已做過的事) |
| 誠實度風險 | 低(可精確過濾 `datatypeId == genetic_association`,避開 `association_score` 混雜 somatic/literature 的問題,見 §4.1) | 低(同上,已有精確欄位) | 中(GWAS Catalog 原始表本身沒有做 fine-mapping/L2G,基因指派可能不準,`docs/mvp-research/level4_external_validation` 已提到 L2G/eQTL 不見得贏 nearest-gene) |
| 可重現性 | 高(單一版本快照,像 gnomAD 的作法) | 中(需要固定 TTL/日期,逐基因結果可能隨查詢時間漂移) | 高 |
| 對應此次 Tier-1 學到的教訓 | ✅ 完全對齊(bulk > per-gene API,見 gnomAD Tier-2 的 v4.1 autosomes-only 教訓、EVIDENCE_COVERAGE.md 的 6%→97% 教訓) | ❌ 重蹈覆轍 | 部份對齊,但重造輪子 |

**建議:Option A 為主,Option B 為降級後備。** Option C 不建議——`docs/mvp-research/level4_external_validation/LEVEL4_EXTERNAL_VALIDATION.md` 已經記錄 Open Targets Platform 本身就是「aggregating GWAS Catalog, UK Biobank, FinnGen, ClinVar」的整合層,直接用 OT 的整合結果,不必回頭重新组装原始 GWAS Catalog(這也是現有 `evidence/disease.py` 既有資料的來源邏輯,維持一致)。

---

## 4. 建議設計(Option A 細節)

### 4.1 過濾規則(誠實度的關鍵)

- **只取 `datatypeId == "genetic_association"` 的分數**,不要用聚合後的 `association_score`(混了 `somatic_mutation`/`literature`/`known_drug`/`rna_expression` 等)。這點在 `data_dictionary.md` 已經有先例警告:VAV1「高 overall_score 是癌症文獻/somatic,不是遺傳學」,`genetic_support_confidence_from_evidence()` 因此**故意只用 `genetic_association_score`**——Tier-2 必須延續同一條紀律。
- 每個 target-disease pair 保留:`disease_efo`(EFO ID)、`disease_name`、`gene_symbol`(+ Ensembl ID)、`genetic_association_score`、`genetic_evidence_types`(該分數底下有哪些 evidence source,如 `gwas_credible_sets`/`eva`/`clingen`,盡量保留原始細分而非只給單一分數)。
- **不做「absence = 0」**:一個 gene-disease pair 沒出現在資料裡就是「未測量/沒證據」,不是「score=0」——跟 gnomAD Tier-2 的 `unknown != 0` 紀律一致。

### 4.2 疾病範圍(已決定:選項 2)

三個選項曾列在此比較,**已選定選項 2**:

1. ~~維持現有 13 個策展適應症~~(風險最低但只解決基因覆蓋,不解決疾病廣度——未採用)
2. **✅ 已選定:擴大到整個 EFO「immune system disease」/「autoimmune disease」treatment area 分支**——不只 13 個,涵蓋更廣的自體免疫/發炎性疾病,但仍聚焦在論文強調的免疫學範疇,呼應論文本身的 autoimmune-GWAS 重點。
3. ~~不設疾病範圍限制,全 EFO 收錄~~(會混入大量與 CD4 T 細胞、免疫學無關的疾病,稀釋訊號——未採用)

理由:呼應 `docs/ROADMAP.md` 原文「aligns with the paper's autoimmune-GWAS emphasis」的定位,也呼應 `autoimmune_clusters.py` 已經建立的「聚焦免疫/自體免疫」產品調性。

### 4.3 與現有模組的整合點(已決定:並存 + 資料分層)

- **不取代**現有 `evidence/disease.py` 的 13-disease 策展表,而是**新增一份更廣的 overlay,並存 + 資料分層**(理由:現有 13 個是人工策展、已知品質高且與論文的 cluster enrichment 分析同源;新的 OT 全量資料是機器規模但可能含較多雜訊。兩者並存,UI 上要清楚標示差異——類似 `REPRODUCIBILITY.md` 已經用「策展 vs 全量」區分 concept 模組 seed 跟其他 overlay 的做法)。
- Schema 對齊現有 `disease_gene_associations_detailed.csv` 欄位(`disease_efo, disease_name, gene_symbol, association_score, genetic_evidence_score, genetic_evidence_types`),讓 `evidence/disease.py::load_disease_associations()` 可以直接指到新檔案而不用改介面——但**新增一個 `source` / `curation_tier` 欄位**區分「本次論文策展 13 項」vs「OT 全量擴充」,避免使用者誤把兩者當同等品質。
- `common/evidence_grading.genetic_support_confidence_from_evidence()`:目前吃的是**逐基因即時快照**(`_evidence/<gene>.json`),覆蓋率完全取決於哪些基因被查過。Tier-2 完成後,可以讓這個函式**優先讀 bulk overlay**(全量、免即時查詢),查不到才 fallback 到即時快照——覆蓋率會從「懶加載、不定」變成「11,526 個標的中 OT 收錄了多少就有多少」。

---

## 5. 建置腳本設計(比照 `build_gnomad_constraint_overlay.py` 的模式)

新檔案:`src/3_DE_analysis/data_acquisition/build_opentargets_genetics_overlay.py`

```
輸入:
  --source <本地 parquet/檔案路徑>   (離線優先,比照 gnomAD 腳本的 --source/--download 雙模式)
  --download                        (從 GCS bulk release 抓)
  --disease-scope {curated13,immune_efo,all}   (已決定 immune_efo,見 §4.2;仍保留其餘選項供未來調整)
  --output sources/target_tool_cache/_overlays/opentargets_genetics_overlay.csv

流程:
  1. 讀 OT release 的 target 索引(Ensembl ID ↔ approved symbol,含版本號)
  2. 讀 OT release 的 disease 索引(EFO ID ↔ name ↔ therapeutic area),依 --disease-scope 過濾
  3. 讀 associationByDatatypeIndirect(或該版本對應的資料集名稱——**待實作時依當下 OT release 的實際 schema 核對,不能假設路徑不變**),過濾 datatypeId == genetic_association
  4. Join 三者,輸出 gene_symbol + disease_name + genetic_association_score + evidence_types + source="opentargets_bulk_v<release>"
  5. 值缺失的列直接丟棄,不補 0(unknown != 0)
  6. 確定性排序 + 固定浮點格式,讓輸出可重複、可 git diff(比照 gnomAD 腳本已驗證過的「重跑後 md5 相同」規則)
```

**實作前必須做的驗證**(不能假設,參考 gnomAD Tier-2 那次發現 v4.1 是 autosomes-only 的教訓):
- 確認當前 OT release 版本號與資料集實際欄位名稱(OT 的 parquet schema 在不同年度版本間有改過,不能照抄舊文件)
- 確認 `open-targets-data-releases` bucket 到底是不是真的 requester-pays(§2 的 400 錯誤要嘛換個 object-level 路徑重測,要嘛需要 GCP 專案)

**降級方案(Option B)先不規劃**:已確認換環境後直接照 Option A 執行,若真的連不上 bulk parquet 再回頭處理逐基因 GraphQL 的降級路徑,不在本次計劃範圍內預先設計。

---

## 6. 實作步驟(範圍已拍板,依此順序執行)

1. 換到有網路權限的環境,重跑 §2 的可達性測試,確認 Option A 的實際路徑可行(bulk parquet or 需要 billing project)。**先不考慮降級成 Option B**——連不上再回頭處理。
2. 依 §4.2 已選定的 EFO 免疫疾病範圍,寫 `build_opentargets_genetics_overlay.py`,先跑一次確認輸出列數/基因數/疾病數,不要盲目相信文件寫的舊數字。
3. 更新 `evidence/disease.py`:新增讀取新 overlay 的路徑(保留舊 13-disease 表不變,新增 `curation_tier` 欄位區分)。
4. 更新 `common/evidence_grading.genetic_support_confidence_from_evidence()`:改為優先讀 bulk overlay,查不到才 fallback 即時快照。
5. 更新 `docs/data_dictionary.md`(新增 overlay 欄位定義)、`docs/data_governance_checklist.md`(新增資料來源列)、`docs/REPRODUCIBILITY.md` §3 覆蓋率表(disease_association 那一列數字會變)、`docs/ROADMAP.md`(標記此項 shipped)。
6. 新增/更新測試:比照 gnomAD Tier-2 的做法——
   - `tests/test_evidence_disease.py`(或既有等價檔案)覆蓋率斷言(17.2% → 新數字)
   - known-answer 測試:挑幾個論文已知的自體免疫基因(CTLA4/IL2RA/PTPN22 等)確認能撈到合理疾病關聯,呼應 `autoimmune_clusters.py` 已經驗證過的「textbook 基因對 textbook 疾病」模式
   - `common/evidence_grading` 的 unknown-fallback 測試維持通過(bulk 查不到時仍要能 fallback 到即時快照或回 unknown,不能報錯)
7. 加進 `FREEZE_MANIFEST.csv` + `scripts/freeze_pipeline.py::EXPLICIT_PATHS`(比照 gnomAD overlay 的做法)。
8. 全 pytest、commit、push、開 draft PR(沿用既有的分支/PR 流程)。

---

## 7. 決策紀錄(2026-07-12 拍板)

| 問題 | 決定 |
|---|---|
| 疾病範圍(§4.2) | **選項 2:擴大到 EFO 免疫疾病分支**(不是維持 13 個,也不是全 EFO 不設限) |
| 取代 vs 並存(§4.3) | **並存 + 資料分層標籤**(新 overlay 加 `curation_tier` 欄位,不動現有 13-disease 策展表) |
| 換環境後連不上 bulk parquet 怎麼辦 | **先不規劃 Option B 降級**,直接照 Option A 執行,連不上再回頭處理(不在本次計劃範圍內預先設計降級路徑) |

---

## 8. 誠實護欄(延續全平台原則,本計劃不打算破例)

- `unknown != 0`:沒收錄的 gene-disease pair 是「未評估」,不是「無關聯」。
- 描述性、非決策:確認過(§1.3)這次擴大的三個訊號都不進 `readiness_call`/`overall_readiness_stage`,不需要重跑校準 harness。
- 誠實區分證據強度:只用 `genetic_association` datatype,不用會混入 somatic/literature 的聚合分數(§4.1),避免重蹈 VAV1 式假陽性。
- 版本化:單一 OT release 版本快照,建置腳本可重跑、輸出確定性(比照 gnomAD Tier-2 已驗證的「重跑 md5 相同」標準)。
- 不假設網路可達:任何路徑細節在真正動手實作前都要重新實測(§2/§5 已多次強調),不能照抄本文件寫的猜測性路徑名稱。
