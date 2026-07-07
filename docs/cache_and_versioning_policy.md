# Cache & Version Invalidation Policy (C6)

**Status:** living policy · **Last updated:** 2026-07-07

This documents how the toolkit's caches (`sources/target_tool_cache/`) and version fields behave today,
and the concrete rule for when something should be rebuilt or refetched. Every claim below is checked
against the actual code (`target_card_api.py`, `external_evidence_cache.py`), not aspirational.

---

## 1. `target_cards.csv` builds: immutable, not invalidated in place

Every `POST /api/build` (`target_card_api.py`) mints a **new** `dataset_id` (`uuid4()`) and writes to a
new `sources/target_tool_cache/<dataset_id>/` directory — it never overwrites or mutates an existing
build. There is no automatic staleness check that forces a rebuild when an upstream input file changes;
a rebuild only happens when a client explicitly calls `/api/build` again.

**What every build stamps** (`_persist_metadata`, written to `metadata.json`):

| Field | What changes it | Real current value |
|---|---|---|
| `data_version` | `_data_version_fingerprint()` — name + mtime + size of every input file (`DE_stats`, `guide_kd`, `library_metadata`, benchmark, `sample_metadata`) | changes automatically the moment any upstream CSV is touched |
| `dataset_version` | Manual bump in `target_card_api.py::DATASET_VERSION`, only when the upstream GWT release itself changes (a new bioRxiv version, a new manuscript DOI) | `gwt_marson2025/bioRxiv-10.64898-2025.12.23.696273v1`; only stamped on `origin="gwt_reference"` builds, never user uploads |
| `engine_version` | Manual bump in `target_card_api.py::ENGINE_VERSION`, whenever `build_target_cards.py`, `readiness_engine.py`, `calibration.py`, or `external_evidence_cache.py` change scoring/engine behavior | `1.3.0` |
| `schema_version` | Manual bump in `target_card_api.py::CARD_SCHEMA_VERSION`, whenever `out_cols` in `build_target_cards.py` adds/removes/renames a column | `card_schema/v2` |
| `signature_set_version` | `_data_version_fingerprint([SEED_MODULES])` — automatic, from the seed-module CSV's own mtime/size | recomputed per build |

**Rule: when to trigger a new `/api/build`:**
1. Any of `DE_stats.suppl_table.csv`, `guide_kd_efficiency.suppl_table.csv`,
   `sgrna_library_metadata.suppl_table.csv`, `sample_metadata.suppl_table.csv`, or the clinical-benchmark
   CSV changes on disk (`data_version` fingerprint will differ from any prior build's — compare before
   assuming an existing `dataset_id` is still current).
2. `ENGINE_VERSION` is bumped (a code change to scoring/readiness/calibration logic) — old builds keep
   their stamped `engine_version` so they're identifiable as pre-change, but they are not retroactively
   recomputed.
3. `CARD_SCHEMA_VERSION` is bumped — any consumer hard-coding a column-name assumption should check this
   field rather than assume `target_cards.csv`'s shape is stable across builds.
4. A user upload is re-approved/re-merged with a different column mapping — this always produces a new
   `usr_<import_id[:8]>_<uuid>` dataset_id already (see `import_manager.py`), not an in-place update.

**What is NOT auto-invalidated:** an old `dataset_id`'s `target_cards.csv` on disk stays exactly as it
was built, forever, even after `ENGINE_VERSION`/`CARD_SCHEMA_VERSION` bump — by design, so a
previously-shared dataset_id/report link keeps returning the same numbers. Treat an old `dataset_id` as a
frozen snapshot, not a live view; rebuild explicitly for a fresh one.

---

## 2. External evidence cache: TTL-based, per-gene

`external_evidence_cache.py` snapshots one JSON file per gene at
`sources/target_tool_cache/_evidence/<gene>.json`.

- **Default TTL: 30 days** (`TTL_SECONDS_DEFAULT = 30 * 24 * 3600`) — external evidence (trials,
  literature, genetics) changes slowly enough that daily/hourly refetching is unnecessary and would
  waste the connectors' rate limits.
- **Staleness check** (`_is_stale`): compares `fetched_at` (ISO-8601, UTC) against `now()`; a snapshot
  older than the TTL is treated as stale and refetched on the next `build_evidence_for_gene(..., force=False)`
  call.
- **Force refresh:** `build_evidence_for_gene(gene, force=True)` (or `POST /api/evidence/build` with
  `force=True`) refetches regardless of TTL — use when a specific gene's trial/literature landscape is
  known to have changed (e.g. a new trial was just registered) and 30 days is too long to wait.
