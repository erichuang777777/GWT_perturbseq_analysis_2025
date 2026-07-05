# Project Roadmap

Date: 2026-07-04

## Goal

Build a research-use CD4 Perturb-seq platform that supports:

```text
target-condition evidence browsing
cell-level integration with external datasets
external evidence validation
ML-assisted prioritization
validation experiment planning
```

## Architecture

```text
CSV summary stream
  -> target cards

Cell-level stream
  -> h5ad / 10x ingestion
  -> metadata harmonization
  -> QC
  -> integration / batch correction
  -> cell-state validation
  -> target-card evidence

Evidence-only stream
  -> Open Targets / ChEMBL / DepMap / ClinicalTrials / PubMed
  -> standardized evidence table
  -> context match score
  -> target-card evidence

ML stream
  -> ML-ready feature table
  -> weak labels
  -> ranking / PU learning / uncertainty
  -> validation-priority recommendations
```

## Phase 1 - Evidence Browser MVP

Status: partially implemented.

Implemented:

- `build_target_cards.py`
- FastAPI target-card service
- Streamlit evidence browser
- HTML / Markdown / JSON report export

Next improvements:

- richer target detail memo
- automatic validation-assay suggestion
- better clinical warning display
- target-condition comparison plots

## Phase 2 - External Evidence Stream

Status: next priority.

Build:

- `external_evidence_table`
- source adapters for Open Targets, ChEMBL, DepMap, ClinicalTrials, PubMed/FDA labels
- `context_match_score`
- source/version/date/license tracking
- target-card overlay fields:
  - disease evidence
  - druggability
  - known drugs
  - safety warnings
  - clinical stage bucket

## Phase 3 - Cell-Level Integration Stream

Status: scaffold implemented.

Implemented:

- `src/9_cell_integration/cell_integration_pipeline.py`
- manifest-based h5ad / 10x ingestion
- metadata harmonization
- QC
- concatenation
- PCA / UMAP
- optional integration method: none / combat / harmony / scvi

Next improvements:

- Zarr/backed/chunked mode for large datasets
- external atlas label transfer
- CD4 module scoring per cell
- integration summary returned to target cards
- batch sensitivity report

## Phase 4 - Perturbation Validation

Build after raw cell data are available:

- guide assignment QC
- guide UMI / multi-guide / NTC diagnostics
- escaped or non-responder detection
- Mixscape / pertpy workflow
- SCEPTRE or pseudobulk validation for top targets
- responder fraction by target-condition

## Phase 5 - ML-Ready Feature Table

Build:

- `target_condition_features.csv`
- `weak_labels.csv`
- `benchmark_targets.csv`

Feature groups:

- perturbation strength
- KD evidence
- donor / guide robustness
- condition specificity
- pathway/module scores
- clinical axis
- external disease evidence
- druggability
- safety warnings
- context match score

Labels:

- `biology_positive_label`
- `clinical_precedent_label`
- `safety_warning_label`

## Phase 6 - ML Prioritization

Use label-scarce strategies:

- positive-unlabeled learning
- weakly supervised ranking
- signature similarity
- graph / embedding methods
- uncertainty scoring
- active learning for next validation experiment

Do not build a drug success/failure classifier as the first model.

## Immediate Next Step

Build Phase 2:

```text
external evidence schema + first adapter + target-card overlay
```

Recommended first adapter:

```text
Open Targets / ChEMBL-like local snapshot or API wrapper
```

Reason:

It adds immediate value to target cards without requiring large raw cell data.
