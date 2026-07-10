# Third-Party Reproducibility Verification — v2

**Bundle:** `reproducibility_bundle_v2.tar.gz`
**Role:** independent third-party auditor. No prior knowledge of the pipeline.
Recomputed all stage outputs from the raw input only; no pipeline output
artifacts outside the bundle were read.

## Method
- Extracted the bundle and followed `REPRODUCE.md` verbatim.
- Sole raw input: `raw/DE_stats.suppl_table.csv` (33,983 data rows).
- Ran the **Python** implementations of each stage in order
  (curated → processed → statistical), then the **R** implementations.
- For each of the 5 audited stage outputs, applied the canonicalisation
  documented in `expected_outputs_checksums.csv` / `REPRODUCE.md`
  (alphabetise columns → stable-sort by key + tie-breakers → normalise every
  cell → CSV with `,`, no index, `\n` terminator, UTF-8 → md5) and compared to
  the expected `canonical_md5`.
- **Decoy handled:** used `curated_py.csv`/`curated_r.csv` (33,983 rows) for
  `curated_targets`, NOT the similarly-named 1,235-row `curated_targets_*.csv`.
- **Statistical stage:** verified the audited **18-metric core**
  (`summary_*.json`) only; the separate `*_extended.json` (6 per-condition
  DE-gene sums) is not checksum-audited and was excluded.

## Per-stage results

| Stage output | key | rows (exp) | cols (exp) | python_md5_match | r_md5_match |
|---|---|---|---|---|---|
| curated_targets      | index | 33,983 (33,983) | 18 (18) | ✅ True | ✅ True |
| gate_passing_targets | index | 2,131 (2,131) | 18 (18) | ✅ True | ✅ True |
| effect_matrix        | target_contrast_gene_name | 11,526 (11,526) | 4 (4) | ✅ True | ✅ True |
| de_matrix            | target_contrast_gene_name | 11,526 (11,526) | 4 (4) | ✅ True | ✅ True |
| summary_statistics   | metric | 18 (18) | 2 (2) | ✅ True | ✅ True |

### Canonical md5 (recomputed = expected for all)
| Stage | expected canonical_md5 | python | R |
|---|---|---|---|
| curated_targets      | `7b8fbe8caebbbb5fedcfea53d55059e3` | match | match |
| gate_passing_targets | `779e8746ec416096de860dbf9cc20480` | match | match |
| effect_matrix        | `dab5c0badeb31d4f3636644f04147d59` | match | match |
| de_matrix            | `6b2ed5e514ddb4fdc9fcc8c5ee284e6e` | match | match |
| summary_statistics   | `4cebfd24630a6e5cae1c43b23b23dbf2` | match | match |

## Notes on cross-language robustness
- Byte-level CSVs differ between R and Python (float formatting, NA rendering),
  as REPRODUCE.md predicts; the canonical checksum is the authority and matches.
- `corr_nde_ndownstream` differs at the 15th significant digit between R
  (`0.9999984688704547`) and Python (`0.9999984688704552`). Under the
  `.10g` (10 significant digits) canonical float format both round to
  `0.9999984689`, so the summary_statistics checksum matches for both.

## Verdict
**PASS.** Bundle is complete and self-contained. All 5 stage outputs reproduce
from raw for BOTH the Python and R implementations: 10/10 canonical-md5 checks
match the expected values, with correct row/column shapes. No mismatches or
failures observed.
