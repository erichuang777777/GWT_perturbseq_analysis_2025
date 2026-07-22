# Portal 功能採納開發計畫 — 五大工具優缺點 → 落地到 CD4 Target Explorer

**狀態:** 規劃文件(尚未實作) · **語言:** 繁體中文(技術識別碼、檔名、函式名維持英文) · **日期:** 2026-07-22
**來源指示:** `erichuang777777/2026-claude-science-hackthon` → `analysis/Portal_Feature_Adoption_CN.md`
(五個 CD4/Perturb-seq 工具的優缺點清單 + 建議加到本 portal 的功能 A–M + 優先級路線圖)
**對應分支:** `claude/portal-adoption-plan-e5lpfw`

---

## 0. 如何讀這份文件

這是一份**可執行**的計畫,不是願景稿。每個提案都對應到本 repo **已存在的真實檔案與行號**,並註明「現況已有什麼 / 缺口在哪 / 具體改哪幾個檔 / 測試怎麼加 / 誠實 caveat / 成本」。

**最重要的一個發現:來源指示裡的 5 個功能,大多數在本 repo 已經有可複用的骨架** —— PubMed 文獻抓取、ClinicalTrials.gov + Open Targets 藥物比對、signed 方向性 DE、Plotly 象限圖都已存在。因此這份計畫**多半是「把既有基礎設施升級成卡片欄位 / 前端面板」,而不是從零打造**。這讓成本大幅下降、可信度大幅上升。

**目錄**

1. 策略框架 —— 為什麼把 [K] 疾病反轉當系統靈魂
2. 功能 A–M ↔ repo 現況對照表(一眼看出「已有 / 擴充 / 全新」)
3. 不可違反的設計紀律(每個新功能都必須守)
4. 逐功能詳細規格(P0 → P3)
5. 分波路線圖(對齊來源指示的三波)
6. 橫切關注點(schema 版本、provenance、MCP vs 快取、網路政策)
7. 風險與誠實護欄
8. 待決策的開放問題

---

## 1. 策略框架

### 1.1 一句話定位(採納來源指示的策略提醒)

來源指示的結尾警告:**不要變成「什麼都有但沒有靈魂」的大雜燴**。本計畫採納它的建議 —— 把 **[K] 疾病方向反轉評分**當成新的系統核心,其餘功能圍繞它:

> 「上傳你的疾病 signature,我告訴你哪個基因敲低能把細胞推離疾病狀態、這個靶點有多新穎、是否可藥、是否安全 —— 每一項都附來源與版本戳,並清楚標示這是研究用假說,不是臨床建議。」

### 1.2 為什麼 [K] 是靈魂,而且我們有底層資料做它

本 repo 已經有 `src/3_DE_analysis/signed_module_effect.py`,它讀 `metadata/suppl_tables/full_signed_DE/*.parquet`(~2.06M 列、~10,851 targets × 3 conditions、**每個 downstream gene 帶正負號 log_fc**),計算「敲低某 target 會活化還是抑制某 concept module 的程式」。**這正是 [K] 需要的機器** —— 只要把「module seed genes」換成「使用者的疾病 signature 基因集」,就能算「這個 KD 把細胞推向或推離疾病」。這不是空想,是把現成模組泛化一步。

### 1.3 本計畫改變什麼、不改變什麼

- **改變:** 新增描述性訊號(新穎性、方向反轉、下游牽連廣度、藥物連結)、新增前端視覺(象限圖、方向面板)、強化上傳 QC 與可攜報告。
- **不改變(除非明確版本升級):** 既有的 4 種 readiness 判定規則、7 個紅旗、`_stage()` 決策邏輯。**新訊號預設是描述性的,不進決策層**(見 §3)。任何要讓新訊號影響判定的提案,都被明確標為「需版本升級 + 重新校準」的獨立決策。

---

## 2. 功能 A–M ↔ repo 現況對照表

