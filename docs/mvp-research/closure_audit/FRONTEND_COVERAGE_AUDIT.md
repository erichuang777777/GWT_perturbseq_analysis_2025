# Frontend Coverage & Interactivity Audit — Perturbase Chart Catalog

**Artifacts audited**
- `ALL_CHARTS_CATALOG_bilingual.json` (version ad5db98e) — 71 chart records
- `chart_catalog_bilingual.html` (version 9bf4d0e5) — interactive front-end
- `FIGURE_SCRIPTS_INDEX.csv` (version ee015c44) — 71 reproduction scripts

Method: JSON and HTML were parsed directly (not assumed). Every field was tested
for non-empty content in both languages; every interactive handler was located in
the page's JavaScript; the 71 catalog figures were cross-checked against all 368
project artifacts.

---

## 1. Catalog completeness — 71/71 charts fully populated

| Element | Charts complete | Rate |
|---|---|---|
| `en` block (title + family + description + data_explanation) | 71/71 | 100% |
| `zh` block (title + family + description + data_explanation) | 71/71 | 100% |
| **All 4 info elements complete in BOTH languages** | **71/71** | **100%** |
| `raw_source` present (underlying data described) | 71/71 | 100% |
| Script link (`script` + `script_vid`) | 71/71 | 100% |

Group split: **Core gallery 53** + **Analysis & publication 18** = 71 (matches the
declared `Core gallery(53) + Analysis & publication(18)`).

Every chart therefore carries the full five-part information payload
(title / family / description / data_explanation / raw_source) in English and
Traditional Chinese, plus a linked reproduction script. **n_with_all_4_elements = 71.**

One caveat on the script layer: 1 of 71 reproduction scripts is a stub —
**A17 (`A17_figure1.py`)** is flagged `is_stub=True` in the scripts index. The catalog
link is present and the figure is rendered; only the standalone re-run script is a
placeholder. All other 70 scripts are non-stub and declare their package dependencies.

---

## 2. Coverage across produced analysis stages — all 7 stages represented

| Analysis stage | Front-end charts | Status |
|---|---|---|
| Pipeline (raw → dashboard) | C3 (QC funnel), H4 (Sankey), H5 (funnel), A6, A16 | COVERED |
| Benchmark ROC / PR | A1 (PR+ROC+calibration), A15 (AUROC panel) | COVERED |
| Dropout diagnosis | A2 (loss-intolerant dropout) | COVERED |
| Baseline correction | A14 (baseline-correction diagnostic) | COVERED |
| Signed application | A8, A17 (signed-DE 7-panel), N5, A4 | COVERED |
| Level-4 external validation (GWAS / STRING / GSE318876) | A7, A9 (LINCS), A10 (gnomAD), N1 (STRING), A18 (Reactome) | COVERED |
| Delivery funnel | A3 (delivery decision layer) | COVERED |

No analysis stage is absent from the front-end. The Core gallery additionally covers
distributions (D1–D10), matrices (M1–M10), rankings (R1–R10), networks (N1–N7),
hierarchical/interactive (H1–H7), and dimensionality-reduction/composite (C1–C3, V1–V6).

### Figures present in the project but NOT in the catalog (assessed — not gaps)
Cross-checking all 111 image artifacts against the 71 catalog figures leaves 35
un-referenced images. Each was inspected and is **intentionally excluded**, not a gap:
- **13 animated GIFs** (`anim01`–`anim10`, `ANIM_*`) — motion previews; the catalog
  is a static-figure gallery.
- **8 gallery contact-sheets** (`gallery_1`…`gallery_7b`) — montage thumbnails whose
  individual panels are already catalog entries.
- **6 multi-panel source panels** (`panel_a`…`panel_f`) — component panels composited
  into catalog figures A16/A17.
- **4 brand assets** (`logo_*`, 2 PNG + 2 SVG) — not data figures.
- **4 superseded/prototype variants** (`signed_direction.png`,
  `context_specific_shortlist_slope.png`, `viz_dotplot_3d.png`,
  `viz_prototype_4panel.png`) — earlier drafts replaced by A8/A14 and the V-series.

**Conclusion: 0 unrepresented production figures.** Every finalized figure that backs
an analysis stage has a catalog entry.

