"""Calibration harness: does the target-card ranking recover known biology?

A prioritization tool is only credible if it recovers known biology. This
module answers, from a built ``target_cards.csv``, whether the ranking:

1. Surfaces TCR/proximal-activation positive controls in the top deciles.
2. Enriches known immune drug axes (``clinical_axis``) among top-graded cards.
3. Stays stable when off-target / low-cell / low-robustness rows are dropped.

Deterministic, offline, no network calls -- reruns identically on the same
CSV so it can be checked into a report and diffed over time.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from build_target_cards import POSITIVE_CONTROLS

# TCR/proximal-activation genes used as the primary recovery benchmark
# (sources/topic11_breakthrough_directions_toolkit_opportunities.md, "Validation metrics").
TCR_PROXIMAL_GENES = {"CD3E", "LAT", "PLCG1", "ZAP70", "LCP2", "VAV1", "CD247", "ITK"}

# Positive-control panel with well-established CD4 phenotypes, expected to land
# in high grades/advance calls. Extends the existing POSITIVE_CONTROLS set
# (build_target_cards.py) with the 3 genes it didn't already cover.
CONTROL_PANEL_POSITIVE_GENES = POSITIVE_CONTROLS | {"STAT5A", "STAT5B", "TNFRSF9"}

# Known immune drug axes that a credible ranking should enrich for
# (sources/topic05_successful_drug_benchmarks.csv axis vocabulary).
KNOWN_DRUG_AXES = {
    "TCR/CD3 tolerance",
    "Costimulation blockade",
    "IL-2 / IL-2R",
    "JAK/STAT cytokine signaling",
    "Calcineurin/NFAT",
    "S1P trafficking",
}


def _as_bool(series: pd.Series) -> pd.Series:
    """Robust string/int/bool -> bool, independent of pandas dtype inference.

    A bare ``series.astype(bool)`` coerces the *strings* ``"True"``/``"False"``
    (which appear when a bool column is object-dtype, e.g. mixed with a NaN) both
    to ``True``, silently inverting the strict filter. This normalizes explicitly.
    """
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "y", "t"})


def _decile(rank_pct: float) -> int:
    """1 = top decile (best), 10 = bottom decile."""
    return max(1, min(10, int(rank_pct * 10) + 1))


def positive_control_recovery(cards: pd.DataFrame, gene_set: set, rank_col: str = "n_total_de_genes") -> Dict[str, Any]:
    """Per-condition decile rank of a benchmark gene set under a ranking column."""
    results: Dict[str, Any] = {"rank_column": rank_col, "gene_set_size": len(gene_set), "by_condition": {}}
    top_decile_hits = 0
    total_hits = 0
    for condition, group in cards.groupby("condition"):
        ranked = group.sort_values(rank_col, ascending=False).reset_index(drop=True)
        n = len(ranked)
        if n == 0:
            continue
        hits = []
        for gene in sorted(gene_set):
            rows = ranked.index[ranked["target"] == gene].tolist()
            if not rows:
                continue
            pct = rows[0] / max(n - 1, 1)
            decile = _decile(pct)
            hits.append({"target": gene, "rank": int(rows[0]) + 1, "n": n, "decile": decile})
            total_hits += 1
            if decile <= 2:
                top_decile_hits += 1
        results["by_condition"][condition] = hits
    results["fraction_in_top_2_deciles"] = round(top_decile_hits / total_hits, 3) if total_hits else None
    results["n_found"] = total_hits
    return results


def drug_axis_enrichment(cards: pd.DataFrame, min_grade: int = 3) -> Dict[str, Any]:
    """Compare clinical_axis assignment rate in high-grade rows vs the overall rate."""
    if "clinical_axis" not in cards.columns or "statistical_evidence_grade" not in cards.columns:
        return {"available": False}
    axis = cards["clinical_axis"].fillna("unassigned")
    assigned = axis != "unassigned"
    overall_rate = float(assigned.mean())
    high_grade = cards["statistical_evidence_grade"] >= min_grade
    high_grade_rate = float(assigned[high_grade].mean()) if high_grade.any() else None
    axes_present = set(cards.loc[high_grade, "clinical_axis"].dropna().unique().tolist()) if high_grade.any() else set()
    return {
        "available": True,
        "min_grade": min_grade,
        "overall_assignment_rate": round(overall_rate, 4),
        "high_grade_assignment_rate": round(high_grade_rate, 4) if high_grade_rate is not None else None,
        "enrichment_ratio": round(high_grade_rate / overall_rate, 3) if high_grade_rate and overall_rate else None,
        "axes_present": sorted(axes_present),
        "known_axes_recovered": sorted(axes_present & KNOWN_DRUG_AXES),
        "known_axes_missing": sorted(KNOWN_DRUG_AXES - axes_present),
    }


def rank_stability(cards: pd.DataFrame, top_n: int = 50, rank_col: str = "n_total_de_genes") -> Dict[str, Any]:
    """Rank correlation and top-N churn after dropping off-target/low-cell/low-robustness rows."""
    baseline = cards.sort_values(rank_col, ascending=False).reset_index(drop=True)
    baseline_top = set(baseline.head(top_n)["target"])

    strict = cards.copy()
    if "offtarget_flag" in strict.columns:
        strict = strict[~_as_bool(strict["offtarget_flag"])]
    if "n_cells_target" in strict.columns:
        strict = strict[strict["n_cells_target"].fillna(0) >= 200]
    if "crossdonor_correlation_mean" in strict.columns:
        strict = strict[strict["crossdonor_correlation_mean"].fillna(-1) >= 0.2]
    if "crossguide_correlation" in strict.columns:
        strict = strict[strict["crossguide_correlation"].fillna(-1) >= 0.2]
    strict = strict.sort_values(rank_col, ascending=False).reset_index(drop=True)
    strict_top = set(strict.head(top_n)["target"])

    common = set(baseline["target"]) & set(strict["target"])
    spearman = None
    if len(common) >= 3:
        b = baseline[baseline["target"].isin(common)].drop_duplicates("target").set_index("target")[rank_col]
        s = strict[strict["target"].isin(common)].drop_duplicates("target").set_index("target")[rank_col]
        joined = pd.DataFrame({"baseline": b, "strict": s}).dropna()
        if len(joined) >= 3:
            spearman = round(float(joined["baseline"].corr(joined["strict"], method="spearman")), 3)

    overlap = baseline_top & strict_top
    return {
        "rank_column": rank_col,
        "top_n": top_n,
        "baseline_rows": int(len(baseline)),
        "strict_filtered_rows": int(len(strict)),
        "top_n_overlap": len(overlap),
        "top_n_churn_fraction": round(1 - len(overlap) / top_n, 3) if top_n else None,
        "spearman_rank_correlation": spearman,
    }


def qc_funnel(cards: pd.DataFrame, min_de_genes: int = 50, min_cells: int = 200) -> Dict[str, Any]:
    """Row counts through the EDA's strict actionable filter, stage by stage.

    Mirrors sources/topic09_eda_report.md's "Minimal actionable filter" cascade
    (34k raw rows -> ~4.2k high-DE -> ~1.2k high-confidence on the full GWT
    reference set). Reused as-is on any dataset this tool builds cards for.
    """
    stages: List[Dict[str, Any]] = []
    current = cards
    stages.append({"stage": "all_rows", "n": int(len(current))})

    if "n_total_de_genes" in current.columns:
        current = current[pd.to_numeric(current["n_total_de_genes"], errors="coerce").fillna(0) >= min_de_genes]
        stages.append({"stage": f"n_total_de_genes>={min_de_genes}", "n": int(len(current))})

    mask = pd.Series(True, index=current.index)
    if "ontarget_significant" in current.columns:
        mask &= _as_bool(current["ontarget_significant"])
    if "offtarget_flag" in current.columns:
        mask &= ~_as_bool(current["offtarget_flag"])
    if "n_cells_target" in current.columns:
        mask &= pd.to_numeric(current["n_cells_target"], errors="coerce").fillna(0) >= min_cells
    current = current[mask]
    stages.append({"stage": "on_target_significant & not off_target & n_cells>=200", "n": int(len(current))})

    if "crossdonor_correlation_mean" in current.columns:
        current = current[pd.to_numeric(current["crossdonor_correlation_mean"], errors="coerce").fillna(-1) >= 0.2]
        stages.append({"stage": "crossdonor_correlation_mean>=0.2", "n": int(len(current))})

    if "crossguide_correlation" in current.columns:
        current = current[pd.to_numeric(current["crossguide_correlation"], errors="coerce").fillna(-1) >= 0.2]
        stages.append({"stage": "crossguide_correlation>=0.2", "n": int(len(current))})

    return {"stages": stages, "high_confidence_rows": int(len(current))}


def control_panel_calibration(cards: pd.DataFrame, readiness: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Positive- AND negative-control calibration check.

    Positive controls: genes with well-established CD4 phenotypes
    (CONTROL_PANEL_POSITIVE_GENES) are expected to land in high statistical
    grades (and, when a readiness frame is supplied, non-deprioritize calls).
    Negative controls: rows with kd_status == "not_measurable" (baseline
    expression too low in NTC cells to ever assess knockdown -- the real,
    already-computed operational equivalent of "non-expressed gene" controls)
    are expected to land in low grades / deprioritize, since the CRISPRi
    causal chain cannot even be evaluated for them.

    Both directions use the SAME thresholds the rest of the tool uses --
    this checks that one boundary works for both "let the real signal
    through" and "keep the true negatives out," rather than calibrating
    against positive examples alone.
    """
    result: Dict[str, Any] = {}

    if "target" not in cards.columns or "statistical_evidence_grade" not in cards.columns:
        return {"available": False}

    positive_rows = cards[cards["target"].isin(CONTROL_PANEL_POSITIVE_GENES)]
    best_grade_by_gene = positive_rows.groupby("target")["statistical_evidence_grade"].max()
    result["positive_controls"] = {
        "panel_size": len(CONTROL_PANEL_POSITIVE_GENES),
        "n_found_in_cards": int(best_grade_by_gene.shape[0]),
        "fraction_reaching_grade_3_or_4": round(float((best_grade_by_gene >= 3).mean()), 3) if len(best_grade_by_gene) else None,
        "genes_not_reaching_grade_3": sorted(best_grade_by_gene[best_grade_by_gene < 3].index.tolist()),
    }

    if "kd_status" in cards.columns:
        negative_rows = cards[cards["kd_status"] == "not_measurable"]
        result["negative_controls"] = {
            "definition": "kd_status == 'not_measurable' (target baseline expression <= 0.001 in NTC cells)",
            "n_rows": int(len(negative_rows)),
            "fraction_grade_1": round(float((negative_rows["statistical_evidence_grade"] <= 1).mean()), 4) if len(negative_rows) else None,
            "fraction_reaching_grade_3_or_4": round(float((negative_rows["statistical_evidence_grade"] >= 3).mean()), 4) if len(negative_rows) else None,
        }
    else:
        result["negative_controls"] = {"available": False, "reason": "no kd_status column in cards"}

    if readiness is not None and not readiness.empty and "target" in readiness.columns:
        pos_readiness = readiness[readiness["target"].isin(CONTROL_PANEL_POSITIVE_GENES)]
        result["positive_controls"]["fraction_not_deprioritized"] = (
            round(float((pos_readiness["readiness_call"] != "deprioritize").mean()), 3) if len(pos_readiness) else None
        )
        if "kd_status" in cards.columns:
            neg_targets = cards.loc[cards["kd_status"] == "not_measurable", "target"].unique()
            neg_readiness = readiness[readiness["target"].isin(neg_targets)]
            result["negative_controls"]["fraction_advance_or_validate"] = (
                round(float(neg_readiness["readiness_call"].isin(["advance", "validate"]).mean()), 4) if len(neg_readiness) else None
            )

    return result


