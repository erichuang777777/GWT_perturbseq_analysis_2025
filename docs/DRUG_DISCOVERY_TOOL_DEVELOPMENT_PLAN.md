# GWT CD4 Perturb-seq Target-Discovery Toolkit — Development Plan

**Status:** planning document · **Owner:** research/tooling team · **Last updated:** 2026-07-07
**Scope:** a research-use tool + dashboard + researcher upload system for discovering candidate drug targets from the genome-scale CD4+ T-cell Perturb-seq data in this repository and from data researchers bring themselves.

---

## 0. How to read this document

This is a *detailed* plan, written to be actionable. It is organized so you can start at the top for the strategic frame, jump to §5 for the full feature catalog, or jump to §11 for the concrete milestone backlog. Every claim about the data is grounded in files already in this repo (paths are given). Every proposed feature carries an evidence basis, an effort estimate, and its dependencies, so nothing here is aspirational hand-waving.

**Table of contents**

1. Product framing — what this tool is, and what it must never claim to be
2. Current state — what already exists in this repo (with evidence)
3. The concrete data assets we can build on (real numbers)
4. Target architecture (layered)
5. Full feature catalog (dashboard, analysis, upload, external evidence, cell-level)
6. Dashboard design in detail
7. Researcher data upload / bring-your-own-data — full design and current gaps
8. Scoring & readiness methodology
9. Validation, calibration, and trust
10. Data governance, provenance, security, deployment
11. Milestone roadmap and prioritized backlog
12. Risks, scientific limitations, and honesty guardrails
13. Insights & recommendations (opinionated)

---

## 1. Product framing

### 1.1 One-sentence promise

> A versioned, evidence-decomposed CD4+ T-cell Perturb-seq **target-prioritization toolkit** that turns scattered differential-expression and guide-QC tables into transparent, source-stamped `target × condition` hypotheses, ranks them, overlays external druggability/genetics/clinical evidence, and produces a validation plan — plus a staging-first upload system so researchers can score their own datasets with the same rules.

### 1.2 What it is

- A **decision-support** layer over perturbation summaries: target cards, ranked tables, QC badges, condition-specific interpretation, benchmark axes, readiness calls, and next-experiment recommendations.
- A **transparent** system: every score decomposes into named evidence components with provenance and version stamps. A numeric score with no provenance is worse than no score.
- A **bring-your-own-data** platform: researchers upload their own DE/guide/evidence tables (or register large raw-cell files) and get the same cards, gated by schema validation and context checks.

### 1.3 What it must NOT claim (honesty guardrails)

The prior research corpus (`sources/topic11_breakthrough_directions_toolkit_opportunities.md`) is explicit, and this plan adopts it as policy. The tool must **not** promise:

- drug discovery / validated targets / repurposed drugs
- clinical readiness, patient stratification, or efficacy/safety prediction
- that CRISPRi knockdown equals pharmacologic inhibition, agonism, degradation, antibody blockade, ASO/siRNA, or cell therapy
- virtual-cell prediction as a basis for decisions

These are not legal disclaimers to bury; they are **product invariants** enforced in the UI (every card carries caveats) and in the scoring (see §8, "score caps" and "red-flag overrides").

---

## 2. Current state — what already exists

This is not a greenfield build. A working MVP and a deep research corpus already exist. The plan below **extends** them rather than restarting.

### 2.1 Already built (verified in-repo)

| Component | File | What it does | Maturity |
|---|---|---|---|
| Card builder | `src/3_DE_analysis/build_target_cards.py` | Joins DE stats + guide KD + library metadata into a 30-column target-card CSV; assigns `statistical_evidence_grade` 1–4, `pathway_axis`, `clinical_axis`, `condition_specificity_score`, `score_cap_reason`, nearest-success-drug mapping | Working, CSV-first |
| API | `src/3_DE_analysis/target_card_api.py` | FastAPI service: build job, list/filter targets, per-target detail, summary, options, module scores, exports (CSV/JSON), reports (HTML/MD/JSON), import staging endpoints | Working (local) |
| Dashboard | `frontend/dashboard/target_card_dashboard.py` | Streamlit app, 5 tabs: Overview, Target Explorer, Pathway+Clinical, Imports, Export; evidence graph per target. Moved into `frontend/` as an independent, HTTP-only frontend package (see `frontend/README.md`) | Working (local) |
| Upload/import | `src/3_DE_analysis/import_manager.py` | Staging-first upload: source-type inference, schema validation, context-match scoring, preview, explicit approval gate, provenance metadata | Shipped as "M3.5" |
| Report generator | `src/3_DE_analysis/generate_target_report.py` | Builds report payloads and HTML/MD reports | Working |
| Research corpus | `sources/topic01..15_*` | Prior scoping: toolkit architecture, EDA, drug benchmarks, readiness schema, upstream/downstream modules, limitations audit | Complete |

