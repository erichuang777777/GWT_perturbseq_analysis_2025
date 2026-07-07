"""Golden-file test: a small, fixed DE/guide-KD input must build to an exact,
known-by-hand card output. Any change to build_cards_frame's scoring logic
that shifts one of these values is a deliberate change, not an accident --
this test forces you to look at it.
"""
from __future__ import annotations

import pandas as pd
import pytest


def _row(cards: pd.DataFrame, target: str, condition: str) -> pd.Series:
    match = cards[(cards["target"] == target) & (cards["condition"] == condition)]
    assert len(match) == 1, f"expected exactly one row for {target}/{condition}, got {len(match)}"
    return match.iloc[0]


def test_zap70_positive_control_reaches_grade_4(golden_cards):
    for condition in ("Rest", "Stim8hr"):
        row = _row(golden_cards, "ZAP70", condition)
        assert row["statistical_evidence_grade"] == 4
        assert row["kd_status"] == "confirmed"
        assert row["score_cap_reason"] == "none"
        assert row["n_guides"] == 2
        assert bool(row["replicate_pass_flag"]) is True


def test_med12_broad_effect_gene_still_grades_high(golden_cards):
    # build_target_cards.py itself does not know about broad_effect -- that red
    # flag lives in readiness_engine.py. At the statistical-grade layer, MED12
    # looks identical to a clean hit; this test pins that fact down so the two
    # layers' responsibilities don't get blurred later.
    row = _row(golden_cards, "MED12", "Rest")
    assert row["statistical_evidence_grade"] == 4
    assert row["kd_status"] == "confirmed"


def test_lowexpr_gene_is_kd_not_measurable(golden_cards):
    row = _row(golden_cards, "LOWEXPR1", "Rest")
    assert row["kd_status"] == "not_measurable"
    assert row["target_baseline_expression"] == pytest.approx(0.0005)
    assert "kd_not_measurable" in row["score_cap_reason"]
    assert row["statistical_evidence_grade"] == 1


def test_noeffect_gene_is_kd_weak_not_not_measurable(golden_cards):
    # Expressed well above the 0.001 floor, but guide_signif_ratio/fdr don't
    # clear the "confirmed" bar -- this must land as "weak", not "not_measurable".
    row = _row(golden_cards, "NOEFFECT1", "Rest")
    assert row["kd_status"] == "weak"
    assert row["target_baseline_expression"] == pytest.approx(0.5)
    assert "kd_weak" in row["score_cap_reason"]
    assert row["statistical_evidence_grade"] == 1


def test_kd_not_measurable_floor_is_exactly_documented_value(golden_cards):
    from build_target_cards import KD_NOT_MEASURABLE_EXPRESSION_FLOOR

    assert KD_NOT_MEASURABLE_EXPRESSION_FLOOR == 0.001
