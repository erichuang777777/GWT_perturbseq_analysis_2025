# Perturbase: An auditable target-prioritisation layer over a genome-scale CRISPRi Perturb-seq screen in primary human CD4⁺ T cells

**Manuscript · v1.0 · 2026-07**
Research / hypothesis-generating use only — not clinical software.

---

## Abstract

Genome-scale Perturb-seq in primary human immune cells produces differential-expression (DE) results for tens of thousands of gene knockdowns, but the step from that DE table to a defensible, auditable list of candidate drug targets is left to ad-hoc spreadsheet work. We present **Perturbase**, a decision-support layer that consumes the published DE output of a genome-scale CRISPRi Perturb-seq screen in primary human CD4⁺ T cells (Zhu, Dann et al., 2025) and converts 33,983 perturbation × condition rows into structured, versioned **target cards** carrying a four-level decision call (*advance / validate / watchlist / deprioritize*). Three design choices make the output auditable rather than merely ranked: (i) a four-state **knockdown-causality gate** (`kd_status`) that separates perturbations whose downstream transcriptional effects are causally interpretable from those that are not, treating never-measured baselines as *unknown* rather than zero; (ii) a **red-flag override** that caps essential, broad-effect, off-target, batch-confounded, and knockdown-unconfirmed targets at a low decision tier no matter how strong their downstream statistics; and (iii) a **positive/negative control calibration** that quantifies whether the ranking recovers known biology. On a 21-gene canonical CD4 positive-control panel the ranking reaches AUROC 0.85 (13 positives vs 1,211 background; average precision 0.47, 44.7× random; Mann-Whitney *p* = 8.8×10⁻⁶); 4,774 documented negative controls are graded correctly 99.96% of the time with 0% reaching *advance*. We add an external translation layer the screen does not contain — evolutionary constraint, population genetics, clinical-trial and disease evidence, tissue-expression safety windows, druggability, protein structure — as explicitly sparse overlays under an `unknown ≠ 0` governance rule. Cross-checks against three independent datasets (immune GWAS, STRING protein-interaction recovery, and an orthogonal HIV host-factor screen) are corroborative but not confirmatory. We position Perturbase precisely: it is a triage-support tool for prioritising which targets deserve wet-lab follow-up, not a reproduction or extension of the source screen's regulatory-network inference, and every claim it makes is bounded by an unmet prospective-validation gap.

---

## 1. Introduction

Perturb-seq couples pooled CRISPR perturbation with single-cell RNA sequencing, allowing the transcriptional consequences of thousands of individual gene perturbations to be measured in a single experiment. Most large-scale Perturb-seq resources have been built in immortalised cancer cell lines, which are easy to culture but transcriptionally distant from the primary cells in which immune-therapeutic hypotheses must ultimately hold. The screen that anchors this work is unusual in that it is performed in **primary human CD4⁺ T cells**, covers the genome, and is replicated across four donors, two processing batches, and three culture conditions (`Rest`, `Stim8hr`, `Stim48hr`) — giving each perturbation a context-resolved readout with greater translational relevance than a cell-line screen.

A genome-scale screen of this kind is a discovery *substrate*, not a discovery *answer*. The published DE table contains 33,983 rows — one per (target gene × culture condition) — spanning 11,526 perturbed genes. Turning that into an actionable target list requires answering questions the DE table does not answer on its own: Was the target actually knocked down, so that its downstream effects are causally interpretable? Is a broad transcriptional footprint real regulatory breadth, or an essential-gene fitness artefact? Does a candidate carry human genetic, clinical, or druggability evidence that would justify the cost of a wet-lab campaign? These are triage questions, and in practice they are answered inconsistently, without provenance, and without a record of what was *unknown* versus what was *negative*.

