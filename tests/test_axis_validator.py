"""Tests for the ported axis validator (Validated Th1/Th2 Target Map #240)."""

from __future__ import annotations

import numpy as np

import axis_validator as av


def test_strong_axis_validated_weak_axis_exploratory():
    genes = [f"G{i}" for i in range(60)]
    truth = {g: float(i) for i, g in enumerate(genes)}
    strong = {g: truth[g] + np.random.default_rng(0).normal(0, 2) for g in genes}  # tracks truth
    weak = {g: np.random.default_rng(int(g[1:]) + 1).normal() for g in genes}      # noise
    assert av.validate_axis(strong, truth)["verdict"] == "validated"
    assert av.validate_axis(weak, truth)["verdict"] == "exploratory"


def test_too_few_overlap_is_not_evaluable():
    axis = {"A": 1.0, "B": 2.0}
    truth = {"A": 1.0, "B": 2.0, "C": 3.0}
    r = av.validate_axis(axis, truth, min_matched=20)
    assert r["verdict"] == "not_evaluable" and "overlap" in r["reason"]


def test_auroc_recovers_known_positives():
    genes = [f"G{i}" for i in range(60)]
    truth = {g: float(i) for i, g in enumerate(genes)}
    # score ranks the top-10 truth genes highest -> known set recovered
    known = set(genes[-10:])
    axis = {g: truth[g] for g in genes}
    r = av.validate_axis(axis, truth, known_set=known)
    assert r["auroc"] is not None and r["auroc"] > 0.9
    assert r["verdict"] == "validated"


def test_rank_auc_matches_definition():
    y = np.array([0, 0, 1, 1])
    s = np.array([0.1, 0.2, 0.3, 0.4])   # perfect separation
    assert av._rank_auc(y, s) == 1.0
