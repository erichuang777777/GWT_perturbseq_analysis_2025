# CD4 Perturb-seq Drug-Development Toolkit - Decision Log

Date: 2026-07-04

## 1. Product Positioning

The project should be positioned as a research-use target evidence and validation-prioritization platform, not as a drug discovery engine.

Recommended framing:

```text
A CD4 Perturb-seq target-condition evidence and validation-prioritization platform for early drug discovery.
```

Allowed claims:

- Helps prioritize target-condition hypotheses.
- Helps organize Perturb-seq, cell-level, external evidence, and clinical precedent.
- Helps plan validation experiments.
- Helps identify QC caveats, context mismatch, and safety risks.

Claims to avoid:

- Predicts drug success.
- Produces clinical-ready targets.
- Replaces wet-lab validation.
- Proves efficacy or safety.
- Treats CRISPRi knockdown as equivalent to pharmacologic inhibition, antibody blockade, agonism, degradation, or cell therapy.

## 2. Core Scientific Unit

The primary unit should be:

```text
target x condition
```

not just gene-level target.

Reason:

- A target can behave differently in `Rest`, `Stim8hr`, and `Stim48hr`.
- Therapeutic meaning depends on context.
- Drug-development direction depends on condition, disease setting, and intended mechanism.

## 3. Target Card Definition

A target card is an evidence dossier for one `target x condition`.

It is not a new experimental result. It is a decision-support layer that converts scattered data into a consistent, auditable structure.

Required target-card fields:

```text
target
condition
target_id
n_cells_target
n_guides
n_donors
n_total_de_genes
n_up_genes
n_down_genes
ontarget_effect_size
ontarget_significant
offtarget_flag
median_logFC
max_abs_logFC
fdr_min
crossdonor_correlation_mean
crossdonor_correlation_min
crossguide_correlation
replicate_pass_flag
batch_sensitivity_flag
guide_signif_ratio
guide_fdr_min
guide_t_abs_median
positive_control_similarity
pathway_axis
condition_specificity_score
clinical_axis
nearest_success_drug
nearest_failure_or_warning
statistical_evidence_grade
score_cap_reason
```

Purpose:

- Rank target-condition hypotheses.
- Separate strong biology from weak QC.
- Surface caveats before overinterpretation.
- Map hits to CD4 pathway and clinical drug axes.
- Suggest the next validation experiment.

## 4. Current CSV-First Strategy

Decision:

Start with CSV/summary-table workflows before downloading or processing the full raw h5ad dataset.

Reason:

- The local repository already contains enough summary tables to build a useful MVP.
- Full cell-level data are large and should be used after prioritization.
- CSV-first enables fast target-card generation, dashboarding, and ML-ready feature engineering.

Current CSV inputs:

```text
metadata/suppl_tables/DE_stats.suppl_table.csv
metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv
metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv
metadata/suppl_tables/sample_metadata.suppl_table.csv
sources/topic05_successful_drug_benchmarks.csv
sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv
```

Current local scale:

- 33,983 target-condition DE rows.
- 11,526 unique perturbed target genes.
- 3 conditions: `Rest`, `Stim8hr`, `Stim48hr`.
- Strict local filter leaves roughly 1.1k-1.2k high-confidence target-condition candidates.

## 5. When Raw Cell-Level Data Are Needed

CSV-first is sufficient for:

- target cards
- evidence browser
- first-pass ranking
- guide/KD summary
- donor/guide robustness caveats
- off-target/low-cell/batch caveats
- clinical axis mapping
- pathway seed mapping
- report export
- first version of ML-ready feature table

Raw `.h5ad` or 10x cell-level data are needed for:

- per-cell QC
- guide assignment diagnostics
- doublet and multi-guide checks
- escaped/non-responder cell detection
- responder fraction
- cell-state-specific perturbation effects
- subtype-specific CD4 effects
- robust batch diagnosis
- Mixscape / pertpy workflows
- SCEPTRE or calibrated perturbation-gene association testing
- UCell/AUCell/PROGENy/DoRothEA cell-level program scoring
- deeper validation of top targets

Decision:

Use raw cell data after CSV triage, especially for top targets or external atlas validation.

