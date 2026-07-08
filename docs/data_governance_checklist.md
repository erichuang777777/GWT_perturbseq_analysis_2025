# Data Governance Checklist (C5)

**Status:** living checklist · **Last updated:** 2026-07-07

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
| `sources/target_tool_cache/_overlays/gnomad_constraint_seed.csv` (§C of `docs/next_phases_plan.md`, gnomAD LOEUF/pLI safety overlay) | 8-gene seed of gnomAD loss-of-function constraint metrics (LOEUF, pLI), derived from the real values already checked in at `docs/mvp-research/connector_enrichment_demo.csv`, joined to Ensembl gene IDs via `gene_identifier_resolver.load_resolver()` | gnomAD is a public, population-level aggregate constraint database (gnomAD terms of use: freely usable, no patient-level or individual-participant data — LOEUF/pLI are gene x population summary statistics, not genotypes) | Low risk — public aggregate gene-level annotations, no identifiers. This is explicitly a placeholder 8-gene seed for testing/demo; a full-genome gnomAD snapshot (owner-supplied, per the same file path) should carry the same public-aggregate-data characterization when it lands. |
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