| 功能 | 來源指示的意圖 | repo 現況 | 分類 | 主要落點 |
|------|------|------|------|------|
| **E** PubMed 新穎性欄位 | 每基因查文獻數 → 新穎性分數 | `evidence/external_cache.py:112` `fetch_pubmed_literature()` 已在抓 PubMed(esearch+esummary),但只取前 10 筆、未萃取總數/分數 | **擴充** | evidence 快照 + 前端 |
| **K** 疾病方向反轉評分 | 上傳 signature → 算 KD 推向哪個方向 | `signed_module_effect.py` 已用 `full_signed_DE` 做「方向性」；只針對 concept module,未泛化到任意 signature | **擴充(核心)** | 新模組 `disease_reversal.py` |
| **F** 新穎性×效應象限圖 | 二維象限、右上=強效應+少研究 | Plotly 已是相依;`lib/drawFigure.ts:156` `burden` 就是一張帶線性擬合的 2D 象限散點 | **擴充** | `drawFigure.ts` 新分支 |
| **L** 已核准藥/臨床試驗連結 | 每命中基因查藥+trial_count | `external_cache.py:439` `match_disease_drug_evidence()`(OT drugs × CT counts + 離線 fallback)+ `/api/disease-drug-evidence` 已存在;卡片已有 `nearest_success_drug`/`nearest_failure_or_warning` | **多半已有,補呈現** | evidence 快照 + 前端 |
| **H** 網路中心性/trans-effect 廣度 | 下游牽連數 = 重要性 + 安全紅旗 | 卡片已有 `n_total_de_genes`(粗略 out-degree);`full_signed_DE` 有 KD→DEG 有向邊;但**app 程式碼無任何 centrality 計算** | **半全新** | 新 overlay `trans_network.py` |
| **A** QC 前置閘門 | 上傳後先跑品質檢查、擋分 | `upload/import_manager.py:186` context-match tier + `merge_status` 閘門已存在;`thresholds.py` 有 min_cells=200/min_de=50 | **擴充呈現** | `import_manager.py` + `/upload` |
| **C** Claude 可測試假說 | 每卡一句可測試假說 | `core/readiness.py:314` `_next_step()` 已產「下一步驗證建議」 | **擴充** | 先確定性模板,後選配 LLM |
| **D** 自含 HTML 報告匯出 | 一鍵離線 HTML | `/api/reports`、`/api/exports` 存在;`generate_target_report.py` 是 stub | **擴充** | 充實報告模板 |
| **G** 已知 regulator 標記 | 名基因下沉/加徽章 | `core/cards.py:36` `POSITIVE_CONTROLS` 清單已存在 | **擴充** | 前端徽章 |
| **I** 互動因果網路圖 | 選基因看下游 DEG 網路 | 無(`mechanism_graph.py` 只組圖形,無 centrality) | **全新** | 依賴 H,前端面板 |
| **M** 疾病 signature 上傳 | signature 上傳入口 | 無(現只有 DE-table 上傳) | **全新** | 依賴 K,`/upload` 擴充 |
| **B/J** donor-aware / 狀態特異 hub | 提示與標記 | donor 相關欄位、Rest/Stim8/Stim48 分層已在資料中 | **擴充呈現** | 前端標記 |

---

## 3. 不可違反的設計紀律(每個新功能都必須守)

這五條是本 repo 的既有紀律(`docs/data_governance_checklist.md`、`external_overlay_integration_concept.md`、frontend README §Design discipline),**任何新功能違反其一即不合格**:

1. **descriptive ≠ decision(描述/決策牆)。** 新訊號預設**不進** `core/readiness.py` 的 `_stage()`(:301)或 `_red_flags()`(:228)。既有的 ~9 個描述性附加欄(`composite_safety_liability`、`trait_liability_similarity` 等)就是範本 —— 它們被 `tests/test_translation_capped_by.py:73` 明確斷言「不改變 `readiness_call`/`overall_readiness_stage`」。每個新描述欄都要有這條**惰性斷言**測試。
2. **`unknown ≠ 0`。** 沒有證據就是字串 `"unknown"`(或該列直接缺席),永遠不是靜默的 0。`signed_module_effect.py` 對「無 measured 下游」直接不輸出該列,就是範本。
3. **compute 時不打即時網路。** 除了唯一的 `/api/disease-drug-evidence`(disease 是開放參數無法快照),其餘一律讀 `sources/target_tool_cache/_evidence/<gene>.json` 這種**離線批次快照**,透過注入的 `evidence_lookup` closure。新功能沿用此 cache-first 模式。
4. **加法式、局部。** 基因不在新 overlay → 行為完全不變。只為覆蓋到的基因**新增**資訊。
5. **每個數字帶 provenance + 版本戳。** 新訊號要有 `fetched_at`/`source_version`,登錄 `docs/provenance_registry.csv` + `docs/data_dictionary.md`;若落到卡片契約(`contracts/card_schema.py:CARD_COLUMNS`)則 bump `config/versions.py:CARD_SCHEMA_VERSION`。

---

## 4. 逐功能詳細規格

> 排序依來源指示的「影響力 ÷ 成本」優先級。每格標:**目標 / 現況(檔:行)/ 資料底層 / 實作步驟 / 測試 / 誠實 caveat / 成本**。

### 🥇 P0-K — 疾病方向反轉評分(Disease-Reversal Score)【系統核心】

- **目標:** 使用者選/上傳一個疾病 signature(up-genes / down-genes,例如 responder vs non-responder),對每個 KD 算「它把細胞推向 signature 的哪個方向」→ `reverses_disease` / `worsens_disease` / `neutral` / `unknown`。
- **現況:** `signed_module_effect.py`(整檔)已用 `full_signed_DE` 對 concept-module seed genes 做完全相同形狀的計算;`effects_for_target()`(:156)+ `GET /api/signed_module_effect/{gene}` 已上線;sanity anchors(GATA3→Th2、TBX21→Th1、FOXP3→Treg)已在 `tests/test_signed_module_effect.py`。
- **資料底層:** `metadata/suppl_tables/full_signed_DE/*.parquet`(每 downstream gene 帶符號 `log_fc`)—— 與 signed_module_effect 同源。
- **實作步驟:**
  1. 新模組 `src/3_DE_analysis/disease_reversal.py`,鏡像 `signed_module_effect.py`:
     `compute_reversal(signed_de, signature) → DataFrame`,`signature = {"up": [...], "down": [...]}`。
     反轉分數 = 對齊度(把 KD 的 signed profile 與 **−signature** 做點積 / 加權平均):
     up-gene 在 KD 下下降(log_fc<0)+ down-gene 在 KD 下上升(log_fc>0)→ 正的反轉分。
     `direction` 用門檻(比照 `DIRECTION_MIN_ABS_LOGFC=0.5`)分四類;無 measured 交集 → 該列缺席(`unknown≠0`)。
     每列帶 `n_signature_genes_hit` / `n_signature_total`。
  2. API:`POST /api/disease_reversal`(body 帶 signature)→ 全 target 反轉排序;`GET /api/disease_reversal/{gene}?signature=<builtin_id>`。builtin signature 可先用 repo 內既有的 autoimmune signature DE 表(`Th2_Th1_polarization_signature_DE`、`CD4T_aging_signature_DE` —— ROADMAP 標為「尚未 surface」的現成資料)。
  3. **決策牆定位:** 預設**描述性**,不進 `_stage()`/`_red_flags()`。以排序 / badge 呈現,**不 cap readiness**。(來源指示想把它當「判定維度」;建議先描述性上線,是否升級為決策維度列為 §8 開放決策 —— 那會需要 bump `ENGINE_VERSION` + 重新校準。)
  4. 若採用某個**固定 builtin signature** 當預設,才考慮新增卡片描述欄 `disease_reversal_direction`(需 §6 的 schema 流程);使用者上傳的 signature 一律走 per-request compute(如 disease-drug),不落卡片契約。
