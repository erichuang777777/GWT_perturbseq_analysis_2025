# REPRODUCTION REPORT — Signed Tracks

**Generated:** 2026-07-11 06:00 UTC
**Script:** `reproduce_signed_tracks.py`
**Result element** of the reproducibility remediation (DEFINITION =
`DATA_DICTIONARY.md`, SCRIPT = `reproduce_signed_tracks.py`, RESULT = this file).

## What was run

`reproduce_signed_tracks.py` loads the raw signed matrix (2,056,424 hit rows,
10,851 targets) from the two parquet shards plus the documented external inputs
(LINCS demo signatures; Reactome snapshot), regenerates every
reproducible-offline column of the three signed files, and asserts each matches
the delivered artifact within tolerance. External-state and curated columns are
skipped-and-documented, never silently passed. The script exits non-zero if any
reproducible column mismatches.

**Exit status: 0 (PASS).**

## Column-level outcome

This table reconciles ALL 44 columns of the three signed files
(signed_ranking_v2 28 + downstream_enrichment_v2 10 + lincs_concordance 6 = 44).
Note: the script's SUMMARY prints `REPRODUCED=36`, which folds in the three
carried-through label columns (`flagship`, `direction`, `target`) and omits the
`target_gene` group key (used as the merge key, not separately asserted). The
table below classifies those consistently with `DATA_DICTIONARY.md`: label
columns are GIVEN, and `target_gene` (raw group key) is REPRODUCED.

| status | count | meaning |
|---|---|---|
| REPRODUCED | 34 | recomputes exactly / within tolerance from raw + documented inputs (incl. `target_gene` group key; excl. the 3 carried-through labels) |
| GIVEN | 4 | carried-through labels/text: `flagship`, `direction`, `target`, `caveat` |
| SNAPSHOT | 1 | `pathway_size_bg` — reproducible only vs the saved Reactome snapshot |
| CURATED | 1 | `expression_artifact_flag` — curated heuristic, kept & documented |
| EXTERNAL | 4 | `in_gate_shortlist`, `pathway_id`, `pathway_name`, `overlap` |

Total = 34 + 4 + 1 + 1 + 4 = **44** (all columns of the three signed files).
The script log's raw `REPRODUCED=36` = these 34 (minus `target_gene`, +3 labels).

**Numerical fidelity** (max deviations observed during verification):
- integer columns (`n_hits, n_up, n_down, signed_net`, per-condition counts): **exact (0)**
- `directionality_index`: max abs diff 1.1e-16
- `up_down_ratio`: max abs diff 1.8e-15
- `net_logfc`: max abs diff 4.4e-16
- `binom_p`: max rel diff 8.5e-13; `binom_fdr`: max abs diff 2.2e-16
- `footprint_class`, `directionality_class`, `primary_rank`: 100% label/rank match
- downstream `p_value`: max rel diff 9.3e-13; `fdr`: max abs diff 9.5e-15
- LINCS `n_shared_landmark`: exact; `sign_agreement_frac`/`spearman_rho`/`p_value`: <1e-16

## Columns FIXED in this remediation

1. **`signed_ranking_v2.footprint_class`** — the delivered values reproduce under
   a **SIGN** rule on DI (`DI>0/<0/==0`), NOT the `DI>0.1` threshold in the
   originally-captured (wrong) lineage script. Rule is now documented in
   `DATA_DICTIONARY.md` and asserted by the script (100% match).
2. **`signed_ranking_v2.directionality_class`** — the activator/repressor/mixed
   badge (`|DI|>=0.3`) was absent from any captured script. Rule recovered from
   data, documented, asserted (100% match), and given an explicit caveat that it
   is a **legacy up/down label, not a molecular activator/repressor call**, and
   that it partly opposes `footprint_class` naming.
3. **`signed_ranking_v2.signed_rank`** — definition clarified: a 1..N permutation
   ordering `signed_net` descending. The **ordering property** and the exact rank
   on distinct-`signed_net` rows reproduce and are asserted; the exact intra-tie
   integer is documented as **not recoverable** (build row order lost; up to
   1,004 rows share a `signed_net` value).
