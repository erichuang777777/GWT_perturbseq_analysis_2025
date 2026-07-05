# Topic 12 - Literature Limitations, Future Work, And Toolkit Implications

Date reviewed: 2026-07-04

This is a scoped literature synthesis for the GWT primary human CD4 Perturb-seq project. The goal is not to claim clinical readiness. The goal is to convert the literature limitations into concrete requirements for a research-use target-condition evidence toolkit.

## Executive Position

The safest product positioning is a research-use `target x condition` evidence toolkit, not a drug discovery engine. GWT is valuable because it gives primary human CD4 perturbation evidence across Rest, Stim8hr, and Stim48hr contexts, but it does not by itself prove disease relevance, clinical efficacy, safety, modality feasibility, or patient stratification.

The practical conclusion is:

- Use GWT as the experimental anchor for CD4 target hypotheses.
- Keep the primary unit as `target_condition_id`, not a single gene-level score.
- Separate biological signal, QC confidence, external disease evidence, clinical precedent, and safety red flags.
- Cap readiness when evidence is RNA-only, condition-confounded, lacking donor/guide robustness, lacking knockdown validation, or mismatched to disease tissue.
- Treat prediction and drug matching as hypothesis-generating until orthogonal validation exists.

## Evidence Classes Reviewed

| Evidence class | Main role | Main limitation | Toolkit implication |
|---|---|---|---|
| GWT primary human CD4 Perturb-seq | Primary perturbation anchor | In-vitro CD4 states are not disease tissues or patient states | Score `target x condition`; show condition specificity and batch caveats |
| Primary T-cell perturbation papers | Orthogonal immune-cell validation | Usually smaller scale or different assays/stimuli | Use as validation benchmark, not as exact replication |
| Perturb-seq methods and statistics | QC and inference rules | Guide assignment, escaped cells, pseudoreplication, batch/covariates | Build a QC/confidence layer independent of biology |
| Open-data databases | External evidence discovery | Heterogeneous cell types, species, modalities, metadata | Add context-match scoring and source versioning |
| Drug-development literature | Translation guardrails | Target biology alone rarely predicts success | Add clinical precedent, safety caps, and validation next steps |

## Common Limitations And Future Work By Literature Class

### GWT And Primary CD4/T-Cell Perturbation Papers

Common limitations:

- GWT is primary human CD4 evidence, but still an in-vitro perturbation system.
- Rest, Stim8hr, and Stim48hr are culture contexts; they are not disease tissue, antigen-specific T-cell states, or patient strata.
- CRISPRi knockdown does not necessarily phenocopy small-molecule inhibition, antibody blockade, agonism, degradation, or cell therapy engineering.
- RNA readout does not directly measure protein abundance, surface phenotype, cytokine secretion, TCR clonotype, suppression function, or trafficking.
- Donor diversity is limited relative to clinical heterogeneity.
- `Stim48hr` should carry a run/batch caveat until externally replicated.
- Broad chromatin or essential-like perturbations can dominate DE-breadth rankings without being tractable therapeutic targets.

Future work:

- Cell-level h5ad QC: guide assignment, doublets, escaped/non-responder cells, guide dose, responder fraction.
- Protein/cytokine validation by CITE-seq, flow, ELISA, intracellular staining, or functional assays.
- Patient ex vivo validation in disease-relevant CD4 states.
- Disease-atlas matching to RA, SLE, IBD, psoriasis, T1D, MS, and transplant contexts.
- Independent guide, rescue, CRISPRa/CRISPRi directionality, and orthogonal perturbation validation.

Toolkit requirement:

- Make `target_condition_id` the primary key.
- Store `condition`, `n_cells_target`, `n_guides`, `guide_kd_efficiency`, `donor_robustness`, `guide_robustness`, `offtarget_flag`, and `batch_caveat`.
- Default GWT-only findings to discovery/hypothesis-ready, not clinical-ready.

### Perturb-Seq Methods, QC, And Statistics

