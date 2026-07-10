# GB10 signed DE matrix — validation report

**Date:** 2026-07-10 · **Source:** Marson lab GWCD4i.DE_stats.h5ad (S3, 15.63 GB), extracted on GB10, pushed to repo. All English.

## What arrived
Genome-wide, per-target × per-gene SIGNED differential-expression long table — the gene-level resolution the original pipeline lacked (it stored only n_up/n_down counts). This is the real fix for the platform's signed-directionality gap (blindspot 3).

## Files (validated, checksummed)
| file | md5 | bytes |
|---|---|---|
| part-000.parquet | `655c49f86000fdbfdeed382f1f47b4de` | 53,752,667 |
| part-001.parquet | `fd917ce3109b88fc7046c9a9593bca8e` | 24,895,374 |
| gate_passing_signed_DE.csv.gz | `2dd7755d4dcfc869b1f9596ed3abf02b` | 49,600,847 |

## Schema
target_gene, target_ensembl_id, culture_condition, downstream_gene, downstream_ensembl_id, log_fc (signed log2FC), adj_p_value (<0.1), baseMean, zscore.

## Coverage (all confirmed against source README)
- 2,056,424 significant (adj_p<0.1) target×gene pairs — MATCH
- 10,851 targets with >=1 significant downstream (of 11,526; rest have no significant hit — honest, not missing) — MATCH
- 10,273 unique downstream genes — MATCH
- by condition: Stim8hr 786,755 / Stim48hr 670,322 / Rest 599,347 — MATCH
- adj_p max 0.0999 (<0.1 gate correctly applied); log_fc range -9.42..19.05 (genuinely signed)

## CRITICAL consistency check vs frozen pipeline
Rebuilt per-(target,condition) up/down/total counts from the signed matrix and compared to the FROZEN raw DE_stats (11c6348b, 33,983 rows):
- **28,757 matched target×conditions: n_up / n_down / n_total ALL 100% exactly equal (max abs diff 0).**
This proves the GB10 signed matrix is the gene-level expansion of the SAME experiment behind the already-third-party-verified pipeline — not a different run.

## Unlocks (now possible, were GB10-blocked)
- Phenotype-signed target ranking (up vs down programme direction), not just |effect|
- Per-target downstream gene identity for module/pathway analysis (modules 2/3 real compute)
- Directional concordance with LINCS reference signatures