### 2.2 Known gaps (from `sources/release_notes_m3_5_upload_import.md` and code review)

These are the **actual next-work items**, not hypotheticals:

1. **Downstream merge is not implemented** — uploads can be staged and approved but are never merged into target cards. The upload loop currently dead-ends at "approved."
2. **Column-mapping wizard is not implemented** — non-standard uploads are blocked with no interactive remedy.
3. **External-evidence layer is designed but not wired** — Open Targets / ChEMBL / DepMap / GWAS adapters are named in `topic06` but not built.
4. **Readiness engine (R0–R5) is not wired** — cards carry `statistical_evidence_grade` 1–4 (a *statistical* grade), but the 12-domain readiness schema in `sources/topic04_drug_readiness_checklist.csv` (biology causality, tractability, safety window, biomarker, translation, clinical feasibility → R0–R5 → advance/validate/watchlist/deprioritize) is **not** computed.
5. **Cell-level (h5ad) analysis is not present** — no per-cell QC, responder fractions, Mixscape/SCEPTRE/pertpy, or state-specific effects. The 1.6+ TiB cell-level data lives on S3, not locally.
6. **No persistence / multi-user backend** — datasets are file-caches under `sources/target_tool_cache/`; there is no database, auth, or shared project space.
7. **Batch-sensitivity flag is a stub** — `batch_sensitivity_flag` is hard-coded to `"unknown"` in the builder, even though the EDA already knows `Stim48hr` is confounded with run `CD4i_R2`.

---

## 3. Concrete data assets (real numbers)

Everything below is measured from files in this repo (`sources/topic09_eda_outputs/eda_summary.json`, `sources/topic09_eda_report.md`). This is the "solid evidence and concrete raw data" the tool is built on.

### 3.1 Experimental design

- Assay: genome-scale **CRISPRi Perturb-seq** in **primary human CD4+ T cells** (manuscript: bioRxiv `10.64898/2025.12.23.696273v1`).
- **4 donors × 3 culture conditions**: `Rest`, `Stim8hr`, `Stim48hr`.
- Run structure is **not balanced**: `Rest` and `Stim8hr` span runs `CD4i_R1` + `CD4i_R2`; **`Stim48hr` is entirely in `CD4i_R2`** → any Stim48hr-only claim needs a batch caveat. (This is exactly what the stubbed `batch_sensitivity_flag` should encode — see §8.4.)

### 3.2 Table inventory

| Table | Rows | Content | Path |
|---|---:|---|---|
| Sample metadata | 12 | donor, condition, run, library, demographics | `metadata/suppl_tables/sample_metadata.suppl_table.csv` |
| DE stats | **33,983** | `target × condition` DE summaries + robustness fields | `metadata/suppl_tables/DE_stats.suppl_table.csv` |
| Guide KD efficiency | **73,765** | guide-level knockdown stats across conditions | `metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv` |
| sgRNA library metadata | **26,504** | guide design, off-target / nearby-gene annotations | `metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv` |

- **11,526** unique DE target genes; **12,654** unique sgRNA targets.
- DE key columns: `n_cells_target`, `n_up_genes`, `n_down_genes`, `n_total_de_genes`, `ontarget_effect_size`, `ontarget_significant`, `offtarget_flag`, `n_downstream`, `crossdonor_correlation_mean/min`, `crossguide_correlation`.

### 3.3 What the data supports today (candidate funnel)

From `sources/topic09_eda_report.md`:

- DE effects are **highly long-tailed**: median DE genes per target ≈ 2; mean 53–69; ~14–17% of rows show no effect; ~22–23% have >10 DE genes.
- **4,182** high-DE rows at `n_total_de_genes ≥ 50` (Rest 1,368 / Stim8hr 1,433 / Stim48hr 1,381).
- Applying the strict actionable filter — `n_total_de_genes ≥ 50 ∧ ontarget_significant ∧ ¬offtarget_flag ∧ n_cells_target ≥ 200 ∧ crossdonor_correlation_mean ≥ 0.2 ∧ crossguide_correlation ≥ 0.2` — leaves **~1,208 high-confidence `target × condition` rows**.
- **153** robust high-DE targets appear across **all three** conditions (pan-condition prioritization pool).
- Positive-control biology recovered strongly in Stim8hr: `PLCG1, CD247, ITK, CD3E, LAT, ZAP70, LCP2, VAV1, BCL10, PTPRC, LCK`.
- Broad/chromatin/essential-like hits to quarantine from "narrow immune pathway" claims: `TADA2B, SGF29, SUPT20H, TADA1, CCNC, TAF13, KDM1A, NFRKB, MED12, CREBBP, LEO1, ELOB, DENR, TFAM, ARNT, ATP2A2`.

