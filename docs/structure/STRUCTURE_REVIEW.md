# STRUCTURE_REVIEW.md — Adversarial review of PR #93 (whole-repo structuralize)

**Repo:** erichuang777777/GWT_perturbseq_analysis_2025
**Branch:** claude/whole-repo-structuralize-freeze-isolation
**Commit reviewed:** 215f73362298795a808b85a58d5b6233767d1640 (zipball; blob SHAs verified byte-exact against GitHub git API)
**Reviewer:** independent, grounded on the pulled branch tree/blobs.

---

## Verdict summary

| Claim | Verdict | One-line reason |
|-------|---------|-----------------|
| (a) every phase FROZEN (pins reproduce) | **FAIL** | Shipped validator exits **1**: 9/97 modules drift on the very commit they pin. |
| (b) every module separately editable | **PASS** | 97 modules, disjoint longest-prefix ownership; `--freeze` regenerates cleanly. |
| (c) editing one module cannot contaminate another phase | **PARTIAL** | Guard *logic* is sound by construction on a clean baseline, but is **unusable in the shipped state** — the 9 pre-existing drifts poison every `--isolation` run. |
| (d) no invented/empty modules | **PASS (1 phantom token)** | 0 empty/invented modules; but 1 dir token (`STRUCTURE_REVIEW.md`) points at a file that 404s on the branch. |

**Overall: the structure is well-built but was NOT re-frozen against the committed tree. It does not ship green.**

---

## Step 1 — Run shipped verifier

```
$ python scripts/validate_freeze_unified.py
[freeze] 97 modules · 9 unexpected drift · 0 missing · 0 allowed-drift
    ✗ drift: P3_statistics::level4_external_validation
    ✗ drift: P5_informative_figure_server::webserver_public_assets
    ✗ drift: P6_frontend_devops::devops_build_config
    ✗ drift: P6_frontend_devops::frontend_spa_src
    ✗ drift: P7_documentation::documentation_index
    ✗ drift: P7_documentation::perturbation_validation_plan
    ✗ drift: P0_shared_infra::shared_test_utils
    ✗ drift: P8_readme_reference::mvp_research_root
    ✗ drift: P7_documentation::structure_governance
EXIT = 1
```

**Does NOT exit 0.** The freeze does not reproduce on the commit it claims to pin. Extraction is faithful (e.g. `docs/documentation_index.md` local git-blob `e32f5eea…` == GitHub API `e32f5eea…`), so this is a real stale-pin defect, not an unzip artifact.

Root cause (from file-count deltas): the manifest was frozen against a *different* working tree than commit 215f7336. Evidence:
- `structure_governance` pins **3** files incl. `docs/structure/STRUCTURE_REVIEW.md`; branch has only **2** (that file returns 404).
- `mvp_research_root` pins **17** files; branch tree has **83** under `docs/mvp-research/`.
- `level4_external_validation` pins **7**; live **12**. `shared_test_utils` pins **53**; live **54**.
- The docs themselves are "grounded at HEAD **0522a2df**", not the PR commit 215f7336.

## Step 2 — pytest

```
$ python -m pytest tests/test_freeze_unified.py -v
tests/test_freeze_unified.py::test_unified_freeze_verifies FAILED   [ 33%]
tests/test_freeze_unified.py::test_partition_is_disjoint PASSED     [ 66%]
tests/test_freeze_unified.py::test_partition_is_total  PASSED       [100%]
1 failed, 2 passed
```

**2 of 3 pass.** The failing one is `test_unified_freeze_verifies` — same 9-drift cause as Step 1. The two partition invariants (disjoint + total) genuinely hold.

## Step 3 — Partition audit (real counts)

Ran the shipped `partition()` over all 1251 partition-scope repo files:
- **Files owned by >1 module: 0** (overlap_count = 0) — ownership is disjoint.
- **Orphan files (no owner, excluding the manifest itself): 0** — coverage is total.
- Coverage = **1251/1251 (100%), 1 allowed orphan = the manifest**.

Partition is mathematically clean. This is what makes the isolation guarantee sound *in principle*.

## Step 4 — Invented / empty-module check

- Modules owning zero files after partition: **0**.
- Modules whose dir tokens match zero files at all: **0**.
- **No invented or empty modules.** Claim (d) holds at the module level.
- **BUT** one *phantom token*: `P7_documentation::structure_governance` lists `docs/structure/STRUCTURE_REVIEW.md`, which does not exist on the branch (GitHub API → 404). The module isn't empty (it owns 2 other files), but it pins a nonexistent path — which is exactly why it drifts.

## Step 5 — Contamination test (core claim c)

Picked 3 modules in 3 different phases: `P1_data_aggregation::01_raw_data`, `P4_figure_visualization::figure_metadata`, `P9_limitation::KNOWN_LIMITATIONS`.

**On the SHIPPED (stale) baseline:** for all 3, `--isolation <edited module>` returned **exit 1** (WRONG — should be 0), and `--isolation <other module>` also returned exit 1. Cause: the 9 pre-existing drifts are always reported as leaks, so the guard cannot distinguish a legitimate edit from contamination. **In the state as shipped, the contamination guard is unusable.**

**On a CLEAN re-frozen baseline** (`--freeze` → verify exits 0), the same 3 edits behaved correctly:
- `--isolation <edited>` → **exit 0** for all 3.
- `--isolation <other>` → **exit 1** for all 3, and the output **named the actually-edited module** as the leak in all 3 cases.