**Perturbase** is our answer to that gap. It is explicitly **not** a new sequencing or DE method, and it is **not** a reproduction of the source screen's core scientific contribution (the inference of context-specific gene-regulatory networks). It is a decision-support layer that sits on top of the already-published, already-validated DE output and does one thing well: it converts that output into structured, versioned, auditable target cards, preserving provenance and uncertainty at every step, so that an external reviewer can check each decision rather than trust a black-box score.

This manuscript states, for each component, its data provenance, its precise definition, its statistical basis, its validation numbers, and its explicit scope limits. The intent is that a reader can audit the platform line by line — which is the standard we believe a target-prioritisation tool must meet before any of its output influences an experiment.

---

## 2. Methods

### 2.1 Data provenance and governance

The primary dataset is the genome-scale CRISPRi Perturb-seq screen of Zhu, Dann et al. (2025), consumed through its published supplementary tables (`DE_stats.suppl_table.csv`, one row per target × condition, *n* = 33,983; `guide_kd_efficiency.suppl_table.csv`; `sgrna_library_metadata.suppl_table.csv`; `sample_metadata.suppl_table.csv`). Raw sequencing is public (SRA `SRP643211` / GEO `GSE314342`; CZI Virtual Cells Platform). The platform **consumes** this DE output — it does not recompute DE, pseudobulk aggregation, or the non-targeting-control (NTC) baseline.

All effect sizes and DE calls are defined relative to a **condition-matched NTC baseline**: for each (perturbed gene, culture condition), NTC statistics are computed from NTC cells within the *same* condition. We verified this empirically in-repo — across 37,578 groups, zero showed more than one distinct `ntc_mean_expr` within a (gene, condition) pair, confirming the baseline is condition-matched rather than per-guide. On-target effect size is the target gene's own log₂ fold-change in its knockdown contrast versus that condition-matched NTC pseudobulk baseline (DESeq2); DE-gene counts use a 10% FDR (Benjamini–Hochberg).

The governing principle throughout is **`unknown ≠ 0`**: a field that was never measured is recorded as `unknown` and never silently imputed to zero. User-uploaded data is namespace-isolated (`usr_` prefix) and never mixed into the reference set. The platform processes no identifiable personal data and its output is a research-use target prioritisation, not a clinical or prescribing recommendation.

### 2.2 Target-card construction and evidence grading

`build_target_cards.py` aggregates guide-level knockdown data and DE statistics into one card per (target × condition), assigning a `statistical_evidence_grade` (1–4) and a `score_cap_reason`. Grading is a reproducibility gate layered on top of the upstream `keep_for_DE` flag — requiring minimum cell counts, cross-donor and cross-guide correlation, and off-target screening — and is deliberately **conservative**: missing guide data caps a card at grade 2.

### 2.3 The knockdown-causality gate (`kd_status`) — core design

The CRISPRi causal chain is *target repressed → downstream transcription changes*. If the target's own knockdown is not confirmed, its downstream DE is not causally interpretable. The platform summarises guide-level Welch *t*-tests into a four-state gate:

| State | Condition | Interpretation |
|---|---|---|
| `confirmed` | guide-significant ratio ≥ 0.5 and min guide FDR ≤ 0.05 | knockdown confirmed; downstream causally interpretable |
| `weak` | signal present but below confirmation | downstream suspect; capped at *validate* |
| `not_measurable` | measured NTC baseline ≤ 0.001 | knockdown itself unassessable; capped at *watchlist* |
| `not_assessed` | baseline never measured (NaN) | genuinely unknown — **not penalised** |

The `not_measurable` floor (0.001) reuses the dataset's own documented `high_confidence_no_effect_guides` definition rather than inventing a threshold. Distinguishing `not_measurable` (a measured failure) from `not_assessed` (a never-measured unknown) is deliberate: they are different failure modes and are treated differently.

### 2.4 Robustness

