# CI reproducibility guard — CD4+ T-cell Perturb-seq pipeline

This guard proves that the committed pipeline scripts, run from the committed
raw supplementary table, still reproduce the exact stage outputs recorded in a
**frozen** checksum file. It runs in GitHub Actions on every change to the
pipeline and can be run identically on a laptop.

## Files

| File | Location to commit | Role |
|------|--------------------|------|
| `reproducibility.yml` | `.github/workflows/` | The GitHub Action. |
| `verify_reproducibility.py` | `.github/scripts/` | Standalone runner — the actual guard logic. Runs locally **and** from CI. |
| `CI_REPRODUCIBILITY_README.md` | next to the workflow, or in the audit dir | This document. |

The runner and workflow reference the bundle already committed under
`docs/mvp-research/pipeline/reproducibility_audit/reproducibility_bundle/`
(pushed & merged in PR #38). **No new raw data is added** — the raw table is
published bioRxiv-preprint supplementary data, already public in the repo. CI
only reads it via `actions/checkout`.

## What the guard checks

For each of the five audited stage outputs, in **both** the Python and R
implementations:

| stage_output | produced by | key column | shape |
|---|---|---|---|
| `curated_targets` | `curated_{py,r}` → `curated_{py,r}.csv` | `index` | 33,983 × 18 |
| `gate_passing_targets` | `curated_{py,r}` → `gate_passing_{py,r}.csv` | `index` | 2,131 × 18 |
| `effect_matrix` | `processed_{py,r}` → `effect_{py,r}.csv` | `target_contrast_gene_name` | 11,526 × 4 |
| `de_matrix` | `processed_{py,r}` → `de_{py,r}.csv` | `target_contrast_gene_name` | 11,526 × 4 |
| `summary_statistics` | `statistical_{py,r}` → `summary_{py,r}.json` | `metric` | 18 × 2 |

The steps: **checkout committed raw → run the Python stage scripts and the R
stage scripts from that raw → canonicalise each output → md5 → compare to the
frozen `expected_outputs_checksums.csv` → fail on any mismatch.** All 10 checks
(5 outputs × 2 languages) must match.

### The decoy file (do not be fooled)

`curated_{py,r}` also writes a third file literally named
`curated_targets_{py,r}.csv` (the gate-passing set deduplicated to ~1,235
unique targets). **That is a decoy with no expected checksum.** The
`curated_targets` expected output is the *full* 33,983-row annotated table
(`curated_{py,r}.csv`). The runner maps outputs by role, never by matching the
`curated_targets` filename, so the decoy is never checksummed.

## Why canonicalisation, not a raw md5

A byte-for-byte md5 of a freshly written CSV **will not** match across R,
Python, or even pandas versions — float formatting, column order, NA rendering,
and row order all differ. Hashing raw float bytes would false-fail constantly.

The guard therefore implements the bundle's **documented canonicalisation**
(from `REPRODUCE.md`, "the authority") — round/sort/normalise *before* hashing:

1. **Columns** reordered alphabetically (ascending, case-sensitive).
2. **Rows** sorted ascending by the key column, then by all remaining
   (already alphabetised) columns as tie-breakers, using a **stable** sort.
3. **Cells** normalised: missing/NaN → `""`; bool → `"True"`/`"False"`;
   int → plain decimal (no `.0`); float → `format(x, ".10g")` (10 significant
   digits); everything else → its string form.
4. Write CSV: `,` separator, **no index column**, header kept, `"\n"` line
   terminator, UTF-8.
5. `md5` of those bytes = the canonical md5 compared against the frozen file.

Step 3's float rule (`.10g`) is what makes R and Python outputs hash
identically despite different native float serialization. This was verified:
both the Python and R implementations reproduce all five frozen checksums.

## Toolchain is pinned exactly

Frozen checksums require a frozen toolchain — otherwise a runtime upgrade could
change a float in the 11th significant digit and flip a hash. The workflow pins
(sourced from the bundle's `environment.md`):

- **Python** `3.11.9` (exact) — `pandas==2.3.3`, `numpy==2.4.6`, `scipy==1.17.1`
- **R** `4.5.3` (exact patch) — `tidyverse==2.0.0` (`dplyr 1.2.1`, `readr 2.2.0`,
  `tibble 3.3.1`), `jsonlite==2.0.0`

R libraries are installed at exact versions via `remotes::install_version(...)`.
The pins are declared in the `env:` block of `reproducibility.yml`; update them
there if `environment.md` ever changes.

## Frozen-checksum discipline (important)

`expected_outputs_checksums.csv` is the **source of truth and is frozen**.

- **CI never regenerates or auto-updates it.** There is no auto-update path, by
  design. The runner only *reads* the expected file.
- A **red build means output drifted** from the frozen expectation. First
  assume a bug in the pipeline change and fix the code.
- Only if the change is a **legitimate, intended** change to an output does a
  **human** update the expected file — deliberately, in the same PR, with
  review (see below).

### How to deliberately update expected checksums

Do this only when you have decided the new output is correct.

1. Make and review the pipeline change on a branch.
2. Regenerate outputs and recompute canonical md5s locally:
   ```
   python .github/scripts/verify_reproducibility.py \
       --bundle docs/mvp-research/pipeline/reproducibility_audit/reproducibility_bundle \
       --lang both --keep --verbose
   ```
   The report prints the *new* canonical md5 for each stage output (the
   `MISMATCH` lines show `got` vs the old `expected`). Confirm Python and R
   agree on the new value.
3. Edit `expected_outputs_checksums.csv` by hand, replacing only the
   `canonical_md5` (and `n_rows`/`n_cols` if the shape changed) for the outputs
   that legitimately changed. Leave every other row untouched.
4. Commit the checksum change **in the same PR** as the pipeline change, and
   explain in the PR description *why* the output changed. A reviewer signs off
   on the intent, not just the diff.
5. Re-run the guard; it should now pass.

Never paste in a hash you did not regenerate yourself, and never script an
"update the expected file" step into CI.

## Running locally

```
# both implementations (default), auto-detect the committed bundle
python .github/scripts/verify_reproducibility.py

# just Python, explicit bundle path, keep the regenerated outputs
python .github/scripts/verify_reproducibility.py \
    --bundle docs/mvp-research/pipeline/reproducibility_audit/reproducibility_bundle \
    --lang py --keep

# point at a non-default R interpreter
RSCRIPT=/path/to/Rscript python .github/scripts/verify_reproducibility.py --lang r
```

Requirements: Python 3.11 with the pinned `pandas`/`numpy` for the Python path,
and `Rscript` (R 4.5.3 with the pinned libs) on `PATH` — or set `$RSCRIPT` — for
the R path. Exit code `0` = all match; `1` = a mismatch or a stage failed to
run; `2` = usage/environment error (e.g. bundle not found).

## Trigger

The workflow runs on `push` and `pull_request` whenever the pipeline scripts,
the raw bundle, the expected-checksum file, the workflow, or the runner change.
It also supports manual `workflow_dispatch`. Permissions are `contents: read` —
the guard never writes back to the repo.
