# Tier1 Disease Expansion — 621 genes × 3 sources

**Purpose.** Expand disease associations for the 621 tier1 evidence genes (docs/tier1_evidence_genes.txt) by cross-querying three public sources, with immune/autoimmune diseases prioritized (Perturbase is a CD4+ T-cell platform).

## Sources & coverage
| Source | Method | Rows | Genes covered |
|---|---|---|---|
| Open Targets Platform | GraphQL target.associatedDiseases (top 25/gene by score) | 15,399 | 621/621 |
| ClinicalTrials.gov | search_trials by gene symbol (≤20 trials/gene) | 2,090 | 260/621 with ≥1 trial |
| NCBI MedGen | E-utilities esearch(gene) → elink→MedGen concept | 408 | 244/621 with disease |

## Immune prioritization
A gene×disease row is flagged `immune=True` when the Open Targets therapeutic_area matches immune/inflammatory/infectious, or the disease/condition name matches an immune-disease keyword set (arthritis, lupus, psoriasis, Crohn, colitis, MS, asthma, immunodeficiency, lymphoma/leukemia, transplant, T/B-cell, etc.).
- **2,060 immune-flagged association rows**
- **498 / 621 genes carry ≥1 immune-disease association**

## Files
- `disease_expansion_master.csv` — long table, one row per gene×disease×source (17,897 rows), with signed primary_rank/directionality_index/footprint_class joined, sorted immune-first then by rank.
- `disease_expansion_per_gene.csv` — per-gene rollup: n_ot_disease / n_ct_trial / n_ncbi_disease / n_immune_assoc / top_immune_diseases + signed rank.
- Source tables: ot_disease_associations.csv, ct_trial_associations.csv, ncbi_gene_disease.csv.

## Caveats (honest)
- ClinicalTrials free-text query: symbols that are also common English words/abbreviations (MAX, GLS, SMS, GNE, RPE, SARS2) show inflated match counts — not all are true gene-linked trials. Treat CT counts for such symbols as upper bounds.
- Open Targets association score ≠ causation; it aggregates genetic/literature/expression evidence.
- NCBI MedGen coverage is sparser (Mendelian-disease biased); absence ≠ no association.

## Deeper dive
The signed-rank top 50 genes additionally get full disease+drug+trial detail and AlphaFold structure + Protter topology assets (separate deliverable).
