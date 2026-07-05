# CSV, Raw Cell Data, and Interactive Figure Roadmap

Date: 2026-07-05

## Scope

This roadmap separates the project into three workstreams:

1. Existing CSV / summary-table workflow.
2. Raw cell-level workflow for h5ad / 10x / external single-cell data.
3. Interactive bioinformatics figures and tables based on published Perturb-seq, T-cell CRISPR, and scRNA-seq integration literature.

The primary scientific unit remains:

```text
target x condition
```

The first usable product should be a CSV-first target evidence browser. Raw cell data should be brought in when the question requires cell-level QC, batch integration, guide assignment diagnostics, cell-state validation, or perturbation responder analysis.

## A. CSV-First Roadmap

### Data Sources

Local CSV sources:

```text
metadata/suppl_tables/DE_stats.suppl_table.csv
metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv
metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv
metadata/suppl_tables/sample_metadata.suppl_table.csv
metadata/suppl_tables/clustering_downstream_genes.csv
metadata/suppl_tables/clustering_results_and_annotations.csv
metadata/suppl_tables/cluster_autoimmune_enrichment_results.suppl_table.csv
metadata/suppl_tables/CD4T_aging_signature_DE_results_full.suppl_table.csv
metadata/suppl_tables/Th2_Th1_polarization_signature_DE_results_full.suppl_table.csv
metadata/suppl_tables/IL10IL21bulkRNAseq_DESeq2_results.csv
metadata/suppl_tables/IL10_IL21_arrayed_validation.csv
sources/topic05_successful_drug_benchmarks.csv
sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv
```

Implemented code:

```text
src/3_DE_analysis/build_target_cards.py
src/3_DE_analysis/target_card_api.py
src/3_DE_analysis/target_card_dashboard.py
src/3_DE_analysis/generate_target_report.py
```

### Ordered Steps

1. Data inventory and schema validation.
   - Confirm required columns for DE, guide/KD, sgRNA, sample metadata, pathway modules, and benchmark drug axes.
   - Output: `data_inventory.csv`, `schema_validation_report.md`.

2. Build target-condition base table.
   - Join DE statistics, guide/KD quality, donor/guide robustness, and condition metadata.
   - Output: `target_condition_base.csv`.

3. Add biological interpretation fields.
   - Map targets to CD4 pathway axes, upstream/downstream modules, autoimmune enrichment, aging/polarization/IL10-IL21 signatures.
   - Output: `target_condition_biology_features.csv`.

4. Add clinical and drug-development evidence.
   - Map targets to known drug axes, successful/failed clinical examples, safety warnings, and modality plausibility.
   - Output: `target_condition_clinical_features.csv`.

5. Create target cards.
   - Rank target-condition pairs using evidence grade, donor/guide robustness, KD support, DE magnitude, condition specificity, and caveats.
   - Output: `target_cards.csv`, `target_cards.json`, target detail reports.

6. Build interactive dashboard MVP.
   - Use only CSV-derived fields first.
   - Output: Streamlit dashboard and FastAPI endpoints.

7. Create ML-ready feature table.
   - Features should include perturbation strength, robustness, pathway/module scores, clinical axis, safety warning, and context match score.
   - Labels should be weak labels, not hard clinical success labels.
   - Output: `target_condition_features.csv`, `weak_labels.csv`, `benchmark_targets.csv`.

8. Select top candidates for raw-cell validation.
   - Use CSV dashboard to select targets with strong biology but unresolved cell-level questions.
   - Output: `raw_cell_validation_queue.csv`.

### What CSV Can Answer

CSV-first analysis is enough for:

- first-pass target-condition ranking
- evidence cards
- donor/guide/KD caveat display
- condition specificity
- pathway and clinical-axis mapping
- external evidence overlay
- report export
- weak ML feature construction

CSV-first analysis is not enough for:

- per-cell QC
- batch mixing diagnostics at cell level
- guide assignment UMI quality
- escaped/non-responder cells
- cell-state-specific effects
- Mixscape / pertpy perturbation-response calls
- SCEPTRE-like calibrated cell-level association testing

## B. Raw Cell-Level Roadmap

### Data Sources

Primary raw-cell source:

```text
Primary Human CD4+ T Cell Perturb-seq / GWT dataset
```

Known source description from the CZI Virtual Cell Platform:

- single-cell RNA-seq Perturb-seq / CRISPRi in primary human CD4 T cells
- all protein-coding or expressed-gene scale perturbations
- four donors
- three stimulation contexts
- approximately 22 million cells
- cell-level files use `D*_*.assigned_guide.h5ad` style artifacts
- metadata includes guide assignment and QC-related obs fields