def run_calibration(cards: pd.DataFrame, readiness: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Run the full calibration suite and return a JSON-serializable report.

    ``readiness``, if supplied (the output of readiness_engine.compute_readiness),
    additionally checks that positive controls are not deprioritized and that
    kd-not-measurable negative controls are not advanced/validated by the
    readiness layer, not just the raw statistical grade.
    """
    report: Dict[str, Any] = {
        "n_rows": int(len(cards)),
        "n_unique_targets": int(cards["target"].nunique()) if "target" in cards.columns else None,
        "positive_control_recovery": positive_control_recovery(cards, TCR_PROXIMAL_GENES),
        "known_drug_axis_enrichment": drug_axis_enrichment(cards),
        "rank_stability": rank_stability(cards),
        "qc_funnel": qc_funnel(cards),
        "control_panel_calibration": control_panel_calibration(cards, readiness=readiness),
    }
    pc = report["positive_control_recovery"]
    frac = pc.get("fraction_in_top_2_deciles")
    axis = report["known_drug_axis_enrichment"]
    stability = report["rank_stability"]
    narrative = []
    if frac is not None:
        narrative.append(
            f"{pc['n_found']} TCR/proximal positive-control gene-condition rows found; "
            f"{round(frac * 100)}% land in the top 2 deciles by {pc['rank_column']}."
        )
    if axis.get("available") and axis.get("enrichment_ratio"):
        narrative.append(
            f"clinical_axis assignment is {axis['enrichment_ratio']}x more common among "
            f"grade>={axis['min_grade']} rows than overall."
        )
    if stability.get("spearman_rank_correlation") is not None:
        narrative.append(
            f"Top-{stability['top_n']} overlap after strict robustness filtering: "
            f"{stability['top_n_overlap']}/{stability['top_n']} "
            f"(rank Spearman r={stability['spearman_rank_correlation']})."
        )
    panel = report["control_panel_calibration"]
    pos = panel.get("positive_controls", {})
    neg = panel.get("negative_controls", {})
    if pos.get("n_found_in_cards"):
        narrative.append(
            f"Control panel: {pos['n_found_in_cards']}/{pos['panel_size']} positive-control genes found; "
            f"{round((pos.get('fraction_reaching_grade_3_or_4') or 0) * 100)}% reach grade>=3."
        )
    if neg.get("n_rows"):
        narrative.append(
            f"{neg['n_rows']} kd-not-measurable negative-control rows: "
            f"{round((neg.get('fraction_grade_1') or 0) * 100)}% correctly land at grade 1, "
            f"{round((neg.get('fraction_reaching_grade_3_or_4') or 0) * 100)}% incorrectly reach grade>=3."
        )
    report["narrative"] = narrative
    return report


def write_report(report: Dict[str, Any], path: Path) -> None:
    Path(path).write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the calibration harness against a target-cards CSV.")
    parser.add_argument("cards", type=Path)
    parser.add_argument("--readiness", type=Path, default=None, help="optional readiness.csv from readiness_engine.py")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    cards_df = pd.read_csv(args.cards)
    readiness_df = pd.read_csv(args.readiness) if args.readiness and args.readiness.exists() else None
    result = run_calibration(cards_df, readiness=readiness_df)
    if args.output:
        write_report(result, args.output)
    for line in result["narrative"]:
        print(line)
    print(json.dumps({k: v for k, v in result.items() if k != "narrative"}, indent=2)[:2000])
