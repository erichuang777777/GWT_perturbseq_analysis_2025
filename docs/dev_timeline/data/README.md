# Development dot-flow chart — raw data & reproduction

This folder is everything needed to regenerate the "開發流程點圖" chart
(commit count -> dot size, diff volume -> colour, human-touch -> ring,
Phase 1-6 bands, 5-category rows) for `erichuang777777/GWT_perturbseq_analysis_2025`,
without re-deriving anything by hand.

## Files

| File | What it is |
|---|---|
| `build_dev_timeline_data.py` | The script that produced everything else here, directly from `git log`. Rerun it against a fresh clone to refresh all numbers as new commits land. |
| `commits_classified.csv` | One row per non-merge commit: sha, UTC timestamp, day, 8h-slot (0/1/2 = 00-08/08-16/16-24), work-type category, diff size (insertions+deletions), branch-lane, human-touch flag, subject line. The finest-grained dataset — every other file is an aggregate of this one. |
| `grid_by_category.json` | `{"category|YYYY-MM-DD|slot": {"n": commit_count, "diff": total_lines_changed, "human": bool}}` — exactly the numbers used to size/colour/ring every dot in the chart. |
| `bug_events.json` | The 11 known incident-fix commits, each resolved to which category/day/slot cell it landed in (for the red dashed rings). |
| `plan_docs.json` | The 12 planning/decision-doc commits, resolved the same way (for the star markers). |
| `ml_attempts.json` | The 7 commits behind 3 real ML-modelling attempts (T1 perturbation-response benchmark; GenePT+Ridge and GEARS-GNN; T2 known-regulator classifier family), resolved the same way (for the dagger markers). Added after a follow-up review — see phases.json's Phase 5 note. |
| `phases.json` | The project's own Phase 1-6 (from `sources/project_roadmap.md`, 2026-07-04) mapped to real activity windows, with the evidence for each window. Phase 4 is honestly `"status": "blocked"` (no matching commits anywhere in git history); Phase 5 was *initially* marked blocked by a filename-only search, then corrected to `"active"` once its feature-table builders were found under different names (`src/10_ml_perturbation_prediction/*/build_*.py`). |

## Regenerating

```bash
git clone https://github.com/erichuang777777/GWT_perturbseq_analysis_2025
cd GWT_perturbseq_analysis_2025
python3 /path/to/build_dev_timeline_data.py --repo . --out ./dev_timeline_data
```

No third-party Python packages required — only `git` on `PATH`.

## Known limitations (carried into the chart's caption)

- **Category assignment is a heuristic, not a hand-checked label.** Each
  commit is assigned to one of `data_processing / external_integration /
  stats_analysis / visualization / documentation` by line-change-weighted
  majority vote over the files it touched (`classify_file()` in the script).
  A commit that touches both a large code file and a small doc tweak will
  be filed under the code category, and vice versa — this is usually right
  but not always.
- **`is_human` is a proxy, not ground truth.** It is `True` when a commit
  sits outside every AI branch's PR range (a direct push), or its subject
  matches a known human-action pattern (`sync main…`, `Merge main…`,
  `Perturbase review:…`). Codex-authored commits carry the human git
  identity `erichuang777777` even though they were AI-generated on a
  `codex/*` branch, so branch membership — not author email — is what the
  script actually keys on.
- **Some high `diff` cells reflect the same change fanned out across
  several parallel `worktree-agent-*` branches** that were later merged
  back into one long-lived feature branch, not N independent rewrites.
- **Phase 1-6 windows are qualitative**, backed by the `evidence` field in
  `phases.json`, not an automatic classifier — Phase 1 and 3's core scaffold
  already existed in the pre-sprint 2026-07-05 snapshot and is not
  double-counted in the 5-category grid (that commit is excluded from
  `grid_by_category.json` and shown as a standalone "founding" marker in
  the chart instead).
