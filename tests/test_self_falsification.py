"""Tests for the self-falsification audit (Action 3)."""

from __future__ import annotations

import pandas as pd

import self_falsification as sf


def _breadth(rows):
    return pd.DataFrame(rows, columns=["target_gene", "trans_effect_breadth"])


def test_hub_darling_audit_detects_veto_enrichment():
    # Top hubs are on the veto list; the low-breadth tail is clean.
    rows = [("HUB1", 100), ("HUB2", 90), ("HUB3", 80), ("HUB4", 70), ("LEAF1", 3), ("LEAF2", 2), ("LEAF3", 1), ("LEAF4", 1)]
    veto = {"HUB1", "HUB2", "HUB3", "HUB4"}
    a = sf.hub_darling_audit(_breadth(rows), veto, top_n=4)
    assert a["available"] is True
    assert a["top_breadth_vetoed_pct"] == 1.0     # all top hubs vetoed
    assert a["low_breadth_vetoed_pct"] == 0.0     # no leaf vetoed
    assert a["enrichment"] is None                 # low-breadth rate is 0 -> even stronger
    assert set(a["darlings_the_system_rejects"]) == veto


def test_hub_darling_audit_finite_enrichment():
    rows = [("H1", 100), ("H2", 90), ("L1", 5), ("L2", 4)]
    veto = {"H1", "L1"}  # one hub, one leaf vetoed -> enrichment 1.0
    a = sf.hub_darling_audit(_breadth(rows), veto, top_n=2)
    assert a["top_breadth_vetoed_pct"] == 0.5
    assert a["low_breadth_vetoed_pct"] == 0.5
    assert a["enrichment"] == 1.0


def test_audit_honest_unavailable_without_data():
    assert sf.hub_darling_audit(None, {"X"})["available"] is False
    assert sf.hub_darling_audit(_breadth([("A", 1)]), set())["available"] is False


def test_anchor_cases_contain_a_known_reject():
    # The point of the audit: a calibration set that includes a case the system
    # must say NO to (not only positives).
    verdicts = {c["gene"]: c["system_should"] for c in sf.ANCHOR_CASES}
    assert verdicts.get("ZAP70") == "advance"
    assert verdicts.get("MED12") == "reject_broad_effect"
    for c in sf.ANCHOR_CASES:
        assert c["external_confirmation"]  # every anchor carries a receipt


def test_run_report_shape():
    rep = sf.run_self_falsification(
        breadth_df=_breadth([("HUB1", 100), ("HUB2", 90), ("LEAF1", 2), ("LEAF2", 1)]),
        veto_lists={"veto": {"HUB1", "HUB2"}},
        top_n=2,
    )
    assert rep["kind"] == "self_falsification_audit"
    assert rep["hub_darling_audit"]["top_breadth_vetoed_pct"] == 1.0
    assert rep["anchor_cases"]