Each row carries `crossdonor_correlation_mean/min` (Pearson correlation of logFC effects between disjoint donor pairs) and `crossguide_correlation` (between individual gRNAs). Missing values surface an explicit caveat (`weak_replicability` / `missing_crossdonor_data`) and are never zero-filled. `replicate_pass_flag` requires simultaneous cross-donor and cross-guide robustness with ≥2 guides.

### 2.5 Readiness engine and red-flag override

The readiness engine (`core/readiness.py`) scores each card across ~12 evidence facets (statistical grade, replicate robustness, knockdown confirmation, pathway/clinical axes, positive-control similarity, clinical trials, Open Targets associations, genetics via ClinVar/GWAS catalog, gnomAD LOEUF/pLI, nearest successful-drug axis) and places it on an `R0–R5` maturity ladder. A **red-flag override** then caps the call regardless of statistical strength:

| Red flag | Trigger | Cap |
|---|---|---|
| `essential_gene` | core-essential | watchlist |
| `broad_effect` | broad-effect list (239 genes) | watchlist |
| `high_offtarget` | off-target flag (significant down-regulation within 10 kb of TSS) | watchlist |
| `kd_not_measurable` | `kd_status = not_measurable` | watchlist |
| `uncertain_direction` | on-target not significant / direction unclear | validate |
| `batch_confounded` | batch-sensitivity flag | validate |
| `kd_weak` | `kd_status = weak` | validate |

Unbuilt facets return `"unknown"` and are never counted as zero; essential genes are not assigned a fabricated safety-window score.

### 2.6 Decision calling, context-specificity, versioning

`STAGE_TO_CALL` maps the readiness stage to *advance / validate / watchlist / deprioritize*, then the red flags cap it; each row emits a `score_cap_reason`, a `next_step`, and a provenance footer. The `condition_specificity_score` is explicitly declared a **ratio-based heuristic, not a statistical interaction test** — a rigorous condition × perturbation test requires per-guide/per-cell models the platform does not have, and is scoped out by design. Every dataset carries four version layers (engine / dataset / schema / signature_set); each build produces a new immutable `dataset_id` written to a fresh directory, so shared links always return identical numbers.

### 2.7 External evidence and translation layer

An evidence layer integrates, cache-first with `fetched_at` version stamps (30-day TTL, batch cap 50 genes, graceful degradation when the sandbox blocks a fetch): Open Targets, ClinicalTrials.gov, PubMed/PMC, gnomAD (LOEUF/pLI), GTEx tissue-expression safety windows, LINCS/CMap L1000 signature reversal, Reactome + STRING mechanism graphs, AlphaFold structures, CELLxGENE Census, and ChEMBL. A disease-translation module ranks cards against 13 autoimmune indications (7,528 Open Targets association rows). These overlays are real but mostly sparse; sparsity is surfaced, not hidden.

---

## 3. Results

*Results are ordered to lead with the load-bearing evidence — the independent benchmark and a named druggable win — before the mechanism and curation detail, following the handling-editor narrative review in §7.*

### 3.1 A genome-scale screen distils to a small, auditable candidate set

Applying the curation gate to all 33,983 DE-stat rows narrows the screen in four sequential filters — ≥200 cells (33,983 → 30,515, 90% retained), significant on-target knockdown (→ 19,297, 63%), no off-target flag (→ 16,998, 88%), and ≥50 DE genes (→ 2,131, 13%) — yielding **1,235 unique candidate targets** from 11,526 screened genes. On-target knockdown is the dominant effect category, present in ≈62% of DE-stat rows across all three conditions; the ≥50-DE-gene filter is the single strictest gate. Culture condition barely shifts the marginal distributions of effect size or DE breadth, confirming that the informative signal is per-target, not per-condition.

### 3.2 The ranking recovers known biology (calibration)

