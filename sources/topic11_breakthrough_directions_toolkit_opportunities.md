# Topic 11 - Breakthrough Directions and Toolkit Opportunities

## Bottom line

The credible opportunity is a **research-use target-condition evidence toolkit**, not a drug discovery engine.

The strongest MVP is a transparent card system for `target x condition` hypotheses from GWT CD4 Perturb-seq summaries. Each card should expose perturbation effect, KD evidence, donor/guide robustness, off-target flags, druggability, safety, successful-drug benchmark axis, disease evidence, and next validation step.

## Recommended opportunity ranking

| Rank | Module | Value | Feasibility now | Notes |
|---:|---|---|---|---|
| 1 | Decision-grade target cards + readiness score | Turns scattered CSV summaries into shortlistable target dossiers | very high | Use Topic 4 schema |
| 2 | Transparent QC/confidence layer | Shows why a hit is trustworthy or risky | high | Use Topic 8/9 robustness and batch flags |
| 3 | Benchmark + calibration harness | Tests scoring against known T-cell/immune/drug biology | high | Use Topic 5 successful-drug axes |
| 4 | Open Targets-style translational overlay | Converts perturbation hits into tractability/safety/precedence language | high-medium | Use Open Targets/ChEMBL/DGIdb/DepMap later |
| 5 | Condition-specific hypothesis engine | Differentiates Rest, Stim8hr, Stim48hr therapeutic logic | high | Strongest scientific differentiator |
| 6 | Disease/trait translator | Links targets to autoimmune traits and patient states | medium | Needs GWAS/eQTL/disease atlas data |
| 7 | Mechanism graph builder | Summarizes target -> downstream genes -> pathway -> phenotype | medium | Needs signed DE vectors/pathway resources |
| 8 | Signature-to-compound matcher | Connects CD4 perturbation signatures to drug mimics/reversers | medium | LINCS/CMap/sci-Plex/Tahoe context mismatch risk |
| 9 | Wet-lab validation planner | Converts target cards into experiments | medium-high | Strong practical value for a translational audience |
| 10 | Combination/rescue design explorer | Higher-risk research module | medium-low | Do not make MVP promise |

Recommended build order:

```text
MVP: 1 + 2 + 3 + 4
Differentiator: add 5
Translational expansion: add 6 + 8
Research extension: add 7 + 9 + 10
```

## Feasible now with local CSVs

The local repo supports:

- 33,983 DE target-condition rows.
- 11,526 unique DE targets.
- 3 conditions: `Rest`, `Stim8hr`, `Stim48hr`.
- guide KD table.
- sgRNA metadata and off-target annotations.
- donor/guide robustness fields for a subset of targets.
- local druggable gene-class lists.
- prior EDA, readiness schema, and successful-drug benchmark tables.

Feasible modules:

- target-condition ranking
- QC badges and caveats
- condition-specific target interpretation
- local druggable-class overlay
- safety flags from core essentials / ClinVar / IUIS / immune-effector lists where available
- recovery of known biology as positive controls
- target cards with `validate`, `watchlist`, `deprioritize` labels

Using the strict local EDA filter gives roughly 1.1k high-confidence target-condition rows. Treat this as a candidate pool, not a finished target list.

## Credible MVP promise

Promise:

> A versioned, evidence-decomposed CD4 Perturb-seq target-prioritization toolkit that generates transparent target-condition hypotheses and validation plans.

Do not promise:

- drug discovery
- validated targets
- repurposed drugs
- clinical readiness
- patient stratification
- therapeutic efficacy/safety prediction
- virtual-cell prediction

## MVP target-card sections

Each card should contain:

1. Target and condition.
2. GWT perturbation evidence: DE breadth, effect size, on-target KD, cell count.
3. Robustness: donor correlation, guide correlation, off-target flag, batch caveat.
4. CD4 interpretation: activation, cytokine, Treg, Th1/Th2/Th17/Tfh, exhaustion, stress/proliferation if available.
5. Benchmark axis: CD3/TCR, CD28 costimulation, JAK/STAT, IL-2/IL-2R, NFAT/calcineurin, S1P, Th17/IL-23, TNF, integrin, checkpoint.
6. Druggability and modality: kinase, receptor, enzyme, surface protein, cytokine receptor, nuclear receptor, etc.
7. Safety flags: essentiality, broad chromatin/viability-like effect, cytokine release, Treg destabilization, global immunosuppression.
8. External evidence: Open Targets, genetics, ChEMBL, DepMap, disease atlas later.
9. Readiness call: `validate`, `watchlist`, `deprioritize`, with reason.
10. Next validation experiment.

