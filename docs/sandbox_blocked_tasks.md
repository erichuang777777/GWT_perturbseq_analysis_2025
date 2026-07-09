# 需在其他環境執行的任務清單(本 sandbox 做不了)

**用途:** 本 sandbox 有兩個限制——(1) 對外網路只走 agent proxy,對多數第三方 API 會 403;(2) 沒有掛載單細胞原始資料(Stanford OAK)、也沒有大算力。以下每一項都因這兩個限制之一而無法在此完成,需你帶到有網路/有 OAK 掛載/有算力的環境跑。每項列出**資料來源、計算方式、目標、現況、產出後如何放回 repo**。

**最後更新:** 2026-07-09 · 對照 `main` @ PR #18 合併後 + draft PR #21;數字為當日實測

**分類速覽:**

| # | 任務 | 卡在什麼 | 優先 |
|---|---|---|---|
| A | 全量 cell×gene DE 重跑(→ per-target 全基因組 signed DE 矩陣) | 沒有 OAK 單細胞原始資料 + 算力 | 🥇 解鎖最多下游 |
| B | gnomAD LOEUF/pLI 全量 | 網路(gnomAD 403) | 🥈 最小、schema 已定 |
| C | Open Targets 全量證據(含 PLCG1→Angioedema 驗證) | 網路(Open Targets 403) | 🥈 |
| D | 外部證據快取批次(ClinicalTrials/PubMed/bioRxiv) | 網路(production 走 raw requests) | 🥉 覆蓋率 |
| E | Reactome + STRING 機制圖快取批次 | 網路(403) | 🥉 覆蓋率 |
| F | LINCS/CMap 化合物參考 signature(A1b) | 資料不在 repo + 網路 | 🔬 研究性 |
| G | AlphaFold 結構(補齊 shortlist) | 網路(部分已由另一 session 完成) | 選配 |

**不在此清單(已完成、非阻塞):** GTEx per-tissue 安全窗 overlay(已重算、排除 CD4 情境組織、committed)、ADC 膜蛋白/可成藥性 overlay(committed)、UK Biobank LoF 負荷估計(in-repo)。

---

## 資料覆蓋盤點(2026-07-09 實測,基準 = 11,526 個標的基因 / 33,983 target×condition 列)

**內部(篩選自產)vs 外部(疊加的參考資料)——這條線也正好是 decision-vs-descriptive 的分界:內部統計餵 `readiness_call`,外部疊加一律描述性、永不進 call(唯一例外:membrane tractability overlay 會餵 `tractability_score`,實測改 70 個 call)。**

### 內部(廣度已到頂;稀疏處是實驗設計,非缺漏,誠實以 NaN 呈現)
| 欄位 | 非空覆蓋 |
|---|---|
| effect size / DE breadth / batch flag / condition specificity / direction flip | **100%** |
| cross-donor 相關 | 14.1%(需多 donor)|
| cross-guide 相關 | 8.8%(需多 guide)|

### 外部(多為誠實小種子,擴充 = 下方 A–G 任務)
| 來源 | 覆蓋 / 佔比 | 對應任務 |
|---|---|---|
| 成藥性 gene-list(15 檔) | 1,551 / 11,526 = **13.5%** | 擴充 gene-list |
| GTEx 組織廣度 | 5,358 / 11,526 = **46.5%** | 已 committed |
| gnomAD LOEUF/pLI | **15** / 11,526 = **0.13%** | **B** |
| 兩者皆有(composite safety) | 5 / 11,526 = 0.04% | B(隨 B 解)|
| 外部證據快照(trials+lit) | 21 gene / 11,526 = 0.18% | **C / D** |
| LINCS 參考簽章 | **4** gene(demo,已 committed)| **F**(擴充)|
| LINCS 化合物矩陣(老藥新用) | **0**(誠實不可用)| **F** |
| 機制圖 pathway 快照(_pathway/) | 15 entries(已 committed)| **E**(擴充)|
| per-target 全基因組 signed DE 矩陣 | **無**(只有聚合計數)| **A** |

### 缺口優先序(CP 值)
1. **A** — 全量 signed DE 矩陣:signature/LINCS 連結目前退化成單基因符號一致性,補上才對真實 target 有用(解鎖最多下游)。
2. **B** — gnomAD 0.13% → 全表:安全窗現在只對 15 個基因有意義,是最大覆蓋洞;schema 已寫死,純資料替換即生效。
3. **F** — LINCS 化合物矩陣 = 0:老藥新用/reversal 整層目前完全不能跑。
4. **成藥性 13.5%** — 495 個 advance 裡 376 個沒 druggable_class,只靠 genetics 過閘;擴充 gene-list 讓「advance」更有藥物把手意義。