Common limitations:

- Pooled scCRISPR screens have guide assignment, MOI, multiplet, off-target, and incomplete perturbation problems.
- Assigned guide does not guarantee functional perturbation; escaped or non-responder cells can dilute signal.
- Single-cell DE can be distorted by pseudoreplication, low cell counts, donor imbalance, batch effects, and covariate confounding.
- Batch correction should not replace raw-count or pseudobulk statistical inference.
- Deep perturbation prediction models should be benchmarked against simple baselines before entering decision workflows.

Future work:

- Compare SCEPTRE, scMAGeCK, Mixscape/Mixscale, pertpy, muscat/pseudobulk, and negative-control models.
- Add direct guide-capture diagnostics and non-responder detection.
- Add multimodal readouts: RNA + protein + guide + clonotype.
- Keep prediction outputs in a hypothesis-generation tier only.

Toolkit requirement:

- QC/confidence score must be independent from biology/druggability score.
- Readiness must be capped by low cells, poor guide consistency, weak knockdown, off-target flags, or batch caveats.

### Open Data, Databases, And Benchmark Resources

Common limitations:

- scPerturb, PerturBase, PerturbDB, PerturbSeq.db, and TCPGdb improve discoverability but combine heterogeneous cell types, species, assays, perturbation types, and preprocessing.
- LINCS/CMap and many chemical perturbation datasets are mostly cancer/cell-line signatures; context mismatch is substantial for primary CD4 biology.
- OneK1K, DICE, eQTLs, and disease atlases provide observational context, not perturbation proof.
- Open Targets, ChEMBL, DrugCentral, and similar resources are evidence overlays; they do not prove disease efficacy.
- External APIs and database versions drift over time.

Future work:

- Source-versioned evidence cache with `date_accessed`.
- Context-match score by cell type, stimulus, tissue, disease, species, and assay.
- Separate discovery evidence from holdout benchmark evidence.
- Disease-specific immune signature registry.
- Immune-drug clinical benchmark panel.

Toolkit requirement:

- Every external evidence item needs `source`, `version`, `date_accessed`, `license`, and `context_match_score`.
- Penalize context mismatch and avoid double-counting the same evidence class.
- Use database agreement to raise confidence only when context is aligned.

### Drug-Development And Clinical Translation Literature

Common limitations:

- Clinical success depends on indication, modality, dose, exposure, target engagement, patient selection, endpoint, and safety window, not target biology alone.
- The same immune axis can succeed in one disease and fail in another: IL-17 is successful in psoriasis but problematic in Crohn's disease; JAK inhibition is efficacious but safety-limited.
- T-cell activation can be a desired effect or a cytokine-release liability.
- Animal or in-vitro systems can miss human immune toxicity, as shown by TGN1412.
- CD4 RNA signatures alone cannot de-risk trafficking toxicity, PML, opportunistic infection, thrombosis, viral reactivation, malignancy, or long-term immune-mediated organ toxicity.

Future work:

- Build a clinical precedent ontology.
- Separate `success_benchmark`, `failure_benchmark`, `boxed_warning`, `withdrawal`, and `context_specific_risk`.
- Add modality-specific validation plans and first-in-human risk translation fields.
- Require intended therapeutic direction: inhibit, activate, agonize, block, deplete, degrade, or reprogram.

## Paper-By-Paper Limitation And Future-Work Matrix

The limitations below are toolkit-level interpretations of each paper's relevance to this project; they should not be read as a full author-stated limitation list.

