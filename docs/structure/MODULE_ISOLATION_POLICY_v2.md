# MODULE ISOLATION POLICY v2 — Perturbase Platform (whole-repo, unified)

**Repository:** erichuang777777/GWT_perturbseq_analysis_2025 · **main HEAD:** 0522a2df · **frozen:** 2026-07-12
**Supersedes:** `docs/mvp-research/closure_audit/MODULE_ISOLATION_POLICY.md` (pipeline-only) and `docs/mvp-research/pipeline/FREEZE_MANIFEST.csv` (data-only). This v2 covers the WHOLE repo — 9 taxonomy phases + a shared-infra layer, 97 modules, every file — grounded in the live tree.

## 0. The one rule that makes isolation work
Every module talks to its neighbours **only through file/API artifacts with a fixed schema**, never by importing another module's internals. File ownership is a **disjoint partition** — each repo file belongs to exactly one module. If your edit keeps a module's OUTPUT contract stable under its pinned freeze value, nothing downstream can break, and no other module's freeze value can move (the contamination guard enforces this).

**Freeze value:** `module_blob_sha256` = sha256 over sorted per-file git-blob-sha1 of the files the module exclusively owns. Verifier + generator = `scripts/validate_freeze_unified.py`. CI: `tests/test_freeze_unified.py`.

## Isolation recipe (any single module)
1. Find the module below; note its INPUT/OUTPUT contract + validation authority.
2. Edit only its directory. Read upstream via published artifacts, never internal imports.
3. Regenerate its output; re-validate against its authority only.
4. `python scripts/validate_freeze_unified.py --isolation <PHASE>::<MODULE>` — passes only if no OTHER module drifted.
5. Intentional contract change → re-pin (`--freeze`) + update its golden test in the same commit.

---

## P0 — Shared infrastructure (共用層)

### `shared_test_utils`
- **Directories:** tests/ + src/_misc/ + src/utils.py
- **Purpose:** 跨模組共用:pytest 測試套件、golden fixtures、src/utils.py、_misc 腳本
- **INPUT contract:** 各模組輸出(測試讀取)
- **OUTPUT contract:** pytest pass/fail;golden fixtures 為契約錨
- **Shared dependencies:** 所有 src/ 階段
- **ISOLATION RULE:** 共用層——修改須保守,漣漪及多模組;變更 golden fixture = 蓄意契約變更
- **Freeze:** `module_blob_sha256` · `77cd7f6aeceec573…` · 53 files · authority: pytest + golden fixtures


## P1 — Data aggregation (資料聲明與彙整)

### `01_raw_data`
- **Directories:** docs/mvp-research/pipeline/01_raw/data/
- **Purpose:** 01_raw 資料:DE_stats + sgrna/sample metadata suppl tables
- **INPUT contract:** external GWT bioRxiv suppl table + public S3; no upstream module
- **OUTPUT contract:** DE_stats.suppl_table.csv = 33983x16 (16-col dictionary pinned in README_01_raw.md)
- **Shared dependencies:** none (leaf); read by 02_curated only
- **ISOLATION RULE:** treat frozen; edit only to swap source then re-hash + re-pin all downstream
- **Freeze:** `module_blob_sha256` · `4c492f5a75a06d1a…` · 2 files · authority: FREEZE_MANIFEST.csv (01_raw) + reproducibility_audit/parity_01_02.csv (re-verified MATCH at HEAD)

### `01_raw_docs`
- **Directories:** docs/mvp-research/pipeline/01_raw/
- **Purpose:** Raw stage derivation spec (README) + EDA
- **INPUT contract:** describes 01_raw data contract
- **OUTPUT contract:** README_01_raw.md + EDA_01_raw.md (16-col dictionary authority)
- **Shared dependencies:** documents DE_stats schema for all downstream
- **ISOLATION RULE:** edit docs with any raw contract change; keep col dictionary in sync
- **Freeze:** `module_blob_sha256` · `7010faf9becf3077…` · 2 files · authority: self (blob-sha set)

### `marson2025_manifest`
- **Directories:** data/marson2025_data/
- **Purpose:** Manifest of Marson-lab GWT perturb-seq raw S3 drop (separate raw source for signed-DE track)
- **INPUT contract:** external S3 genome-scale-tcell-perturb-seq
- **OUTPUT contract:** manifest.csv = 32x6 file inventory (path/size/checksum)
- **Shared dependencies:** consumed by signed_de_application (h5ad extraction on GB10)
- **ISOLATION RULE:** edit only to re-issue manifest when S3 drop changes; re-hash on change
- **Freeze:** `module_blob_sha256` · `bcd572a8de295318…` · 1 files · authority: self (md5) vs S3 listing