## 6. Two Data Streams

The platform must support two complementary data streams.

### A. Cell-Level Integration Stream

Input:

```text
h5ad / 10x / external atlas / external perturbation scRNA
```

Workflow:

```text
manifest-driven ingestion
-> metadata harmonization
-> QC
-> AnnData concatenation
-> normalization / HVG / PCA
-> optional batch correction or integration
-> UMAP / Leiden / cell-state analysis
-> integrated h5ad + summary outputs
-> evidence returned to target cards
```

Supported first-pass integration methods:

- `none`: PCA baseline.
- `combat`: expression-level correction sensitivity only.
- `harmony`: batch-corrected PCA representation.
- `scvi`: probabilistic integration from raw counts.

Guardrail:

Integrated embeddings should be used for visualization, cell-state matching, and sensitivity checks. They should not be the primary source for DE target-effect inference.

Implemented scaffold:

```text
src/9_cell_integration/cell_integration_pipeline.py
src/9_cell_integration/cell_integration.example.yaml
src/9_cell_integration/manifest.template.csv
src/9_cell_integration/README.md
```

### B. Evidence-Only Validation Stream

Input:

```text
Open Targets
ChEMBL
DrugBank / DrugCentral
DGIdb
DepMap
GTEx
Human Protein Atlas
DICE
OneK1K
CELLxGENE Census
LINCS / CMap
ClinicalTrials.gov
FDA labels / DailyMed
PubMed
scPerturb / PerturBase / PerturbDB / PerturbSeq.db / TCPGdb
```

Workflow:

```text
external source
-> standardized evidence table
-> context match score
-> source/version/date/license tracking
-> clinical, safety, druggability, disease overlay
-> evidence returned to target cards
```

Evidence-only data should not be forced into cell-level integration unless context and modality are compatible.

## 7. External Data Integration Decision

External data can be used in two ways:

1. Direct cell-level integration, if cell type, species, assay, tissue, and metadata are sufficiently compatible.
2. Evidence-only validation, if the resource provides target, disease, drug, safety, genetics, or clinical evidence but is not a compatible raw-cell dataset.

Decision:

Do not batch-correct all external resources into one embedding by default. Use a `context_match_score` to decide whether a source belongs in the cell-level stream or the evidence-only stream.

Context dimensions:

```text
species
cell_type
cell_subtype
tissue
disease
stimulus
condition
timepoint
assay
platform
perturbation_type
modality
```

## 8. Batch Correction Decision

Assume donor/run/library/lane nuisance structure exists.

Do not use blanket batch-corrected expression values as the main DE evidence.

Recommended use:

- Raw-count / pseudobulk model for target-effect inference.
- Batch correction for embedding, visualization, label transfer, atlas mapping, and sensitivity checks.
- Donor and guide robustness should be explicit confidence evidence.
- `Stim48hr` should carry a run/batch caveat unless externally validated.

## 9. ML Strategy

Machine learning is useful, but positive labels are scarce and noisy.

Decision:

Do not start with a binary classifier for clinical success/failure.

Recommended ML tasks:

- weakly supervised ranking
- positive-unlabeled learning
- similarity to known CD4 drug axes
- perturbation signature embedding
- target-condition feature learning
- uncertainty estimation
- active learning for next-experiment recommendation

Recommended label design:

```text
biology_positive_label
clinical_precedent_label
safety_warning_label
```

Model outputs should be:

```text
biology confidence
clinical precedent similarity
safety risk
uncertainty
validation priority
```

not:

```text
drug success probability
```

## 10. Drug-Development Readiness Scale

Use a stage-gated readiness scale:

```text
R0: deprioritize / weak or unsafe
R1: exploratory
R2: hypothesis-ready
R3: validation-ready
R4: preclinical-candidate-like research package
R5: nomination-ready
```

Important constraint:

GWT + target-card + ML can usually reach only `R2/R3`. `R4/R5` requires wet-lab validation, modality evidence, pharmacology, PK/PD, toxicology, CMC, and regulatory package.

Score caps:

