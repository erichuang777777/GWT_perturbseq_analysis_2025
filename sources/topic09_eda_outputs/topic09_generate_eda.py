import json
from pathlib import Path

import numpy as np
import pandas as pd


OUT = Path("sources/topic09_eda_outputs")
OUT.mkdir(parents=True, exist_ok=True)


def load_csv(path):
    df = pd.read_csv(path)
    for col in list(df.columns):
        if col.startswith("Unnamed") or col == "H1":
            df = df.rename(columns={col: "row_id"})
            break
    return df


sample = load_csv("metadata/suppl_tables/sample_metadata.suppl_table.csv")
de = load_csv("metadata/suppl_tables/DE_stats.suppl_table.csv")
kd = load_csv("metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv")
sg = load_csv("metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv")

summary = {
    "sample_rows": int(len(sample)),
    "sample_columns": list(sample.columns),
    "de_rows": int(len(de)),
    "de_columns": list(de.columns),
    "kd_rows": int(len(kd)),
    "kd_columns": list(kd.columns),
    "sgrna_rows": int(len(sg)),
    "sgrna_columns": list(sg.columns),
}

if "target_contrast_gene_name" in de:
    summary["unique_de_targets"] = int(de["target_contrast_gene_name"].nunique())
if "target_gene_name" in sg:
    summary["unique_sgrna_targets"] = int(sg["target_gene_name"].nunique())
elif "perturbed_gene_name" in sg:
    summary["unique_sgrna_targets"] = int(sg["perturbed_gene_name"].nunique())
if "culture_condition" in de:
    summary["conditions"] = sorted(de["culture_condition"].dropna().unique().tolist())

sample.groupby(["10xrun_id", "culture_condition"]).size().reset_index(
    name="n_samples"
).to_csv(OUT / "sample_by_run_condition.csv", index=False)
sample.groupby(["donor_id", "culture_condition"]).size().reset_index(
    name="n_samples"
).to_csv(OUT / "sample_by_donor_condition.csv", index=False)

num_cols = [
    "n_cells_target",
    "n_up_genes",
    "n_down_genes",
    "n_total_de_genes",
    "ontarget_effect_size",
    "target_baseMean",
    "n_downstream",
    "crossdonor_correlation_mean",
    "crossdonor_correlation_min",
    "crossguide_correlation",
]
for col in num_cols:
    if col in de.columns:
        de[col] = pd.to_numeric(de[col], errors="coerce")

if "culture_condition" in de:
    de.groupby("culture_condition").agg(
        rows=("target_contrast_gene_name", "size"),
        targets=("target_contrast_gene_name", "nunique"),
        median_n_cells_target=("n_cells_target", "median"),
        median_total_de_genes=("n_total_de_genes", "median"),
        mean_total_de_genes=("n_total_de_genes", "mean"),
        pct_ontarget_significant=(
            "ontarget_significant",
            lambda x: float((x.astype(str).str.lower() == "true").mean() * 100),
        ),
        pct_offtarget_flag=(
            "offtarget_flag",
            lambda x: float((x.astype(str).str.lower() == "true").mean() * 100),
        ),
        rows_crossdonor=("crossdonor_correlation_mean", lambda x: int(x.notna().sum())),
        rows_crossguide=("crossguide_correlation", lambda x: int(x.notna().sum())),
    ).reset_index().to_csv(OUT / "de_summary_by_condition.csv", index=False)

for col in [
    "n_total_genes_category",
    "ontarget_effect_category",
    "ontarget_significant",
    "offtarget_flag",
]:
    if col in de.columns and "culture_condition" in de.columns:
        de.groupby(["culture_condition", col], observed=False).size().reset_index(
            name="n"
        ).to_csv(OUT / f"de_counts_by_{col}.csv", index=False)

rank = de.copy()
rank["offtarget_bool"] = (
    rank["offtarget_flag"].astype(str).str.lower().eq("true")
    if "offtarget_flag" in rank
    else False
)
rank["ontarget_bool"] = (
    rank["ontarget_significant"].astype(str).str.lower().eq("true")
    if "ontarget_significant" in rank
    else False
)
rank_cols = [
    "target_contrast_gene_name",
    "culture_condition",
    "n_cells_target",
    "n_up_genes",
    "n_down_genes",
    "n_total_de_genes",
    "ontarget_effect_size",
    "ontarget_significant",
    "target_baseMean",
    "offtarget_flag",
    "crossdonor_correlation_mean",
    "crossguide_correlation",
]
rank_cols = [col for col in rank_cols if col in rank.columns]

rank.sort_values(["n_total_de_genes", "ontarget_bool"], ascending=[False, False])[
    rank_cols
].head(100).to_csv(OUT / "top100_targets_by_total_de_genes.csv", index=False)

rank[(rank["ontarget_bool"]) & (~rank["offtarget_bool"])].sort_values(
    ["n_total_de_genes", "ontarget_effect_size"], ascending=[False, False]
)[rank_cols].head(100).to_csv(OUT / "top100_targets_ontarget_no_offtarget.csv", index=False)

