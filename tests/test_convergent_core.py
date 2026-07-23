"""Tests for the convergent-core re-analysis (deterministic; skips if tables absent)."""

from __future__ import annotations

import numpy as np
import pytest

import analysis.convergent_core as cc

_HAS = cc.tables_present()


def test_matched_perm_is_deterministic_and_bounded():
    rng_uni = [f"g{i}" for i in range(200)]
    is_t = np.array([i < 50 for i in range(200)])
    is_h = np.array([i % 3 == 0 for i in range(200)])
    cov = np.arange(200, dtype=float)
    a = cc._matched_perm_p(rng_uni, is_t, is_h, cov, nperm=500)
    b = cc._matched_perm_p(rng_uni, is_t, is_h, cov, nperm=500)
    assert a == b                     # deterministic (seeded)
    assert 0.0 < a["p"] <= 1.0


@pytest.mark.skipif(not _HAS, reason="source suppl tables not present in this checkout")
def test_convergence_and_specificity_hold():
    r = cc.run()
    # convergence survives confound control and strengthens at higher stringency
    assert r["convergence"][0.95]["p"] < 0.05
    assert r["convergence"][0.95]["obs"] > r["convergence"][0.95]["null_mean"]
    # the core is negative-control-specific (paper's own controls)
    s = r["specificity"]
    assert s["core_in_real_disease"] == s["core_size"]
    assert s["core_in_negative_control"] <= 1
    # the known tolerance / IL-2 spine is in the core
    core = set(cc.core_genes(cc.load_axes()))
    assert {"CBLB", "EGR2", "STAT5A", "STAT5B"} <= core


@pytest.mark.skipif(not _HAS, reason="source suppl tables not present in this checkout")
def test_held_out_activation_is_null_axis_specific():
    # Honest negative: the core does NOT generalize to the held-out activation
    # signature (axis-specific, and evidence AGAINST a generic-strength confound).
    r = cc.run()
    assert r["held_out_activation"][0.90]["p"] > 0.2
    assert abs(r["ota_vs_activation_spearman"]) < 0.2   # activation is an independent axis
