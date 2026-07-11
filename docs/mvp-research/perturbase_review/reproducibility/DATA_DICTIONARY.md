# DATA DICTIONARY — Gene-Target Ranking & Validation Tracks

This dictionary is the in-repository DEFINITION element for the signed-track and
Level-4 deliverables. It gives, for every column of every file: **name,
definition, formula/derivation, units, reproducible-from (raw input), and any
caveat.** Values were confirmed by two audits (signed-tracks audit
`8e6060ce`, level4-tracks audit `d327722d`) and re-verified by
`reproduce_signed_tracks.py`.

## Shared raw input (the "raw signed matrix")

Two parquet shards, concatenated, are the primary raw input for the signed
files:
- `ca1ccabf-a849-4eac-9225-be930d12a3a8` (part-000, 1,400,000 rows)
- `3df56bd0-dcae-437c-8137-68c8e0308a40` (part-001, 656,424 rows)
- Combined: **2,056,424 hit rows over 10,851 target genes.**

Each row is one **hit**: a (target_gene x downstream_gene x culture_condition)
differential-expression result from a perturbation screen (target KO / CRISPR
perturbation). Columns: `target_gene, target_ensembl_id, culture_condition,
downstream_gene, downstream_ensembl_id, log_fc, adj_p_value, baseMean, zscore`.
Conventions used throughout:
- **hit** = one row of the raw matrix.
- **up** = `log_fc > 0`; **down** = `log_fc <= 0` (no raw row has `log_fc == 0`).
- `culture_condition` in {`Rest`, `Stim8hr`, `Stim48hr`}.

---

## 1. signed_ranking_v2.csv  (10,851 rows x 28 cols)

**Definition:** one row per target gene; signed directionality statistics of
each target's downstream footprint, plus per-condition breakdowns and ranking
badges. **Reproducible-from:** the raw signed matrix (above), except
`in_gate_shortlist` (external gate input).

| column | definition | formula / derivation | units | reproducible-from | caveat |
|---|---|---|---|---|---|
| `target_gene` | HGNC symbol of the perturbed gene | group key | symbol | raw | — |
| `target_ensembl_id` | Ensembl gene ID of the target | first value per group | ENSG | raw | — |
| `n_hits` | number of downstream DE hits for the target (all conditions) | `count(rows)` per target | count | raw | — |
| `n_up` | up-regulated downstream hits | `count(log_fc > 0)` | count | raw | — |
| `n_down` | down-regulated downstream hits | `n_hits - n_up` | count | raw | — |
| `signed_net` | net up-vs-down count | `n_up - n_down` | count | raw | — |
| `directionality_index` | normalized net direction (DI) | `(n_up - n_down)/(n_up + n_down)` | ratio in [-1,1] | raw | — |
| `up_down_ratio` | up-to-down ratio (pseudocount) | `n_up/(n_down + 1)` | ratio | raw | +1 pseudocount avoids div-by-zero |
| `net_logfc` | mean signed effect size | `mean(log_fc)` over all hits | log2 fold-change | raw | — |
| `binom_p` | two-sided binomial test that up:down = 50:50 | `scipy.stats.binomtest(n_up, n_hits, 0.5)` two-sided | p-value | raw | — |
| `binom_fdr` | BH-adjusted `binom_p` | `false_discovery_control(binom_p, method='bh')` over ALL 10,851 rows | q-value | raw | — |
| `footprint_class` | **SIGN**-based footprint label | `DI>0 -> net_derepressed_on_KO`; `DI<0 -> net_reduced_on_KO`; `DI==0 -> balanced` | category | raw | Uses the SIGN of DI (not a magnitude threshold). |
| `directionality_class` | **LEGACY** up/down magnitude badge | `DI>=0.3 -> repressor`; `DI<=-0.3 -> activator`; else `mixed` | category | raw | **CAVEAT: legacy up/down label, NOT a molecular activator/repressor call.** It is derived purely from the up/down count balance and partly OPPOSES `footprint_class` naming (a high-DI target is `net_derepressed_on_KO` in `footprint_class` but labelled `repressor` here). Interpret as "direction-of-imbalance badge", not mechanism. |
| `in_gate_shortlist` | boolean: target passed the upstream shortlist gate | — | bool (1,235 True) | **EXTERNAL** | **CAVEAT: upstream gate flag, an INPUT.** Not derivable from the raw matrix alone; consumed by `primary_rank` and equals the 1,235-target shortlist that feeds Track C. |
| `primary_rank` | rank within the shortlist by |DI| | `abs(DI)` descending rank (`method='first'`) computed ONLY over `in_gate_shortlist==True` rows; `NaN` otherwise | rank (1..1235) | raw + `in_gate_shortlist` | NaN for non-shortlist targets. |
| `signed_rank` | rank by `signed_net` descending | 1..N permutation ordering `signed_net` descending; ties broken by original build row order | rank (1..10851) | raw (ordering only) | **CAVEAT: exact intra-tie integer is not recoverable** from raw (build row order lost). The ordering property + exact rank on distinct-`signed_net` rows reproduce; ties (up to 1,004 rows share a value) do not. |
| `n_up_Rest`, `n_up_Stim8hr`, `n_up_Stim48hr` | up hits within each condition | `count(log_fc>0)` per target within `culture_condition` | count | raw | — |
| `n_down_Rest`, `n_down_Stim8hr`, `n_down_Stim48hr` | down hits within each condition | `n_hits_cond - n_up_cond` | count | raw | — |
| `signed_net_Rest`, `signed_net_Stim8hr`, `signed_net_Stim48hr` | net up-vs-down within condition | `n_up_cond - n_down_cond` | count | raw | — |
| `net_logfc_Rest`, `net_logfc_Stim8hr`, `net_logfc_Stim48hr` | mean signed effect within condition | `mean(log_fc)` within `culture_condition` | log2 FC | raw | — |