4. **Per-condition columns** (`_Rest/_Stim8hr/_Stim48hr`) and
   `target_ensembl_id`, `up_down_ratio` — were produced by an uncaptured script.
   Their derivation is now documented and each recomputes exactly from the raw
   matrix by `culture_condition`.
5. **In-file DEFINITION element** — the delivered CSVs shipped no column
   definitions. `DATA_DICTIONARY.md` now supplies name/definition/formula/units/
   reproducible-from/caveat for all 7 files.

## External-state columns (documented, not offline-reproducible)

- **`downstream_enrichment_v2`: `pathway_id`, `pathway_name`, `pathway_size_bg`,
  `overlap`** — Reactome gene-set membership was fetched LIVE at v2 build and
  not snapshotted. **Resolution:** a Reactome snapshot artifact
  (`reactome_pathway_snapshot.csv`, 1,807 pathways) was saved so that
  `pathway_size_bg`, the `overlap`-based arithmetic, and the flag are
  reproducible by lookup. `p_value`/`fdr` recompute exactly from these columns.
- **`downstream_enrichment_v2.expression_artifact_flag`** — resolved via **option
  (b)**: delivered values are KEPT and documented as a **curated per-pathway
  heuristic** (152 of 1,807 pathways True). A keyword rule reproduces only ~94.5%
  of unique pathways (audit 87.4% row-level), so the flag is marked
  **non-recomputable**; the exact keyword set is listed in `DATA_DICTIONARY.md`
  and the values are carried verbatim in the Reactome snapshot for lookup.
- **`signed_ranking_v2.in_gate_shortlist`** — upstream gate flag (1,235 targets),
  an INPUT to `primary_rank`; documented as external.
- **Level-4 tracks** — `track_a` OT scores, `track_b` STRING partners, and
  `track_c` GSE318876 MAGeCK results are external database state. `track_a`
  immune classification is a keyword heuristic (substring list documented).
  Document OT Platform / STRING versions & dates at time of use.

## Whole-project column tally (all 7 files, 87 columns)

Consistent with the External-state prose above (Level-4 `track_a`/`track_b`/
`track_c` DB-derived columns all counted as EXTERNAL):

| status | count |
|---|---|
| REPRODUCED | 57 |
| EXTERNAL | 23 |
| GIVEN | 5 |
| SNAPSHOT | 1 |
| CURATED | 1 |
| **total** | **87** |

Per-file EXTERNAL breakdown: signed_ranking_v2 1 (`in_gate_shortlist`);
downstream_enrichment_v2 3 (`pathway_id`, `pathway_name`, `overlap`) + 1 SNAPSHOT
+ 1 CURATED; track_a_gwas 10 (OT scores/heuristic); track_b_string 1
(`n_known_partners`); track_c_gse318876 8 (GSE318876 MAGeCK-derived:
`in_library, best_neg_fdr, best_pos_fdr, best_lfc, screen, best_dir,
hiv_hit_class, moves_in_uninfected`). GIVEN = `flagship, direction, target,
caveat` + track_c `target`.

## Full script log

