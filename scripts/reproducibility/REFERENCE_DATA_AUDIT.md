# REFERENCE_DATA_AUDIT.md

_Generated 2026-07-13T07:33:00+00:00 · GWT CD4 Perturb-seq portal · Phase 1 sub-agent (reference correctness + data internal consistency)_

Scope: every PMID/DOI in `frontend/webserver/src/components/ui/PageReferences.tsx` (26-entry catalog) and `frontend/webserver/public/provenance_registry.csv` (79 rows); plus internal consistency of `real-dataset.json` vs `disclosure.json`.

## Summary

- **References checked:** 27 unique cited works (25 PMIDs + DOI-only entries). **All resolve; all topic-match.** 0 wrong / 0 dead / 0 mismatched.
- **Data-consistency checks:** 8 run, **8 PASS, 0 FAIL.**
- **Fixes applied:** none required — no fabricated, wrong, or dead identifiers found; all counts reconcile.
- **Note:** `public/*` and deployed `dist/*` copies are byte-identical (MD5 match) for real-dataset.json, disclosure.json, provenance_registry.csv.

## 1. Reference resolution + claim match

Method: PMIDs resolved via NCBI E-utilities esummary (title/journal/year); DOIs resolved via doi.org/CrossRef. 'Match' = the resolved paper's title/topic corresponds to the label it is attached to.

| Source key / ref | PMID | DOI | Resolves | Resolved title (NCBI/CrossRef) | Topic match |
|---|---|---|---|---|---|
| gwt_primary | — | `10.64898/2025.12.23.696273` | YES | Genome-scale perturb-seq in primary human CD4+ T cells… (bioRxiv) | MATCH |
| open_targets/ochoa_ot(ref16) | 39657122 | `10.1093/nar/gkae1128` | YES | Open Targets Platform: facilitating therapeutic hypotheses building in | MATCH |
| gnomad/karczewski(ref17) | 32461654 | `10.1038/s41586-020-2308-7` | YES | The mutational constraint spectrum quantified from variation in 141,45 | MATCH |
| gtex/consortium(ref18) | 32913098 | `10.1126/science.aaz1776` | YES | The GTEx Consortium atlas of genetic regulatory effects across human t | MATCH |
| lincs/subramanian(ref19) | 29195078 | `10.1016/j.cell.2017.10.049` | YES | A Next Generation Connectivity Map: L1000 Platform and the First 1,000 | MATCH |
| reactome/gillespie(ref20) | 34788843 | `10.1093/nar/gkab1028` | YES | The reactome pathway knowledgebase 2022. | MATCH |
| string/szklarczyk(ref21) | 36370105 | `10.1093/nar/gkac1000` | YES | The STRING database in 2023: protein-protein association networks and  | MATCH |
| alphafold/jumper(ref22) | 34265844 | `10.1038/s41586-021-03819-2` | YES | Highly accurate protein structure prediction with AlphaFold. | MATCH |
| chembl/zdrazil(ref24) | 37933841 | `10.1093/nar/gkad1004` | YES | The ChEMBL Database in 2023: a drug discovery platform spanning multip | MATCH |
| cellxgene/cz(ref23) | 39607691 | `10.1093/nar/gkae1142` | YES | CZ CELLxGENE Discover: a single-cell data platform for scalable explor | MATCH |
| deseq2/love(ref09) | 25516281 | `10.1186/s13059-014-0550-8` | YES | Moderated estimation of fold change and dispersion for RNA-seq data wi | MATCH |
| benjamini_hochberg(ref10) | — | `10.1111/j.2517-6161.1995.tb02031.x` | YES | Controlling the False Discovery Rate… (J R Stat Soc B) | MATCH |
| jak_oral_surveillance(ref27) | 35081280 | `10.1056/NEJMoa2109927` | YES | Cardiovascular and Cancer Risk with Tofacitinib in Rheumatoid Arthriti | MATCH |
| teplizumab(ref28) | 31180194 | `10.1056/NEJMoa1902226` | YES | An Anti-CD3 Antibody, Teplizumab, in Relatives at Risk for Type 1 Diab | MATCH |
| dixit(ref02) | 27984732 | `10.1016/j.cell.2016.11.038` | YES | Perturb-Seq: Dissecting Molecular Circuits with Scalable Single-Cell R | MATCH |
| datlinger(ref03) | 28099430 | `10.1038/nmeth.4177` | YES | Pooled CRISPR screening with single-cell transcriptome readout. | MATCH |
| replogle2022(ref04) | 35688146 | `10.1016/j.cell.2022.05.013` | YES | Mapping information-rich genotype-phenotype landscapes with genome-sca | MATCH |
| shifrut(ref05) | 30449619 | `10.1016/j.cell.2018.10.024` | YES | Genome-wide CRISPR Screens in Primary Human T Cells Reveal Key Regulat | MATCH |
| schmidt(ref06) | 35113687 | `10.1126/science.abj4008` | YES | CRISPR activation and interference screens decode stimulation response | MATCH |
| freimer(ref07) | 36356142 | `10.1126/science.abn5647` | YES | Enhanced T cell effector activity by targeting the Mediator kinase mod | MATCH |
| weinstock(ref08) | 39395408 | `10.1016/j.xgen.2024.100671` | YES | Gene regulatory network inference from CRISPR perturbations in primary | MATCH |
| barry2021_sceptre(ref11) | 34930414 | `10.1186/s13059-021-02545-2` | YES | SCEPTRE improves calibration and sensitivity in single-cell CRISPR scr | MATCH |
| barry2024_sceptre(ref12) | 38760839 | `10.1186/s13059-024-03254-2` | YES | Robust differential expression testing for single-cell CRISPR screens  | MATCH |
| papalexi_mixscape(ref13) | 33649593 | `10.1038/s41588-021-00778-2` | YES | Characterizing the molecular regulation of inhibitory immune checkpoin | MATCH |
| replogle2020_guide(ref14) | 32231336 | `10.1038/s41587-020-0470-y` | YES | Combinatorial single-cell CRISPR screens by direct guide RNA capture a | MATCH |
| hart(ref15) | 26627737 | `10.1016/j.cell.2015.11.015` | YES | High-Resolution CRISPR Screens Reveal Fitness Genes and Genotype-Speci | MATCH |
| lambert(ref26) | 30290144 | `10.1016/j.cell.2018.01.029` | YES | The Human Transcription Factors. | MATCH |