*(以下 A–G 為各缺口的完整規格:資料來源 / 計算方式 / 目標 / 放回 repo 方式。現況數字已同步至 2026-07-09。)*

---

## A. 全量 cell×gene DE 重跑 → per-target 全基因組 signed DE 矩陣 🥇

這是你記得的「全量 cell gene 重跑」。**這是解鎖最多下游功能的一項。**

### 資料來源
- **單細胞原始 `.h5ad`**:放在 Stanford OAK,路徑經 `src/utils.py::_convert_oak_path` 轉換(`/oak/stanford/groups/pritch/...` → `/mnt/oak/...`),由各 pipeline 的 `--config` YAML 的 `datadir` + `experiment_name` 指定。**不在本 repo,且是單細胞規模,本 sandbox 無此掛載。**
- 細胞層 metadata:`metadata/sgRNA_library_curated.csv`(`perturbed_gene_id`↔`perturbed_gene_name`)。

### 計算方式(三步 pipeline,全部在 `src/3_DE_analysis/`)
1. **`make_pseudobulk.py`** — 讀單細胞 `.h5ad`,以 `sc.get.aggregate(..., func='sum')` 依 `sample_id`(= sample_metadata 欄位 + lane/guide/perturbed_gene 組合)聚合成 pseudobulk,輸出 `<experiment>_merged.DE_pseudobulk.h5ad`。
2. **`run_DE_chunk.py`** — 讀 pseudobulk,用 **pertpy `PyDESeq2`**(見 `MultiStatePerturbSeqDataset.py::run_target_DE`),design formula `~ log10_n_cells + target`(可由 config `run_de_params.design_formula` 覆寫),**逐 `culture_condition`(Rest/Stim8hr/Stim48hr)、逐 target chunk** 跑 DE,並額外對 `donor_id`/`log10_n_cells` 做 confound contrasts。輸出 `DE_results.*.csv.gz` chunk(欄位含 `baseMean, log_fc, lfcSE, p_value, adj_p_value, contrast, variable`);另可產 MASH 後驗(`MASH_results*.csv.gz`,`PosteriorMean/PosteriorSD/lfsr`)。
3. **`merge_DE_results.py`** — 把所有 chunk `pivot(values=stat, columns='variable'(=gene), index='target_contrast')`,組成 **target×gene 的 AnnData**,layers = `baseMean/log_fc/lfcSE/p_value/adj_p_value`(+ 若有 MASH 則 `MASH_PosteriorMean/SD/lfsr`),obs 標 `n_cells_target`,輸出 `<experiment>.merged_DE_results.h5ad`。

### 目標
產出**全基因組、per-target、帶基因身分的 signed DE 矩陣**。目前 repo 只有**聚合後**的 `metadata/suppl_tables/DE_stats.suppl_table.csv`(每 target×condition 一列,只有 `n_up_genes/n_down_genes` 計數 + `ontarget_effect_size` 單一標量,**沒有哪些 downstream 基因上/下調的身分**)。這個重跑會補上 gene-level 身分,直接解鎖:
- `signature_explorer.py` 目前被迫用「單基因 proxy signature」(module docstring 已誠實說明);有了 target×gene 矩陣,`build_query_signature` 可產真正的全基因組 query signature,connectivity 分析才有統計力。
- 任何需要 per-target downstream gene set 的功能(機制圖的 downstream 疊加、combination explorer 的真實基因重疊等)。

### 產出後如何放回 repo
merged `.h5ad` 是全量矩陣,**太大不該進 git**。建議:跑完後**萃取 shortlist(top15 候選標的)的 per-gene signed DE** 成一個精簡長表(如 `target_gene, downstream_gene, log_fc, adj_p_value, culture_condition`)放進 `metadata/suppl_tables/`,並在 `signature_explorer.py` 加一個 loader 讀它(取代單基因 proxy)。全量 `.h5ad` 留在 OAK,repo 只放萃取結果 + 一份 provenance(experiment_name / run_name / DE 版本)。

---

## B. gnomAD LOEUF/pLI 全量 🥈

### 資料來源
- **gnomAD constraint**:gnomAD GraphQL API(`https://gnomad.broadinstitute.org` 的 GraphQL 端點),或你先前提過的 `mcp-variants` 連結器 `gene_constraint`。本 sandbox egress 對 gnomAD 403。

