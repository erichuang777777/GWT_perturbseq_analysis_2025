"""The ``target_cards.csv`` column contract (B4's ``CARD_SCHEMA_VERSION``, made real).

Previously ``CARD_SCHEMA_VERSION`` was only a version *string* stamped into
provenance -- nothing actually checked that a card DataFrame matched it. This
module makes the contract checkable: ``CARD_COLUMNS`` is the exact,
real column list ``build_target_cards.build_cards_frame`` produces (verified
against both the GWT-reference and generic/upload schema paths -- both
produce all 39 columns, filling NaN where a value is unavailable rather than
omitting the column), and ``validate_cards`` checks a DataFrame against it.

This is the seam that makes "safe swap" concrete: any function -- a different
scoring model, a reimplementation, a mock for testing -- that returns a
DataFrame satisfying ``validate_cards`` is a drop-in replacement for
``build_cards_frame`` from the point of view of every downstream consumer
(``calibration.py``, ``readiness_engine.py``, ``generate_target_report.py``,
the API routes, the dashboard), none of which need to change.

See ``docs/data_dictionary.md`` §2 for what each column means, and
``docs/architecture_refactor_plan.md`` §4.2 for the isolation rationale.
"""

from __future__ import annotations

from typing import List

import pandas as pd

# Exact column set produced by build_target_cards.build_cards_frame, in its
# native order. Verified identical for both schema="gwt" and schema="generic"
# builds (a generic/upload build fills unavailable fields with NaN rather
# than omitting the column).
CARD_COLUMNS: List[str] = [
    "target",
    "condition",
    "target_id",
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
    "condition_specificity_zscore",
    "effect_direction_flip_flag",
    "clinical_axis",
    "nearest_success_drug",
    "nearest_failure_or_warning",
    "target_baseline_expression",
    "kd_status",
    "kd_threshold_version",
    "statistical_evidence_grade",
    "score_cap_reason",
    "n_donors",
    "druggable_class",
    "tractability_modality",
    "safety_note",
]

# The minimal subset every downstream consumer actually keys off of --
# calibration's control-panel/QC-funnel gates, readiness_engine's domain
# scoring, and the dashboard's core views all fail without these specifically
# (the rest degrade gracefully via .get()/`if col in df.columns` guards
# already present in those modules). Useful for a lighter-weight check when a
# caller only needs to know "is this usable," not "is this the full contract."
CORE_REQUIRED_COLUMNS: List[str] = [
    "target",
    "condition",
    "statistical_evidence_grade",
    "kd_status",
    "score_cap_reason",
    "n_total_de_genes",
    "n_cells_target",
    "ontarget_significant",
    "offtarget_flag",
]

KD_STATUS_VALUES = {"confirmed", "weak", "not_measurable", "not_assessed"}


def validate_cards(df: pd.DataFrame, *, strict: bool = False) -> List[str]:
    """Check ``df`` against the card contract. Returns a list of problems (empty = valid).

    Never raises -- callers decide what to do with a non-empty result (log,
    reject, degrade). With ``strict=False`` (default), only checks
    ``CORE_REQUIRED_COLUMNS`` are present; with ``strict=True``, requires the
    full ``CARD_COLUMNS`` set.
    """
    problems: List[str] = []
    required = CARD_COLUMNS if strict else CORE_REQUIRED_COLUMNS
    missing = [c for c in required if c not in df.columns]
    if missing:
        problems.append(f"missing columns: {missing}")
    if "kd_status" in df.columns:
        bad_values = set(df["kd_status"].dropna().unique()) - KD_STATUS_VALUES
        if bad_values:
            problems.append(f"kd_status has values outside {sorted(KD_STATUS_VALUES)}: {sorted(bad_values)}")
    if "statistical_evidence_grade" in df.columns:
        grades = pd.to_numeric(df["statistical_evidence_grade"], errors="coerce").dropna()
        bad_grades = sorted(set(grades) - {1.0, 2.0, 3.0, 4.0})
        if bad_grades:
            problems.append(f"statistical_evidence_grade has values outside 1-4: {bad_grades}")
    return problems
