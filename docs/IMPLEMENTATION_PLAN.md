# Implementation Plan — CD4 Perturb-seq Target-Discovery Toolkit

**Status:** living plan · **Last updated:** 2026-07-07 · **Branch:** `claude/drug-discovery-tool-plan-258jof`
(PR #1 merged wave 1; this branch was rebuilt from `main` post-merge for wave 2 per repo workflow rules)

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

### Wave 2 — landed and verified (this update)

| Piece | Module | State | Evidence of verification |
|---|---|---|---|
| Broad-effect/chromatin confounder quarantine | C7 (§1.1) | **done** | `sources/broad_effect_genes.txt` (239 genes: EDA-named offenders ∪ CORUM chromatin/transcription complexes); `MED12/CREBBP/KDM1A/SGF29` no longer reach `advance` (319→302 unique targets), `PLCG1/CD247/ITK` unaffected, 513 rows carry the reason |
| Local druggability/safety overlay columns | T1/T9 (§1.3) | **done** | `druggable_class`, `tractability_modality`, `safety_note` columns on every card; `DRUGGABLE_CLASS_MODALITY` is a single source of truth shared by the builder and the readiness engine; verified via TestClient on `/api/targets/{id}/{target}` |
| Calibration harness | §1.6 | **done** | `calibration.py` + `GET /api/calibration/{id}` + Overview-tab section; on the real GWT cards, Stim8hr recovers **all 8** TCR/proximal positive controls in the top decile; naive top-50 by DE breadth only 13/50-overlaps the strict-filtered top-50 (Spearman r=0.943) — an honest finding that the naive ranking alone is not robustness-safe |

Wave 2 closed the scientific gap noted below (superseded, kept for history): the `advance` set
used to contain broad chromatin/essential-like genes (`MED12`, `CREBBP`, `KDM1A`, `ELOB`) because
`core_essentials_hart.tsv` (283 genes) alone did not cover them.

### Wave 3 — landed and verified (this update)

| Piece | Module | State | Evidence of verification |
|---|---|---|---|
| External-evidence layer | §1.2 | **done** | `external_evidence_cache.py` + `/api/evidence/{gene}` + `/api/evidence/build`; readiness `clinical_feasibility_score` upgrades 3→5 when a real Phase 3/4 trial exists |
| Target Card provenance footer | §1.4 (partial) | **done** | Every dataset stamped with `engine_version`, `built_at`, `data_version`; rendered on the Target Explorer detail |
| Signed CD4 module scoring | §1.5 | **descoped — see below** | Confirmed `DE_stats.suppl_table.csv` has no per-gene downstream direction data to score against |

**Module C (§1.2) implementation notes.** `external_evidence_cache.py` hits the public
ClinicalTrials.gov API v2, NCBI PubMed E-utilities, and the Open Targets Platform GraphQL API
directly via `requests` — not through session-scoped MCP connectors, since the module runs inside
the standalone FastAPI backend. In this sandboxed verification environment, the outbound proxy's
own status endpoint confirms a policy denial (`connect_rejected`/403) for all three domains, so the
graceful-degradation path (`source_status: "unavailable"`, no crash) is what was actually exercised
end-to-end here — this is the correct thing to verify, since a locked-down deployment is exactly the
scenario the design anticipates. Separately, **9 genes were seeded with real evidence** (the
calibration harness's 8 TCR/proximal positive controls plus 4 clinically-precedented targets) by using
the live ClinicalTrials.gov/PubMed connectors available in *this* agent session and hand-curating for
topical relevance (e.g. teplizumab/CD3 in T1D, abatacept/CTLA4-CD28 in RA, tofacitinib/JAK3 in RA) —
these ship in `sources/target_tool_cache/_evidence/*.json` so the dashboard has real evidence to show
immediately, independent of whatever network policy a given deployment has. Open Targets could not be
seeded this way (no GraphQL-capable MCP tool was available) and is honestly marked `unavailable` in
every seeded snapshot.

**§1.5 descope — honest finding, not a shortcut.** The plan's original design said "use each target's
DE direction (`ontarget_effect_size` / up-down split) against the 20 signed modules." Checking
`DE_stats.suppl_table.csv` directly: it stores only **counts** (`n_up_genes`, `n_down_genes`), not
which specific downstream genes were up- or down-regulated. Without per-gene downstream DE records
(not present in any `metadata/suppl_tables/*` file), a genuinely signed *pathway-specific* direction
score cannot be computed without fabricating a mapping. Rather than ship a score that looks
mechanistic but isn't backed by the data, this item is descoped until per-gene downstream DE tables
are available (would require the h5ad extension, §1.9, or a new pseudobulk export). The existing
binary-membership module score (`/api/modules`) is left as-is.

---

## 1. Remaining work — specs, sequencing, acceptance

Ordered by ROI and dependency. Each item is independently shippable.

### 1.1 C7 — Broad/essential-confounder quarantine  *(small, offline-verifiable)* — **DONE**
**Why:** raises trust in the existing readiness list immediately; the EDA explicitly warns that
broad chromatin/essential hits dominate high-DE rankings and must not read as narrow immune pathway hits.
**Shipped:** `sources/broad_effect_genes.txt` (239 genes: EDA-named offenders ∪ CORUM chromatin/
transcription complexes matched by keyword); `readiness_engine.py` `broad_effect` red flag (distinct
from `essential_gene`) caps the call at watchlist and surfaces in `cd4_immune_red_flags` /
`next_validation_step`. Verified: `MED12/CREBBP/KDM1A/SGF29` no longer reach `advance`; `PLCG1/CD247/ITK`
unaffected; 513 rows carry the reason; deterministic.

### 1.2 Module C — External-evidence layer  *(medium; uses live connectors)* — **DONE**
**Why:** fills the readiness domains currently stuck at `unknown` (tractability, genetics, clinical) and
gives each card trials + literature. This is the biggest jump in decision-grade value.
**Shipped:** `external_evidence_cache.py` fetches ClinicalTrials.gov API v2, NCBI PubMed E-utilities,
and Open Targets GraphQL directly (not via MCP — the module runs standalone inside the FastAPI
backend); every fetcher degrades to `source_status: "unavailable"` on any network failure instead of
raising. `GET /api/evidence/{gene}` (404 if not fetched) and `POST /api/evidence/build`
`{dataset_id|genes, top_n, force}`. `readiness_engine.compute_readiness(..., evidence_dir=...)` upgrades
`clinical_feasibility_score` (3→5 with a real Phase 3/4 trial) and `human_genetic_support` when a
snapshot was actually fetched, leaving genes with no snapshot unaffected. Dashboard Target Explorer
detail renders trials/literature/Open-Targets sub-panels with `fetched_at` shown.
**Verified:** graceful degradation confirmed in this sandboxed environment (outbound proxy policy
blocks all three domains — confirmed via the proxy's own status endpoint); 9 genes seeded with real
evidence via this session's live MCP connectors (see Wave 3 notes above); TestClient covers
GET/POST endpoints and the readiness upgrade (`CD28`/`IL2RA`/`CTLA4` clinical_feasibility 3→5).

### 1.3 Local translational overlays  *(small; offline)* — **DONE**
**Why:** cheap, local, no external calls — strengthens tractability before Module C lands.
**Shipped:** every card now carries `druggable_class`, `tractability_modality` (from
`metadata/gene_lists/*` druggable-class files; `DRUGGABLE_CLASS_MODALITY` lives once in
`build_target_cards.py` and is imported by `readiness_engine.py` so the two never drift), and
`safety_note` (ClinVar pathogenic/likely-pathogenic ∪ `metadata/immune_effector_genes.csv` category
membership — substituted for the originally planned IUIS-IEI table, which is disease-level, not a
clean gene list, so using it would have meant fabricating a parser over messy free-text fields).
Verified: `ZAP70`→kinases/small molecule, `IL2RA`→catalytic_receptors/small molecule-biologic,
`CTLA4`→no druggable-class match but carries ClinVar + immune-effector notes; 4,592/33,983 rows matched.

### 1.4 Module D+ — Target Card dossier  *(medium)* — **PARTIALLY DONE**
**Why:** the deep per-`target × condition` view ties everything together with provenance.
**Shipped so far:** rather than a separate query-param page (which would duplicate a lot of the
existing Target Explorer detail block), the 10 dossier sections were folded directly into that
existing view as each module landed: GWT evidence + robustness (existing), druggability/safety
metrics (§1.3), readiness call + reasons + next step (wave 1), external evidence panel (§1.2), and a
**provenance footer** (`dataset_id`, `origin`, `engine_version`, `built_at`, `data_version`, and —
for user uploads — `import_id`/`source_name`). `ENGINE_VERSION` is a single constant in
`target_card_api.py`, auto-stamped onto every dataset's `metadata.json` by `_persist_metadata`, bump
it whenever `build_target_cards.py`/`readiness_engine.py`/`calibration.py`/`external_evidence_cache.py`
change scoring behavior. **Remaining:** signed CD4 module scores (blocked, see §1.5) and a real
`crossguide_vs_crossdonor_scatter`/`target_card_waterfall` chart (still just a raw table + graphviz
node graph). **Acceptance (met so far):** provenance footer verified via TestClient
(`engine_version=1.3.0`, real `built_at`/`data_version` on both GWT and user-merged datasets).

### 1.5 Signed CD4 module scoring upgrade (C8)  *(medium; offline)* — **DESCOPED (data gap, see Wave 3 notes above)*
**Why:** current `/api/modules` is binary membership; the original idea was to upgrade to signed
direction scoring so a card says *how* a target moves a program.
**Finding:** `DE_stats.suppl_table.csv` stores only `n_up_genes`/`n_down_genes` **counts**, not which
specific downstream genes moved which direction — there is no per-gene downstream DE table in
`metadata/suppl_tables/*` to score module-specific direction against. Computing a "signed" score from
counts alone would be a fabricated signal presented as mechanistic. Descoped until per-gene downstream
DE becomes available (most likely via the h5ad extension, §1.9, or a new pseudobulk export). The
existing binary-membership `/api/modules` endpoint is unchanged.

### 1.6 Calibration harness  *(medium; offline)* — **DONE**
**Why:** trust is demonstrated, not asserted — recover known biology on demand.
**Shipped:** `src/3_DE_analysis/calibration.py` computes positive-control recovery (8 TCR/proximal genes,
per-condition decile rank), known drug-axis enrichment (`clinical_axis` assignment rate in grade≥3 rows
vs overall, plus which of the 6 named axes are actually recovered), and rank stability (Spearman
correlation + top-50 churn between the naive DE-breadth ranking and the same ranking after the EDA's
strict off-target/low-cell/low-robustness filter) — built directly on `target_cards.csv`'s existing
`crossdonor_correlation_mean`/`crossguide_correlation` columns rather than recomputing pairwise donor/guide
holdout correlations from the raw per-guide/per-donor result files, since those are already summarized
into the card. `GET /api/calibration/{dataset_id}` (cached alongside `readiness.csv`) + an Overview-tab
section. **Verified:** Stim8hr recovers all 8 positive controls in the top decile (matching the EDA's own
finding that Stim8hr has the strongest acute-activation signal); 75% land in top-2-deciles overall; 2/6
known drug axes recovered among grade≥3 rows; naive top-50 only 13/50-overlaps the strict-filtered top-50
(Spearman r=0.943) — a real, honest finding that the naive ranking alone is not robustness-safe.

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
Wave 2 (DONE):   1.1 C7 quarantine  →  1.3 local overlays  →  1.6 calibration harness   [all offline, high trust]
Wave 3 (DONE):   1.2 Module C external evidence  →  1.4 provenance footer   [1.5 descoped, see §1.5]
Wave 4 (next):   1.7 disease translator  →  1.8 persistence/multi-user
Wave 5:          1.9 cell-level (after h5ad)  →  1.10 v2 generators (guarded)
```

Rationale: Wave 2 was small, offline, and directly raised the credibility of what already ships (fixed the
`advance`-list confounders, exposed modality, proved biology recovery) before taking on the connector- and
data-heavy Wave 3. Wave 3 depended on live external connectors (ClinicalTrials.gov, PubMed, Open Targets)
and was the biggest remaining jump in decision-grade value; it's done, modulo Open Targets genetics (no
GraphQL-capable fetch tool was available this session — the automated fetcher is wired and ready for a
deployment with direct network access). Wave 4 is the next largest jump: a disease/indication picker
(depends on Module C, now available) and moving off the file-cache to a real multi-user backend.

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