Additional compatible raw-cell sources to consider later:

```text
CELLxGENE Census CD4 / T-cell atlases
scPerturb / PerturBase / PerturbDB / PerturbSeq.db
primary human T-cell CRISPRa / CRISPRi datasets
disease-state CD4 T-cell atlases
patient PBMC / tissue T-cell scRNA-seq datasets
```

Implemented scaffold:

```text
src/9_cell_integration/cell_integration_pipeline.py
src/9_cell_integration/cell_integration.example.yaml
src/9_cell_integration/manifest.template.csv
src/9_cell_integration/README.md
```

### Ordered Steps

1. Create manifest.
   - Each row should identify dataset, file path, format, species, tissue, cell type, donor, condition, stimulation time, assay, platform, batch/lane/library, perturbation type, and source.
   - Output: filled `manifest.csv`.

2. Ingest data.
   - Supported first formats: `h5ad`, `10x_h5`, `10x_mtx`.
   - Use backed/chunked strategy for large h5ad files when needed.
   - Output: loaded AnnData objects.

3. Harmonize metadata.
   - Standardize donor, condition, timepoint, guide, target, batch, sample, and source fields.
   - Output: harmonized `.obs` schema.

4. Run per-dataset QC.
   - Metrics: n_genes, n_counts, mitochondrial percentage, ribosomal percentage, doublet flags if available, guide UMI distribution, multi-guide rate.
   - Output: `cell_qc_summary.csv`, QC plots.

5. Build baseline uncorrected object.
   - Normalize/log transform, select HVG, PCA, UMAP without integration.
   - Output: `integrated_none.h5ad`.

6. Diagnose batch structure before correction.
   - Color UMAP/PCA by donor, lane, library, condition, dataset, guide, and source.
   - Quantify LISI/kBET/ASW-style metrics when feasible.
   - Output: `batch_diagnosis_report.md`.

7. Run integration sensitivity arms.
   - Start with `none`, `harmony`, and `scvi`; use `combat` only as a sensitivity check, not as the primary DE basis.
   - Output: `integrated_harmony.h5ad`, `integrated_scvi.h5ad`, `integration_metrics.csv`.

8. Transfer labels and score cell states.
   - Label transfer from compatible CD4/T-cell atlases.
   - Score CD4 activation, rest, exhaustion, Treg, Th1, Th2, Th17, Tfh, IL2/IFNG/IL17/IL10, NFAT, NF-kB, JAK/STAT modules.
   - Output: `cell_state_scores.csv`, updated h5ad.

9. Perturbation-specific validation.
   - Run guide assignment QC, target-level guide concordance, non-responder/escaped-cell detection, responder fraction, and target-condition pseudobulk checks.
   - Use pertpy/Mixscape-style perturbation response and SCEPTRE/pseudobulk-style association for selected top targets.
   - Output: `perturbation_validation_summary.csv`.

10. Return cell-level evidence to target cards.
   - Add fields such as responder fraction, cell-state-specific effect, batch sensitivity, guide assignment quality, and atlas context match.
   - Output: updated `target_cards.csv`.

### When To Touch Raw Cell Data

Use raw cell data after CSV triage, especially when a candidate is:

- high ranking but has batch caveats
- high ranking but weak guide/KD support
- condition-specific and needs cell-state confirmation
- clinically interesting but biologically ambiguous
- likely affected by responder/non-responder heterogeneity
- intended for external validation against another atlas or disease context

Do not use integrated corrected expression as the main DE evidence. Use integration for visualization, label transfer, cell-state matching, and sensitivity checks. For effect estimation, prefer raw-count-aware pseudobulk or calibrated perturbation models.

## C. PubMed-Guided Interactive Figures And Tables

### Literature Scan Keywords

The PubMed scan used existing project keywords:

```text
Perturb-seq single-cell CRISPR screen
primary human T cell CRISPR screen single-cell RNA-seq
SCEPTRE single-cell CRISPR screen
Mixscape single-cell CRISPR screen
single-cell RNA-seq batch correction integration benchmark
Perturb-CITE-seq single-cell CRISPR
CD4 T cell CRISPRa CRISPRi stimulation response
```

Partial PubMed results were saved here:

```text
sources/pubmed_figures_scan/pubmed_keyword_scan.csv
sources/pubmed_figures_scan/pubmed_keyword_scan.json
```

NCBI public API rate-limited the scan, so the current file is a first-pass result, not a complete systematic review.

