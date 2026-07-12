# Data Governance Checklist (C5)

**Status:** living checklist · **Last updated:** 2026-07-12

Scope: every data source this toolkit reads, writes, or fetches, and the handling rules that apply to
each. This is a checklist to run through before any of the following: adding a new data source, changing
what's exposed via the API/dashboard, or considering external redistribution/publication of an output.

---

## 1. Source inventory and licensing status

| Source | What it is | License / terms | Action needed |
|---|---|---|---|
| This repo's own code (`src/`, `docs/`) | Toolkit implementation | MIT (`LICENSE`) | None — freely reusable |
| GWT reference dataset (`metadata/suppl_tables/*.csv`, bioRxiv `10.64898/2025.12.23.696273v1`) | Marson-lab CD4 Perturb-seq screen | **Not stated** anywhere in this repo (`metadata/data_sharing_readme.md` documents schema, not reuse terms) | **Verify before any external redistribution or publication use.** Treat as internal-research-use-only until the dataset's own license/DUA is confirmed. This toolkit only *reads* it locally — it never re-publishes the raw tables. |
| Local overlay gene lists (`metadata/gene_lists/*.tsv`: core-essentiality/Hart, druggable-class, ClinVar path/likely-path membership; `sources/broad_effect_genes.txt`) | Static snapshots already committed to the repo | Each source has its own terms (e.g. Hart essentiality screen is a published academic dataset; ClinVar is public domain via NCBI) | These are membership lookups, not redistributed wholesale — low risk. No `fetched_at` stamp exists on these static files; if they are ever refreshed, add one (see §3, "static overlay staleness" below) |
| `src/6_functional_interaction/results/disease_gene_associations_detailed.csv` (Open Targets export) | Prior-research join table used by `disease_translator.py` | Open Targets platform data is published under their own open-data terms | Re-verify Open Targets' current terms before external redistribution of this specific derived export |
| Live connectors: ClinicalTrials.gov, PubMed/E-utilities, Open Targets GraphQL (`external_evidence_cache.py`) | Public government/nonprofit registries | NLM/NCBI usage policies (rate limits, no bulk scraping), Open Targets API terms | Already respected by design: fetches happen only in an offline batch job (`build_evidence_for_gene(s)`), never in the request path, and are TTL-cached (30 days, see §3) rather than re-fetched per view |
| `docs/mvp-research/adc_overlay_gwt_overlap_full.csv` (§1.12 membrane/tractability overlay) | GWT-target join of the project owner's ADC target-discovery database (`candidate_genes.parquet`) | Per `docs/mvp-research/ADC_LOCAL_DATA_INGESTION_SPEC.md`, the underlying fields (surface-protein/transmembrane-domain calls) derive from public databases (HPA, UniProt, CSPA) — no patient-level or proprietary-cohort data. The join itself (which GWT genes overlap) is derived, not raw redistribution. | Low risk — public-database-derived gene annotations, not patient data. Re-confirm before external redistribution if the source parquet's own terms are ever formalized. |
| `sources/target_tool_cache/_overlays/gnomad_constraint_seed.csv` (§C of `docs/next_phases_plan.md`, gnomAD LOEUF/pLI safety overlay) | Full-genome gnomAD **v2.1.1** by-gene loss-of-function constraint metrics (LOEUF = `oe_lof_upper`, pLI), 19,155 genes (one row per gene, chrX included), built reproducibly from gnomAD's public GCS release bucket by `src/3_DE_analysis/data_acquisition/build_gnomad_constraint_overlay.py` (`gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz`). Ensembl gene IDs come straight from the source's `gene_id` column (no invented IDs). Covers 11,267 / 11,526 targets (~97.8%); replaced the earlier 15-gene demo seed derived from `connector_enrichment_demo.csv`. | gnomAD is a public, population-level aggregate constraint database (gnomAD terms of use: freely usable, no patient-level or individual-participant data — LOEUF/pLI are gene x population summary statistics, not genotypes) | Low risk — public aggregate gene-level annotations, no identifiers. Whole-genome public snapshot; v2.1.1 chosen over v4.1 because it is complete across chrX (the v4.1 flat distribution reachable in the build env was autosomes-only and would have dropped FOXP3/MED12/CD40LG). Rebuild is deterministic and byte-stable. |
| UK Biobank LoF-burden estimates (`src/8_lymphocyte_counts_LoF/input/Backman_*.tsv`, `population_hypothesis.py`) | Backman et al. 2021 exome-wide rare-variant burden effect estimates | Published, de-identified, **population-level** (gene x trait posterior estimates) — not individual UK Biobank participant data | Already gene-level aggregate only; the population-vs-patient distinction is enforced in code (§2 below extends the same principle from donor demographics to this source) |

