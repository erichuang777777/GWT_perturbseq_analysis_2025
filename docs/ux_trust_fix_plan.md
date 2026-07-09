# UX / Trust Fix Plan — closing the "developer-complete vs user-incomplete" gap

**Status:** proposal (pre-build). Derived from the 4-persona blind-spot read
(bench immunologist, API consumer, skeptical PI, first-run/ops).

**Root cause (one line):** the project's honesty discipline (`unknown != 0`,
descriptive/decision separation, measured-empty vs not-fetched, coverage
sparsity) is real but lives in the **backend and in `REPRODUCIBILITY.md`** — the
user only ever reads chips and cards. Every fix below **moves existing honesty to
the point of use**; almost none of it invents new science.

**Invariants that constrain every item here (unchanged):**
- `unknown != 0` — no fix may impute a number where data is absent.
- **Descriptive/decision wall** — nothing added here may feed `readiness_call`,
  `overall_readiness_stage`, `_stage()`, or `statistical_evidence_grade`. All new
  UI is presentational/explanatory only, and stays inert through
  `compute_readiness` (regression locks must still pass).
- **Never fabricate** — coverage numbers, ages, and definitions must come from
  real data/live computation or be stable factual copy, never hardcoded guesses
  that can silently drift.
- **Additive-only**, full `pytest` green before each commit, **frontend isolation**
  (only HTTP/JSON via `_api_get`; no `src/3_DE_analysis` imports from `frontend/`),
  draft PRs, provenance stamped.

---

## Wave 0 — P0 BUG: the dossier concept waterfall shows the IL2RA fixture for every gene

### Problem (confirmed)
`frontend/dashboard/pages/2_標的檔案_target_dossier.py:581-585` renders
`build_waterfall_figure(SAMPLE_REPORT.get("concept_profile", []))`
**unconditionally**, under the gene-specific header "③ CD4 概念剖面(concept
profile)". `SAMPLE_REPORT` is the hardcoded IL2RA demo fixture in
`concept_waterfall.py`. There is **no** per-target signed activation profile in
the API (`/api/modules/{dataset_id}` returns per-target module *hits*, not a
signed waterfall — the in-code comment at `:577-580` admits this). So **every
gene's dossier shows the identical IL2RA-shaped waterfall.** Two different genes
produce a pixel-identical "profile" chart → catastrophic trust failure the moment
a user notices.

### Fix (honest, minimal)
The page must not present a fixture as *this gene's* profile. Options, in order of
preference:

- **0a (recommended, ship now):** Remove the fixture waterfall from the per-target
  dossier entirely. Keep only what is genuinely about this gene: the **live
  per-target module-hits table** (already present at `:590-593`) with the honest
  `_not_available(...)` empty state (`:594-595`). Replace the chart with a one-line
  note explaining that a signed per-gene activation waterfall is not available from
  the current screen contract, and that module *hits* are shown instead. The
  waterfall component itself stays untouched — it remains correct on the
  individual/COMPASS layer where `SAMPLE_REPORT` is a labeled demo.
- **0b (only if 0a feels too bare):** Keep a waterfall **only** when real per-gene
  activation data exists; otherwise render nothing. Since no such endpoint exists
  today, 0b == 0a until a real `/api/concept_profile/{dataset_id}/{target}` is built
  (out of scope; see Wave 3 backlog).

### Tests
- Update `tests/test_dashboard_smoke.py` (or add a focused test) asserting the
  dossier page renders **without** a hardcoded-fixture chart, and still renders the
  title + module-hit section, offline.
- Add a guard test: the string `SAMPLE_REPORT` / `build_waterfall_figure` must not
  appear on the per-target dossier's concept-profile path (regression lock so the
  fixture can't creep back onto the entity page).

### Risk
Very low. Deletes a misleading element; keeps the honest table. Frontend-only.

---

## Wave 1 — P1 over-trust + interpretability (frontend-first, additive, no new science)

Highest leverage. Everything here surfaces facts the backend already knows.

### 1a. Glossary / "what this does NOT mean" for the decision words
- **Problem:** `advance / validate / watchlist / deprioritize` and `grade` are
  shown as bold decision chips with **zero in-product definition**. "advance"
  reads as "move into a program"; it only means the target cleared
  `_stage()→R3` on a single screen. No glossary anywhere in the UI.
