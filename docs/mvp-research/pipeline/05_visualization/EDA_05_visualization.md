# EDA — 視覺化 · Visualization catalog

> **本階段目標為何 · Stage goal**
>
> 凍結 53 張 refined publication 圖的目錄(每張:族系、來源資料、再導出數字),確保每張圖可追溯回上游階段。
> Freeze the 53-figure publication catalog with per-figure lineage back to a pipeline stage.

**輸入 · Inputs**
- 04_statistical/*
- 03_processed/*

**重現指令 · Reproduce**: 圖目錄 REFINED_CATALOG_53.csv;lineage 見 reproducibility_audit/figure_registry.csv。

> `unknown != 0`: 缺失以 missingness% 呈現,類別分佈保留 `(missing)` 桶;NaN 不會被當成 0。

## REFINED_CATALOG_53.csv

- **path**: `docs/mvp-research/pipeline/05_visualization/refined_figures/REFINED_CATALOG_53.csv`
- **shape** (parsed records): **53 rows × 6 cols**
- **md5**: `f07ce8a4ab41e04b42795fa5105032d7`  (cross-check FREEZE_MANIFEST.csv)

### Schema & missingness
| column | dtype | missing % | distinct |
|---|---|---|---|
| `id` | object | 0.0% | 53 |
| `title` | object | 0.0% | 53 |
| `family` | object | 0.0% | 6 |
| `filename` | object | 0.0% | 53 |
| `version_id` | object | 0.0% | 53 |
| `what` | object | 0.0% | 53 |

### Numeric summary
_(no numeric columns)_

### Categorical / low-cardinality distributions
- **`family`**: `分佈族`=10 · `排序族`=10 · `矩陣族`=10 · `降維與複合族`=9 · `網路族`=7 · `階層互動族`=7

---
_Regenerate: `python scripts/generate_stage_eda.py`. Deterministic (no timestamp); guarded by `tests/test_generate_stage_eda.py`. Part of the release freeze — see `docs/mvp-research/pipeline/EDA_INDEX.md`._
