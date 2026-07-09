"""Tests for stimulation_switch_explorer.py (exploration follow-up C).

The synthetic fixture is the HARD lock (deterministic classification of a
hand-built frame). The real-data assertion is a SOFT sanity range -- the "true
sign flip" count is a re-derivable classification (~28 under this module's
|logFC|>=1 rule; the exploration reported ~27), not a stored golden number, so
the test bounds it rather than pinning an exact value.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from stimulation_switch_explorer import (
    REQUIRED_COLUMNS,
    SIGN_FLIP_MIN_ABS_LOGFC,
    list_switches,
    switch_report,
)

REPO = Path(__file__).resolve().parent.parent
REAL_CARDS = REPO / "sources" / "target_tool_cache" / "a6bba17b-f194-4a50-8cf8-96e03eededd6" / "target_cards.csv"


def _synthetic_cards() -> pd.DataFrame:
    """Hand-built cards exercising each classification branch."""
    rows = []
    # TRUE sign flip: strong negative at Rest, strong positive at Stim48hr
    rows += [
        {"target": "IKZF1", "condition": "Rest", "median_logFC": -9.9, "effect_direction_flip_flag": True},
        {"target": "IKZF1", "condition": "Stim8hr", "median_logFC": -3.8, "effect_direction_flip_flag": True},
        {"target": "IKZF1", "condition": "Stim48hr", "median_logFC": 1.25, "effect_direction_flip_flag": True},
    ]
    # ON/OFF switch: flagged, strong only at Stim8hr, ~0 elsewhere (no sign reversal)
    rows += [
        {"target": "CD3E", "condition": "Rest", "median_logFC": 0.01, "effect_direction_flip_flag": True},
        {"target": "CD3E", "condition": "Stim8hr", "median_logFC": 8.0, "effect_direction_flip_flag": True},
        {"target": "CD3E", "condition": "Stim48hr", "median_logFC": 2.0, "effect_direction_flip_flag": True},
    ]
    # NOT a switch: stable positive across conditions, not flagged
    rows += [
        {"target": "TADA2B", "condition": "Rest", "median_logFC": 5.0, "effect_direction_flip_flag": False},
        {"target": "TADA2B", "condition": "Stim8hr", "median_logFC": 5.2, "effect_direction_flip_flag": False},
        {"target": "TADA2B", "condition": "Stim48hr", "median_logFC": 4.8, "effect_direction_flip_flag": False},
    ]
    # incomplete (Stim only, no Rest) -> unknown, must be excluded (not 0)
    rows += [
        {"target": "ORPHAN", "condition": "Stim8hr", "median_logFC": 3.0, "effect_direction_flip_flag": True},
    ]
    return pd.DataFrame(rows)


def test_classification_is_correct_and_deterministic():
    sw = list_switches(_synthetic_cards())
    by_target = sw.set_index("target")["switch_type"].to_dict()
    assert by_target["IKZF1"] == "true_sign_flip"
    assert by_target["CD3E"] == "on_off_switch"
    assert "TADA2B" not in by_target  # not flagged, no reversal
    assert "ORPHAN" not in by_target  # incomplete -> unknown, excluded (not fabricated)
    # true sign flips rank ahead of on/off switches
    assert sw.iloc[0]["target"] == "IKZF1"
    # per-condition signed effects are surfaced
    ikzf1 = sw[sw["target"] == "IKZF1"].iloc[0]
    assert ikzf1["logFC_Rest"] == pytest.approx(-9.9)
    assert ikzf1["logFC_Stim48hr"] == pytest.approx(1.25)
    assert ikzf1["switch_magnitude"] == pytest.approx(9.9 + 1.25)


def test_honest_fallback_on_missing_columns():
    bad = pd.DataFrame({"target": ["X"], "condition": ["Rest"]})
    rep = switch_report(bad)
    assert rep["available"] is False
    assert rep["reason"]
    assert rep["switches"] == []


def test_report_shape_and_provenance():
    rep = switch_report(_synthetic_cards(), top_n=1)
    assert rep["available"] is True
    assert rep["n_true_sign_flip"] == 1
    assert rep["n_on_off_switch"] == 1
    assert rep["sign_flip_threshold_abs_logfc"] == SIGN_FLIP_MIN_ABS_LOGFC
    assert rep["returned"] == 1
    assert rep["concept_set_version"]


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_real_data_switch_counts_in_sanity_range():
    cards = pd.read_csv(REAL_CARDS, low_memory=False)
    rep = switch_report(cards)
    assert rep["available"] is True
    # 247 flagged unique targets total (confirmed column fact); every classified
    # switch is one of them, so the union is bounded by 247.
    assert rep["n_switches"] <= 247
    # true sign flips: a re-derivable ~27-28; bound it as a soft sanity range.
    assert 15 <= rep["n_true_sign_flip"] <= 45
    # known immune switches surface
    targets = {s["target"].upper() for s in rep["switches"]}
    assert "IKZF1" in targets
