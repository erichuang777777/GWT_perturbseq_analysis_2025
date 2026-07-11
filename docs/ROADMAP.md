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
- **Fix stale build wiring** (see KNOWN_LIMITATIONS "stale build wiring"):
  - point `Makefile` `dashboard`/`dev` at the React `frontend/webserver` (Vite),
    or remove the dead Streamlit targets;
  - switch `export_real_data.py` to the canonical 39-col `a6bba17b` dataset and
    regenerate the portal export;
  - reconcile the `dataset.ts` import path vs the committed `public/real-dataset.json`.
- **Refresh `data_dictionary.md` code-path references** (`build_target_cards.py::build_cards_frame`
  / `readiness_engine.py` → `core/cards.py` / `core/readiness.py`) — OF-7 residual.

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
