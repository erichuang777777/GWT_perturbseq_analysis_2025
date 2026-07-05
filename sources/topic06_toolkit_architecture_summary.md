# Topic 6 - 類似資料及目前已有哪些開發出來的工具

## Executive takeaways

Topic 2 的工具清單仍然成立，但 Topic 6 的重點應該改成「如何把現有工具組成 GWT CD4 target-card toolkit」。不要再做一套新的 Perturb-seq workflow runner；比較有價值的是 target-centered evidence toolkit。

核心設計：

- **MVP**: 使用本地 repo 已有 CSV / supplementary tables / DE summaries，先做 target ranking、pathway interpretation、external evidence overlay、readiness score、target card。
- **Later**: 等 `GWCD4i.DE_stats.h5ad`、pseudobulk `.h5ad` 或 cell-level h5ad 下載後，再加 cell-level QC、Mixscape/SCEPTRE/pertpy、state-specific perturbation effects、responder cell analysis。
- **Evidence backbone**: Topic 4 的 readiness schema + Topic 5 的 successful-drug benchmark table。

## Toolkit architecture

| Layer | Purpose | Existing tools/resources | Custom code needed |
|---|---|---|---|
| Input contract | Normalize repo CSV/signature/h5ad into stable tables | pandas, AnnData, Scanpy, local metadata schema | `target`, `target_condition_effect`, `signature`, `program_score`, `external_evidence`, `benchmark_axis`, `readiness_score` contracts |
| GWT perturbation evidence | Convert DE/guide/donor outputs into target-level facts | local `DE_analysis_utils.py`, `merge_DE_results.py`, DE supplementary tables | target summaries, direction calls, guide/donor/on-target/off-target flags |
| Signature/program layer | Interpret DE as CD4 programs/pathways | decoupleR, PROGENy, DoRothEA, UCell/AUCell, MSigDB, Reactome, OmniPath | CD4 signed program registry, signature similarity, 3-10 gene PD biomarker extraction |
| Perturbation statistics | Robust perturbation effect models | SCEPTRE, scMAGeCK, Mixscape/Mixscale, pertpy, muscat, DESeq2/edgeR/limma, MAST | bridge outputs into target cards; compare CSV-first vs h5ad results |
| External evidence | Add what GWT cannot answer | Open Targets, ChEMBL, DGIdb, Pharos, DrugCentral, DepMap, GTEx, HPA, DICE, CELLxGENE, ClinicalTrials.gov, FDA labels | cached adapters, gene ID mapping, source/version stamps |
| Disease/drug matching | Connect signatures to drugs and disease states | LINCS/CMap, CLUE, SigCom LINCS, L1000FWD, CREEDS, Enrichr | signed query export, drug-axis mapping, benchmark matching |
| Successful-drug benchmark | Map targets to clinical precedent | `topic05_successful_drug_benchmarks.csv` | axis rules, positive controls, safety caps |
| Readiness decision | Turn evidence into `advance/validate/watchlist/deprioritize` | `topic04_drug_readiness_checklist.csv` | R0-R5 stage gate, red-flag overrides, provenance trace |
| Report/dashboard | Make outputs usable | Quarto/Jupyter, Streamlit/Dash/Shiny, Vitessce, cellxgene Explorer, UCSC Cell Browser | target cards, sortable ranking table, HTML/JSON/CSV export |

## Highest-priority additions beyond Topic 2

| Category | Tools/resources to add | Why |
|---|---|---|
| Perturbation data resources | PerturbSeq.db, PerturbDB, PerturBase, scPerturb, Tahoe-100M/Arc Virtual Cell Atlas | Reference datasets, benchmarks, and optional ML-scale data |
| Guide/QC | crispat, SoupX, DecontX, Scrublet, DoubletFinder, scDblFinder | Perturb-seq guide assignment, ambient RNA, doublet risk |
| Robust statistics | SCEPTRE low-MOI update, TRADE, perturbation-response score, GSFA, MUSIC, GPerturb | Better perturbation effect quantification, heterogeneous response, latent programs |
| Replicate/composition | muscat, dreamlet, pseudobulk edgeR/DESeq2/limma, Milo, Augur, scCODA | donor-aware and condition-aware inference |
| Program/regulon | clusterProfiler, g:Profiler, GSEApy, Enrichr, MSigDB, Reactome, OmniPath, SCENIC+, VIPER | More interpretable pathway/TF/regulon layers |
| Cell-cell context | NicheNet, CellChat, LIANA+ | Needed later for tissue disease context, not MVP core |
| Prediction | scGen, CPA, CellOT, GEARS, ChemCPA, biolord, scDisInFact, trVAE, scGPT, scFoundation, Geneformer | Useful for v2, but benchmark against simple baselines first |
| Target evidence | Open Targets Genetics, GWAS Catalog, ClinVar, OMIM, ClinGen, UniProt, HPA, GTEx, Pharos, DrugCentral, DGIdb, ChEMBL, DepMap | Required for target-card readiness beyond GWT |