risk = rank.copy()
risk["has_crossdonor"] = (
    risk["crossdonor_correlation_mean"].notna()
    if "crossdonor_correlation_mean" in risk
    else False
)
risk["has_crossguide"] = (
    risk["crossguide_correlation"].notna()
    if "crossguide_correlation" in risk
    else False
)
risk["low_crossdonor"] = (
    risk["crossdonor_correlation_mean"] < 0.2
    if "crossdonor_correlation_mean" in risk
    else False
)
risk["low_crossguide"] = (
    risk["crossguide_correlation"] < 0.2
    if "crossguide_correlation" in risk
    else False
)
risk["low_cells"] = (
    risk["n_cells_target"] < risk["n_cells_target"].quantile(0.1)
    if "n_cells_target" in risk
    else False
)
risk_cols = [
    "target_contrast_gene_name",
    "culture_condition",
    "n_cells_target",
    "n_total_de_genes",
    "ontarget_effect_size",
    "offtarget_flag",
    "crossdonor_correlation_mean",
    "crossguide_correlation",
    "has_crossdonor",
    "has_crossguide",
    "low_crossdonor",
    "low_crossguide",
    "low_cells",
]
risk_cols = [col for col in risk_cols if col in risk.columns]
risk[risk["n_total_de_genes"].fillna(0) >= 50][risk_cols].to_csv(
    OUT / "batch_robustness_risk_table_de50.csv", index=False
)

pd.DataFrame(
    [
        {
            "table": "sample_metadata",
            "rows": len(sample),
            "columns": len(sample.columns),
            "path": "metadata/suppl_tables/sample_metadata.suppl_table.csv",
        },
        {
            "table": "DE_stats",
            "rows": len(de),
            "columns": len(de.columns),
            "path": "metadata/suppl_tables/DE_stats.suppl_table.csv",
        },
        {
            "table": "guide_kd_efficiency",
            "rows": len(kd),
            "columns": len(kd.columns),
            "path": "metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv",
        },
        {
            "table": "sgrna_library_metadata",
            "rows": len(sg),
            "columns": len(sg.columns),
            "path": "metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv",
        },
    ]
).to_csv(OUT / "eda_table_inventory.csv", index=False)

kd_summary = {"rows": len(kd), "columns": list(kd.columns)}
if "target_gene_name" in kd.columns:
    kd_summary["targets"] = int(kd["target_gene_name"].nunique())
if "guide_id" in kd.columns:
    kd_summary["guides"] = int(kd["guide_id"].nunique())
if "sgRNA" in sg.columns:
    kd_summary["sgrna_metadata_guides"] = int(sg["sgRNA"].nunique())
if "target_gene_name" in sg.columns:
    sg.groupby("target_gene_name").size().describe().to_frame(
        "guides_per_target"
    ).to_csv(OUT / "sgrna_guides_per_target_summary.csv")
summary["kd_summary"] = kd_summary

with open(OUT / "eda_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

try:
    import matplotlib.pyplot as plt

    plt.switch_backend("Agg")

    fig, ax = plt.subplots(figsize=(8, 5))
    for cond, group in de.groupby("culture_condition"):
        ax.hist(group["n_total_de_genes"].dropna(), bins=50, alpha=0.45, label=str(cond))
    ax.set_xlabel("n_total_de_genes")
    ax.set_ylabel("target-condition rows")
    ax.legend()
    ax.set_title("Distribution of downstream DE gene counts")
    fig.tight_layout()
    fig.savefig(OUT / "hist_n_total_de_genes_by_condition.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 5))
    sub = de[
        ["crossdonor_correlation_mean", "crossguide_correlation", "n_total_de_genes"]
    ].dropna()
    ax.scatter(
        sub["crossdonor_correlation_mean"],
        sub["crossguide_correlation"],
        s=np.clip(sub["n_total_de_genes"] / 10, 5, 80),
        alpha=0.35,
    )
    ax.axhline(0.2, color="grey", lw=1, ls="--")
    ax.axvline(0.2, color="grey", lw=1, ls="--")
    ax.set_xlabel("crossdonor_correlation_mean")
    ax.set_ylabel("crossguide_correlation")
    ax.set_title("Donor vs guide robustness")
    fig.tight_layout()
    fig.savefig(OUT / "scatter_crossdonor_vs_crossguide.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    sub = de[["n_cells_target", "n_total_de_genes", "culture_condition"]].dropna()
    for cond, group in sub.groupby("culture_condition"):
        ax.scatter(group["n_cells_target"], group["n_total_de_genes"], s=8, alpha=0.35, label=str(cond))
    ax.set_xscale("log")
    ax.set_xlabel("n_cells_target (log scale)")
    ax.set_ylabel("n_total_de_genes")
    ax.legend(markerscale=2)
    ax.set_title("Target cell count vs DE breadth")
    fig.tight_layout()
    fig.savefig(OUT / "scatter_cells_vs_de_genes.png", dpi=160)
    plt.close(fig)
except Exception as exc:
    with open(OUT / "plot_error.txt", "w", encoding="utf-8") as f:
        f.write(repr(exc))

print(f"EDA outputs written to {OUT}")
