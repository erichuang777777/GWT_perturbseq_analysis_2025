"""Statistical-evidence-grade scoring (split out of ``build_target_cards.py``,
architecture refactor Phase 2 -- see ``docs/architecture_refactor_plan.md`` §3).

Pure, deterministic, no I/O beyond the row it is given; reads thresholds from
``config.thresholds`` (the single source of truth, Phase 0).
"""

from __future__ import annotations

import pandas as pd

from config import thresholds


def make_score(
    row: pd.Series,
    min_cells: int = thresholds.MIN_CELLS_DEFAULT,
    min_de_genes: int = thresholds.MIN_DE_GENES_DEFAULT,
) -> int:
    replicate = (
        (row["n_cells_target"] >= min_cells)
        and (row["n_total_de_genes"] >= min_de_genes)
        and bool(row["ontarget_significant"])
        and not bool(row["offtarget_flag"])
        and (row["crossdonor_correlation_mean"] >= thresholds.CROSSDONOR_MIN)
        and (row["crossguide_correlation"] >= thresholds.CROSSGUIDE_MIN)
    )
    if (
        replicate
        and row["guide_signif_ratio"] >= thresholds.GUIDE_SIGNIF_RATIO_MIN
        and row["guide_fdr_min"] <= thresholds.GUIDE_FDR_MAX_CONFIRMED
        and row["crossdonor_correlation_mean"] >= thresholds.CROSSDONOR_ROBUST
        and row["crossguide_correlation"] >= thresholds.CROSSGUIDE_ROBUST
        and row["n_guides"] >= thresholds.N_GUIDES_MIN_HIGH_GRADE
    ):
        return 4
    if replicate and row["n_guides"] >= thresholds.N_GUIDES_MIN_HIGH_GRADE and row["fdr_min"] <= thresholds.GUIDE_FDR_MAX_GRADE3:
        return 3
    if (row["n_cells_target"] >= min_cells) and row["ontarget_significant"]:
        return 2
    return 1


def score_cap_reasons(
    row: pd.Series,
    min_cells: int = thresholds.MIN_CELLS_DEFAULT,
    min_de_genes: int = thresholds.MIN_DE_GENES_DEFAULT,
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
    if pd.isna(cd) or pd.isna(cg) or cd < thresholds.CROSSDONOR_MIN or cg < thresholds.CROSSGUIDE_MIN:
        reasons.append("weak_replicability")
    if pd.isna(row["fdr_min"]) or row["fdr_min"] > thresholds.GUIDE_FDR_MAX_GRADE3:
        reasons.append("guide_limit")
    if pd.isna(row["condition_specificity_score"]):
        reasons.append("single_donor_dominance")
    if row["guide_signif_ratio"] < thresholds.GUIDE_SIGNIF_RATIO_MIN:
        reasons.append("guides_inconsistent")
    if row.get("batch_sensitivity_flag") == "sensitive":
        reasons.append("batch_sensitive")
    if row["n_guides"] < thresholds.N_GUIDES_MIN_HIGH_GRADE:
        reasons.append("single_guide")
    kd_status = row.get("kd_status")
    if kd_status == "not_measurable":
        reasons.append("kd_not_measurable")
    elif kd_status == "weak":
        reasons.append("kd_weak")
    # De-duplicate while preserving first-seen order.
    reasons = list(dict.fromkeys(reasons))
    return ";".join(reasons) if reasons else "none"


# Backward-compatible aliases: build_target_cards.py's private names for
# these functions before the Phase 2 split.
_make_score = make_score
_score_cap_reasons = score_cap_reasons
