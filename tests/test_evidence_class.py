"""Tests for the ported evidence-class vocabulary + invariants (PerturbGate #155)."""

from __future__ import annotations

import evidence_class as ec


def test_call_maps_to_typed_class_and_depth():
    a = ec.classify("advance", has_external_evidence=True)
    assert a["evidence_class"] == "RETAINED_ADVANCE" and a["evidence_depth"] == "deep"
    d = ec.classify("deprioritize", red_flags=["essential_gene"])
    assert d["evidence_class"] == "REJECTED_DEPRIORITIZE" and "essential_gene" in d["reason"]
    # unknown call -> UNRESOLVED, never a rejection (unknown != 0)
    u = ec.classify(None)
    assert u["evidence_class"] == "UNRESOLVED" and u["evidence_depth"] == "screen_only"


def test_funnel_conservation():
    good = [{"name": "screen", "entering": 100, "advanced": 10, "not_advanced": 60,
             "rejected": 25, "unresolved": 5, "source_artifact": "cards.csv"}]
    assert ec.check_funnel(good) == []
    bad = [{"name": "screen", "entering": 100, "advanced": 10, "not_advanced": 60,
            "rejected": 25, "unresolved": 0, "source_artifact": "cards.csv"}]  # 95 != 100
    probs = ec.check_funnel(bad)
    assert probs and "!= entering" in probs[0]
    # missing source is flagged
    assert any("no source_artifact" in p for p in ec.check_funnel(
        [{"name": "x", "entering": 1, "advanced": 1, "not_advanced": 0, "rejected": 0, "unresolved": 0}]))


def test_depth_honesty_blocks_unbacked_deep_rejection():
    rows = [{"target": "X", "evidence_class": "REJECTED_DEPRIORITIZE",
             "evidence_depth": "screen_only", "claims_deep_rejection": True}]
    probs = ec.check_depth_honesty(rows)
    assert probs and "deep rejection" in probs[0]
    # a properly-backed deep rejection passes
    ok = [{"target": "Y", "evidence_class": "REJECTED_DEPRIORITIZE",
           "evidence_depth": "deep", "claims_deep_rejection": True}]
    assert ec.check_depth_honesty(ok) == []