**Interpretation for product:** the honest addressable candidate pool is ~1.2k rows, not 34k. The tool's job is to make that funnel visible and defensible, separating (a) TCR/proximal-activation biology, (b) pan-condition robust hits, (c) condition-specific hits, and (d) broad/essential confounders.

### 3.4 Reference/curation assets already present

- `sources/topic05_successful_drug_benchmarks.csv` — clinical anchors (e.g., teplizumab anti-CD3, ibalizumab anti-CD4) with directionality warnings and safety notes; drives `clinical_axis` / `nearest_success_drug`.
- `sources/topic04_drug_readiness_checklist.csv` — 12-domain readiness schema → R0–R5 → advance/validate/watchlist/deprioritize (not yet wired; see §8.5).
- `sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv` — 20 signed CD4 modules (TCR core, proximal signaling, costimulation, checkpoint, Th1/Th2/Th17/Treg/Tfh, cytokine, exhaustion, etc.) for module scoring.
- `metadata/gene_lists/*` — local druggable-class lists: `kinases`, `gpcr_union`, `catalytic_receptors`, `enzymes`, `ion_channels`, `transporters`, `nuclear_receptors`, `cytokine_receptors`, `core_essentials_hart`, `clinvar_path_likelypath`, `gwascatalog`, plus `IUIS-IEI` immune-effector and `immune_effector_genes.csv`.

### 3.5 Live external connectors available in this environment (a key insight)

The prior research (`topic06`) said the external-evidence layer was needed but not built. **This environment already exposes live MCP connectors that map directly onto that layer** — we should use them instead of hand-rolling HTTP clients:

- **ClinicalTrials.gov** — trials by condition/intervention/sponsor, endpoints → powers `clinical_feasibility_score`, `nearest_success_drug`, competitor landscape.
- **PubMed** + **bioRxiv** — literature evidence, mechanism/limitation mining → `biology_causality_score`, evidence citations on each card.
- **ICD-10** — disease-context normalization for the disease translator.
- **Hugging Face** — reference perturbation datasets/models (scPerturb, foundation models) for the v2 prediction/benchmark layer.
- **Supabase** — a Postgres backend + auth for the multi-user / persistence gap (§10).

This turns several "later, external, hard" items into "wire an adapter to a connector we already have."

---

## 4. Target architecture (layered)

Adopt the layered design from `sources/topic06_toolkit_architecture_summary.md`, made concrete against what exists:

```
┌──────────────────────────────────────────────────────────────────────┐
│  PRESENTATION                                                          │
│  Streamlit dashboard (exists) → migrate/extend to multi-page          │
│  Static HTML/MD/JSON reports (exists) · shareable target cards         │
├──────────────────────────────────────────────────────────────────────┤
│  SERVICE / API  (FastAPI, exists)                                     │
│  /run · /targets · /summary · /modules · /imports · /exports          │
│  + NEW: /readiness · /evidence/{gene} · /disease · /validate-plan     │
├──────────────────────────────────────────────────────────────────────┤
│  ENGINES                                                               │
│  card_builder (exists) │ readiness_engine (NEW) │ module_scoring       │
│  external_evidence_cache (NEW) │ disease_translator (NEW)              │
│  signature_matcher (NEW, v2) │ cell_level_engine (NEW, needs h5ad)     │
├──────────────────────────────────────────────────────────────────────┤
│  DATA CONTRACTS (stable schemas, versioned)                           │
│  target · target_condition_effect · guide_evidence · signature ·      │
│  program_score · external_evidence · benchmark_axis · readiness_score │
├──────────────────────────────────────────────────────────────────────┤
│  STORAGE                                                               │
│  now: file cache (sources/target_tool_cache/)                         │
│  next: Supabase/Postgres (datasets, imports, users, provenance)       │
│  raw: S3 cell-level h5ad (1.6+ TiB, on-demand)                        │
└──────────────────────────────────────────────────────────────────────┘
```

**Design rules**
- CSV-first stays the backbone; h5ad is an *extension*, never a prerequisite for the core loop.
- Every engine output is source-stamped and version-stamped. Provenance is a column, not an afterthought.
- Contracts are frozen and versioned so uploaded data and internal data flow through the same pipes.

---

## 5. Full feature catalog

Organized by module, prioritized. Legend — **Value**: research impact; **Effort**: S/M/L/XL; **Data**: what it needs; **Status**: exists / gap / new.

### 5.1 Core target-evidence modules

