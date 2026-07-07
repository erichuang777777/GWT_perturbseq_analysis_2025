# Data Dictionary — CD4 Perturb-seq Target-Discovery Toolkit

**Status:** living reference · **Last updated:** 2026-07-07

This documents every column and field the toolkit *produces* (`target_cards.csv`, the readiness
frame, the resolver/search results, the CRE schema, the external-evidence snapshot, and the module-score
table), plus the *real, in-repo raw inputs* they're derived from. It does not restate DE/NTC/knockdown
methodology already covered in `docs/de_and_baseline_spec.md` — see that document for the statistical
definitions; this one is a column-by-column reference for anyone joining against or consuming the
toolkit's outputs.

Every field below is either (a) copied through from a real upstream file, (b) a deterministic function
of upstream fields (formula given), or (c) an explicit `"unknown"`/empty placeholder when the toolkit has
no data for it. Nothing here is a fabricated or imputed value unless stated.

---

## 1. Raw inputs (upstream, not computed by this toolkit)

| File | Rows | Key columns used | Notes |
|---|---|---|---|
| `metadata/suppl_tables/DE_stats.suppl_table.csv` | 33,983 | `target_contrast_gene_name`, `culture_condition`, `target_contrast` (Ensembl ID), `n_cells_target`, `n_up_genes`, `n_down_genes`, `n_total_de_genes`, `ontarget_effect_size`, `ontarget_significant`, `target_baseMean`, `offtarget_flag`, `crossdonor_correlation_mean/min`, `crossguide_correlation` | One row per `(target gene, culture_condition)`. DESeq2 pseudobulk results; see `de_and_baseline_spec.md` §2. |
| `metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv` | 73,765 | `guide_id`, `perturbed_gene_id` (Ensembl ID), `culture_condition`, `ntc_mean_expr/std_expr/n`, `guide_mean_expr/std_expr/n`, `t_statistic`, `p_value`, `adj_p_value`, `signif_knockdown` | One row per guide per condition. Knockdown t-test vs condition-matched NTC pool; see `de_and_baseline_spec.md` §3. |
| `metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv` | 31,109 | `target_gene_id` (Ensembl ID), `target_gene_name` (curated canonical symbol), `target_gene_name_from_sgRNA` (sgRNA-design-time symbol) | 12,654 unique targeted genes; 344 have a real design-time-vs-curated symbol difference. Source of B1's alias table. |
| `metadata/suppl_tables/sample_metadata.suppl_table.csv` | 11 | `culture_condition`, `10xRun_ID` (or `run_id`) | Used to detect condition/run confounds (`confounded_conditions()`). |
| `sources/broad_effect_genes.txt` | 239 genes | newline-delimited gene symbols | CORUM-keyword ∪ EDA-named broad/pleiotropic chromatin-transcription-machinery genes (Mediator, SAGA, HAT/HDAC, SWI/SNF). Feeds the `broad_effect` red flag. |
| `metadata/gene_lists/core_essentials_hart.tsv`, `metadata/gene_lists/*.tsv` | varies | gene symbol per line | Core-essentiality (Hart screen) and druggable-class overlays (kinase/GPCR/enzyme/surface/cytokine-R/NR). Missing files simply leave the corresponding domain `"unknown"`, never `0`. |
| `src/6_functional_interaction/results/disease_gene_associations_detailed.csv` | 7,528 | `disease_efo`, `disease_name`, `gene_symbol`, `association_score`, `genetic_evidence_score`, `genetic_evidence_types` | 13 autoimmune/inflammatory indications; feeds `disease_translator.py`. |
| `sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv` | — | gene sets per CD4 program (activation/Treg/Th1/Th2/Th17/Tfh/exhaustion/cytokine) | Feeds `/api/modules` binary-overlap module scoring (see §5). |

---

## 2. `target_cards.csv` — one row per `(target, condition)`

Built by `build_target_cards.py::build_cards_frame`. `target_id` here is the raw contrast ID
(`target_contrast`, e.g. an Ensembl gene ID); `target` is the resolved gene symbol.

