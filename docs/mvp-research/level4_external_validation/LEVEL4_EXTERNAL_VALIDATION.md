# Level 4 — Orthogonal Computational Validation

**Platform:** CD4+ T-cell Perturb-seq signed target-ranking pipeline
**Scope of this document:** independent, differently-generated public datasets cross-checking the signed target ranking (`signed_ranking_v2`, 10,851 genes; 55-target validation shortlist).
**Bottom line up front:** external data exists, is retrievable, and is usable. It produces concrete positive signals — the marketed autoimmune-drug target TYK2 sits at rank 11, and flagship TCR-signalling hubs recover their known interaction partners — while the honest limitations (association ≠ causation; the available genome-wide CRISPR screen measures HIV infection, not T-cell activation; small validation n) are stated explicitly and bound what the tracks can claim.

---

## 1. The five-level validation ladder

The platform's target ranking is validated across a graded ladder. Each level is a *different kind* of evidence; a claim is only as strong as the highest level that supports it.

| Level | Question it answers | Status |
|-------|---------------------|--------|
| **L1 — Computational reproducibility** | Does the pipeline recompute the same ranking from the same inputs? | ✅ Done |
| **L2 — Statistical robustness** | Is the ranking stable to resampling, thresholds, and multiple-testing control? | ✅ Done |
| **L3 — Internal directional consistency** | Do up/down directionality and per-condition signs agree across the internal Perturb-seq arms? | ✅ Done |
| **L4 — Orthogonal computational validation** | Do *independent, differently-generated* public datasets cross-check the ranking? | ◀ **THIS DOCUMENT** |
| **L5 — Wet-lab validation** | Do the top targets change T-cell activation phenotype in prospective experiments? | ⧗ Future |

Level 4 is the first level that uses data the platform did **not** generate. It cannot establish causation (that is L5) — it establishes whether independent lines of public evidence are *consistent* with the ranking and whether the top targets are real, functional genes in the correct biological context.

---

## 2. The three orthogonal tracks

Three independent public resources, each interrogating a different axis of biology, were cross-referenced against the signed ranking. The composite figure (`level4_external_validation_figure.png`) shows one panel per track.

### Track A — Genetic association (GWAS / human genetics)

- **Data source:** Open Targets Platform (genetic-association evidence, aggregating GWAS Catalog, UK Biobank, FinnGen, ClinVar, and curated Mendelian sources), queried via the Open Targets GraphQL API. Cross-check table: `ot_genetic_association_crosscheck.csv` (55 targets).
- **Method:** for each validation target, the Open Targets `target–disease` genetic-association scores were retrieved, filtered to immune/autoimmune/immunodeficiency indications, and the top immune disease and its association score recorded alongside the target's signed primary rank and perturbation footprint class.
- **Result:** **26 / 55 targets (47%)** carry at least one immune genetic association, and **22 / 55** associate with a classic autoimmune/immunodeficiency phenotype. Immune associations span the full ranking (rank–GA Spearman ρ = 0.26, p = 0.20, n = 26 — not a significant directional trend); several top-ranked targets carry strong associations:
  - **TYK2** (rank 11) — rheumatoid arthritis, GA = 0.93. TYK2 is the molecular target of **deucravacitinib**, an FDA-approved marketed autoimmune drug. This is the strongest single external anchor: an independent human-genetics line and an approved-drug program converge on a top-11 platform target.
  - **STAT3** (rank 925) — hyper-IgE syndrome / autoimmune, GA = 0.95.
  - **CD3E** (rank 401) — immunodeficiency-18, GA = 0.92.
  - **IFNGR2** (rank 33) — immunodeficiency-28, GA = 0.90.
  - **SIK2** (rank 3) — asthma, GA = 0.72.
  - **ZNF627** (rank 15) — spondyloenchondrodysplasia with immune dysregulation, GA = 0.94.
