# Topic 7 - 類似資料、成果、研究論文與 PMID

## Executive takeaways

GWT primary human CD4 Perturb-seq 的最佳外部 validation 不是一般 cell-line Perturb-seq，而是 primary human T cell/CD4 perturbation、T-cell regulatory network、immune disease genetics、以及 perturbation QC/statistical method papers。

最重要的使用方式：

- **Primary T-cell validation**: 驗證 GWT target cards 是否找得到 TCR activation、IL-2/IFN-gamma、rest/activation、Treg/FOXP3/costimulation 等已知 biology。
- **Pipeline/statistical validation**: 驗證 guide assignment、escaped/non-responder cells、low-MOI testing、pseudobulk/single-cell DE。
- **Disease/drug matching**: 將 GWT target effects 連到 autoimmune genetics、patient single-cell atlases、CMap/LINCS/chemical perturbation。
- **Resource lookup**: 用 scPerturb/PerturBase/PerturbDB/PerturbSeq.db/TCPGdb 查 target 是否在其他 perturbation screens 出現。

## Highest-priority papers for GWT target-card validation

| Use | Paper/resource | PMID/DOI | Dataset/resource | Relevance |
|---|---|---|---|---|
| Main GWT anchor | Zhu/Dann et al., genome-scale Perturb-seq in primary human CD4+ T cells | DOI `10.64898/2025.12.23.696273`; preprint, no PMID | GWT public S3/CZI data | Internal ground truth for target ranking, condition specificity, donor/guide robustness |
| Primary T-cell validation | Shifrut et al., primary human T-cell SLICE/CROP-seq | PMID `30449619`; DOI `10.1016/j.cell.2018.10.024`; PMC6689405 | GSE119450 | Best public predecessor for primary human T-cell perturbation benchmarking |
| Primary T-cell validation | Schmidt et al., CRISPRa/i screens in primary human T cells | PMID `35113687`; DOI `10.1126/science.abj4008`; PMC9307090 | GSE190604 | Directionality benchmark for IL-2/IFN-gamma stimulation-response networks |
| Primary T-cell validation | Arce et al., T-cell rest/activation circuits | PMID `39663454`; DOI `10.1038/s41586-024-08314-y`; PMC11754113 | paper/code resource | Strong targeted CD4+ T-cell validation set for Rest vs Stim signatures |
| Primary CD4 GRN | Weinstock et al., CD4 GRN inference | PMID `39395408`; DOI `10.1016/j.xgen.2024.100671` | primary CD4 perturbation map | Network-edge, IEI, JAK-STAT, and CD4 regulatory validation |
| Primary T-cell networks | Freimer et al., T-cell effector screens | PMID `36356142`; DOI `10.1126/science.abn5647`; PMC10335827 | primary human T-cell screens | Effector/cytokine regulator cross-check |
| Autoimmune variants | Ho et al., autoimmune variants + primary CD4 T-cell MPRA/CRISPRi | PMID `40968290`; DOI `10.1038/s41588-025-02301-3`; PMC12513834 | primary CD4 MPRA + CRISPRi | Links autoimmune causal variants to T-cell networks |
| In vivo T-cell validation | Zhou et al., in vivo single-cell CRISPR T-cell fate regulomes | PMID `37968405`; DOI `10.1038/s41586-023-06733-x`; PMC10700132 | in vivo T-cell CRISPR screens | Compare in-vitro CD4 programs to in-vivo T-cell fate regulation |
| CAR T translational validation | Knudsen et al., CAR T modifiers | PMID `40993381`; DOI `10.1038/s41586-025-09489-8`; PMC12806180 | FITdb Perturb-seq view | Translational comparator for T-cell engineering targets |

## Safety and directionality references

