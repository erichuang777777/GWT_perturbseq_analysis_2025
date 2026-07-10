# GB10 signed DE — application methods (v2, methods-review revised)

**Input:** validated genome-wide signed DE matrix (2,056,424 significant target x gene pairs, 100% consistent with the frozen pipeline). Schema: target_gene, culture_condition, downstream_gene, log_fc (signed log2FC), adj_p_value(<0.1), baseMean, zscore. ALL English.

**Revision note (v2):** Applies four methods-review must-fixes — (1) scale-free polarity ranking replacing the coverage-confounded signed_net axis; (2) footprint-descriptive class replacing the misleading activator/repressor badge; (3) detected-gene-background enrichment replacing whole-genome ORA; (4) softened Track-3 LINCS wording. Track-1/2/3 prose reconciled accordingly.

## Sign convention (used consistently across all three tracks)
Knockout/perturbation screen: log_fc = downstream gene change AFTER perturbing the target. Downstream DOWN-regulation (log_fc<0) after KO means the target normally PROMOTES those genes. signed_net = n_up - n_down over a target's significant downstream genes.

## Track 1 — Scale-free polarity ranking axis (Panel A) [REVISED — must-fix 1 & 2]

**Problem fixed (must-fix 1):** the previous PRIMARY rank was signed_net = n_up - n_down, whose magnitude scales with the total number of hits n. The old top-8 were therefore all high-coverage SAGA / transcription-machinery genes (TADA2B, SGF29, SUPT7L, TAF6L, TADA1, ...), an artifact of coverage rather than a directional signal.

**Fix — new PRIMARY statistic:**
- `directionality_index = (n_up - n_down) / (n_up + n_down)`, bounded [-1, +1]. Scale-free: it measures how one-sided the downstream footprint is, independent of total coverage. The 1,235-gene gate shortlist is re-ranked by |directionality_index| (rank 1 = most polarised).
- Two-sided binomial test (n_up vs n_down, H0: p = 0.5), BH-FDR across all 10,851 targets (`binom_p`, `binom_fdr`). Small-n targets are down-weighted honestly: a 90:10 split at n=100 is significant, at n=10 it is not.
- `signed_net` and `n_hits` are KEPT as SECONDARY visible columns (flagged as coverage-confounded), so the old axis remains inspectable.

**New primary top-5 (by |directionality_index|, shortlist):** FOXN2, MGA, SIK2, ZNF274, TMEM131L — these replace the SAGA-dominated signed_net top-8. Output: `signed_ranking_v2.csv` (adds directionality_index, binom_p, binom_fdr, primary_rank, footprint_class; keeps all original columns incl. signed_net, n_hits, signed_rank).

**Problem fixed (must-fix 2):** the activator/repressor badge was a NET-FOOTPRINT MAJORITY VOTE (sign of signed_net), NOT a molecular claim. It misleads for non-TF targets — e.g. CD3E is a TCR component, not a transcriptional repressor, yet KO releases more downstream genes than it loses, so it was mislabelled 'repressor'.

**Fix — footprint-descriptive class** (`footprint_class`):
- `net_derepressed_on_KO` — signed_net > 0 (KO up-regulates more downstream genes than it reduces)
- `net_reduced_on_KO` — signed_net < 0 (KO down-regulates more downstream genes than it raises)
- `balanced` — signed_net = 0

> CAVEAT (also in the CSV header and the Entry A board): footprint_class is the target's NET transcriptional FOOTPRINT direction in this KO screen — whether KO up- or down-regulates more downstream genes — NOT a molecular activator/repressor assignment. A TCR component such as CD3E is net_derepressed_on_KO without being a transcriptional repressor.

**Flagships under the corrected axis** (all net_derepressed_on_KO, but their honest primary rank is mid-shortlist, not top): CD3E (DI=+0.377, signed_net +2749, binom_FDR 8.0e-230, primary_rank 401); PLCG1 (DI=+0.313, signed_net +2274, binom_FDR 3.2e-157, primary_rank 520); VAV1 (DI=+0.233, signed_net +1987, binom_FDR 2.5e-101, primary_rank 698); BCL10 (DI=+0.145, signed_net +933, binom_FDR 6.4e-30, primary_rank 889); STAT3 (DI=+0.129, signed_net +500, binom_FDR 1.5e-14, primary_rank 925). The old prose ("five flagships all signed_net>0, CD3E +2,749 highest", implying activation) is withdrawn: signed_net>0 means net-derepressed footprint on KO, and by the scale-free polarity axis these flagships rank well below the most-polarised targets.

Entry A wiring (search / novelty / blind-spot / export) is intact; the board now defaults to the |directionality_index| primary axis with signed_net shown as a secondary diverging bar, and the badge is renamed to the footprint terms above.

## Track 2 — Downstream pathway enrichment (Panel B) [REVISED — must-fix 3]

**Problem fixed:** the previous ORA used the Reactome AnalysisService with a WHOLE-GENOME background, which biases toward highly-expressed housekeeping programmes (RNA metabolism, splicing, cell cycle) that are over-represented among detectable genes — falsely 'enriched'.

**Fix — detected-gene background:** recomputed for the 5 flagships (CD3E/PLCG1/VAV1/STAT3/BCL10), up/down downstream sets (split by mean signed log2FC across conditions), using an offline HYPERGEOMETRIC test with universe = the DETECTED-GENE BACKGROUND = all 10,273 downstream_gene symbols ever significant in the matrix, NOT the whole genome. Gene sets: Reactome pathways (ReactomePathways.gmt, current release), restricted to the detected background; pathways with >=5 background genes tested; overlap >=3 required; BH-FDR per flagship x direction. Output: `downstream_enrichment_v2.csv`.

