# REPRODUCIBILITY_REPORT — GWT CD4 Perturb-seq portal display numbers

Every DERIVED number shown on the portal, recomputed from in-repo raw data and
verdicted **REPRODUCED / MISMATCH / NOT-REPRODUCIBLE-IN-REPO**. Recompute engines:

- **Python** — `scripts/recompute_display_numbers.py` → `scripts/recomputed_numbers.json` (31 numbers).
- **R (independent cross-check)** — `scripts/recompute_crosscheck.R` → `scripts/recomputed_numbers_R.csv` (33 rows; re-derives the CSV/JSON-reproducible subset with a different toolchain: readr/dplyr/jsonlite).

**Summary: 31 numbers → 29 REPRODUCED · 0 MISMATCH · 2 NOT-REPRODUCIBLE-IN-REPO.**

R↔Python cross-check on the 13 shared keys: **13/13 AGREE, 0 divergence.**

| # | Displayed number | Shipped | Recomputed (Py) | R cross-check | Verdict | Source · how derived |
|---|---|---|---|---|---|---|
| 1 | coverage.de_rows_total | 33983 | 33983 | 33983 (AGREE) | ✅ REPRODUCED | `metadata/suppl_tables/DE_stats.suppl_table.csv` · row count of DE_stats.suppl_table.csv (one row per target×condition) |
| 2 | coverage.genome_total_targets | 11526 | 11526 | 11526 (AGREE) | ✅ REPRODUCED | `metadata/suppl_tables/DE_stats.suppl_table.csv` · unique target_contrast (Ensembl ID) count in DE_stats.suppl_table.csv |
| 3 | coverage.targets_in_portal | 7249 | 7249 | 7249 (AGREE) | ✅ REPRODUCED | `frontend/webserver/public/real-dataset.json` · unique gene count in real-dataset.json targets[] (grade>=2 UNION advance/watchlist selection over the full screen) |
| 4 | coverage.donors | 4 | 4 | — | ✅ REPRODUCED | `metadata/suppl_tables/sample_metadata.suppl_table.csv` · unique donor_id count in sample_metadata.suppl_table.csv |
| 5 | coverage.runs | 2 | 2 | — | ✅ REPRODUCED | `metadata/suppl_tables/sample_metadata.suppl_table.csv` · unique 10xrun_id count in sample_metadata.suppl_table.csv |
| 6 | coverage.gnomad_constraint_genes | 11267 | 11267 | 11267 (AGREE) | ✅ REPRODUCED | `metadata/suppl_tables/DE_stats.suppl_table.csv + sources/target_tool_cache/_overlays/gnomad_constraint_seed.csv` · count of DE target Ensembl IDs (DE_stats.target_contrast) present in gnomad_constraint_seed.csv ensembl_id |
| 7 | coverage.deep_external_evidence_genes | 21 | 21 | — | ✅ REPRODUCED | `sources/target_tool_cache/_evidence/*.json` · count of *.json files in the per-gene evidence cache directory (mirrors export_real_data.py's evidence_genes enumeration) |
| 8 | coverage.measured_downstream_genes | 10282 | — | — | ⚠️ NOT-REPRODUCIBLE-IN-REPO | `docs/mvp-research/TASK_A_GB10_HANDOFF.md (h5ad var; S3-only ~1.7TB)` · h5ad var (measured-gene) axis dimension. In-repo gate-passing signed-DE table contains 10271 unique significant downstream genes; the full-signed table has 10,273. The exact 10,282 is the S3-only GWCD4i.DE_stats.h5ad var dimension. — **reason:** var dimension of the S3-only single-cell h5ad; in-repo CSVs expose 10,271-10,273 unique downstream genes, not 10,282. |
| 9 | concept_layer.count (=modules) | 20 | 20 | 20 (AGREE) | ✅ REPRODUCED | `frontend/webserver/public/real-dataset.json` · length of real-dataset.json modules[] (M01-M20 concept layer) |
| 10 | real-dataset modules[] | 20 | 20 | 20 (AGREE) | ✅ REPRODUCED | `frontend/webserver/public/real-dataset.json` · length of real-dataset.json modules[] |
| 11 | real-dataset readiness=watchlist | 6628 | 6628 | 6628 (AGREE) | ✅ REPRODUCED | `frontend/webserver/public/real-dataset.json` · count of targets[] with readiness.call == 'watchlist' |
| 12 | real-dataset readiness=validate | 319 | 319 | 319 (AGREE) | ✅ REPRODUCED | `frontend/webserver/public/real-dataset.json` · count of targets[] with readiness.call == 'validate' |
| 13 | real-dataset readiness=advance | 302 | 302 | 302 (AGREE) | ✅ REPRODUCED | `frontend/webserver/public/real-dataset.json` · count of targets[] with readiness.call == 'advance' |
| 14 | risk-tier clear | 3309 | 3309 | 3309 (AGREE) | ✅ REPRODUCED | `frontend/webserver/public/real-dataset.json + src/lib/exprCompare.ts::deriveRiskTier` · client-side deriveRiskTier (exprCompare.ts) applied to real-dataset.json targets[]: f = #redFlags + #safetyLiabilities + (gnomad.constraintTier=='high'); f>=3 avoid / 2 high / 1 caution / 0 clear |
| 15 | risk-tier caution | 3197 | 3197 | 3197 (AGREE) | ✅ REPRODUCED | `frontend/webserver/public/real-dataset.json + src/lib/exprCompare.ts::deriveRiskTier` · client-side deriveRiskTier (exprCompare.ts) applied to real-dataset.json targets[]: f = #redFlags + #safetyLiabilities + (gnomad.constraintTier=='high'); f>=3 avoid / 2 high / 1 caution / 0 clear |
| 16 | risk-tier high | 696 | 696 | 696 (AGREE) | ✅ REPRODUCED | `frontend/webserver/public/real-dataset.json + src/lib/exprCompare.ts::deriveRiskTier` · client-side deriveRiskTier (exprCompare.ts) applied to real-dataset.json targets[]: f = #redFlags + #safetyLiabilities + (gnomad.constraintTier=='high'); f>=3 avoid / 2 high / 1 caution / 0 clear |
| 17 | risk-tier avoid | 47 | 47 | 47 (AGREE) | ✅ REPRODUCED | `frontend/webserver/public/real-dataset.json + src/lib/exprCompare.ts::deriveRiskTier` · client-side deriveRiskTier (exprCompare.ts) applied to real-dataset.json targets[]: f = #redFlags + #safetyLiabilities + (gnomad.constraintTier=='high'); f>=3 avoid / 2 high / 1 caution / 0 clear |
| 18 | validation.calibration.neg_control_grade1_pct | 99.96 | 99.96 | 99.96 (AGREE) | ✅ REPRODUCED | `sources/target_tool_cache/a792d68c-7adc-46a6-964a-35770e5adbde/target_cards.csv` · percent of kd_status=='not_measurable' target-card rows with statistical_evidence_grade==1 (n=4774) |
| 19 | validation.calibration.neg_control_advance_pct | 0.0 | 0.0 | — | ✅ REPRODUCED | `sources/target_tool_cache/a792d68c-7adc-46a6-964a-35770e5adbde/target_cards.csv + sources/target_tool_cache/_cache/readiness_full.parquet` · percent of kd_status=='not_measurable' rows with readiness_call=='advance' (n=4774) |
| 20 | validation.calibration.ranking_auroc | 0.85 | — | — | ⚠️ NOT-REPRODUCIBLE-IN-REPO | `docs/technical_methods.md §4 (documented value)` · ranking benchmark AUROC (13 canonical positives vs 1,211; Mann-Whitney). run_all_validation.py records it as 'documented (not recomputed here)'; no benchmark engine + labelled positive/negative input set ships in-repo. — **reason:** AUROC needs the labelled canonical-positive benchmark engine; only the documented value is in-repo, not a runnable recipe. |
| 21 | validation ladder L2 Spearman r | 0.943 | 0.943 | — | ✅ REPRODUCED | `sources/target_tool_cache/a792d68c-7adc-46a6-964a-35770e5adbde/target_cards.csv + src/3_DE_analysis/core/calibration.py::rank_stability` · core.calibration.rank_stability(target_cards).spearman_rank_correlation (naive n_total_de_genes ranking vs strict-filtered ranking) |
| 22 | validation ladder L2 top-50 overlap | 13 | 13 | — | ✅ REPRODUCED | `sources/target_tool_cache/a792d68c-7adc-46a6-964a-35770e5adbde/target_cards.csv + src/3_DE_analysis/core/calibration.py::rank_stability` · core.calibration.rank_stability(target_cards).top_n_overlap (naive top-50 vs strict top-50 intersection) |
| 23 | Open Targets symbol match | 55/55 | 55/55 | — | ✅ REPRODUCED | `docs/mvp-research/level4_external_validation/track_a_opentargets_revalidation.csv` · rows with a resolved Ensembl ID / total rows in track_a_opentargets_revalidation.csv |
| 24 | Open Targets named-disease GA exact | 26/26 | 26/26 | — | ✅ REPRODUCED | `docs/mvp-research/level4_external_validation/track_a_opentargets_revalidation.csv` · rows whose status == 'OK (exact disease-name GA match)' in track_a_opentargets_revalidation.csv |
| 25 | STRING@700 VAV1 | 86 | 86 | — | ✅ REPRODUCED | `docs/mvp-research/level4_external_validation/track_b_string_revalidation.csv` · string_n@700 for VAV1 in track_b_string_revalidation.csv (STRING v12 interaction_partners, required_score>=700) |
| 26 | STRING@700 CD3E | 65 | 65 | — | ✅ REPRODUCED | `docs/mvp-research/level4_external_validation/track_b_string_revalidation.csv` · string_n@700 for CD3E in track_b_string_revalidation.csv (STRING v12 interaction_partners, required_score>=700) |
| 27 | STRING@700 PLCG1 | 173 | 173 | — | ✅ REPRODUCED | `docs/mvp-research/level4_external_validation/track_b_string_revalidation.csv` · string_n@700 for PLCG1 in track_b_string_revalidation.csv (STRING v12 interaction_partners, required_score>=700) |
| 28 | STRING@700 BCL10 | 46 | 46 | — | ✅ REPRODUCED | `docs/mvp-research/level4_external_validation/track_b_string_revalidation.csv` · string_n@700 for BCL10 in track_b_string_revalidation.csv (STRING v12 interaction_partners, required_score>=700) |
| 29 | STRING@700 STAT3 | 324 | 324 | — | ✅ REPRODUCED | `docs/mvp-research/level4_external_validation/track_b_string_revalidation.csv` · string_n@700 for STAT3 in track_b_string_revalidation.csv (STRING v12 interaction_partners, required_score>=700) |
| 30 | STRING exact-match | 5/5 | 5/5 | — | ✅ REPRODUCED | `docs/mvp-research/level4_external_validation/track_b_string_revalidation.csv` · count of exact_match==True rows / total in track_b_string_revalidation.csv |
| 31 | GEO GSE318876 existence/description | present | present | — | ✅ REPRODUCED | `docs/mvp-research/level4_external_validation/track_c_gse318876_target_evidence.csv + docs/mvp-research/level4_external_validation/EXTERNAL_REVALIDATION.json` · GSE318876 target-evidence table exists (1235 rows) and EXTERNAL_REVALIDATION.json track_c verdict starts with REAL (accession + description). Live GEO fetch is network-gated; the in-repo cache is the reproducibility surface. |

## Notes on the two NOT-REPRODUCIBLE-IN-REPO numbers (honest, not forced)

1. **coverage.measured_downstream_genes = 10,282** — this is the `var` (measured-gene)
   axis dimension of the S3-only `GWCD4i.DE_stats.h5ad` (~1.7 TB single-cell layer,
   documented in `docs/mvp-research/TASK_A_GB10_HANDOFF.md`). The in-repo signed-DE
   long tables expose only the genes with ≥1 *significant* downstream hit: 10,271
   (gate-passing) / 10,273 (full-signed) unique downstream genes — close but not 10,282,
   because 10,282 counts all *measured* genes, not just significant ones. The h5ad
   itself is not in the checkout, so the exact value cannot be recomputed here.

2. **validation.calibration.ranking_auroc = 0.85** — the ranking benchmark AUROC
   (13 canonical positives vs 1,211 rest; Mann-Whitney p=8.8e-06). `src/3_DE_analysis/`
   `validation/run_all_validation.py` records it explicitly as *'documented (not
   recomputed here)'*: the repo ships the documented value, but not a runnable
   benchmark engine bound to the labelled canonical-positive/negative set, so it
   cannot be regenerated from raw data in-repo.

   The rest of the calibration block **is** reproducible and passes: negative-control
   grade-1 % (99.96, from `target_cards.csv` kd_status=='not_measurable'), advance %
   (0, via the readiness cache), and the L2 rank-stability Spearman r=0.943 + top-50
   overlap 13/50 (from the in-repo `core.calibration.rank_stability` engine on
   `target_cards.csv`).