### 計算方式
對全部 **11,526 個標的基因**(或至少 top15 shortlist)查 LOEUF、pLI,輸出成 CSV,**schema 必須是 `ensembl_id, gene_symbol, loeuf, pli`**(= `src/3_DE_analysis/evidence/safety_overlay.py::GNOMAD_REQUIRED_COLUMNS`,程式端已寫死驗這四欄)。Ensembl ID 用 `gene_identifier_resolver.load_resolver()` 解析(與現有種子檔一致)。

### 目標
用全量檔取代現有的 **15 基因種子** `sources/target_tool_cache/_overlays/gnomad_constraint_seed.csv`(2026-07-09 實測 = 15 gene,gnomAD v4 值)。**程式端 loader `load_gnomad_constraint_overlay()` 完全不用改**(同 schema),純資料替換即生效——`gnomad_constraint_flag`、`gnomad_loeuf`、`gnomad_pli` 三個描述性欄位覆蓋率從 15 個基因(0.13%)擴到全標的。門檻現為 **LOEUF<0.6**(gnomAD v4「constrained」;`overlay_lookup.LOEUF_LOSS_INTOLERANT_THRESHOLD=0.6`)。

### 備註
citation 審查發現:LOEUF<0.35 是 gnomAD **v2.1.1** 時代的「constrained」門檻;gnomAD **v4.0** 官方建議已改為 LOEUF<0.6。若你抓的是 v4 資料,考慮在 `safety_overlay.py` docstring 標明門檻版本(或改用 0.6),不要沿用舊門檻而不註記。

---

## C. Open Targets 全量證據(含 PLCG1→Angioedema 驗證)🥈

### 資料來源
- **Open Targets Platform GraphQL**:`https://api.platform.opentargets.org/api/v4/graphql`。本 sandbox egress 403。

### 計算方式
- `external_evidence_cache.py::fetch_open_targets(gene)` — 查 tractability buckets、genetic_association、safetyLiabilities(先 `_open_targets_resolve_ensembl_id` 解析 ID)。
- `match_disease_drug_evidence(gene, disease)` — 查 `target.drugAndClinicalCandidates` + `associatedDiseases`,再對每個候選藥用**藥名**去 ClinicalTrials.gov 查該藥在該適應症是否真有試驗。

### 目標
1. 補齊 `sources/target_tool_cache/_evidence/<gene>.json` 的 `open_targets` 區塊(目前多數是 `source_status: "unavailable"`)。
2. **特別要跑一次 PLCG1**:citation 審查標記——某 commit message 宣稱「PLCG1 now surfaces a real Angioedema safety liability」,但 repo 內唯一 committed 的 `PLCG1.json` 快照顯示 `open_targets: unavailable`,**沒有任何 artifact 佐證這個宣稱**。請在有網路的環境真跑 `fetch_open_targets("PLCG1")`,把結果 JSON commit 進 repo 當證據;若 Angioedema safety liability 確實存在就坐實它,若不存在就把該宣稱從歷史敘述中修正/移除。

---

## D. 外部證據快取批次預抓(ClinicalTrials / PubMed / bioRxiv)🥉

### 資料來源(production 模組用 raw `requests`,非 MCP)
- ClinicalTrials.gov:`https://clinicaltrials.gov/api/v2/studies`
- PubMed E-utilities:`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` + `esummary.fcgi`
- (bioRxiv 相關)
- **注意**:本 session 內我有 MCP 工具(`mcp__Clinical_Trials__*`、`mcp__PubMed__*`、`mcp__bioRxiv__*`)可以**查證**,但 `external_evidence_cache.py` 的 docstring 明訂它 production 時是**無 MCP 的純後端程序**,只能用 raw requests——而 raw requests 在本 sandbox 被 proxy 擋。所以 MCP 只能拿來驗證,不能寫進 shipped 模組。

### 計算方式
`build_evidence_for_genes(genes, force=False)` — 批次,尊重 30 天 TTL,每次 API endpoint 上限 `MAX_EVIDENCE_GENES=50`,走 `BackgroundTasks` 不擋 request thread。每來源獨立 `source_status`(ok/unavailable)。