- Off-target flag: cap at low readiness unless independent guides validate.
- Weak donor/guide robustness: cap at exploratory/watchlist.
- Missing knockdown evidence: cap target confidence.
- RNA-only signal: requires protein/cytokine/functional validation.
- No disease/genetics/patient-state support: cap disease relevance.
- No plausible modality: watchlist or deprioritize.
- Broad essential/chromatin/global suppression: watchlist.
- T-cell activation/cytokine-release risk: validation-only or deprioritize.
- `Stim48hr`-only signal: add batch caveat.

## 11. Clinical Benchmark Axes

Target cards should map hits to clinical precedent axes.

Positive or informative axes:

```text
CD3/TCR tolerance: teplizumab, foralumab
CD28/B7 costimulation blockade: abatacept, belatacept
CD40L/CD154: frexalimab, dapirolizumab, tegoprubart
OX40/OX40L: rocatinlimab, amlitelimab
IL-2/Treg: low-dose IL-2, rezpegaldesleukin, basiliximab
PD-1 agonism / tolerance: peresolimab, rosnilimab
JAK/STAT: tofacitinib, upadacitinib, baricitinib, TYK2 agents
IL-17/IL-23/Th17: secukinumab, ustekinumab, risankizumab
S1P/integrin trafficking: fingolimod, ozanimod, vedolizumab, natalizumab
Direct CD4: ibalizumab
```

Failure/safety warning anchors:

```text
TGN1412 / CD28 agonism / cytokine storm
BG9588 / anti-CD40L / thromboembolism
daclizumab / IL2RA / immune-mediated toxicity
tofacitinib ORAL Surveillance / MACE, malignancy, infection
secukinumab in Crohn's disease / IL-17 tissue-specific failure
abatacept in IBD / indication mismatch
natalizumab / PML risk
otelixizumab / anti-CD3 Phase 3 failure
```

## 12. Validation Planning

Each target card should suggest a next validation experiment.

Candidate validation assays:

```text
independent sgRNA
CRISPRi/a rescue
siRNA validation
tool compound or antibody perturbation
flow cytometry: CD69, CD25, FOXP3, CTLA4
cytokines: IL2, IFNG, IL17A, IL10
phospho-flow: pSTAT, pZAP70, pNFAT
proliferation / apoptosis
Treg suppression assay
Th17 / Th1 / Tfh functional assay
patient ex vivo CD4 validation
```

## 13. Current Implemented Components

CSV-first target-card tool:

```text
src/3_DE_analysis/build_target_cards.py
```

FastAPI service:

```text
src/3_DE_analysis/target_card_api.py
```

Interactive evidence browser:

```text
src/3_DE_analysis/target_card_dashboard.py
```

Report generator:

```text
src/3_DE_analysis/generate_target_report.py
```

Cell-level integration scaffold:

```text
src/9_cell_integration/cell_integration_pipeline.py
```

Running services from latest test:

```text
API: http://127.0.0.1:8004
Dashboard: http://127.0.0.1:8503
```

## 14. Recommended Next Development Steps

Priority 1: External evidence schema and loaders.

Build:

```text
external_evidence_table
target_external_evidence_api
Open Targets / ChEMBL / DepMap / ClinicalTrials adapters
context_match_score
source/version/date tracking
```

Priority 2: Cell-level bridge back to target cards.

Build:

```text
integrated cell-state summary
target cell-state enrichment
module score by dataset / condition / cluster
batch sensitivity summary
target-card evidence fields from integrated h5ad
```

Priority 3: ML-ready feature table.

Build:

```text
features.csv
weak_labels.csv
benchmark_targets.csv
training/evaluation split
PU-learning or ranking baseline
uncertainty and validation-priority output
```

Priority 4: Guide/perturbation cell-level validation.

Add:

```text
guide assignment QC
escaped / non-responder analysis
Mixscape / pertpy integration
SCEPTRE or pseudobulk validation for top targets
```

## 15. Strategic Decision

The platform should not be a single monolithic model.

It should be an evidence system:

```text
CSV perturbation evidence
+ raw cell integration evidence
+ external database evidence
+ clinical benchmark evidence
+ weak ML prioritization
= transparent target-condition decision support
```

This is the most defensible direction scientifically and technically.
