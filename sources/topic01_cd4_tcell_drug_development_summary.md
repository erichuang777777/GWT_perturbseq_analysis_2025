# Topic 1: CD4 T Cell Perturb-seq Data for Drug Development

Date: 2026-07-04

## Bottom Line

This GWT primary human CD4+ T cell CRISPRi Perturb-seq dataset is most immediately useful as a target-to-therapeutic-hypothesis engine, not as a direct drug-candidate generator.

The most practical near-term output is a ranked, explainable set of target, pathway, disease-module, and safety hypotheses from causal transcriptomic perturbation effects across Rest, Stim8hr, and Stim48hr states.

## Best-Fit Drug Development Directions

1. Target discovery and target prioritization
   - Best fit for this dataset.
   - Local start: rank targets by DE strength, condition specificity, on-target significance, cross-donor robustness, cross-guide concordance, and knockdown efficiency.
   - External validation needed: Open Targets, ChEMBL, DrugBank, protein-level assays, cytokine secretion, proliferation, flow cytometry, small molecule or antibody replication.

2. Pathway and MoA prioritization
   - Strong fit because Perturb-seq gives downstream transcriptional programs, not only single markers.
   - Local start: map perturbation signatures to TCR activation, IL-2/IL2RA, CTLA4/CD28, NF-kB, JAK/STAT, Th17/Treg, and polarization modules.
   - External validation needed: Reactome, GO, MSigDB, OmniPath, STRING, phosphoproteomics, pathway reporter assays.

3. Autoimmune / inflammatory indication mapping
   - Highest disease-area fit because primary CD4 T cells are central to Th17/Treg biology, IL-2 signaling, costimulation, and immune-mediated traits.
   - Local start: use Open Targets autoimmune genes already in the repo, cluster autoimmune enrichment, disease gene associations, and perturbation signatures.
   - External validation needed: GWAS fine-mapping, eQTL/colocalization, disease scRNA atlases for RA, IBD, MS, psoriasis, SLE, and clinical response datasets.

4. Target validation
   - Good fit for transcriptomic validation of causal CD4 T cell target effects.
   - Local start: donor robustness, guide-level concordance, KD efficiency versus downstream effects, and concordance with known T cell CRISPR screens.
   - External validation needed: CRISPR KO/a, siRNA, small molecule perturbation, arrayed assays, IL2/IFNG/IL17A/IL10/FOXP3/CD25/CD69 readouts.

5. Drug repurposing
   - Medium fit until drug signatures are added.
   - Local start: export robust target-condition up/down gene signatures.
   - External validation needed: LINCS L1000 / CMap, immune-cell drug perturbation atlases, drug-target annotation, cell-type mismatch checks.

6. Immune toxicity and safety filtering
   - Useful as a prioritization layer.
   - Local start: flag broad T cell dysfunction signatures, core essential overlap, IUIS IEI overlap, ClinVar LoF, immune effector genes.
   - External validation needed: FAERS, broader immune cell screens, in vivo or organoid immune safety models.

7. Cancer immunotherapy, transplant tolerance, and vaccine response
   - Useful secondary areas.
   - Cancer: strongest for CD4 help/activation engineering, not full CD8/CAR-T/TME modeling.
   - Transplant: relevant to CD28/CTLA4 and Treg/tolerance pathways, but lacks alloantigen-specific stimulation.
   - Vaccine: relevant to CD4 activation and Th1/Tfh-like regulation, but lacks antigen-specific stimulation and B cell help readout.

## Tool Kit Opportunities

1. Target Card Generator
   - Per gene: KD efficiency, DE strength, condition specificity, donor robustness, guide concordance, pathway modules, disease links, druggability, safety flags.

2. Condition-Specific Target Browser
   - Rest / Stim8hr / Stim48hr views for early activation, late effector, and resting-state dependency targets.

3. Disease Module Mapper
   - Enrichment and reversal scoring against autoimmune, cancer immunity, vaccine response, and transplant tolerance modules.

4. Druggability + Safety Filter
   - Overlay kinases, GPCRs, ion channels, cytokine receptors, enzymes, ClinVar, IUIS IEI, and core essential genes.

5. Repurposing Connector
   - Export robust perturbation signatures into LINCS/CMap-ready query format.

## Local Prototype Findings

Using the existing local `DE_stats.suppl_table.csv` and repo gene lists:

- DE rows: 33,983
- Unique perturbed targets: 11,526
- Targets overlapping common druggable classes: 1,014
- Strong rows using coarse filter `n_total_de_genes >= 100`, `ontarget_significant == True`, `offtarget_flag == False`: 2,174
- Strong unique targets: 1,269
- Strong druggable-class targets: 78