### 目標
目前有 **21 個基因**有快照(2026-07-09 實測 `_evidence/*.json` = 21,含最初的 CD28/CD3E/CTLA4/IL2RA/ITK/JAK3/PLCG1/VAV1/ZAP70 + 後續擴充)。對 top15 shortlist(或全標的)批次跑,讓 dashboard 對更多標的能直接顯示 trials/literature/genetics,不必即時抓。

---

## E. Reactome + STRING 機制圖快取批次預抓 🥉

### 資料來源
- **Reactome**:`https://reactome.org/ContentService/data/mapping/ENSEMBL/<ensembl_id>/...`
- **STRING**:`https://string-db.org/api/json/network`(參數 `required_score=700`, `species=9606`)。
- 本 sandbox egress 對兩者 403。

### 計算方式
`pathway_network_cache.py::build_pathway_network_for_genes(ensembl_map, cache_dir)` — 對每個基因 `fetch_reactome_pathways` + `fetch_string_network`,存成 snapshot `sources/target_tool_cache/_pathway/<gene>.json`(有 TTL)。

### 目標
**repo 內目前有 15 個 `_pathway/` 快照**(2026-07-09 實測;已從「零快照」擴到少數 shortlist 落地)。要讓 `GET /api/mechanism-graph/{gene}` 對**任意**標的都能秒開,仍需在有網路環境對更多 shortlist / 全標的批次預抓並 commit snapshot(15 entries 遠不及 11,526 標的)。citation 審查已確認 CD3E→CD3D/CD3G/CD4/SYK、MED12→Mediator 成員在生物學上正確,只是缺落地的 artifact。

---

## F. LINCS / CMap 化合物參考 signature(A1b)🔬

### 資料來源
- **LINCS L1000 Level 5** 子集,或 **CLUE API**(`clue.io`)。**不在 repo**,且本 sandbox egress 擋。

### 計算方式
研究者本機下載 L1000 Level 5 化合物 signature 子集(或部署時連 CLUE),餵給 `signature_explorer.py::connectivity_score`(**已寫好,吃任意 `{gene: score}` 參考 signature,無需改碼**)。理想上搭配 A(全量 DE 矩陣)產出的真實全基因組 query signature 一起用。

**現況(2026-07-09)**:repo 已 commit 一份 **4 基因遺傳敲降 demo 簽章** `sources/target_tool_cache/_lincs/lincs_demo_signatures_4genes.csv`(PLCG1/SENP5/CCNC/PMVK,978 landmark × 4,來自 GSE106127 cancer cell line)——僅供方法學驗證。**化合物矩陣仍為 0**:`load_compound_signatures()` → `available:False`、`compound_reversal_matches()` → `n_compounds_scored:0`。本任務要補的正是化合物那一半。

### 目標
解鎖 `signature_explorer.py::match_reference_compounds`(目前是誠實的 `source_status: "unavailable"` stub)→ 回答「哪些化合物的 signature **反轉**這個標的的 downstream signature」(connectivity-map 反向連結,假設性化合物線索,附方法學 caveat,非療效宣稱)。

---

## G. AlphaFold 結構(補齊 shortlist)— 選配

### 資料來源 / 現況
- 另一個 session 已下載並 commit 5 個結構到 `docs/mvp-research/visualization/structures/`(CD247/CD3E/LAT/PLCG1/VAV1 的 `*_AF.cif`,來自 AlphaFold DB by UniProt ID)。
- 若要補齊其餘 shortlist 標的,從 AlphaFold DB(`https://alphafold.ebi.ac.uk/`)按 UniProt ID 下載對應 `.cif`。本 sandbox egress 擋。

### 目標
把 shortlist 其餘標的的預測結構補進同一資料夾,供視覺化模組用。優先度最低。

---

## 附:放回 repo 的共同原則(維持本專案紀律)

- **誠實 fallback 不變**:抓不到就 `source_status: "unavailable"` / `available: False`,不要用抓到的部分假裝全量;`unknown ≠ 0`。
- **schema 不要改**:B(gnomAD)、GTEx 等 overlay 的欄位契約程式端已寫死,產出檔對齊即可零改碼生效。
- **大檔留在外面**:全量 `.h5ad`(A)不進 git,只 commit 萃取結果 + provenance。
- **標時間與版本**:批次抓的證據沿用 `external_evidence_cache.py` 的 `fetched_at` + `source_version`;DE 重跑記 `experiment_name`/`run_name`/DE 引擎版本。
- **每次放回都跑 `pytest tests/ -q`** 確認既有 golden-file/known-answer 測試仍綠(schema 對齊的資料替換不應改變任何既有數字)。
