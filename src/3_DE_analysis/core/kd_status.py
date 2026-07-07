"""On-target knockdown status classification (split out of ``build_target_cards.py``,
architecture refactor Phase 2 -- see ``docs/architecture_refactor_plan.md`` §3).

Pure, deterministic, no I/O beyond the row it is given; reads thresholds from
``config.thresholds``/``config.versions`` (the single source of truth, Phase 0).
"""

from __future__ import annotations

import pandas as pd

from config import thresholds, versions

# Re-exported from config.thresholds/config.versions (the single source of
# truth, see docs/architecture_refactor_plan.md §5 Phase 0) so existing
# `from build_target_cards import KD_NOT_MEASURABLE_EXPRESSION_FLOOR` callers
# keep working unchanged.
KD_NOT_MEASURABLE_EXPRESSION_FLOOR = thresholds.KD_NOT_MEASURABLE_EXPRESSION_FLOOR
KD_THRESHOLD_VERSION = versions.KD_THRESHOLD_VERSION


def kd_status(row: pd.Series) -> str:
    """Four-state on-target knockdown status: confirmed / weak / not_measurable / not_assessed.

    CRISPRi's causal chain is target-suppressed -> downstream transcription
    changes; if the target itself was never knocked down, downstream DE is
    not causally interpretable.

    Two genuinely different "cannot confirm knockdown" cases are kept distinct,
    per the ``unknown != 0`` principle (docs/data_governance_checklist.md §3):

        not_measurable -- target baseline expression was MEASURED and sits at
                          or below the 0.001 NTC floor, so knockdown cannot be
                          assessed. A real, evidence-backed failure mode that
                          justifies a red flag downstream.
        not_assessed   -- no knockdown data exists at all (e.g. a guide-less
                          generic upload, where target_baseline_expression is
                          NaN because there was never an NTC/guide table to
                          measure it from). This is genuinely UNKNOWN, not a
                          measured failure, so it must NOT be penalized as if
                          the target failed knockdown -- doing so would both
                          fabricate an "NTC expression too low" claim about an
                          upload that never had NTC cells, and wrongly cap the
                          whole upload at watchlist.
    """
    baseline = row.get("target_baseline_expression")
    if pd.isna(baseline):
        return "not_assessed"
    if baseline <= KD_NOT_MEASURABLE_EXPRESSION_FLOOR:
        return "not_measurable"
    ratio = row.get("guide_signif_ratio")
    fdr = row.get("guide_fdr_min")
    if (
        pd.notna(ratio)
        and pd.notna(fdr)
        and ratio >= thresholds.GUIDE_SIGNIF_RATIO_MIN
        and fdr <= thresholds.GUIDE_FDR_MAX_CONFIRMED
    ):
        return "confirmed"
    return "weak"


# Backward-compatible alias: build_target_cards.py's private name for this
# function before the Phase 2 split.
_kd_status = kd_status
