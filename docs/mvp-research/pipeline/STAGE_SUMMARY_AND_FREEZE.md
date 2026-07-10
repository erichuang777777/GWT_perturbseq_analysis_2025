# Stage summary & freeze report

**Frozen:** 2026-07-10 · **Scope:** 7-stage pipeline + 3 recent work packages · **Mechanism:** manifest freeze (immutable artifact version_ids + md5)

Each asset below is pinned to a specific artifact version_id. Version_ids are immutable — a frozen id always resolves to exactly these bytes (md5 in FREEZE_MANIFEST.csv). Re-running any stage produces a NEW version and never overwrites a frozen one.

---

## Stage 01 - Raw

**Result.** 33,983 rows = 11,526 unique targets x up to 3 culture conditions; source md5 f5cf2e07. Aggregated DE statistics, the single upstream input for everything downstream.

**Verification.** Frozen. Source of truth; not recomputed.

| asset | version_id | md5 | shape |
|---|---|---|---|
| DE_stats.suppl_table.csv | `11c6348b-f46d-48a3-8c22-7ae328f40c6c` | `f5cf2e070bc8…` | (8,) |

## Stage 02 - Curated

**Result.** Quality gate (n_cells>=200 & significant & !offtarget & DE>=50) applied and deduplicated: 33,983 curated rows -> 2,131 gate-passing rows -> 1,235 unique gate-passing targets. R==Python row-level (0 mismatch).

**Verification.** Frozen + R/Python parity verified + third-party reproduced.

| asset | version_id | md5 | shape |
|---|---|---|---|
| curated_targets.csv | `506b62e3-4ad0-42a0-ac4d-b779a31f8121` | `5346cdd6e272…` | (8,) |
| gate_passing_targets.csv | `024cefa5-3a8f-4e4e-b82a-51f356a03960` | `5efd16dec06b…` | (8,) |

## Stage 03 - Processed

**Result.** effect_matrix and de_matrix pivots, both 11,526 targets x 3 conditions (34,578 data cells each). R==Python cell-level, max abs diff 3.6e-15, NA patterns agree.

**Verification.** Frozen + R/Python parity verified + third-party reproduced.

| asset | version_id | md5 | shape |
|---|---|---|---|
| effect_matrix.csv | `e168ccb9-6d5d-427c-a5cf-93f388492f2f` | `dfb61e0c3a65…` | (8,) |
| de_matrix.csv | `a58b4ba0-da04-46b9-9ad2-21a3e632615c` | `3e6c03522620…` | (8,) |

## Stage 04 - Statistical

**Result.** 18-metric summary_statistics + 3-condition up/down DE sums. 24-metric R<->Python cross-validation all PASS. Key: nde_median 2, effect range -58.5..7.09, ncells_median 539, corr(nDE,nDownstream)~1.0.

**Verification.** Frozen + R/Python cross-validation (24/24 PASS) + third-party reproduced.

| asset | version_id | md5 | shape |
|---|---|---|---|
| summary_statistics.csv | `419a18fa-4229-4b87-a373-1de23f79952d` | `f562a9c49313…` | (8,) |
| condition_stats.csv | `aeb64a9d-02e2-4e32-98d4-0c49a525db1c` | `5ffe137dffe3…` | (8,) |

## Work package - Blindspot fixes

**Result.** Six developer->user blindspot fixes. gene_gate_diagnosis: all 11,526 genes with per-gene 'why filtered' (5,227 too-few-DE / 3,233 not-sig / 1,129 too-few-cells / 702 off-target). novelty_flags: 96 ctx genes = 73 novel-untapped / 21 druggable-known / 2 novel-undruggable. evidence_strength: 91 high / 5 med, single-source caveat every row.

**Verification.** Frozen + 2-round review (data_honest, 0 must-fix).

| asset | version_id | md5 | shape |
|---|---|---|---|
| gene_gate_diagnosis.csv | `8fd09c08-3ac6-48cc-99c9-95f78c0a1eb2` | `228c68bf4b46…` | (8,) |
| novelty_flags.csv | `a7aa43c7-512f-49d8-bbf4-3f335329302c` | `ef693e5e6853…` | (8,) |
| evidence_strength.csv | `240e5948-6d34-4c5d-b974-c02800ffccc5` | `2a0064ec4093…` | (8,) |

## Work package - Methodological validation

**Result.** Three GB10-free methodological validations. benchmark: ranking recovers known regulators, AUROC 0.85, positives median rank 36 vs housekeeping 964. dropout: 237 gate-failed genes are high-constraint essential-suspects (platform blind spot). baseline: 96 ctx candidates = 84 true regulators / 11 expression artifacts / 1 unknown.

**Verification.** Frozen + 2-round methodological review (final_accept).

| asset | version_id | md5 | shape |
|---|---|---|---|
| benchmark_results.csv | `b5899e1f-e6ae-4de8-8438-7be8def535dd` | `4de9797db023…` | (8,) |
| dropout_diagnosis.csv | `a76505a5-a3d7-4d2b-b6c7-0d6d2689b88f` | `1573a70a7873…` | (8,) |
| context_specific_corrected.csv | `26f49368-549f-4923-bf86-f02ca670180f` | `6ba620783550…` | (8,) |

## Work package - Reproducibility audit

**Result.** Third-party reproducibility audit. Per-stage R<->Python parity row/cell-level (0 mismatch). Self-contained bundle (raw + 6 scripts + checksums + REPRODUCE.md). Independent third party recomputed 5/5 stages to byte-identical canonical md5 in BOTH R and Python (10/10). Two adversarial review rounds: final accept.

**Verification.** Frozen + 2-round rigor review (final_accept, R+Python both executed).

| asset | version_id | md5 | shape |
|---|---|---|---|
| cross_validation_results_en.csv | `f7ad6ebe-09ef-45e8-89aa-a5d1041fd512` | `3c9f21204854…` | (8,) |
| parity_01_02.csv | `14e94a94-1868-41db-b26d-8c22cbeaabc8` | `181be5d62b93…` | (8,) |
| parity_03.csv | `fbc97a90-bde1-4662-a515-31c6e858aeca` | `c502b9d74fe8…` | (8,) |
| figure_registry.csv | `af9b6263-e6d9-43f0-89b8-614761a4cce7` | `d125a1e62ee3…` | (8,) |
| reproducibility_bundle_v2.tar.gz | `1ccbbc49-2d43-4e2d-8706-05bd23f8c424` | `aef56de3d1c2…` | (8,) |

---
## Freeze integrity
To verify a frozen asset: resolve its version_id, compute md5, compare to FREEZE_MANIFEST.csv. All 18 assets resolved OK at freeze time. The raw input (01_raw, md5 f5cf2e07) is the sole upstream source; all downstream stages are reproducible from it via the reproducibility bundle.
