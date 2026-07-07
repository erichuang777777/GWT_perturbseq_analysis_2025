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

# Canonical target-evidence contract used by generic (uploaded) DE tables.
GENERIC_TARGET_FIELDS = ("target", "condition", "effect_size", "logfc", "p_value", "fdr", "n_cells", "n_guides")

# Local druggable-class gene lists (metadata/gene_lists/<name>.tsv) -> likely modality.
# Shared with readiness_engine.py so tractability inference stays in one place.
DRUGGABLE_CLASS_MODALITY: Dict[str, str] = {
    "kinases": "small molecule",
    "gpcr_union": "small molecule",
    "rhodop_gpcr": "small molecule",
    "ion_channels": "small molecule",
    "transporters": "small molecule",
    "nuclear_receptors": "small molecule",
    "enzymes": "small molecule",
    "catalytic_receptors": "small molecule / biologic",
    "cytokine_receptors": "antibody / biologic",
    "gpi_anchored": "antibody (surface)",
}

GENE_LISTS_DIR_DEFAULT = Path("metadata/gene_lists")
IMMUNE_EFFECTOR_CSV_DEFAULT = Path("metadata/immune_effector_genes.csv")


def load_druggable_overlays(gene_lists_dir: Path) -> Dict[str, set]:
    """Load druggable-class + genetics gene sets from ``metadata/gene_lists``."""
    gene_lists_dir = Path(gene_lists_dir)
    overlays: Dict[str, set] = {}
    for name in list(DRUGGABLE_CLASS_MODALITY) + ["gwascatalog", "clinvar_path_likelypath"]:
        genes = load_gene_set(gene_lists_dir / f"{name}.tsv")
        if genes:
            overlays[name] = genes
    return overlays


def load_immune_effector_map(path: Path) -> Dict[str, str]:
    """Load ``gene_name,Category`` immune-effector annotations into an upper-cased dict."""
    path = Path(path)
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    gene_col = cols.get("gene_name") or cols.get("gene")
    cat_col = cols.get("category")
    if not gene_col or not cat_col:
        return {}
    out: Dict[str, str] = {}
    for _, row in df.iterrows():
        gene = str(row[gene_col]).strip().upper()
        if gene:
            out[gene] = str(row[cat_col]).strip()
    return out


def _druggable_class_for(gene: str, overlays: Dict[str, set]) -> tuple:
    for name, modality in DRUGGABLE_CLASS_MODALITY.items():
        genes = overlays.get(name)
        if genes and gene in genes:
            return name, modality
    return "", ""


def annotate_local_overlays(
    card_df: pd.DataFrame,
    gene_lists_dir: Path = GENE_LISTS_DIR_DEFAULT,
    immune_effector_csv: Path = IMMUNE_EFFECTOR_CSV_DEFAULT,
) -> pd.DataFrame:
    """Add ``druggable_class``, ``tractability_modality``, and ``safety_note`` columns.

    Purely local, offline overlays (no external calls): druggable-gene-class lists,
    ClinVar pathogenic/likely-pathogenic membership, and immune-effector-gene
    category membership. A target absent from every local list gets empty strings,
    never a fabricated value.
    """
    overlays = load_druggable_overlays(gene_lists_dir)
    clinvar = overlays.get("clinvar_path_likelypath", set())
    immune_map = load_immune_effector_map(immune_effector_csv)

    genes = card_df["target"].astype(str).str.strip().str.upper()
    classes, modalities, notes = [], [], []
    for gene in genes:
        cls, modality = _druggable_class_for(gene, overlays)
        classes.append(cls)
        modalities.append(modality)
        note_parts = []
        if gene in clinvar:
            note_parts.append("clinvar_pathogenic_or_likely_pathogenic")
        if gene in immune_map:
            note_parts.append(f"immune_effector:{immune_map[gene]}")
        notes.append(";".join(note_parts))

    out = card_df.copy()
    out["druggable_class"] = classes
    out["tractability_modality"] = modalities
    out["safety_note"] = notes
    return out


def load_gene_set(path: Path) -> set:
    """Load a newline-delimited gene-symbol list (no header) into an upper-cased set."""
    if not Path(path).exists():
        return set()
    genes: set = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        token = line.strip().split("\t")[0].strip()
        if token and not token.lower().startswith("gene"):
            genes.add(token.upper())
    return genes


