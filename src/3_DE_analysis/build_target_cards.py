"""Build target-condition cards for Topic 14/15.

This script combines DE_stats and guide KD tables into a compact, reproducible
target-card table that follows:
  sources/topic14_target_card_specification.md

It intentionally avoids touching h5ad files.  The output can be used as CSV-first
evidence ranking and then passed to downstream h5ad-based validation.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd


POSITIVE_CONTROLS = {
    "CD3D",
    "CD3E",
    "CD3G",
    "CD247",
    "CD28",
    "ICOS",
    "CTLA4",
    "CD80",
    "CD86",
    "IL2RA",
    "IL2RB",
    "IL7R",
    "LCK",
    "ZAP70",
    "JAK3",
    "PTPN2",
    "FOXP3",
    "PTGER4",
}

PATHWAY_AXIS_HINTS: Dict[str, Sequence[str]] = {
    "TCR_core": ("CD3D", "CD3E", "CD3G", "CD247", "ZAP70", "LCK", "LAT", "LCP2", "TRBC1", "TRBC2"),
    "Costimulation": ("CD28", "ICOS", "CTLA4", "CD40", "CD40LG", "TIGIT", "LAG3"),
    "Cytokine_signaling": ("IL2RA", "IL2RB", "IL7R", "IFNAR1", "IFNAR2", "JAK1", "JAK3", "STAT1", "STAT3", "STAT4", "STAT5A", "STAT5B"),
    "Th1": ("TBX21", "IFNG", "STAT4", "CXCR3", "EOMES"),
    "Th2": ("GATA3", "IL4", "IL13", "IL4R", "STAT6"),
    "Th17": ("RORC", "IL17A", "IL17F", "IL23R", "CCR6"),
    "Treg": ("FOXP3", "IKZF2", "CTLA4", "IL2RA", "TIGIT", "LAG3"),
    "Trafficking": ("CCR7", "SELL", "S1PR1", "CXCR3", "CXCR4", "CCR5"),
    "Exhaustion": ("PDCD1", "HAVCR2", "TOX", "ENTPD1"),
    "Cell_cycle": ("MKI67", "TOP2A", "MCM7", "PCNA", "TYMS"),
}

CLINICAL_BENCHMARK_KEYWORDS = {
    "TCR/CD3 tolerance": ("CD3D", "CD3E", "CD3G", "CD247", "CD2", "CD28", "TCR"),
    "Direct CD4": ("CD4",),
    "Costimulation blockade": ("CD28", "CTLA4", "CD80", "CD86"),
    "Calcineurin/NFAT": ("NFATC1", "NFATC2", "PPP3CA", "PPP3CB", "PPP3CC", "PPP3R1"),
    "IL-2 / IL-2R": ("IL2RA", "IL2RB", "IL2RG"),
    "JAK/STAT cytokine signaling": ("JAK1", "JAK2", "JAK3", "STAT1", "STAT3", "STAT4", "STAT5A", "STAT5B", "SOCS"),
    "S1P trafficking": ("CCR7", "S1PR1", "S1PR2", "S1PR3", "S1PR4", "S1PR5"),
}

BENCHMARK_CSV_DEFAULT = Path("sources/topic05_successful_drug_benchmarks.csv")


def _to_bool(v: object) -> bool:
    if isinstance(v, bool):
        return v
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return False
    s = str(v).strip().lower()
    return s in {"true", "1", "yes", "y", "t"}


def _to_float(v: object) -> float:
    try:
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return np.nan
        return float(str(v).strip())
    except (TypeError, ValueError):
        return np.nan


def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip() for c in df.columns]
    # Remove empty first index-like column produced by CSV export.
    drop_cols = [c for c in df.columns if not c or re.fullmatch(r"index|Unnamed:.*", c, flags=re.IGNORECASE)]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    return df


def _safe_split_tokens(x: str) -> List[str]:
    if not isinstance(x, str):
        return []
    return [p.strip() for p in re.split(r"[;,]", x) if p.strip()]


def _pathway_axis(gene: Optional[str]) -> str:
    if not isinstance(gene, str) or not gene:
        return "unassigned"
    for axis, genes in PATHWAY_AXIS_HINTS.items():
        if gene in genes:
            return axis
    return "unassigned"


def _clinical_axis(gene: str) -> str:
    if not gene:
        return "unassigned"
    g = gene.upper()
    for axis, markers in CLINICAL_BENCHMARK_KEYWORDS.items():
        for m in markers:
            if m in g:
                return axis
    return "unassigned"


def _first_match_in_benchmark(gene: str, bench: Optional[pd.DataFrame]) -> str:
    if bench is None or not isinstance(gene, str):
        return ""
    pattern = re.compile(re.escape(gene), re.IGNORECASE)
    mask = bench["target_or_modality"].fillna("").str.contains(pattern)
    match = bench.loc[mask, "representative_drugs"]
    if match.empty:
        return ""
    return match.iloc[0]


def _build_guide_summary(
    guide_df: pd.DataFrame,
) -> pd.DataFrame:
    g = guide_df.copy()
    g["signif_knockdown"] = g["signif_knockdown"].apply(_to_bool)
    g["guide_id"] = g.get("guide_id", g.index.astype(str))
    agg = (
        g.groupby(["perturbed_gene_id", "culture_condition"], dropna=False)
        .agg(
            n_guides=("guide_id", "nunique"),
            guide_signif_ratio=("signif_knockdown", "mean"),
            guide_fdr_min=("adj_p_value", lambda s: pd.to_numeric(s, errors="coerce").min()),
            guide_t_abs_median=("t_statistic", lambda s: pd.to_numeric(s, errors="coerce").abs().median()),
        )
        .reset_index()
        .rename(columns={"perturbed_gene_id": "target_id"})
    )
    return agg


def _load_benchmark(path: Optional[Path]) -> Optional[pd.DataFrame]:
    if path is None:
        return None
    if not path.exists():
        return None
    return pd.read_csv(path)


def _make_score(
    row: pd.Series,
    min_cells: int = 200,
    min_de_genes: int = 50,
) -> int:
    replicate = (
        (row["n_cells_target"] >= min_cells)
        and (row["n_total_de_genes"] >= min_de_genes)
        and bool(row["ontarget_significant"])
        and not bool(row["offtarget_flag"])
        and (row["crossdonor_correlation_mean"] >= 0.2)
        and (row["crossguide_correlation"] >= 0.2)
    )
    if (
        replicate
        and row["guide_signif_ratio"] >= 0.5
        and row["guide_fdr_min"] <= 0.05
        and row["crossdonor_correlation_mean"] >= 0.3
        and row["crossguide_correlation"] >= 0.3
        and row["n_guides"] >= 2
    ):
        return 4
    if replicate and row["n_guides"] >= 2 and row["fdr_min"] <= 0.1:
        return 3
    if (row["n_cells_target"] >= min_cells) and row["ontarget_significant"]:
        return 2
    return 1


def _score_cap_reasons(
    row: pd.Series,
    min_cells: int = 200,
    min_de_genes: int = 50,
) -> str:
    reasons = []
    if row["n_cells_target"] < min_cells:
        reasons.append("low_cells")
    if row["n_total_de_genes"] < min_de_genes:
        reasons.append("low_signal")
    if not bool(row["ontarget_significant"]):
        reasons.append("direction_unclear")
    if bool(row["offtarget_flag"]):
        reasons.append("high_offtarget")
    if row["crossdonor_correlation_mean"] < 0.2 or row["crossguide_correlation"] < 0.2:
        reasons.append("weak_replicability")
    if pd.isna(row["fdr_min"]) or row["fdr_min"] > 0.1:
        reasons.append("guide_limit")
    if pd.isna(row["condition_specificity_score"]):
        reasons.append("single_donor_dominance")
    if row["guide_signif_ratio"] < 0.5:
        reasons.append("guides_inconsistent")
    if row.get("batch_sensitivity_flag") == "sensitive":
        reasons.append("batch_sensitive")
    if row["n_guides"] < 2:
        reasons.append("single_donor_dominance")
    return ";".join(reasons) if reasons else "none"


def _build_cards(
    de_df: pd.DataFrame,
    guide_df: pd.DataFrame,
    lib_map: Optional[pd.DataFrame],
    out_path: Path,
    benchmark: Optional[pd.DataFrame],
    min_cells: int = 200,
    min_de_genes: int = 50,
) -> None:
    de = de_df.copy()
    # Keep only usable numeric rows.
    numeric_cols = [
        "n_cells_target",
        "n_up_genes",
        "n_down_genes",
        "n_total_de_genes",
        "ontarget_effect_size",
        "crossdonor_correlation_mean",
        "crossdonor_correlation_min",
        "crossguide_correlation",
    ]
    for c in numeric_cols:
        de[c] = pd.to_numeric(de[c], errors="coerce")

    de["ontarget_significant"] = de["ontarget_significant"].apply(_to_bool)
    de["offtarget_flag"] = de["offtarget_flag"].apply(_to_bool)

    # Add target gene symbol from DE itself (preferred), then library map fallback.
    de["target"] = de["target_contrast_gene_name"].fillna(de["target_contrast"])

    if lib_map is not None and "target_gene_id" in lib_map.columns:
        id_to_name = (
            lib_map.dropna(subset=["target_gene_id"])
            .drop_duplicates("target_gene_id")
            .set_index("target_gene_id")["target_gene_name"]
            .to_dict()
        )
        de["target"] = de.apply(
            lambda r: r["target"] if pd.notna(r["target"]) else id_to_name.get(r["target_contrast"], ""),
            axis=1,
        )

    guide_summary = _build_guide_summary(guide_df)
    card_df = de.merge(
        guide_summary,
        left_on=["target_contrast", "culture_condition"],
        right_on=["target_id", "culture_condition"],
        how="left",
    )

    card_df["n_guides"] = card_df["n_guides"].fillna(0).astype(int)
    card_df["guide_signif_ratio"] = card_df["guide_signif_ratio"].fillna(0.0)
    card_df["guide_fdr_min"] = card_df["guide_fdr_min"].astype(float)
    card_df["guide_t_abs_median"] = card_df["guide_t_abs_median"].astype(float)
    card_df["fdr_min"] = card_df["guide_fdr_min"]

    # Replace missing numeric correlations with low confidence values.
    for c in ["crossdonor_correlation_mean", "crossdonor_correlation_min", "crossguide_correlation"]:
        card_df[c] = card_df[c].fillna(np.nan)

    # target-condition score enrichment
    total_by_target = card_df.groupby("target_contrast")["n_total_de_genes"].transform("sum")
    card_df["condition_specificity_score"] = np.where(
        total_by_target > 0,
        card_df["n_total_de_genes"] / total_by_target,
        0.0,
    )
    card_df["replicate_pass_flag"] = ((card_df["n_cells_target"] >= min_cells) &
                                     (card_df["n_total_de_genes"] >= min_de_genes) &
                                     card_df["ontarget_significant"] &
                                     (~card_df["offtarget_flag"]) &
                                     (card_df["crossdonor_correlation_mean"].fillna(-1) >= 0.2) &
                                     (card_df["crossguide_correlation"].fillna(-1) >= 0.2)
                                    ).astype(bool)

    card_df["batch_sensitivity_flag"] = "unknown"
    card_df["pathway_axis"] = card_df["target"].apply(_pathway_axis)
    card_df["clinical_axis"] = card_df["target"].apply(_clinical_axis)
    card_df["positive_control_similarity"] = card_df["target"].apply(
        lambda t: 1 if isinstance(t, str) and t in POSITIVE_CONTROLS else 0
    )
    card_df["nearest_success_drug"] = card_df["target"].apply(
        lambda t: _first_match_in_benchmark(t, benchmark) if isinstance(benchmark, pd.DataFrame) else ""
    )
    card_df["nearest_failure_or_warning"] = ""

    card_df["median_logFC"] = card_df["ontarget_effect_size"]
    card_df["max_abs_logFC"] = card_df["ontarget_effect_size"].abs()
    # If any missing/ambiguous, keep explicit NaN.
    card_df["statistical_evidence_grade"] = card_df.apply(
        lambda r: _make_score(r, min_cells=min_cells, min_de_genes=min_de_genes), axis=1
    )

    def _cap_reason(row: pd.Series) -> str:
        if row["n_cells_target"] < min_cells:
            reasons = ["low_cells"]
        else:
            reasons = []
        if row["n_total_de_genes"] < min_de_genes:
            reasons.append("low_signal")
        if row.get("single_donor_dominance_hint", False):
            reasons.append("single_donor_dominance")
        return ";".join(reasons) if reasons else _score_cap_reasons(row, min_cells=min_cells, min_de_genes=min_de_genes)

    card_df["score_cap_reason"] = card_df.apply(_cap_reason, axis=1)

    out_cols = [
        "target",
        "culture_condition",
        "target_contrast",
        "n_cells_target",
        "n_guides",
        "n_total_de_genes",
        "n_up_genes",
        "n_down_genes",
        "ontarget_effect_size",
        "ontarget_significant",
        "offtarget_flag",
        "median_logFC",
        "max_abs_logFC",
        "fdr_min",
        "crossdonor_correlation_mean",
        "crossdonor_correlation_min",
        "crossguide_correlation",
        "replicate_pass_flag",
        "batch_sensitivity_flag",
        "guide_signif_ratio",
        "guide_fdr_min",
        "guide_t_abs_median",
        "positive_control_similarity",
        "pathway_axis",
        "condition_specificity_score",
        "clinical_axis",
        "nearest_success_drug",
        "nearest_failure_or_warning",
        "statistical_evidence_grade",
        "score_cap_reason",
    ]

    card_out = card_df[out_cols].copy()
    # Keep deterministic sorting: clinical relevance first, then evidence.
    card_out = card_out.sort_values(
        by=["statistical_evidence_grade", "n_total_de_genes", "n_cells_target", "condition_specificity_score"],
        ascending=[False, False, False, False],
    )
    # Add n_donors fallback: currently unavailable from DE_summary alone.
    if "n_donors" not in card_out.columns:
        card_out["n_donors"] = np.nan

    # Column renaming to match specification names.
    card_out = card_out.rename(columns={"culture_condition": "condition", "target_contrast": "target_id"})
    # Keep a stable alias for score_cap_reason string.
    card_out = card_out.reset_index(drop=True)
    card_out.to_csv(out_path, index=False)


def build_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build CSV-first target-condition cards.")
    parser.add_argument("--de-stats", type=Path, default=Path("metadata/suppl_tables/DE_stats.suppl_table.csv"))
    parser.add_argument("--guide-kd", type=Path, default=Path("metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv"))
    parser.add_argument("--library-metadata", type=Path, default=Path("metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv"))
    parser.add_argument("--clinical-benchmark", type=Path, default=BENCHMARK_CSV_DEFAULT)
    parser.add_argument("--output", type=Path, default=Path("sources/topic14_target_cards.csv"))
    parser.add_argument("--skip-benchmark", action="store_true")
    parser.add_argument("--min-cells", type=int, default=200)
    parser.add_argument("--min-de", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    args = build_parser()
    de = _normalize_cols(pd.read_csv(args.de_stats))
    guide = _normalize_cols(pd.read_csv(args.guide_kd))
    lib = _normalize_cols(pd.read_csv(args.library_metadata)) if args.library_metadata.exists() else None

    benchmark: Optional[pd.DataFrame]
    if args.skip_benchmark:
        benchmark = None
    else:
        benchmark = _load_benchmark(args.clinical_benchmark)
        if benchmark is None:
            print(f"Clinical benchmark not found, continue without mapping: {args.clinical_benchmark}")

    _build_cards(de, guide, lib, args.output, benchmark, min_cells=args.min_cells, min_de_genes=args.min_de)
    print(f"Wrote target cards -> {args.output.resolve()}")


if __name__ == "__main__":
    main()
