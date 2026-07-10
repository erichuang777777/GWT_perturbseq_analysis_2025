"""Known-answer tests for translation_capped_by (Wave 1b, docs/ux_trust_fix_plan.md).

Distinguishes WHY translation_score is below 5 -- a missing (NaN)
crossdonor_correlation_mean caps it exactly like a measured-but-low value,
and the bare integer alone can't tell the two apart. Also locks that the new
column cannot move readiness_call/overall_readiness_stage (the
descriptive/decision wall).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "3_DE_analysis"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.readiness import compute_readiness  # noqa: E402

BASE_ROW = {
    "target": "TESTGENE",
    "condition": "Stim_8hr",
    "statistical_evidence_grade": 3,
    "pathway_axis": "unassigned",
    "replicate_pass_flag": True,
    "crossdonor_correlation_mean": 0.5,
    "clinical_axis": "unassigned",
    "positive_control_similarity": False,
    "offtarget_flag": False,
    "batch_sensitivity_flag": "not_sensitive",
    "score_cap_reason": "none",
    "kd_status": "confirmed",
    "n_total_de_genes": 100,
    "target_id": "",
}


def _cards(overrides: dict) -> pd.DataFrame:
    row = {**BASE_ROW, **overrides}
    return pd.DataFrame([row])


def test_not_capped_when_translation_is_5():
    result = compute_readiness(_cards({"crossdonor_correlation_mean": 0.5, "replicate_pass_flag": True}))
    assert result.iloc[0]["translation_score"] == 5
    assert result.iloc[0]["translation_capped_by"] == "not_capped"


def test_missing_crossdonor_data_not_measured_low():
    """A NaN crossdonor_correlation_mean (unmeasured) must be labeled distinctly
    from a real low value -- both cap translation_score at 3 identically."""
    result = compute_readiness(_cards({"crossdonor_correlation_mean": np.nan, "replicate_pass_flag": True}))
    assert result.iloc[0]["translation_score"] == 3
    assert result.iloc[0]["translation_capped_by"] == "missing_crossdonor_data"


def test_measured_low_crossdonor_is_distinguished_from_missing():
    result = compute_readiness(_cards({"crossdonor_correlation_mean": 0.1, "replicate_pass_flag": True}))
    assert result.iloc[0]["translation_score"] == 3
    assert result.iloc[0]["translation_capped_by"] == "measured_low_crossdonor"


def test_replicate_not_passed():
    result = compute_readiness(_cards({"replicate_pass_flag": False, "crossdonor_correlation_mean": np.nan}))
    assert result.iloc[0]["translation_score"] == 0
    assert result.iloc[0]["translation_capped_by"] == "replicate_not_passed"


def test_translation_capped_by_is_inert_through_compute_readiness():
    """Descriptive/decision wall: adding translation_capped_by must not change
    readiness_call/overall_readiness_stage relative to a run without reading
    it -- it is derived FROM translation_score, never fed back into _stage()."""
    with_missing = compute_readiness(_cards({"crossdonor_correlation_mean": np.nan, "replicate_pass_flag": True}))
    with_measured_low = compute_readiness(_cards({"crossdonor_correlation_mean": 0.1, "replicate_pass_flag": True}))
    # Both are capped at translation_score=3 by DIFFERENT capped_by reasons,
    # but must produce the IDENTICAL readiness_call/stage -- the descriptive
    # label changes, the decision does not.
    assert with_missing.iloc[0]["translation_score"] == with_measured_low.iloc[0]["translation_score"]
    assert with_missing.iloc[0]["readiness_call"] == with_measured_low.iloc[0]["readiness_call"]
    assert with_missing.iloc[0]["overall_readiness_stage"] == with_measured_low.iloc[0]["overall_readiness_stage"]
