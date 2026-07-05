# Topic 10 - Broad Related Information Scan

## Executive takeaways

The main external signal is clear: primary-human CD4 Perturb-seq is most valuable as an **experimental evidence anchor inside a larger target-evidence graph**, not as a standalone virtual-cell model.

For this project, the near-term opportunity is not to compete with large AI drug-discovery platforms. It is to turn the GWT CD4 perturbation summaries into transparent, condition-specific, drug-target hypothesis cards.

## Most useful implications

| External signal | Implication for this toolkit |
|---|---|
| Virtual cell / Tahoe / Arc / CZI VCP | Do not build MVP around large virtual-cell prediction. Use GWT as a high-quality CD4 perturbation evidence layer and future benchmark source. |
| Open Targets 2026 | Reuse product language: precedence, tractability, doability, safety, known drugs, baseline expression. Make GWT scores align with this style instead of creating an opaque total score. |
| ImmPort / ImmuneSpace | Useful human immunology validation layer: vaccine, infection, autoimmune, cytokine-response signatures can contextualize GWT target effects. |
| Treg / CAR-T / autoimmune cell therapy | Strong application story: Treg stability, immune tolerance, activation suppression, autoimmune reset. Keep it as hypothesis generation, not therapy claim. |
| FDA / regulatory guidance | Keep evidence provenance, context of use, versioning, and score decomposition. Short-term label should be research-use target prioritization. |
| Competitor landscape | Do not position as generic AI drug discovery. Differentiate on primary human CD4, genome-scale CRISPRi, condition-specific immune biology, and transparent evidence cards. |

## Near-term CSV-first takeaways

1. Build target-condition cards, not just gene cards. `Rest`, `Stim8hr`, and `Stim48hr` can imply different therapeutic hypotheses.
2. Use transparent scoring fields: perturbation effect, robustness, on-target KD, off-target flag, condition specificity, disease relevance, druggability, safety, known-drug precedent.
3. Keep simple linear/additive/null baselines. Recent benchmarks show deep perturbation predictors do not yet reliably outperform simple baselines.
4. Make therapeutic direction explicit: inhibit, activate, agonize, block, degrade, deplete, or reprogram.
5. Maintain separate modes for known-benchmark recovery and novel-opportunity discovery.

## Needs h5ad later

These should not block MVP, but require cell-level data:

- Mixscape/pertpy escaped-cell and non-responder checks.
- SCEPTRE or calibrated perturbation-gene association testing.
- Cell-state/subset-aware target effects.
- Responder fractions and donor heterogeneity.
- Full guide assignment diagnostics.
- Signature similarity at per-cell or state-specific resolution.
- Multimodal extensions such as RNA + protein + guide + clonotype.

## External APIs/resources to connect

| Resource | Use |
|---|---|
| Open Targets Platform/Genetics | disease evidence, genetics, known drugs, tractability, safety |
| ChEMBL / DGIdb / DrugCentral / Pharos | compounds, mechanisms, target annotations, clinical precedent |
| GWAS Catalog / eQTL Catalogue / Open Targets L2G | causal-gene and immune disease genetic support |
| DepMap / Project Score | common-essential and broad toxicity-like flags |
| scPerturb / PerturBase / PerturbDB / PerturbSeq.db / TCPGdb | external perturbation validation and benchmark pool |
| LINCS/CMap / sci-Plex / Tahoe-100M | drug-response signature matching and chemical perturbation reference |
| DICE / OneK1K / ImmPort / ImmuneSpace | immune expression, eQTL, vaccine/infection/autoimmune context |
| CELLxGENE Census | baseline cell-context expression |

## Long-term/virtual-cell perspective

Virtual-cell resources are expanding fast:

- Arc Virtual Cell Atlas / Tahoe-100M: large-scale drug-cell perturbation reference.
- CZI/Biohub Virtual Cells Platform: data/model/benchmark ecosystem.
- Geneformer, scGPT, scFoundation, GEARS and related models: useful optional comparators.

But current benchmarks argue against making these models the core of the first toolkit. They should be used as optional comparison layers after the evidence-card workflow is working.

## Competitive/novelty positioning

Adjacent players and resources:

- Recursion: phenomics and large-scale perturbation imaging.
- Cellarity: cell-state correction and chemistry-to-disease biology.
- insitro: ML over cellular and clinical data.
- Tahoe/Arc/CZI: virtual-cell data/model infrastructure.
- Myllia-like platforms: primary-cell CRISPR target discovery.

Differentiation for this project:

- primary human CD4 focus
- genome-scale CRISPRi perturbation evidence
- condition-specific immune state interpretation
- target-condition cards
- transparent QC badges
- drug-readiness and clinical-benchmark overlays

## Key references/resources

- GWT CD4 dataset/VCP: https://virtualcellmodels.cziscience.com/dataset/genome-scale-tcell-perturb-seq
- GWT preprint: DOI `10.64898/2025.12.23.696273v1`
- Arc Virtual Cell Atlas: https://arcinstitute.org/tools/virtualcellatlas
- Virtual Cell Challenge: PMID `40578317`
- Deep-learning perturbation benchmark: PMID `40759747`, DOI `10.1038/s41592-025-02772-6`
- Generalizable perturbation benchmark: PMID `41381899`, DOI `10.1038/s41592-025-02980-0`
- Geneformer: PMID `37258680`, DOI `10.1038/s41586-023-06139-9`
- scGPT: PMID `38409223`, DOI `10.1038/s41592-024-02201-0`
- scFoundation: PMID `38844628`, DOI `10.1038/s41592-024-02305-7`
- GEARS: PMID `37592036`, DOI `10.1038/s41587-023-01905-6`
- TCPGdb: PMID `41270225`, DOI `10.1158/2326-6066.CIR-25-0168`
- scPerturb: PMID `38279009`, DOI `10.1038/s41592-023-02144-y`
- Open Targets Platform: https://platform.opentargets.org
- Open Targets Platform 2025 update: PMID `39657122`, DOI `10.1093/nar/gkae1128`
- ChEMBL 2023: PMID `37933841`, DOI `10.1093/nar/gkad1004`
- ECCITE-seq: PMID `31011186`, DOI `10.1038/s41592-019-0392-0`
- Perturb-CITE-seq: PMID `33649592`, DOI `10.1038/s41588-021-00779-1`
- CAR-T autoimmune case series: PMID `38381673`, DOI `10.1056/NEJMoa2308917`
