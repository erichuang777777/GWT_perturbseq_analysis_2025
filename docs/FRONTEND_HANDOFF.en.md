# Frontend Handoff

> **One page for the frontend team**: the best/most-relevant files and assets the portal needs — each with what it is, path, how the frontend uses it, and status. This is the **curated** list (the full inventory is `documentation_index.md`). 繁中版:`FRONTEND_HANDOFF.md`.
>
> **Golden rule**: the frontend **never invents numbers** — every number and disclosure comes from the files below. When there's no data, show `unknown` + a coverage note, **never a fabricated 0**.

## 0. TL;DR

The portal discloses everything by reading three files in `public/`: `real-dataset.json` (data), `disclosure.json` (versions / disclaimer / principles / limitations / attribution), and `provenance_registry.csv` (source × algorithm × reference). **The Provenance and Overview pages are already built** (entry points in Header/Footer); the rest is just rendering these files.

---

## 1. Data & content files (portal fetches from `public/`)

| File | What it is | How the frontend uses it | Status |
|---|---|---|---|
| `public/real-dataset.json` | Targets (7,249) + concept modules (M01–M20); exported by `scripts/export_real_data.py` | Main data source (loaded in `data/dataset.ts`) | ✅ wired |
| `public/disclosure.json` | Versions, coverage, disclaimer, 5 principles, limitations, 12 attributions, concept-layer note | Rendered on Provenance page + Footer version | ✅ wired |
| `public/provenance_registry.csv` | 79 rows: data source × algorithm × reference (fixed 8 columns) | Provenance page, 3 tabbed tables | ✅ wired |
| `public/flagship/*.png` | Flagship figures for the two Home persona cards | Home hero images | ✅ wired |

> Field structure and the "null = unknown" rule: `docs/bulk_download_schema.md`.

---

## 2. Frontend specs & public-facing docs (read / link)

| File | Purpose |
|---|---|
| `docs/frontend_disclosure_spec.md` | **Disclosure spec**: what to surface, where, source files, gaps G1–G6 |
| `docs/bulk_download_schema.md` | Per-field schema of the downloadable files |
| `docs/data_use_terms.md` · `DATA_LICENSE.md` | Public terms / licence |

---

## 3. Fact sources (where numbers/definitions come from)

| File | Provides |
|---|---|
| `docs/data_dictionary.md` | Per-field definitions (card / readiness / evidence columns) |
| `docs/technical_methods.md` | Methods, calibration numbers, limitations, **§8 formal references** |
| `docs/server_modules.md` | The 13 API routers' endpoints/IO (for ApiDocs / future live wiring) |
| `docs/concept_dictionary.md` | Concept modules M01–M20 (seed genes; "never feeds decisions" invariant) |
| `docs/figure_guide.md` | Figure reading guide (if surfacing more figures) |
| `docs/provenance_registry.csv` | Machine-readable source × algorithm × reference table |

---

## 4. Already built in the portal (**do not redo**)

| Location | What |
|---|---|
| `views/Provenance.tsx` | Disclosure page: renders `disclosure.json` + `provenance_registry.csv` (versions/coverage/registry/principles/limitations/concept layer/attribution) **and the validation ladder L1–L5 incl. the Track D phenotype-matched result — directionality null, magnitude fair-version passes-with-confound, honestly labelled**. Header + Footer entry points |
| `views/Deck.tsx` | Overview: the 4-slide project summary (overview/method/results/infographic). Header + Footer entry points |
| `views/ApiDocs.tsx` | REST API docs page |
| `views/Home.tsx` | Two persona cards + flagship figures |
| Other views (Clinical/Dossier/Compare…) | Already implement `unknown ≠ 0`, per-number sourcing, research-use disclaimer, descriptive-vs-decision |
| Footer | `Data dictionary` (→ GitHub) · `Provenance` · `Overview` · `REST API` · `Bulk download` (→ `real-dataset.json`) — **all previously-dead links now wired** |

---

## 5. Frontend TODO (not yet done)

1. Add a top-level `meta` block to `scripts/export_real_data.py` (versions/coverage/`generatedAt`) so Footer/Provenance read data-driven values instead of TS constants (see `frontend_disclosure_spec.md` §4, approach B).
2. `Data dictionary` currently links to GitHub; to render in-app, turn `data_dictionary.md` into a page.
3. `Bulk download` currently serves `real-dataset.json`; can also offer `provenance_registry.csv` + a schema page.

---

## 6. UI non-negotiables

`unknown ≠ 0` · every number carries its `source` (+ `fetched_at` for external evidence) · research-use disclaimer always visible · concept layer / mechanism graph labelled "descriptive, not part of the decision" · user-adjustable weights never change `readiness_call`.

---

## 7. Citation & licence

Cite the primary dataset (Zhu & Dann 2025, bioRxiv `10.64898/2025.12.23.696273`) + external-source attribution (see `disclosure.json.attribution` or `data_use_terms.md`). **Research use — not clinical advice.**

---

> Full documentation inventory: `docs/documentation_index.md`. Authoritative content is the `docs/` files and the code themselves.