---

## 2. downstream_enrichment_v2.csv  (12,975 rows x 10 cols)

**Definition:** Reactome pathway over-representation of the up/down downstream
gene sets of the 5 flagship targets (`BCL10, CD3E, PLCG1, STAT3, VAV1`).
**Reproducible-from:** the raw matrix (for `query_size`) plus the file's own
Reactome-derived columns (for `p_value`/`fdr`). Pathway membership is EXTERNAL
state — see caveats and the Reactome snapshot artifact.

| column | definition | formula / derivation | units | reproducible-from | caveat |
|---|---|---|---|---|---|
| `flagship` | flagship target whose downstream set is tested | label | symbol | given | one of the 5 flagships |
| `direction` | which downstream set (`up`/`down`) | label | category | given | direction of the query gene set |
| `query_size` | # up (or down) downstream genes for the flagship, within detected background | count of downstream genes with mean(log_fc across conditions) >0 (up) / <=0 (down), restricted to the detected background | count | raw | — |
| `pathway_id` | Reactome pathway stable ID | live Reactome fetch | R-HSA-* | **EXTERNAL** | live-fetched at v2 build; see snapshot |
| `pathway_name` | Reactome pathway name | live Reactome fetch | text | **EXTERNAL** | live-fetched at v2 build; see snapshot |
| `pathway_size_bg` | # pathway genes present in the detected background | live Reactome membership ∩ background | count | **EXTERNAL / SNAPSHOT** | not snapshotted at fetch time; reproducible only by lookup vs `reactome_pathway_snapshot.csv` |
| `overlap` | # query genes in the pathway | query ∩ pathway membership | count | **EXTERNAL** | depends on live membership; not offline-reproducible |
| `p_value` | hypergeometric over-representation p | `hypergeom.sf(overlap-1, N=10273, pathway_size_bg, query_size)` | p-value | file's own columns | N=10,273 unique detected downstream genes (confirmed) |
| `fdr` | BH-adjusted p within flagship/direction | `false_discovery_control(p_value, method='bh')` grouped by (flagship, direction) | q-value | file's own columns | — |
| `expression_artifact_flag` | curated flag: pathway is a generic high-expression / proliferation artifact | curated per-pathway attribute (152 of 1,807 unique pathways True) | bool | **CURATED (non-recomputable)** | **CAVEAT: curated heuristic, NOT fully recomputable.** A keyword rule over proliferation/cell-cycle/RNA/translation/DNA-replication/repair/rRNA/splicing/tRNA/proteasome/SUMOylation/APC-C/telomere/spindle/checkpoint terms reproduces only ~94.5% of unique pathways (audit: 87.4% row-level). The flag is consistent per pathway_id and is carried verbatim in `reactome_pathway_snapshot.csv`; verify by lookup, do not recompute. |