Conclusion: the guard *logic* is correct and the longest-prefix partition really does prevent one module's edit from moving another's freeze value. The mechanism is sound; the shipped **pins** are stale, which defeats it in practice. Hence claim (c) = PARTIAL.

## Step 6 — Contract-gap check

Scored the manifest's structured fields (— / blank = missing):
- **All three (input + output + validation_authority) non-blank: 88/97.**
- output_contract: 97/97. validation_authority: 97/97. input_contract: **88/97** (9 missing).
- The 9 missing input_contract are all documentation/reference leaves where an input contract is arguably N/A: `P7_documentation::{explainer, researcher_guide, slides, wiki}` and `P8_readme_reference::{DATA_LICENSE, LICENSE, README, project_decision_log, provenance_registry}`.
- No phase is "mostly empty"; the weakest is **P8_readme_reference (3/8 input contracts)**, expected for license/readme leaves.

Contract coverage is a genuine strength of this PR.

## Step 7 — Stale-claim check

**PASS.** The doc does **not** repeat the false "perturbase_frontend does not exist (404)" claim. It explicitly corrects it:
- `PHASE_MODULE_MAP.md` L41: the old 404 claim is "STALE: it EXISTS … with 146 files".
- `MODULE_ISOLATION_POLICY_v2.md` L361–367: `perturbase_frontend` documented as a real module.
- `FREEZE_MANIFEST_UNIFIED.csv` row 30: `P5_informative_figure_server,perturbase_frontend, dir=docs/mvp-research/perturbase_frontend/ …, 146 files`.
- The directory exists on the tree (`figure_scripts/`, `figures_en/`, `catalog/`) and this module verifies clean (not in the drift set).

---

## Issues found (ranked)

1. **[BLOCKER] Freeze does not reproduce — 9/97 modules drift; validator + pytest both red on the shipped commit.** The manifest was frozen against a different tree (HEAD 0522a2df / a dirty checkout) than PR commit 215f7336. Claim (a) FAIL.
2. **[BLOCKER] Contamination guard unusable as shipped** — because the baseline already has 9 drifts, `--isolation X` returns exit 1 for every X, including the legitimately-edited module. Claim (c) only holds after a clean re-freeze.
3. **[HIGH] Phantom pin:** `structure_governance` pins `docs/structure/STRUCTURE_REVIEW.md`, which 404s on the branch.
4. **[MED] Stale file-counts** in 4 modules: `mvp_research_root` (17 vs 83), `level4_external_validation` (7 vs 12), `shared_test_utils` (53 vs 54), `structure_governance` (3 vs 2).
5. **[LOW] Stale docstring:** `validate_freeze_unified.py` says "94 modules"; actual = 97.
6. **[LOW] 9 modules lack an input_contract** (doc/reference leaves; acceptable but should be explicitly "—/NA" with a rationale rather than blank).

## Concrete fixes

1. On the exact PR commit, run `python scripts/validate_freeze_unified.py --freeze` and commit the regenerated `FREEZE_MANIFEST_UNIFIED.csv`. This alone turns Steps 1, 2, 5 green and makes the `--isolation` guard usable. (Verified locally: after `--freeze`, verify exits 0 and all 3 contamination probes pass.)
2. Either create `docs/structure/STRUCTURE_REVIEW.md` (this review) so the `structure_governance` token resolves, or drop it from that module's `dir`. Re-freeze after.
3. Add a CI gate that runs `--freeze` in `--check` mode (fail if it would change the manifest) so pins can never be committed stale again — i.e. freeze must be regenerated in the same commit that changes any owned file.
4. Fix the "94 modules" docstring → 97.
5. For the 9 blank input_contracts, write an explicit "— (leaf doc, no upstream input)" so the field is intentional, not empty.


---

## POST-FIX STATUS (2026-07-12) — all blockers resolved

The two blockers and the HIGH/MED/LOW items in this review were fixed by re-freezing against the exact PR tree and committing the missing file. Re-verified on the final commit:

| Claim | Before | After fix |
|---|---|---|
| (a) every phase frozen | FAIL — 9/97 drift, verify exit 1 | **PASS** — `validate_freeze_unified.py` exit 0, `0 unexpected drift · 0 missing` |
| (b) every module editable | PASS | **PASS** — 97 disjoint modules |
| (c) no cross-phase contamination | PARTIAL — drifts poisoned the guard | **PASS** — 3-phase probe: `--isolation <edited>` exit 0, `--isolation <other>` exit 1 naming the edited module, restore exit 0 |
| (d) no invented modules | PASS (1 phantom token) | **PASS** — `structure_governance` now pins the committed `STRUCTURE_REVIEW.md`; 0 phantom, 0 empty |

**Fixes applied:**
1. Re-ran `--freeze` on the exact PR tree and committed the regenerated manifest → verify green, pytest 3/3, all contamination probes pass.
2. Created `docs/structure/STRUCTURE_REVIEW.md` (this file) so `structure_governance`'s pin resolves (was 404).
3. Stale file-counts corrected by the re-freeze (they are recomputed from the live tree).
4. Docstring in `validate_freeze_unified.py` corrected `94 modules` → `97 modules`.
5. 9 leaf doc/reference modules given explicit `— (no upstream module; leaf doc/reference)` input contracts instead of blank.

**CI gate:** `tests/test_freeze_unified.py::test_unified_freeze_verifies` fails on any future stale pin — pins cannot be committed drifted.

**Partition (final):** 100% coverage, every repo file owned by exactly one module, 0 overlap, the manifest itself the only allowed non-frozen file.
