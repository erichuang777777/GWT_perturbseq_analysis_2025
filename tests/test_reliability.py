"""Tests for the ported reliability/confidence coefficient (G-perturb #133)."""

from __future__ import annotations

import math

import reliability as rl


def test_r_dep_formula_and_monotonicity():
    # perfect reliability on both facets -> 1.0
    assert rl.r_dep(1.0, 1.0) == 1.0
    # equal facets: R=0.5,0.5 -> 1/(1+1+1)=1/3
    assert rl.r_dep(0.5, 0.5) == round(1 / 3, 4)
    # monotone increasing in each facet
    assert rl.r_dep(0.3, 0.5) < rl.r_dep(0.6, 0.5) < rl.r_dep(0.9, 0.5)


def test_unknown_is_none_not_zero():
    # missing/NaN -> None (unknown != 0)
    assert rl.r_dep(None, 0.5) is None
    assert rl.r_dep(float("nan"), 0.5) is None
    # a measured non-positive correlation is reliably UNreliable -> 0.0, distinct from None
    assert rl.r_dep(-0.2, 0.5) == 0.0
    assert rl.r_dep(0.0, 0.5) == 0.0


def test_confidence_tiers():
    assert rl.confidence_tier(None) == "unknown"
    assert rl.confidence_tier(0.0) == "unreliable"
    assert rl.confidence_tier(0.2) == "low"
    assert rl.confidence_tier(0.5) == "moderate"
    assert rl.confidence_tier(0.8) == "high"


def test_reliability_for_card_s_score():
    out = rl.reliability_for_card(0.6, 0.6, effect_size=-4.0)
    assert 0 < out["r_dep"] <= 1
    assert out["confidence_tier"] in {"low", "moderate", "high"}
    # S_t = |effect| * R_dep
    assert out["s_score"] == round(4.0 * out["r_dep"], 4)
    # unmeasured correlation -> r_dep None, s_score None (never 0)
    out2 = rl.reliability_for_card(None, 0.6, effect_size=-4.0)
    assert out2["r_dep"] is None and out2["s_score"] is None