## Risk-tier distribution

Recomputed by the exact `src/lib/exprCompare.ts` `deriveRiskTier` rule
(`f = #redFlags + #safetyLiabilities + (gnomad.constraintTier=='high'?1:0)`;
`f≥3 avoid / 2 high / 1 caution / 0 clear`) over `real-dataset.json` targets[]:
**clear 3309 · caution 3197 · high 696 · avoid 47** (Python and R identical). This is a
client-derived distribution (no shipped ground-truth constant); the verdict REPRODUCED
means the documented rule runs deterministically and both engines agree.

## External validation (all REPRODUCED from in-repo track CSVs)

- **Open Targets**: 55/55 symbols resolved + 26/26 named-disease GA exact-match
  (`track_a_opentargets_revalidation.csv`).
- **STRING @700 flagship partner counts**: VAV1 86 · CD3E 65 · PLCG1 173 · BCL10 46 ·
  STAT3 324, all exact (5/5) (`track_b_string_revalidation.csv`).
- **GEO GSE318876**: accession + description present in the in-repo evidence cache
  (`track_c_gse318876_target_evidence.csv` + `EXTERNAL_REVALIDATION.json`; live GEO
  fetch is network-gated, so the cache is the reproducibility surface).

## Freeze

Both scripts and both outputs are registered under the `scripts/`-owned unified-manifest
module **`P6_frontend_devops::freeze_validate_scripts`**. Adding the 4 files changes that
module's content-addressed `module_blob_sha256` from
`7421711e583b462dfd12e705c5c4f55631adf74269fbfc4dabc58a68852b639c` (4 files) to
`b46a2f3832786117d19107935353065e28948ac81a8bc08fe34f40157d84091f` (8 files). A
simulated `--freeze` confirms **no module the edit does not own drifts** because of it —
only `freeze_validate_scripts` moves (the other drifts in the tree predate this task and
belong to concurrent sub-agents). The pipeline-level md5 freeze (`freeze_pipeline.py`)
stays 24/24 OK — none of its pinned data assets were touched.
