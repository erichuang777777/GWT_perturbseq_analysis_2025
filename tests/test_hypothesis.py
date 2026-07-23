"""Tests for the deterministic testable-hypothesis generator (plan P2-C)."""

from __future__ import annotations

import hypothesis as h


def test_activator_predicts_downregulation():
    strongest = {
        "direction": "activator", "module_name": "Th2_program", "condition": "Stim8hr",
        "mean_logfc": -1.4, "n_downstream_hit": 6,
    }
    out = h.build_hypothesis("GATA3", strongest=strongest, next_validation_step="CRISPRi in an OPC-like line")
    assert out["available"] is True
    assert "down-regulate" in out["hypothesis"]
    assert "Th2 program" in out["hypothesis"]
    assert "Stim8hr" in out["hypothesis"]
    assert out["suggested_validation"] == "CRISPRi in an OPC-like line"
    assert any("signed_module_effect" in b for b in out["basis"])
    assert "not a therapeutic claim" in out["caveat"]


def test_repressor_predicts_upregulation():
    strongest = {"direction": "repressor", "module_name": "Treg_program", "condition": "Rest",
                 "mean_logfc": 1.1, "n_downstream_hit": 4}
    out = h.build_hypothesis("FOXP3", strongest=strongest)
    assert "up-regulate" in out["hypothesis"]


def test_pathway_axis_fallback_when_no_module_effect():
    out = h.build_hypothesis("ZAP70", strongest=None, pathway_axis="TCR_core")
    assert out["available"] is True
    assert "TCR core" in out["hypothesis"]


def test_next_step_alone_still_available():
    out = h.build_hypothesis("XYZ1", strongest=None, pathway_axis=None, next_validation_step="replicate in a second donor")
    assert out["available"] is True
    assert out["hypothesis"] is None
    assert out["suggested_validation"] == "replicate in a second donor"


def test_no_signal_is_honest_unavailable_not_fabricated():
    out = h.build_hypothesis("GHOST1", strongest=None, pathway_axis=None, next_validation_step=None)
    assert out["available"] is False
    assert "insufficient" in out["reason"]


def test_strongest_module_prefers_more_hits():
    effects = [
        {"direction": "activator", "module_name": "A", "mean_logfc": -0.6, "n_downstream_hit": 2},
        {"direction": "repressor", "module_name": "B", "mean_logfc": 0.9, "n_downstream_hit": 9},
        {"direction": "weak_or_mixed", "module_name": "C", "mean_logfc": 0.1, "n_downstream_hit": 50},
    ]
    picked = h._strongest_module(effects)
    assert picked["module_name"] == "B"  # most hits among confident directions; weak_or_mixed excluded