| Use | Reference | PMID/DOI | Why it matters |
|---|---|---|---|
| Direct CD4 caution | Ibalizumab anti-CD4 HIV trial | PMID `30110589`; DOI `10.1056/NEJMoa1711460` | CD4 is druggable, but success is antiviral entry blockade, not autoimmune CD4 modulation |
| TCR tolerance | Teplizumab anti-CD3 in T1D prevention | PMID `31180194`; DOI `10.1056/NEJMoa1902226` | T-cell tolerance anchor; CRS/lymphopenia safety warning |
| Costimulation | Abatacept CD80/CD86-CD28 blockade | PMID `16785475`; DOI `10.7326/0003-4819-144-12-200606200-00003` | Costimulation blockade benchmark |
| Calcineurin/NFAT | Cyclosporine in transplant | PMID `6350878`; DOI `10.1056/NEJM198310063091401` | Strong TCR suppression, narrow therapeutic window |
| JAK safety | ORAL Surveillance tofacitinib | PMID `35081280`; DOI `10.1056/NEJMoa2109927` | Safety cap for JAK-like signatures: MACE, cancer, infection |
| S1P trafficking | Fingolimod in MS | PMID `20089952`; DOI `10.1056/NEJMoa0909494` | Trafficking effects are not fully captured by in-vitro CD4 RNA |
| Checkpoint activation | Ipilimumab melanoma | PMID `20525992`; DOI `10.1056/NEJMoa1003466` | Oncology direction can be immune-boosting rather than suppressive |

## Pipeline, perturbation, and statistical method references

| Use | Reference | PMID/DOI | Relevance |
|---|---|---|---|
| Foundational method | Perturb-seq | PMID `27984732`; DOI `10.1016/j.cell.2016.11.038`; PMC5181115 | Foundational pooled genetic perturbation plus scRNA-seq method |
| Immune CRISP-seq | Jaitin et al. CRISP-seq | PMID `27984734`; DOI `10.1016/j.cell.2016.11.039` | Early immune-cell single-cell perturbation precedent |
| CROP-seq/TCR benchmark | Datlinger et al. CROP-seq | PMID `28099430`; DOI `10.1038/nmeth.4177`; PMC5334791 | Guide capture and Jurkat TCR signaling benchmark; lower biological relevance than primary CD4 |
| Multimodal design | ECCITE-seq | PMID `31011186`; DOI `10.1038/s41592-019-0392-0`; PMC6557128 | RNA, protein, clonotype, and CRISPR perturbation readout |
| Guide assignment | Direct guide capture Perturb-seq | PMID `32231336`; DOI `10.1038/s41587-020-0470-y`; PMC7416462 | sgRNA assignment and combinatorial screen design |
| Genome-scale reference | Replogle genome-scale Perturb-seq | PMID `35688146`; DOI `10.1016/j.cell.2022.05.013`; PMC9380471 | Broad genome-scale perturbation/effect modeling reference |
| Genetic interactions | Norman et al. | PMID `31395745`; DOI `10.1126/science.aax4438`; PMC6746554 | Combinatorial perturbation and phenotype manifold interpretation |
| RNA+protein perturbation QC | Papalexi et al. Mixscape/ECCITE-seq | PMID `33649593`; DOI `10.1038/s41588-021-00778-2`; PMC8011839 | Escaped/non-responder perturbation handling |
| Immune evasion perturbation | Frangieh et al. Perturb-CITE-seq | PMID `33649592`; DOI `10.1038/s41588-021-00779-1`; PMC8376399 | Patient model, RNA+protein, immune-evasion modules |
| Genotype-to-phenotype method | scMAGeCK | PMID `31980032`; DOI `10.1186/s13059-020-1928-4`; PMC6979386 | Links CRISPR genotypes to multiple single-cell phenotypes |
| Association testing | SCEPTRE | PMID `34930414`; DOI `10.1186/s13059-021-02545-2`; PMC8686614 | Calibrated scCRISPR association testing |
| Low-MOI robust testing | SCEPTRE low-MOI update | PMID `38760839`; DOI `10.1186/s13059-024-03254-2` | Robust differential expression testing at low MOI |
| AnnData toolkit | pertpy | PMID `41476114`; DOI `10.1038/s41592-025-02909-7`; PMC12904789 | End-to-end scverse perturbation framework |

## Drug, disease, and target evidence references