**Resolution of `expression_artifact_flag` and the Reactome dependency (option b + snapshot):**
the delivered flag values are KEPT (they are internally consistent, one value
per pathway). Because no keyword rule fully reproduces them and Reactome was not
snapshotted at build time, a **Reactome snapshot artifact**
(`reactome_pathway_snapshot.csv`: `reactome_version, pathway_id, pathway_name,
pathway_size_bg, expression_artifact_flag, n_rows_used`) is saved so that `pathway_size_bg`,
`overlap` arithmetic, and the flag are reproducible by lookup. These four
pathway columns are documented as **external-state** columns.

---

## 3. lincs_concordance.csv  (4 rows x 6 cols)

**Definition:** DEMO-level directional sanity check of 4 targets against LINCS
L1000 landmark signatures. **Audit: CLEAN — all values reproduce exactly.**
**Reproducible-from:** raw matrix + `lincs_demo_signatures_4genes.csv`
(`db18632b-f68a-4025-9f03-4688c343e939`, 978 landmark genes x {SENP5,PLCG1,CCNC,PMVK}).

| column | definition | formula / derivation | units | reproducible-from | caveat |
|---|---|---|---|---|---|
| `target` | target gene tested | label | symbol | given | one of SENP5, PLCG1, CCNC, PMVK |
| `n_shared_landmark` | # downstream genes shared with the 978 LINCS landmarks | `|profile.index ∩ landmarks|` | count | raw + LINCS sig | — |
| `sign_agreement_frac` | fraction of shared genes with matching sign | `mean(sign(profile)==sign(LINCS))` over shared genes | fraction | raw + LINCS sig | profile = strongest `|log_fc|` across conditions per downstream gene |
| `spearman_rho` | Spearman correlation of the two profiles over shared genes | `spearmanr(profile, LINCS)` rho | correlation | raw + LINCS sig | — |
| `p_value` | Spearman p-value | `spearmanr(...)` pvalue | p-value | raw + LINCS sig | — |
| `caveat` | free-text disclaimer | given | text | given | DEMO-level: non-T-cell LINCS lines, 4 targets, NOT full external validation |

---

## 4. validation_target_set.csv  (55 rows x 8 cols)  [Level 4 — audit CLEAN]

**Definition:** the 55-gene validation set = top-50 by `primary_rank` + 5
flagships (`CD3E, PLCG1, VAV1, BCL10, STAT3`). **Reproducible-from:**
`signed_ranking_v2.csv` shortlist (exact row-order reproduction).

| column | definition | formula / derivation | units | reproducible-from | caveat |
|---|---|---|---|---|---|
| `primary_rank` | as in signed_ranking_v2 | inherited | rank | signed_ranking_v2 | — |
| `target_gene` | HGNC symbol | inherited | symbol | signed_ranking_v2 | — |
| `target_ensembl_id` | Ensembl ID | inherited | ENSG | signed_ranking_v2 | — |
| `directionality_index` | DI (see file 1) | `(n_up-n_down)/(n_up+n_down)` | ratio | signed_ranking_v2 | formula defined in file 1 |
| `footprint_class` | SIGN footprint label (see file 1) | inherited | category | signed_ranking_v2 | — |
| `signed_net` | net up-vs-down | `n_up-n_down` | count | signed_ranking_v2 | — |
| `n_up` | up hits | inherited | count | signed_ranking_v2 | — |
| `n_down` | down hits | inherited | count | signed_ranking_v2 | — |

---

## 5. track_a_gwas.csv  (55 rows x 16 cols)  [Level 4 — audit CLEAN]