| Column | Type | Meaning | Derivation |
|---|---|---|---|
| `target` | str | Gene symbol | `target_contrast_gene_name`, or library-map fallback by `target_gene_id` |
| `condition` | str | Culture condition (e.g. `Rest`, `Stim8hr`, `Stim48hr`) | `culture_condition`, renamed |
| `target_id` | str | Raw contrast identifier (Ensembl gene ID) | `target_contrast`, renamed |
| `n_cells_target` | int | Cells in this target/condition's pseudobulk aggregate | passthrough |
| `n_guides` | int | Distinct guides with KD data for this target/condition | `nunique(guide_id)` grouped by `(perturbed_gene_id, culture_condition)` |
| `n_total_de_genes`, `n_up_genes`, `n_down_genes` | int | DE gene counts at 10% FDR | passthrough, see `de_and_baseline_spec.md` §2 |
| `ontarget_effect_size` | float | On-target log2FC | passthrough |
| `ontarget_significant` | bool | On-target effect clears 10% FDR in the KD direction | passthrough |
| `offtarget_flag` | bool | Upstream off-target flag | passthrough |
| `median_logFC`, `max_abs_logFC` | float | Alias/derived from `ontarget_effect_size` | `median_logFC = ontarget_effect_size`; `max_abs_logFC = abs(ontarget_effect_size)` |
| `fdr_min`, `guide_fdr_min` | float | Minimum `adj_p_value` across this target/condition's guides | `min()` of guide `adj_p_value` |
| `crossdonor_correlation_mean`, `crossdonor_correlation_min` | float | Cross-donor DE reproducibility | passthrough; `NaN` treated as failing every downstream `>=` comparison, never imputed |
| `crossguide_correlation` | float | Cross-guide DE reproducibility | passthrough, same NaN policy |
| `replicate_pass_flag` | bool | Passes the coarse reproducibility bar (cells, DE count, significance, no off-target, cross-donor/guide >= 0.2) | boolean AND of the 6 conditions in `build_cards_frame` |
| `batch_sensitivity_flag` | `"sensitive"` / `"confounded_but_robust"` / `"not_flagged"` / `"unknown"` | Whether this condition is confounded with a single 10x run | `"unknown"` if no `sample_meta` supplied; else computed via `confounded_conditions()` |
| `guide_signif_ratio` | float [0,1] | Fraction of this target/condition's guides with `signif_knockdown=True` | mean of `signif_knockdown` |
| `guide_t_abs_median` | float | Median absolute t-statistic across guides | passthrough aggregate |
| `positive_control_similarity` | 0/1 | Is this target in the curated `POSITIVE_CONTROLS` set | membership test |
| `pathway_axis` | str or `"unassigned"` | Local pathway-keyword overlay (not an external ontology) | keyword match against `PATHWAY_AXIS_HINTS` |
| `condition_specificity_score` | float [0,1] | Share of this target's total DE count contributed by this condition | `n_total_de_genes / sum(n_total_de_genes for this target across conditions)`. **Heuristic**, not a statistical interaction test — see code comment in `build_target_cards.py` |
| `condition_specificity_zscore` | float | Same signal, standardized within-condition | `(n_total_de_genes - condition_mean) / condition_std` |
| `effect_direction_flip_flag` | bool | Does this target's on-target effect sign flip across conditions | `any(sign>0) and any(sign<0)` grouped by target |
| `clinical_axis` | str or `"unassigned"` | Local clinical-benchmark-drug axis keyword match | keyword match against `CLINICAL_BENCHMARK_KEYWORDS` |
| `nearest_success_drug` | str (may be empty) | First matching drug name from the local clinical-benchmark CSV | regex containment match; empty if no benchmark supplied or no match |
| `nearest_failure_or_warning` | str | Reserved column, always empty in this build | placeholder, not yet populated by any data source |
| `target_baseline_expression` | float or NaN | Target's baseline expression in NTC cells for this condition | `ntc_mean_expr`, `"first"` aggregate (confirmed invariant per target/condition group, 0/37,578 groups violate this) |
| `kd_status` | `"confirmed"` / `"weak"` / `"not_measurable"` | 3-state on-target knockdown status | `not_measurable` if baseline <= 0.001 (or missing); else `confirmed` if `guide_signif_ratio>=0.5 and guide_fdr_min<=0.05`; else `weak` |
| `kd_threshold_version` | str | Version tag for the kd_status threshold logic | constant `"kd_status/v1"` |
| `statistical_evidence_grade` | int 1-4 | Coarse evidence-strength grade | see `_make_score()`: 4 requires full replication + guide robustness + `n_guides>=2`; 3 requires replication + `n_guides>=2` + `fdr_min<=0.1`; 2 requires cells+significance only; else 1 |
| `score_cap_reason` | `;`-joined str or `"none"` | Every reason this row didn't reach a higher grade | union of off-target/batch/replicability/direction/guide-count/kd tokens, de-duplicated |
| `n_donors` | NaN | Reserved column | not available from `DE_stats.suppl_table.csv` alone; always NaN in this build |
| `druggable_class`, `tractability_modality`, `safety_note` | str (may be empty) | Local druggable-gene-class / ClinVar / immune-effector overlays | `annotate_local_overlays()`; empty string (not `"unknown"`) when a gene is absent from every local list — these are membership lookups, not model-scored domains |

