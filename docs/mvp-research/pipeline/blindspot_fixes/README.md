# Blindspot-fix data layer — data dictionary & handoff

This layer closes six developer→user blindspots. All values English. All GB10-free
(computed from existing DE_stats + Open Targets; no per-gene signed matrix needed).

## Files

### gene_gate_diagnosis.csv — 11,526 rows (blindspot 1: "why isn't my gene here?")
Diagnoses, for EVERY target in the raw data, whether it passed the quality gate and — if not — why.
Official gate (per-condition): n_cells_target>=200 AND ontarget_significant AND NOT offtarget_flag AND n_total_de_genes>=50.
Columns:
- target_contrast_gene_name — gene symbol
- gate_pass — AUTHORITATIVE per-condition pipeline result (sums to exactly 1,235)
- best_condition — condition with strongest evidence
- fail_primary — first threshold tripped in gate order (cells→significance→offtarget→DE), or 'PASS'
- failure_reasons — all tripped thresholds, human-readable
- n_cells_best, de_genes_best — best-condition supporting values (for the UI funnel)
- significant_any, offtarget_any — **ANY-CONDITION AGGREGATE FLAGS** (True if true in ANY of the 3 conditions)
- n_conditions — conditions available for this target

> **IMPORTANT column-semantics note (from adversarial review):**
> `gate_pass` is the authoritative per-condition pipeline output (1,235 pass).
> `significant_any` and `offtarget_any` are **any-condition aggregates**, whereas
> `n_cells_best`/`de_genes_best` are **best-condition** values. Re-deriving the gate
> naively from these summary columns yields 1,185, not 1,235 — a NET of two effects:
> +62 genes stored PASS but carrying offtarget_any=True from a NON-best condition,
> minus 12 genes stored FAIL whose significant_any=True. (62−12=50.) This is a
> summary-column artifact, not a pipeline discrepancy. For a bit-for-bit external
> re-derivation, use the per-condition raw DE_stats, not these aggregates.
> fail_primary is always consistent with its own best-condition numbers.

### novelty_flags.csv — 96 context-specific genes (blindspot 2: known vs novel)
- n_known_drugs — Open Targets known-drug count (0 = genuinely none, from a successful query)
- tractability_summary, novelty_flag (druggable_known / novel_untapped / novel_undruggable / unknown), ot_status
- All 96 have ot_status='ok' → no masked unknowns. 73 novel_untapped, 21 druggable_known, 2 novel_undruggable.

### evidence_strength.csv — 96 genes (blindspot 4: single-dataset fragility)
- n_conditions_significant, sign_consistency, n_cells_tier, evidence_strength (high/medium/low/unknown)
- evidence_caveat — single-source limitation stated on EVERY row (one Perturb-seq study, CD4+ T, 3 timepoints; within-study consistency only, NOT cross-study reproducibility)

## Prototypes
- entry_a_rank_board.html — any-gene search + funnel diagnosis (11,526), known-vs-novel badge + novel-only toggle, CSV export, plain-language tooltips, evidence badge
- entry_b_risk_evidence.html — dual-mode: Tab1 Target Safety Lookup (default, "not patient-level advice"), Tab2 Patient Upload (explicit DEMO); always-visible CD4-T context-boundary banner; evidence-strength badges

## Not built (honest scope)
- Feedback loop / community-validated targets (blindspot 5, second half) — needs a real backend + database, out of scope for a static demo.
- Patient-level recommendations — deliberately NOT provided; Entry B gives target-level evidence only.

## Review
Two adversarial rounds: R1 data_honest=True, gate reproduces to 1,235, both prototypes pass, 0 must-fix.
R2 final_accept=True, no regression, 0 CJK. Only optional item = this data-dictionary note (now added).