## Validation metrics

Use explicit benchmarks:

- Recovery of TCR/proximal activation controls: `CD3E`, `LAT`, `PLCG1`, `ZAP70`, `LCP2`, `VAV1`, `CD247`, `ITK`.
- Recovery of known immune drug axes: CD3, CD28/CD80/CD86, IL-2/IL-2R, JAK/STAT, NFAT/calcineurin, IL-17/IL-23, TNF.
- Enrichment of known immune/T-cell regulators in top deciles.
- Rank stability after excluding off-target, low-cell, low-donor-robustness, and low-guide-robustness rows.
- Donor-holdout and guide-holdout concordance when data allow.
- Expert review agreement for top 50-100 cards.

## Main risks

- Scores may look more certain than evidence supports.
- CRISPRi knockdown does not equal pharmacologic inhibition, agonism, degradation, antibody blockade, or cell therapy.
- `Stim48hr` has run/batch caveat.
- Broad chromatin/essential-like hits may dominate high-DE rankings.
- External target annotations can be incomplete or disease-agnostic.
- LINCS/CMap/Tahoe drug signatures may not match primary CD4 biology.
- Without h5ad, no escaped-cell, responder-fraction, per-cell QC, or state-specific analysis.

## What needs more data

Needs `.h5ad` / `.h5mu`:

- per-cell QC
- guide assignment diagnostics
- doublet checks
- Mixscape/pertpy/SCEPTRE
- cell-state/subset effects
- responder fractions
- donor heterogeneity
- per-cell program scoring
- state-specific signature matching

Needs external data:

- Open Targets/Genetics
- GWAS/eQTL
- ChEMBL/DGIdb/DrugCentral/Pharos
- DepMap/Project Score
- GTEx/HPA/DICE/CELLxGENE
- LINCS/CMap/sci-Plex/Tahoe
- scPerturb/PerturBase/PerturbDB/TCPGdb
- disease scRNA atlases for RA, IBD, MS, psoriasis, SLE, cancer/TME

Needs wet lab:

- independent sgRNA / CRISPRi/a / siRNA validation
- protein-level target engagement
- primary donor replication
- cytokine, proliferation, apoptosis, activation marker assays
- Treg/Th17/Tfh functional assays
- tool compound or antibody perturbation where a modality exists

## Conservative roadmap

1. Freeze evidence schema using Topic 4 readiness checklist.
2. Build CSV-first target ranking using Topic 9 strict filters.
3. Add QC badges: off-target, low-cell, donor robustness, guide robustness, `Stim48hr` caveat.
4. Add successful-drug benchmark axes from Topic 5.
5. Add local druggability/essentiality overlays.
6. Generate top 50-100 target cards as Markdown/JSON/CSV.
7. Add Open Targets/ChEMBL/DepMap evidence snapshots.
8. Add signed CD4 program scoring and condition-specific hypothesis labels.
9. Add h5ad extension only after MVP: Mixscape/SCEPTRE/pertpy, responder/state analyses.
10. Validate 10-20 candidates experimentally before making target-readiness claims.

## Key grounding files

- `sources/topic04_drug_readiness_checklist.csv`
- `sources/topic05_successful_drug_benchmarks.csv`
- `sources/topic06_toolkit_architecture_summary.md`
- `sources/topic08_batch_effect_correction_summary.md`
- `sources/topic09_eda_report.md`
- `sources/topic10_related_information_broad_scan.md`

## Key external sources

- GWT CD4 Perturb-seq preprint: DOI `10.64898/2025.12.23.696273v1`
- CZI VCP dataset: https://virtualcellmodels.cziscience.com/dataset/genome-scale-tcell-perturb-seq
- Open Targets Platform: https://platform.opentargets.org
- scPerturb: PMID `38279009`, DOI `10.1038/s41592-023-02144-y`
- Perturbation prediction benchmark: PMID `40759747`, DOI `10.1038/s41592-025-02772-6`
- Generalizable perturbation benchmark: PMID `41381899`, DOI `10.1038/s41592-025-02980-0`
