# BACKEND COMPLETENESS & REPRODUCIBILITY AUDIT
### Perturbase CD4+ T-cell Perturb-seq platform — backend data layer

**Generated:** 2026-07-11 16:44 UTC
**Scope:** 10 core backend data artifacts + 2 reproducibility three-element files
(DATA_DICTIONARY.md, reproduction_report.md), plus the standalone
`reproduce_signed_tracks.py` script.
**Method:** For every file, the three reproducibility elements were checked —
(a) DEFINITION (presence in DATA_DICTIONARY.md), (b) SCRIPT (lineage code
present, `extraction_pending=False`, inputs listed), (c) RESULT (artifact loads,
expected shape). Three files (gate_passing, summary_statistics,
signed_ranking_v2) were RE-RUN OFFLINE in an isolated namespace from their
lineage/standalone script and compared cell-by-cell to the frozen artifact.

---

## 1. Three-element status — one row per file

| # | file | definition (DD) | script vid | script chars | extraction | inputs | loads (shape) | reproducible offline | caveat |
|---|------|:---:|---|---:|:---:|---:|---|---|---|
| 1 | `raw_DE_stats` | **No** | `11c6348b-f46d-48a3-8c22-7ae328f40c6c` | 334 | done | 0 | Yes (33983, 16) | N/A (raw input) | root input; not in DD |
| 2 | `curated_targets` | **No** | `506b62e3-4ad0-42a0-ac4d-b779a31f8121` | 871 | done | 1 | Yes (33983, 18) | not re-run (derived; out of scope) | not in DD |
| 3 | `effect_matrix` | **No** | `e168ccb9-6d5d-427c-a5cf-93f388492f2f` | 1073 | done | 1 | Yes (11526, 4) | not re-run (derived; out of scope) | not in DD |
| 4 | `de_matrix` | **No** | `a58b4ba0-da04-46b9-9ad2-21a3e632615c` | 1053 | done | 1 | Yes (11526, 4) | not re-run (derived; out of scope) | not in DD |
| 5 | `gate_passing` | **No** | `024cefa5-3a8f-4e4e-b82a-51f356a03960` | 883 | done | 1 | Yes (2131, 18) | **YES — exact (diff 0.0)** | not in DD (only inline lineage) |
| 6 | `summary_statistics` | **No** | `419a18fa-4229-4b87-a373-1de23f79952d` | 2710 | done | 1 | Yes (18, 2) | **YES — exact (diff 0.0)** | not in DD |
| 7 | `condition_stats` | **No** | `aeb64a9d-02e2-4e32-98d4-0c49a525db1c` | 1150 | done | 1 | Yes (3, 4) | not re-run (out of scope) | not in DD; not verified here |
| 8 | `signed_ranking_v2` | Yes | `729315c2-a086-4988-a12c-ecf15a1b5ffb` | 3901 | done | 5 | Yes (10851, 28) | **YES — via reproduce_signed_tracks.py** (int/label exact, float ≤4.4e-16) | captured lineage SUPERSEDED — use reproduce_signed_tracks.py |
| 9 | `downstream_enrichment_v2` | Yes | `c454a7d1-11f0-49f1-94a6-f8bc692e682b` | 8788 | done | 4 | Yes (12975, 10) | partial (p_value/fdr yes; Reactome cols EXTERNAL/SNAPSHOT/CURATED) | Reactome external snapshot dependency |
| 10 | `lincs_concordance` | Yes | `be0150d9-d316-4f49-bfd7-b2fe82d0f999` | 2116 | done | 3 | Yes (4, 6) | numeric cols yes; caveat GIVEN | DEMO (4 rows) |

**Reproducibility three-element files**

| file | version_id | role | present |
|------|-----------|------|:---:|
| DATA_DICTIONARY.md | `3e6d85a2-be90-434e-8230-6da2c9c2126d` | DEFINITION element (18.5 KB; covers signed_ranking_v2, downstream_enrichment_v2, lincs_concordance + Level-4 tracks) | Yes |
| reproduction_report.md | `936d38a0-ee8b-410a-a825-7273bddf30e6` | RESULT element (column-level PASS log, exit 0) | Yes |
| reproduce_signed_tracks.py | `5f151a60-dbf5-475a-b866-84fd24aa8588` | SCRIPT element (14.6 KB, standalone, argparse) | **Yes (saved as artifact)** |

---

## 2. Offline recompute-verification (third-party reproducibility proof)

Each target was re-run from raw inputs + script alone, in an isolated kernel
namespace, and compared cell-by-cell to the frozen artifact.

### 2.1 `gate_passing` — REPRODUCED EXACT
- Source: captured lineage (input: `DE_stats.suppl_table.csv`).
- Recomputed shape (2131, 18) == frozen (2131, 18); columns identical.
- **max abs numeric diff = 0.0; non-numeric mismatches = 0** across all 18 columns.
- A third party with raw DE_stats + this script reproduces gate_passing bit-for-bit.

### 2.2 `summary_statistics` — REPRODUCED EXACT
- Source: captured lineage (input: `DE_stats.suppl_table.csv`).
- 18/18 metrics matched; **max abs diff = 0.0** (incl. floats effect_min/median/max,
  corr_nde_ndownstream, frac_logde_lt1).

### 2.3 `signed_ranking_v2` — REPRODUCED (offline columns) — with a lineage caveat
- **Important:** the *captured lineage* for this artifact is the **superseded /
  wrong script** — it emits only 13 columns and uses a `directionality_index > 0.1`
  threshold for `footprint_class`, whereas the delivered 28-column artifact uses a
  pure **SIGN rule** on DI. Reproduction was therefore performed with the correct
  standalone artifact **`reproduce_signed_tracks.py`** (`5f151a60-dbf5-475a-b866-84fd24aa8588`), run against
  the two raw parquet shards.