On a 21-gene canonical CD4 positive-control panel (CD3D/E/G, CD247, CD28, ICOS, CTLA4, CD80/86, IL2RA/B, IL7R, LCK, ZAP70, JAK3, PTPN2, FOXP3, PTGER4, STAT5A/B, TNFRSF9), the ranking achieves **AUROC 0.85** (13 curated positives vs 1,211 background), average precision 0.47 (44.7× the 0.011 random baseline), Mann-Whitney *p* = 8.8×10⁻⁶, and a median rank of 36 for positives versus 964 for background. In the `Stim8hr` condition the calibration recovers **all 8** TCR-proximal positive controls within the top decile. Critically, only **20%** of the positive panel clears the strict `grade ≥ 3` gate (which demands simultaneous cross-donor and cross-guide robustness with ≥2 guides in a specific condition), yet **93.1%** are not deprioritised by the readiness engine — an honest signal that strict grade is a narrow "everything lines up in this row" gate, not a proxy for biological truth, and must be read together with the readiness call.

### 3.3 The negative controls behave

The 4,774 documented negative controls (`kd_status = not_measurable`) are graded correctly **99.96%** of the time, with **0%** reaching grade ≥3 and **0%** reaching *advance* or *validate*. This is the complement of the positive-control result: the red-flag override does what it claims, and near-zero-baseline "hits" cannot leak into the actionable tiers.

### 3.4 Two artefact classes are caught before they mislead

Two systematic artefacts are diagnosed explicitly. First, **237 top-of-ranking candidates are essential-gene fitness artefacts**: they cluster below the ≥200-cell gate with low gnomAD LOEUF (94% below 0.35), i.e. their apparent signal is lost cells, not lost function. Second, a **baseline-expression correction flags 11 of 96 context-specific hits as expression artefacts** (all with resting baseline < 10), leaving 84 baseline-confirmed regulators. The discovery funnel therefore reads 1,235 candidates → 96 context-specific hits → 84 baseline-confirmed → 34 deliverable with a known therapeutic modality.

### 3.5 Ranking stability is reported honestly

A naive "top-50 by DE breadth" and the strict-filtered top-50 overlap in only **13 of 50** targets (Spearman *r* = 0.943 over the full universe). We report this as a finding, not a footnote: naive breadth-ranking is not itself robust, which is precisely why the curation gate and red-flag override exist.

### 3.6 Orthogonal external cross-checks (corroborative, not confirmatory)

Three independent datasets provide orthogonal cross-checks. (a) **Immune GWAS**: 26 of 55 validated targets carry immune genetic associations and 22 of 55 carry classic autoimmune associations, including strong exemplars such as TYK2–rheumatoid arthritis (0.93; target of the marketed drug deucravacitinib) and STAT3–hyper-IgE (0.95). (b) **STRING partner recovery**: flagship TCR-signalling hubs recover known partners in the perturbation downstream network (VAV1 62%, CD3E 58%), while novel targets under-recover — a literature-bias signal, not weak evidence. (c) **Orthogonal HIV host-factor screen (GSE318876)**: 52 of 55 targets are present in the genome-wide CD4⁺ screen library (confirming they are real functional genes in the correct cell type), but only 4 score as HIV host factors and the enrichment is non-significant (*p* = 0.535) — an honest negative that shows the tool does not overclaim cross-phenotype transfer.

### 3.7 The external translation layer

Beyond the screen, the platform attaches evidence the dataset does not contain: a signed directional overlay (from a separate in-repo `full_signed_DE` table with per-downstream-gene logFC) that recovers master regulators with correct sign (GATA3→Th2, TBX21→Th1, FOXP3→Treg as activators) for the ~3,739 targets that measurably perturb a module marker; a disease expansion across 621 tier-1 evidence genes (Open Targets 15,399 associations, ClinicalTrials.gov 2,090, NCBI MedGen 408); and protein-structure assets (AlphaFold models and Protter topology diagrams for the top-50 signed targets). Each overlay is presented with its coverage stated explicitly, under `unknown ≠ 0`.

---

## 4. Discussion

