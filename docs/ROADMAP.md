# Roadmap (post-freeze future work)

Future improvements identified during the release freeze. **None of these are in
scope for the freeze itself** — they are recorded here so the frozen release has an
honest forward pointer. Paired with `docs/KNOWN_LIMITATIONS.md`.

## Near-term (frontend / upload workstream — separate PRs)

- ✅ **Standalone live upload tool** (approach "C") — **shipped**: `GET /upload`
  (`src/3_DE_analysis/api/routers/upload_ui.py`) drives the live FastAPI
  `/api/imports/*` flow (upload → column-mapping → approve → merge → real
  readiness), kept separate from the static portal so the frozen portal stays
  untouched. Guarded by `tests/test_upload_ui.py`.
- ✅ **Fix stale build wiring** — **shipped** (see KNOWN_LIMITATIONS "stale build
  wiring", now resolved): `Makefile` `web`/`dev` point at the React
  `frontend/webserver` (Vite); `export_real_data.py` switched to the canonical
  39-col `a6bba17b` dataset and the portal export was regenerated; the
  `dataset.ts`/`public/real-dataset.json` path was re-verified as already
  correct (only a stale comment needed fixing).
- **Refresh `data_dictionary.md` code-path references** (`build_target_cards.py::build_cards_frame`
  / `readiness_engine.py` → `core/cards.py` / `core/readiness.py`) — OF-7 residual.

## Better use of the paper's own in-repo data (identified in the coverage audit)

Higher-value than external DBs: data the paper already ships in-repo but the tool
underused.

- ✅ **Signed directional module-effect scoring** (Tier-1 ①) — **shipped**:
  `signed_module_effect.py` + `GET /api/signed_module_effect/{gene}`. Uses the in-repo
  `full_signed_DE` table (per-downstream-gene `log_fc`) to answer "does knocking this
  target down activate or repress each concept module's program?" — recovering master
  regulators with the correct sign (GATA3→Th2, TBX21→Th1, FOXP3→Treg as activators).
  Descriptive only, sparse (`unknown != 0`), guarded by `tests/test_signed_module_effect.py`,
  freeze-pinned. Does NOT reproduce the paper's network inference (see KNOWN_LIMITATIONS).
- ✅ **Surface the paper's own regulator nominations** (Tier-1 ②) — **shipped** for the
  regulator-coefficient tables: `paper_regulators.py` + `GET /api/paper_regulators/{gene}`
  serve the paper's `*_regulator_coefficients` tables verbatim (per gene: signed `coef_mean`,
  `coef_rank` 0-1 percentile, and the paper's own known/novel flag), keyed by gene, across
  polarization + aging signatures × context. Recovers the paper's own top calls (GATA3
  polarization rank 1.0 known; BCL6 a novel nomination). Descriptive only, `unknown != 0`,
  guarded by `tests/test_paper_regulators.py`.
- ✅ **Surface the paper's autoimmune-cluster enrichment** (Tier-1, autoimmune axis) —
  **shipped**: `autoimmune_clusters.py` + `GET /api/autoimmune_clusters/{gene}` explode the
  paper's cluster-level `cluster_autoimmune_enrichment_results` (negative controls excluded)
  so it's gene-queryable — "does this target sit in a perturbation cluster enriched for an
  autoimmune disease, in which context, at what odds ratio?" Recovers textbook autoimmune
  genes against textbook diseases (CTLA4 → Hashimoto's/RA/celiac/T1DM/SLE). Framed honestly
  as **guilt-by-cluster-membership**, not a direct gene→disease association; descriptive
  only, `unknown != 0`; guarded by `tests/test_autoimmune_clusters.py`. **Still not surfaced**
  (lower priority): the raw signature DE tables (`Th2_Th1_polarization_signature_DE`,
  `CD4T_aging_signature_DE`).
- ✅ **Full gnomAD constraint** (Tier-2, biggest external win) — **shipped**: replaced the
  15-gene demo seed (0.13% coverage) with an authentic full-genome gnomAD **v2.1.1** by-gene
  LOEUF/pLI snapshot (19,155 genes, one row per gene, chrX included), covering 11,267 / 11,526
  targets (~97.8%). Built reproducibly by
  `src/3_DE_analysis/data_acquisition/build_gnomad_constraint_overlay.py` from gnomAD's public
  GCS bucket; v2.1.1 chosen over v4.1 because the v4.1 flat distribution reachable in-env was
  autosomes-only (would have dropped FOXP3/MED12/CD40LG). Still descriptive-only, `unknown != 0`,
  never caps `readiness_call`; guarded by `tests/test_safety_overlay.py`. The composite safety
  axis is now limited by the GTEx breadth overlay (~5k genes), not gnomAD.
- **Full Open Targets Genetics / GWAS Catalog** (Tier-2, aligns with the paper's
  autoimmune-GWAS emphasis): expand disease association beyond the current 13 curated
  indications / 17% coverage.

## Medium-term (evidence & modeling)

- **Real safety + membrane/tractability overlay** (§1.12): wire CellxGene safety
  validation + internal membrane-protein library + TCGA/GTEx to fill the currently
  near-all-`unknown` `safety_window_score` / `tractability_modality`.
- **v2 hypothesis generator** (§1.10): LINCS signature reversal, mechanism graph,
  perturbation prediction — **benchmark-only, never feeds decisions** (same
  guardrail as the existing `src/10_ml_perturbation_prediction/` tracks).

## Longer-term (platform & real-data scale)

- **Multi-user platform** (§1.8): Supabase/Postgres + auth + per-user workspace,
  replacing the single-user file cache.
- **Run the cell-level data on real hardware**; add a COMPASS-style
  individual-sample → concept projection (P2/P4); vectorize the per-row (34k-row)
  operations that currently use `iterrows()`/`apply` (see `wiki/Tech-Debt.md`
  B.8–B.9).