### Key Published Anchors

Perturb-seq foundations:

- PMID 27984732: Perturb-seq, scalable single-cell RNA profiling of pooled CRISPR perturbations.
- PMID 27984733: multiplexed single-cell CRISPR screening for UPR dissection.
- PMID 35688146: genome-scale Perturb-seq genotype-phenotype landscapes.
- PMID 32231336: direct guide RNA capture and combinatorial single-cell CRISPR screens.

Perturbation statistics and response calling:

- PMID 34930414: SCEPTRE calibration and sensitivity for single-cell CRISPR screen analysis.
- PMID 38760839: robust differential expression testing for single-cell CRISPR screens.
- Perturb-CITE-seq / Mixscape family: perturbation-response calling, escaped/non-perturbed cells, multimodal RNA/protein evidence.

Batch correction and integration:

- PMID 31948481: benchmark of batch-effect correction methods for scRNA-seq; relevant metrics include runtime, correction efficacy, cell-type purity preservation, kBET, LISI, ASW, and ARI.

Primary human T-cell CRISPR:

- PMID 30449619: primary human T-cell genome-wide CRISPR screens with scRNA-seq stimulation-response programs.
- PMID 35113687: CRISPRa/CRISPRi screens in primary human T cells for stimulation-responsive cytokine regulation.
- Nature 2024 T-cell circuit paper: condition-aware CRISPR screens, activation/rest scores, and regulator-to-DE-gene networks.

## D. Dashboard MVP Figures From Existing CSV

These can be built immediately without raw cell downloads.

1. Target-condition ranking table.
   - Rows: target x condition.
   - Columns: evidence grade, n_cells, n_guides, n_donors, n_DE_genes, KD evidence, median logFC, fdr_min, pathway axis, clinical axis, score cap reason.
   - Interaction: filter by condition, evidence grade, pathway, caveat, target search.

2. Evidence-grade distribution.
   - Bar chart of `statistical_evidence_grade`.
   - Facet or color by condition.
   - Purpose: show how many candidates are strong, moderate, weak, or capped.

3. Condition x evidence heatmap.
   - Rows: conditions.
   - Columns: evidence grades or pathway axes.
   - Values: number of target-condition candidates.
   - Purpose: identify whether Rest, Stim8hr, or Stim48hr dominates the hit landscape.

4. Target-condition heatmap.
   - Rows: top targets.
   - Columns: Rest / Stim8hr / Stim48hr.
   - Color: selected score, evidence grade, n_DE_genes, or condition specificity.
   - Purpose: show context specificity.

5. Robustness plane.
   - X-axis: donor robustness or cross-donor correlation.
   - Y-axis: guide robustness or cross-guide correlation.
   - Color: evidence grade.
   - Size: n_cells or n_DE_genes.
   - Purpose: separate reproducible biology from fragile hits.

6. Perturbation effect scatter.
   - X-axis: n_cells_target or n_guides.
   - Y-axis: n_total_de_genes or max_abs_logFC.
   - Color: condition.
   - Purpose: distinguish broad transcriptional shifts from underpowered signals.

7. Score-cap reason chart.
   - Bar chart of reasons candidates were capped.
   - Purpose: immediately show what blocks drug-development readiness.

8. Pathway x clinical axis matrix.
   - Rows: CD4 biological pathway axes.
   - Columns: clinical precedent axes.
   - Values: candidate count or best evidence score.
   - Purpose: connect perturbation biology to drug-development strategy.

9. Target detail waterfall.
   - One selected target-condition card.
   - Shows contribution or penalty from DE strength, KD quality, donor robustness, guide robustness, pathway evidence, external precedent, and safety caveats.
   - Purpose: explain why a target is ranked high or low.

10. External evidence table.
   - Rows: target x evidence source.
   - Columns: disease relevance, druggability, known drugs, clinical stage, safety warning, context match, source date.
   - Purpose: make the target card auditable.

## E. Raw Cell Interactive Figures

These should be built after raw h5ad / 10x ingestion.

1. QC violin / ridge plots.
   - n_genes, n_counts, mitochondrial percentage, guide UMI count.
   - Group by dataset, donor, condition, lane, and source.

2. UMAP before and after integration.
   - Panels: uncorrected, Harmony, scVI.
   - Color by batch/source/donor/condition/cell state/guide/target.
   - Purpose: show whether integration removes nuisance variation while preserving biology.

3. Integration metric panel.
   - kBET, LISI, ASW, ARI, cell-type purity, runtime, memory.
   - Purpose: avoid judging batch correction by UMAP alone.

