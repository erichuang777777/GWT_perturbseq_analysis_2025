# Methodological validation of the target ranking (GB10-free)

Three validations addressing reviewer-level concerns raised in expert (bioinformatics) review.
All computed from the existing DE_stats + gnomAD constraint; NONE require the per-gene signed
DE matrix (GB10 / Task A).

---

## Validation 1 — Ranking benchmark against an INDEPENDENT ground truth
**Concern:** does the ranking actually surface known CD4 T-cell regulators, or could it be random?

**Method.** Ground truth = a hardcoded canonical set, deliberately INDEPENDENT of the platform's
concept-module annotation (using the seed modules would be circular):
- Positives (should rank high): TCR proximal signalling (CD3E, CD3D/G, CD247, LAT, ZAP70, LCK,
  PLCG1, VAV1, ITK, LCP2, FYN), Th-lineage TFs (TBX21, GATA3, STAT6, STAT4, RORC, FOXP3, BCL6,
  STAT3), costim/cytokine (CD28, ICOS, IL2RA, CTLA4, IL2RB, JAK3, STAT5B).
- Negatives (should rank low): housekeeping (ACTB, GAPDH, TUBB, B2M, RPL13A, PPIA, HPRT1, YWHAZ,
  SDHA, TBP, GUSB).
Ranked all 1,235 gated targets by ctx_specific_de (the default immune-interest metric); computed
ROC, precision-recall, Mann-Whitney U, and top-50 hypergeometric enrichment.

**Scope of 'independent'.** The ranking SCORE (ctx_specific_de = max|de_Stim−de_Rest|) takes no input
from the concept modules or the seed-module file — there is no score→label circularity, which is the
circularity that would fake a good AUROC. Note however that 12/27 canonical positives also appear in
the platform's concept modules: independence is from the SCORE, not from a shared canonical-immunology
prior. 'Independent' should be read as 'the metric did not see the labels', not 'the labels and the
platform share no biology'.

**Result — VALIDATED** (with the single-dataset caveat below — 'VALIDATED' should not be cited without it).
- AUROC = 0.85 (positives vs the 1,211 unlabelled 'rest' genes — the operative negative class); average
  precision 0.47 (~45× the 0.011 random prevalence). IMPORTANT: only 1 of 11 curated housekeeping
  negatives (HPRT1) survived the n≥200 gate (10 were pre-filtered), so the ROC rests on 'positives vs
  rest', NOT on a balanced curated negative set. We do NOT quote the pos-vs-1-negative figure (0.92) as
  a headline — it is inflated by the single surviving negative.
- Positives median rank 36 vs housekeeping 964. Mann-Whitney one-sided p = 8.8e-6 (rank-biserial r = 0.69).
- Top-50 hypergeometric p = 1.8e-7 (7/50 positives, 0.53 expected).
- 5/5 top-ranked and 6/8 of the top-8 are canonical positives (CD3E, LAT, PLCG1, VAV1, CD247, ITK).
- Honest note: 10/11 housekeeping negatives and 14/27 positives were already filtered upstream of the
  1,235 — the near-total housekeeping exclusion is itself consistent with the gate down-weighting
  non-specific genes. Weakest positive BCL6 (rank 1082) is a germinal-center/Tfh TF, biologically
  plausible to be low in this CD4 assay.

## Validation 2 — Essential-gene / dropout survivorship-bias diagnosis
**Concern:** Perturb-seq depletes cells when essential genes are knocked down → low cell counts →
filtered by the n_cells≥200 gate. The platform may be systematically blind to the most important genes.

**Method.** Reference cell count = median n_cells_target across all 33,983 observations (=539; no
explicit non-targeting control was labelled). Cell-gate failure = max n_cells < 200 (1,036/11,526
targets). Constraint (LOEUF/pLI) for the filtered genes was pulled from an EXTERNAL, filter-independent
source (gnomAD v2.1.1 loss-of-function metrics by gene, file `gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz`
from the public GCS bucket `gcp-public-data--gnomad`; the exact LOEUF/pLI values used are persisted
in `dropout_diagnosis.csv` itself, so the diagnosis is reproducible from the saved artifacts) — critically, the master table is the POST-gate survivor table (min cell count
= 200), so it could not supply constraint for filtered genes. High-constraint = LOEUF<0.35 OR pLI≥0.9.

**Result.** 237 gate-failed genes are high-constraint → 'likely_essential_dropout' — the genes the
platform is blind to. 799 are gate-failed but low-constraint ('low_cells_other' = evidence-insufficient,
not too-important). 75 have unknown constraint (reported unknown, never 0). The dropout zone is
enriched for canonical essential genes: PRKDC, KMT2A, EIF4G1, INO80, TOPBP1, ARID1A, USP7, HCFC1,
TAF4, MED13L. This is a SUSPECTED-dropout heuristic, not a measured essentiality screen.

## Validation 3 — Baseline-expression correction of context-specificity
**Concern:** "silent at Rest, active on Stim" could be a true activation-specific regulator OR an
artifact — a gene barely expressed at Rest, so knockdown trivially has no Rest effect.

**Method.** For each of the 96 context-specific candidates, took Rest target_baseMean. Floor = 8.33
(Q25 of all target_baseMean, n=28,133 non-null). true_regulator = Rest baseMean ≥ floor (expressed,
so low Rest DE is genuine); expression_artifact = Rest baseMean < floor (confounded, DEMOTE);
unknown = missing (not filled 0).

**Result.** 84 true regulators / 11 expression artifacts / 1 unknown. The 11 to demote: ANKRD61,
EGR2, FITM2, IBA57, IFNGR2, IL23R, NATD1, PTCD2, RNFT2, UBE2E2, ZNF837. All 5 flagship genes are
CONFIRMED true regulators (CD3E baseMean 357, PLCG1 223, VAV1 74, STAT3 62, BCL10 45 — all above floor).

---

## What this does and does not establish
- **Does:** the ranking is non-random and recovers known biology (V1); the platform's blind spot is
  named and quantified (V2); the 96-candidate shortlist is cleaned of 11 expression artifacts (V3).
- **Does not:** replace an external replication cohort (still single-dataset), nor provide phenotype-
  signed direction (needs GB10). Polarity remains an aggregate proxy.

## Files
- benchmark_results.csv, dropout_diagnosis.csv, context_specific_corrected.csv
- methodological_validation.png (3-panel: ROC · dropout survivorship · expression correction)
