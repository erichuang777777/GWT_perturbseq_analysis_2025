# 可重現性 Dossier — CD4 T-cell Perturb-seq 標的發現工具

**目的**:讓第三方能(1)完整看懂所有檔案、(2)依處理順序重建 pipeline、(3)自行驗證正確性。
**基準**:`main` @ `ee5f9a5`(含本 session 兩波開發 PR #21 / #22 + 平行 session PR #23/#24)
**日期**:2026-07-09 · **語言**:繁體中文(識別碼/路徑/指令用英文)
**驗證狀態**:全 pytest **214 passed, 8 skipped**;下列所有 known-answer 皆在真實資料上實測重現(見 §6)。

---

## 0. 一頁總覽:資料如何流動

```
[OAK 單細胞 .h5ad]  ← BLOCKED(需 Stanford OAK 資料 + SLURM/pertpy,不在 repo)
   │  make_pseudobulk.py → run_DE_chunk.py → merge_DE_results.py
   ▼
◆ metadata/suppl_tables/DE_stats.suppl_table.csv  ← 第三方重現「起點」(COMMITTED)
   │  (+ guide_kd / sgrna_library / sample_metadata / drug benchmark 皆 committed)
   ▼
[core/cards.py::build_cards_frame]  →  target_cards.csv (39 欄)  +  metadata.json(provenance)
   │           ▲ 疊加 overlays(gnomAD/GTEx/gene-lists/benchmark)
   ▼
[core/readiness.py::compute_readiness]  →  readiness_call / R0–R3 / red-flag caps  ← 「決策」層
   │
   ▼
[描述性疊加層(本 session 新增,絕不進決策)]
   concept_annotation · stimulation_switch_explorer · robust_ranking
   · genetic_double_support · triage_view
   │
   ▼
[FastAPI(api/app.py + routers/)]  →  ~38 endpoints  →  [Streamlit dashboard]
```

**重現邊界(關鍵)**:`DE_stats.suppl_table.csv` **之前**的所有步驟(原始單細胞 → DE)因需要 OAK 單細胞資料 + SLURM/pertpy 算力而**無法在此重跑**,但腳本與 config 全部 committed、**方法完全可稽核**。`DE_stats` **之後**的所有步驟(cards → readiness → 描述性層 → API/dashboard)**完全可在 repo 內重現**,起點檔案已寫死於 `src/3_DE_analysis/config/settings.py`。

---

## 1. Stage 0–4:原始單細胞 → DE_stats(BLOCKED,可稽核不可重跑)

`.h5ad`/`.h5mu` 全域 git-ignore,repo 內無任何被追蹤的 `.h5ad`。腳本全 committed。

| # | 檔案 | 角色 | 輸入 → 輸出 | 狀態 |
|---|---|---|---|---|
| 0 | (OAK) `{datadir}/{experiment}/tmp/*.postQC.h5ad`;`src/utils.py::_convert_oak_path`(`/oak/…`→`/mnt/oak/…`) | 原始 post-QC 單細胞計數 + sgRNA 指派 | 上游 `src/1_preprocess/` 產出 | **BLOCKED**(OAK) |
| 1 | `src/3_DE_analysis/make_pseudobulk.py` | 單細胞 → pseudobulk(sum counts / sample) | `.h5ad` + sample_metadata → `*.DE_pseudobulk.h5ad` | **BLOCKED** |
| 1b | `src/3_DE_analysis/prep_DE.ipynb` | 選基因、標 `keep_for_DE`、切 chunk | pseudobulk → `DE_test_genes.*.txt` / `DE_target2chunk.*.csv.gz` | **BLOCKED** |
| 2 | `src/3_DE_analysis/run_DE_chunk.py` + `MultiStatePerturbSeqDataset.py` | DE 引擎(pertpy `PyDESeq2`),design `~ log10_n_cells + donor_id + target`,逐 condition × chunk;控制組 `NTC` | pseudobulk + chunk → `DE_results.{cond}.chunk_{ix}.csv.gz`(+ confounders / MASH) | **BLOCKED**(SLURM + pertpy env) |
| 3 | `src/3_DE_analysis/merge_DE_results.py` | pivot chunk → target×gene AnnData(layers: baseMean/log_fc/lfcSE/p_value/adj_p_value[/MASH]) | chunk CSV + `metadata/sgRNA_library_curated.csv`(committed) → `merged_DE_results.h5ad` | **BLOCKED** |
| 4 | **`metadata/suppl_tables/DE_stats.suppl_table.csv`** | per-target×condition 摘要 = **重現起點** | 由 `merged_DE_results.h5ad` 經分析 notebook 產出 | **COMMITTED** |

**DE_stats 實測**:33,984 行(33,983 資料列)× 20 欄;11,526 unique targets(`target_contrast`=Ensembl ID,`target_contrast_gene_name`=symbol),3 條件(Rest/Stim8hr/Stim48hr)。

**config 參數(可稽核)**:`DE_config_full.yaml` — `min_replicates:3`、`min_cells_per_guide:5`、`n_hvgs:10000`、`chunk_size:50`、`chunk_split_seed:1423`、`design_formula: ~ log10_n_cells + donor_id + target`。

### 其他 committed 支援表(cards 建立需要)
| 表 | 路徑 | 行數(含 header) | 角色 |
|---|---|---|---|
| guide KD | `metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv` | 73,766 | 每 guide 對 NTC 的 KD t-test |
| sgRNA library | `metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv` | 31,110 | sgRNA 註釋 |
| sample metadata | `metadata/suppl_tables/sample_metadata.suppl_table.csv` | 12 | donor×condition 驅動 `batch_sensitivity_flag` |
| drug benchmark | `sources/topic05_successful_drug_benchmarks.csv` | 13 | 核准藥 benchmark 軸 |
| gene_id↔name | `metadata/sgRNA_library_curated.csv` | 27,273 | merge 用映射 |

---

## 2. Stage 5:DE_stats → target_cards(可重現)

- **入口**:`src/3_DE_analysis/core/cards.py::build_cards_frame(de_df, guide_df, lib_map, benchmark, min_cells=200, min_de_genes=50, schema="gwt", sample_meta=None)`。
  `build_target_cards.py` 是 flat-import + CLI shim(API 子程序呼叫的就是它)。
- **輸入**(全由 `config/settings.py` 解析,anchored 到 `REPO_ROOT=parents[3]`):DE_stats、guide_kd、sgrna_library、sample_metadata、drug benchmark、`metadata/gene_lists/*` + `metadata/immune_effector_genes.csv`。
- **委派邏輯**:`core/kd_status.py`(KD 分級,floor 0.001,`kd_status/v2`)、`core/scoring.py`(grade 1–4 + `score_cap_reasons`)、`config/thresholds.py`(所有數值 gate)、`common/coerce.py`。
- **輸出**:`target_cards.csv`(39 欄);`metadata.json` 僅由 API build route 的 `deps._persist_metadata` 產出(見 §5)。

**39 欄分組**(`contracts/card_schema.py::CARD_COLUMNS`,`card_schema/v2`):Identity(3)、DE 量/計數(8)、顯著/方向(3)、穩健/複製(5:含 `replicate_pass_flag`/`crossdonor_*`/`crossguide_correlation`/`n_donors`)、guide-KD(5)、condition/batch(3:含 `batch_sensitivity_flag`/`condition_specificity_zscore`)、生物/臨床軸(4:含 `effect_direction_flip_flag`)、benchmark(2)、grade+provenance(3)、局部成藥/安全 overlay(3:`druggable_class`/`tractability_modality`/`safety_note`)。

---

## 3. Stage 6:Overlays 與**真實覆蓋率**(疊加在 11,526 targets 上)

| 來源 | 檔案 | 檔內基因 | 交集 11,526 | % | 性質 |
|---|---|---|---|---|---|
| gnomAD constraint | `sources/target_tool_cache/_overlays/gnomad_constraint_seed.csv`(v2.1.1 by-gene 全基因組,LOEUF 門檻 0.6) | 19,155 | 11,267 | 97.8% | 全量 |
| GTEx 組織廣度 | `sources/target_tool_cache/_overlays/gtex_per_tissue.parquet` | 9,718 | 5,266(Ensembl)/5,358(symbol) | 45.7% | 實質 |
| 成藥性 gene-lists | `metadata/gene_lists/*`（15 檔）| 10 類 union 3,290 | 1,551 | 13.5% | 中等 |
| LINCS | `sources/target_tool_cache/_lincs/*`(shortlist 15,covered 4;demo 978×4) | 15 | 15 | 0.1% | **demo** |
| 概念模組 seed | `sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv`(20 模組) | 115 | 106 | 0.9% | 策展 |
| 疾病關聯(模組正典) | `src/6_functional_interaction/**results**/disease_gene_associations_detailed.csv`(**13 疾病**,7,527 列) | 2,989 | 1,977 | 17.2% | 實質 |
| ⚠ 非正典 | `src/6_functional_interaction/autoimmune_analysis/…`(17 疾病)**模組不用它** | — | — | — | — |
| 族群 LoF 負荷 | `src/8_lymphocyte_counts_LoF/input/Backman_LymphocyteCount_*.tsv`(18,543,key `ensg`) | 18,543 | 11,296 | 98.0% | 實質 |

**內部(篩選自產)欄位覆蓋**:effect size / DE breadth / batch flag / condition-specificity / direction-flip 皆 **100%**;cross-donor 14.1% / cross-guide 8.8%(實驗設計稀疏,誠實以 NaN 呈現)。

---

## 4. Stage 7:Readiness 引擎(決策層)= `core/readiness.py::compute_readiness`

- **cwd-anchoring 修復**(本 session B):`_REPO_ROOT = Path(__file__).resolve().parents[3]`,CLI 預設路徑 anchored 到 repo root;載到 0 overlay 會 `RuntimeWarning`(僅 CLI)。
- **決策輸出**:`readiness_call`(advance/validate/watchlist/deprioritize)、`overall_readiness_stage`(R0–R3)、`red_flag_override`、`readiness_reasons`、`next_validation_step`。
- **餵進 call 的四個 domain**:`biology_causality_score`、`translation_score`、`tractability_score`、`human_genetic_support`。
- **Stage 邏輯**:R0 若 biology==0 或(essential 且 grade≤1);R3 若 biology≥3 且 translation==5 且(tractability≥3 或 genetics=="yes");R2 若 biology≥3 且 translation≥3;R1 若 biology≥3;否則 R0。
- **紅旗封頂**(以 `min()` over `[deprioritize,watchlist,validate,advance]`):essential_gene / broad_effect / high_offtarget / kd_not_measurable → 封 watchlist;uncertain_direction / batch_confounded / kd_weak → 封 validate。(`kd_status=="not_assessed"` 刻意**不**當紅旗——unknown≠measured failure。)

**決策 vs 描述界線(關鍵)**:**只有**上述四 domain + 七紅旗會動 call。**所有安全/遺傳 overlay 皆描述性**:`safety_window_score`(GTEx)、`gnomad_constraint_flag/loeuf/pli`、`composite_safety_liability`、`genetic_support_confidence`、`trait_liability_similarity`、`disease_relevance`、`biomarker`、`clinical_feasibility`——並列呈現,**永不**進 `_stage()`/`_red_flags()`。

---

## 5. Stage 8:描述性疊加層(本 session 新增)

每個模組:**唯讀、additive、descriptive-only**,且各有一個 **inert 迴歸鎖**(把 view 欄位丟進 `compute_readiness`,輸出逐列不變 → 證明不可能改決策)。

| 模組 | 波 | 組合/讀取 | 主要輸出 | Endpoint | 鎖 |
|---|---|---|---|---|---|
| `concept_annotation.py` | 1·A | `individual_concept_profile.load_concept_modules`(20 模組) | `concept_modules`/`n_concept_modules`/`stimulation_gated`(NaN→None) | `/api/immune_ranked` | inert(compute_readiness 逐列同) |
| `stimulation_switch_explorer.py` | 1·C | 讀 `effect_direction_flip_flag`/`median_logFC` | `switch_type`/per-condition logFC/`switch_magnitude` | `/api/switches` | 讀既有旗標,非決策輸入 |
| `robust_ranking.py` | 2·D | 讀 `replicate_pass_flag`/cross-*/batch/cells | 三態 `robustness_tier`;filter-then-rank | `/api/robust_ranked` | inert;NaN→unresolved |
| `genetic_double_support.py` | 2·E | 組合 `evidence/disease.py`+`evidence/population.py` | `n_diseases`/`max_assoc`/`ci`/`caveat` | `/api/genetic_double_support` | 單邊不列;honest-fallback |
| `triage_view.py` | 2·F | 組合 D+E+concept+switch+safety | 多軸 composite + `total_score`/`n_axes` | `/api/triage` | inert;unknown safety 記 0 分 |

**Stage 9:API + Dashboard**
- `api/app.py`(version 0.2.0,12 OpenAPI tag groups,每 router 恰一 tag,`X-API/Engine/Schema-Version` header 於每筆回應)。
- 11 routers ~38 endpoints;5 個新 endpoint 皆 GET、皆 tagged、summary 標「descriptive」。
- Dashboard 8 tabs:新增「免疫優先 Immune Priority」(tab 6:immune_ranked + switches)、「整合 Triage」(tab 7:triage + robust_ranked);「Disease Translator」(tab 5)加遺傳雙證據小節。

**架構(依賴方向鐵律:內層不 import 外/脆弱層)**:
`config`(路徑/門檻/版本)→ `contracts`(schema)→ `common`(純 helper)→ `data`(loader)→ `core`(純引擎:cards/kd/scoring/readiness/calibration)→ `resolve` / `evidence`(脆弱外緣,offline-batch + TTL cache)/ `report` / `upload` → `api`(composition root,注入已載入的值/callable)。`core/` 只 import config/contracts/common/data。

**版本/provenance**(`config/versions.py` 單一真相):`ENGINE_VERSION=1.3.0`、`DATASET_VERSION=gwt_marson2025/bioRxiv-…696273v1`、`CARD_SCHEMA_VERSION=card_schema/v2`、`KD_THRESHOLD_VERSION=kd_status/v2`、`concept_set_version`=seed 檔 `name@mtime:size` 指紋。`metadata.json` 每 build 記 engine/schema/dataset/data version + 輸入檔指紋;API 每筆回應帶版本 header。

---

## 6. 驗證:如何自行重現(第三方照做)

### 6.1 環境與全測試
```bash
cd <repo-root>
python -m pytest -q            # 期望:214 passed, 8 skipped(8 skip 為 network/OAK-gated)
```

### 6.2 Known-answer 重現(在真實 cards 上,全部實測通過)
起點資料集(committed):`sources/target_tool_cache/a6bba17b-f194-4a50-8cf8-96e03eededd6/target_cards.csv`(33,983 列 / 11,526 targets)。
於 `src/3_DE_analysis/` 執行(`sys.path` 加該目錄):

| 模組 | 呼叫 | 期望值(實測✓) |
|---|---|---|
| A concept | `concept_annotation.build_gene_to_modules()` | PLCG1→`['M02']`;LAG3→`['M04','M18']`;NSD1 不在;annotate 後 106 targets 有≥1 模組 |
| C switches | `stimulation_switch_explorer.switch_report(cards)` | `n_true_sign_flip=27`、`n_on_off_switch=215`、total 242;IKZF1 在列 |
| D robust | `robust_ranking.robust_rank(cards, **kw)` | default `n_high_confidence=725`;lenient=1097;strict=400;`n_unresolved=30989`;total 33983 |
| E double-support | `genetic_double_support.double_support(cards)` | `n_double_support=161`;IL23R n_diseases=9、SH2B3=12、PTPN22=11;PTPN2 被排除;每列帶 caveat |
| F triage | `triage_view.triage_rank(cards, gnomad_overlay, gtex_overlay, top_n=40)` | winners 排名:PLCG1(2)/CD247(3)/PIK3R1(4)/IL4R(5)/ITK(6)/CD3E(18) 皆進 top40;LAT 被安全降級(>200) |

（F 的 overlay:`from evidence.safety_overlay import load_gnomad_constraint_overlay, load_gtex_safety_overlay`。）

### 6.3 端到端(API)
```bash
# 起 API(repo root)
uvicorn --app-dir src/3_DE_analysis api.app:app --port 8000
# 查詢(另一個 shell）
curl -s localhost:8000/api/health | jq .versions        # engine/dataset/schema 版本
curl -s "localhost:8000/api/robust_ranked/<dataset_id>?lenient=true" | jq '.n_high_confidence'   # → 1097
curl -s "localhost:8000/api/genetic_double_support/<dataset_id>" | jq '.n_double_support'          # → 161
curl -s "localhost:8000/api/triage/<dataset_id>?top_n=6" | jq '.targets[].target'
# 互動文件:localhost:8000/docs (Swagger) / /redoc
```

### 6.4 重建 cards(選擇性,從 committed 起點)
```bash
cd src/3_DE_analysis
python build_target_cards.py --de-stats ../../metadata/suppl_tables/DE_stats.suppl_table.csv \
  --guide-kd ../../metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv \
  --library ../../metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv \
  --output /tmp/target_cards.rebuilt.csv
# 應得 33,983 列 × 39 欄;與 committed cards 的統計欄位一致(overlay 覆蓋依 seed 檔)
```

---

## 7. 完整檔案清單(依處理順序)

**上游(BLOCKED,可稽核)**:`src/utils.py` · `src/1_preprocess/*` · `src/3_DE_analysis/{make_pseudobulk,run_DE_chunk,MultiStatePerturbSeqDataset,merge_DE_results}.py` · `prep_DE.ipynb` · `DE_config_full.yaml` / `DE_config_nodonor.yaml` · `submit_DE_chunked.sh`

**重現起點(COMMITTED)**:`metadata/suppl_tables/{DE_stats,guide_kd_efficiency,sgrna_library_metadata,sample_metadata,K562_comparison}.suppl_table.csv` · `metadata/sgRNA_library_curated.csv` · `sources/topic05_successful_drug_benchmarks.csv`

**核心引擎**:`src/3_DE_analysis/config/{settings,thresholds,versions}.py` · `contracts/{card_schema,concept_schema,interfaces}.py` · `common/{coerce,degrade,evidence_grading,overlay_lookup,timeutil}.py` · `data/loaders.py` · `core/{cards,kd_status,scoring,readiness,calibration}.py` · `build_target_cards.py`

**Overlays / evidence**:`sources/target_tool_cache/_overlays/{gnomad_constraint_seed.csv,gtex_per_tissue.parquet}` · `metadata/gene_lists/*`(15) · `sources/target_tool_cache/_lincs/*` · `sources/topic15_…seed_modules.csv` · `src/6_functional_interaction/results/disease_gene_associations_detailed.csv` · `src/8_lymphocyte_counts_LoF/input/*.tsv` · `evidence/{disease,population,safety_overlay,lincs_reference_cache,pathway_cache,mechanism_graph,external_cache,registry}.py`

**描述性層(本 session)**:`src/3_DE_analysis/{concept_annotation,stimulation_switch_explorer,robust_ranking,genetic_double_support,triage_view}.py`

**API / 前端**:`src/3_DE_analysis/api/{app,deps}.py` + `api/routers/*`(11) · `frontend/dashboard/target_card_dashboard.py` + `pages/*`

**測試(24 個 `test_*.py`)**:known-answer/inert-lock 見 §5、§6;含 `test_golden_file.py`、`test_join_integrity.py`、`test_known_answer.py`、`test_empty_states.py`(四態 result_status)、`test_api_openapi.py`(tag 紀律)、以及 5 個新模組各自的測試。

**文件**:`docs/{REPRODUCIBILITY(本檔),def_followup_plan,sandbox_blocked_tasks,server_northstar,improvement_roadmap,data_dictionary,data_governance_checklist,next_phases_plan}.md`

---

## 8. 重現邊界總結

| 範圍 | 可重現? | 為何 |
|---|---|---|
| 原始單細胞 → DE_stats(Stage 0–4) | ❌ 可稽核不可重跑 | 需 OAK 單細胞資料 + SLURM + pertpy/PyDESeq2 env;`.h5ad` 全 git-ignore |
| DE_stats → cards → readiness(Stage 5–7) | ✅ | 起點檔全 committed 且寫死於 `config/settings.py` |
| 描述性層 + API + dashboard(Stage 8–9) | ✅ | 全唯讀、additive、descriptive-only,known-answer 已實測 |
| 外部 overlay(gnomAD 全量 v2.1.1;LINCS/機制圖 種子/demo) | gnomAD ✅ 全量,其餘 ⚠ | gnomAD 已換全基因組(`data_acquisition/build_gnomad_constraint_overlay.py`);LINCS/機制圖全量需外部網路/資料,見 `docs/sandbox_blocked_tasks.md` |

**貫穿保證(每一步都守)**:`unknown != 0`(缺資料誠實標 unknown,不補 0)· descriptive-vs-decision 分離(新欄位永不進 `readiness_call`)· never-fabricate · provenance 標記(版本 + 檔指紋)· 全 pytest 綠。
</content>