The load-bearing result is the module-independent benchmark: the ranking recovers 13 canonical CD4 regulators at AUROC 0.85 against ground truth that is independent of the concept modules used to build the ranking, and it does so while rejecting 237 essential-dropout artefacts at the ≥200-cell curation gate (with gnomAD LOEUF as the diagnostic) and 11 near-zero-baseline artefacts through the baseline-expression correction. A named, fundable consequence follows directly — TYK2, a top signed-DE hit, is the target of the marketed drug deucravacitinib and carries a strong rheumatoid-arthritis genetic association, and the platform advances it on evidence a reviewer can trace. We foreground these because they are the claims that justify the tool; the curation counts and mechanism detail below are the machinery that makes them defensible.

The contribution of Perturbase is not a new measurement but a new *discipline* imposed on an existing one. A genome-scale primary-cell Perturb-seq screen is expensive and information-rich, and the temptation is to rank its targets by the most visible statistic — downstream DE breadth — and hand the top of that list to a wet lab. Our results show why that is unsafe: naive breadth-ranking overlaps the robust ranking in only 13 of 50 targets, 237 top candidates are essential-gene artefacts, and 11 of 96 context-specific hits vanish under a baseline-expression correction. Each of these failure modes is invisible in the raw DE table and is caught only by an explicit gate.

The design principle that carries the most weight is the separation of *unknown* from *negative*. Most scoring systems collapse the two — a missing knockdown measurement becomes a zero, a never-fetched clinical association becomes "no evidence" — and the collapse silently penalises exactly the novel targets a discovery effort exists to find. By preserving `not_assessed` as a distinct, unpenalised state, and by having the readiness engine return `"unknown"` rather than zero for unbuilt facets, the platform keeps novel-but-under-annotated targets in contention while still capping genuinely disqualifying ones through the red-flag override.

The calibration strategy is deliberately adversarial to our own conclusions. We could have widened the grade gate until the positive-control panel looked good; instead we report that only 20% of canonical positives clear strict grade ≥3, and we interpret that as a property of the gate, not a failure of the biology. Calibrating a metric *to* the answer is not validation, and the honest 20%/93.1% split (strict grade vs not-deprioritised) is more informative than a tuned number would be.

The external cross-checks deserve their careful framing. The immune-GWAS overlap and the VAV1/CD3E STRING recovery are genuine positive signals; the non-significant HIV host-factor enrichment is a genuine negative. Reporting all three — rather than only the two that flatter the tool — is what makes the validation ladder corroborative rather than confirmatory. The bottom line is deliberately modest: the computational evidence is sufficient to prioritise which targets deserve wet-lab follow-up, and not sufficient to claim causation or therapeutic effect.

---

## 5. Limitations

The following are deliberately recorded so they are not mistaken for oversights:

1. **No prospective wet-lab validation (L5).** The validation ladder reaches orthogonal computational cross-checks (L4); no prospective experiment has been performed. This is the binding limitation — no output should be read as stronger than "worth testing."
2. **Not a reproduction of the source screen's science.** The platform does not re-derive the paper's context-specific gene-regulatory networks. What appears as "pathways" is either static concept-module membership (binary overlap; the aggregate DE table carries only up/down counts, no per-gene direction) or external Reactome/STRING graphs — not networks inferred from this screen.
3. **No new genes.** The cards reprocess the same 11,526-gene, 4-donor universe; there are no genes to discover beyond the screen. ML tracks that attempted predictive discovery lost to or failed to beat simple baselines.
4. **Context-specificity is a heuristic**, not a condition × perturbation interaction test.
5. **Strict grade 3/4 is a narrow gate** (~20% of the positive panel); it must be read with the readiness call, never alone.
6. **Explicit method descopes:** signed module scoring on the aggregate table is refused (a signed score would be fabricated); SCEPTRE is an honest external R hook with graceful degradation, not a naive Python rewrite; pertpy/Mixscape is replaced by a documented scikit-learn stand-in (upstream build failure).
7. **Cell-level real data not run.** The full single-cell layer (~1.67 TB) and `DE_stats.h5ad` (15.6 GB) are S3-only and exceed the analysis environment; the cell-integration path was validated only on a schema-faithful synthetic fixture (81.8% classification accuracy) — a different claim from processing the real data.
8. **`n_donors` is a permanent placeholder (always NaN; 0/33,983 rows populated)** — no per-target donor-count source is wired in; recorded as `unknown`.
9. **Sparse external coverage.** Sandbox network policy limits live fetches; the evidence overlay covers only cache-covered genes, with the rest `unknown` (never `0`).
10. **Product scope:** single-user file-cache with no access control; the front-end is a static React portal baked from a one-time export and does not call the live backend at runtime.