**Open action:** none of the above are blocking today (nothing in this toolkit re-publishes raw source
data outside this repo), but the GWT dataset's own license status is the single item to close out before
any external sharing decision.

---

## 2. Human-subject data handling

- `sample_metadata.suppl_table.csv` carries per-donor demographics for a **small cohort (D1–D4, 4
  donors)**: `age`, `sex`, `ethnicity`, `weight_kg`, `height_cm`. No name/MRN/direct identifier is
  present, but with only 4 donors, a full demographic combination is potentially quasi-identifying if
  ever cross-referenced against another dataset describing the same cohort.
- **Confirmed by code search:** no module under `src/3_DE_analysis/` reads or exposes `age`, `sex`,
  `ethnicity`, `weight_kg`, or `height_cm` anywhere — the only sample-metadata field this toolkit
  actually uses is `culture_condition` + run/lane ID, for the batch-confound check
  (`confounded_conditions()`). This is a real, verified property of the current code, not an assumption.
- **Rule going forward:** any future feature that would summarize or expose donor demographics (e.g. "do
  responders skew by donor age/sex") needs a governance review before shipping — don't add a per-donor
  demographic breakdown to the API or dashboard without one, precisely because n=4 is too small to
  aggregate away re-identification risk.
- Cell-level and pseudobulk data (`donor_id` — an internal `D1`–`D4`-style code, not the demographics
  table) is not itself sensitive; the demographics table above is the one file this rule targets.

### 2a. Individual-sample input (exploratory demo module — `individual_concept_profile.py`)

The prior blanket rule "this toolkit accepts no individual-sample input" is **superseded, in a
tightly-scoped way**, by the exploratory concept-profile demo (see
`docs/compass_concept_integration_plan.md`). The rewritten rule and its enforced guarantees:

- **Scope:** one module (`POST /api/individual-concept-profile`) accepts a single sample's
  gene-expression vector (`{gene_symbol: value}`) and returns a **transparent projection** onto the
  20 CD4 immune concept modules plus hypothesis-only screened-target links. It is an **exploratory
  research demo, explicitly NOT medical software** — every output carries a forced non-diagnostic
  caveat, and it never emits diagnosis, treatment, dose, prognosis, or efficacy predictions.
- **No identifiers:** the endpoint accepts only expression values; no name/MRN/date/demographic field
  is read or stored. (Same n=4-style re-identification caution as §2 does not even arise, because no
  identifying attributes are ingested at all.)
- **Request-only, never persisted:** the raw input expression vector lives only in the request's
  memory — it is never written to `sources/target_tool_cache/`, never logged to a file, never cached,
  never transmitted to any external service. This is enforced by a no-persist audit test
  (`tests/test_individual_concept_profile.py`) that asserts no new file appears under the cache
  directory across a request.
- **Transparent, not black-box:** concept activation is a hand-auditable aggregate of standardized
  expression over each concept's seed genes (with reported coverage), not a learned/opaque weight —
  so a reviewer can reproduce every number. No response-prediction classifier is built (that would
  need patient-outcome labels this repo does not have and must not fabricate — flagged data-blocked
  in the plan §6).
- **Descriptive only:** the concept profile never feeds `readiness_call`/`overall_readiness_stage`/
  `statistical_evidence_grade` — same causal-independence property enforced for `safety_window_score`
  and the gnomAD/mechanism-graph overlays.

---

## 3. Freshness / staleness disclosure

- **Static overlay lists** (essentiality, druggable-class, ClinVar, broad-effect genes) have no
  `fetched_at` stamp today — they are whatever was committed to the repo at whatever time that was. If
  any of these is ever regenerated from a live source, stamp it the same way `external_evidence_cache.py`
  does (`fetched_at` + a source-version string), so a consumer can tell how current a given membership
  check is.
- **Live-connector evidence** already self-discloses freshness via `fetched_at` per gene and a 30-day TTL
  (see `docs/cache_and_versioning_policy.md` §2) — no action needed here, just keep using the existing
  pattern for any new connector.
- **`unknown` vs `0` discipline**: every domain this toolkit cannot currently answer (safety window,
  genetics without a fetched Open Targets snapshot, tractability without a local overlay hit) returns the
  literal string `"unknown"`, never a numeric `0` — this is enforced by convention across
  `readiness_engine.py`, not by a runtime check. **Governance rule:** any new domain/score added later
  must follow the same convention; a reviewer should reject a PR that silently defaults an unmeasured
  domain to `0`.

---

## 4. User-upload data isolation

- Every dataset build now carries an `origin` field: `"gwt_reference"` vs `"user_upload"` (stamped in
  `target_card_api.py` and consumed by `frontend/dashboard/target_card_dashboard.py`'s compatibility banner).
- User-uploaded datasets are namespaced (`usr_<uuid>` / import-lineage-tracked) and are **never** blended
  into the GWT reference card set — confirmed in `import_manager.py`/`target_card_api.py`'s merge path,
  which always writes to a new dataset directory rather than appending to the reference build.
- Runtime caches for user uploads (`sources/target_tool_cache/usr_*/`, `sources/target_tool_cache/imports/*/`)
  are `.gitignore`d — they never get committed. Only the GWT reference build and the one intentional demo
  dataset (`sources/target_tool_cache/e7ecd8d5-.../`) are tracked in git.
- No authentication/multi-user isolation exists yet (`docs/IMPLEMENTATION_PLAN.md` §1.8, explicitly
  deprioritized by the project owner) — this is single-user/file-cache research use, not a
  multi-tenant platform. **Do not treat the current per-dataset-directory namespacing as access control**
  — it prevents accidental data blending, not unauthorized access, since there is no auth layer.

---

## 5. Before adding a new external data source — checklist

1. Does it require network access? If yes, does it go through the same offline-batch-job +
   TTL-cache-snapshot pattern as `external_evidence_cache.py` (never a live fetch in a request path)?
2. Does it degrade honestly (`source_status: "unavailable"`, not a crash or a fabricated value) when
   unreachable — confirmed against this sandbox's actual outbound-proxy policy, not assumed?
3. What's its license/terms, and are they compatible with this repo's stated use (internal research
   tooling, not redistribution)? Record it in the §1 table above.
4. Does it carry any human-subject or otherwise sensitive fields? If yes, apply the same rule as §2:
   don't expose per-individual breakdowns without a review, especially at small n.
5. Does every domain it can't answer land on an explicit `"unknown"`, never a silent `0`?

---

## 6. Prepared-but-unintegrated data inventory

Audited 2026-07-12 in response to an explicit release-prep question: is there any data this repo
already has, sitting completely independent — not generated by any pipeline stage, and not read/imported
by any code? Scope: `metadata/` (raw-input tier) and `sources/` (research/overlay tier).

**Method:** `git log --all --oneline -S"<basename>" -- '*.py' '*.ipynb' '*.R' '*.sh'` against the full
531-commit, non-shallow history — not just the current working tree — for every candidate file. This
answers "was this file EVER read by executable code, at any point in this repo's history," which is a
stronger check than grepping the current tree (it also catches code that read a file and was later
deleted).

**Finding: every file below is "never integrated," not "integrated then abandoned."** The pickaxe search
returned **zero** commits for all seven candidates, across every commit and every code file type. None
was ever referenced inside a `.py`/`.ipynb`/`.R`/`.sh` file at any point in this repo's history. Where a
file is mentioned in a doc (provenance registry, wiki, README), that is documentation-level intent, not
code execution — called out explicitly where it applies, since a few of these are cases of "we said we'd
use it" rather than silent omission.

| File | What it is | Status | Why it was never wired in (assessment) | Recommended action |
|---|---|---|---|---|
| `metadata/rna_single_cell_datasets.tsv.zip` | Human Protein Atlas single-cell RNA expression, per dataset | Never integrated (0 code refs, all history) | Its sibling `rna_tissue_consensus.tsv.zip` (bulk-tissue version) WAS read, in full, by `src/6_functional_interaction/tissue_specificity.ipynb` (16/17 cells executed) — that notebook simply never got to the single-cell-resolution siblings. No stated reason found; scope appears to have stopped at the bulk-tissue analysis. | Candidate to widen `safety_window_from_gtex`'s off-context-breadth signal with single-cell-resolution tissue specificity, if pursued later — record as a `docs/ROADMAP.md` item, not a silent gap. |
| `metadata/rna_single_cell_type_group.tsv.zip` | HPA single-cell type-group summary | Never integrated (0 code refs, all history) | Same as above — downloaded alongside the two files above, never opened by any notebook/script. | Same as above. |
| `sources/topic13_clinicaltrials_flat.csv` | 327-row ClinicalTrials.gov snapshot (`search_term, nctId, status, phases, conditions, interventions`), captured during the pre-development literature scan | Never integrated (0 code refs, all history) | The live `external_evidence_cache.py` ClinicalTrials fetcher was built independently, later, with its own TTL-cache pattern — this static snapshot was never wired in as a seed or offline fallback, even though the fetcher's target host is sometimes policy-blocked in sandboxed environments (confirmed this session for Open Targets/GWAS Catalog — see `docs/tier2-gene-for-Claude science.md` §2). | Candidate offline fallback/seed for the ClinicalTrials connector when the live host is unreachable. Would need an explicit freshness caveat (snapshot date, not live) if ever used this way — do not present it as current. |
| `metadata/Freimer2022_Screen.csv` | Freimer et al. 2022 T-cell effector screen results | Never integrated (0 code refs, all history) — but documentation-level intent exists | `docs/provenance_registry.csv` registers it as a data source with the stated purpose "external screen cross-check" (PMID 36356142) — the intent to cross-validate GWT hits against this screen was documented, but no code was ever written to do the join. This is a **stated-intent-not-executed** gap, not a silent omission. | Either build the cross-check (join on gene symbol, compare hit calls) or correct `docs/provenance_registry.csv`/`wiki/Manual.md` so they stop implying an active cross-check that doesn't exist. |
| `metadata/donor_info.csv` | 4-donor demographic table (age/sex/ethnicity/weight/height/blood type) | Never integrated (0 code refs, all history) | Genuinely orphaned — mentioned only in `metadata/README.md`'s own file listing. Consistent with §2 above ("no module under `src/3_DE_analysis/` reads or exposes age/sex/ethnicity/weight_kg/height_cm") — this is that finding's source file, made explicit. | None needed for the toolkit as-is. If a future donor-covariate QC feature is ever built from this file, it must go through the §2 small-*n* re-identification review before exposing any field. |
| `sources/topic01_local_druggable_targets_summary.csv` | 1,015-row early-stage druggability summary built directly from DE stats (`target_contrast_gene_name, max_de, mean_de, conditions_with_gt10, max_cells, any_offtarget, ontarget_sig_conditions, target_class`) | Never integrated (0 code refs, all history) | A pre-development research artifact, **not** a superseded former dependency — git history confirms no commit ever had code read it, so this is not a case of code being removed later. Its intended function (gene-level druggability classification) was subsequently implemented more completely by `build_target_cards.py` + the `metadata/gene_lists/*.tsv` druggable-class overlays. | None — its role is already fulfilled by the current pipeline. Keep as a historical research artifact only, no action needed. |
| `metadata/suppl_tables/stabl_constructs.csv` | Plasmid/construct DNA sequence list (construct name, sequence, usage annotation e.g. "perturb-seq and IL10/IL21 validation") | Never integrated (0 code refs, all history) | Wet-lab construct metadata for the source paper's validation experiments, not gene-expression or association data — there is nothing in it for a bioinformatics analysis pipeline to read. Correctly unused. | None — out of scope for this toolkit by design, not an oversight. |

**Related documentation bug found during this audit:** `metadata/README.md`'s "External Screen/Study
Data" and "Reference Gene Lists" sections each listed one file that does not exist anywhere in this
checkout — `rest_functional_group.csv` and `Replogle2022_TableS3_perturb_clusters.xlsx` (both were
already marked `??` in the README itself, suggesting even the original author was unsure). Corrected to
say so explicitly rather than silently dropped, so the gap stays visible instead of just disappearing
from the doc.

**Re-running this audit later:** `git log --all --oneline -S"<basename>" -- '*.py' '*.ipynb' '*.R' '*.sh'`
returning empty is the check — it means no commit in the entire history ever added or removed a reference
to that filename inside executable code. That is the bar for "integrated," not merely appearing in a
directory listing or being mentioned in prose.