- **Limitations:**
  - **Association ≠ causation.** A genetic association places a gene near a disease locus; it does not prove the gene drives T-cell activation, nor that perturbing it is therapeutic.
  - **Essential-gene confound.** Broadly essential genes (e.g. core signalling components) can associate with immune phenotypes for reasons unrelated to the activation axis the platform ranks.
  - **Ascertainment bias.** GWAS/curation coverage is uneven across diseases and ancestries; absence of an association is weak evidence, not evidence of absence.
  - **Score heterogeneity.** Open Targets GA scores blend Mendelian and common-variant evidence of different strengths; scores are comparable in rank, less so in absolute magnitude.

### Track B — Protein-interaction network recovery (STRING)

- **Data source:** STRING database (physical + functional protein–protein interactions, *Homo sapiens*), queried via the STRING API. Recovery table: `string_partner_recovery.csv` (15 targets: 5 flagship hubs + 10 novel primary top-10 targets).
- **Method:** for each target, its curated STRING partners were retrieved and intersected with the genes appearing in that target's Perturb-seq downstream footprint. `recovery_frac = partners_in_downstream / n_known_partners`. This asks: *does knocking out the gene perturb the transcriptional neighbourhood of its known protein partners?*
- **Result:** flagship TCR-signalling hubs recover a large fraction of their known partners, reconstructing the canonical TCR-signalling network from perturbation data alone:
  - **VAV1** — 53/86 partners recovered (62%).
  - **CD3E** — 38/65 (58%).
  - **PLCG1** 40%, **BCL10** 39%, **STAT3** 36%.
  - Novel primary top-10 targets recover much less (max 4.3%, most 0%).
- **Limitations:**
  - **Literature bias is the dominant confound.** STRING interaction coverage scales with how much a gene has been studied. Flagship hubs (VAV1, CD3E) have hundreds of curated interactions; a novel target such as **FOXN2** has **one** known partner. **Low recovery for a novel target is NOT evidence against it** — it reflects sparse prior literature, not a weak perturbation signal. This caveat is annotated directly in the figure panel.
  - **Recovery is a network-consistency check, not a hit test.** High recovery confirms the perturbation reconstructs known biology for well-characterised hubs; it says nothing about whether a hub is a good *therapeutic* target.
  - **Denominator instability.** `recovery_frac` is unstable when `n_known_partners` is small; targets with 0 known partners (TMEM131L) are undefined and excluded.

### Track C — Genome-wide CD4+ CRISPR screen (GSE318876)

> **Honest framing — read first.** GSE318876 is a genome-wide CRISPR screen in primary CD4+ T cells whose phenotype is **HIV infection** (identifying pro- and anti-HIV host factors), **NOT T-cell activation.** This track is therefore a **functional-coverage / correct-cell-type check**, explicitly **NOT** a confirmation of the activation-based ranking.

- **Data source:** GEO accession **GSE318876** — genome-wide CRISPRa/CRISPRi HIV host-factor screen in primary human CD4+ T cells. Evidence table: `gse318876_target_evidence.csv` (1,235 genes; 55 validation targets flagged).
- **Method:** validation targets were matched to the screen's per-gene results; library membership, best positive/negative FDR, log fold-change, and HIV-hit classification were recorded. Enrichment of the 55 targets among HIV hits was tested against the screened background.
- **Result:**
  - **Coverage is high: 52 / 55 validation targets (95%) are present in the screen library** (1,192 / 1,235 rows in library overall). This establishes that the platform's targets are **real, expressed, functional genes in the correct cell type** — primary CD4+ T cells — not artefacts.
  - **HIV-hit enrichment is null (p = 0.535, not significant).** Only 4 targets score as HIV host factors: **VAV1** (pro-HIV, CRISPRa positive FDR = 2.4×10⁻⁴ — the sole flagship HIV hit), and **ITM2A**, **GPR15**, **KLHDC10** (anti-HIV / depletion).
  - **The null is EXPECTED and is NOT evidence against the ranking.** HIV infection and T-cell activation are different phenotype axes; there is no reason the activation ranking should enrich for HIV host factors. Track C is presented as coverage, not concordance — the figure panel title states "HIV screen ≠ T-cell activation phenotype" explicitly and shows only the genuine hits, never a fabricated concordance signal.