---

## 6. Conclusion

Perturbase demonstrates that the value added on top of a genome-scale primary-cell Perturb-seq screen is not another ranking but an *auditable* one. By gating on knockdown causality, overriding with hard red flags, calibrating against known biology in both directions, preserving `unknown` as distinct from `negative`, and stamping every dataset with immutable four-layer provenance, the platform turns 33,983 opaque DE rows into 1,235 candidate cards whose every decision a reviewer can trace and contest. The ranking recovers canonical CD4 regulators (AUROC 0.85), rejects negative controls near-perfectly (99.96%), catches two systematic artefact classes before they mislead, and is corroborated — not confirmed — by three orthogonal external datasets. What remains is the experiment: prospective wet-lab validation is the one gap the computation cannot close, and the platform is built to say so on every card. Positioned honestly, it is a triage-support layer that makes the expensive next step — the wet lab — better targeted, and nothing more than that.

---

## 7. Figure narrative and revision plan (handling-editor review)

The figure deck (33 main-display figures) was assessed by a handling-editor narrative review (paper-narrative skill) judging *story*, not craft. The verdict and the resulting revision plan are recorded here so the manuscript's figure strategy is explicit and auditable.

**Hook verdict — lean yes, but not on Figure 1 as currently drawn.** The idea is fundable and the proof exists: a causal-gated signed ranking recovers 13 canonical CD4 regulators at AUROC 0.85 (AP 0.47, 45× random; median rank 36 vs 964; *p* = 8.8×10⁻⁶) against ground truth **independent** of the modules used to build the ranking. That benchmark is what earns a review — but in the current deck it arrives deep in the validation figures, while Figure 1 spends four of seven panels on defensive controls. The single most arresting fact — TYK2 is a top signed-DE hit *and* the target of a marketed drug (deucravacitinib) — is buried as one dot in a lollipop panel. The hook therefore undersells the work.

**Narrative arc (hook → mechanism → evidence → application):**
- *Hook* — currently diluted across two pipeline banners with different denominators (33,983 rows vs 10,851/11,526 targets vs 1,235 shortlist). Collapse to one canonical pipeline with one denominator held constant across all figures.
- *Mechanism* — the strongest-told act: the signed directionality axis separating repressor-like (net-derepressing on KO) from activator-like knockdowns, plus the three T-cell modules (TCR-proximal / SAGA / Mediator) and the silent-at-rest, surge-on-stim heatmap.
- *Evidence* — the strongest asset, currently inverted with the hook: the independent benchmark and the two artefact-rejection analyses (237 essential-dropout suspects; 11 near-zero-baseline artefacts; funnel 1,235 → 96 → 84 → 34).
- *Application* — present across the delivery-modality, kinetic-archetype, clinical-avoid-list and dev-vs-user-gap panels. Note: the reviewer flagged the "missing" centrepiece as the target card itself, but the target card is a **live webserver feature**, not a manuscript figure — a static mock would be a screenshot of software, not a scientific result. It is documented in the product/UI materials and belongs in a supplementary UI walkthrough, not the narrative figure deck.