## CSV-first MVP

The local repository can support the MVP without downloading the full 1.6+ TiB cell-level dataset.

MVP modules:

1. `target_summary`: aggregate DE/significance/guide/on-target/off-target evidence by target and condition.
2. `signature_registry`: store signed CD4 programs, successful-drug axes, disease signatures, and safety signatures.
3. `program_scoring`: score each target signature for activation, Treg, Th1, Th2, Th17, Tfh, exhaustion, stress, apoptosis, proliferation, cytokine output.
4. `external_evidence_cache`: Open Targets, ChEMBL/DGIdb/Pharos, DepMap, GTEx/HPA/DICE/CELLxGENE, FDA/ClinicalTrials references.
5. `target_card_engine`: combine GWT facts, program scores, external evidence, benchmark axes, and readiness rules.
6. `report_export`: `target_rankings.csv`, `target_cards.json`, static HTML/Quarto report.

MVP outputs should be transparent and source-stamped. A numeric target score without provenance will be misleading.

## h5ad/cell-level extension

Add after data download:

- AnnData/Scanpy loaders for `GWCD4i.DE_stats.h5ad`, pseudobulk `.h5ad`, and cell-level h5ad.
- Mixscape/Mixscale for escaped or non-responder cells.
- SCEPTRE for calibrated perturbation-gene associations.
- pertpy for AnnData-native perturbation workflows.
- UCell/AUCell per-cell CD4 program scores.
- SCENIC/arboreto/CellOracle for regulon and network interpretation.
- responder-cell and state-specific effect summaries bridged back to the same target-card schema.

## Prediction-model caution

GEARS, CPA, scGen, CellOT, scGPT, Geneformer, and newer foundation-model approaches should be treated as optional v2 hypothesis generators. As of 2025, benchmarks report that deep/foundation perturbation predictors do not consistently beat simple baselines across settings. Use Open Problems / scPerturBench-style evaluations before using predictions for readiness decisions.

## Key risks

- CSV-first cannot recover cell heterogeneity, responder fractions, escaped perturbations, or precise cell-state effects.
- CRISPR loss-of-function does not automatically translate to small-molecule inhibition, agonism, degradation, antibody blockade, or RNA modality.
- In-vitro isolated CD4 cells miss antigen specificity, trafficking, tissue context, myeloid/stromal feedback, and protein-level cytokine output.
- External APIs can drift; cache and version evidence snapshots.
- Drug benchmark matching should be curated first. Fully automatic axis assignment can overstate evidence.

## Key references and resources

- SCEPTRE: PMID 34930414; low-MOI update PMID 38760839.
- scMAGeCK: PMID 31980032.
- Mixscape: PMID 33649593.
- pertpy: DOI `10.1038/s41592-025-02909-7`.
- PerturbSeq.db: PMID 40381983; DOI `10.1016/j.jmb.2025.169209`.
- PerturbDB: PMID 39265120; DOI `10.1093/nar/gkae777`.
- PerturBase: PMID 39377396; DOI `10.1093/nar/gkae858`.
- crispat: PMID 39240651; DOI `10.1093/bioinformatics/btae535`.
- TRADE: PMID 40259084; DOI `10.1038/s41588-025-02169-3`.
- Perturbation-response score: PMID 40011559; DOI `10.1038/s41556-025-01626-9`.
- GSFA: PMID 37770710; DOI `10.1038/s41592-023-02017-4`.
- MUSIC: PMID 31110232; DOI `10.1038/s41467-019-10216-x`.
- GPerturb: PMID 40593897; DOI `10.1038/s41467-025-61165-7`.
- scGen: PMID 31363220; DOI `10.1038/s41592-019-0494-8`.
- CPA: DOI `10.15252/msb.202211517`.
- GEARS: DOI `10.1038/s41587-023-01905-6`.
- L1000/CMap: PMID 29195078; DOI `10.1016/j.cell.2017.10.049`.
- Open Targets Platform: PMID 33196847; https://platform.opentargets.org.
- ChEMBL 2023: PMID 37933841; DOI `10.1093/nar/gkad1004`.