- **前端:** 新 dossier 面板 `views/dossier/DiseaseReversalPanel.tsx`;Clinical view 增 signature 選擇器(接 P3-M)。
- **測試:** `tests/test_disease_reversal.py` —— 已知活化子被 KD 應反轉某程式的 sanity anchor;若描述性,加惰性斷言。
- **誠實 caveat:** CRISPRi 敲低 ≠ 藥理抑制;signature 若來自別種細胞,顯性標 cell-context mismatch(沿用 `improvement_roadmap.md` OQ3 對 LINCS 的既有做法);覆蓋稀疏 → unknown。
- **成本:** 中(核心邏輯是 signed_module_effect 的泛化;前端 + signature 入口為增量)。

### 🥇 P0-E — 即時 PubMed 新穎性欄位

- **目標:** 每基因一個 `literature_count` + `novelty_tier`(well-studied / moderate / understudied / no-record),新穎性 = 文獻數的倒數/分位。這是 ShiftScope(#5 得獎)的核心軸。
- **現況:** `evidence/external_cache.py:112` `fetch_pubmed_literature(gene, context="CD4 T cell", max_results=10)` 已在打 NCBI E-utilities esearch+esummary,並快照進 `_evidence/<gene>.json` 的 `literature` 鍵。**但**它只取回前 10 筆 item,沒有抓 esearch 回傳的**總數** `esearchresult.count`,也沒萃取成分數。
- **資料底層:** NCBI esearch `count` 欄(已在打的同一支 API,零新相依)。
- **實作步驟:**
  1. 擴充 `fetch_pubmed_literature`:額外回傳 `total_count = esearchresult.count`;失敗 → `unknown`(不是 0)。
  2. 匯出時對「已覆蓋基因」算 cohort 分位 → `novelty_tier`。放在 **evidence 快照 + `/api/evidence/{gene}`**,不動卡片契約(避免 schema churn;見 §6 的取捨)。
  3. **覆蓋現實:** evidence 快取目前僅 21 基因(frontend README)。要讓新穎性普遍可用,需**離線批次**跑更多基因(尊重 `thresholds.py:MAX_EVIDENCE_GENES_PER_BUILD=50` 與 NCBI 速率限制)。此為真實成本/覆蓋註記,誠實標示未覆蓋基因為 `unknown`。
  4. **[G] 連帶:** `core/cards.py:36` 已有 `POSITIVE_CONTROLS` 已知 regulator 清單 → 前端「well-known」徽章,幫使用者過濾老面孔。
- **前端:** Explorer 新增 novelty 欄;Dossier `ClinicalLiteraturePanel` 顯示計數 + tier 徽章。
- **測試:** `tests/test_pubmed_novelty.py`,mock esearch count;斷言 fail 時是 `unknown` 非 0。
- **誠實 caveat:** 低文獻數可能是「真冷門」也可能「不重要」→ 必須配 P1-F 的二維象限(新穎性 × 效應)才有意義,不可單軸下結論。
- **成本:** 低。

### 🥈 P1-F — 新穎性 × 效應 二維象限圖

- **目標:** X=effect size(`ontarget_effect_size`/`max_abs_logFC`),Y=novelty(低文獻數)。右上象限=強效應+少研究=最值得測試(ShiftScope 精髓)。依 readiness call 上色。
- **現況:** `lib/drawFigure.ts:156` 的 `burden` 分支已是一張 2D 象限散點 + 線性擬合,**直接照抄的模板**;Plotly 已 lazy-load。
- **實作步驟:** 在 `drawFigure.ts` 加新分支(鏡像 burden);資料由 export script 帶(target 已有 effect,novelty 來自 P0-E)。註冊進 `views/Figures.tsx` + `data/gallery.ts`。可另做 dossier 內嵌迷你象限。因 portal 是靜態建置,資料經 `scripts/export_real_data.py` 流入。
- **測試:** 前端 `npm run build` type-check;資料形狀單元測試。
- **依賴:** P0-E。
- **成本:** 低。

### 🥈 P1-L — 已核准藥 / 臨床試驗連結

- **目標:** 每基因一個 disease-agnostic 的「有無已知/已核准藥 + 最高臨床期別 + trial_count」摘要 badge,接「靶點發現 → 可立即測試的藥」。
- **現況(多半已有):** `external_cache.py:439` `match_disease_drug_evidence()`(OT drugs × CT counts,含 `sources/topic13_clinicaltrials_flat.csv` 離線 fallback)+ `/api/disease-drug-evidence`(唯一 live route)已上線;`fetch_open_targets`(:181)已回傳 known drugs;卡片契約**已有** `nearest_success_drug` / `nearest_failure_or_warning`(`card_schema.py:61-62`);前端 `ClinicalTrial` 型別 + `ClinicalLiteraturePanel` 已存在。
- **實作步驟:**
  1. 從 `fetch_open_targets` 的既有回傳萃取 `known_drug_count` + `max_clinical_phase`,寫進 evidence 快照(per-gene,離線批次)。
  2. 前端 `TractabilityPanel`/`ClinicalLiteraturePanel` 加「已核准藥」徽章 + 連結;Explorer 加欄。
- **誠實 caveat:** 沿用既有函式的嚴格契約 —— known drug ≠ 此靶點以同機制可藥;某藥有 trial ≠ 針對此適應症有 trial(該函式刻意把兩者拆成兩個可查事實,不合併成分數,不做治療建議)。
- **成本:** 低。

### 🥈 P1-H — 網路中心性 / trans-effect 廣度

- **目標:** 每基因「敲低會牽連幾個下游基因」→ `trans_effect_breadth` + 分位。一箭雙鵰:高廣度=master-regulator 重要性訊號,**也**=broad-effect 副作用風險。
- **現況(半全新):** app 程式碼**無任何 centrality**(`mechanism_graph.py` 只組圖形;`grep` 確認無 networkx/betweenness);centrality 只在探索性 notebook(`DE_results_analysis_full.ipynb`)出現,不可 import。**但**卡片已有 `n_total_de_genes`(粗略 out-degree),`full_signed_DE` 有 KD→DEG 有向邊。
- **實作步驟:**
  1. **低成本版:** 把既有 `n_total_de_genes` 顯性呈現為 `trans_effect_breadth` + cohort 分位。零新計算。
  2. **中成本版:** 新批次模組 `src/3_DE_analysis/trans_network.py`,從 `full_signed_DE` 建 target×gene 有向表,算 de-dup 下游數 / hub 集中度(Gini,對齊 #234 CoDEGNet 的 top-5%→78% trans-effect 洞見);out-degree 純函式即可,不需 networkx;寫 overlay parquet(鏡像 `signed_module_effect.build()`)。
  3. **決策牆定位:** 先**描述性**(新欄、惰性斷言)。**開放決策(§8):** `broad_effect` 紅旗(`readiness.py:243`)目前用靜態 broad-effect 基因清單 —— 未來可否讓 `trans_effect_breadth` 超過校準門檻去**觸發** `broad_effect`?那會讓它變決策性,需 bump `ENGINE_VERSION` + 重新校準,列為獨立提案,不在第一版動。
- **前端:** Explorer 加 `trans_effect_breadth` 欄;Dossier 加「下游 footprint」stat;互動網路圖見 P3-I。
- **測試:** `tests/test_trans_network.py` —— 已知 master regulator 高廣度的 hub-recovery sanity;描述性則加惰性斷言。
- **成本:** 中(廣度低、完整網路中)。

### 🥉 P2-A — QC 前置閘門(Pre-flight QC Gate)

- **目標:** 上傳後、評分前,先顯示 cell count / donor 數 / guide 數 / 缺失率,不通過即紅色警告擋住 approve。強化 `unknown≠0` 的前端表現。
- **現況:** 上傳流程已有 context-match tier(`import_manager.py:186` `context_match_score`)+ `merge_status` 閘門(:467)+ `merge_import` 守門(`imports.py:147`);`thresholds.py` 有 min_cells=200 / min_de_genes=50;`/upload`(`upload_ui.py`)已呈現這些狀態。缺的是一個**評分前的視覺 QC 面板**把上述閘門形式化。
- **實作步驟:**
  1. 後端:在 preview/mapping 回應(`build_mapped_view`/`read_table_preview`)加 `qc_report`:n_cells 分布、n_donors(若有欄)、n_guides、逐欄缺失率、對門檻的 pass/fail。新函式 `qc_preflight(df, mapping)` 於 `import_manager.py`。
  2. 前端:`/upload` HTML 頁(`upload_ui.py`,即 live 工具,非凍結的 React portal —— 互動上傳的正確歸屬)加 QC 區,硬失敗時鎖住 approve 鈕。
- **誠實 caveat:** 顯性顯示缺失率、不 impute,對齊 `unknown≠0`。
- **成本:** 低。

### 🥉 P2-C — Claude 可測試假說(每卡一句)

- **目標:** 每靶點一句有來源根據的「可測試假說 + 建議驗證」,把靜態卡片變行動導向。
- **現況:** `core/readiness.py:314` `_next_step()` 已產「下一步驗證建議」(essential→…、broad_effect→…、uncertain_direction→…)—— **C 已部分達成**。
- **實作步驟:**
  1. **確定性模板優先(不在 compute 路徑放 LLM,守紀律 3):** 由既有欄位組裝更豐富的 NL 句 —— 方向(signed_module_effect)+ top module + `pathway_axis` + 既有 `next_validation_step` + context-specificity。可審計、可重現。
  2. **選配 LLM 版(延後):** 一個**離線批次** enrichment(如 evidence 抓取),寫快取的 `hypothesis` 字串,明確戳「model-generated, not evidence」,離線重生、版本化、不進決策路徑。開發期可用本 session 的 Claude/Anthropic API 預先產生,但必須快取 + 標示。
- **前端:** DossierHeader 一行 / 新「Hypothesis」chip。
- **誠實 caveat:** 標為假說非結論;確定性衍生可稽核。
- **成本:** 低。

### 🥉 P2-D — 自含 HTML 報告匯出

- **目標:** 一鍵下載單檔離線 HTML(含卡片+面板+provenance),給不用 portal 的合作者。
- **現況:** `/api/reports` + `/api/exports` 存在(`cards.py`);`generate_target_report.py` 是 682-byte stub。
- **實作步驟:** 充實 `generate_target_report.py` 成自含 HTML 模板(inline CSS、嵌入資料);經 `/api/reports/{gene}.html` 提供;Dossier export rail 加「下載報告」鈕。嵌入相同 caveat/provenance 戳。
- **成本:** 低。

### 🏅 P3-I — 互動因果網路圖

- **目標:** 選一基因 → 顯示其下游 DEG 網路,視覺化「動了會牽連什麼」,對安全性審查極有用。
- **依賴:** P1-H 的 network overlay。
- **實作步驟:** 前端新 dossier 面板,用 Plotly network scatter / 輕量 SVG 畫該 target 的下游鄰域(從 `full_signed_DE` / trans_network overlay)。靜態匯出:在 export script 預算每基因 ego-network。
- **成本:** 高。

### 🏅 P3-M — 疾病 signature 上傳路徑

- **目標:** 除 DE-table 上傳外,加 signature 上傳入口 → 跑 `compute_reversal` → 反轉排序表。把 portal 從固定 CD4 擴到任何疾病情境。
- **依賴:** P0-K。
- **實作步驟:** `/upload` live 工具加 signature 上傳分支,重用 P0-K 的 `POST /api/disease_reversal`。
- **成本:** 中。

---

## 5. 分波路線圖(對齊來源指示的三波)

| 波次 | 目標 | 內含 | 為什麼一起 |
|------|------|------|------|
| **第一波** | 補最缺的「方向性」+ 抄得獎核心 | **P0-K**(反轉核心,描述性)· **P0-E**(PubMed 新穎性)· **P1-F**(象限圖) | 三個一起直接對應來源指示的「動作1」,把系統從「靜態打分」升級成「有方向、有新穎性的發現引擎」 |
| **第二波** | 臨床說服力 + 安全性 | **P1-L**(藥物連結呈現)· **P1-H**(trans-effect 廣度) | 對臨床醫生與安全性審查最有感;L 幾乎已有,H 廣度版零新計算 |
| **第三波** | 誠實架構前端 + 可攜性 | **P2-A**(QC 閘門)· **P2-C**(假說,確定性版)· **P2-D**(HTML 匯出) | 強化既有誠實紀律的前端表現與可攜性,全部低成本 |
| **後續** | 視覺化 + 擴展適用範圍 | **P3-I**(網路圖)· **P3-M**(signature 上傳)· LLM 版 C | 較重,依賴前兩波的 overlay 與 API |

**建議先做第一波的 P0-E + P1-F**(最低成本、最快看到 ShiftScope 式價值),與 **P0-K 的描述性核心**並行 —— K 的後端邏輯與 E/F 無耦合,可平行推進。

---

## 6. 橫切關注點

### 6.1 卡片 schema 版本 vs. overlay 快照(關鍵取捨)

新訊號有兩個歸屬選擇:

- **落卡片契約**(`contracts/card_schema.py:CARD_COLUMNS`,`core/cards.py:504` 的 `out_cols`)→ 進 `target_cards.csv` → 必須 **bump `config/versions.py:CARD_SCHEMA_VERSION`**、重建卡片、重跑 `export_real_data.py --force`、更新 legacy dataset 註記(README §Target-discovery toolkit)。成本高、牽動 freeze。
- **落 evidence 快照 / overlay parquet**(per-gene JSON 或 per-target parquet,如 signed_module_effect)→ **不動卡片契約**、無 schema churn。

**建議:** E / L / K / H(廣度以外)先走 **overlay/快照**,把卡片契約變更保留給「已穩定且決策相關」的訊號。這對齊 `signed_module_effect.py`/`paper_regulators.py`/`autoimmune_clusters.py` 的既有做法(全部 overlay,不落卡片)。

### 6.2 provenance 與文件

每個新訊號:`fetched_at` + `source_version` 戳;登錄 `docs/provenance_registry.csv` + `docs/provenance_registry.md`;`docs/data_dictionary.md` 加欄位說明;若影響前端,更新 `frontend/webserver/README.md` 的資料來源清單。

### 6.3 MCP 工具 vs. portal 執行期快取

本 session 有 `mcp__PubMed__*`、`mcp__Clinical_Trials__*`、`mcp__bioRxiv__*` 工具 —— 但那是 **session-time**,**不是 portal runtime**。portal 執行期只用自己的離線快照(`fetch_pubmed_literature` 等),**開發期可用 MCP 工具預先填充快取**,但不可讓 portal 每請求打即時網路(唯一例外:既有 `/api/disease-drug-evidence`)。

### 6.4 網路政策(sandbox)

ROADMAP 記錄過 `clinicaltrials.gov` 被政策擋、離線 fallback 實際生效(`sources/topic13_clinicaltrials_flat.csv`)。PubMed(NCBI)/Open Targets 也可能被擋。**每個抓取路徑都需離線 fallback + 誠實 `source_status`(`ok` / `offline_snapshot` / `unavailable`),未覆蓋一律 `unknown`。**

### 6.5 前端靜態建置流水線

portal 是 `scripts/export_real_data.py` 一次性烘焙的靜態 bundle,**不呼叫 live API**。新卡片欄流程固定:
`readiness/cards → export_real_data.py 的欄位 allowlist(:382 readiness 欄 / :561 per-target 區塊)→ data/types.ts 的 `RealTarget`/`Readiness` → views/dossier/*Panel.tsx 或 Explorer.tsx 的 GRID`。互動/live 功能(QC、signature 上傳)走獨立的 `/upload` HTML 頁,不進凍結的 React app。

---

## 7. 風險與誠實護欄

1. **大雜燴風險(來源指示的核心警告)。** 對策:以 [K] 為靈魂,每個功能都能用一句話說清它服務 K 的哪一面(方向/新穎/可藥/安全),不為加而加。
2. **決策污染。** 新訊號誤入決策層會破壞既有校準。對策:紀律 1 的惰性斷言測試把關;任何決策性提案獨立版本化 + 重新校準。
3. **虛假覆蓋。** 新穎性/藥物/反轉在未覆蓋基因上必須 `unknown`,不可 0 或猜測。對策:紀律 2 + `source_status` 三態。
4. **CRISPRi ≠ 藥理。** K/L 特別容易被過度解讀成「可治療」。對策:沿用既有 caveat 文案,UI 每處標「研究用假說,非臨床軟體」。
5. **schema/freeze 破壞。** 落卡片契約會牽動 freeze 測試(`test_freeze_unified.py`)。對策:§6.1 優先 overlay,契約變更走完整版本流程。
6. **稀疏樣本的假信心。** 反轉/廣度的 1-gene 平均不可當強支持。對策:比照 signed_module_effect 攜帶 `n_hit`/`n_total`。

---

## 8. 待決策的開放問題

1. **[K] 要不要升級為決策維度?** 第一版建議純描述性(不 cap readiness)。若要讓 `reverses/worsens` 影響判定,需 bump `ENGINE_VERSION` + 對已知 anchor 重新校準 —— 是否要做、何時做?
2. **[H] trans_effect_breadth 要不要餵 `broad_effect` 紅旗?** 目前紅旗用靜態清單。用資料驅動的廣度門檻取代/補充,需校準門檻並驗證不誤傷 master regulators(如 MED12 案例)。
3. **新穎性 evidence 快取要擴到幾個基因?** 21 → 全 7,249?受 NCBI 速率與 `MAX_EVIDENCE_GENES_PER_BUILD=50` 限制,需分批 + 時間預算。先擴到 Explorer 預設可見的高 grade 子集?
4. **builtin 疾病 signature 用哪些?** repo 內 `Th2_Th1_polarization_signature_DE` / `CD4T_aging_signature_DE` 現成但需確認方向定義;或等使用者自帶(P3-M)。
5. **[C] 假說要不要上 LLM 版?** 確定性模板零風險先上;LLM 版需離線批次 + 明確「generated ≠ evidence」標示 —— 是否納入本輪?

---

## 附錄:一頁對照(給實作者)

| 我要做的事 | 改哪裡 |
|------|------|
| 加一個描述性卡片欄 | `core/cards.py:504` `out_cols` + `contracts/card_schema.py:32` `CARD_COLUMNS` + bump `config/versions.py:29` + `export_real_data.py:382/561` + `data/types.ts` + 對應 Panel |
| 加一個 overlay 訊號(不動契約,建議) | 新模組鏡像 `signed_module_effect.py` + 新 router 鏡像 `api/routers/signed_module_effect.py` + `export_real_data.py` per-target 區塊 |
| 加一個 readiness 域 | `core/readiness.py` 加 `_helper()` + per-row(:452)+ domains dict(:497);決策性才動 `_stage()`(:301)/`_red_flags()`(:228) |
| 加一個 2D 象限圖 | `lib/drawFigure.ts:156` 鏡像 `burden` + `views/Figures.tsx` + `data/gallery.ts` |
| 加一個 dossier 面板 | `views/dossier/XPanel.tsx` + 在 `views/Dossier.tsx` 組合 |
| 加一個域/欄測試 | 鏡像 `tests/test_translation_capped_by.py`(含惰性斷言)或 `tests/test_golden_file.py` |
| 改門檻 | `config/thresholds.py`(唯一真值來源) |
