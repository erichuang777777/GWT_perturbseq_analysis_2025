# Track D — Phenotype-matched external CRISPR-screen cross-check

Cross-check of `signed_ranking_v2.csv` against a user-supplied external **activation-phenotype** CRISPR screen hit table (e.g. Shifrut 2018 GSE119450 / Schmidt 2022 GSE190604 / Freimer 2022). This strengthens L4 by matching the phenotype axis (T-cell activation/proliferation), unlike Track C (GSE318876, HIV infection).

- Genes present in both tables (inner merge): **10313**

## (a) Rank-rank Spearman (primary_rank vs external effect_score)
- rho = **0.0554**, p = 0.05597, n = 1191
  - Note: primary_rank is 1=top; a ranking that agrees with the external screen is expected to show a **negative** rho (small rank paired with large effect magnitude).

## (b) Top-N enrichment AUROC (external hit, fdr < 0.10, vs inverted primary_rank)
- AUROC = **0.4746** (Mann-Whitney U identity), n_pos = 91, n_neg = 1100, Mann-Whitney p = 0.4203

## (c) Flagship-hub direction agreement (VAV1, CD3E, PLCG1, LCK, ZAP70)
- 1/5 (20.0%) flagship hubs agree in sign between `signed_net` and external `hit_direction`.
  - CD3E: our_sign=+1, external_hit_direction=-1, agree=False
  - PLCG1: our_sign=+1, external_hit_direction=-1, agree=False
  - VAV1: our_sign=+1, external_hit_direction=-1, agree=False
  - ZAP70: our_sign=+1, external_hit_direction=-1, agree=False
  - LCK: our_sign=+1, external_hit_direction=+1, agree=True

## Honest framing
**Corroborative, not confirmatory.** As with Tracks A-C in `LEVEL4_EXTERNAL_VALIDATION.md`, agreement here is consistent with, but does not prove, that the signed ranking captures causal drivers of T-cell activation. Any null or weak result above is reported as-is — it is **not** smoothed over, re-run with different thresholds, or omitted. See `perturbation_validation_plan.md` §5b (P1) for the acceptance criterion this track was designed against (AUROC >= 0.65 with permutation p < 0.05, plus flagship direction agreement).
