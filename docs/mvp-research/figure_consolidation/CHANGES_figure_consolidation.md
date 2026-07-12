# Figure Consolidation & Archive — CHANGES

**Date:** 2026-07-12
**Scope:** Full visual audit of all 98 PNG figures in the artifact store; consolidation of redundant chart-family series into publication-grade composites; non-destructive archival of superseded single charts.

---

## Summary

| | count |
|---|---|
| Total unique figures audited | 93 source PNGs |
| **Main display** (kept for front-end / publication) | **33** |
| **Archived** (retained, not deleted) | **62** |
| New composite figures created | 2 (H, C series) |

No file was deleted. Every superseded chart moved to `archive/` with a documented reason.

---

## What was consolidated

### H-series (hierarchical / composition): 7 charts → 1 composite (3 panels)
The 7 H-series charts carried heavy internal redundancy — they encoded the *same three relations* in different visual forms:
- H1 mosaic / H2 sunburst / H3 icicle → **same** condition×on-target-effect hierarchy, three encodings
- H4 sankey / H5 funnel → **same** four-gate curation funnel
- H6 parallel-coords / H7 → **same** feature-invariance-across-conditions story

**`H_composite_hierarchical.png`** keeps one representative per relation:
- panel a = mosaic (H1) — on-target knockdown dominates ~62% of DE-stat rows across all three conditions
- panel b = funnel (H5) — curation gate 33,983 → 2,131 (6.3%), ≥50-DE genes is the strictest gate
- panel c = parallel-coords (H6) — culture condition barely shifts effect size or DE breadth

Archived: H2 sunburst, H3 icicle, H4 sankey, H7 (4 redundant single charts).

### C-series (special / advanced encoding): 3 charts → 1 composite (2 panels)
- C3 funnel **duplicated** the curation funnel already shown in H5 and Figure1 → archived.

**`C_composite_special.png`** keeps the two complementary views:
- panel a = triple-encoded dot plot (C1) — size = DE-gene count, colour = signed on-target effect, across Rest/Stim8hr/Stim48hr (focused shortlist)
- panel b = genome-wide pseudo-volcano (C2) — effect size vs DE-gene count, ≥50-DE gate line, off-target flagged (whole-library landscape)

---

## What was archived and why

**`archive/series_singles/` (53 files)** — the C/D/H/M/N/R/V catalog single charts. These were the exploratory chart-family gallery (each series = one chart type applied to the same data). They are **already tiled** into the 7 `gallery_1`–`gallery_7b` family composites for front-end display, and the two new H/C composites now cover the previously-uncomposited series. Kept for anyone who wants a single chart in isolation.

**`archive/composed_panels/` (6 files)** — `panel_a`–`panel_f`. These are the atomic panels **already composed into** the two flagship figures (`Figure1_integrated_story.png` and `figure1.png`). The flagships are the canonical form; the loose panels are redundant.

**`archive/old_prototypes/` (2 files)** — `viz_prototype_4panel.png`, `viz_dotplot_3d.png`. Early visual-exploration prototypes, superseded by the refined 53-chart catalog.

**`archive/cjk_stub/` (1 file)** — `gallery_7_ranking_variants.png`. Contains a Chinese-text placeholder UpSet stub panel ("UpSet 圖圖圖…"), which violates the English-only requirement. The real UpSet chart is covered separately by `gallery_7b_upset.png`.

---

## Main-display set (33 figures)

**Flagship stories (3):** figure1.png (signed-axis + external validation), Figure1_integrated_story.png (platform pipeline), figure_target_validation.png
**New composites (2):** H_composite_hierarchical.png, C_composite_special.png
**Family composites (7):** gallery_1 … gallery_7b (dedup-checked; gallery_7 replaced by 7b)
**Validation (7):** benchmark_pr_roc, dropout_diagnosis, context_specific_corrected, threshold_sensitivity, methodological_validation, level4_external_validation, context_specific_shortlist_slope
**Signed application (2):** signed_application_composed, signed_direction
**Domain (5):** mechanism_map, lincs_concordance, kinetics_and_avoid, delivery_funnel, dev_vs_user_gap
**Structure demos (2):** protter_GPAA1, protter_TRIM39 (representative TM / soluble)
**Cover (3):** COVER_target_ranking + cover assets
**Branding (2):** logo_scientific, logo_wordmark

---

## How to use

- Full per-figure decision table: **`FIGURE_AUDIT_MASTER.csv`** (filename, class, destination, artifact version_id, reason).
- Front-end should point its gallery at the **main-display** set + the 2 new composites.
- Archived files remain in the repo under `archive/` — nothing is lost; a developer can restore any single chart to main display by moving it back and updating the catalog.
