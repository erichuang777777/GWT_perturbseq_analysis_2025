#!/usr/bin/env python3
"""Deterministic per-stage EDA (exploratory data analysis) report generator.

Release-freeze deliverable. For every frozen pipeline stage (raw -> curated ->
processed -> results -> statistical -> visualization -> frontend) this emits a
co-located ``EDA_<stage>.md`` inventory report so a human can confirm, stage by
stage, exactly what was frozen: the stage's goal, its input/output files, each
asset's shape + column dtypes + per-column missingness + key distributions, the
asset's md5 (cross-referenced against ``FREEZE_MANIFEST.csv``), and the exact
command that regenerates the stage.

Design constraints (why it looks the way it does):
- **Deterministic**: no wall-clock timestamp, no randomness, columns/rows emitted
  in a stable order, floats rounded to fixed precision. Running it twice on
  unchanged inputs produces a byte-identical report, so it is safe to commit and
  diff in CI (``tests/test_generate_stage_eda.py`` guards this).
- **unknown != 0**: missing values are reported as an explicit missingness rate;
  a NaN is never silently rendered as 0. Categorical value counts surface a
  ``(missing)`` bucket rather than dropping NaNs.
- **Read-only**: never mutates any pipeline asset; only writes the EDA_*.md files
  (and only when their content changes).
- **Authoritative counts**: shapes are ``pandas`` parsed-record counts, not raw
  line counts (some source CSVs contain embedded newlines in quoted fields).

Usage::

    python scripts/generate_stage_eda.py            # write all reports + index
    python scripts/generate_stage_eda.py --check     # exit 1 if any report is stale
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
PIPE = REPO / "docs" / "mvp-research" / "pipeline"
FLOAT_FMT = "{:.4g}"
MAX_CATEGORICAL_LEVELS = 15  # value_counts rows shown before collapsing to "(other)"
CATEGORICAL_MAX_CARD = 40  # a column with <= this many distinct values is treated as categorical


# --------------------------------------------------------------------------- #
# Stage configuration -- the single source of truth for what each report covers.
# `assets` paths are repo-relative. `goal` answers the user's "本階段目標為何".
# --------------------------------------------------------------------------- #
STAGES: List[Dict] = [
    {
        "id": "01_raw",
        "title": "原始資料 · Raw data",
        "out": PIPE / "01_raw" / "EDA_01_raw.md",
        "goal": (
            "凍結唯一的上游輸入,作為整條 in-repo pipeline 的可稽核起點。此階段**不重算**任何值——"
            "它就是 provider 交付的聚合 DESeq2 pseudobulk DE 統計(每 target×condition 一列)加樣本表。"
            "更上游(原始單細胞 ~1.67 TB、DE_stats h5ad 15.6 GB)只在 S3,離線不可重跑,故此層為"
            "「可稽核、不可重生成」。 / Freeze the sole upstream input as the auditable entry point; "
            "nothing here is recomputed. Everything before this file is S3-only and not re-runnable offline."
        ),
        "inputs": ["(upstream, S3-only) GWCD4i.DE_stats.h5ad — 15.6 GB, not in repo"],
        "repro": "不可離線重生成;md5 對 FREEZE_MANIFEST.csv 01_raw 稽核。See docs/REPRODUCIBILITY.md §8.",
        "assets": {
            "DE_stats.suppl_table.csv": PIPE / "01_raw" / "data" / "DE_stats.suppl_table.csv",
            "sample_metadata.suppl_table.csv": PIPE / "01_raw" / "data" / "sample_metadata.suppl_table.csv",
        },
    },
    {
        "id": "02_curated",
        "title": "清理資料 · Curated",
        "out": PIPE / "02_curated" / "EDA_02_curated.md",
        "goal": (
            "對 raw 施加 MVP 品質門檻並標準化欄位:加 `passes_gate`(n_cells≥200 且顯著且非脫靶且 DE≥50)、"
            "`logDE`,不丟列(全 33,983 列保留,只加註記)。 / Apply the MVP quality gate and standardise "
            "columns without dropping rows — annotate pass/fail rather than filter."
        ),
        "inputs": ["01_raw/data/DE_stats.suppl_table.csv"],
        "repro": "reproducibility_bundle_v2.tar.gz 內 curated_{py,r};R==Python 0 mismatch。",
        "assets": {
            "curated_targets.csv": PIPE / "02_curated" / "data" / "curated_targets.csv",
        },
    },
    {
        "id": "03_processed",
        "title": "處理後資料 · Processed",
        "out": PIPE / "03_processed" / "EDA_03_processed.md",
        "goal": (
            "把通過門檻的列 pivot 成 target×condition 矩陣(effect / DE-count),並輸出 gate-passing 子集"
            "(2,131 列 → 1,235 unique targets),供下游統計與視覺化。 / Pivot gate-passing rows into "
            "target×condition matrices and emit the gate-passing subset for downstream stats."
        ),
        "inputs": ["02_curated/data/curated_targets.csv"],
        "repro": "reproducibility_bundle_v2.tar.gz 內 processed_{py,r};cell-level max diff 3.6e-15。",
        "assets": {
            "effect_matrix.csv": PIPE / "03_processed" / "data" / "effect_matrix.csv",
            "de_matrix.csv": PIPE / "03_processed" / "data" / "de_matrix.csv",
            "gate_passing_targets.csv": PIPE / "03_processed" / "data" / "gate_passing_targets.csv",
        },
    },
    {
        "id": "04_results_target_cards",
        "title": "初步結果 · Target cards (canonical 39-col)",
        "out": PIPE / "04_statistical" / "EDA_04a_target_cards.md",
        "goal": (
            "把統計證據組裝成決策就緒的 target cards(39 欄:效應/顯著性/敲低狀態/穩健性/等級/藥理與疾病 overlay)。"
            "這是使用者實際看到的產品資料;kd_status 遵守 unknown≠0(not_assessed vs not_measurable)。 / "
            "Assemble per-target-per-condition decision-ready cards (the canonical 39-col product)."
        ),
        "inputs": [
            "metadata/suppl_tables/DE_stats.suppl_table.csv",
            "metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv",
            "metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv",
        ],
        "repro": "cd src/3_DE_analysis && python build_target_cards.py --de-stats ... --output ...  (see docs/REPRODUCIBILITY.md §6.4)",
        "assets": {
            "target_cards.csv (a6bba17b, canonical)": REPO
            / "sources" / "target_tool_cache" / "a6bba17b-f194-4a50-8cf8-96e03eededd6" / "target_cards.csv",
        },
    },
    {
        "id": "04_statistical",
        "title": "統計檢定 · Statistical summaries + validation",
        "out": PIPE / "04_statistical" / "EDA_04b_statistical.md",
        "goal": (
            "彙整全域統計(門檻/分佈/條件別)與方法學驗證(known-regulator ranking AUROC 0.85、"
            "dropout 診斷、情境專一性 artifact vs true)。這是「檢定層」——把處理後資料轉成可判讀的統計宣稱。 / "
            "Aggregate global/per-condition statistics and the methodological-validation artifacts."
        ),
        "inputs": ["03_processed/*", "04_results (target_cards)"],
        "repro": "summary/condition_stats 由 statistical_{py,r} 重算(24/24 parity PASS);benchmark_results 為凍結驗證輸出。",
        "assets": {
            "summary_statistics.csv": PIPE / "04_statistical" / "data" / "summary_statistics.csv",
            "condition_stats.csv": PIPE / "04_statistical" / "data" / "condition_stats.csv",
            "benchmark_results.csv (AUROC 0.85 set)": PIPE / "methodological_validation" / "benchmark_results.csv",
        },
    },
    {
        "id": "05_visualization",
        "title": "視覺化 · Visualization catalog",
        "out": PIPE / "05_visualization" / "EDA_05_visualization.md",
        "goal": (
            "凍結 53 張 refined publication 圖的目錄(每張:族系、來源資料、再導出數字),確保每張圖可追溯回上游"
            "階段。 / Freeze the 53-figure publication catalog with per-figure lineage back to a pipeline stage."
        ),
        "inputs": ["04_statistical/*", "03_processed/*"],
        "repro": "圖目錄 REFINED_CATALOG_53.csv;lineage 見 reproducibility_audit/figure_registry.csv。",
        "assets": {
            "REFINED_CATALOG_53.csv": PIPE / "05_visualization" / "refined_figures" / "REFINED_CATALOG_53.csv",
        },
    },
]


# --------------------------------------------------------------------------- #
# Profiling helpers (all deterministic, NaN-safe).
# --------------------------------------------------------------------------- #
def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fmt(x) -> str:
    if pd.isna(x):
        return "—"
    if isinstance(x, float):
        return FLOAT_FMT.format(x)
    return str(x)


def _is_numeric(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)


def _schema_table(df: pd.DataFrame) -> str:
    lines = ["| column | dtype | missing % | distinct |", "|---|---|---|---|"]
    for col in df.columns:
        s = df[col]
        miss = 100.0 * s.isna().mean()
        lines.append(f"| `{col}` | {s.dtype} | {miss:.1f}% | {s.nunique(dropna=True)} |")
    return "\n".join(lines)


def _numeric_summary(df: pd.DataFrame) -> str:
    num_cols = [c for c in df.columns if _is_numeric(df[c])]
    if not num_cols:
        return "_(no numeric columns)_"
    lines = ["| column | count | missing % | min | median | max | mean |", "|---|---|---|---|---|---|---|"]
    for col in num_cols:
        s = df[col]
        n = int(s.notna().sum())
        miss = 100.0 * s.isna().mean()
        if n == 0:  # all-NaN column: report dashes, never compute mean-of-empty
            lines.append(f"| `{col}` | 0 | 100.0% | — | — | — | — |")
            continue
        lines.append(
            f"| `{col}` | {n} | {miss:.1f}% | {_fmt(s.min())} | {_fmt(s.median())} | "
            f"{_fmt(s.max())} | {_fmt(s.mean())} |"
        )
    return "\n".join(lines)


def _categorical_summary(df: pd.DataFrame) -> str:
    cat_cols = [
        c for c in df.columns
        if (not _is_numeric(df[c])) and df[c].nunique(dropna=True) <= CATEGORICAL_MAX_CARD
    ]
    if not cat_cols:
        return "_(no low-cardinality categorical columns)_"
    blocks = []
    for col in cat_cols:
        s = df[col]
        vc = s.value_counts(dropna=False)
        rows = []
        for val, cnt in vc.items():
            label = "(missing)" if pd.isna(val) else f"`{val}`"
            rows.append((label, int(cnt)))
        # deterministic order: by count desc, then label asc
        rows.sort(key=lambda r: (-r[1], r[0]))
        shown = rows[:MAX_CATEGORICAL_LEVELS]
        if len(rows) > MAX_CATEGORICAL_LEVELS:
            other = sum(c for _, c in rows[MAX_CATEGORICAL_LEVELS:])
            shown.append(("(other)", other))
        body = " · ".join(f"{lab}={cnt}" for lab, cnt in shown)
        blocks.append(f"- **`{col}`**: {body}")
    return "\n".join(blocks)


def _render_stage(stage: Dict) -> str:
    out = [f"# EDA — {stage['title']}", ""]
    out.append("> **本階段目標為何 · Stage goal**")
    out.append(">")
    for line in stage["goal"].split(" / "):
        out.append(f"> {line.strip()}")
    out.append("")
    out.append("**輸入 · Inputs**")
    for i in stage["inputs"]:
        out.append(f"- {i}")
    out.append("")
    out.append(f"**重現指令 · Reproduce**: {stage['repro']}")
    out.append("")
    out.append(
        "> `unknown != 0`: 缺失以 missingness% 呈現,類別分佈保留 `(missing)` 桶;NaN 不會被當成 0。"
    )
    out.append("")

    for label, path in stage["assets"].items():
        out.append(f"## {label}")
        if not path.exists():
            out.append(f"\n**MISSING on disk**: `{path.relative_to(REPO)}`\n")
            continue
        df = pd.read_csv(path, low_memory=False)
        out.append("")
        out.append(f"- **path**: `{path.relative_to(REPO)}`")
        out.append(f"- **shape** (parsed records): **{df.shape[0]:,} rows × {df.shape[1]} cols**")
        out.append(f"- **md5**: `{_md5(path)}`  (cross-check FREEZE_MANIFEST.csv)")
        out.append("")
        out.append("### Schema & missingness")
        out.append(_schema_table(df))
        out.append("")
        out.append("### Numeric summary")
        out.append(_numeric_summary(df))
        out.append("")
        out.append("### Categorical / low-cardinality distributions")
        out.append(_categorical_summary(df))
        out.append("")

    out.append("---")
    out.append(
        "_Regenerate: `python scripts/generate_stage_eda.py`. Deterministic (no timestamp); "
        "guarded by `tests/test_generate_stage_eda.py`. Part of the release freeze — see "
        "`docs/mvp-research/pipeline/EDA_INDEX.md`._"
    )
    out.append("")
    return "\n".join(out)


def _render_index() -> str:
    out = ["# EDA index — per-stage freeze inventory", ""]
    out.append(
        "每個 pipeline 階段一份 EDA 盤點報告,附「本階段目標」、shape、逐欄缺失率、關鍵分佈、md5"
        "(對 `FREEZE_MANIFEST.csv`)與重現指令。全部由 `scripts/generate_stage_eda.py` deterministically 產生。"
    )
    out.append("")
    out.append("| # | Stage | Report |")
    out.append("|---|---|---|")
    for stage in STAGES:
        rel = stage["out"].relative_to(PIPE)
        out.append(f"| {stage['id']} | {stage['title']} | [`{rel}`]({rel}) |")
    out.append("")
    out.append(
        "視覺化下游的 **前端(React static portal)** 與 **06_animation** 為展示層,其盤點見 "
        "`docs/mvp-research/pipeline/07_dashboard/` 與 `frontend/webserver/README.md`;"
        "上傳功能(即時)為獨立工具,見其自身 PR。"
    )
    out.append("")
    return "\n".join(out)


def _write(path: Path, content: str, check: bool) -> bool:
    """Return True if the file is up to date, False if it was (or would be) changed."""
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == content:
        return True
    if not check:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return False


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 if any report is stale (do not write)")
    args = ap.parse_args(argv)

    stale: List[str] = []
    for stage in STAGES:
        content = _render_stage(stage)
        if not _write(stage["out"], content, args.check):
            stale.append(str(stage["out"].relative_to(REPO)))

    index_path = PIPE / "EDA_INDEX.md"
    if not _write(index_path, _render_index(), args.check):
        stale.append(str(index_path.relative_to(REPO)))

    if args.check and stale:
        print("STALE EDA reports (run scripts/generate_stage_eda.py):")
        for s in stale:
            print(f"  - {s}")
        return 1
    action = "checked" if args.check else "wrote"
    print(f"{action} {len(STAGES)} stage reports + index (up to date)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