- **Per-source `source_status`**: `"ok"` vs `"unavailable"` is tracked *per source* inside one gene's
  snapshot (`clinical_trials`, `literature`, `open_targets` can each independently be `"ok"` or
  `"unavailable"` in the same fetch) — a partial connector outage doesn't invalidate the sources that did
  succeed, and doesn't get silently retried as if it were fresh (an `"unavailable"` snapshot is still
  subject to the same 30-day TTL before automatic retry, not retried on every request).
- **Batch endpoint cap:** `POST /api/evidence/build` is capped at `MAX_EVIDENCE_GENES = 50` genes per
  call and runs via `BackgroundTasks`, never blocking the request thread — see the Fable-review fix in
  `docs/IMPLEMENTATION_PLAN.md`'s hardening-pass section for why.

---

## 3. Local static overlay files: no cache, no TTL, no auto-refresh

Files like `sources/broad_effect_genes.txt`, `metadata/gene_lists/*.tsv`, and the disease-association
export are read fresh from disk on every process start (`load_gene_set()`, `load_overlays()`,
`load_disease_associations()`) — they are not cached with a TTL because they're static, checked-in
files, not live fetches. **If any of these is ever regenerated from a live source**, add the same
`fetched_at` + source-version stamping pattern used in `external_evidence_cache.py`, and update
`docs/data_governance_checklist.md` §3 accordingly — today there is no automated way to tell how current
one of these lists is beyond `git log` on the file itself.

---

## 4. Runtime cache directory lifecycle (`sources/target_tool_cache/`)

| Path pattern | Contents | Git status | Cleanup policy |
|---|---|---|---|
| `sources/target_tool_cache/<uuid>/` (GWT-reference builds) | `target_cards.csv`, `target_report.{html,md}`, `metadata.json` | Untracked by default (`.gitignore`); the one existing demo dataset (`e7ecd8d5-...`) was committed intentionally before the ignore rule was added and stays tracked | No automatic cleanup — a research session accumulates one directory per `/api/build` call. Manually prune old `dataset_id` directories that are no longer referenced by any shared link/report. |
| `sources/target_tool_cache/usr_*/` | User-upload merge outputs | `.gitignore`d | Never commit. These are per-session working data for one researcher's upload; delete when the upload workflow is done, or leave for that researcher's continued use — there is no multi-user access control (`docs/data_governance_checklist.md` §4), so don't assume isolation beyond directory naming. |
| `sources/target_tool_cache/imports/*/` | Staged-but-not-yet-approved import files | `.gitignore`d | Same as above; a staged import that's never approved just sits here — no automatic expiry exists today. If this becomes a real disk-usage problem, add a `staged_at`-based sweep (not built now, since it isn't one yet). |
| `sources/target_tool_cache/_evidence/<gene>.json` | External evidence snapshots | **Tracked** (intentional seed data, per `docs/IMPLEMENTATION_PLAN.md`) | Governed by the 30-day TTL in §2, not manual cleanup — stale snapshots are refetched, not deleted. |
| `sources/target_tool_cache/_overlays/*.parquet` | §1.12 membrane-tractability + GTEx safety-window overlay snapshots (`candidate_genes_membrane.parquet`, `gtex_per_tissue.parquet`) | **Tracked** (intentional real-data snapshots, public-database-derived per `docs/data_governance_checklist.md`) | Static, no TTL — these are point-in-time snapshots of external public databases (HPA/UniProt/CSPA/GTEx), not live-refreshed. Replace manually if a newer snapshot is obtained; `safety_overlay.py`'s loaders read whatever file is present with no version check today (a gap noted, not silently accepted — same caveat as static overlay lists in §3). |

---

## 5. Quick reference: "is this number still current?"

1. Check the provenance block / `metadata.json` for the `dataset_id` in question:
   `engine_version`, `schema_version`, `dataset_version`, `data_version`, `built_at`.
2. Compare `engine_version`/`schema_version` against the current values in `target_card_api.py` (§1
   table above). If they differ, the numbers reflect an older scoring/column contract — rebuild for a
   current view.
3. For any external-evidence panel, check `fetched_at` on the gene's snapshot against the 30-day TTL
   (§2) — if it's older, a refresh is due (automatic on next natural fetch, or force it).
4. Static overlay lists (§3) have no version stamp today — treat them as "as current as this checkout of
   the repo," and check `git log <file>` if you need to know exactly when.
