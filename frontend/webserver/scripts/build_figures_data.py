#!/usr/bin/env python3
"""Build a real, non-synthetic "figure atlas" dataset for the CD4 Target
Discovery Portal frontend (PART 1 of a two-part effort; a later change
rewrites the frontend to consume this file instead of client-side-generated
synthetic figures).

This is a manual, offline extraction step (run by hand, like the sibling
`export_real_data.py` in this same directory) that reads directly from this
repo's already-computed pipeline output tables -- never invents a gene name,
log-fold-change, p-value, cluster label, or correlation value. Every number
in the output is read verbatim (only rounded to 4 decimals, or aggregated by
a documented mean/rank/bucket rule) from one of these six source files:

  - metadata/suppl_tables/full_signed_DE/part-000.parquet + part-001.parquet
      This repo's genome-scale signed differential-expression table for the
      CD4 Perturb-seq screen (target_gene, downstream_gene, culture_condition,
      log_fc, adj_p_value, ...). Backs both the `volcano` panel (on-target
      knockdown effect per condition, target_gene == downstream_gene, 20,581
      rows) and the `cytokine` panel (regulators of a fixed canonical
      cytokine gene list, ranked by signed log_fc among significant hits).
  - src/4_polarization_signatures/results/polarization_model_coefs.csv
      This repo's Th1/Th2/Treg polarization regression coefficients per gene
      (coef_mean, coef_sem, r2, state). Backs the `polar` panel (Th2-vs-Th1
      polarization-skew scatter for every gene modeled in both states).
  - src/6_functional_interaction/results/clustering_nde75ntotal50_enrichment_annotated.csv
      This repo's 112 co-regulation clusters with CORUM/STRINGdb/KEGG/
      Reactome-informed manual annotations and per-condition active-member
      counts. Backs the `heatmap` panel (fraction of each cluster's members
      differentially expressed per condition).
  - src/6_functional_interaction/results/cluster_autoimmune_enrichment_results.csv
      This repo's cluster x autoimmune/inflammatory-disease enrichment
      results (odds_ratio, p_value, gene_set). Backs the `gwas` panel,
      filtered to gene_set == "regulators" (the perturbed-gene/regulator set,
      as opposed to the downstream_Rest/downstream_Stim8hr/downstream_Stim48hr
      differential-expression-target sets also present in this file).
  - src/3_DE_analysis/power_analysis/heldout_correlation_results.csv
      This repo's held-out-donor replication analysis: log-fold-change
      correlation between independent donor splits, at three subsampled
      sequencing depths (depth_perc in {10, 50, 100}) and varying per-target
      cell counts. Backs the `power` panel (a real reproducibility-vs-
      cell-count proxy, binned and averaged -- see BUCKET_SIZE below).

`sourceVersion` is copied verbatim from the already-committed
frontend/webserver/public/real-dataset.json (produced by export_real_data.py)
so both files self-report where their inputs came from.

burden and umap are intentionally NOT included here: burden is built by the
frontend directly from fields already present in real-dataset.json, and umap
has no real 2D embedding coordinates anywhere in this repo -- the frontend
will render that panel as an honest "data unavailable" state rather than
fabricate coordinates.

Usage (from repo root):
    pip install pandas numpy pyarrow
    python3 frontend/webserver/scripts/build_figures_data.py

Writes frontend/webserver/public/figures.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]

FULL_SIGNED_DE_DIR = REPO_ROOT / "metadata" / "suppl_tables" / "full_signed_DE"
POLARIZATION_COEFS_CSV = REPO_ROOT / "src" / "4_polarization_signatures" / "results" / "polarization_model_coefs.csv"
CLUSTERING_ANNOTATED_CSV = (
    REPO_ROOT / "src" / "6_functional_interaction" / "results" / "clustering_nde75ntotal50_enrichment_annotated.csv"
)
GWAS_ENRICHMENT_CSV = REPO_ROOT / "src" / "6_functional_interaction" / "results" / "cluster_autoimmune_enrichment_results.csv"
POWER_ANALYSIS_CSV = REPO_ROOT / "src" / "3_DE_analysis" / "power_analysis" / "heldout_correlation_results.csv"

REAL_DATASET_JSON = REPO_ROOT / "frontend" / "webserver" / "public" / "real-dataset.json"
OUT_PATH = Path(__file__).resolve().parents[1] / "public" / "figures.json"

CONDITIONS = ["Rest", "Stim8hr", "Stim48hr"]

CANONICAL_CYTOKINES = [
    "IFNG", "IL2", "IL2RA", "IL3", "IL4", "IL5", "IL6", "IL10", "IL13",
    "IL21", "IL22", "TNF", "CSF2", "LTA",
]
CYTOKINE_SIG_P = 0.1
CYTOKINE_MIN_REGULATORS = 20
CYTOKINE_TOP_N = 12

GWAS_GENE_SET = "regulators"

# Power-analysis n_cells bucket width (round to nearest 10, per spec).
POWER_BUCKET_SIZE = 10

R = 4  # float rounding


def r4(x) -> float:
    return round(float(x), R)


def neg_log10_p(p) -> float:
    return r4(min(50.0, -np.log10(max(float(p), 1e-50))))


def main() -> None:
    real_dataset = json.loads(REAL_DATASET_JSON.read_text())
    source_version = real_dataset["sourceVersion"]
    print(f"Copied sourceVersion from {REAL_DATASET_JSON.relative_to(REPO_ROOT)}", file=sys.stderr)

    print(f"Loading real signed DE table from {FULL_SIGNED_DE_DIR}", file=sys.stderr)
    de = pd.concat(
        [
            pd.read_parquet(FULL_SIGNED_DE_DIR / "part-000.parquet"),
            pd.read_parquet(FULL_SIGNED_DE_DIR / "part-001.parquet"),
        ],
        ignore_index=True,
    )
    print(f"Full signed DE table: {len(de)} rows", file=sys.stderr)

    # ---------------------------------------------------------------
    # volcano: on-target knockdown effect per condition
    # ---------------------------------------------------------------
    onto = de[de["target_gene"] == de["downstream_gene"]]
    print(f"On-target rows (target_gene == downstream_gene): {len(onto)}", file=sys.stderr)

    volcano: dict[str, list[dict]] = {}
    for cond in CONDITIONS:
        sub = onto[onto["culture_condition"] == cond]
        rows = [
            {
                "g": row.target_gene,
                "x": r4(row.log_fc),
                "y": neg_log10_p(row.adj_p_value),
            }
            for row in sub.itertuples(index=False)
        ]
        volcano[cond] = rows
        print(f"volcano[{cond}]: {len(rows)} rows", file=sys.stderr)

    # ---------------------------------------------------------------
    # cytokine: top/bottom regulators per canonical cytokine
    # ---------------------------------------------------------------
    cytokine: dict[str, list[dict]] = {}
    for cyt in CANONICAL_CYTOKINES:
        sub = de[(de["downstream_gene"] == cyt) & (de["adj_p_value"] < CYTOKINE_SIG_P)]
        if sub.empty:
            print(f"cytokine[{cyt}]: 0 significant regulators, skipped", file=sys.stderr)
            continue
        # For each target_gene, keep the single row with smallest adj_p_value.
        best = sub.sort_values("adj_p_value").groupby("target_gene", as_index=False).head(1)
        n_regulators = len(best)
        if n_regulators < CYTOKINE_MIN_REGULATORS:
            print(
                f"cytokine[{cyt}]: {n_regulators} significant regulators (< {CYTOKINE_MIN_REGULATORS}), skipped",
                file=sys.stderr,
            )
            continue
        best_sorted = best.sort_values("log_fc")
        top_bottom = pd.concat([best_sorted.head(CYTOKINE_TOP_N), best_sorted.tail(CYTOKINE_TOP_N)])
        top_bottom = top_bottom.drop_duplicates(subset="target_gene").sort_values("log_fc")
        rows = [{"g": row.target_gene, "x": r4(row.log_fc)} for row in top_bottom.itertuples(index=False)]
        cytokine[cyt] = rows
        print(f"cytokine[{cyt}]: {n_regulators} significant regulators -> {len(rows)} emitted", file=sys.stderr)

    cytokines_list = sorted(cytokine.keys())

    # ---------------------------------------------------------------
    # polar: Th2-vs-Th1 polarization skew
    # ---------------------------------------------------------------
    print(f"Loading polarization model coefficients from {POLARIZATION_COEFS_CSV}", file=sys.stderr)
    pol = pd.read_csv(POLARIZATION_COEFS_CSV)
    pol = pol.rename(columns={"Unnamed: 0": "gene"})
    th1 = pol[pol["state"] == "Th1"].set_index("gene")["coef_mean"]
    th2 = pol[pol["state"] == "Th2"].set_index("gene")["coef_mean"]
    common_genes = sorted(set(th1.index) & set(th2.index))
    polar = []
    for gene in common_genes:
        c1 = th1[gene]
        c2 = th2[gene]
        polar.append({"g": gene, "x": r4(c2 - c1), "y": r4(max(abs(c1), abs(c2)))})
    print(f"polar: {len(polar)} genes present in both Th1 and Th2", file=sys.stderr)

    # ---------------------------------------------------------------
    # heatmap: fraction of cluster members active per condition
    # ---------------------------------------------------------------
    print(f"Loading cluster enrichment/annotation table from {CLUSTERING_ANNOTATED_CSV}", file=sys.stderr)
    clust = pd.read_csv(CLUSTERING_ANNOTATED_CSV)

    def frac(count, size):
        size = float(size) if pd.notna(size) else 0.0
        if size <= 0:
            return 0.0
        return float(count) / size

    heatmap_entries = []
    for row in clust.itertuples(index=False):
        ann = getattr(row, "manual_annotation")
        label = ann if (pd.notna(ann) and ann != "unknown") else f"cluster {row.cluster}"
        size = row.cluster_gene_size
        z_row = [
            r4(frac(row.rest_count, size)),
            r4(frac(row.stim8hr_count, size)),
            r4(frac(row.stim48hr_count, size)),
        ]
        heatmap_entries.append({"cluster": row.cluster, "label": label, "z": z_row})
    heatmap_entries.sort(key=lambda e: e["label"])
    heatmap = {
        "rows": [{"cluster": e["cluster"], "label": e["label"]} for e in heatmap_entries],
        "cols": CONDITIONS,
        "z": [e["z"] for e in heatmap_entries],
    }
    print(f"heatmap: {len(heatmap['rows'])} clusters", file=sys.stderr)

    # ---------------------------------------------------------------
    # gwas: disease enrichment per cluster, regulators gene_set
    # ---------------------------------------------------------------
    print(f"Loading cluster autoimmune-disease enrichment from {GWAS_ENRICHMENT_CSV}", file=sys.stderr)
    gwas_df = pd.read_csv(GWAS_ENRICHMENT_CSV)
    unique_gene_sets = sorted(gwas_df["gene_set"].unique())
    print(f"gene_set unique values: {unique_gene_sets}; using gene_set == {GWAS_GENE_SET!r}", file=sys.stderr)
    gwas_reg = gwas_df[gwas_df["gene_set"] == GWAS_GENE_SET]

    gwas: dict[str, list[dict]] = {}
    for disease, sub in gwas_reg.groupby("disease"):
        sub_sorted = sub.sort_values("cluster")
        gwas[disease] = [
            {"cluster": str(row.cluster), "y": neg_log10_p(row.p_value)}
            for row in sub_sorted.itertuples(index=False)
        ]
    diseases_list = sorted(gwas.keys())
    print(f"gwas: {len(diseases_list)} diseases, {len(gwas_reg)} total cluster-disease rows", file=sys.stderr)

    # ---------------------------------------------------------------
    # power: held-out replication correlation vs cell count, per depth
    # ---------------------------------------------------------------
    print(f"Loading held-out correlation power analysis from {POWER_ANALYSIS_CSV}", file=sys.stderr)
    power_df = pd.read_csv(POWER_ANALYSIS_CSV)
    depths = sorted(int(d) for d in power_df["depth_perc"].unique())

    power: dict[str, list[dict]] = {}
    for depth in depths:
        sub = power_df[power_df["depth_perc"] == depth].copy()
        sub["n_cells_bucket"] = (sub["n_cells"] / POWER_BUCKET_SIZE).round().astype(int) * POWER_BUCKET_SIZE
        grouped = sub.groupby("n_cells_bucket")["lfc_correlation"].mean().reset_index()
        grouped = grouped.sort_values("n_cells_bucket")
        power[str(depth)] = [
            {"n_cells": int(row.n_cells_bucket), "corr": r4(row.lfc_correlation)}
            for row in grouped.itertuples(index=False)
        ]
        print(f"power[{depth}]: {len(sub)} rows -> {len(power[str(depth)])} n_cells buckets", file=sys.stderr)

    # ---------------------------------------------------------------
    out = {
        "sourceVersion": source_version,
        "conditions": CONDITIONS,
        "cytokines": cytokines_list,
        "diseases": diseases_list,
        "depths": depths,
        "volcano": volcano,
        "cytokine": cytokine,
        "polar": polar,
        "heatmap": heatmap,
        "gwas": gwas,
        "power": power,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out))
    print(f"Wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1024 / 1024:.2f} MB)", file=sys.stderr)


if __name__ == "__main__":
    main()