def confounded_conditions(sample_meta: Optional[pd.DataFrame]) -> set:
    """Return culture conditions confounded with a single 10x run (condition-run confound).

    A condition whose samples all fall in one run cannot be separated from batch, so
    condition-specific claims for it are batch-sensitive unless donor/guide-robust.
    """
    if sample_meta is None or sample_meta.empty:
        return set()
    cols = {c.lower(): c for c in sample_meta.columns}
    cond_col = cols.get("culture_condition")
    run_col = cols.get("10xrun_id") or cols.get("run_id")
    if not cond_col or not run_col:
        return set()
    runs_per_cond = sample_meta.groupby(cond_col)[run_col].nunique()
    return set(runs_per_cond[runs_per_cond <= 1].index.astype(str))


def adapt_generic_de(df: pd.DataFrame) -> pd.DataFrame:
    """Map a generic canonical DE table onto the builder's internal GWT column names.

    Missing robustness fields are left as NaN so grading degrades gracefully
    (a guide-less generic upload caps at grade 2).
    """
    g = _normalize_cols(df.copy())
    lower = {str(c).strip().lower(): c for c in g.columns}

    def col(name: str) -> Optional[str]:
        return lower.get(name)

    out = pd.DataFrame(index=g.index)
    target_col = col("target") or col("gene") or col("target_gene")
    out["target_contrast_gene_name"] = g[target_col].astype(str) if target_col else ""
    out["target_contrast"] = out["target_contrast_gene_name"]
    cond_col = col("condition") or col("culture_condition")
    out["culture_condition"] = g[cond_col].astype(str) if cond_col else "unspecified"

    eff_col = col("effect_size") or col("logfc") or col("log2fc")
    out["ontarget_effect_size"] = pd.to_numeric(g[eff_col], errors="coerce") if eff_col else np.nan

    fdr_col = col("fdr") or col("padj") or col("adj_p_value")
    p_col = col("p_value") or col("pvalue") or col("p_val")
    if fdr_col:
        fdr = pd.to_numeric(g[fdr_col], errors="coerce")
        out["ontarget_significant"] = fdr <= 0.05
    elif p_col:
        pval = pd.to_numeric(g[p_col], errors="coerce")
        out["ontarget_significant"] = pval <= 0.05
    else:
        out["ontarget_significant"] = False
    out["_generic_fdr_min"] = pd.to_numeric(g[fdr_col], errors="coerce") if fdr_col else np.nan

    ncell_col = col("n_cells") or col("n_cells_target")
    out["n_cells_target"] = pd.to_numeric(g[ncell_col], errors="coerce") if ncell_col else np.nan
    nguide_col = col("n_guides")
    out["_generic_n_guides"] = pd.to_numeric(g[nguide_col], errors="coerce") if nguide_col else np.nan

    ntot_col = col("n_total_de_genes")
    out["n_total_de_genes"] = pd.to_numeric(g[ntot_col], errors="coerce") if ntot_col else np.nan
    out["n_up_genes"] = np.nan
    out["n_down_genes"] = np.nan
    out["offtarget_flag"] = False
    out["crossdonor_correlation_mean"] = np.nan
    out["crossdonor_correlation_min"] = np.nan
    out["crossguide_correlation"] = np.nan
    return out


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
    cd = row["crossdonor_correlation_mean"]
    cg = row["crossguide_correlation"]
    # Missing (NaN) robustness is treated as weak, matching the EDA caveat that
    # rows lacking cross-donor/cross-guide support are not highest-confidence.
    if pd.isna(cd) or pd.isna(cg) or cd < 0.2 or cg < 0.2:
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
        reasons.append("single_guide")
    # De-duplicate while preserving first-seen order.
    reasons = list(dict.fromkeys(reasons))
    return ";".join(reasons) if reasons else "none"