Top local druggable-class examples by breadth/effect include ZAP70, ATP2A2, SMG1, LCK, SIK3, INSR, STK11, CDK13, IL12RB2, CSK, LRRC8A, RIPK1, and RXRB.

Saved local output:
- `sources/topic01_local_druggable_targets_summary.csv`
- `sources/topic01_local_druggable_targets_summary.json`

## High-Signal Sources

Directly supports this data type for drug discovery:

- GWT dataset/preprint: DOI `10.64898/2025.12.23.696273`
- PMID `30449619`, DOI `10.1016/j.cell.2018.10.024`: Genome-wide CRISPR screens in primary human T cells.
- PMID `35113687`, DOI `10.1126/science.abj4008`: CRISPRa/i screens decode stimulation responses in primary human T cells.
- PMID `35817986`, DOI `10.1038/s41588-022-01106-y`: Regulatory genes and immune networks in human T cells.
- PMID `32989329`, DOI `10.1038/s41590-020-0784-4`: CRISPR dissection of human Treg identity.
- PMID `27984732`, DOI `10.1016/j.cell.2016.11.038`: Foundational Perturb-seq.
- PMID `27984733`, DOI `10.1016/j.cell.2016.11.048`: Multiplexed single-cell CRISPR screening.
- PMID `35688146`, DOI `10.1016/j.cell.2022.05.013`: Genome-scale Perturb-seq genotype-phenotype landscapes.
- PMID `37117846`, DOI `10.1038/s41573-023-00688-4`: scRNA-seq in drug discovery and development.
- PMID `33196847`, DOI `10.1093/nar/gkaa1027`: Open Targets Platform.
- PMID `39657122`, DOI `10.1093/nar/gkae1128`: Open Targets Platform update.
- PMID `29195078`, DOI `10.1016/j.cell.2017.10.049`: LINCS/CMap L1000.
- PMID `31253980`, DOI `10.1038/s41588-019-0456-1`: Genetics-led immune trait drug target landscape.

Background immunology / disease-context sources:

- PMID `30057419`, DOI `10.1038/s41577-018-0044-0`: CD4 T cell help in cancer immunology and immunotherapy.
- PMID `34453880`, DOI `10.1016/j.immuni.2021.08.001`: Antigen-specific CD4 T cells in mRNA vaccination.
- PMID `40887501`, DOI `10.1038/s12276-025-01535-9`: Th17 pathogenicity in autoimmune disease.
- PMID `35005594`, DOI `10.1016/j.jtauto.2021.100130`: Treg function in autoimmune disease.
- PMID `39889703`, DOI `10.1016/j.immuni.2025.01.008`: CD4 epitopes in transplant rejection/tolerance.
- PMID `31520803`, DOI `10.1016/j.autrev.2019.102390`: JAK inhibitors in autoimmune/inflammatory disease.
- PMID `37882232`, DOI `10.1080/08830185.2023.2274574`: Low-dose IL-2 therapy in autoimmune disease.
- PMID `27591335`, DOI `10.4049/jimmunol.1601135`: CD28 pathway costimulation blockade.

## Next Actionable Analyses

1. Robust target ranking from DE strength, donor robustness, guide concordance, condition specificity.
2. KD-aware filtering using guide knockdown efficiency.
3. Condition specificity matrix: Rest-only, Stim8hr-only, Stim48hr-only, pan-condition.
4. Druggable target overlay using kinases, GPCRs, ion channels, cytokine receptors, enzymes.
5. Autoimmune prioritization score using Open Targets autoimmune genes and enrichment tables.
6. T cell polarization impact score using Th1/Th2/Th17/Treg-related outputs.
7. Safety flagging layer using IUIS IEI, core essential genes, ClinVar LoF, immune effector genes.
8. Known T cell CRISPR screen concordance check.
9. Signature export for CMap/LINCS.
10. Target Card MVP for top 50 candidates.

## Remaining Questions

1. Can GWT CD4 perturbation signatures be compared cleanly to LINCS/CMap cancer-cell-line signatures, or do we need immune-specific drug perturbation data?
2. Which autoimmune GWAS causal genes have strong context-specific trans-effects and druggability in GWT?
3. Do Stim8hr and Stim48hr reliably separate acute activation from polarization-like programs?
4. How transferable are CD4-only hits to cancer immunotherapy, especially CD8/CAR-T persistence and exhaustion?
5. Which hits are promising immune-modulation targets but carry infection, cytokine, Treg, or broad immunosuppression risk?