**Definition:** Open Targets (OT) genetic-association crosscheck for the 55
validation targets. **Reproducible-from:** `signed_ranking_v2.csv` (identity
columns) + **OT Platform GraphQL** (association scores). OT is EXTERNAL state.

| column | definition | formula / derivation | units | reproducible-from | caveat |
|---|---|---|---|---|---|
| `primary_rank`, `target_gene`, `target_ensembl_id`, `directionality_index`, `footprint_class`, `signed_net` | identity columns | inherited from signed_ranking_v2 | — | signed_ranking_v2 | — |
| `n_genetic_assoc_diseases` | # diseases with a genetic_association datatype score | count from OT | count | **EXTERNAL (OT)** | OT Platform v4 GraphQL |
| `n_immune_genetic_assoc` | # of those diseases classified "immune" | count after immune keyword filter | count | **EXTERNAL (OT) + heuristic** | see immune-classification caveat |
| `top_immune_disease` | highest-scoring immune-classified disease | argmax GA score among immune diseases | text | **EXTERNAL (OT) + heuristic** | — |
| `top_immune_GA_score` | its genetic_association score | OT GA score | score in [0,1] | **EXTERNAL (OT)** | — |
| `top_immune_overall` | overall association score of the top immune disease | OT overall score | score | **EXTERNAL (OT)** | — |
| `top_any_disease` | highest-scoring disease of any class | argmax GA score overall | text | **EXTERNAL (OT)** | — |
| `top_any_GA_score` | its GA score | OT GA score | score | **EXTERNAL (OT)** | — |
| `immune_diseases_list` | `disease(score); ...` list of immune diseases | formatted list | text | **EXTERNAL (OT) + heuristic** | — |
| `classic_autoimmune_hit` | `disease(score); ...` list restricted to classic autoimmune diseases | formatted list | text | **EXTERNAL (OT) + heuristic** | — |
| `has_classic_autoimmune` | any classic autoimmune hit present | bool | bool | **EXTERNAL (OT) + heuristic** | 22 True / 33 False |

**CAVEATS (track A):**
1. **"immune" classification is a hardcoded keyword heuristic** (plus the OT
   "immune system disorder" therapeutic area) — a subjective boundary, not an
   ontology-driven definition. The classification matches disease names/areas
   containing substrings such as: `immune`, `autoimmune`, `arthritis`, `lupus`,
   `psoriasis`, `asthma`, `allergic`/`allergy`, `eczema`/`dermatitis`,
   `colitis`, `Crohn`, `inflammatory bowel`, `multiple sclerosis`, `diabetes
   mellitus` (type 1), `thyroid`/`thyroiditis`/`Graves`/`Hashimoto`,
   `vitiligo`, `ankylosing spondylitis`, `Behcet`, `celiac`, `immunodef*`. The
   "classic autoimmune" subset is a narrower curated list of canonical
   autoimmune diseases. Treat these labels as heuristic, not definitive.
2. **OT scores are external state.** Live re-query confirmed the saved values
   (audit: TYK2 RA=0.9310/n=37; CD3E immunodef=0.9155/n=5; STAT3 hyperIgE=0.9472/n=16),
   but scores change with OT releases. Document the OT Platform version/date at
   the time of use (v2 build used OT Platform v4 GraphQL). Not offline-reproducible.
   Verbatim audit confirmation (specific OT disease terms preserved): TYK2 RA=0.9310/n=37,
   CD3E immunodef18=0.9155/n=5, STAT3 hyperIgE6=0.9472/n=16 — the `18`/`6` suffixes
   identify the specific OT immunodeficiency / hyper-IgE-syndrome subtype terms.

---

## 6. track_b_string.csv  (15 rows x 7 cols)  [Level 4 — audit CLEAN]

**Definition:** STRING known-partner recovery for 5 flagships + top-10 primary
targets. **Reproducible-from:** downstream gene sets + `partners.json` (STRING
partner lists). STRING is EXTERNAL state.