| Use | Reference/resource | PMID/DOI | Relevance |
|---|---|---|---|
| Drug signatures | LINCS/CMap L1000 | PMID `29195078`; DOI `10.1016/j.cell.2017.10.049` | Drug-signature matching backbone |
| Chemical perturbation | sci-Plex3 | PMID `31806696`; DOI `10.1126/science.aax6234`; PMC7289078 | Single-cell chemical transcriptomics |
| Benchmark framework | Open Problems single-cell benchmark | PMID `40595413`; DOI `10.1038/s41587-025-02694-w` | Benchmark framework; PBMC drug task is resource-level |
| Immune eQTL/autoimmune genetics | OneK1K | PMID `35389779`; DOI `10.1126/science.abf3041` | 1.27M PBMCs, immune cell eQTLs, autoimmune disease context |
| Immune expression/eQTL | DICE | PMID `30449622`; DOI `10.1016/j.cell.2018.10.022` | Immune-cell expression and eQTL context |
| SLE atlas | Lupus PBMC atlas | PMID `35389781`; DOI `10.1126/science.abf1970` | SLE immune-state matching |
| UC tissue atlas | UC colon atlas | PMID `31348891`; DOI `10.1016/j.cell.2019.06.029` | IBD tissue disease programs |
| Crohn therapy resistance | Crohn anti-TNF resistance atlas | PMID `31474370`; DOI `10.1016/j.cell.2019.08.008` | Therapy-resistance disease modules |
| RA tissue atlas | RA synovium AMP atlas | PMID `31061532`; DOI `10.1038/s41590-019-0378-1` | RA tissue immune states |
| RA inflammatory subtypes | RA synovium phase II atlas | PMID `37938773`; DOI `10.1038/s41586-023-06708-y` | Larger RA inflammatory subtype map |
| Trait integration | Ota et al. perturbation + genetics model | PMID `41372418`; DOI `10.1038/s41586-025-09866-3` | Integrates regulators, programs, and genetic associations |

## Databases and resources

| Resource | PMID/DOI | Role |
|---|---|---|
| scPerturb | PMID `38279009`; DOI `10.1038/s41592-023-02144-y`; PMC12220817 | Harmonized public single-cell perturbation datasets |
| PerturBase | PMID `39377396`; DOI `10.1093/nar/gkae858`; PMC11701531 | Searchable single-cell perturbation database |
| PerturbDB | PMID `39265120`; DOI `10.1093/nar/gkae777`; PMC11701683 | Perturb-seq datasets, gene-function modules, networks |
| PerturbSeq.db | PMID `40381983`; DOI `10.1016/j.jmb.2025.169209` | Broad single-cell perturbation database |
| TCPGdb | PMID `41270225`; DOI `10.1158/2326-6066.CIR-25-0168` | T-cell-specific perturbation screen database |
| Open Targets Platform | PMID `39657122`; DOI `10.1093/nar/gkae1128` | Target-disease, tractability, safety, drugs, genetics |
| ChEMBL 2023 | PMID `37933841`; DOI `10.1093/nar/gkad1004` | Drug/target/bioactivity metadata |
| CELLxGENE Discover/Census | PMID `39607691`; DOI `10.1093/nar/gkae1142` | Baseline expression and atlas context |
| Tahoe-100M / Arc Virtual Cell Atlas | DOI `10.1101/2025.02.20.639398`; preprint, no PMID | Optional large chemical perturbation resource |

## Papers to prioritize for Topic 12 limitations/future work

1. ECCITE-seq, PMID `31011186`: GWT RNA-only limitation; future protein/TCR/multimodal readout.
2. Papalexi/Mixscape, PMID `33649593`: escaped/non-responding perturbations and perturbation-response confidence.
3. Direct guide capture, PMID `32231336`: guide assignment and future combinatorial perturbation upgrades.
4. SCEPTRE and low-MOI update, PMIDs `34930414`, `38760839`: statistical calibration, low-MOI testing, pseudobulk versus single-cell modeling.
5. Ota perturbation + genetics, PMID `41372418`: future target cards should link perturbation programs to traits and causal human genetics.
6. OneK1K, PMID `35389779`: population variation/eQTL/disease genetics are external validation, not something GWT alone answers.
7. PerturbDB/PerturbSeq.db/TCPGdb, PMIDs `39265120`, `40381983`, `41270225`: future cross-study benchmarking and T-cell-specific evidence cache.

## Practical benchmark rule

A GWT target card should be considered `validation-ready` only if it has robust GWT effect, donor/guide consistency, signed agreement with at least one primary T-cell perturbation paper, disease/genetics support from Open Targets or scRNA/eQTL atlases, and no major safety contradiction from Treg/costimulation/JAK/IL-2 benchmark axes.