Notes on individual entries:
- **gwt_primary / ref01** (`10.64898/2025.12.23.696273`): resolves to the bioRxiv preprint 'Genome-scale perturb-seq in primary human CD4+ T cells…' — correct primary dataset. `posted-content` type (preprint), as expected.
- **Lambert et al. 2018 / ref26** (`10.1016/j.cell.2018.01.029`): resolves via CrossRef to 'The Human Transcription Factors' (Cell, 2018) — **correct**. NCBI lists an alternate canonical DOI `10.1016/j.cell.2018.09.045` for the same article (a duplicate-DOI situation on the publisher side); the cited DOI is valid and resolves to the right paper, so **no change made**. Flagged as informational only.
- **jak_oral_surveillance / ref27** (PMID 35081280): NCBI title 'Cardiovascular and Cancer Risk with Tofacitinib in Rheumatoid Arthritis' — this IS the ORAL Surveillance trial (Ytterberg et al., NEJM 2022). Correct.
- **PageReferences.tsx vs provenance_registry.csv**: every PMID/DOI in the TSX catalog appears with the identical identifier in the CSV registry. No divergence.
## 2. Data internal-consistency checks

Files: `frontend/webserver/public/real-dataset.json`, `frontend/webserver/public/disclosure.json`.

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | targets count == 7249 (real-dataset len & disclosure coverage) | PASS | real-dataset=7249, disclosure.coverage.targets_in_portal=7249 |
| 2 | modules count == 20 (real-dataset modules & disclosure concept_layer.count) | PASS | modules=20, concept_layer.count=20 |
| 3 | readiness distribution 6628+319+302 == 7249 | PASS | watchlist=6628, validate=319, advance=302, sum=7249, total=7249; all calls={'watchlist': 6628, 'validate': 319, 'advance': 302} |
| 4 | field 'readiness' present & non-null on all 7249 targets | PASS | missing=0, null=0 |
| 5 | field 'effect' present & non-null on all 7249 targets | PASS | missing=0, null=0 |
| 6 | field 'diseases' present & non-null on all 7249 targets | PASS | missing=0, null=0 |
| 7 | field 'gnomad' present & non-null on all 7249 targets | PASS | missing=0, null=0 |
| 8 | field 'safetyLiabilities' present & non-null on all 7249 targets | PASS | missing=0, null=0 |

Additional blank-card / render-safety checks (all clean):
- Targets with blank `gene`: 0; blank `readiness.call`: 0; blank `effect`: 0.
- `diseases` is a list on all 7249 targets (7234 empty lists — valid, renders as 'no disease association', not a blank/undefined card).
- `safetyLiabilities` is a list on all 7249 targets (7248 empty lists — valid).
- `gnomad` is a dict on all 7249 targets (keys: loeuf, pli, constraintTier).
- `effect` is numeric on all targets.
- All 20 modules M01–M20 have non-blank id and name.

Cross-file note: the readiness distribution (6628/319/302) is stored only in `real-dataset.json`; `disclosure.json` does not restate those counts, so there is no cross-file numeric conflict to reconcile. The 7249 / 20 figures ARE stated in both files and agree.

## 3. Fixes applied

**None.** No wrong, mismatched, or dead identifiers were found, and all internal-consistency checks pass. No edits were made to any repo file. (Per the honesty rule: no values were changed or fabricated.)

## 4. Files examined
- `frontend/webserver/src/components/ui/PageReferences.tsx`
- `frontend/webserver/public/provenance_registry.csv` (79 rows; 28 `reference` rows ref01–ref28 + inline PMIDs in data_source/algorithm rows)
- `frontend/webserver/public/real-dataset.json` (7249 targets, 20 modules)
- `frontend/webserver/public/disclosure.json`
- deployed `dist/` copies (confirmed identical to `public/`)