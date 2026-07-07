# Implementation Plan — CD4 Perturb-seq Target-Discovery Toolkit

**Status:** living plan · **Last updated:** 2026-07-07 · **Branch:** `claude/drug-discovery-tool-plan-258jof` (PR #1)

This is the executable companion to `docs/DRUG_DISCOVERY_TOOL_DEVELOPMENT_PLAN.md` (the strategy).
It tracks what is **built and verified**, what is **next**, and gives each remaining piece a concrete
spec, sequencing, effort, and acceptance test. Every data claim is grounded in in-repo files.

---

## 0. Where we are (verified, on this branch)

The first implementation wave is landed and tested end-to-end against the real in-repo CSVs.

| Piece | Module | State | Evidence of verification |
|---|---|---|---|
| Importable `build_cards_frame()` refactor | foundation | **done** | GWT build reproduced (33,983 rows) in-process and via CLI |
| Real `batch_sensitivity_flag` (was stubbed) | C4 | **done** | Only `Stim48hr` flagged (10,108 `sensitive`, 1,173 `confounded_but_robust`); Rest/Stim8hr never |
| NaN cross-corr → `weak_replicability` bug fix | foundation | **done** | Missing robustness now surfaces the caveat |
| `readiness_engine.py` (12-domain → R0–R5 → call) | R1–R3 | **done** | R3 530 / R2 572 / R1 18,252 / R0 14,629; essentials never `advance`; deterministic |
| Column-mapping wizard + merge helpers | U3/U4 | **done** | `import_manager` helpers + endpoints |
| Upload merge loop (approve → cards) | U4/U5 | **done** | TestClient: generic upload → map → approve → merge → `usr_` dataset → cards → readiness |
| API endpoints (mapping/merge/readiness) | A/B | **done** | `/api/imports/{id}/mapping[/suggestion]`, `/merge`, `/api/readiness/{id}` |
| Dashboard wiring (wizard, merge, readiness, banner) | D | **done** | py_compile + AST clean; calls verified endpoints |

**Files changed:** `src/3_DE_analysis/build_target_cards.py`, `readiness_engine.py` (new),
`import_manager.py`, `target_card_api.py`, `target_card_dashboard.py`.

### Known scientific gap surfaced during verification
The `advance` set still contains broad chromatin/essential-like genes (`MED12`, `CREBBP`, `KDM1A`,
`ELOB`) because `core_essentials_hart.tsv` (283 genes) does not cover them. This is the planned
**C7 confounder quarantine** — see §1.1. It is flagged, not ignored.

---

## 1. Remaining work — specs, sequencing, acceptance

Ordered by ROI and dependency. Each item is independently shippable.

### 1.1 C7 — Broad/essential-confounder quarantine  *(small, offline-verifiable)*
**Why:** raises trust in the existing readiness list immediately; the EDA explicitly warns that
broad chromatin/essential hits dominate high-DE rankings and must not read as narrow immune pathway hits.
**Design:**
- Build a combined "broad-effect" gene set from local resources: `metadata/gene_lists/core_essentials_hart.tsv`
  + CORUM complexes (`metadata/enrichment_database/corum_humanComplexes.txt`, extract chromatin/transcription
  complexes) + a curated chromatin/basal-transcription list (the EDA already names the offenders:
  `TADA2B, SGF29, SUPT20H, TADA1, CCNC, TAF13, KDM1A, NFRKB, MED12, CREBBP, LEO1, ELOB, DENR, TFAM, ARNT, ATP2A2`).
- In `readiness_engine.py`, add a `broad_effect` red flag (distinct from `essential_gene`) that caps the
  call at **watchlist** and adds `cd4_immune_red_flags += "broad_effect"`, with a reason string.
- Keep it a *separate, named* flag so users see "broad/pleiotropic effect" vs "core essential."
**Files:** `readiness_engine.py`, plus a small `sources/broad_effect_genes.txt` curation.
**Acceptance:** `MED12`, `CREBBP`, `KDM1A` no longer appear in `advance`; genuine immune genes (`PLCG1`,
`CD247`, `ITK`) still can; every quarantined row carries a `broad_effect` reason. Verify offline:
`python readiness_engine.py /tmp/gwt_cards.csv` and assert the set difference.

### 1.2 Module C — External-evidence layer  *(medium; uses live connectors)*
**Why:** fills the readiness domains currently stuck at `unknown` (tractability, genetics, clinical) and
gives each card trials + literature. This is the biggest jump in decision-grade value.
**Design (cache-first, connector-backed, offline batch — never in the request path):**
- New `src/3_DE_analysis/external_evidence_cache.py`:
  - `fetch_trials(gene, conditions)` → ClinicalTrials.gov (immune indications, phase/status/intervention).
  - `fetch_literature(gene, context="CD4 T cell")` → PubMed + bioRxiv top-N.
  - `fetch_open_targets(gene)` → GraphQL: tractability buckets, genetic association, safety.
  - `build_evidence_for_genes(genes, force=False)` → writes `sources/target_tool_cache/_evidence/<gene>.json`
    with `fetched_at` + `source_version`; respects a TTL; records `source_status: "unavailable"` when a
    connector is absent (headless-safe).
- API: `GET /api/evidence/{gene}` (cached snapshot; 404 → not fetched), `POST /api/evidence/build`
  `{dataset_id, top_n}` (batch the top-N genes of a dataset).
- Feed genetics/tractability snapshots into `readiness_engine` overlays so `human_genetic_support` and
  `tractability_score` graduate from `unknown` to real values, unlocking R3→R4 where warranted.
- Target Card page renders trials/literature/genetics sub-panels with `fetched_at` shown.
**Files:** `external_evidence_cache.py` (new), `target_card_api.py`, `readiness_engine.py`, dashboard.
**Acceptance:** for a shortlist (e.g. `IL2RA`, `JAK1`, `CTLA4`) snapshots contain ≥1 trial and ≥1
citation where they exist; readiness for those genes shows non-`unknown` tractability; connector-absent
runs degrade to `source_status: "unavailable"` without crashing.

### 1.3 Local translational overlays  *(small; offline)*
**Why:** cheap, local, no external calls — strengthens tractability before Module C lands.
**Design:** T1 druggable-class overlay (kinase/GPCR/enzyme/surface/cytokine-R/NR from
`metadata/gene_lists/*`) is already loaded by `readiness_engine.load_overlays`. Expose it as a card
column (`druggable_class`, `tractability_modality`) in `build_cards_frame` output and in the dashboard
Target Card so users see modality without opening readiness. T9 safety overlay: add
`clinvar_path_likelypath` + IUIS-IEI immune-effector membership as a `safety_note`.
**Files:** `build_target_cards.py`, dashboard. **Acceptance:** kinases show "small molecule", cytokine
receptors show "antibody/biologic"; genes in no class show "none".

### 1.4 Module D+ — Target Card dossier page  *(medium)*
**Why:** the deep per-`target × condition` view ties everything together with provenance.
**Design:** query-param deep view `?dataset_id=&target=&condition=` rendering the 10 sections from the
strategy doc (§6.1.3): identity + grades, GWT evidence, robustness/caveats, signed CD4 module scores,
benchmark axis, druggability, external evidence, readiness call + reasons, next experiment, provenance
footer. Reuse existing `_target_detail`, `_modules`, new `_readiness`, `_evidence`.
**Files:** `target_card_dashboard.py`. **Acceptance:** navigating to a known positive control (`CD3E`/Stim8hr)
and a `Stim48hr`-only hit renders both, with the batch caveat and readiness caps visible on the latter.

### 1.5 Signed CD4 module scoring upgrade (C8)  *(medium; offline)*
**Why:** current `/api/modules` is binary membership; upgrade to signed direction scoring so a card says
*how* a target moves a program.
**Design:** use each target's DE direction (`ontarget_effect_size` / up-down split) against the 20 signed
modules in `sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv`; emit per-module signed scores.
**Files:** `target_card_api.py` `_module_scores`, dashboard. **Acceptance:** Treg/Th1/Th2 modules score with
sign; positive controls land in expected modules.

### 1.6 Calibration harness  *(medium; offline)*
**Why:** trust is demonstrated, not asserted — recover known biology on demand.
**Design:** `src/3_DE_analysis/calibration.py`: positive-control recovery (TCR/proximal genes in top
deciles), known drug-axis recovery, rank stability after dropping off-target/low-cell/low-robustness rows,
donor/guide-holdout concordance (inputs exist under `donor_robustness/`, `guide_robustness/`). Emit a
`calibration_report` the dashboard renders. **Acceptance:** `CD3E/LAT/ZAP70/PLCG1` in top deciles; report
reproducible.

### 1.7 Disease translator (T8)  *(large)*
Indication picker (RA/IBD/MS/SLE/psoriasis/cancer-TME via ICD-10 normalization) → targets whose CD4
programs + genetics + trials align. Depends on Module C. New page + `GET /api/disease`.

### 1.8 Persistence + multi-user (governance)  *(large)*
Move from file-cache to Supabase/Postgres (datasets, imports, users, provenance, merge lineage) + auth +
per-user workspaces. Keep the file cache as an export target. Add server/proxy request-body limits.

### 1.9 Cell-level (h5ad) extension  *(large; needs S3 download)*
H1–H6: loaders, per-cell QC, Mixscape, SCEPTRE, pertpy/UCell, state-specific effects bridged back to the
card schema; U6 raw-cell manifest builder + on-demand jobs. Opt-in per analysis (1.6+ TiB, never auto-download).

### 1.10 v2 hypothesis generators (guarded)  *(optional)*
Signature-to-compound (LINCS/CMap), mechanism graph, perturbation prediction (**benchmark vs baselines
first; never feed readiness decisions**), combination explorer (research-only).

---

## 2. Sequencing (recommended)

```
Wave 1 (DONE):   foundation + C4 batch flag + readiness engine (R1–R3) + upload merge loop + dashboard
Wave 2 (next):   1.1 C7 quarantine  →  1.3 local overlays  →  1.6 calibration harness   [all offline, high trust]
Wave 3:          1.2 Module C external evidence  →  1.4 Target Card dossier  →  1.5 signed modules
Wave 4:          1.7 disease translator  →  1.8 persistence/multi-user
Wave 5:          1.9 cell-level (after h5ad)  →  1.10 v2 generators (guarded)
```

Rationale: Wave 2 is small, offline, and directly raises the credibility of what already ships (fixes the
`advance`-list confounders, exposes modality, proves biology recovery) before taking on the connector- and
data-heavy waves.

---

## 3. Global verification strategy

- **Offline unit checks** on the real CSVs for every engine change (batch flag distribution, readiness
  caps, calibration recovery) — no server needed.
- **TestClient integration** for every endpoint (the upload loop is already covered).
- **Dashboard smoke** via a documented local launch (`uvicorn target_card_api:app` + `streamlit run
  target_card_dashboard.py`) driving a positive control and a confounded hit.
- **Provenance assertion**: every produced card set carries `origin`, `data_version`, `engine_version`,
  and (uploads) merge lineage.

---

## 4. Guardrails carried into every wave

- `unknown` ≠ `0`: unbuilt evidence domains stay explicit `unknown`.
- Red-flag overrides cap calls regardless of statistics (essential, broad-effect, off-target, uncertain
  direction, batch confound).
- User-uploaded datasets stay namespaced (`usr_`) and labelled; never blended into the GWT reference set.
- CRISPRi ≠ pharmacology; in-vitro CD4 context caveats stay visible on the card.
- External APIs are cached and version-stamped; connector-absent runs degrade gracefully.
