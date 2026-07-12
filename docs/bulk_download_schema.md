# Bulk Download Schema(前端下載欄位說明)

> 說明 portal「Bulk download」提供的檔案與欄位,讓下載者知道每個欄位的意義與**未知的表示法**。欄位名取自實際的 `frontend/webserver/public/real-dataset.json`。逐欄科學定義見 `docs/data_dictionary.md`;provenance 見 `docs/provenance_registry.csv`。

## 可下載檔案

| 檔案 | 內容 |
|---|---|
| `real-dataset.json` | 標靶資料(每基因最佳條件 + 逐條件明細 + 就緒度 + 外部證據)+ 20 個概念模組 |
| `provenance_registry.csv` | 資料來源 × 演算法 × 參考文獻登錄表(79 列 × 8 欄) |
| `disclosure.json` | 版本 / 覆蓋率 / 免責 / 原則 / 限制 / attribution / 概念層說明 |

## 未知的表示法(重要)

**`null` 或空陣列 = `unknown`,不是 0。** 例如 `gnomad.loeuf = null` 代表「未查得約束資料」,`diseases = []` 代表「Open Targets 無索引到疾病關聯」——皆為誠實未知,不得當作 0 或無風險。深層外部證據僅 21 個基因有(見 `disclosure.json.coverage`)。

## `real-dataset.json` 結構

### 頂層
| key | 型別 | 說明 |
|---|---|---|
| `generatedAt` | string\|null | 匯出時間戳(目前可能為 null;由 export 填) |
| `sourceVersion` | string | 資料來源與版本描述(含 evidence fetch 日期) |
| `modules` | array(20) | 概念模組 M01–M20 |
| `targets` | array | 標靶(portal 收錄 7,249 個,為全基因 11,526 的門檻子集) |

### `modules[]`
`id`(M01–M20)· `name`(如 TCR_Core_Receptor)· `category`(Upstream/Downstream)· `seedGenes`(string[])。

### `targets[]`（每基因一列,取最佳條件彙整 + 巢狀明細）
| key | 型別 | 說明 |
|---|---|---|
| `gene` / `name` / `ensembl` | string | 符號 / 名稱 / Ensembl 主鍵 |
| `module` / `allModules` | string / string[] | 主要 / 全部概念模組(未指派時 unknown) |
| `primaryCondition` | string | 最佳條件(Rest/Stim8hr/Stim48hr) |
| `grade` / `gradeNum` | string / int | 統計證據等級 1–4 |
| `effect` / `medianLogFC` / `fdr` | number | on-target 效應量 / 中位 logFC / 最小 FDR |
| `nCells` / `nGuides` / `nDonors` | int | 細胞 / guide / 捐贈者數 |
| `nTotalDeGenes` / `nUpGenes` / `nDownGenes` | int | 下游 DE 基因數 |
| `crossDonorCorrelationMean` / `crossDonorCorrelationMin` | number\|null | 跨捐贈者穩健性 |
| `replicatePassFlag` / `offtargetFlag` | bool\|null | 複製通過 / 脫靶旗 |
| `stimulationGated` | bool | 情境專一描述性標記(heuristic) |
| `conditions` | array | 逐條件明細(見下) |
| `readiness` | object | 就緒度(見下) |
| `diseases` / `literature` / `clinicalTrials` | array | 外部證據(空 = unknown) |
| `tractabilityFlags` / `safetyLiabilities` | array | Open Targets 可成藥性 / 安全責任(空 = unknown) |
| `gnomad` | object | `loeuf` / `pli` / `constraintTier`(null = unknown) |

### `targets[].conditions[]`
`condition` · `nTotalDeGenes` · `nUpGenes` · `nDownGenes` · `maxAbsLogFC` · `fdrMin` · `ontargetSignificant`(bool)· `grade`。

### `targets[].readiness`
`call`(advance/validate/watchlist/deprioritize)· `stage`(R0–R5)· `reasons` · `nextValidationStep` · `redFlags`(string[])· `biologyScore` / `translationScore` / `tractabilityScore` / `clinicalFeasibilityScore`(int)· `translationCappedBy` · `tractabilityModality` · `humanGeneticSupport` · `diseaseRelevanceScore` · `compositeSafetyLiability` · `geneticSupportConfidence` · `hasExternalEvidence`(bool)。
> `readiness.call` 由 repo 規則引擎(`core/readiness.py`)決定,**不隨前端權重改變**;紅旗覆蓋見 `technical_methods.md` §3.5。

## `provenance_registry.csv` 欄位
`category`(data_source/algorithm/reference)· `component` · `type` · `identifier` · `version` · `source_url_or_id` · `produced_by` · `notes`。

## `disclosure.json` 頂層 key
`schema_version` · `versions` · `coverage` · `disclaimer` · `principles` · `limitations` · `attribution` · `concept_layer` · `doc_links`。

---

> 授權與引用見 `docs/data_use_terms.md`;欄位科學定義見 `docs/data_dictionary.md`。