| # | Feature | Value | Effort | Data | Status |
|---|---|---|---|---|---|
| C1 | Target-condition ranking table (sortable/filterable) | very high | — | DE + guide CSVs | **exists** |
| C2 | Per-target card with evidence decomposition | very high | — | as C1 | **exists** |
| C3 | QC/confidence badges (off-target, low-cell, donor/guide robustness) | high | S | robustness fields | partial → **finish** |
| C4 | Batch-sensitivity flag (Stim48hr↔R2 confound) | high | S | sample metadata + DE | **gap (stub)** |
| C5 | Condition-specific hypothesis engine (Rest vs Stim8hr vs Stim48hr logic) | high | M | DE per condition | partial |
| C6 | Pan-condition vs condition-specific separation (the 153 robust targets) | high | S | DE cross-condition | new |
| C7 | Broad/essential-confounder quarantine (essential-gene overlay) | high | S | `core_essentials_hart.tsv` | new |
| C8 | Signed CD4 module scoring (20 seed modules) | high | M | `topic15` seed modules | partial (overlap only) |
| C9 | Positive-control recovery panel (TCR/proximal genes) | high | S | DE + control list | new |
| C10 | QC funnel visualization (34k → 4.2k → 1.2k) | medium | S | DE | new |

### 5.2 Translational / external-evidence modules

| # | Feature | Value | Effort | Data | Status |
|---|---|---|---|---|---|
| T1 | Druggable-class overlay (kinase, GPCR, enzyme, surface, cytokine-R, NR…) | high | S | `metadata/gene_lists/*` | new (local, easy) |
| T2 | Open Targets tractability + genetics overlay | high | M | Open Targets API | new |
| T3 | ChEMBL / DGIdb / DrugCentral / Pharos drug-precedent | high | M | external APIs | new |
| T4 | DepMap essentiality / selectivity overlay | medium | M | DepMap | new |
| T5 | Clinical-trial landscape (ClinicalTrials.gov connector) | high | S–M | **CT.gov MCP (live)** | new (connector exists) |
| T6 | Literature evidence + citations (PubMed / bioRxiv) | high | S–M | **PubMed/bioRxiv MCP (live)** | new (connector exists) |
| T7 | Successful-drug benchmark axes + directionality warnings | high | — | `topic05` CSV | **exists** |
| T8 | Disease/trait translator (RA, IBD, MS, SLE, psoriasis, cancer/TME) | medium | L | GWAS/eQTL + disease atlases + ICD-10 | new |
| T9 | Safety-flag panel (essentiality, cytokine release, Treg destabilization, global immunosuppression) | high | M | local lists + signatures | partial |

### 5.3 Readiness & decision modules

| # | Feature | Value | Effort | Data | Status |
|---|---|---|---|---|---|
| R1 | 12-domain readiness scoring (biology, tractability, safety, biomarker, translation, clinical) | very high | L | `topic04` schema + overlays | **gap** |
| R2 | R0–R5 stage-gate engine with red-flag overrides | very high | M | R1 outputs | **gap** |
| R3 | `advance / validate / watchlist / deprioritize` call with reasons | very high | S | R2 | **gap** |
| R4 | Wet-lab validation planner (per-card next experiment) | high | M | card + modality | new |
| R5 | Rank-stability / sensitivity analysis (drop off-target/low-cell/low-robustness) | high | M | DE | new |

### 5.4 Upload / bring-your-own-data modules

| # | Feature | Value | Effort | Data | Status |
|---|---|---|---|---|---|
| U1 | Staging upload (small tables) + local large-file registration | high | — | — | **exists** |
| U2 | Schema validation + context-match scoring + approval gate | high | — | — | **exists** |
| U3 | **Interactive column-mapping wizard** | high | M | — | **gap** |
| U4 | **Merge approved import → target cards** (the dead-end fix) | very high | M | — | **gap** |
| U5 | Uploaded-dataset scoring with the same rules (BYO DE tables → cards) | very high | M | U4 | new |
| U6 | Raw-cell manifest builder + on-demand cell-level processing | medium | L | h5ad + manifest | new |
| U7 | Dataset diff / compare (my data vs GWT reference) | high | M | two card sets | new |
| U8 | Provenance & versioning of every uploaded source | high | S | metadata (partly exists) | partial |

### 5.5 Cell-level (h5ad) extension — after data download

| # | Feature | Value | Effort | Data | Status |
|---|---|---|---|---|---|
| H1 | AnnData/Scanpy loaders (DE_stats.h5ad, pseudobulk, cell-level) | high | M | S3 h5ad | new |
| H2 | Per-cell QC, guide-assignment diagnostics, doublet/ambient checks | high | M | cell h5ad | new |
| H3 | Mixscape/Mixscale — responder vs escaped cells | high | L | cell h5ad | new |
| H4 | SCEPTRE — calibrated perturbation-gene associations | high | L | cell h5ad | new |
| H5 | pertpy-native workflows; UCell/AUCell per-cell program scores | medium | M | cell h5ad | new |
| H6 | State-specific / subset effects bridged back to the card schema | high | L | cell h5ad | new |

### 5.6 v2 hypothesis-generation modules (guarded)