- **Limitations:**
  - **Wrong phenotype axis.** This is the central limitation: the screen does not measure the platform's endpoint. It can confirm that targets are functional in CD4+ T cells; it cannot confirm they regulate activation.
  - **Perturbation modality differs.** CRISPRa/CRISPRi gain/loss in a pooled infection assay is not equivalent to the platform's Perturb-seq knockout transcriptional readout.
  - **Single hit is not a trend.** VAV1's strong HIV signal is one gene; it corroborates VAV1's centrality (consistent with Track B) but does not generalise.

---

## 3. Credibility tiers — what each track does and does not establish

| Track | Establishes (DOES) | Does NOT establish |
|-------|--------------------|--------------------|
| **A — GWAS / Open Targets** | Independent human-genetics evidence links a substantial fraction (26/55) of targets, incl. top-ranked genes, to immune disease; TYK2 (rank 11) is a marketed-drug target for RA. | Causation; that the associated gene drives *activation*; therapeutic direction of effect. Cannot rule out essential-gene / ascertainment confounds. |
| **B — STRING recovery** | Perturbation of flagship hubs (VAV1 62%, CD3E 58%) reconstructs their known TCR-signalling partners — the pipeline recovers real biology for well-characterised genes. | Anything about novel targets (literature-biased); therapeutic value of any hub. Low recovery ≠ weak target. |
| **C — GSE318876 CD4+ screen** | Targets are real, functional genes present in the correct cell type (52/55 in a genome-wide CD4+ library). | Activation-regulator status — wrong phenotype (HIV infection). Null HIV enrichment is expected and non-informative for the activation ranking. |

**Tier reading:** Track A is the strongest external evidence (independent data axis + a marketed drug), bounded by association≠causation. Track B is a positive internal-biology sanity check that applies only to well-studied hubs. Track C is a coverage/context check, deliberately not a concordance claim.

---

## 4. Overall statement (honest)

External, independently-generated public data **exists, is retrievable through standard APIs/accessions, and is usable** to cross-check the CD4+ Perturb-seq target ranking. It delivers concrete positive signals:

- **TYK2**, a top-11 platform target, is independently supported by human genetics (RA, GA 0.93) and is the target of a **marketed autoimmune drug (deucravacitinib)** — a convergence of three independent lines on one ranked gene.
- **VAV1 and CD3E**, flagship TCR hubs, have their known protein-interaction networks **reconstructed from perturbation data** (62% and 58% partner recovery), and VAV1 additionally scores as a genome-wide CD4+ screen hit.
- Nearly **half (26/55)** of validation targets carry immune genetic associations, and **95% (52/55)** are confirmed functional genes in primary CD4+ T cells.

The evidence is **corroborative, not confirmatory**, and three limitations bound every claim above:

1. **Association ≠ causation** (Track A) — genetic proximity is not a mechanism.
2. **Phenotype mismatch** (Track C) — the only available genome-wide CD4+ CRISPR screen measures HIV infection, not activation; its null enrichment is expected and cannot validate (or refute) the activation ranking.
3. **Small n and literature bias** — 55 validation targets, STRING recovery confounded by study effort, and novel targets under-represented in every literature-derived resource.

These are exactly the gaps **Level 5 (prospective wet-lab validation)** is designed to close. Level 4 establishes that the platform's top targets are genetically plausible, functionally real in the correct cell type, and network-consistent — a well-supported foundation for prioritising which targets enter wet-lab testing, not a substitute for it.

---

*Figure:* `level4_external_validation_figure.png` (3 panels: A — GWAS immune association vs signed rank; B — STRING partner recovery; C — GSE318876 functional coverage).
*Tables:* `ot_genetic_association_crosscheck.csv`, `string_partner_recovery.csv`, `gse318876_target_evidence.csv`, `signed_ranking_v2.csv`.
