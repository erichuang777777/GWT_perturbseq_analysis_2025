# Topic 3: Open Data Strategy for GWT CD4 Perturb-seq Drug-Discovery Workflows

Date: 2026-07-04

## Bottom Line

Use a CSV / signature-first strategy. Do not start by downloading and harmonizing every large h5ad.

The practical MVP is:

```text
GWT perturbation CSV
-> signature_table
-> gene_evidence_table
-> context_table
-> target cards / disease mapper / LINCS connector / safety filter / benchmark
```

Cell-level h5ad should be a second-phase enhancement for state-specific analysis, responder-cell detection, reference mapping, and perturbation modeling.

## Top Open Data Priorities

| Priority | Dataset / Resource | Size Burden | First Use | Role |
|---|---:|---|---|---|
| 1 | GWT Primary Human CD4+ T Cell Perturb-seq | large | metadata, DE, pseudobulk, subsets | main dataset |
| 2 | GSE119450 primary human T cell CROP-seq | small-medium | processed matrix | T cell validation |
| 3 | GSE92872 Jurkat TCR CROP-seq | small | expression CSV | TCR pathway smoke test |
| 4 | Open Problems PBMC drug perturbation | medium | benchmark files / signatures | immune drug-response benchmark |
| 5 | sci-Plex3 | medium-large | drug signatures or subsets | MoA and repurposing |
| 6 | scPerturb | medium | selected h5ad only | standardized perturbation benchmark |
| 7 | PerturBase | small | metadata / signatures | perturbation lookup |
| 8 | Perturb-CITE-seq melanoma/TIL | medium | processed RNA/protein | checkpoint and TME validation |
| 9 | IBD / RA / SLE / psoriasis atlases | small-large | disease-state signatures first | disease mapping |
| 10 | Replogle genome-scale Perturb-seq | large | pseudobulk/signature only | large perturbation benchmark |

Do not start by fully downloading GWT 22M cells, Replogle full genome-scale, full CELLxGENE atlases, raw sci-Plex3, or all of scPerturb. Use metadata/signatures first.

## Data Contract

### signature_table.csv

Stores perturbation, disease, drug, and validation signatures.

Core fields:

```text
signature_id, dataset_id, source_name, source_type, context_id,
species, perturbation_type, perturbation_name, target_gene_id,
target_gene_symbol, condition, control_condition, disease_id,
disease_name, drug_id, drug_name, cell_type, cell_subtype, tissue,
stimulus, timepoint, dose, gene_id, gene_symbol, logFC, effect_size,
p_value, fdr, direction, rank, n_cells, n_donors, platform, license,
source_url, created_at
```

### gene_evidence_table.csv

Stores gene-level evidence used for target cards and ranking.

Core fields:

```text
evidence_id, gene_id, gene_symbol, evidence_type, source_name,
source_dataset_id, context_id, disease_id, disease_name, cell_type,
cell_subtype, tissue, species, score, score_type, direction,
confidence, evidence_strength, p_value, fdr, rank, description,
license, source_url, last_updated
```

Evidence types:

```text
gwt_perturbation_effect, external_validation, disease_DE, GWAS, eQTL,
drug_target, druggability, pathway_membership, cell_type_marker,
tissue_expression, essentiality, toxicity, mouse_phenotype,
clinical_evidence, literature_evidence
```

### context_table.csv

Describes biological and technical context for every signature/evidence source.

Core fields:

```text
context_id, dataset_id, source_name, source_type, species,
organism_taxon_id, tissue, tissue_ontology_id, cell_type,
cell_type_ontology_id, cell_subtype, activation_state, disease_id,
disease_name, disease_status, stimulus, perturbation_context, platform,
assay, library_protocol, sample_type, donor_count, sample_count,
cell_count, batch_count, normalization_method, annotation_method,
metadata_completeness_score, context_quality_score, license, source_url,
notes
```

## Tool Mapping

Target Cards:
- Inputs: `gene_evidence_table`, `signature_table`, `context_table`
- Data: Open Targets, ChEMBL/DrugBank, GWAS Catalog, GTEx/HPA, DepMap, MSigDB/Reactome/GO, CELLxGENE, external Perturb-seq

Disease Module Mapper:
- Inputs: GWT perturbation signatures and disease signatures
- Data: IBD/RA/SLE/psoriasis/cancer TME atlases, GWAS/Open Targets, MSigDB/Reactome

LINCS Connector:
- Inputs: GWT target signatures, disease signatures, LINCS/CMap signatures
- Outputs: drug mimicry, drug reversal, MoA, known target mapping

Safety Filter:
- Data: DepMap, GTEx, HPA, MGI/IMPC, DrugBank/ChEMBL, Open Targets
- Flags: pan-essentiality, broad tissue expression, vital tissue expression, immune suppression risk, known toxicity, low therapeutic window

Benchmark:
- Tasks: recover known immune targets, recover disease-target associations, recover known drug reversals, recover expected pathways, reproduce external perturbation direction
- Metrics: AUROC, AUPRC, Recall@K, NDCG@K, top-K enrichment, Spearman correlation, reversal score

## Risks and Controls

| Risk | Control |
|---|---|
| Batch/platform mismatch | Compare rank/signature direction before raw count integration |
| Species mismatch | Ortholog mapping plus species penalty |
| Cell type mismatch | Require context table and context match score |
| Tissue mismatch | Add tissue match score |
| Stimulation mismatch | Make stimulus required or lower confidence |
| Metadata incompleteness | Metadata completeness score |
| License ambiguity | Add license field and commercial-use allowlist |
| Dataset size | Ingest summary signatures first |
| Gene symbol drift | Ensembl ID as primary key |
| Drug metadata ambiguity | Align to ChEMBL / DrugBank / PubChem |
| Evidence double counting | Source-aware evidence weighting |
| Public-data overfitting | Separate discovery evidence from holdout benchmarks |

## Four-Week Integration Roadmap

Week 1: schemas and contracts
- Define schema YAML for signature, gene evidence, and context tables.
- Build mock examples and schema validator.

Week 2: priority evidence sources
- Import Open Targets, ChEMBL/DrugBank-like target data, GWAS Catalog, GTEx/HPA, DepMap, MSigDB/Reactome/GO.
- Convert all into `gene_evidence_table`.

Week 3: signature engine
- Define GWT signature format.
- Add LINCS/CMap summary signatures.
- Add 1-2 autoimmune disease CD4 signatures.
- Implement cosine, Spearman, top up/down overlap, reversal score, and GSEA-style matching.

Week 4: target cards and benchmark
- Build target card generator.
- Build safety filter.
- Define target score: GWT effect, disease relevance, validation, druggability, safety penalty, context match.
- Run smoke-test benchmark on 10-20 known immune targets.

## Output Files

- `sources/topic03_open_data_inventory.csv`
- `sources/topic03_pubmed_open_data_round1.json`
- `sources/topic03_open_data_strategy_summary.md`