| Paper/resource | PMID/DOI | Role | Limitation for GWT translation | Future work / toolkit action |
|---|---|---|---|---|
| Zhu/Dann et al. GWT primary human CD4 Perturb-seq | DOI `10.64898/2025.12.23.696273` | Main GWT data anchor | Preprint; in-vitro primary CD4 states; RNA-centric; disease relevance not automatic | Use as primary hypothesis anchor; add disease/genetics/protein/functional validation layers |
| Shifrut et al. primary human T-cell SLICE/CROP-seq | PMID `30449619`; DOI `10.1016/j.cell.2018.10.024` | Primary T-cell perturbation benchmark | Different perturbation design and stimulation context from GWT | Use for signed T-cell activation/cytokine benchmark genes |
| Schmidt et al. CRISPRa/i primary human T cells | PMID `35113687`; DOI `10.1126/science.abj4008` | Directionality benchmark | Focused immune phenotypes, not genome-scale CD4 transcriptome | Cross-check whether GWT inhibition agrees with activation/inhibition direction |
| Arce et al. T-cell rest/activation circuits | PMID `39663454`; DOI `10.1038/s41586-024-08314-y` | CD4 rest/activation circuit validation | Targeted regulatory circuits, not broad drug-readiness evidence | Use to validate Rest vs Stim program interpretation |
| Weinstock et al. CD4 GRN inference | PMID `39395408`; DOI `10.1016/j.xgen.2024.100671` | Regulatory network comparator | Network inference remains model-dependent | Use as upstream/downstream network overlay, not as causal proof by itself |
| Freimer et al. T-cell effector screens | PMID `36356142`; DOI `10.1126/science.abn5647` | Effector/cytokine regulator benchmark | Effector assay differs from GWT RNA endpoint | Benchmark cytokine-output regulators and validation assays |
| Ho et al. autoimmune variants + primary CD4 MPRA/CRISPRi | PMID `40968290`; DOI `10.1038/s41588-025-02301-3` | Genetics-to-CD4 mechanism link | Variant and target mappings remain locus/context dependent | Add autoimmune variant/eQTL support as a separate evidence tier |
| Zhou et al. in-vivo single-cell CRISPR T-cell fate regulomes | PMID `37968405`; DOI `10.1038/s41586-023-06733-x` | In-vivo T-cell fate comparator | In-vivo context is not directly comparable to in-vitro CD4 culture | Use to flag targets whose effects reverse or change in tissue/in-vivo settings |
| Knudsen et al. CAR T modifiers | PMID `40993381`; DOI `10.1038/s41586-025-09489-8` | Translational T-cell engineering comparator | Oncology/CAR T context differs from autoimmune CD4 modulation | Use as modality-specific comparator for T-cell engineering, not autoimmune therapy |
| Perturb-seq foundational paper | PMID `27984732`; DOI `10.1016/j.cell.2016.11.038` | Foundational scCRISPR method | Early designs and cell models do not solve primary-cell translation | Keep method lineage; rely on newer QC/statistics for inference |
| CRISP-seq | PMID `27984734`; DOI `10.1016/j.cell.2016.11.039` | Early immune scCRISPR precedent | Early immune-cell setting, limited scale and modern QC | Use as conceptual precedent only |
| CROP-seq | PMID `28099430`; DOI `10.1038/nmeth.4177` | Guide capture and TCR signaling benchmark | Jurkat/cell-line biology differs from primary CD4 | Use guide-capture ideas; do not use cell-line TCR response as disease proof |
| ECCITE-seq | PMID `31011186`; DOI `10.1038/s41592-019-0392-0` | Multimodal perturbation design | GWT RNA-only output misses protein/clonotype dimensions | Plan RNA + protein + guide + TCR/clonotype extension |
| Direct guide capture Perturb-seq | PMID `32231336`; DOI `10.1038/s41587-020-0470-y` | Guide assignment improvement | Requires assay design beyond current CSV summaries | Add guide assignment QC when h5ad/raw data are available |
| Replogle genome-scale Perturb-seq | PMID `35688146`; DOI `10.1016/j.cell.2022.05.013` | Genome-scale perturbation reference | Cell-line scale does not equal primary immune translation | Use for computational benchmarking and effect-size expectations |
| Norman combinatorial perturbations | PMID `31395745`; DOI `10.1126/science.aax4438` | Genetic interaction/phenotype manifold | Combinatorial effects not covered by single-gene GWT cards | Future module for target combinations and pathway-level perturbations |
| Papalexi/Mixscape | PMID `33649593`; DOI `10.1038/s41588-021-00778-2` | Escaped-cell and perturbation-response QC | Requires cell-level data and modeling | Add non-responder/escaped-cell confidence when raw data are loaded |
| Frangieh Perturb-CITE-seq | PMID `33649592`; DOI `10.1038/s41588-021-00779-1` | RNA+protein immune perturbation in patient model | Oncology immune-evasion context differs from CD4 autoimmune discovery | Use as model for multimodal and patient-context validation |
| scMAGeCK | PMID `31980032`; DOI `10.1186/s13059-020-1928-4` | Genotype-to-phenotype testing | Method assumptions may not fit every low-MOI donor design | Compare with SCEPTRE/pseudobulk and require negative-control calibration |
| SCEPTRE | PMID `34930414`; DOI `10.1186/s13059-021-02545-2` | Calibrated scCRISPR association testing | Requires careful covariates and design metadata | Use for cell-level validation, not just summary CSV ranking |
| SCEPTRE low-MOI update | PMID `38760839`; DOI `10.1186/s13059-024-03254-2` | Low-MOI robust testing | Still needs appropriate controls and donor/run covariates | Prioritize for h5ad-level reanalysis |
| pertpy | PMID `41476114`; DOI `10.1038/s41592-025-02909-7` | scverse perturbation toolkit | Tool choice does not solve biological validation | Use for reproducible pipeline integration |
| scPerturb | PMID `38279009`; DOI `10.1038/s41592-023-02144-y` | Harmonized public perturbation resource | Heterogeneous datasets and metadata | Use as external lookup with context-match penalty |
| PerturBase | PMID `39377396`; DOI `10.1093/nar/gkae858` | Searchable perturbation database | Cross-dataset comparability limited | Add source-versioned evidence cache |
| PerturbDB | PMID `39265120`; DOI `10.1093/nar/gkae777` | Perturb-seq datasets/modules/networks | May mix modalities and preprocessing | Use for network/module hints, not direct readiness scoring |
| PerturbSeq.db | PMID `40381983`; DOI `10.1016/j.jmb.2025.169209` | Broad sc perturbation database | Evidence quality varies by dataset | Use context scoring and holdout validation |
| TCPGdb | PMID `41270225`; DOI `10.1158/2326-6066.CIR-25-0168` | T-cell perturbation screen database | T-cell context may be oncology-biased | High-priority external T-cell lookup, with disease/modality caveat |
| LINCS/CMap L1000 | PMID `29195078`; DOI `10.1016/j.cell.2017.10.049` | Drug signature matching | Mostly cell lines and L1000 genes, not primary CD4 | Use as weak drug-signature evidence only after context penalty |
| sci-Plex3 | PMID `31806696`; DOI `10.1126/science.aax6234` | Chemical perturbation scRNA precedent | Cell-line chemical response differs from primary immune response | Use as future design model for primary CD4 chemical perturbation |
| OneK1K | PMID `35389779`; DOI `10.1126/science.abf3041` | PBMC immune eQTL and disease context | Observational genetics, not perturbation proof | Add genetic support and patient heterogeneity layer |
| DICE | PMID `30449622`; DOI `10.1016/j.cell.2018.10.022` | Immune-cell expression/eQTL resource | Bulk/sorted immune context, not perturbation | Use for baseline expression and immune-cell specificity |
| Ota et al. perturbation + genetics model | PMID `41372418`; DOI `10.1038/s41586-025-09866-3` | Trait integration model | General model still needs target-specific validation | Use as template for connecting GWT programs to traits |
| Open Targets Platform | PMID `39657122`; DOI `10.1093/nar/gkae1128` | Target-disease/drug/safety overlay | Evidence aggregation can hide context mismatch | Store component evidence and do not double-count |
| ChEMBL 2023 | PMID `37933841`; DOI `10.1093/nar/gkad1004` | Bioactivity and drug-target metadata | Binding/assay evidence is not immune efficacy | Use for tractability and known ligand status |
| CELLxGENE Discover/Census | PMID `39607691`; DOI `10.1093/nar/gkae1142` | Baseline expression and atlas context | Atlas expression is observational and batch-variable | Use for disease-state/cell-type expression matching |

