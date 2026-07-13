# Threshold Sensitivity Analysis — Methods

## Objective
Descriptive robustness assessment of the CD4+ T-cell Perturb-seq target shortlist
under variation of the two count-based gate thresholds. This is a **descriptive
robustness analysis only**; the frozen baseline shortlist of **1,235 unique
targets** is never redefined.

## Data
- Input: raw DE_stats supplementary table, 33,983 rows = 11,526 unique targets x
  up to 3 culture conditions (Rest / Stim8hr / Stim48hr).
- Join / identity key: per-target gate evaluated on `target_contrast_gene_name`
  (equivalently `dropout_diagnosis.target == gene_gate_diagnosis.target_contrast_gene_name`).
- Row distribution: 11,086 targets have 3 condition-rows, 285 have 2, 155 have 1.

## Gate definition (shared, cross-track consistent)
A target **passes** a gate at (C, D) if **ANY** of its condition-rows satisfies:

    n_cells_target >= C  AND  ontarget_significant  AND  NOT offtarget_flag  AND  n_total_de_genes >= D

- **Baseline gate = (C=200, D=50)**, additionally requiring n_total_de_genes >= 50
  at the passing row. Baseline shortlist = **1,235 unique targets (FROZEN)**.
  Reproduced exactly by this pipeline.

## NA handling (verified)
The four gate fields — `n_cells_target`, `ontarget_significant`, `offtarget_flag`,
`n_total_de_genes` — have **ZERO NA values** (verified: NA count = 0 for all four).
Therefore **every gate failure is on a measured value; none is due to missing data.**

## Sweep
C in {100, 150, 200, 250, 300, 400} x D in {30, 40, 50, 75, 100} = **30 combinations**.
Baseline = (200, 50).

## Survivorship-corrected stability (review fix #1)
`pass_fraction` is computed over the **FULL universe of all 11,526 targets**, not
only baseline-passers, as the fraction of the 30 combos each target passes. Each
target is annotated `in_baseline` (bool). Two instability counts are reported to
instrument **both directions**:

- **(a) Unstable INCLUSIONS** = baseline-passing targets with pass_fraction < 0.9:
  **653** of 1,235 baseline targets (52.9%).
  These are inside the frozen shortlist but drop out under many threshold choices.
- **(b) Unstable EXCLUSIONS** = targets NOT in baseline that pass in >= 50% of combos:
  **0**. (For context, the maximum pass_fraction among any
  non-baseline target is 0.40; 71 non-baseline targets reach >= 40% but none reach
  50%. 546 non-baseline targets pass at least one combo.)

Interpretation: churn is asymmetric. A substantial minority of the frozen shortlist
is threshold-sensitive (would leave under stricter gates), but **no excluded target
is a strong majority-passer** — nothing outside the baseline clears the >=50% bar,
so the baseline is not systematically excluding robust targets.

## Set overlap (review fix #2)
For each combo, Jaccard similarity and intersection count of its target set vs the
frozen 1,235-target baseline set are reported in `threshold_sensitivity_grid.csv`.
Count delta alone is insufficient; membership churn is captured by Jaccard. Note
several combos have small |delta| yet Jaccard well below 1.0 (e.g. C=250,D=40 has
delta=-24 but Jaccard=0.825), confirming that net-count similarity hides membership
turnover.

## Rank stability (review fix #3) — CAVEAT: test is structurally degenerate
Rank score = each target's **max n_total_de_genes across its conditions** (the
platform's context-specific DE count per target, as specified). Spearman rho of
target ordering vs baseline is computed over the intersection of passing targets;
it is **rho = 1.00 for all 30 combos** (median = 1.00) and recorded in the grid.

**This rho = 1.00 is a mathematical identity, NOT an empirical result, and provides
zero evidence about reordering.** The chosen rank score is *target-intrinsic*: each
target carries one fixed score that does not depend on (C, D). Over the intersection
of shared targets, the baseline ordering key and the combo ordering key are literally
the same numbers, so Spearman of that vector against itself is 1.0 by construction —
it cannot return any other value for any subset. A genuine rank-stability test would
require a **combo-specific** score (a rank that is recomputed per threshold, e.g. from
condition-rows that actually pass at that (C, D)); the intrinsic score specified here
does not admit such a test. We therefore make **no claim** that thresholding does or
does not reorder the top targets — that question is out of reach of this metric.

What the sweep *does* establish (fix #1, fix #2) is that thresholding drives
**membership churn** (Jaccard 0.47-1.00), not that ordering is preserved.

## Core / Boundary / Fragile classes (review fix #4)
- **CORE**: pass_fraction >= 0.9
- **BOUNDARY**: 0.1 <= pass_fraction < 0.9
- **FRAGILE**: 0 < pass_fraction < 0.1
- (NEVER: pass_fraction = 0)

**These 90% / 10% cutpoints are ARBITRARY CONVENTIONS**, stated explicitly as such.
The full pass_fraction histogram (figure panel B) is provided so the reader can see
where the cutpoints land relative to the empirical density. Full-universe class
counts: CORE=582, BOUNDARY=1166,
FRAGILE=33, NEVER=9745.
Among the 1,235 baseline passers: CORE=582, BOUNDARY=653, FRAGILE=0.

## Genetic-constraint note (definition provided for cross-track consistency)
High genetic constraint is defined at the **ORGANISM level** (loss-of-function
intolerance, NOT T-cell essentiality): **LOEUF < 0.35 OR pLI >= 0.9**. This
definition is recorded here for cross-track consistency; constraint annotation is
not applied within this descriptive threshold-sensitivity track.

## Outputs
- `threshold_sensitivity_grid.csv` — 30 rows (C, D, n_targets, delta_vs_baseline,
  jaccard_vs_baseline, intersect_count, spearman_rho_vs_baseline)
- `target_stability.csv` — per-target over full universe (target, pass_fraction,
  in_baseline, stability_class)
- `threshold_sensitivity_figure.png` — 3-panel (A heatmap, B pass_fraction histogram
  with bands, C Spearman rho distribution)

## Guardrail
Descriptive robustness only. The frozen 1,235-target baseline is not redefined.