**Survival of the biological headline claims under the corrected background:**
- VAV1 -> "Differentiation of T cells" SURVIVES — significant in the DOWN-after-KO set (FDR 6.9e-3; Th1 differentiation FDR 1.7e-2, Th2 FDR 3.7e-2), non-significant in the UP set (FDR 0.85). Direction is coherent: VAV1 normally promotes the T-cell differentiation programme, so KO reduces it.
- STAT3 -> "Signaling by Interleukins" SURVIVES — FDR 6.8e-9 (down) and 3.5e-2 (up); Interleukin-4/13 signaling FDR 3.9e-6 (down). The interleukin headline is robust to background correction.
- UP sets for CD3E/PLCG1/VAV1/BCL10 robustly enrich Immune System / Innate Immune System / Neutrophil degranulation / Interferon / Rho-GTPase signalling (TCR-downstream).

**Residual expression-artifact flag (honest):** the corrected background REDUCES but does NOT eliminate the highly-expressed-machinery bias. RNA-metabolism / splicing / rRNA / tRNA / translation pathways still dominate the DOWN-after-KO sets of all five flagships, and Cell Cycle / Mitotic pathways dominate STAT3-down. These rows are marked `expression_artifact_flag=True` in the output and should be read as residual detectability bias, not biology.

## Track 3 — LINCS directional concordance (Panel C) [REVISED — must-fix 4 + PMVK correction]

Signed downstream profile (strongest |log2FC| across conditions) vs LINCS demo signatures, restricted to the 978 landmark-gene overlap, for the 4 overlapping targets (SENP5/PLCG1/CCNC/PMVK). This is a demo-level directional sanity check, NOT external validation.

**Corrected per-target result:** 3/4 targets (SENP5 0.480, PLCG1 0.485, CCNC 0.494) show near-chance sign-agreement (~0.48-0.49) and non-significant Spearman ~0. PMVK shows a higher sign-agreement (0.608) and a weak but statistically significant positive concordance (Spearman rho = 0.219, p = 2.76e-5). The blanket "Spearman~0 (non-significant)" description is withdrawn — it was wrong for PMVK; the four targets are NOT all non-significant.

**Honest interpretation (softened per must-fix 4):** for the 3 near-chance targets, concordance is indistinguishable from chance. LINCS profiles are from non-T-cell immortalised cell lines, so a CD4+ T-cell context-specific signature need not match them. This near-chance result is CONSISTENT WITH context-specificity, but n=4 targets and the 978-landmark restriction preclude a strong conclusion — it is not, on its own, evidence for why context-specific (GB10) data is necessary.


## Appendix — CSV column notes (moved from CSV headers for machine-readability)

### signed_ranking_v2.csv
- signed_ranking_v2 — GB10 CD4+ T-cell KO Perturb-seq signed DE
- PRIMARY rank = |directionality_index| over the 1,235-gene gate shortlist (rank 1 = most polarised footprint).
- directionality_index = (n_up - n_down)/(n_up + n_down), bounded [-1,1]; scale-free, NOT confounded by total hit count.
- binom_p/binom_fdr = two-sided binomial test of n_up vs n_down (H0: p=0.5), BH-FDR across all 10,851 targets; down-weights small-n targets honestly.
- SECONDARY (coverage-confounded, kept visible): signed_net = n_up - n_down, n_hits = total significant downstream pairs. signed_rank = old coverage-driven rank.
- footprint_class: net_derepressed_on_KO (signed_net>0), net_reduced_on_KO (signed_net<0), balanced (signed_net=0).
- CAVEAT: footprint_class is the target's NET transcriptional FOOTPRINT direction in this KO screen (does KO up- or down-regulate more downstream genes),
- NOT a molecular activator/repressor assignment. A TCR component (e.g. CD3E) is net_derepressed_on_KO without being a transcriptional repressor.

### downstream_enrichment_v2.csv
- downstream_enrichment_v2 — corrected-background ORA for 5 flagships (CD3E/PLCG1/VAV1/STAT3/BCL10)
- METHOD: hypergeometric over-representation, universe = DETECTED-GENE BACKGROUND (all downstream_gene symbols ever significant in the matrix, N=10273),
- NOT whole-genome. Gene sets: Reactome pathways (ReactomePathways.gmt, current release), restricted to the detected background; pathways with >=5 bg genes tested.
- Query sets: downstream genes per flagship split by MEAN signed log2FC across Rest/Stim8hr/Stim48hr (up = mean>0, down = mean<0). Overlap>=3 required. BH-FDR per flagship x direction.
- expression_artifact_flag=True marks RNA-metabolism/splicing/rRNA/tRNA/translation/cell-cycle/mitotic pathways — residual highly-expressed-machinery bias that the detected background REDUCES but does not fully eliminate (dominant in the DOWN sets).
- KEY SURVIVAL CHECKS under corrected background: VAV1->'Differentiation of T cells' SURVIVES (down set FDR 6.9e-3; Th1 1.7e-2, Th2 3.7e-2; up set n.s. FDR 0.85). STAT3->'Signaling by Interleukins' SURVIVES (down FDR 6.8e-9, up FDR 3.5e-2; IL-4/13 down 3.9e-6). Immune System / Innate Immune System / Neutrophil degranulation / Interferon enrich robustly in UP sets.