```
Loading raw signed matrix ...
  2,056,424 hit rows, 10,851 targets

[REPRODUCED] signed_ranking_v2.csv        n_hits                                   exact integer match
[REPRODUCED] signed_ranking_v2.csv        n_up                                     exact integer match
[REPRODUCED] signed_ranking_v2.csv        n_down                                   exact integer match
[REPRODUCED] signed_ranking_v2.csv        signed_net                               exact integer match
[REPRODUCED] signed_ranking_v2.csv        signed_rank                              orders signed_net DESC + exact on distinct-signed_net rows (intra-tie order not recoverable)
[REPRODUCED] signed_ranking_v2.csv        target_ensembl_id                        exact string match
[REPRODUCED] signed_ranking_v2.csv        directionality_index                     numeric match (rtol=1e-09)
[REPRODUCED] signed_ranking_v2.csv        up_down_ratio                            numeric match (rtol=1e-09)
[REPRODUCED] signed_ranking_v2.csv        net_logfc                                numeric match (rtol=1e-09)
[REPRODUCED] signed_ranking_v2.csv        binom_p                                  numeric match (rtol=1e-09)
[REPRODUCED] signed_ranking_v2.csv        binom_fdr                                numeric match (rtol=1e-09)
[REPRODUCED] signed_ranking_v2.csv        footprint_class                          exact label match (documented rule)
[REPRODUCED] signed_ranking_v2.csv        directionality_class                     exact label match (documented rule)
[REPRODUCED] signed_ranking_v2.csv        primary_rank                             |DI| desc within in_gate_shortlist; NaN outside (uses gate as input)
[REPRODUCED] signed_ranking_v2.csv        n_up_Rest                                per-condition recompute
[REPRODUCED] signed_ranking_v2.csv        n_down_Rest                              per-condition recompute
[REPRODUCED] signed_ranking_v2.csv        signed_net_Rest                          per-condition recompute
[REPRODUCED] signed_ranking_v2.csv        net_logfc_Rest                           per-condition recompute
[REPRODUCED] signed_ranking_v2.csv        n_up_Stim8hr                             per-condition recompute
[REPRODUCED] signed_ranking_v2.csv        n_down_Stim8hr                           per-condition recompute
[REPRODUCED] signed_ranking_v2.csv        signed_net_Stim8hr                       per-condition recompute
[REPRODUCED] signed_ranking_v2.csv        net_logfc_Stim8hr                        per-condition recompute
[REPRODUCED] signed_ranking_v2.csv        n_up_Stim48hr                            per-condition recompute
[REPRODUCED] signed_ranking_v2.csv        n_down_Stim48hr                          per-condition recompute
[REPRODUCED] signed_ranking_v2.csv        signed_net_Stim48hr                      per-condition recompute
[REPRODUCED] signed_ranking_v2.csv        net_logfc_Stim48hr                       per-condition recompute
[EXTERNAL  ] signed_ranking_v2.csv        in_gate_shortlist                        upstream gate flag (1235 targets); INPUT, not recomputed

[REPRODUCED] downstream_enrichment_v2.csv p_value                                  hypergeom.sf(overlap-1, N=10273, size_bg, query_size)
[REPRODUCED] downstream_enrichment_v2.csv fdr                                      BH within flagship/direction
[REPRODUCED] downstream_enrichment_v2.csv flagship                                 label; one of ['BCL10', 'CD3E', 'PLCG1', 'STAT3', 'VAV1']
[REPRODUCED] downstream_enrichment_v2.csv direction                                label; up/down downstream gene set
[REPRODUCED] downstream_enrichment_v2.csv query_size                               # up/down downstream genes (mean log_fc across conditions) within detected background
[SNAPSHOT  ] downstream_enrichment_v2.csv pathway_size_bg                          Reactome external state; verified vs saved snapshot
[CURATED   ] downstream_enrichment_v2.csv expression_artifact_flag                 curated per-pathway heuristic; verified vs snapshot (NOT recomputable)
[EXTERNAL  ] downstream_enrichment_v2.csv pathway_id                               Reactome pathway identifier (live fetch)
[EXTERNAL  ] downstream_enrichment_v2.csv pathway_name                             Reactome pathway name (live fetch)
[EXTERNAL  ] downstream_enrichment_v2.csv overlap                                  query x Reactome-membership intersection (live fetch)

[REPRODUCED] lincs_concordance.csv        n_shared_landmark                        exact
[REPRODUCED] lincs_concordance.csv        sign_agreement_frac                      strongest |log_fc| profile vs LINCS landmarks
[REPRODUCED] lincs_concordance.csv        spearman_rho                             strongest |log_fc| profile vs LINCS landmarks
[REPRODUCED] lincs_concordance.csv        p_value                                  strongest |log_fc| profile vs LINCS landmarks
[REPRODUCED] lincs_concordance.csv        target                                   one of ['SENP5', 'PLCG1', 'CCNC', 'PMVK']
[GIVEN     ] lincs_concordance.csv        caveat                                   free-text DEMO-level disclaimer (not computed)

==============================================================================
SUMMARY: {'REPRODUCED': 36, 'EXTERNAL': 4, 'SNAPSHOT': 1, 'CURATED': 1, 'GIVEN': 1}

All reproducible columns matched the delivered files within tolerance.
External-state / curated / given columns were skipped-and-documented (see above).
```