**Revision plan applied to the figure set:**
1. **Promote the benchmark PR/ROC into Figure 1** as the anchor panel — its module-independent ground truth is the whole argument and must be unmissable.
2. **Promote the TYK2 worked example** into its own hero panel: top signed-DE repressor-like hit + marketed inhibitor + rheumatoid-arthritis genetic association → resulting *advance* call.
3. **Demote the HIV-null and LINCS-exploratory panels** out of Figure 1 into a methods/limitations supplement (keep them — they answer "what did we *not* prove" — just not as the hook).
4. **Merge the two opening pipeline banners** into one canonical schematic with a single denominator.
5. **Consolidate the three artefact-rejection panels** (RNA/cell-cycle dotplot, LOEUF essential-dropout scatter, baseline-correction) into one "how the system rejects false positives" figure.
6. **Collapse the three LINCS concordance panels** into a single supplementary panel (a demo-level, *n* = 4, non-T-cell check should not be told three times).

**Missing panels to build (analyses to run):** *(the reviewer's fourth item — "show the target card" — is deliberately excluded: the target card is a live webserver feature, not a scientific figure, and is covered by the product/UI documentation, not the narrative deck. The three panels below are genuine analytical results.)*
- **Call calibration, not just rank discrimination** — precision at each of the four tiers against the 13 positives and the 237 + 11 artefacts as negatives, converting a ranking metric (AUROC) into a decision metric (what the tool actually outputs).
- **Red-flag override demonstration** — a before/after panel for 2–3 targets that scored high on signed-DE and were demoted, showing pre-override rank, the flag triggered, and the final tier.
- **Audit-trail / versioning view** — a schematic tracing one call back to its inputs (screen row → signed rank → gate decision → each external overlay with source + version), giving the "auditable / versioned" claim a figure.

**Cut from the paper (chart-range demonstrations, not the argument):** the seven `gallery_*` chart-family composites; the two Protter topology cartoons (unless tied to a modality claim); two of three cover concepts; both brand assets; and de-duplicated benchmark/LINCS instances.

**Boldest defensible Figure 1** — four panels, leading with proof and a named win: (a) one pipeline line, single denominator; (b) the benchmark PR/ROC as the anchor, with the module-independence note explicit; (c) the TYK2 worked example as a data panel — signed-DE rank, gate PASS, RA genetic association, and marketed-inhibitor annotation converging on an *advance* call (the evidence behind the call, not a screenshot of the card UI); (d) one honesty panel showing the system deprioritises the 237 + 11 artefacts as confidently as it advances real hits. This trades four defensive panels for a single calibrated claim — *"we recover known CD4 biology, we flag the junk, and here is a druggable win"* — told in the order a reviewer needs to hear it.

---

## Data and code availability

Code: `https://github.com/erichuang777777/GWT_perturbseq_analysis_2025` (`src/3_DE_analysis/`); environment `environment.yaml` (Python 3.11); tests `python -m pytest tests/ -q`. Primary data: CZI Virtual Cells Platform; SRA `SRP643211` / GEO `GSE314342`. Source screen: Zhu R., Dann E. et al. (2025), bioRxiv doi:10.64898/2025.12.23.696273. Determinism: identical inputs + identical four-layer versions → identical outputs; each `dataset_id` is an immutable snapshot.

*This manuscript describes a research-use, hypothesis-generating target-prioritisation toolkit built on published data. It is not clinical software and makes no diagnostic, prescribing, or treatment claim.*

---

## References (literature-appraisal set, verified)

The following primary sources were retrieved and DOI-verified during the literature appraisal (`LITERATURE_APPRAISAL.md`). They anchor the manuscript's claims to external evidence, supportive and non-supportive.

**Genetic evidence for targets**
- Nelson M.R., et al. (2015) The support of human genetic evidence for approved drug indications. *Nat Genet.* doi:10.1038/ng.3314
- King E.A., Davis J.W., Degner J.F. (2019) Are drug targets with genetic support twice as likely to be approved? *PLoS Genet.* doi:10.1371/journal.pgen.1008489
- Minikel E.V., et al. (2024) Refining the impact of genetic evidence on clinical success. *Nature.* doi:10.1038/s41586-024-07316-0
- Buniello A., et al. (2024) Open Targets Platform. *Nucleic Acids Res.* doi:10.1093/nar/gkae1128

**Constraint, essentiality, and CRISPR-screen calibration**
- Karczewski K.J., et al. (2020) The mutational constraint spectrum (gnomAD). *Nature.* doi:10.1038/s41586-020-2308-7
- Tsherniak A., et al. (2017) Defining a Cancer Dependency Map. *Cell.* doi:10.1016/j.cell.2017.06.010
- Dempster J.M., et al. (2021) Chronos: a cell population dynamics model of CRISPR experiments. *Genome Biol.* doi:10.1186/s13059-021-02540-7
- Barry T., et al. (2021) SCEPTRE improves calibration and sensitivity in single-cell CRISPR screen analysis. *Genome Biol.* doi:10.1186/s13059-021-02545-2
- Barry T., et al. (2024) Robust differential expression testing for single-cell CRISPR screens at low MOI. *Genome Biol.* doi:10.1186/s13059-024-03254-2
- Morris J.A., et al. (2023) Discovery of target genes and pathways at GWAS loci by pooled single-cell CRISPR screens. *Science.* doi:10.1126/science.adh7699

**Single-cell DE readout and perturbation modelling**
- Squair J.W., et al. (2021) Confronting false discoveries in single-cell differential expression. *Nat Commun.* doi:10.1038/s41467-021-25960-2
- Dong M., et al. (2023) Causal identification of single-cell experimental perturbation effects with CINEMA-OT. *Nat Methods.* doi:10.1038/s41592-023-02040-5
- Roohani Y., et al. (2023) Predicting transcriptional outcomes of novel multigene perturbations with GEARS. *Nat Biotechnol.* doi:10.1038/s41587-023-01905-6

**Primary human T-cell functional genomics**
- Shifrut E., et al. (2018) Genome-wide CRISPR screens in primary human T cells. *Cell.* doi:10.1016/j.cell.2018.10.024
- Schmidt R., et al. (2022) CRISPR activation and interference screens decode stimulation responses in primary human T cells. *Science.* doi:10.1126/science.abj4008
- Freitas K.A., Belk J.A., Sotillo E., et al. (2022) Enhanced T cell effector activity by targeting the Mediator kinase module. *Science.* doi:10.1126/science.abn5647
- Carnevale J., et al. (2022) RASA2 ablation in T cells boosts antigen sensitivity and long-term function. *Nature.* doi:10.1038/s41586-022-05126-w

**TYK2 / deucravacitinib worked example**
- Wrobleski S.T., et al. (2019) Highly selective inhibition of tyrosine kinase 2 (TYK2). *J Med Chem.* doi:10.1021/acs.jmedchem.9b00444
- Armstrong A.W., et al. (2023) Deucravacitinib versus placebo and apremilast in plaque psoriasis (POETYK PSO-1). *J Am Acad Dermatol.* doi:10.1016/j.jaad.2022.07.002
- Strober B., et al. (2023) Deucravacitinib versus placebo and apremilast (POETYK PSO-2). *J Am Acad Dermatol.* doi:10.1016/j.jaad.2022.08.061
- Morand E.F., et al. (2022) Deucravacitinib in systemic lupus erythematosus (phase 2). *Arthritis Rheumatol.* doi:10.1002/art.42391

*The full methods-and-domain reference list (DESeq2, Benjamini–Hochberg, Perturb-seq foundational methods, external databases) is maintained in `docs/technical_methods.md §8`; this section adds the appraisal's verified evidence-appraisal sources.*