| # | Feature | Value | Effort | Notes |
|---|---|---|---|---|
| V1 | Signature-to-compound matcher (LINCS/CMap/SigCom) | medium | L | context-mismatch risk; label clearly as hypothesis |
| V2 | Mechanism graph (target → downstream → pathway → phenotype) | medium | L | needs signed DE vectors |
| V3 | Perturbation-effect prediction (GEARS/CPA/scGPT/Geneformer) | low–med | XL | **benchmark vs simple baselines first**; do not use for readiness decisions (2025 benchmarks: foundation models don't consistently beat baselines) |
| V4 | Combination/rescue explorer | low | L | research-only; never an MVP promise |

---

## 6. Dashboard design in detail

The current Streamlit app has 5 tabs. Target end-state is a multi-page workspace. Below is the proposed information architecture; existing tabs are marked.

### 6.1 Pages

1. **Home / Overview** *(exists)* — headline metrics (rows, targets, conditions, grade 3–4, replicate-pass, watchlist), evidence-grade distribution, condition/pathway bars, top candidates, watchlist. **Add:** the QC funnel (34k→4.2k→1.2k), pan-condition vs condition-specific split, positive-control recovery panel.

2. **Target Explorer** *(exists)* — filterable table (grade, condition, pathway/clinical axis, cap reason, replicate-pass, off-target, min DE genes) + per-target detail with evidence graph. **Add:** druggable-class chips (T1), external-evidence panel (T2–T6) rendered inline, per-condition bar of DE breadth, guide-level KD strip.

3. **Target Card** (new, deep view per `target × condition`) — the "target dossier." Sections mirror `topic11`:
   - identity (target, condition) + statistical grade + readiness call
   - GWT evidence (DE breadth, effect size, on-target KD, cell count)
   - robustness (donor/guide correlation, off-target, batch caveat)
   - CD4 interpretation (module scores: activation, Treg, Th1/Th2/Th17/Tfh, exhaustion, cytokine)
   - benchmark axis (CD3/TCR, CD28, JAK/STAT, IL-2/IL-2R, NFAT, S1P, IL-17/IL-23, TNF)
   - druggability & modality
   - safety flags
   - external evidence (Open Targets, genetics, ChEMBL, DepMap, trials, literature)
   - readiness call with reasons + next validation experiment
   - **provenance footer**: data version, engine version, source stamps, run timestamp

4. **Compare / Conditions** *(partly in Pathway+Clinical tab)* — condition-specificity heatmap, cross-guide vs cross-donor scatter, clinical-axis radar, condition-specific hypothesis labels.

5. **Disease Translator** (new) — pick an indication (RA/IBD/MS/SLE/psoriasis/cancer-TME via ICD-10 normalization) → targets whose CD4 programs + genetics + trials align.

6. **Upload / My Data** *(exists as Imports)* — staging table, schema/context panels, preview, approval; **add** column-mapping wizard (U3), merge-to-cards action (U4), and a "score my dataset" button (U5).

7. **Validation Planner** (new) — for a shortlist, generate per-target next experiments (independent sgRNA/CRISPRa/siRNA, protein readout, cytokine/proliferation/apoptosis assays, Treg/Th17 functional assays, tool compound/antibody where a modality exists).

8. **Export / Reports** *(exists)* — CSV / JSON / HTML / MD; **add** per-card PDF/HTML dossier and a shareable read-only link.

### 6.2 Key visualizations (from `topic14` spec §F)

- `QC_funnel` — raw target → ontology → high-confidence flow
- `crossguide_vs_crossdonor_scatter` — robustness quadrants
- `condition_specificity_heatmap` — target × condition
- `control_null_overlay` — non-targeting/negative-control null band on effect distributions
- `clinical_axis_radar` — success/warning axes per target
- `target_card_waterfall` — 5–8 evidence components per card, showing what raises/caps the score

**Design/consistency note:** when these are built, follow the repo's own `metadata/figure_palettes.yaml` for color consistency with the manuscript, and load the `dataviz` skill before writing any chart code so light/dark, categorical palettes, and accessibility are handled once, system-wide.

### 6.3 Interaction principles

- Every score is clickable → expands into its components (no black boxes).
- Every card shows caveats *before* conclusions.
- Filters are URL-encodable so a view is shareable.
- "Why is this capped?" is always answerable from `score_cap_reason`.

---

## 7. Researcher upload / bring-your-own-data — full design

This is a first-class requirement ("also for researcher to upload their own data"). The staging foundation (`import_manager.py`) is solid; the loop is incomplete. Here is the full intended flow and the three gaps to close.

### 7.1 Current flow (works today)

```
upload small table (≤25 MB)  ─┐
register local large file    ─┴─▶ infer source_type ─▶ schema validation ─▶
context-match score (CD4/human/perturb/single-cell keywords) ─▶ preview (25 rows) ─▶
merge_status (staged / blocked / needs-classification / low-context / manifest-required) ─▶
explicit approval gate ─▶ approved_for_downstream_use
```

Source types: `target_evidence`, `guide_evidence`, `external_evidence`, `metadata_manifest`, `raw_cell_data`. Routes and approval rules are enforced (`sources/release_notes_m3_5_upload_import.md`). Security: whitelisted types, extension checks, 25 MB base64 cap, allowed-root restriction for local paths.

### 7.2 Gap U3 — interactive column-mapping wizard

**Problem:** an upload with columns like `gene`, `padj`, `log2fc` is auto-aliased, but anything outside the alias table is blocked with no remedy.
**Design:**
- After preview, show detected columns next to the canonical contract (`target`, `condition`, `effect_size`, `logfc`, `p_value`, `fdr`, `n_cells`, `n_guides`, …).
- Let the user map each unrecognized column to a canonical field (or "ignore").
- Persist the mapping in the import metadata (provenance), re-run validation against the mapped view, and unblock if it now passes.
- Offer "save mapping as template" for repeated dataset formats.

### 7.3 Gap U4 — merge approved import → target cards (the dead-end fix)

**Problem:** approval currently does nothing downstream.
**Design:**
- On merge, run the *same* `build_target_cards` logic over the uploaded DE/guide tables (with the user's column mapping), producing a card set tagged with the source dataset id.
- Keep uploaded-derived cards **namespaced and clearly labeled** as user-provided, never silently blended with the GWT reference set.
- Record a merge record (who, when, which import, engine version) for provenance.

### 7.4 Gap U5 — score my dataset with the same rules

Once U4 lands, a researcher can drop in a DE table from *their* Perturb-seq screen (any cell type, if they accept the CD4-tuned axes are advisory) and get: ranked cards, QC badges, statistical grade, readiness call, and export. Add a **compatibility banner** driven by the existing context-match score so cross-context data is flagged (e.g., "non-CD4 context: pathway/clinical axes are advisory only").

### 7.5 Raw-cell path (U6)

Large `.h5ad/.h5/.mtx/.loom/.zarr` files stay **staged-only** and require a manifest (donor, condition, batch, guide/target, control) before any processing — already enforced. Next step is a **manifest builder** UI + an on-demand cell-level job (§5.5) that runs only when the user explicitly requests it (cost control).

### 7.6 Provenance & versioning (U8)

Every uploaded source already stores `import_id`, timestamps, source path, schema result, context result. Extend with: data hash, column mapping, engine/schema version, and a merge lineage so any card can answer "where did this come from and which rules produced it."

---

## 8. Scoring & readiness methodology

### 8.1 Data contract (the 24–30 column card)

The card schema is defined in `sources/topic14_target_card_specification.md` and produced by `build_target_cards.py`. Freeze it as **v1** and version any change.

### 8.2 Statistical evidence grade (exists, 1–4)

From `build_target_cards.py::_make_score`:
- **Grade 4 (A):** all thresholds pass **and** strong replicability (cross-donor & cross-guide ≥ 0.3, guide-signif ratio ≥ 0.5, guide FDR ≤ 0.05, ≥2 guides).
- **Grade 3 (B):** replicate-pass, ≥2 guides, guide FDR ≤ 0.1.
- **Grade 2 (C):** ≥200 cells and on-target significant (needs h5ad reinforcement).
- **Grade 1 (D):** raw DE signal only.

`replicate_pass_flag` gate: `n_cells ≥ 200 ∧ n_total_de_genes ≥ 50 ∧ ontarget_significant ∧ ¬offtarget_flag ∧ crossdonor_mean ≥ 0.2 ∧ crossguide ≥ 0.2`.

### 8.3 Score-cap reasons (exists)

Every capped card must carry ≥1 reason: `low_cells`, `low_signal`, `direction_unclear`, `high_offtarget`, `weak_replicability`, `guide_limit`, `single_donor_dominance`, `guides_inconsistent`, `batch_sensitive`. This is the anti-black-box mechanism.

### 8.4 Fix C4 — real batch-sensitivity flag (currently a stub)

Replace the hard-coded `"unknown"`. Rule (grounded in §3.1): a `target × Stim48hr` claim that is **not** supported by cross-donor/cross-guide robustness is `batch_sensitive` because Stim48hr is confounded with run `CD4i_R2`. Wire this into `score_cap_reason` so Stim48hr-only hits are visibly down-weighted.

### 8.5 Wire the readiness engine (gap R1–R3)

The 12-domain schema already exists in `sources/topic04_drug_readiness_checklist.csv`:
`biology_causality`, `disease_relevance`, `human_genetic_support`, `tractability_modality/score`, `safety_window`, `cd4_immune_red_flags`, `biomarker`, `translation`, `clinical_feasibility` → **R0–R5** → `advance/validate/watchlist/deprioritize`.

Build a rule engine that:
- fills GWT-native domains (biology causality, translation) from cards;
- fills external domains (genetics, tractability, safety, clinical) from the evidence layer (§5.2), leaving them explicitly `unknown` when no overlay is available (never silently 0);
- applies **red-flag overrides** (essential/killer risk, uncertain direction, off-target) that cap the call regardless of other scores;
- emits a stage (R0–R5) + a decision label + human-readable reasons.

**Invariant:** the readiness call can never exceed what evidence supports; uncertain direction caps at `validate`, missing tractability caps `advance`.

### 8.6 Module scoring (upgrade C8)

The API currently does binary membership overlap against seed modules. Upgrade to **signed** module scoring: use each target's DE direction vector against the 20 signed CD4 modules (`topic15` seed modules) to score activation/Treg/Th1/Th2/Th17/Tfh/exhaustion/cytokine, so a card says *how* a target moves a program, not just that it overlaps.

---

## 9. Validation, calibration, and trust

A prioritization tool is only credible if it recovers known biology. Build a **calibration harness** (from `topic11` §Validation metrics) as a first-class, re-runnable module:

- **Positive-control recovery:** TCR/proximal genes (`CD3E, LAT, PLCG1, ZAP70, LCP2, VAV1, CD247, ITK`) should surface in top deciles.
- **Known drug-axis recovery:** CD3, CD28/CD80/CD86, IL-2/IL-2R, JAK/STAT, NFAT/calcineurin, IL-17/IL-23, TNF.
- **Rank stability:** re-rank after excluding off-target / low-cell / low-donor-robustness / low-guide-robustness rows; report rank churn.
- **Donor-holdout / guide-holdout concordance** where data allow (`src/3_DE_analysis/donor_robustness/`, `guide_robustness/` already compute the raw inputs).
- **Expert-review agreement** on the top 50–100 cards.

Ship these as a `calibration_report` the dashboard can render, so trust is demonstrated, not asserted.

---

## 10. Data governance, provenance, security, deployment

- **Persistence:** move from file-cache to **Supabase/Postgres** (connector available) for datasets, imports, users, provenance, and merge lineage. Keep the file cache as an export target.
- **Multi-user:** add auth + per-user/project workspaces so uploaded data is isolated. Uploaded-derived cards stay namespaced (§7.3).
- **Security (already partly enforced):** whitelisted source types, extension checks, 25 MB upload cap, allowed-root restriction for local paths. **Add** server/proxy request-body limits (noted as a known issue), rate limiting, and virus/format sniffing for uploads.
- **Provenance everywhere:** data version + engine version + source stamps on every card, report, and export. Reports already cache under `sources/target_tool_cache/<dataset_id>/`.
- **Deployment:** containerize API + dashboard; pin `environment.yaml`; expose health checks (exist: `/api/health`). Keep everything runnable locally for research use (the M3.5 release was local-first).
- **Cost control for cell-level:** the 1.6+ TiB S3 dataset is opt-in per analysis; never auto-download.

---

## 11. Milestone roadmap and prioritized backlog

Building on the existing M3.5 (upload staging). Each milestone is shippable and demoable.

### M4 — Close the upload loop + finish QC (highest ROI)
- **U4** merge approved import → cards · **U3** column-mapping wizard · **U5** score-my-dataset
- **C4** real batch-sensitivity flag · **C3** finish QC badges · **C7** essential-confounder quarantine · **C6** pan-condition split · **C9** positive-control panel · **C10** QC funnel
- **Calibration harness** (§9) v1
- *Outcome:* a researcher can upload a DE table and get calibrated, QC-badged cards; GWT cards show honest confidence.

### M5 — Readiness engine + local translational overlays
- **R1–R3** 12-domain readiness → R0–R5 → decision call with reasons and red-flag overrides
- **T1** local druggable-class overlay · **T9** safety-flag panel (local lists)
- **R4** validation planner · **R5** rank-stability analysis
- **Target Card** deep page (§6.1.3)
- *Outcome:* every card carries a defensible advance/validate/watchlist/deprioritize call and a next experiment.

### M6 — External evidence via live connectors
- **T5** ClinicalTrials.gov · **T6** PubMed/bioRxiv literature+citations · **T2** Open Targets · **T3** ChEMBL/DGIdb · **T4** DepMap
- Cached, version-stamped adapters (external APIs drift — snapshot everything)
- *Outcome:* cards speak the Open-Targets-style translational language; genetics/tractability/clinical domains fill in.

### M7 — Disease translator + platform hardening
- **T8** disease/trait translator (RA/IBD/MS/SLE/psoriasis/cancer-TME, ICD-10 normalized) · Disease Translator page
- **Supabase** persistence + auth + workspaces (§10) · shareable report links
- *Outcome:* multi-user platform; indication-driven target discovery.

### M8 — Cell-level extension (after h5ad download)
- **H1–H2** loaders + per-cell QC · **H3** Mixscape · **H4** SCEPTRE · **H5** pertpy/UCell · **H6** state-specific effects bridged to cards
- **U6** raw-cell manifest builder + on-demand jobs
- *Outcome:* responder fractions, escaped cells, state-specific effects strengthen (or cap) grade-2 cards.

### M9 — v2 hypothesis generators (guarded, optional)
- **V1** signature-to-compound · **V2** mechanism graph · **V3** prediction models *(benchmark vs baselines first; never feed readiness decisions)* · **V4** combination explorer *(research-only)*

**Immediate next actions (this week):** wire U4 (merge dead-end), replace the C4 batch stub, add the C7 essential overlay from `core_essentials_hart.tsv`, and stand up the calibration harness — these are small, high-trust wins on data already in-repo.

---

## 12. Risks, scientific limitations, honesty guardrails

From `sources/topic11` and `topic15_limitation_future_work_audit_table.md` — surface these *in the UI*, not just in docs:

- **Scores can look more certain than evidence supports** → mandatory `score_cap_reason`, provenance footer, uncertainty framing.
- **CRISPRi ≠ pharmacology** → modality caveat on every readiness call.
- **In-vitro isolated CD4** misses antigen specificity, trafficking, tissue context, myeloid/stromal feedback, protein-level cytokine output → "in-vitro context" banner.
- **Stim48hr batch confound** → §8.4 flag.
- **Broad chromatin/essential hits dominate high-DE rankings** → §5.1 C7 quarantine.
- **External annotations drift / are disease-agnostic** → cache + version snapshots.
- **LINCS/CMap/Tahoe context mismatch** → label V1 outputs as hypotheses only.
- **No h5ad → no responder/escaped/per-cell/state analysis** → grade-2 cards explicitly say "needs cell-level validation."
- **Foundation-model predictors** don't consistently beat baselines (2025 benchmarks) → V3 gated behind baseline comparison, never a decision input.

---

## 13. Insights & recommendations (opinionated)

1. **This is a target-prioritization + evidence-transparency product, not a drug-discovery engine.** The credible, differentiated value is *decision-grade, decomposable cards*, not a magic score. Every prior research doc converges on this; the plan enforces it.

2. **The single highest-ROI work item is closing the upload loop (U4).** The system already stages and approves uploads but does nothing with them — the researcher-upload requirement is 80% built and 0% useful until merge exists. Fix that first.

3. **Wire the readiness engine you already designed.** The 12-domain schema and R0–R5 gate exist in `topic04` but the cards only compute a *statistical* grade. The gap between "statistically strong perturbation" and "readiness call" is exactly where researchers need help — and the schema is already written.

4. **Use the live MCP connectors for the external-evidence layer.** ClinicalTrials.gov, PubMed, and bioRxiv are connected in this environment. The prior research listed these as "later, external, hard." They're now "wire an adapter." Supabase solves the persistence/multi-user gap the same way.

5. **Make honesty a feature, not a footnote.** The condition confound (Stim48hr↔R2), the essential-gene confounders, and the CRISPRi≠pharmacology caveat should be *visible on the card*. A tool that shows why a hit is risky is more trustworthy — and more scientifically defensible — than one that hides it. This is the product's real moat.

6. **Fund the calibration harness early.** Recovering `CD3E/LAT/ZAP70/PLCG1` in the top deciles and known drug axes (CD3, IL-2/IL-2R, JAK/STAT, NFAT) is how you earn a researcher's trust in one screen. It's cheap (data is in-repo) and it de-risks everything downstream.

7. **Keep CSV-first as the spine.** ~1.2k high-confidence rows are addressable *today* without touching the 1.6 TiB cell-level data. Ship value on CSVs; treat h5ad as an accuracy upgrade for the shortlist, not a gate.

---

### Appendix A — key grounding files in this repo

- Data: `metadata/suppl_tables/{DE_stats, guide_kd_efficiency, sgrna_library_metadata, sample_metadata}.suppl_table.csv`
- EDA: `sources/topic09_eda_report.md`, `sources/topic09_eda_outputs/eda_summary.json`
- Schemas: `sources/topic14_target_card_specification.md`, `sources/topic04_drug_readiness_checklist.csv`
- Benchmarks/modules: `sources/topic05_successful_drug_benchmarks.csv`, `sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv`
- Architecture: `sources/topic06_toolkit_architecture_summary.md`, `sources/topic11_breakthrough_directions_toolkit_opportunities.md`
- Existing code: `src/3_DE_analysis/{build_target_cards, target_card_api, target_card_dashboard, import_manager, generate_target_report}.py`
- Release history: `sources/release_notes_m3_5_upload_import.md`
- Gene-class lists: `metadata/gene_lists/*`, `metadata/IUIS-IEI-list-July-2024V2.csv`, `metadata/immune_effector_genes.csv`
- Palettes: `metadata/figure_palettes.yaml`
