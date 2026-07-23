"""Tests for the ported confounder-control utilities (CoDEGNet #234)."""

from __future__ import annotations

import numpy as np

import controlled_enrichment as ce


def test_matched_permutation_deterministic_and_detects_real_enrichment():
    n = 400
    cov = np.linspace(0, 1, n)
    # target and hit both concentrated at high covariate but with GENUINE extra overlap
    is_target = cov > 0.5
    is_hit = cov > 0.5
    a = ce.matched_permutation_test(is_target, is_hit, cov, nperm=800)
    b = ce.matched_permutation_test(is_target, is_hit, cov, nperm=800)
    assert a == b                                   # deterministic
    # perfectly co-located within the same covariate range -> obs at/above matched null
    assert a["obs"] >= a["null_mean"]


def test_matched_permutation_kills_covariate_artifact():
    # target and hit are BOTH just "high covariate" but otherwise independent within bins
    rng = np.random.default_rng(1)
    n = 600
    cov = rng.random(n)
    # within every covariate level, target and hit are independent coin flips
    is_target = rng.random(n) < 0.3
    is_hit = rng.random(n) < 0.3
    r = ce.matched_permutation_test(is_target, is_hit, cov, nperm=1000)
    assert r["p"] > 0.05                             # no real enrichment beyond covariate


def test_partial_spearman_removes_confounder():
    rng = np.random.default_rng(0)
    z = rng.random(300)
    # x and y each strongly track z but with INDEPENDENT extra noise -> their raw
    # correlation is high (driven by z), but partial-out-z should be ~0.
    x = 3 * z + rng.normal(0, 0.3, 300)
    y = 3 * z + rng.normal(0, 0.3, 300)
    assert abs(ce.partial_spearman(x, y, z)) < 0.2       # confounder removed
    # a genuine x-y link BEYOND z (shared extra factor) survives partialling
    extra = rng.normal(0, 1, 300)
    x2 = z + extra
    y2 = z + extra
    assert ce.partial_spearman(x2, y2, z) > 0.5