---

## 3. Readiness frame — one row per `(target, condition)`

Built by `readiness_engine.py::compute_readiness`. Joins 1:1 onto `target_cards.csv` by
`(target, condition)`.

| Column | Type | Meaning | Derivation |
|---|---|---|---|
| `biology_causality_score` | 0/3/5 | Grade + known-pathway-membership composite | `_biology_causality()` |
| `disease_relevance_score` | 3 or `"unknown"` | Has a clinical axis or is a positive control | `_disease_relevance()` |
| `human_genetic_support` | `"yes"`/`"no"`/`"unknown"` | GWAS/ClinVar overlay membership, upgraded by a fetched Open Targets snapshot if present | `_human_genetic()` / `_human_genetic_from_evidence()` |
| `tractability_modality` | str or `"unknown"`/`"none"` | Druggable-class overlay match | `_tractability()` |
| `tractability_score` | 0/3 or `"unknown"` | Companion score to the modality | `_tractability()` |
| `safety_window_score` | 0 or `"unknown"` | `0` only if the gene is a known essential gene; else `"unknown"` (no safety-margin data source exists) | |
| `cd4_immune_red_flags` | `,`-joined str or `"none"` | Which immune-specific flags are set (offtarget/batch_sensitive/broad_effect) | |
| `biomarker_score` | 0/3 | Whether `n_total_de_genes >= 50` | `_biomarker()` |
| `translation_score` | 0/3/5 | Reproducibility composite | `_translation()` |
| `clinical_feasibility_score` | 3 or `"unknown"`, upgradable to 5 | Local benchmark-drug fallback, upgraded by fetched trial-phase evidence | `_clinical_feasibility()` |
| `red_flag_override` | `;`-joined str or `"none"` | Which red flags fired and capped the call | `essential_gene`, `broad_effect`, `high_offtarget`, `uncertain_direction`, `batch_confounded`, `kd_not_measurable`, `kd_weak` |
| `overall_readiness_stage` | `R0`-`R3` | Stage from the biology/translation/tractability/genetics composite | `_stage()` |
| `readiness_call` | `deprioritize`/`watchlist`/`validate`/`advance` | Final call: stage-implied call capped by the most restrictive fired red flag | `min()` over `CALL_ORDER` |
| `readiness_reasons` | str | Human-readable breakdown of every domain score and any red flags | `_reasons()` |
| `next_validation_step` | str | Concrete next experiment/check, chosen by the most specific applicable red flag or domain gap | `_next_step()` |
| `has_external_evidence` | bool | Whether a pre-fetched evidence snapshot (`external_evidence_cache.py`) was found for this gene | |

---

## 4. Gene resolution & search (B1/B2/B6)

**Resolver result** (`gene_identifier_resolver.py::GeneResolver.resolve` / `result_status`):

| Field | Type | Meaning |
|---|---|---|
| `query` | str | The original input string |
| `matched` | bool | Whether the query resolved to a known gene |
| `resolution_path` | str | `exact_ensembl_id` / `exact_canonical_symbol` / `exact_alias_symbol` / `case_insensitive_canonical_symbol` / `case_insensitive_alias_symbol` / `no_match` / `empty_query` |
| `ensembl_gene_id` | str or None | Resolved primary key |
| `canonical_symbol` | str or None | Resolved curated gene symbol |
| `is_expressed_in_dataset` | bool or None | `True`/`False` if a guide-KD expression floor check was supplied; `None` if not checked |
| `result_status` (B2, `result_status()` only) | `"not_in_library"` / `"not_expressed"` / `"no_significant_effect"` / `"has_effect"` | See `gene_identifier_resolver.py` module docstring for the exact decision order |
| `n_condition_rows` (B2 only) | int | How many DE/card rows back the `result_status` call |

