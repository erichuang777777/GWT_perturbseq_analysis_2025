# Frontend design — researcher & clinical-evidence personas

**Status:** implemented (2026-07-10) · **Decision confirmed:** clinical-evidence *lookup* persona
only (no patient records/history) — see §1. `target_card_dashboard.py`'s six tabs became nine
standalone researcher pages (§4 -- the extra count vs. this doc's original R1-R7 is 整合 Triage,
免疫優先, and Pathway+Clinical's module hits, added to the dashboard after this doc's first
draft); the existing individual-concept-profile page and two new pages became the clinical-evidence
group (§5). Page numbering is `01`-`10` (researcher) / `11`-`13` (clinical), zero-padded so
Streamlit's string-sort keeps them in the intended order — not the `1`-`7` / `8`-`10` gap this doc
originally sketched.

> Research / hypothesis-generating tool — **NOT clinical software**. This design adds a second
> persona's *navigation and framing*, not a second product with different rules. Every constraint in
> `docs/data_governance_checklist.md` and the existing `individual_concept_profile.py` demo (request-only,
> no identifiers, non-persisted, forced caveat) applies unchanged to everything below.

---

## 0. Why this doc exists

The dashboard today (`frontend/dashboard/`) is one implicit persona: a researcher who already knows the
screen and wants to slice target cards. The ask was to also support someone who arrives with a *clinical*
question — "what does this sample's expression pattern suggest?", "this patient has disease X and drug Y
is on the table, what's the evidence?" — without turning the tool into something it has explicitly and
repeatedly decided not to be (`docs/mvp-research/MODULE3_病人層假設引擎_DEMO設計.md`: population statistics
≠ patient prediction; CRISPRi knockdown ≠ pharmacological intervention).

**Audience for this iteration:** an internal demo to the company's Head of [organization], using this
project's existing open/public data (the GWT screen, Open Targets, ClinicalTrials.gov, UK Biobank
aggregates) to show *what's possible* with this toolkit's evidence base — not a production clinical
deployment and not a request for new proprietary or patient data. This sharpens, rather than relaxes, the
non-clinical framing in §1: a leadership demo is exactly the setting where overclaiming what's real would
be most costly, so every guardrail below (forced caveats, honest `available: False`/zero-trial states,
no identifiers) stays intact and visible in the demo, not stripped out for polish.

This doc is presentation-layer only. It changes no backend scoring/readiness logic, and (per the
decision below) requires exactly one new API route — everything else is UI composition over existing
endpoints.

---

## 1. Constraints this design must respect

These are not proposals — they are already true of this repo and this design must not regress any of
them:

1. **Not clinical software.** No output here is a diagnosis, treatment, dose, drug choice, or efficacy
   prediction, for any persona. Every clinical-evidence page carries a forced, non-hideable caveat banner
   (same mechanism as `pages/1_個體概念剖面_探索demo.py`'s `_forced_caveat_header()`).
2. **No auth, no multi-user backend.** `docs/IMPLEMENTATION_PLAN.md` §1.8 explicitly deprioritizes
   Supabase/Postgres + auth + workspaces. **This design does not require reviving that work.** Every
   individual-level input (a sample's expression vector, a free-text disease/drug query) stays
   request-only and is never written to `sources/target_tool_cache/` or any other disk location — the
   same guarantee `docs/data_governance_checklist.md` §2a already enforces for the concept-profile
   endpoint, extended to the new page in §5.2.
3. **Population-level ≠ patient-level**, always labeled as such where population genetics data
   (`/api/population-hypothesis/{gene}`) is shown.
4. **No patient identifiers, ever.** No name/MRN/date-of-birth/demographic field is accepted anywhere in
   this design — inputs are limited to gene symbols, expression values, disease names, and drug names.
5. **Descriptive vs. decision separation.** Nothing a clinical-evidence page shows feeds
   `readiness_call` / `overall_readiness_stage` — same causal-independence rule the mechanism graph and
   safety overlays already follow.

**Explicitly out of scope** (would require revisiting constraint 2, and is a separate, much larger
project if ever pursued): persistent per-patient case records, saved matching history across sessions,
longitudinal tracking, login/accounts, role-based access control. If a real clinical deployment is ever
wanted, that is a follow-on decision gated on the auth/DB work in `docs/IMPLEMENTATION_PLAN.md` §1.8 —
not something this design should quietly grow into.

---

## 2. Two personas, one backend

| | Researcher | Clinical-evidence lookup |
|---|---|---|
| Who | Someone analyzing the CD4 Perturb-seq screen itself | Someone arriving with a specific gene/sample or disease+drug question, who doesn't need the screen's internals |
| Wants | Rank/filter/compare targets, inspect readiness + calibration, build/merge datasets, export | Paste one sample's expression *or* one disease+drug pair, get transparent evidence back |
| Current entry point | `target_card_dashboard.py` (Overview/Target Explorer/Pathway+Clinical/Imports/Export/Disease Translator tabs) + `pages/2_標的檔案_target_dossier.py` | `pages/1_個體概念剖面_探索demo.py` (partial — framed as a generic demo, not a persona) |
| Missing today | Nothing structural — reorg only | A disease×drug evidence page (backend function exists, unexposed); a clear "this is the clinical-lookup section" framing |

Both personas hit the **same** unauthenticated FastAPI app (`src/3_DE_analysis/api/app.py`). There is no
backend permission boundary between them — there can't be one without constraint §1.2 changing — so the
split is purely an **information-architecture decision in the frontend**: which pages a visitor sees
first and how the same underlying data is framed for their question. Nothing stops a researcher from
opening a clinical-evidence page or vice versa, same as today.

---

## 3. Navigation redesign

**Reference mockup:** `frontend_persona_mockup.html` (clickable HTML prototype — persona switch, a
feature list per persona in a left rail, and a dashboard→case-study drill-down on every page) visualizes
the target interaction model below. It is a *design reference*, not the implementation: it's a static
single-file mockup with client-side show/hide, not a Streamlit app.

**Left-rail pattern (what the mockup shows):** a persistent left rail with (top) a two-way persona switch
— Researcher / Clinical evidence — and (below it) that persona's feature list; the main pane always shows
one feature at a time, structured top-to-bottom as **program pulse → readiness/quality signal → a named
case study** (a real worked example, drilled into), never dashboard-only or detail-only. Every page opens
with a one-line user story (§3a) so the "why this page exists" is never separated from the page itself.

**Streamlit implementation of that pattern:** keep the single Streamlit app (per `docs/server_northstar.md`'s
already-confirmed "reinforce Streamlit, not React" decision). Two ways to realize the persona-switch rail,
in order of preference:
- **Preferred, if the pinned Streamlit version is ≥1.36:** `st.navigation`/`st.Page` with a persona radio
  in `st.sidebar` driving which `st.Page` list is passed in — this gets the mockup's single-rail,
  instant-switch behavior natively.
- **Fallback (any Streamlit version):** group the sidebar into two labeled sections using Streamlit's
  native numeric-prefix page ordering — no dependency on a Streamlit version bump:

```
frontend/dashboard/
  target_card_dashboard.py                    # Home: landing + persona picker, no tabs left here
  pages/
    1_研究者_總覽_overview.py                   # NEW: extracted from target_card_dashboard.py's "Overview" tab
    2_研究者_標的探索_target_explorer.py         # NEW: extracted from the "Target Explorer" tab
    3_研究者_標的檔案_target_dossier.py          # existing target_dossier.py, renumbered — unchanged content
    4_研究者_校準與穩健性_calibration.py          # NEW: extracted from the "Pathway + Clinical" tab's calibration section
    5_研究者_疾病標的翻譯_disease_translator.py   # NEW: extracted from the existing "Disease Translator" tab
    6_研究者_資料集上傳合併_upload.py             # NEW: extracted from the "Imports" tab (~line 253-420)
    7_研究者_匯出_exports.py                     # NEW: extracted from the "Export" tab
    8_臨床證據_個體概念剖面.py                    # existing page 1, renamed + moved into the clinical group
    9_臨床證據_疾病藥物證據配對.py                 # NEW: wraps the new API route (§5.2)
    10_臨床證據_群體遺傳查詢.py                    # NEW: population-hypothesis lookup, promoted out of the
                                                 #   dossier page into its own clinical-facing page (§5.3)
```

The `1`–`7` vs `8`–`10` prefix gap is deliberate: it visually clusters "researcher" pages together and
"clinical evidence" pages together in Streamlit's auto-generated sidebar, with room to insert more pages
into either group later without renumbering everything. This is a bigger split than "extract one Imports
tab" (§7 of the original draft) — flattening `target_card_dashboard.py`'s six tabs into six standalone
pages is the direct Streamlit-native answer to "one feature per left-nav entry, not buried in a tab
strip," which the mockup's flat rail makes concrete. Each extracted page keeps its existing API calls
verbatim (`_api_get`/`_api_post` helpers move to a small shared `frontend/dashboard/api_client.py` so
seven pages don't each redefine them) — this is code motion, not new logic.

### 3a. User stories per page

One story anchors each page — the same line the mockup prints under every page's title. A story that
can't be stated this plainly is a signal the page is trying to do two jobs at once.

| # | Page | User story |
|---|---|---|
| R1 | Program overview | As a researcher, I want a single view of where every screened target stands, so I can spot where the program's attention should go next. |
| R2 | Target explorer | As a researcher, I want to filter and rank targets by condition, stage, and evidence grade, so I can shortlist candidates worth a closer look. |
| R3 | Target dossier | As a researcher, I want every piece of evidence for one target in one traceable page, so I can justify an advance / watchlist / deprioritize call. |
| R4 | Calibration & robustness | As a researcher, I want to see whether this ranking actually recovers known successful drug targets, so I can trust the score before acting on it. |
| R5 | Disease → target translator | As a researcher, I want to start from a disease name instead of a gene, so I can find which screened targets are already implicated in it. |
| R6 | Dataset upload & merge | As a researcher, I want to bring my own DE results through the same scoring engine, so I can compare my screen on equal footing with the reference dataset. |
| R7 | Exports | As a researcher, I want a versioned, provenance-stamped export, so results stay reproducible outside this tool. |
| C1 | Scope & guardrails | As a clinical reviewer, I want to know exactly what this tool can and can't answer before I use it, so I never mistake a hypothesis for a recommendation. |
| C2 | Individual concept profile | As a clinical reviewer, I want to see which immune programs one sample's expression pattern activates, so I can generate a transparent, auditable hypothesis — not a black-box score. |
| C3 | Disease × drug evidence match | As a clinical reviewer, I want to check whether a candidate drug has real trial evidence for this specific disease, so I don't assume a drug works just because it hits the right gene. |
| C4 | Population genetics lookup | As a clinical reviewer, I want independent population-level genetic evidence for a gene, so I have a second, checkable line of support beyond the screen itself. |

Every page follows the same three-part shape (visible in the mockup): **program pulse** (stat tiles /
distribution, answering "where do things stand right now") → **the working view** (filterable list,
input form, or reasoning detail) → **case study** (one named, real worked example drilled all the way to
the bottom, using this repo's own data — PLCG1, IL2RA + rheumatoid arthritis, the Backman burden numbers
— never a placeholder). This is deliberate: a stat tile alone invites "so what," and a case study alone
has no way to show scale — together they answer both "how big is this" and "what does one instance
actually look like."

**Landing page (`target_card_dashboard.py`, now nav-only):** two cards/buttons — "Researcher workspace"
and "Clinical evidence lookup" — each a one-line description + link to the first page in that group.
This is framing only (both are always reachable via the sidebar regardless); it exists so a first-time
clinical-evidence visitor isn't dropped into a target-ranking table that assumes screen familiarity.

Splitting `target_card_dashboard.py`'s six tabs into six standalone pages (R1–R7 above; `Pathway +
Clinical` splits into R4 Calibration and part of R3's Mechanism-graph tab) is a bigger move than the
original draft's "just extract Imports," but it's still pure code motion — `target_card_dashboard.py` is
893 lines of already-separable `st.tabs(...)` bodies, each already talking to the API only through the
existing `_api_get`/`_api_post` helpers. No handler logic changes; only which file a tab's body lives in
and what the sidebar calls it.

---

## 4. Researcher workspace

No functional change to behavior — a structural change to *where* each tab lives (§3). Every researcher
page keeps calling the same API endpoints `target_card_dashboard.py` already calls today; `pages/3_...
target_dossier.py` (renumbered, not rewritten) carries over as-is. This section exists in the doc for
completeness of the persona table in §2, not because the underlying features need new work.

---

## 5. Clinical-evidence workspace

Four pages. All are stateless, single-request lookups — no session carries over between one lookup and
the next beyond normal Streamlit widget state (nothing is written to disk or a database).

### 5.1 Individual concept profile (existing — reframe only)

`pages/1_個體概念剖面_探索demo.py` → renamed/moved to `pages/8_臨床證據_個體概念剖面.py`. No behavior
change: still `POST /api/individual-concept-profile`, still request-only/non-persisted/no-identifiers,
still the forced caveat header. The only change is which sidebar group it lives in and removing "探索
demo" framing in favor of describing it as what it actually is: paste one de-identified sample's
expression, get a transparent concept-module projection + hypothesis-only target clues.

### 5.2 NEW: Disease × Drug evidence match

Answers the "patient already has a diagnosis and a candidate drug — what's the actual evidence?"
question, using `match_disease_drug_evidence()` (already implemented in
`src/3_DE_analysis/evidence/external_cache.py:360`, currently **not exposed via any API route or UI**).

**New backend route required** (thin wrapper, no new logic):

```
GET /api/disease-drug-evidence?gene={gene}&disease={disease_name}&max_drugs={n}
```
- Calls `match_disease_drug_evidence(gene, disease_name, max_drugs)` directly and returns its dict.
- Add to a router (`api/routers/evidence.py` or a new `api/routers/disease_drug.py`) tagged
  `"Clinical evidence (research use)"` in `OPENAPI_TAGS` (`api/app.py`).
- Read-only, no persistence — matches the existing pattern of every other evidence lookup in this API.
- Returns the function's own `available`/`reason`/`caveat` fields unmodified: **the frontend must not
  paper over an `available: False` response** (e.g. gene not found in Open Targets) — render it as an
  honest "no evidence available" state, not an error to be retried away.

**New page (`pages/9_臨床證據_疾病藥物證據配對.py`):**
- Inputs: gene symbol (or resolve via `/api/genes/resolve` first, reusing existing resolution UX from
  the target dossier page), disease name (free text, matching `disease_translator.py`'s existing
  normalization).
- Output table: one row per known drug for the gene, columns = drug name, development phase, and
  **`trials_for_this_disease`** (`n_trials` + `source_status`) — i.e., whether *this specific drug* has
  actually been trialled for *this specific disease*, not just whether the gene is disease-associated.
- Forced caveat, verbatim from the backend response: *"evidence-matching only — not a treatment
  recommendation or efficacy prediction; a nonzero drug count for this gene does not mean the drug has
  been trialled for the disease queried; verified drug-indication pairings must be confirmed against the
  drug label and a qualified physician."*
- Explicitly show drugs with **zero** trials for the queried disease in the same table (not filtered
  out) — per the Module 3 design doc §6, hiding the "no trials for this indication" rows is exactly the
  kind of visual softening this feature exists to prevent (e.g. basiliximab shows up for IL2RA with 0
  RA trials, because its real approved indication is kidney-transplant rejection).
- **Demo-reliability fallback**, matching `pages/1_個體概念剖面_探索demo.py`'s existing pattern
  (`SAMPLE_REPORT` used when the live call fails): this page depends on two live external services
  (Open Targets GraphQL, ClinicalTrials.gov) neither of which this repo controls. For a live walkthrough
  in front of leadership, add the same "load a known-good example" button and the same honest fallback
  labeling (`st.warning("SAMPLE fallback — endpoint unreachable")`) rather than letting a transient
  network hiccup stall the demo. The canned example should be a real, previously-verified pair (e.g.
  IL2RA + rheumatoid arthritis, per the worked example in the Module 3 doc §6) — not a fabricated one.

### 5.3 Population genetics lookup (promoted to its own page)

`/api/population-hypothesis/{gene}` is already implemented and already surfaced inside the researcher's
target dossier page (`pages/3_...target_dossier.py`, formerly `pages/2_...`, UK Biobank LoF-burden
hypothesis section). Revised from the original draft: rather than only cross-linking to that dossier
section, give the clinical-evidence persona its own page (`pages/10_臨床證據_群體遺傳查詢.py`) — a
standalone gene+trait lookup is a smaller ask than "open the full researcher dossier to find one
section," and it matches the flattened one-feature-per-nav-item shape §3 commits to. Both surfaces call
the same read-only endpoint; neither writes anything. The result table must show a CI-includes-zero row
exactly as plainly as a CI-excludes-zero one — a non-significant gene is reported, not hidden (see the
worked contrast in the mockup's Population Genetics page: PLCG1/VAV1/SENP5/TADA1 excl. zero vs. a GATA3
CI-includes-zero row shown with equal visual weight).

---

## 6. Shared guardrail component (small refactor, enables §5)

Today the forced-caveat banner is reimplemented per module with its own `CAVEAT_TEXT` constant
(`concept_waterfall.py`, `population_hypothesis.py`, `signature_explorer.py` each define their own,
per `concept_waterfall.py`'s own comment at line 24). Adding a second clinical-evidence page is a good
trigger to extract one shared helper so the guarantee is enforced by one function instead of copy-pasted
per page:

```python
# frontend/dashboard/guardrails.py (NEW)
def forced_caveat_header(text: str) -> None: ...      # st.error(), unconditional, no toggle param
def render_response_caveat(payload: dict) -> None: ... # surfaces payload["caveat"], errors loudly if absent
def provenance_footer(payload: dict, api_base: str) -> None: ...
```

`pages/8_...` and `pages/9_...` both import this instead of hand-rolling their own banner logic. This is
a pure refactor of existing duplicated logic, not new UI behavior — the rendered text and behavior stay
identical to what `pages/1_個體概念剖面_探索demo.py` already does today.

---

## 7. Summary of concrete changes

| Change | Type | Files |
|---|---|---|
| Split `target_card_dashboard.py`'s 6 tabs into 6 standalone researcher pages | Move, no logic change | new `pages/1_...` through `pages/7_...` (§3) |
| Rename/renumber existing individual-concept-profile page into the clinical group | Move, no logic change | `pages/1_個體概念剖面_探索demo.py` → `pages/8_臨床證據_個體概念剖面.py` |
| Extract `_api_get`/`_api_post`/etc. into one shared client | Refactor (dedup) | new `frontend/dashboard/api_client.py` |
| Landing page persona picker | New UI, no new data | `target_card_dashboard.py` |
| Disease×drug evidence API route | New route, existing logic | new/edited file under `api/routers/`, `api/app.py` (OPENAPI_TAGS) |
| Disease×drug evidence page | New page | new `pages/9_臨床證據_疾病藥物證據配對.py` |
| Population genetics lookup, promoted to its own clinical page | New page (existing endpoint) | new `pages/10_臨床證據_群體遺傳查詢.py` |
| Shared guardrail helper | Refactor (dedup) | new `frontend/dashboard/guardrails.py` |

Nothing here touches `core/`, `readiness_engine.py`, scoring, or dataset build/merge logic. Nothing here
adds authentication, persistence of individual-level data, or a new disk-cache namespace.

---

## 8. Open questions for a future iteration (not blocking this design)

- If a real clinical pilot is ever wanted (persistent per-patient history, accounts), that's gated on
  reviving `docs/IMPLEMENTATION_PLAN.md` §1.8 (Supabase/Postgres + auth) — a separate proposal, not an
  extension of this one.
- Whether `disease_translator.py`'s existing disease-name normalization is permissive enough for
  free-text clinical phrasing (e.g. "lupus" vs "systemic lupus erythematosus") should be checked when
  §5.2 is implemented; if not, reuse the same normalization the Disease Translator tab already has rather
  than adding a second one.