- **Fix:** one shared, reusable glossary component (in `ui_chips.py` or a new
  `frontend/dashboard/glossary.py`) rendering stable factual copy:
  - each call = one line of what it means + one line of what it does **not** mean
    ("advance ≠ clinically validated / ≠ ready for a program; = cleared the R3
    statistical gate on one CRISPRi screen").
  - `grade` = "measures statistical power & reproducibility of the measurement,
    **not** biological importance; a high grade can just mean many cells / high
    expression."
  - Rendered as an always-available expander on the dossier decision section and
    on the Overview "readiness call" chart, plus an `ℹ` affordance next to each
    chip. Copy is stable fact, not drifting data → safe as static UI text.
- **Wall check:** pure presentation; feeds nothing.

### 1b. Distinguish "under-called by MISSING data" from "tested and WEAK"
- **Problem:** when `crossdonor_correlation_mean` is NaN (86% of rows), translation
  is capped by *absent measurement*, but the chip is identical to a target we
  measured and found non-robust. Non-statisticians read "translation 3" as
  "moderate," not "we couldn't measure this."
- **Fix:** where a call/sub-score is capped, detect whether the capping input was
  `unknown` vs measured-low (the info is already in `readiness_reasons` /
  the raw fields the API returns) and render a distinct visual token:
  `⚠ 因缺少測量而下修 (capped by missing data)` vs `測得偏低 (measured low)`.
  No new number is computed — we only relabel what the reason string already says.
- **Wall check:** reads existing `readiness_reasons`; changes no decision.

### 1c. Coverage-at-the-glance for sparse domains (safety / genetics / disease)
- **Problem:** gnomAD constraint covers 15/11,526 genes (0.1%), GTEx 45.7%,
  disease universe = 13, LINCS = 4. The confident chips + dropdowns don't carry
  this at the point of the glance; sparsity is a caption at best.
- **Fix (honest = live numbers, not doc-copied):** add a small backend meta
  endpoint `GET /api/meta/coverage` that **computes** real coverage counts from
  the loaded reference tables (genes with non-unknown gnomAD / GTEx / disease /
  LINCS ÷ total) and returns `{domain: {covered, total, pct, as_of}}`. The dossier
  and Disease Translator render a coverage badge next to each sparse chip
  ("gnomAD constraint: 15/11,526 基因 · 0.1% 覆蓋") sourced from that endpoint.
  Disease Translator additionally shows "共 N 個疾病" and, on a miss, distinguishes
  "不在這 N 個疾病內" from "查無關聯".
- **Why an endpoint, not hardcoded:** keeps `never-fabricate` — numbers track the
  real data and can't drift out of sync with a doc.
- **Wall check:** read-only meta; feeds no score.

### 1d. "Data as of / preprint, not peer-reviewed" + staleness age
- **Problem:** UI shows raw `fetched_at`/`built_at` but never computes an **age**
  or flags stale (>30-day TTL); the dataset is a **preprint** pin and the UI never
  says so. 8-month-old sample fixtures render with only a timestamp.
- **Fix:** (i) a single "資料時點 / data as of <date> · 來源:preprint(未經同儕審查)"
  line in the dossier header/footer; (ii) compute age from `fetched_at` and show a
  `⚠ 可能過期 (older than 30d TTL)` badge when stale. `date.today()` is available in
  the frontend (allowed there); age is derived, not fabricated.
- **Wall check:** presentation only.

### 1e. Structural-limits banner (single screen / one cell type / N≈3 donors)
- **Problem:** the entire tool rests on ONE CRISPRi screen, CD4⁺ only, 3
  conditions, 3 donors — never restated at the decision.
- **Fix:** a compact, un-hideable one-liner in the dossier decision section
  ("整個工具基於單一 CRISPRi screen · CD4⁺ · 3 conditions · N≈3 donors · 假設生成用途"),
  reusing the existing forced-caveat pattern. Link out to `REPRODUCIBILITY.md`.

### Wave 1 tests
- Glossary component unit test (renders all four calls + grade, each with a
  "does not mean" line).
- `/api/meta/coverage` known-answer test (gnomAD covered==15, disease==13, etc.,
  computed from the reference dataset; skipif dataset absent — same guard as
  `test_triage_target_api.py`).
- Missing-vs-weak token test (NaN cross-donor → "capped by missing data" token;
  measured-low → "measured low" token).
- Staleness test (a >30d `fetched_at` yields the stale badge; fresh does not).
- Full `compute_readiness` regression locks must remain green (proves the wall).

---

## Wave 2 — P2 cold-start / run / ops (get a newcomer from clone → running)

### 2a. Declare runtime dependencies (currently undeclared)
- **Problem:** no `requirements.txt` / `pyproject` / lock anywhere; `environment.yaml`
  is the scanpy analysis env and has **no** fastapi/uvicorn/streamlit/pydantic.
  A maintainer literally cannot start the API from any declared manifest. The
  frontend README references `frontend/dashboard/requirements.txt` — verify it
  exists; if not, that command is broken.
- **Fix:** add pinned `requirements.txt` (backend: fastapi, uvicorn, pydantic,
  pandas, numpy, pyyaml, requests, python-multipart, …) and confirm/create
  `frontend/dashboard/requirements.txt` (streamlit, plotly, pandas, requests).
  Keep `environment.yaml` for the heavy analysis pipeline; the toolkit runtime is
  a separate, light manifest.

### 2b. One-command run
- **Problem:** no Docker/compose/Makefile; starting = two manual terminals from a
  README buried in `frontend/`.
- **Fix:** a `Makefile` (or `run.sh`) with `make api`, `make dashboard`, `make dev`
  (both), and `make test`. Optional lightweight `docker-compose.yml` (api +
  dashboard) as a follow-up, not blocking.

### 2c. Empty-state onboarding (fresh clone has zero datasets)
- **Problem:** with no prebuilt dataset the dashboard `st.stop()`s
  (`target_card_dashboard.py:573-579`) → blank app, no guidance.
- **Fix:** replace the bare stop with an onboarding panel: "No dataset yet — build
  the reference cards with `<command>` or upload a DE table," linking the build
  route and the upload flow. Purely a better empty state.

### 2d. Top-level README quickstart + honesty pointer
- **Problem:** root `README.md` is the old manuscript readme; no quickstart;
  `REPRODUCIBILITY.md` (the best trust artifact) is unlinked from the app.
- **Fix:** add a "Quickstart (toolkit)" section (install → build reference →
  run API → run dashboard) and link `REPRODUCIBILITY.md` from both the README and a
  dashboard "About / limitations" expander.

### Wave 2 tests / checks
- CI-style smoke: `pip install -r requirements.txt` resolves; `import target_card_api`
  succeeds; `make test` runs the suite.
- Empty-state: AppTest with no dataset shows the onboarding panel (not a bare stop),
  no exception.

---

## Wave 3 — backlog (explicitly NOT in this plan; needs product decisions or new science)

- Real per-target concept-activation endpoint (would let 0b show a true per-gene
  waterfall) — new science/plumbing.
- Auth / CORS / multi-user / deployment / HTTPS; `approved_by` is hardcoded.
- Persistence: cache is gitignored; deep-links use transient UUID `dataset_id`
  (stable dataset slugs needed for shareable links).
- Upload flow completion (only target/guide-evidence merge today; 25MB cap).
- Pagination + surfaced caps (targets-500 / triage-1000 / modules-1000 silently
  truncate).
- i18n (mixed EN/繁中 UI; Chinese-only docs), save/bookmark/PDF-cite, mobile.
- External benchmark / calibration track record ("of past advance-calls, how many
  validated?") — needs ground-truth data the project doesn't have.

---

## Recommended first PR
**Wave 0 + Wave 1a/1b/1e** (the trust-critical, frontend-only, no-endpoint subset):
kills the fixture-waterfall bug and puts definitions + missing-vs-weak + structural
limits in front of the user, with zero backend change and zero wall risk. Waves
1c/1d (need the `/api/meta/coverage` endpoint + staleness) and Wave 2 (ops) follow
as separate PRs.