**Search result** (`gene_search.py::search_genes`, one dict per hit, best first):

| Field | Type | Meaning |
|---|---|---|
| `ensembl_gene_id`, `canonical_symbol` | str | Resolved identity |
| `match_type` | `"exact"` / `"alias"` / `"prefix"` / `"fuzzy"` | Ranked in that order (`MATCH_TYPE_RANK`) |
| `score` | float [0,1] | Match confidence within its tier; `SequenceMatcher` ratio for fuzzy, length-ratio-based for prefix, `1.0` for exact/alias |

---

## 5. CRE schema placeholders (B5)

`cre_schema.py`. No CRE dataset exists in this repo as of this writing — every field below is a reserved
contract, returned empty with `available: False` until a real file is supplied.

| Table | Columns |
|---|---|
| `CisRegulatoryElement` | `cre_id`, `dataset_id`, `genome_build` (e.g. `"hg38"`), `chrom`, `start`, `end`, `linked_gene_ids` (`;`-joined) |
| `VariantCRELink` | `variant_id` (rsID or `chr:pos:ref:alt`), `cre_id`, `gwas_trait`, `source` |

---

## 6. External evidence snapshot (T5/T6/T2)

`external_evidence_cache.py`, one JSON file per gene at `sources/target_tool_cache/_evidence/<gene>.json`.

```
{ "gene": str, "fetched_at": ISO-8601 str,
  "sources": {
    "clinical_trials": { "source_status": "ok"|"unavailable", "items": [ {nct_id, title, phase, status, intervention, condition, url}, ... ] },
    "literature":      { "source_status": "ok"|"unavailable", "items": [ {pmid_or_doi, title, year, source, url, snippet}, ... ] },
    "open_targets":    { "source_status": "ok"|"unavailable", "items": [...] }
  }
}
```
`source_status: "unavailable"` (with an empty `items` list) means the connector was unreachable at
fetch time — confirmed in this sandbox for ClinicalTrials.gov, PubMed E-utilities, and the Open Targets
API (outbound-proxy policy blocks them); it never means "checked and found nothing," which is a `"ok"`
status with an empty `items` list.

---

## 7. Module scores (`/api/modules`)

Not a `target_cards.csv` column — served separately by `target_card_api.py::get_module_scores`, one row
per `(target, condition, module_id)`:

| Column | Meaning |
|---|---|
| `module_id`, `module_name` | CD4 program identifier (activation/Treg/Th1/Th2/Th17/Tfh/exhaustion/cytokine) from `sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv` |
| `overlap` | Count of this program's seed genes appearing in this target/condition's DE gene set |
| `module_score` | `overlap * (1 + score_basis)` — a binary-overlap composite, **not signed** (direction-of-effect is not incorporated; see the descope note in `docs/IMPLEMENTATION_PLAN.md` §1.5) |

---

## 8. Disease translator output (T8)

`disease_translator.py::translate_disease` returns `{"matched": bool, "reason": str|None, "targets": [...]}`.
Each target record adds `disease_association_score`, `genetic_evidence_score`, `genetic_evidence_types`
(all passthrough from the local Open Targets export, joined by upper-cased gene symbol) onto the usual
card + readiness columns.

---

## 9. Versioning fields (B4)

Stamped on every built dataset's `metadata.json` and every API response's `provenance` block
(`target_card_api.py::_provenance_block`):

| Field | Meaning |
|---|---|
| `engine_version` | This toolkit's own version string (`ENGINE_VERSION`) |
| `dataset_version` | GWT reference dataset version (references the bioRxiv DOI); only stamped on GWT-reference builds, never user uploads |
| `schema_version` | `target_cards.csv` column-schema version (`CARD_SCHEMA_VERSION`) — bump this whenever a column is added/removed/redefined |
| `signature_set_version` | Fingerprint of the seed-module gene sets used for module scoring |
| `kd_threshold_version` | Per-row, see §2 above |
| `built_at` | Timestamp the dataset was built |
