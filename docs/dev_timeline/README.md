# Development Timeline Visualization

This directory contains comprehensive visualizations and raw data for the GWT_perturbseq_analysis_2025 development timeline, tracking commit activity across different work categories during the project's main development phase (2026-07-05 through 2026-07-12).

## Files

### Visualizations

- **figure1_dot_flow_chart.html** — Static dot-flow chart showing:
  - Commit volume (dot size, √n scale)
  - Lines changed (fill color intensity, log scale: cream→clay→ink)
  - Human-touch commits (solid ring)
  - Incident-fix commits (dashed red ring)
  - Planning documents (asterisk markers)
  - ML-modelling attempts (dagger markers)
  - 8 project phases across the development window

- **figure1_animated.html** — Interactive animated version with:
  - Play/Pause/Restart controls
  - Timeline slider for frame-by-frame exploration
  - Same data as static version, revealed progressively day-by-day

- **dot_flow_animated.gif** — Animated GIF (7 frames) showing the development progression:
  - 6 frames at 900ms each (one per day, 07-07 through 07-12)
  - 1 final frame at 2500ms (for readability)
  - 878 KB file size

### Data & Scripts

The `data/` directory contains the raw data and reproduction scripts:

- **commits_classified.csv** — 462 non-merge commits with:
  - SHA, timestamp, date, 8-hour slot
  - Work-type category (data_processing / external_integration / stats_analysis / visualization / documentation)
  - Diff size (insertions + deletions)
  - Lane and human-touch flag
  - Commit subject line

- **grid_by_category.json** — Aggregated commit counts and diff volumes:
  - One entry per category/day/slot combination
  - Format: `{"category|YYYY-MM-DD|slot": {"n": count, "diff": lines, "human": bool}}`
  - 63 cells total, driving visualization sizing/coloring

- **phases.json** — Project phase definitions:
  - P0: Exploratory research (pre-sprint, 07-05)
  - P1-P6: Roadmap phases (from sources/project_roadmap.md, 2026-07-04)
  - P7: Server establish (FastAPI backend)
  - P8: Interface optimization (React frontend)
  - Each phase includes active_days, status, evidence, and source references
  - Phase 4 (Perturbation Validation) omitted: superseded by signed DE matrix work

- **bug_events.json** — 11 incident-fix commits resolved to grid cells
- **plan_docs.json** — 12 planning/decision-document commits resolved to grid cells
- **ml_attempts.json** — 3 ML-modelling attempts resolved to grid cells
- **build_dev_timeline_data.py** — Python script to regenerate all data from git history
- **README.md** — This file

## Regenerating the Data

To refresh the analysis with new commits:

```bash
cd /path/to/GWT_perturbseq_analysis_2025
python3 docs/dev_timeline/data/build_dev_timeline_data.py --repo . --out ./docs/dev_timeline/data
```

This requires `git` on PATH and no third-party Python packages.

## Known Limitations

See `data/README.md` for details on:
- Category assignment heuristics (line-weighted file-path classification)
- Human-touch proxy (branch membership vs. git author identity)
- Parallel worktree branch expansion
- Qualitative phase window definitions
- Pre-sprint snapshot exclusion from grid

## Context

This visualization documents the project's main development sprint, showing how effort distributed across 5 work-type categories, which days were most active, and which commits represented critical bug fixes or planning milestones.
