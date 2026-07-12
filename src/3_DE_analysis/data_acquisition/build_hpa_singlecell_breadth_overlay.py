#!/usr/bin/env python3
"""Build a single-cell-resolution off-context expression-breadth overlay from HPA data.

`metadata/rna_single_cell_type_group.tsv.zip` (Human Protein Atlas, per-gene nCPM across 51
consensus single-cell "Cell type group" categories) has been sitting in this repo, unused, since
its initial commit (confirmed via full git-history search -- see
`docs/data_governance_checklist.md` §6). This repo's existing GTEx-derived safety overlay
(`sources/target_tool_cache/_overlays/gtex_per_tissue.parquet`) already answers "how many bulk
TISSUES express this gene outside CD4-relevant context" -- this script builds the same question
at single-CELL-TYPE resolution instead, which is a materially finer-grained off-target signal for
an immunology platform than bulk tissue (a tissue can look "narrow" in bulk while actually
containing several off-target immune cell populations that only single-cell resolution resolves).

Design mirrors the existing GTEx overlay's stated philosophy exactly (see
`evidence/safety_overlay.py`'s module docstring): "CD4 T cell high expression" is normal, expected
biology on THIS platform, not an off-target risk -- so the "T-cells" category (the direct proxy
for this platform's own context) is excluded from both the breadth count and the max-expression
figure, the same way the GTEx overlay excludes Blood/Spleen. Every OTHER cell type (NK-cells,
B-cells, dendritic cells, hepatocytes, ...) is a legitimate off-target data point.

This is a genuinely independent, additional signal -- NOT a replacement for the existing GTEx
overlay, and NOT folded into `composite_safety_liability` (which is already calibrated and
tested against the two-way gnomAD+GTEx composite). It is exposed as its own standalone
descriptive column so existing composite behavior/tests are untouched.

Output columns (mirrors `gtex_per_tissue.parquet`'s naming convention exactly):
  ensembl_id, gene_symbol, n_celltypes_expressed, max_expression_outside_tcell_context

"Expressed" = nCPM > EXPRESSED_NCPM_THRESHOLD (1.0, a standard HPA-style detection cutoff --
independently chosen for this nCPM-normalized single-cell data, not inherited from GTEx's
nTPM-based, undocumented threshold, since the two are different units/assays).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE = _REPO_ROOT / "metadata" / "rna_single_cell_type_group.tsv.zip"
DEFAULT_OUTPUT = (
    _REPO_ROOT / "sources" / "target_tool_cache" / "_overlays" / "hpa_singlecell_breadth_seed.parquet"
)

ON_CONTEXT_CELL_TYPE = "T-cells"
EXPRESSED_NCPM_THRESHOLD = 1.0


def build_overlay(df: pd.DataFrame) -> pd.DataFrame:
    required = {"Gene", "Gene name", "Cell type group", "nCPM"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"HPA source is missing expected columns: {sorted(missing)}")

    off_context = df[df["Cell type group"] != ON_CONTEXT_CELL_TYPE].copy()
    expressed = off_context[off_context["nCPM"] > EXPRESSED_NCPM_THRESHOLD]

    breadth = expressed.groupby("Gene").size().rename("n_celltypes_expressed")
    max_expr = off_context.groupby("Gene")["nCPM"].max().rename("max_expression_outside_tcell_context")
    symbol = df.groupby("Gene")["Gene name"].first().rename("gene_symbol")

    out = pd.concat([symbol, breadth, max_expr], axis=1).reset_index()
    out = out.rename(columns={"Gene": "ensembl_id"})
    out["n_celltypes_expressed"] = out["n_celltypes_expressed"].fillna(0).astype(int)
    out["max_expression_outside_tcell_context"] = out["max_expression_outside_tcell_context"].astype(float)

    out = out[["ensembl_id", "gene_symbol", "n_celltypes_expressed", "max_expression_outside_tcell_context"]]
    out = out.sort_values("ensembl_id").reset_index(drop=True)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args(argv)

    if not args.source.exists():
        raise SystemExit(f"source file not found: {args.source}")

    df = pd.read_csv(args.source, sep="\t", compression="zip")
    overlay = build_overlay(df)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    overlay.to_parquet(args.output, index=False)
    print(f"wrote {len(overlay)} genes -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
