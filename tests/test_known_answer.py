"""Known-answer regression tests against the REAL GWT reference dataset.

These pin down numbers that were independently verified during development
(against sources/topic09_eda_report.md's EDA cascade and the calibration
control panel) -- if any of these move, the change is either a real
calibration shift worth reviewing, or a regression. Session-scoped fixtures
(conftest.py: real_cards/real_readiness) build the pipeline once (~15-20s
total) and every test below reuses that single build.
"""
from __future__ import annotations

import pytest


def test_qc_funnel_matches_eda_report_cascade(real_cards):
    from calibration import qc_funnel

    funnel = qc_funnel(real_cards)
    stages = {s["stage"]: s["n"] for s in funnel["stages"]}
    assert stages["all_rows"] == 33983
    # Independently confirmed against sources/topic09_eda_report.md's own count.
    assert stages["n_total_de_genes>=50"] == 4182
    assert funnel["high_confidence_rows"] == 1102


def test_control_panel_positive_controls_recovered(real_cards, real_readiness):
    from calibration import control_panel_calibration

    result = control_panel_calibration(real_cards, readiness=real_readiness)
    pos = result["positive_controls"]
    assert pos["n_found_in_cards"] == 20
    # ~20% of the 21-gene positive-control panel reaches grade>=3 -- known,
    # honestly-reported weak spot (most TCR-proximal genes are essential/broad,
    # so they get capped elsewhere), not a bug. Bounded, not pinned exactly,
    # so unrelated floating-point noise doesn't break this test.
    assert 0.10 <= pos["fraction_reaching_grade_3_or_4"] <= 0.35
    # The readiness layer's job is to not throw away known-good genes outright.
    assert pos["fraction_not_deprioritized"] >= 0.85


def test_control_panel_negative_controls_correctly_rejected(real_cards, real_readiness):
    from calibration import control_panel_calibration

    result = control_panel_calibration(real_cards, readiness=real_readiness)
    neg = result["negative_controls"]
    assert neg["n_rows"] > 4000
    # kd_status == "not_measurable" rows must overwhelmingly land at grade 1
    # and must never be graded 3/4 or advanced/validated -- this is the whole
    # point of the kd_status causal gate.
    assert neg["fraction_grade_1"] >= 0.95
    assert neg["fraction_reaching_grade_3_or_4"] == 0.0
    assert neg["fraction_advance_or_validate"] == 0.0


def test_no_kd_weak_row_ever_reaches_advance(real_readiness, real_cards):
    """Regression guard for a bug caught and fixed during development: kd_status
    == 'weak' must cap at 'validate', never 'advance'. Joins on (target,
    condition), not target alone -- an earlier ad hoc check that joined on
    target alone produced false positives from a different condition of the
    same gene.
    """
    weak = real_cards[real_cards["kd_status"] == "weak"][["target", "condition"]]
    assert len(weak) > 0
    joined = weak.merge(real_readiness, on=["target", "condition"], how="left")
    assert (joined["readiness_call"] != "advance").all()


def test_no_kd_not_measurable_row_ever_reaches_advance_or_validate(real_readiness, real_cards):
    not_measurable = real_cards[real_cards["kd_status"] == "not_measurable"][["target", "condition"]]
    assert len(not_measurable) > 0
    joined = not_measurable.merge(real_readiness, on=["target", "condition"], how="left")
    assert joined["readiness_call"].isin(["deprioritize", "watchlist"]).all()