## Recommended Target-Card Fields

```text
target_gene
target_condition_id
culture_condition
gwt_effect_size
n_total_de_genes
top_up_genes
top_down_genes
ontarget_effect_size
ontarget_significant
guide_kd_efficiency
n_cells_target
n_guides
donor_n
crossdonor_correlation_mean
crossguide_correlation
offtarget_flag
batch_caveat
condition_specificity
program_scores
clinical_axis
intended_direction
disease_evidence_score
genetic_evidence_score
druggability_class
known_drugs
known_success_benchmark
known_failure_benchmark
safety_flags
readiness_stage
score_cap_reason
next_validation_experiment
```

## Recommended Score Caps

| Condition | Maximum readiness before new evidence |
|---|---|
| GWT signal only, no external support | R1/R2 |
| No donor or guide robustness | R1 or watchlist |
| Off-target flag | R1 unless independent guides validate |
| Missing knockdown evidence | R2 |
| RNA-only without protein/cytokine validation | R2/R3 |
| No disease/genetics/patient-state support | Disease relevance capped low |
| No plausible modality | Watchlist |
| Context mismatch with disease/drug benchmark | No clinical upgrade |
| Broad essential/chromatin/global suppression signal | Watchlist |
| Strong T-cell activation/cytokine-release risk | Validation only; often deprioritize |
| Treg destabilization risk | Validation only until Treg assays pass |
| JAK-like broad cytokine suppression | Safety-window cap |
| Trafficking/integrin/S1P axis | Requires tissue/egress safety evidence |
| Stim48hr-only claim | Add batch caveat; max R2 unless externally replicated |