- Raw matrix loaded: **2,056,424 hit rows over 10,851 targets** (matches DD).
- Cell-by-cell vs frozen (merged on `target_gene`, all 10,851 rows retained):

  | column group | result |
  |---|---|
  | `n_hits, n_up, n_down, signed_net`, `target_ensembl_id` | exact (0 mismatch) |
  | per-condition counts (`n_up/n_down/signed_net _Rest/_Stim8hr/_Stim48hr`) | exact (0) |
  | `directionality_index` | max abs diff 1.1e-16 |
  | `up_down_ratio` | max abs diff 1.8e-15 |
  | `net_logfc` / per-condition `net_logfc_*` | max abs diff 4.4e-16 |
  | `binom_p` | max abs diff 1.1e-16 |
  | `binom_fdr` | max abs diff 2.2e-16 |
  | `footprint_class`, `directionality_class` | 100% label match |
  | `signed_rank` | permutation of 1..N, orders signed_net DESC, exact on distinct-signed_net rows (intra-tie integer not recoverable — documented) |
  | `primary_rank` | exact within in_gate_shortlist; NaN outside |
  | `in_gate_shortlist` | **EXTERNAL** — upstream gate flag (1,235 targets), an INPUT, not recomputed |

  All 26 offline-reproducible columns match within stated tolerance; only the
  documented EXTERNAL/label-tie columns are not bit-exact (and are correctly
  flagged as such).

**Frozen-consistency note (given):** gate_passing / DE_stats per-cell consistency
was previously verified (max abs diff 0). This audit independently re-ran 3 files
offline and re-confirmed reproducibility from raw + script.

---

## 3. MISSING / GAPS and remediation

| # | gap | severity | affected files | remediation |
|---|-----|----------|----------------|-------------|
| G1 | **7 of 10 core files have NO entry in DATA_DICTIONARY.md.** DD documents only signed_ranking_v2, downstream_enrichment_v2, lincs_concordance (+ Level-4 tracks). raw_DE_stats, curated_targets, effect_matrix, de_matrix, gate_passing, summary_statistics, condition_stats have no column-level DEFINITION element. | **High** | raw_DE_stats, curated_targets, effect_matrix, de_matrix, gate_passing, summary_statistics, condition_stats | Extend DATA_DICTIONARY.md with a section per file (name/definition/formula/units/reproducible-from/caveat), same schema already used for the signed files. Their derivations are simple and fully captured in lineage, so this is documentation work only. |
| G2 | **signed_ranking_v2 captured lineage is the WRONG/superseded script** (13 cols, `DI>0.1` footprint rule). A third party replaying the artifact's own lineage would NOT reproduce the delivered 28-column file. | **High** | signed_ranking_v2 | Re-save signed_ranking_v2 with `reproduce_signed_tracks.py` as its lineage, or add a lineage note pointing to the `5f151a60-dbf5-475a-b866-84fd24aa8588` artifact as the authoritative build script. (The correct script exists and reproduces exactly — verified in §2.3.) |
| G3 | **Reactome external-state dependency** for downstream_enrichment_v2: `pathway_id`, `pathway_name`, `overlap` were fetched LIVE and not snapshotted at build; `pathway_size_bg` is SNAPSHOT-only; `expression_artifact_flag` is a CURATED heuristic (~94.5% keyword-reachable, NOT fully recomputable). | Medium | downstream_enrichment_v2 | The remediation snapshot `reactome_pathway_snapshot.csv` (1,807 pathways) is documented in the reproduction_report; confirm it is saved as an artifact and referenced as an input so the lookup-reproducible columns are recoverable. Record Reactome version/date. |
| G4 | **condition_stats not recompute-verified** in this audit (out of the 3-file scope) and not in DATA_DICTIONARY. | Low | condition_stats | Lineage present (1,150 chars, input = raw); add DD entry and run the same offline recompute check to close it. |
| G5 | **signed_rank intra-tie integer not recoverable** (build row order lost; up to 1,004 rows share a signed_net value). | Low (documented) | signed_ranking_v2 | Accept as documented limitation; the ordering property and distinct-row ranks are reproduced. No action beyond the existing caveat. |
| G6 | **lincs_concordance is DEMO-level (4 rows)** with a free-text GIVEN caveat column. | Low (documented) | lincs_concordance | Numeric columns reproduce from `lincs_demo_signatures_4genes.csv`; flag clearly as demo, not production concordance. |

**Resolved / not a gap:** `reproduce_signed_tracks.py` IS saved as an artifact
(`5f151a60-dbf5-475a-b866-84fd24aa8588`) — the reproduction_report's SCRIPT element is present, contradicting
any assumption it was unsaved. All 12 files load, all have non-empty lineage code
with `extraction_pending=False`.

---

## 4. Bottom line

- **Files checked (data + repro):** 12 (10 core data + DATA_DICTIONARY + reproduction_report).
- **Offline recompute-verified:** 3/3 requested (gate_passing, summary_statistics, signed_ranking_v2) — all reproduce within tolerance (two bit-exact, one exact-on-integers/labels with floats ≤4.4e-16).
- **Third-party reproducible from raw + script?** YES for the three verified files
  — **conditional on using `reproduce_signed_tracks.py` (not the captured lineage)
  for signed_ranking_v2**, and accepting the documented EXTERNAL/SNAPSHOT/CURATED
  columns of downstream_enrichment_v2 as non-offline.
- **Open gaps:** 6, of which 2 are High (G1 DD coverage of 7 files; G2 wrong
  captured lineage for signed_ranking_v2). None block reproduction of the numeric
  scientific content; all are documentation / lineage-hygiene fixes.