### Data tables — one structural gap (see §4)
70 CSV data tables exist in the project. The front-end is a **figure catalog**: it
describes each table's contents inside the relevant chart's `raw_source` prose, but
exposes **no table-download / table-browse surface**. Several Level-4 evidence tables
(`gse318876_target_evidence`, `panelD_gwas`, `panelE_string`, `string_partner_recovery`,
`clinical_avoid_list`, `kinetic_archetypes`, `threshold_sensitivity_grid`,
`gnomad_constraint_seed`, `reactome_pathway_snapshot`, `cross_validation_results`) are
visualized in a figure but are **not named or linked** as downloadable tables. This is
the single genuine coverage gap and is a scope decision, not a defect (see remediation).

---

## 3. Interactivity — 4/4 features verified in code

All four interactive behaviors were located in the page's inline JavaScript
(`chart_catalog_bilingual.html`, lines 51–79) and confirmed wired, not merely styled.

| # | Feature | Verified | How it works (code evidence) |
|---|---|---|---|
| a | **Search box filter** | ✅ Present | Input `#q`; `render()` (l.65-66) lowercases the query and filters `DATA` on `title+description+family+data_explanation` of the active language. Bound via `addEventListener('input', render)` (l.78). |
| b | **Group + Family dropdown filters** | ✅ Present | Two `<select>` (`#grp`, `#fam`, l.40). `buildFilters()` (l.61-64) populates them from `DATA` distinct groups/families; `render()` applies `d.group===g` and `L(d).family===f`. Both preserve selection across language switch. |
| c | **Per-chart modal (all 4 elements)** | ✅ Present | `openM(id)` (l.71-75) fills the modal image, tag (group·family), title, description, data_explanation, and raw_source. Opened by card `onclick` (l.68); closed by ✕ or backdrop click (l.76-77). Shows title + description + data_explanation + raw_source = full payload. |
| d | **EN / 中文 site-level language toggle** | ✅ Present | Header buttons `#btnEN`/`#btnZH` → `setLang(l)` (l.54-56) swaps `LANG`, updates `<html lang>`, re-applies UI labels via `applyUI()` (from a bilingual `UI` label object with `en`/`zh` sub-objects, whose keys are `tagline`, `search`, `allg`, `allf`, `charts`, `desc`, `mean`, `src`, `group_core`, `group_ana` — UI chrome only, not chart content), rebuilds filters, re-renders grid, and re-opens the current modal in the new language. |

Supporting facts confirmed by parsing: the embedded `DATA` array holds exactly **71**
records; a bilingual `UI` label object (tagline, search placeholder, filter labels,
field labels) exists for both `en` and `zh`; all 71 figure `img` sources are
`{artifact:…}` markers that resolve to the same version_ids as the catalog.

### Information sufficiency
**Sufficient.** For any chart, a user reaching the modal without the paper obtains:
(1) a plain-language **title**, (2) a **family/type** tag, (3) a **description** of what
the visual encodes (axes, color, size, marks), (4) a **data_explanation** giving the
biological/decision meaning, and (5) a **raw_source** block naming the underlying table,
its dimensions, and key fields. This is enough to interpret each figure standalone in
either language. The prior multi-subagent visual QC (39 records corrected, 26 figures
re-rendered to English) is carried forward; language of figure content and catalog text
is consistent English/Chinese.

Minor sufficiency limitations (not blocking): (i) the linked reproduction script is not
surfaced in the modal UI (present in JSON/index only); (ii) raw_source is descriptive
prose, not a clickable link to the CSV.

---

## 4. Remediation

| Priority | Item | Recommendation |
|---|---|---|
| Low | A17 stub script (`A17_figure1.py`, `is_stub=True`) | Replace the placeholder with the real reproduction script so all 71 scripts are runnable. |
| Low | No table-download surface | Add a "Data tables" tab or a per-chart "Download source CSV" link resolving `raw_source` to the actual artifact, so Level-4 evidence tables (GWAS/STRING/GSE318876/gnomAD/Reactome/clinical-avoid) are directly accessible, not only described. |
| Info | Script link not shown in modal | Optionally expose the `script_vid` link inside the modal for reproducibility-minded users. |

**None of these block release.** Figure coverage is complete (71/71), stage coverage is
complete (7/7), bilingual information is complete (71/71 with all 4 elements in both
languages), and all four interactive features are functional.

---

## Summary scorecard
- Charts on front-end: **71 / 71** (100%)
- Charts with all 4 info elements in BOTH languages: **71 / 71** (100%)
- Charts with raw_source + script link: **71 / 71** (script link; 1 stub script)
- Analysis stages represented: **7 / 7** (100%)
- Production figures unrepresented: **0**
- Interactive features working: **4 / 4** (search, group+family filter, modal, EN/中文 toggle)
- Genuine gaps: **1** (no downloadable-table surface — scope decision, low priority)