## Anti-Overclaiming Rules

Allowed language:

- Research-use CD4 target hypothesis.
- Target-condition evidence.
- Candidate for orthogonal validation.
- Clinical precedent-informed safety caveat.
- Requires disease-context, protein, functional, and modality-specific validation.

Avoid before additional evidence:

- Clinical-ready.
- Drug-ready.
- Validated therapeutic target.
- Repurposing candidate.
- Predicts clinical efficacy or safety.
- Proves patient stratification.
- CRISPRi knockdown phenocopies a drug.

## Key Source Links

- GWT preprint DOI: https://doi.org/10.64898/2025.12.23.696273
- Shifrut primary T-cell SLICE/CROP-seq: https://pubmed.ncbi.nlm.nih.gov/30449619/
- Schmidt primary human T-cell CRISPRa/i: https://pubmed.ncbi.nlm.nih.gov/35113687/
- ECCITE-seq: https://pubmed.ncbi.nlm.nih.gov/31011186/
- Direct guide capture: https://pubmed.ncbi.nlm.nih.gov/32231336/
- Mixscape/ECCITE-seq QC: https://pubmed.ncbi.nlm.nih.gov/33649593/
- SCEPTRE: https://pubmed.ncbi.nlm.nih.gov/34930414/
- SCEPTRE low-MOI update: https://pubmed.ncbi.nlm.nih.gov/38760839/
- scPerturb: https://pubmed.ncbi.nlm.nih.gov/38279009/
- PerturBase: https://pubmed.ncbi.nlm.nih.gov/39377396/
- PerturbDB: https://pubmed.ncbi.nlm.nih.gov/39265120/
- TCPGdb: https://pubmed.ncbi.nlm.nih.gov/41270225/
- LINCS/CMap: https://pubmed.ncbi.nlm.nih.gov/29195078/
- OneK1K: https://pubmed.ncbi.nlm.nih.gov/35389779/
- Open Targets Platform: https://pubmed.ncbi.nlm.nih.gov/39657122/