### `metadata`
- **Directories:** metadata/
- **Purpose:** External reference tables, curated gene lists, sgRNA libraries, supplementary tables (reference-data warehouse)
- **INPUT contract:** external only (published paper suppl files, HPA/CORUM/GWAS catalog, Marson sgRNA library)
- **OUTPUT contract:** AS-IS heterogeneous reference collection; per-file schema owned by originating publication
- **Shared dependencies:** gene_lists/* & suppl_tables/* read by curation/enrichment/signed_de_application; sgrna_df_final.* cross-checked vs src/1_preprocess results
- **ISOLATION RULE:** edit only under metadata/; read-only inputs; replacing a source re-pins code_blob_sha + re-validate downstream consumers
- **Freeze:** `module_blob_sha256` · `24a8fb429d1130b8…` · 64 files · authority: self (dir blob-sha set); per-file schema = originating publication (metadata/README.md,data_sharing_readme.md)

### `sources`
- **Directories:** sources/
- **Purpose:** Literature/landscape research outputs + target-tool evidence/pathway/overlay cache; single collected source
- **INPUT contract:** external only (PubMed/OpenAlex/ClinicalTrials/LINCS/gnomAD/GTEx/HPA/Reactome)
- **OUTPUT contract:** AS-IS collection; no fixed row/schema contract; read-only opaque cache keyed by filename
- **Shared dependencies:** read-only by dashboard/target-card layer (_evidence/*.json,_pathway/*.json); _overlays/* also pinned in FREEZE_MANIFEST overlays
- **ISOLATION RULE:** edit only under sources/; re-pin code_blob_sha on any add/edit; cannot affect stages 01-04 (never read here)
- **Freeze:** `module_blob_sha256` · `2420097d26d27bf7…` · 57 files · authority: self (dir blob-sha set) + FREEZE_MANIFEST overlays rows


## P2 — Pre-processing (前處理)

### `02_curated_docs`
- **Directories:** docs/mvp-research/pipeline/02_curated/
- **Purpose:** Curated stage derivation spec (README) + EDA
- **INPUT contract:** describes 02_curated transform (passes_gate/logDE formulas)
- **OUTPUT contract:** README_02_curated.md + EDA_02_curated.md
- **Shared dependencies:** documents gate/logDE semantics for downstream
- **ISOLATION RULE:** edit docs with any curated contract change
- **Freeze:** `module_blob_sha256` · `d1b7599805f9893a…` · 2 files · authority: self (blob-sha set)

### `02_curated_targets`
- **Directories:** docs/mvp-research/pipeline/02_curated/data/
- **Purpose:** Type-normalise + gate flags; keep all 33983 rows; add passes_gate + logDE (columns-only)
- **INPUT contract:** 01_raw/data/DE_stats.suppl_table.csv (33983x16)
- **OUTPUT contract:** curated_targets.csv = 33983x18 (16 raw + passes_gate + logDE)
- **Shared dependencies:** raw schema; read by 03/04 and 05_visualization
- **ISOLATION RULE:** edit curated transform + README only; regenerate; confirm 33983 rows + MD5; do not touch 03/04
- **Freeze:** `module_blob_sha256` · `29998644ffcd4180…` · 1 files · authority: FREEZE_MANIFEST.csv (02_curated) + reproducibility_audit/parity_01_02.csv (supersedes policy 7b8fbe8c; re-verified MATCH)

### `03_processed_data`
- **Directories:** docs/mvp-research/pipeline/03_processed/data/
- **Purpose:** 03_processed 資料:effect_matrix + de_matrix + gate_passing_targets
- **INPUT contract:** 02_curated/data/curated_targets.csv (33983x18)
- **OUTPUT contract:** de_matrix.csv = 11526x4; columns ordered Rest->Stim8hr->Stim48hr; NaN-for-missing
- **Shared dependencies:** curated schema
- **ISOLATION RULE:** edit pivot transform + README; preserve col order + NaN semantics
- **Freeze:** `module_blob_sha256` · `40aec828a74e05d6…` · 3 files · authority: FREEZE_MANIFEST.csv (03_processed) + reproducibility_audit/parity_03.csv (supersedes policy 6b2ed5e5; re-verified MATCH)

### `03_processed_docs`
- **Directories:** docs/mvp-research/pipeline/03_processed/
- **Purpose:** Processed stage derivation spec (README) + EDA
- **INPUT contract:** describes pivot/subset transforms + condition ordering
- **OUTPUT contract:** README_03_processed.md + EDA_03_processed.md
- **Shared dependencies:** documents matrix shapes/col order for downstream
- **ISOLATION RULE:** edit docs with any processed contract change
- **Freeze:** `module_blob_sha256` · `44c9871302883efa…` · 2 files · authority: self (blob-sha set)

### `src/1_preprocess`
- **Directories:** src/1_preprocess/
- **Purpose:** Type normalisation, QC gating, guide-effect estimation, sgRNA->gene annotation
- **INPUT contract:** raw count matrices (S3/GB10, out of repo) + metadata/ tables + sample lists
- **OUTPUT contract:** CODE MODULE - freeze=git blob-sha set; no single data contract; committed results/*.parquet reproducible from code (canonical copy=metadata/sgrna_df_final.*)
- **Shared dependencies:** metadata/sgRNA_library_curated.csv, metadata/sgrna_df_final.*, environment.yaml, src/utils.py
- **ISOLATION RULE:** self-contained numbered stage; no sibling src/N_* imports; share via written artifacts
- **Freeze:** `module_blob_sha256` · `6b401829c48e9eef…` · 30 files · authority: self (dir blob-sha set); produced sgRNA table cross-checked vs metadata/sgrna_df_final.parquet

### `src/2_embedding`
- **Directories:** src/2_embedding/
- **Purpose:** NTC/cell embedding computation used downstream for integration
- **INPUT contract:** QC-d count matrices from stage 1 (out of repo)
- **OUTPUT contract:** CODE MODULE - freeze=git blob-sha set; no committed data contract (embeddings regenerated)
- **Shared dependencies:** environment.yaml (scanpy/pertpy); stage-1 outputs
- **ISOLATION RULE:** edit only under src/2_embedding/; consumes stage-1 read-only
- **Freeze:** `module_blob_sha256` · `0463e0438e246bf8…` · 2 files · authority: self (dir blob-sha set); no data pin (active/regenerated)

### `src/9_cell_integration`
- **Directories:** src/9_cell_integration/
- **Purpose:** Integrate cells across samples/donors; perturbation-response readouts; runtime YAML+manifest parameterised
- **INPUT contract:** user-supplied real data via manifest.template.csv + cell_integration.example.yaml (paths at run time)
- **OUTPUT contract:** CODE MODULE - freeze=git blob-sha set; no data contract (outputs run-specific per runtime manifest)
- **Shared dependencies:** environment.yaml; stage-1/2 outputs at run time
- **ISOLATION RULE:** edit only under src/9_cell_integration/; data binding via runtime manifest/YAML; never hardcode sibling paths
- **Freeze:** `module_blob_sha256` · `7c5174837e26fa69…` · 6 files · authority: self (dir blob-sha set); active cloud-dev code, no data pin


## P3 — Statistics & analysis (統計與分析)

### `cytokine_regulators`
- **Directories:** src/5_cytokine_regulators/
- **Purpose:** 找出調控細胞激素程式的擾動標靶並做後續分析(細胞激素受體焦點基因清單)
- **INPUT contract:** DE 統計 + cytokine_receptor_genes.txt(細胞激素受體焦點基因)
- **OUTPUT contract:** notebook 派生分析(cytokine_regulators_overview / followup);對應論文細胞激素調控子圖
- **Shared dependencies:** 上游 DE 統計;figure_map.md
- **ISOLATION RULE:** 僅編輯本資料夾。無固定資料輸出契約(notebook 探索),freeze = 程式碼 blob 集合。
- **Freeze:** `module_blob_sha256` · `5cb82d2d4b7339c3…` · 4 files · authority: code_blob_sha 定版(notebook + 焦點基因清單);無獨立資料契約

### `de_engine_and_backend`
- **Directories:** src/3_DE_analysis/
- **Purpose:** DE 統計引擎(pseudobulk→chunked DE→merge)+ target-card 契約 core/ + FastAPI 唯讀後端 api/ + contracts/(card_schema 39欄)、power/donor/guide robustness、K562 對照
- **INPUT contract:** raw/curated DE 資料(依 stage README)、DE_config_*.yaml、上游 layer tables + evidence/pathway 快取(唯讀)
- **OUTPUT contract:** pipeline data/*.csv(stages 1.1–1.4)+ card JSON(contracts/card_schema.py 39欄, kd_status∈{confirmed,weak,not_measurable,not_assessed}, grade 1–4)、HTTP/JSON API
- **Shared dependencies:** src/utils.py; environment.yaml; contracts/card_schema.py; tests/fixtures/golden_*.csv
- **ISOLATION RULE:** 各 src/N_* 子資料夾自足;不跨編號資料夾 import,只經寫出的 artifact 分享。後端內部可自由改寫,只要 card_schema JSON 契約不變。
- **Freeze:** `module_blob_sha256` · `86114d9bc271d448…` · 118 files · authority: pytest (test_api_openapi/test_triage_target_api/test_exports_provenance/test_join_integrity/test_golden_file) + contracts/card_schema.py:validate_cards; test_freeze_integrity.py

### `functional_interaction`
- **Directories:** src/6_functional_interaction/
- **Purpose:** 下游功能富集(GO)、條件/組織專一性、聚類、T活化調控子,與 Open Targets 自體免疫疾病關聯
- **INPUT contract:** 上游 DE/聚類結果;Open Targets 疾病基因(download_disease_genes.py)
- **OUTPUT contract:** results/ 聚類富集(clustering_nde75ntotal50_enrichment*.csv/parquet/xlsx)、cluster_autoimmune_enrichment_results.csv、疾病基因 barplot SVG
- **Shared dependencies:** 上游 DE schema;Open Targets API;下游「疾病轉譯」工具的來源之一
- **ISOLATION RULE:** 僅編輯本資料夾;疾病關聯匯出以檔案交付下游,不被下游 import。
- **Freeze:** `module_blob_sha256` · `46b15351b7ed1bca…` · 27 files · authority: code_blob_sha + 輸出檔 md5;Open Targets 富集可用 live API 重查驗證

### `level4_external_validation`
- **Directories:** docs/mvp-research/level4_external_validation/
- **Purpose:** 以獨立公開資料集正交交叉驗證 signed 排名(5 級驗證階梯之 L4):GWAS/Open Targets、STRING、GEO GSE318876
- **INPUT contract:** signed_ranking_v2(10,851;55-target shortlist)+ 外部 Open Targets/STRING/GEO GSE318876
- **OUTPUT contract:** track_a_gwas_genetic_association.csv(55×16)、track_b_string_partner_recovery.csv(15×7)、track_c_gse318876_target_evidence.csv(1235×12)、validation_target_set.csv(55×8)、level4_external_validation_figure.png
- **Shared dependencies:** signed_ranking_v2.csv(上游,唯讀);外部公開 DB;phenotype_matched_crosscheck.py
- **ISOLATION RULE:** 僅編輯本資料夾;唯讀消費 signed 輸出、產出自有 tracks — 與 stages 01–07 解耦。association≠causation 限制須保留。
- **Freeze:** `module_blob_sha256` · `6e96b2d5e7c6efd7…` · 7 files · authority: third-party recompute(15/15 numbers;live Open Targets 重查 TYK2/STAT3/CD3E)+ pytest test_phenotype_matched_crosscheck.py

### `lymphocyte_lof_burden`
- **Directories:** src/8_lymphocyte_counts_LoF/
- **Purpose:** Regulator-burden 相關分析對淋巴球數量;找各條件(Stim8hr/Stim48hr)核心基因及其調控子
- **INPUT contract:** input/ 外部 LoF burden 估計(Backman 2021 per-gene estimates、shet_10bins、gencode v41 gene map)
- **OUTPUT contract:** results/ core_genes_{cond}_{dir}.txt(4)、core_genes_enrich_analysis_results.csv
- **Shared dependencies:** 外部 Backman/gnomAD burden 資料;R 腳本(Regulator_burden_correlation_*.R)
- **ISOLATION RULE:** 僅編輯本資料夾;R 與 notebook 分析獨立於主 pipeline。
- **Freeze:** `module_blob_sha256` · `703ef34b27b6ad39…` · 14 files · authority: code_blob_sha + core-gene 清單/富集 md5;R×外部 burden 重算比對

### `ml_perturbation_prediction`
- **Directories:** src/10_ml_perturbation_prediction/
- **Purpose:** 刻意隔離的探索性 ML 實驗場:預測下游被影響基因(GenePert 風格基線、GEARS GNN、known-regulator 分類、real-features 基線);誠實負面報告
- **INPUT contract:** metadata/suppl_tables/full_signed_DE(205萬配對,10,851標的)、gate_passing_signed_DE
- **OUTPUT contract:** results/*_benchmark.json + *_README.md(基準結果,永不寫入 target_cards/readiness)
- **Shared dependencies:** 自有 requirements.txt(獨立 venv,不進 environment.yaml)
- **ISOLATION RULE:** 硬邊界:絕不 import src/3_DE_analysis production 路徑,production 也絕不 import 此目錄。輸出只寫本目錄 results/。GroupKFold 防洩漏、deterministic、unknown≠0。
- **Freeze:** `module_blob_sha256` · `eaf823bf357f8c8f…` · 19 files · authority: pytest (test_perturbation_prediction_benchmark/test_perturbation_prediction_ml) + benchmark.json 定版;決定性 seed 可重算

### `onek1k_external_analysis`
- **Directories:** src/7_1k1k_analysis/
- **Purpose:** 以外部 OneK1K 族群單細胞資料做 DE 與 pert2state 模型的比較/外部驗證
- **INPUT contract:** GWT 擾動效應 + 外部 OneK1K 族群單細胞資料
- **OUTPUT contract:** notebook + 腳本鏈 (process.py→1k1k_analysis.py→compare.py→plot.py) 派生比較(無 committed 資料輸出)
- **Shared dependencies:** GWT 擾動效應 artifact;外部 OneK1K 資料
- **ISOLATION RULE:** 僅編輯本資料夾;純外部驗證,不寫回主 pipeline。無 committed 資料契約。
- **Freeze:** `module_blob_sha256` · `c7a46adf74106db6…` · 7 files · authority: code_blob_sha 定版(notebook + 4 個 .py 腳本);外部資料重算比對

### `polarization_signatures`
- **Directories:** src/4_polarization_signatures/
- **Purpose:** Th1/Th2/Treg/Th17 極化差異表現(DE)與極化預測模型;discovery/replication 比較、外部對照(Ota/Arce/Hollbacher/Oh/Yazar)
- **INPUT contract:** src/2 嵌入 + DE 統計;外部對照資料集
- **OUTPUT contract:** results/ 內各極化 DE CSV、polarization_model_coefs.csv、Ota sweep 評估、單細胞 signature/volcano SVG
- **Shared dependencies:** 上游 DE 統計 schema;figure_map.md(論文極化圖)
- **ISOLATION RULE:** 僅編輯本資料夾;讀上游只透過已發佈 artifact。輸出為描述性 DE 結果表,非 pipeline stage 契約。
- **Freeze:** `module_blob_sha256` · `06ecc7c78d709416…` · 32 files · authority: code_blob_sha 定版 + 描述性輸出檔 md5(non-pipeline;第三方可用相同外部資料重算 DE 比對)

### `signed_de_application`
- **Directories:** docs/mvp-research/signed_de_application/
- **Purpose:** 補上 count-only pipeline 缺的基因層次 signed 方向性(blindspot 3):scale-free 極性排名(directionality_index)、footprint 類別、corrected-background 富集、LINCS 一致性
- **INPUT contract:** Marson-lab GWCD4i.DE_stats.h5ad(S3, 15.63GB, GB10 萃取)— 獨立 raw source,非 33,983 列表
- **OUTPUT contract:** signed_ranking_v2.csv(10,851×28)、downstream_enrichment_v2.csv(12,975×10)、lincs_concordance.csv、signed_application_figure.png
- **Shared dependencies:** producing script reproduce_signed_tracks.py;DATA_DICTIONARY.md;reactome snapshot
- **ISOLATION RULE:** 僅編輯本資料夾 + reproduce_signed_tracks.py。獨立於 stages 02–07(不同 raw input)— 可重建 signed tracks 不動主 pipeline。directionality_class(legacy)/expression_artifact_flag(不可重算)caveat 須保留文件化。
- **Freeze:** `module_blob_sha256` · `32a260cff0b38b0b…` · 6 files · authority: GB10_SIGNED_DE_VALIDATION.md coverage 對源 README(2,056,424 sig pairs;10,851 標的;28,757 target×cond 對主 pipeline n_up/n_down/n_total 全等 max diff 0)+ MASTER_REVIEW_SUMMARY.md 30/34 spot-check

### `stage04_statistical_doc`
- **Directories:** docs/mvp-research/pipeline/04_statistical/
- **Purpose:** 統計摘要層(pipeline stage 04):全域 KV 摘要 + 逐條件擾動方向統計;可重現性驗收點
- **INPUT contract:** 02_curated/curated_targets.csv(直接讀 curated,非 processed)
- **OUTPUT contract:** data/summary_statistics.csv(18 metric×{metric,value})、data/condition_stats.csv(3 條件×4);README + EDA 派生文件
- **Shared dependencies:** curated schema;cross_validation_results.csv(每 metric calc_logic)
- **ISOLATION RULE:** 僅編輯本 stage 摘要 transform + README。此層為 R×Python cell-by-cell 0-mismatch;任何編輯須在兩語言重現。加 metric = 追加列 + 擴充 R 與 Python 實作 + 重新定 checksum。
- **Freeze:** `module_blob_sha256` · `c5b96f60af0f1370…` · 5 files · authority: R×Python parity(stats_parity_report.md 24/24 PASS,唯一非零差 4.44e-16)+ third_party_verification.md(18-metric core 兩語言 md5 match)+ _validation/cross_validation_results.csv

### `pipeline_validation_audits`
- **Directories:** docs/mvp-research/pipeline/reproducibility_audit/ + docs/mvp-research/pipeline/_validation/ + docs/mvp-research/pipeline/methodological_validation/
- **Purpose:** 統計可重現性稽核:R×Python parity、third-party recompute、方法學驗證
- **INPUT contract:** 上游 04_statistical 輸出
- **OUTPUT contract:** parity/verification 報告
- **Shared dependencies:** 04_statistical
- **ISOLATION RULE:** 僅編輯稽核資料夾;為 P3 的 validation authority 錨點
- **Freeze:** `module_blob_sha256` · `d5776636d02808e7…` · 19 files · authority: R×Python parity + third-party recompute

### `analysis_products`
- **Directories:** docs/mvp-research/pipeline/kinetics_avoid/ + docs/mvp-research/pipeline/blindspot_fixes/ + docs/mvp-research/pipeline/delivery/ + docs/mvp-research/pipeline/delivery_decision/ + docs/mvp-research/pipeline/context_specific/
- **Purpose:** 下游分析產物:kinetics/avoid 分層、盲點修復、遞送決策、context-specific shortlist
- **INPUT contract:** gate-passing targets + 統計
- **OUTPUT contract:** 分析 csv/md 產物
- **Shared dependencies:** 04_statistical
- **ISOLATION RULE:** 僅編輯各分析資料夾;產物為衍生,不改上游契約
- **Freeze:** `module_blob_sha256` · `6a627d9b7523f45b…` · 22 files · authority: pinned md5 + 第三方重算

### `perturbase_review`
- **Directories:** docs/mvp-research/perturbase_review/
- **Purpose:** 平行審查交付:review summary、源論文/相關論文清單、可重現 bundle
- **INPUT contract:** 各分析輸出
- **OUTPUT contract:** 審查 md/csv
- **Shared dependencies:** —
- **ISOLATION RULE:** 僅編輯 review 資料夾
- **Freeze:** `module_blob_sha256` · `a6c4782f94a8a730…` · 13 files · authority: 審查記錄

### `disease_expansion`
- **Directories:** docs/mvp-research/disease_expansion/
- **Purpose:** 621 基因三源疾病擴充 + top50 結構資產
- **INPUT contract:** signed 排名 + 外部 API
- **OUTPUT contract:** 擴充 csv/zip
- **Shared dependencies:** signed_de_application
- **ISOLATION RULE:** 僅編輯擴充資料夾
- **Freeze:** `module_blob_sha256` · `344f21c3ed4fb99b…` · 11 files · authority: 三源交叉核對

### `closure_audit`
- **Directories:** docs/mvp-research/closure_audit/
- **Purpose:** 收尾三軸稽核:後端完整性、前端覆蓋、順序驗證矩陣、舊隔離政策
- **INPUT contract:** 全模組
- **OUTPUT contract:** 稽核 md/csv
- **Shared dependencies:** —
- **ISOLATION RULE:** 僅編輯稽核資料夾;舊 MODULE_ISOLATION_POLICY.md 由 v2 取代
- **Freeze:** `module_blob_sha256` · `981119e023ede5da…` · 8 files · authority: 稽核記錄


## P4 — Figure & visualization (視覺化與圖表)

### `figure_metadata`
- **Directories:** metadata/figure_map.md + metadata/figure_palettes.yaml
- **Purpose:** 圖表 metadata:figure_map.md(圖-源對照)+ figure_palettes.yaml(配色)
- **INPUT contract:** none (authoritative)
- **OUTPUT contract:** figure_palettes.yaml palette keys + figure_map.md IDs + figure_guide.md rules
- **Shared dependencies:** consumed by 05_visualization & visualization
- **ISOLATION RULE:** palette edit is CROSS-MODULE (shifts all figure colors); re-render+re-audit all after edit
- **Freeze:** `module_blob_sha256` · `34d7da8de2841f80…` · 2 files · authority: visual-audit (color/style regression)

### `viz_design_catalog`
- **Directories:** docs/mvp-research/visualization/
- **Purpose:** design-side chart catalog + interactive/3D HTML prototypes + 15 AlphaFold cif
- **INPUT contract:** design intent + processed schemas (read-only)
- **OUTPUT contract:** chart_catalog.csv (53), interactivity_spec.csv, STAGE1/2/3 HTML+MD, figures/*.png, structures/*.cif
- **Shared dependencies:** none downstream (pure presentation)
- **ISOLATION RULE:** edit under docs/mvp-research/visualization/ only; cannot affect pipeline numbers
- **Freeze:** `module_blob_sha256` · `6d306bc296cfe121…` · 29 files · authority: visual-audit + chart_catalog completeness

### `viz_pipeline_05`
- **Directories:** docs/mvp-research/pipeline/05_visualization/ + docs/mvp-research/pipeline/05_visualization/refined_figures/
- **Purpose:** 53-chart refined figure render stage; render-only, no new statistics
- **INPUT contract:** stages 02/03/04 tables (read-only) + figure_palettes.yaml
- **OUTPUT contract:** refined_figures/<ID>.png x53 + REFINED_CATALOG_53.csv (53x6)
- **Shared dependencies:** upstream 02/03/04 schemas; figure_registry.csv
- **ISOLATION RULE:** edit under 05_visualization/ only; cannot alter upstream numbers; re-audit 53 IDs
- **Freeze:** `module_blob_sha256` · `28ba38e7fa7473bd…` · 57 files · authority: visual-audit vs figure_registry.csv

### `viz_pipeline_06_animation`
- **Directories:** docs/mvp-research/pipeline/06_animation/
- **Purpose:** presentation animation layer; 1:1 timed reveal of stage-05 statics; AS-IS (doc only on main)
- **INPUT contract:** stage-05 statics + 02/03/04 (read-only)
- **OUTPUT contract:** documented: anim01-10.gif 25fps + cover mp4/png (no binaries committed on main)
- **Shared dependencies:** stage-05 figure set
- **ISOLATION RULE:** edit under 06_animation/ only; each anim maps to an audited static
- **Freeze:** `module_blob_sha256` · `7a9f6b7170b82811…` · 1 files · authority: visual-audit

### `pipeline_viz_extra`
- **Directories:** docs/mvp-research/pipeline/cover/ + docs/mvp-research/pipeline/generative_art/
- **Purpose:** 視覺化階段補充:封面、生成藝術(05_visualization/06_animation 由 viz_pipeline_05/06 各自擁有)
- **INPUT contract:** processed/statistical 輸出
- **OUTPUT contract:** png/gif/md
- **Shared dependencies:** figure_map.md
- **ISOLATION RULE:** 僅編輯視覺化資料夾;唯讀 render 不產新統計
- **Freeze:** `module_blob_sha256` · `d184458070239310…` · 5 files · authority: 視覺稽核 vs catalog

### `pipeline_root_docs`
- **Directories:** docs/mvp-research/pipeline/STAGE_SUMMARY_AND_FREEZE.md + docs/mvp-research/pipeline/PIPELINE_LINEAGE.md + docs/mvp-research/pipeline/FREEZE_MANIFEST.csv + docs/mvp-research/pipeline/EDA_INDEX.md + docs/mvp-research/pipeline/_docs/
- **Purpose:** pipeline 根層文件:階段摘要、lineage、舊 freeze manifest、EDA 索引
- **INPUT contract:** 各階段
- **OUTPUT contract:** 文件
- **Shared dependencies:** —
- **ISOLATION RULE:** 僅編輯根文件;舊 FREEZE_MANIFEST.csv 由 v2 統一版取代但保留供 lineage
- **Freeze:** `module_blob_sha256` · `cea3d37c89a18da5…` · 7 files · authority: 文件審查


## P5 — Informative figure & server (發表圖與後端)

### `dashboard_doc_07`
- **Directories:** docs/mvp-research/pipeline/07_dashboard/
- **Purpose:** dashboard consumer-layer doc; runtime is backend(P5.2)+frontend
- **INPUT contract:** all upstream tables + _evidence/_pathway json (documented)
- **OUTPUT contract:** stage-07 doc; runtime real-dataset.json pinned separately in FREEZE_MANIFEST
- **Shared dependencies:** backend API + frontend
- **ISOLATION RULE:** edit doc here; runtime isolated in src/3_DE_analysis + frontend/
- **Freeze:** `module_blob_sha256` · `a9cf5bb6f469bd71…` · 1 files · authority: visual-audit(doc)+pytest(runtime)

### `de_api_backend`
- **Directories:** src/3_DE_analysis/api/
- **Purpose:** read-only FastAPI target-card backend; 47 route handlers across 19 routers
- **INPUT contract:** frozen upstream DE artifacts + evidence caches (read-only via deps.py)
- **OUTPUT contract:** HTTP/JSON API pinned by contracts/card_schema.py + tests/test_api_openapi.py
- **Shared dependencies:** contracts/card_schema.py; core/
- **ISOLATION RULE:** change internals freely iff JSON contract holds; frontend never imports these
- **Freeze:** `module_blob_sha256` · `ffa83f2476e0192e…` · 23 files · authority: pytest tests/test_api_openapi.py + golden fixtures

### `perturbase_frontend`
- **Directories:** docs/mvp-research/perturbase_frontend/ + docs/mvp-research/perturbase_frontend/catalog/
- **Purpose:** flagship/informative figure factory: 71 figure_scripts + 71 rendered PNG + bilingual catalog (PR#69, 404 claim CORRECTED)
- **INPUT contract:** frozen upstream signed/level4/stage-05 artifacts (read-only)
- **OUTPUT contract:** figure_scripts/<ID>.py -> matching PNG; ALL_CHARTS_CATALOG_bilingual.csv master manifest
- **Shared dependencies:** upstream data; FIGURE_SCRIPTS_INDEX.csv
- **ISOLATION RULE:** edit under perturbase_frontend/ only; scripts re-render from frozen upstream
- **Freeze:** `module_blob_sha256` · `6437c5c07941c4ac…` · 146 files · authority: visual-audit + catalog/script-index completeness

### `webserver_public_assets`
- **Directories:** frontend/webserver/public/ + frontend/webserver/public/flagship/delivery_funnel.png + frontend/webserver/public/flagship/screen_story.png + frontend/webserver/public/gallery/figures/A16.png + frontend/webserver/public/gallery/figures/A17.png + frontend/webserver/public/gallery/figures/A18.png
- **Purpose:** SPA-served static assets: flagship figures + full gallery PNG set + 3D cif + charts.json
- **INPUT contract:** rendered outputs from P5.3/P4 (build-copied)
- **OUTPUT contract:** stable asset paths + gallery/data/charts.json (141KB) + structures.json
- **Shared dependencies:** P5.3 figure scripts; backend API
- **ISOLATION RULE:** edit under public/ only; assets re-rendered from frozen sources
- **Freeze:** `module_blob_sha256` · `531bc7f51c0a5ded…` · 178 files · authority: visual-audit + charts.json manifest integrity

### `ui_prototypes`
- **Directories:** docs/mvp-research/pipeline/ui_prototypes/
- **Purpose:** Entry A/B 互動 UI 原型(rank board 等)
- **INPUT contract:** 排名/statistics 輸出
- **OUTPUT contract:** HTML 原型
- **Shared dependencies:** 07_dashboard
- **ISOLATION RULE:** 僅編輯原型資料夾
- **Freeze:** `module_blob_sha256` · `7f7897815b8733b4…` · 10 files · authority: 視覺/功能檢視


## P6 — Frontend & devops (前端與 devops)

### `freeze_validate_scripts`
- **Directories:** scripts/
- **Purpose:** Freeze/validate/EDA devops scripts: freeze_pipeline.py, validate_pipeline.py (read-only collector), generate_stage_eda.py
- **INPUT contract:** Pipeline data files (read-only)
- **OUTPUT contract:** Terminal report / freeze manifest; no pipeline mutation
- **Shared dependencies:** pipeline data layout; make targets
- **ISOLATION RULE:** Edit scripts/ only; validate_pipeline decides nothing (tests/ are authority); run make validate-pipeline
- **Freeze:** `module_blob_sha256` · `e969d3dfd0552d69…` · 4 files · authority: pytest tests/test_validate_pipeline_collector.py; make validate-pipeline runs

### `devops_build_config`
- **Directories:** frontend/webserver/package.json + frontend/webserver/package-lock.json + frontend/webserver/vite.config.ts + frontend/webserver/tsconfig.json + frontend/webserver/tsconfig.app.json + frontend/webserver/tsconfig.node.json + frontend/webserver/index.html + frontend/webserver/.oxlintrc.json + frontend/webserver/.gitignore + frontend/webserver/scripts + Makefile + environment.yaml + pytest.ini + .gitignore + frontend/webserver/README.md
- **Purpose:** DevOps/build:前端 build/config(package/vite/tsconfig/index.html)+ 頂層 Makefile/environment.yaml/pytest.ini/.gitignore
- **INPUT contract:** Node/npm toolchain; source under src/
- **OUTPUT contract:** Production build bundle; real-dataset.json export
- **Shared dependencies:** package.json/package-lock.json pinned deps
- **ISOLATION RULE:** Edit build/config here only; keep package-lock in sync; rebuild to validate
- **Freeze:** `module_blob_sha256` · `1862fbfd46a8ddae…` · 12 files · authority: npm run build succeeds; lockfile parity

### `frontend_readme`
- **Directories:** frontend/README.md
- **Purpose:** Frontend module boundary rules (no import of backend internals; JSON is only contract)
- **INPUT contract:** n/a (human-readable)
- **OUTPUT contract:** Module isolation rule statement
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit doc only; reflects current React SPA (not stale Streamlit)
- **Freeze:** `module_blob_sha256` · `63aadecb84046982…` · 1 files · authority: human review

### `frontend_spa_src`
- **Directories:** frontend/webserver/src/
- **Purpose:** React/TS SPA source: App, views (Explorer/Compare/Dossier/Clinical/Deck/Figures/Provenance/ApiDocs/Home), components, data models, lib (drawFigure/logic), store
- **INPUT contract:** FastAPI HTTP/JSON only (card_schema.py contract) + static public/real-dataset.json
- **OUTPUT contract:** Rendered SPA UI; writes nothing back to pipeline
- **Shared dependencies:** FastAPI JSON contract (card_schema.py); webserver/package.json deps
- **ISOLATION RULE:** Edit only frontend/webserver/src/; never import src/3_DE_analysis internals; run npm run build + pytest
- **Freeze:** `module_blob_sha256` · `29c5e36be3b5930c…` · 22 files · authority: npm run build (make web) + pytest tests/test_empty_states.py,test_upload_ui.py


## P7 — Documentation (文檔)

### `API`
- **Directories:** docs/API.md
- **Purpose:** Named authority doc: API.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `0439dad9a7f0da17…` · 1 files · authority: human review + matches code

### `DRUG_DISCOVERY_TOOL_DEVELOPMENT_PLAN`
- **Directories:** docs/DRUG_DISCOVERY_TOOL_DEVELOPMENT_PLAN.md
- **Purpose:** Non-mvp human-readable doc: DRUG_DISCOVERY_TOOL_DEVELOPMENT_PLAN.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `188f0f35a62a3872…` · 1 files · authority: human review

### `FRONTEND_HANDOFF`
- **Directories:** docs/FRONTEND_HANDOFF.md
- **Purpose:** Non-mvp human-readable doc: FRONTEND_HANDOFF.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `127e875975d5fd29…` · 1 files · authority: human review

### `FRONTEND_HANDOFF.en`
- **Directories:** docs/FRONTEND_HANDOFF.en.md
- **Purpose:** Non-mvp human-readable doc: FRONTEND_HANDOFF.en.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `18e21a13be12d71d…` · 1 files · authority: human review

### `IMPLEMENTATION_PLAN`
- **Directories:** docs/IMPLEMENTATION_PLAN.md
- **Purpose:** Non-mvp human-readable doc: IMPLEMENTATION_PLAN.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `e983d0594d114db1…` · 1 files · authority: human review

### `REPRODUCIBILITY`
- **Directories:** docs/REPRODUCIBILITY.md
- **Purpose:** Named authority doc: REPRODUCIBILITY.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `a8dccdd9c1226ec9…` · 1 files · authority: human review + matches code

### `ROADMAP`
- **Directories:** docs/ROADMAP.md
- **Purpose:** Non-mvp human-readable doc: ROADMAP.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `3314084c80b3213f…` · 1 files · authority: human review

### `architecture_refactor_plan`
- **Directories:** docs/architecture_refactor_plan.md
- **Purpose:** Non-mvp human-readable doc: architecture_refactor_plan.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `72ae70c27690a571…` · 1 files · authority: human review

### `bulk_download_schema`
- **Directories:** docs/bulk_download_schema.md
- **Purpose:** Non-mvp human-readable doc: bulk_download_schema.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `aadb6869cde59eb9…` · 1 files · authority: human review

### `cache_and_versioning_policy`
- **Directories:** docs/cache_and_versioning_policy.md
- **Purpose:** Non-mvp human-readable doc: cache_and_versioning_policy.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `fc56696bf9015d6d…` · 1 files · authority: human review

### `compass_concept_integration_plan`
- **Directories:** docs/compass_concept_integration_plan.md
- **Purpose:** Non-mvp human-readable doc: compass_concept_integration_plan.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `f8ef78948b738c88…` · 1 files · authority: human review

### `concept_dictionary`
- **Directories:** docs/concept_dictionary.md
- **Purpose:** Non-mvp human-readable doc: concept_dictionary.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `b229397b10d054c1…` · 1 files · authority: human review

### `data_dictionary`
- **Directories:** docs/data_dictionary.md
- **Purpose:** Non-mvp human-readable doc: data_dictionary.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `0e26b66ebb1892e9…` · 1 files · authority: human review

### `data_governance_checklist`
- **Directories:** docs/data_governance_checklist.md
- **Purpose:** Non-mvp human-readable doc: data_governance_checklist.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `b2a3d66f59893814…` · 1 files · authority: human review

### `data_use_terms`
- **Directories:** docs/data_use_terms.md
- **Purpose:** Non-mvp human-readable doc: data_use_terms.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `843e845d7fdd7bba…` · 1 files · authority: human review

### `de_and_baseline_spec`
- **Directories:** docs/de_and_baseline_spec.md
- **Purpose:** Non-mvp human-readable doc: de_and_baseline_spec.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `36894eebeb99ca67…` · 1 files · authority: human review

### `def_followup_plan`
- **Directories:** docs/def_followup_plan.md
- **Purpose:** Non-mvp human-readable doc: def_followup_plan.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `a9656377861532d1…` · 1 files · authority: human review

### `documentation_index`
- **Directories:** docs/documentation_index.md
- **Purpose:** Named authority doc: documentation_index.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `63214dc321a48de1…` · 1 files · authority: human review + matches code

### `explainer`
- **Directories:** docs/explainer/
- **Purpose:** Human-readable explainer bundle (index.html + README)
- **INPUT contract:** — (no upstream module; leaf doc/reference)
- **OUTPUT contract:** Static HTML explainer
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit under docs/explainer/ only; combined sha re-pinned on change
- **Freeze:** `module_blob_sha256` · `bf761c3fd5844b32…` · 2 files · authority: human review / renders in browser

### `external_overlay_integration_concept`
- **Directories:** docs/external_overlay_integration_concept.md
- **Purpose:** Non-mvp human-readable doc: external_overlay_integration_concept.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `8ab01d727ee993a1…` · 1 files · authority: human review

### `external_qa_review_2026-07-10`
- **Directories:** docs/external_qa_review_2026-07-10.md
- **Purpose:** Non-mvp human-readable doc: external_qa_review_2026-07-10.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `cdc38e683265507d…` · 1 files · authority: human review

### `figure_guide`
- **Directories:** docs/figure_guide.md
- **Purpose:** Non-mvp human-readable doc: figure_guide.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `1c747029b26ead30…` · 1 files · authority: human review

### `frontend_design`
- **Directories:** docs/frontend_design.md
- **Purpose:** Non-mvp human-readable doc: frontend_design.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `3f75757b3574a1c8…` · 1 files · authority: human review

### `frontend_disclosure_spec`
- **Directories:** docs/frontend_disclosure_spec.md
- **Purpose:** Non-mvp human-readable doc: frontend_disclosure_spec.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `d8ebcb7f1af1e413…` · 1 files · authority: human review

### `frontend_fix_plan`
- **Directories:** docs/frontend_fix_plan.md
- **Purpose:** Non-mvp human-readable doc: frontend_fix_plan.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `589d5444fe4f9454…` · 1 files · authority: human review

### `human_validation_protocol`
- **Directories:** docs/human_validation_protocol.md
- **Purpose:** Non-mvp human-readable doc: human_validation_protocol.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `f702d8ce34cd86b7…` · 1 files · authority: human review

### `improvement_roadmap`
- **Directories:** docs/improvement_roadmap.md
- **Purpose:** Non-mvp human-readable doc: improvement_roadmap.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `74e6a2593b4dda66…` · 1 files · authority: human review

### `ml_feasibility_assessment`
- **Directories:** docs/ml_feasibility_assessment.md
- **Purpose:** Non-mvp human-readable doc: ml_feasibility_assessment.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `92e84e3ccd9084b1…` · 1 files · authority: human review

### `next_phases_plan`
- **Directories:** docs/next_phases_plan.md
- **Purpose:** Non-mvp human-readable doc: next_phases_plan.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `1ae929b12e0e1a91…` · 1 files · authority: human review

### `perturbation_validation_plan`
- **Directories:** docs/perturbation_validation_plan.md
- **Purpose:** Non-mvp human-readable doc: perturbation_validation_plan.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `355a959dfeabe668…` · 1 files · authority: human review

### `researcher_guide`
- **Directories:** docs/researcher_guide/
- **Purpose:** Human-readable researcher_guide bundle (index.html + README)
- **INPUT contract:** — (no upstream module; leaf doc/reference)
- **OUTPUT contract:** Static HTML explainer
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit under docs/researcher_guide/ only; combined sha re-pinned on change
- **Freeze:** `module_blob_sha256` · `1c27e1c43b83b1be…` · 2 files · authority: human review / renders in browser

### `server_modules`
- **Directories:** docs/server_modules.md
- **Purpose:** Non-mvp human-readable doc: server_modules.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `62e6cc1ce1e0d8e4…` · 1 files · authority: human review

### `server_northstar`
- **Directories:** docs/server_northstar.md
- **Purpose:** Non-mvp human-readable doc: server_northstar.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `cf49f6f2c26ab13c…` · 1 files · authority: human review

### `slides`
- **Directories:** docs/slides/
- **Purpose:** Human-readable slides bundle (index.html + README)
- **INPUT contract:** — (no upstream module; leaf doc/reference)
- **OUTPUT contract:** Static HTML explainer
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit under docs/slides/ only; combined sha re-pinned on change
- **Freeze:** `module_blob_sha256` · `bfed93143d4fb358…` · 3 files · authority: human review / renders in browser

### `technical_methods`
- **Directories:** docs/technical_methods.md
- **Purpose:** Named authority doc: technical_methods.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `aa4bfc5f68008454…` · 1 files · authority: human review + matches code

### `tier2-gene-for-Claude science`
- **Directories:** docs/tier2-gene-for-Claude science.md
- **Purpose:** Non-mvp human-readable doc: tier2-gene-for-Claude science.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `fd11ca1921d89a5e…` · 1 files · authority: human review

### `ux_flow_stepwise_plan`
- **Directories:** docs/ux_flow_stepwise_plan.md
- **Purpose:** Non-mvp human-readable doc: ux_flow_stepwise_plan.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `4b9724746026b420…` · 1 files · authority: human review

### `ux_trust_fix_plan`
- **Directories:** docs/ux_trust_fix_plan.md
- **Purpose:** Non-mvp human-readable doc: ux_trust_fix_plan.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `42ecb8fb07f5345c…` · 1 files · authority: human review

### `validation_report`
- **Directories:** docs/validation_report.md
- **Purpose:** Non-mvp human-readable doc: validation_report.md
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `fef297614fb41472…` · 1 files · authority: human review

### `validation_status`
- **Directories:** docs/validation_status.csv
- **Purpose:** Non-mvp human-readable doc: validation_status.csv
- **INPUT contract:** n/a (human-readable spec)
- **OUTPUT contract:** Prose/spec content; no machine contract
- **Shared dependencies:** cross-references other docs
- **ISOLATION RULE:** Edit this md/csv only; no code re-validation (unless it pins numbers e.g. validation_status.csv)
- **Freeze:** `module_blob_sha256` · `ae7663b4755e8a3a…` · 1 files · authority: human review

### `wiki`
- **Directories:** wiki/
- **Purpose:** Project wiki: Home/Manual/Map/Plan/Roadmap/Maintenance/Development-Guide/Tech-Debt/_Sidebar
- **INPUT contract:** — (no upstream module; leaf doc/reference)
- **OUTPUT contract:** Human-readable wiki pages
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit under wiki/ only; combined sha re-pinned on deliberate change
- **Freeze:** `module_blob_sha256` · `9076246bc1901eb8…` · 10 files · authority: human review

### `structure_governance`
- **Directories:** docs/structure/PHASE_MODULE_MAP.md + docs/structure/MODULE_ISOLATION_POLICY_v2.md + docs/structure/STRUCTURE_REVIEW.md
- **Purpose:** 全倉結構治理文件:PHASE_MODULE_MAP、MODULE_ISOLATION_POLICY_v2、FREEZE_MANIFEST_UNIFIED、STRUCTURE_REVIEW
- **INPUT contract:** 全模組 manifest
- **OUTPUT contract:** 治理 md/csv(本層自我描述)
- **Shared dependencies:** —
- **ISOLATION RULE:** 僅編輯 docs/structure/;此為結構真值層,變更即重新凍結
- **Freeze:** `module_blob_sha256` · `a90a15e219748e16…` · 3 files · authority: validate_freeze_unified.py 自我一致


## P8 — README & reference (說明與引用)

### `DATA_LICENSE`
- **Directories:** DATA_LICENSE.md
- **Purpose:** Data usage license/terms
- **INPUT contract:** — (no upstream module; leaf doc/reference)
- **OUTPUT contract:** Human-readable reference
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit file only; blob sha re-pinned on change
- **Freeze:** `module_blob_sha256` · `be7dac87058a4a88…` · 1 files · authority: legal

### `LICENSE`
- **Directories:** LICENSE
- **Purpose:** Code license
- **INPUT contract:** — (no upstream module; leaf doc/reference)
- **OUTPUT contract:** Human-readable reference
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit file only; blob sha re-pinned on change
- **Freeze:** `module_blob_sha256` · `0dabb0e788437f63…` · 1 files · authority: legal

### `README`
- **Directories:** README.md
- **Purpose:** Top-level repo README / entry point
- **INPUT contract:** — (no upstream module; leaf doc/reference)
- **OUTPUT contract:** Human-readable reference
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit file only; blob sha re-pinned on change
- **Freeze:** `module_blob_sha256` · `83d2c1f6d947427e…` · 1 files · authority: human review

### `literature_reference_corpus`
- **Directories:** sources/topic*
- **Purpose:** Literature & PMID reference corpus: topic01-16 PubMed/OpenAlex/ClinicalTrials JSON dumps, summary md, target/inventory csv
- **INPUT contract:** External literature (PubMed/OpenAlex/ClinicalTrials) — frozen snapshots
- **OUTPUT contract:** Reference corpus consumed by docs/target tool
- **Shared dependencies:** external DB snapshots
- **ISOLATION RULE:** Append/replace whole topic files; combined sha re-pinned on deliberate corpus change; individual PMIDs are immutable snapshots
- **Freeze:** `module_blob_sha256` · `e6d6618ab8c3a81b…` · 60 files · authority: snapshot immutability / human review

### `project_decision_log`
- **Directories:** sources/project_decision_log.md
- **Purpose:** Chronological project decision log
- **INPUT contract:** — (no upstream module; leaf doc/reference)
- **OUTPUT contract:** Human-readable reference
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit file only; blob sha re-pinned on change
- **Freeze:** `module_blob_sha256` · `64020c427e461d4b…` · 1 files · authority: human review

### `provenance_registry`
- **Directories:** docs/provenance_registry.md
- **Purpose:** Provenance registry (human-readable)
- **INPUT contract:** — (no upstream module; leaf doc/reference)
- **OUTPUT contract:** Human-readable reference
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit file only; blob sha re-pinned on change
- **Freeze:** `module_blob_sha256` · `49634206779d2ba6…` · 1 files · authority: human review

### `provenance_registry_csv`
- **Directories:** docs/provenance_registry.csv
- **Purpose:** Machine-readable provenance registry (source->artifact mapping)
- **INPUT contract:** Records for each pipeline/source artifact
- **OUTPUT contract:** CSV provenance table
- **Shared dependencies:** consumed by docs + audits
- **ISOLATION RULE:** Edit CSV only; both git blob sha and content md5 re-pinned on change
- **Freeze:** `module_blob_sha256` · `03de2ba6f6654eb1…` · 1 files · authority: schema check + human review

### `mvp_research_root`
- **Directories:** docs/mvp-research/
- **Purpose:** mvp-research 根層散置文件:MVP 簡報、模組定位、任務 runbook、資料清單、demo
- **INPUT contract:** 各來源
- **OUTPUT contract:** md/csv/json
- **Shared dependencies:** —
- **ISOLATION RULE:** 僅編輯根層散檔
- **Freeze:** `module_blob_sha256` · `efbe9ec6b19b4729…` · 17 files · authority: 文件審查


## P9 — Limitation (限制)

### `KNOWN_LIMITATIONS`
- **Directories:** docs/KNOWN_LIMITATIONS.md
- **Purpose:** Known platform limitations — honest boundary statement
- **INPUT contract:** n/a (honest boundary declaration)
- **OUTPUT contract:** Human-readable limitation statement
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit md only; blob sha re-pinned on change
- **Freeze:** `module_blob_sha256` · `ca3dd3aa2e0bdc6a…` · 1 files · authority: human review

### `sandbox_blocked_tasks`
- **Directories:** docs/sandbox_blocked_tasks.md
- **Purpose:** Sandbox-blocked tasks (network/compute limits encountered)
- **INPUT contract:** n/a (honest boundary declaration)
- **OUTPUT contract:** Human-readable limitation statement
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit md only; blob sha re-pinned on change
- **Freeze:** `module_blob_sha256` · `d6deff74a247e5e0…` · 1 files · authority: human review

### `topic12_paper_limitations_future_work`
- **Directories:** sources/topic12_paper_limitations_future_work.md
- **Purpose:** Paper-level limitations & future work synthesis
- **INPUT contract:** n/a (honest boundary declaration)
- **OUTPUT contract:** Human-readable limitation statement
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit md only; blob sha re-pinned on change
- **Freeze:** `module_blob_sha256` · `314cdc011978c701…` · 1 files · authority: human review

### `topic15_limitation_future_work_audit_table`
- **Directories:** sources/topic15_limitation_future_work_audit_table.md
- **Purpose:** Limitation/future-work audit table
- **INPUT contract:** n/a (honest boundary declaration)
- **OUTPUT contract:** Human-readable limitation statement
- **Shared dependencies:** none
- **ISOLATION RULE:** Edit md only; blob sha re-pinned on change
- **Freeze:** `module_blob_sha256` · `ba38ba0b2669338e…` · 1 files · authority: human review

