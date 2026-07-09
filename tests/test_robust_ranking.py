"""Tests for robust_ranking.py -- robustness-first filter-then-rank (follow-up D).

Locks the things that matter:
  1. Synthetic hard-lock: the three-state tier is correct, and a row with a NaN
     robustness field (cross-donor) is ``unresolved`` -- NOT low, NOT high
     (honors ``unknown != 0``).
  2. Real-data sanity (skipif-gated): the high_confidence survivor count is in
     the calibration-reported ballpark (~1,102 under the lenient batch policy;
     the conservative default is smaller), and every returned target's row is
     actually high_confidence (filter-then-rank did filter first).
  3. INERT lock: adding a ``robustness_tier`` column and running the frame
     through ``compute_readiness`` yields byte-identical readiness output vs the
     plain frame -- proving the tier can never leak into any call.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from robust_ranking import (
    CROSS_MIN,
    MIN_CELLS,
    TIER_HIGH,
    TIER_LOW,
    TIER_UNRESOLVED,
    high_confidence_mask,
    robust_rank,
    robustness_tier,
)

REPO = Path(__file__).resolve().parent.parent
REAL_CARDS = REPO / "sources" / "target_tool_cache" / "a6bba17b-f194-4a50-8cf8-96e03eededd6" / "target_cards.csv"


def _synthetic_cards() -> pd.DataFrame:
    """Hand-built rows exercising every tier + NaN branch."""
    base = {
        "statistical_evidence_grade": 3,
        "n_total_de_genes": 1000,
    }
    rows = [
        # HIGH: every measurable check passes.
        {
            "target": "GOOD",
            "replicate_pass_flag": True,
            "batch_sensitivity_flag": "not_flagged",
            "offtarget_flag": False,
            "crossdonor_correlation_mean": 0.6,
            "crossguide_correlation": 0.5,
            "n_cells_target": 800,
            **base,
        },
        # LOW: measurable but replicate fails.
        {
            "target": "REPFAIL",
            "replicate_pass_flag": False,
            "batch_sensitivity_flag": "not_flagged",
            "offtarget_flag": False,
            "crossdonor_correlation_mean": 0.6,
            "crossguide_correlation": 0.5,
            "n_cells_target": 800,
            **base,
        },
        # LOW: measurable but off-target flagged.
        {
            "target": "OFFTGT",
            "replicate_pass_flag": True,
            "batch_sensitivity_flag": "not_flagged",
            "offtarget_flag": True,
            "crossdonor_correlation_mean": 0.6,
            "crossguide_correlation": 0.5,
            "n_cells_target": 800,
            **base,
        },
        # LOW: measurable but batch 'sensitive'.
        {
            "target": "BATCHSENS",
            "replicate_pass_flag": True,
            "batch_sensitivity_flag": "sensitive",
            "offtarget_flag": False,
            "crossdonor_correlation_mean": 0.6,
            "crossguide_correlation": 0.5,
            "n_cells_target": 800,
            **base,
        },
        # LOW: measurable but too few cells.
        {
            "target": "FEWCELLS",
            "replicate_pass_flag": True,
            "batch_sensitivity_flag": "not_flagged",
            "offtarget_flag": False,
            "crossdonor_correlation_mean": 0.6,
            "crossguide_correlation": 0.5,
            "n_cells_target": 10,
            **base,
        },
        # UNRESOLVED: cross-donor is NaN (unmeasured) -> not low, not high.
        {
            "target": "NANDONOR",
            "replicate_pass_flag": True,
            "batch_sensitivity_flag": "not_flagged",
            "offtarget_flag": False,
            "crossdonor_correlation_mean": np.nan,
            "crossguide_correlation": 0.5,
            "n_cells_target": 800,
            **base,
        },
        # CONFOUNDED_BUT_ROBUST: unresolved-free but batch not in default pass
        # set -> LOW by default, HIGH only under lenient.
        {
            "target": "CONFROBUST",
            "replicate_pass_flag": True,
            "batch_sensitivity_flag": "confounded_but_robust",
            "offtarget_flag": False,
            "crossdonor_correlation_mean": 0.6,
            "crossguide_correlation": 0.5,
            "n_cells_target": 800,
            **base,
        },
    ]
    return pd.DataFrame(rows)


def test_three_state_classification_hard_lock():
    df = _synthetic_cards()
    tier = robustness_tier(df)
    got = dict(zip(df["target"], tier))
    assert got["GOOD"] == TIER_HIGH
    assert got["REPFAIL"] == TIER_LOW
    assert got["OFFTGT"] == TIER_LOW
    assert got["BATCHSENS"] == TIER_LOW
    assert got["FEWCELLS"] == TIER_LOW
    assert got["CONFROBUST"] == TIER_LOW  # confounded_but_robust is not default-high
    # THE unknown!=0 lock: a NaN robustness field is unresolved, never low/high.
    assert got["NANDONOR"] == TIER_UNRESOLVED
    assert got["NANDONOR"] != TIER_LOW
    assert got["NANDONOR"] != TIER_HIGH


def test_lenient_promotes_confounded_but_robust():
    df = _synthetic_cards()
    default = dict(zip(df["target"], robustness_tier(df, lenient=False)))
    lenient = dict(zip(df["target"], robustness_tier(df, lenient=True)))
    assert default["CONFROBUST"] == TIER_LOW
    assert lenient["CONFROBUST"] == TIER_HIGH
    # lenient must NOT rescue a genuinely-unmeasured row.
    assert lenient["NANDONOR"] == TIER_UNRESOLVED


def test_strict_raises_cross_floor():
    # A row passing at 0.2 but below 0.5 flips high -> low under strict.
    df = pd.DataFrame(
        [
            {
                "target": "BORDERLINE",
                "replicate_pass_flag": True,
                "batch_sensitivity_flag": "not_flagged",
                "offtarget_flag": False,
                "crossdonor_correlation_mean": 0.3,
                "crossguide_correlation": 0.3,
                "n_cells_target": 800,
                "statistical_evidence_grade": 3,
                "n_total_de_genes": 1000,
            }
        ]
    )
    assert robustness_tier(df, strict=False).iloc[0] == TIER_HIGH
    assert robustness_tier(df, strict=True).iloc[0] == TIER_LOW


def test_high_confidence_mask_matches_tier():
    df = _synthetic_cards()
    mask = high_confidence_mask(df)
    assert list(df.loc[mask, "target"]) == ["GOOD"]


def test_robust_rank_filters_then_ranks_and_dedups():
    # Two rows for GOOD (different conditions), one high + one low; the low row
    # for the same target must never sneak into the short-list, and the target
    # appears exactly once.
    df = _synthetic_cards()
    extra = df[df["target"] == "GOOD"].iloc[0].to_dict()
    extra["replicate_pass_flag"] = False  # a low-confidence GOOD condition
    extra["n_total_de_genes"] = 9999
    df2 = pd.concat([df, pd.DataFrame([extra])], ignore_index=True)

    out = robust_rank(df2, top_n=100)
    assert out["available"] is True
    assert out["n_high_confidence"] == 1  # only the high GOOD row
    assert out["n_unresolved"] == 1  # NANDONOR
    returned_targets = [r["target"] for r in out["targets"]]
    assert returned_targets == ["GOOD"]  # deduped to one row
    assert out["targets"][0]["robustness_tier"] == TIER_HIGH
    # the low-confidence GOOD condition (9999 DE genes) was filtered out, so the
    # surviving row is the high one, not the higher-DE unstable one.
    assert out["targets"][0]["n_total_de_genes"] == 1000
    # provenance echoed
    assert out["thresholds"]["cross_min"] == CROSS_MIN
    assert out["thresholds"]["min_cells"] == MIN_CELLS


def test_robust_rank_honest_fallback_when_columns_missing():
    df = pd.DataFrame([{"foo": 1}])
    out = robust_rank(df)
    assert out["available"] is False
    assert out["n_high_confidence"] == 0
    assert out["targets"] == []


# --- real-data (skipif-gated) ----------------------------------------------


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_real_data_high_confidence_magnitude():
    from api import deps  # normalize cell values exactly as the endpoint does

    cards = deps._normalize_cell_values(pd.read_csv(REAL_CARDS, low_memory=False))

    # Lenient variant reproduces the calibration's ~1,102 replicate-passing
    # figure (1,102 minus the handful of 'sensitive' rows).
    lenient = robust_rank(cards, top_n=1000, lenient=True)
    assert lenient["available"] is True
    assert 900 <= lenient["n_high_confidence"] <= 1300, lenient["n_high_confidence"]

    # Conservative default (not_flagged only) is strictly smaller and positive --
    # 372 replicate-passing rows are 'confounded_but_robust' and drop out.
    default = robust_rank(cards, top_n=1000)
    assert 0 < default["n_high_confidence"] < lenient["n_high_confidence"]

    # unknown != 0: the vast majority of rows are unresolved (cross-donor NaN),
    # never silently counted as pass or fail.
    assert default["n_unresolved"] > 10_000
    assert default["n_total"] == len(cards)

    # every returned target's row is genuinely high_confidence (filter-first).
    for record in default["targets"]:
        assert record["robustness_tier"] == TIER_HIGH
    returned = [r["target"] for r in default["targets"]]
    assert len(returned) == len(set(returned))  # one row per target


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_real_data_returned_rows_all_high_confidence_recomputed():
    """Independent recompute: pull each returned target back out of the source
    cards and confirm at least one of its rows is high_confidence."""
    from api import deps

    cards = deps._normalize_cell_values(pd.read_csv(REAL_CARDS, low_memory=False))
    out = robust_rank(cards, top_n=50)
    tier = robustness_tier(cards)
    for record in out["targets"]:
        rows_tier = tier[cards["target"] == record["target"]]
        assert (rows_tier == TIER_HIGH).any(), record["target"]


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_robustness_tier_is_inert_through_compute_readiness():
    """THE decision-separation lock: attaching robustness_tier must not change
    ANY readiness output. Run compute_readiness on the plain frame and on the
    frame carrying robustness_tier; every readiness-produced column must be
    row-identical."""
    from core.readiness import compute_readiness

    cards = pd.read_csv(REAL_CARDS, nrows=60, low_memory=False)
    base = compute_readiness(cards)

    tagged = cards.copy()
    tagged["robustness_tier"] = robustness_tier(tagged).to_numpy()
    after = compute_readiness(tagged)

    readiness_cols = [c for c in base.columns if c not in cards.columns]
    assert "readiness_call" in readiness_cols
    for col in readiness_cols:
        left = base[col].reset_index(drop=True)
        right = after[col].reset_index(drop=True)
        assert left.equals(right), f"robustness_tier changed readiness column {col!r}"