| column | definition | formula / derivation | units | reproducible-from | caveat |
|---|---|---|---|---|---|
| `target_gene` | target symbol | label | symbol | given | — |
| `group` | `flagship` or `primary_top10` | label | category | given | 5 flagship + 10 primary_top10 |
| `n_known_partners` | # STRING known partners | count from `partners.json` | count | **EXTERNAL (STRING)** | STRING confidence threshold set upstream in partners.json build (not stated in-file) |
| `n_downstream_total` | # downstream genes for the target | count | count | raw | — |
| `n_in_downstream` | # known partners recovered among downstream genes | `|partners ∩ downstream|` | count | raw + STRING | — |
| `recovery_frac` | fraction of known partners recovered | `n_in_downstream / n_known_partners` | fraction | raw + STRING | **NaN when n_known_partners==0** (e.g. TMEM131L) — correct div-by-zero handling. Audit confirmed STAT3 = 115/324 = 0.3549. |
| `partners_in_downstream` | `;`-joined recovered partner symbols | set intersection, sorted | text | raw + STRING | — |

**CAVEAT (track B):** `n_known_partners` and the partner lists depend on the
STRING snapshot / confidence threshold used to build `partners.json`. Document
the STRING version/date and confidence cutoff at time of use. External state.

---

## 7. track_c_gse318876.csv  (1,235 rows x 12 cols)  [Level 4 — audit CLEAN]

**Definition:** cross-reference of the 1,235-target shortlist against the
GSE318876 genome-wide CRISPR HIV screens (CRISPRa & CRISPRn). **Reproducible-from:**
shortlist identity columns + GSE318876 MAGeCK results (raw screen data).

| column | definition | formula / derivation | units | reproducible-from | caveat |
|---|---|---|---|---|---|
| `target` | target symbol | label | symbol | given | shortlist genes |
| `in_library` | target present in the CRISPR library | bool | bool | GSE318876 | 1,192 True / 43 False |
| `best_neg_fdr` | best (min) MAGeCK negative-selection FDR across screens | `min FDR` over GW-CRISPRa-HIV & GW-CRISPRn-HIV | q-value | GSE318876 | NaN if not in library |
| `best_pos_fdr` | best (min) MAGeCK positive-selection FDR across screens | `min FDR` over both screens | q-value | GSE318876 | audit: VAV1 pos FDR ~2.4e-4 confirmed |
| `best_lfc` | log-fold-change at the best-FDR call | MAGeCK lfc | log FC | GSE318876 | — |
| `screen` | which screen gave the best call | `GW-CRISPRa-HIV` / `GW-CRISPRn-HIV` | category | GSE318876 | NaN if not in library |
| `best_dir` | direction of the best call | `pos` / `neg` | category | GSE318876 | — |
| `hiv_hit_class` | HIV screen hit classification | `HIV_host_factor_hit` (87) / `present_no_hit` (1,105) / `not_in_library` (43) | category | GSE318876 | threshold-based on FDR |
| `moves_in_uninfected` | target also moves in the uninfected control arm | bool | bool | GSE318876 | 46 True |
| `primary_rank` | as in signed_ranking_v2 | inherited | rank | signed_ranking_v2 | — |
| `signed_rank` | as in signed_ranking_v2 | inherited | rank | signed_ranking_v2 | see file-1 intra-tie caveat |
| `in_val55` | target is in the 55-gene validation set | bool | bool | validation_target_set | 55 True |

**CAVEAT (track C):** MAGeCK FDR/lfc values inherit the GSE318876 processing
pipeline; `hiv_hit_class` thresholds are applied on those FDRs. All 1,235 rows
reproduced in audit (52/55 val55 and 1,192/1,235 shortlist in library).

---

## Reproducibility status summary

| status | meaning |
|---|---|
| **REPRODUCED** | recomputes exactly (or within numerical tolerance) from raw + documented inputs |
| **SNAPSHOT** | reproducible only by lookup against a saved snapshot (Reactome membership) |
| **CURATED** | curated heuristic; values kept & documented, not fully recomputable |
| **EXTERNAL** | depends on external database state (Reactome / OT / STRING / GEO); document version/date |
| **GIVEN** | free-text or label carried through, not computed |

Run `reproduce_signed_tracks.py` to regenerate and assert the REPRODUCED columns
of the three signed files. See `reproduction_report.md` for the latest run.
