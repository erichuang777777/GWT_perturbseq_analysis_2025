# Running the cell-level extension on the real GWT dataset

This file is the concrete, step-by-step guide for processing the real
per-cell data once you have downloaded it on a machine with enough resources.
Everything in this directory (`cell_integration_pipeline.py` and
`perturbation_response_analysis.py`) was built and verified in a sandboxed
session that could **not** download or store the real files — see
"Why this is separate from the rest of the toolkit" below before you start.

## 0. What you're downloading, and what it takes

Source of truth: `data/marson2025_data/manifest.csv` (already in this repo).

```bash
python3 -c "
import csv
with open('data/marson2025_data/manifest.csv') as f:
    rows = list(csv.DictReader(f))
total = sum(int(r['size_bytes']) for r in rows)
print(f'{len(rows)} files, {total/1024**4:.2f} TiB total')
print('smallest:', min(float(r['size_gib']) for r in rows if float(r['size_gib'])>1), 'GiB')
print('largest:', max(float(r['size_gib']) for r in rows), 'GiB')
"
```

As of this writing: **32 files, 1.68 TiB total**, the smallest substantive
per-donor-condition file (`D*_*.assigned_guide.h5ad`) is **~131 GiB**, the
largest **~161 GiB**. Plan for:

- **Storage**: at minimum, 2x the size of whatever subset you process (raw +
  intermediate outputs). Processing all 32 files needs several TiB free.
- **Memory**: every function below is written to work in *backed* mode
  (`anndata.read_h5ad(path, backed="r")`), reading only small, bounded slices
  off disk. The one exception is `score_cd4_programs`, which scores gene
  modules across the full matrix it's given — pass `max_cells` to subsample
  first if you don't have a big-memory node (128GB+ RAM recommended for a
  full ~130GB file without subsampling).
- **Network**: the bucket is public, no AWS credentials needed:
  ```bash
  aws s3 cp --no-sign-request \
    s3://genome-scale-tcell-perturb-seq/marson2025_data/D1_Rest.assigned_guide.h5ad \
    ./data/marson2025_data/D1_Rest.assigned_guide.h5ad
  ```
  Repeat per file (or per donor/condition subset — you do **not** need all 32
  files to get useful results; e.g. one donor's 3 conditions is a reasonable
  first pass).

## 1. Environment

```bash
conda env create -f environment.yaml   # scanpy/anndata already listed there
conda activate gwt-env
pip install scikit-learn               # used by the Mixscape-style classifier
```

`pertpy` is **not** required and was deliberately not used (it failed to
install in the development sandbox due to an unrelated transitive dependency
— `blitzgsea`'s build). The Mixscape-style classifier in
`perturbation_response_analysis.py` reimplements the core statistical idea
directly with `scikit-learn` (PCA + 2-component Gaussian mixture) — see that
file's docstring for exactly what it does and why.

If you want SCEPTRE (§H4, real calibrated conditional-resampling test — NOT
reimplemented here, see the docstring for why): install R + the `sceptre`
package separately, and write a driver script that `run_sceptre_external()`
can invoke via `Rscript`.

## 2. What to actually produce — concrete checklist

For each downloaded `D{n}_{condition}.assigned_guide.h5ad` file:

```python
import sys
sys.path.insert(0, "src/9_cell_integration")
from pathlib import Path
import pandas as pd
from perturbation_response_analysis import (
    load_donor_condition_h5ad, validate_schema, guide_assignment_qc,
    classify_perturbation_response, summarize_state_specific_effects,
    score_cd4_programs, load_seed_modules,
)

path = Path("data/marson2025_data/D1_Rest.assigned_guide.h5ad")
adata = load_donor_condition_h5ad(path)  # donor_id="D1", culture_condition="Rest" parsed from filename

problems = validate_schema(adata)
assert not problems, problems

# (a) guide-assignment QC report -- cheap, obs-only, safe on the full backed file
qc = guide_assignment_qc(adata)
Path(f"outputs/cell_level/{path.stem}.guide_qc.json").write_text(__import__("json").dumps(qc, indent=2))

# (b) Mixscape-style responder/escaper calls -- backed-safe, per-target slicing
calls = classify_perturbation_response(adata)
calls.to_csv(f"outputs/cell_level/{path.stem}.response_calls.csv", index=False)

# (c) per-target x condition summary for THIS file
summary = summarize_state_specific_effects(calls)
summary.to_csv(f"outputs/cell_level/{path.stem}.state_summary.csv", index=False)

# (d) CD4 program scores -- the memory-heavy step; subsample if needed
modules = load_seed_modules(Path("sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv"))
scored_status, scored_adata = score_cd4_programs(adata, modules, max_cells=50_000)
scored_adata.obs.to_csv(f"outputs/cell_level/{path.stem}.program_scores.csv")
```

Repeat across every donor/condition file you download, then combine:

```python
from perturbation_response_analysis import merge_donor_condition_summaries, bridge_to_card_columns

summaries = [pd.read_csv(f"outputs/cell_level/{f}.state_summary.csv") for f in your_processed_files]
combined = merge_donor_condition_summaries(summaries)
combined.to_csv("outputs/cell_level/combined_state_summary.csv", index=False)

# Bridge into the existing CSV-first target cards (additive -- NaN where no cell-level data exists)
cards = pd.read_csv("sources/target_tool_cache/<dataset_id>/target_cards.csv")
enriched = bridge_to_card_columns(combined, cards)
enriched.to_csv("sources/target_tool_cache/<dataset_id>/target_cards.cell_enriched.csv", index=False)
```

This gives you, per `target x condition`: `n_cells_classified`,
`responder_fraction`, `n_donors_classified` — new columns additive to the
existing CSV-first card, never replacing it. A low `responder_fraction` on an
otherwise high-grade card is exactly the kind of caveat this toolkit's
`score_cap_reason`/readiness engine is designed to surface; wiring
`responder_fraction` into `readiness_engine.py`'s `translation_score` (or as
a new domain) is the natural next step once you have real numbers — it
wasn't done in this session because there was no real data to calibrate
against.

## 3. (Optional) full multi-dataset integration

If you also want batch-corrected embeddings / UMAP / Leiden clusters across
donors (for cell-state-specific questions beyond responder/escaper calling),
use the existing `cell_integration_pipeline.py` in this same directory —
build a manifest from `manifest.template.csv` pointing at your downloaded
files and follow that script's own README section above.

## 4. Why this is a separate document instead of a "done" checkbox

The rest of this toolkit (`src/3_DE_analysis/*`) was built and verified
against the real, already-in-repo CSV summary tables (33,983 DE rows, etc.).
This directory's code was built the same way — real logic, real
verification — but verified against a **synthetic** AnnData
(`build_synthetic_adata`, in `perturbation_response_analysis.py`) constructed
to match the exact real schema documented in
`metadata/data_sharing_readme.md`, because the real cell-level files (131+
GiB each) could not be downloaded or stored in the sandboxed environment this
was developed in. The classifier was validated against a known ground truth
in that synthetic fixture (81.8% accuracy recovering an injected responder/
escaper split — see the git history for this file for the exact numbers).

Point every function at a real file and it will run identically — nothing
here is schema-specific to the synthetic fixture. But "the code is correct
and tested" and "this has been run against the real 1.68 TiB dataset" are
different claims, and only the first one is true as of this commit. Update
this section once you've run it for real.