def build_cards_frame(
    de_df: pd.DataFrame,
    guide_df: Optional[pd.DataFrame],
    lib_map: Optional[pd.DataFrame],
    benchmark: Optional[pd.DataFrame],
    min_cells: int = 200,
    min_de_genes: int = 50,
    schema: str = "gwt",
    sample_meta: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Assemble the target-condition card table and return it as a DataFrame.

    ``schema="generic"`` accepts an already-adapted uploaded DE table (see
    ``adapt_generic_de``) and tolerates a missing guide table, in which case
    guide-dependent grades (3/4) are unreachable and cards cap at grade 2.
    """
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

    has_guides = (
        guide_df is not None
        and not guide_df.empty
        and "signif_knockdown" in guide_df.columns
    )
    if has_guides:
        guide_summary = _build_guide_summary(guide_df)
        card_df = de.merge(
            guide_summary,
            left_on=["target_contrast", "culture_condition"],
            right_on=["target_id", "culture_condition"],
            how="left",
        )
    else:
        # Generic / guide-less path: synthesize guide fields (NaN-heavy) so grading
        # degrades gracefully instead of crashing on the missing merge.
        card_df = de.copy()
        card_df["target_id"] = card_df["target_contrast"]
        card_df["n_guides"] = card_df.get("_generic_n_guides", np.nan)
        card_df["guide_signif_ratio"] = np.nan
        card_df["guide_fdr_min"] = card_df.get("_generic_fdr_min", np.nan)
        card_df["guide_t_abs_median"] = np.nan

    card_df["n_guides"] = card_df["n_guides"].fillna(0).astype(int)
    card_df["guide_signif_ratio"] = card_df["guide_signif_ratio"].fillna(0.0)
    card_df["guide_fdr_min"] = card_df["guide_fdr_min"].astype(float)
    card_df["guide_t_abs_median"] = card_df["guide_t_abs_median"].astype(float)
    card_df["fdr_min"] = card_df["guide_fdr_min"]

    # Missing correlations stay NaN on purpose: every downstream comparison
    # (_make_score, replicate_pass_flag, _score_cap_reasons) already treats NaN
    # as failing/weak, so no sentinel substitution is needed.

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

    confounded = confounded_conditions(sample_meta)
    if confounded:
        cond = card_df["culture_condition"].astype(str)
        is_conf = cond.isin(confounded)
        robust = (card_df["crossdonor_correlation_mean"].fillna(-1) >= 0.3) | (
            card_df["crossguide_correlation"].fillna(-1) >= 0.3
        )
        card_df["batch_sensitivity_flag"] = np.select(
            [is_conf & ~robust, is_conf & robust],
            ["sensitive", "confounded_but_robust"],
            default="not_flagged",
        )
    else:
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
        # Always compute the full reason set (off-target, batch, replicability,
        # direction, guide flags) and union in the low-cell/low-signal/hint tokens.
        # A previous early-return here suppressed every other reason on any
        # low-cell or low-signal row, hiding off-target and batch-confound
        # signals on ~1,100 rows of the reference dataset.
        full = _score_cap_reasons(row, min_cells=min_cells, min_de_genes=min_de_genes)
        reasons = [] if full == "none" else full.split(";")
        if row.get("single_donor_dominance_hint", False):
            reasons.append("single_donor_dominance")
        reasons = list(dict.fromkeys(reasons))
        return ";".join(reasons) if reasons else "none"

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
    card_out = annotate_local_overlays(card_out)
    return card_out


def _build_cards(
    de_df: pd.DataFrame,
    guide_df: Optional[pd.DataFrame],
    lib_map: Optional[pd.DataFrame],
    out_path: Path,
    benchmark: Optional[pd.DataFrame],
    min_cells: int = 200,
    min_de_genes: int = 50,
    schema: str = "gwt",
    sample_meta: Optional[pd.DataFrame] = None,
) -> None:
    """IO wrapper: assemble cards and write them to ``out_path``."""
    frame = build_cards_frame(
        de_df,
        guide_df,
        lib_map,
        benchmark,
        min_cells=min_cells,
        min_de_genes=min_de_genes,
        schema=schema,
        sample_meta=sample_meta,
    )
    frame.to_csv(out_path, index=False)


def build_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build CSV-first target-condition cards.")
    parser.add_argument("--de-stats", type=Path, default=Path("metadata/suppl_tables/DE_stats.suppl_table.csv"))
    parser.add_argument("--guide-kd", type=Path, default=Path("metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv"))
    parser.add_argument("--library-metadata", type=Path, default=Path("metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv"))
    parser.add_argument("--clinical-benchmark", type=Path, default=BENCHMARK_CSV_DEFAULT)
    parser.add_argument("--sample-metadata", type=Path, default=Path("metadata/suppl_tables/sample_metadata.suppl_table.csv"))
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
    sample_meta = pd.read_csv(args.sample_metadata) if args.sample_metadata and Path(args.sample_metadata).exists() else None

    benchmark: Optional[pd.DataFrame]
    if args.skip_benchmark:
        benchmark = None
    else:
        benchmark = _load_benchmark(args.clinical_benchmark)
        if benchmark is None:
            print(f"Clinical benchmark not found, continue without mapping: {args.clinical_benchmark}")

    _build_cards(de, guide, lib, args.output, benchmark, min_cells=args.min_cells, min_de_genes=args.min_de, sample_meta=sample_meta)
    print(f"Wrote target cards -> {args.output.resolve()}")


if __name__ == "__main__":
    main()