4. Guide assignment diagnostics.
   - Guide UMI distribution, multi-guide rate, NTC distribution, cells per guide, cells per target.
   - Purpose: identify poor guide assignment and perturbation-quality caveats.

5. Perturbation response density.
   - Mixscape/Mixscale-style perturbation score density per target.
   - Compare target-assigned cells vs NTC.
   - Purpose: estimate responder/non-responder structure.

6. Responder fraction plot.
   - Bar or dot plot of responder fraction by target, condition, donor, and guide.
   - Purpose: expose heterogeneous perturbation effects.

7. Pseudobulk PCA.
   - Pseudobulk profiles by target/guide/donor/condition.
   - Purpose: detect donor, condition, and guide-driven structure before DE interpretation.

8. Module score UMAP / dot plot.
   - CD4 activation/rest/exhaustion/Treg/Th1/Th2/Th17/Tfh and cytokine modules.
   - Purpose: translate gene-level perturbation into cell-state biology.

9. Volcano / MA plot for selected target-condition.
   - Requires full gene-level DE vectors.
   - Purpose: inspect downstream genes and effect direction.

10. Calibration diagnostics.
   - Null p-value histograms, QQ plots, guide-level null controls.
   - Purpose: SCEPTRE-like check that association tests are not inflated.

## F. Network And Drug-Development Figures

1. Target-to-downstream-gene network.
   - Nodes: perturbed targets and downstream DE genes/modules.
   - Edges: significant pseudobulk or SCEPTRE-style associations.
   - Color: condition or pathway axis.

2. Activation/rest regulator network.
   - Inspired by published T-cell CRISPR studies where perturbed regulators connect to activation score shifts and downstream DE genes.
   - Useful for CD4 activation, rest, and stimulation-response interpretation.

3. Drug-readiness ladder.
   - R0 to R5 stage-gated view.
   - Current data usually support R1-R3 only; R4-R5 require wet-lab, pharmacology, PK/PD, tox, CMC, and regulatory evidence.

4. Clinical precedent matrix.
   - Rows: CD4 pathways / targets.
   - Columns: known drug axes such as CD3, CD28/B7, CD40L, OX40/OX40L, IL-2/Treg, PD-1 agonism, JAK/STAT, IL-17/IL-23, S1P/integrin.
   - Values: evidence strength, success precedent, failure precedent, safety warning.

5. Safety warning matrix.
   - Rows: target/pathway.
   - Columns: cytokine storm, infection, malignancy, MACE, thrombosis, PML, immune-mediated toxicity, tissue-specific failure.

## G. Recommended Build Order

### Phase 1: CSV Dashboard Figures

Build now:

```text
target-condition ranking table
evidence-grade distribution
condition x evidence heatmap
target-condition heatmap
robustness plane
perturbation effect scatter
score-cap reason chart
pathway x clinical axis matrix
target detail waterfall
external evidence table
```

### Phase 2: External Evidence Overlay

Add:

```text
Open Targets / ChEMBL / DGIdb / DepMap / ClinicalTrials / PubMed adapters
context_match_score
source version/date/license tracking
clinical and safety evidence fields
```

### Phase 3: Raw Cell Pilot

Do not download all 22M cells first. Start with:

```text
one donor
one condition
top 50-200 target candidates plus NTC if subset files allow it
or one h5ad lane/sample for pipeline smoke testing
```

Run:

```text
ingestion
QC
uncorrected UMAP
batch diagnosis
Harmony/scVI sensitivity
guide assignment QC
module scoring
```

### Phase 4: Cell-Level Evidence Back To Cards

Add target-card fields:

```text
raw_cell_qc_pass
guide_assignment_pass
responder_fraction
cell_state_specificity
batch_sensitivity_score
integration_context_match
pseudobulk_validation_pass
```

### Phase 5: ML-Ready Table And Weak Ranking

Build:

```text
target_condition_features.csv
weak_labels.csv
benchmark_targets.csv
ranking model / PU-learning baseline
uncertainty and validation-priority output
```

## H. Immediate Decision

The next engineering step should be to expand the existing Streamlit dashboard with the Phase 1 CSV figures. This creates visible value before raw data transfer and defines exactly which raw-cell questions must be answered later.

The next scientific step should be to choose the first validation queue:

```text
top high-confidence target-condition pairs
+ top clinically interesting but caveated pairs
+ NTC / known pathway controls
```

This queue determines the smallest raw-cell subset worth downloading first.

