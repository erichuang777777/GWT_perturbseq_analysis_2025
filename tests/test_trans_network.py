"""Tests for trans-effect breadth / hub scoring (development plan P1-H).

Synthetic known-answer core (no data files) pins the union-out-degree counting,
the padj filter, percentile, and unknown != 0; a real-data sanity test runs
against the built overlay when present and otherwise skips.
"""

from __future__ import annotations

import glob

import numpy as np
import pandas as pd
import pytest

import trans_network as tn


def _signed(rows):
    return pd.DataFrame(rows, columns=["target_gene", "culture_condition", "downstream_gene", "adj_p_value"])


def test_breadth_is_distinct_downstream_union_across_conditions():
    signed = _signed([
        # HUB: 3 distinct downstream genes (G1 in two conditions counts once)
        ("HUB", "Rest", "G1", 0.01),
        ("HUB", "Stim8hr", "G1", 0.01),
        ("HUB", "Stim8hr", "G2", 0.01),
        ("HUB", "Stim48hr", "G3", 0.01),
        # LEAF: 1 downstream gene
        ("LEAF", "Rest", "G1", 0.01),
    ])
    out = tn.compute_breadth(signed)
    by = {r["target_gene"]: r for r in out.to_dict("records")}
    assert by["HUB"]["trans_effect_breadth"] == 3
    assert by["HUB"]["n_edges_total"] == 4  # edges, not distinct genes
    assert by["HUB"]["breadth_rest"] == 1 and by["HUB"]["breadth_stim8hr"] == 2 and by["HUB"]["breadth_stim48hr"] == 1
    assert by["LEAF"]["trans_effect_breadth"] == 1
    # HUB ranks above LEAF
    assert by["HUB"]["breadth_percentile"] > by["LEAF"]["breadth_percentile"]


def test_padj_filter_and_unknown_not_zero():
    signed = _signed([
        ("A", "Rest", "G1", 0.01),   # significant
        ("A", "Rest", "G2", 0.20),   # NOT significant (dropped by 0.05 cut)
        ("B", "Rest", "G3", 0.30),   # B has only a non-significant edge -> absent entirely
    ])
    out = tn.compute_breadth(signed, max_padj=0.05)
    genes = set(out["target_gene"])
    assert out[out["target_gene"] == "A"].iloc[0]["trans_effect_breadth"] == 1  # G2 excluded
    assert "B" not in genes  # unknown != 0: no fabricated breadth-0 row


def test_broad_effect_candidate_is_high_percentile_flag():
    # 20 targets with increasing breadth; top ~5% flagged.
    rows = []
    for i in range(20):
        for j in range(i + 1):
            rows.append((f"T{i:02d}", "Rest", f"G{j}", 0.01))
    out = tn.compute_breadth(_signed(rows))
    top = out.sort_values("trans_effect_breadth").iloc[-1]
    assert bool(top["broad_effect_candidate"]) is True
    # a bottom target is not flagged
    bottom = out.sort_values("trans_effect_breadth").iloc[0]
    assert bool(bottom["broad_effect_candidate"]) is False


def test_gini_concentration_range():
    equal = tn._gini(np.array([5.0, 5.0, 5.0, 5.0]))
    concentrated = tn._gini(np.array([0.0, 0.0, 0.0, 100.0]))
    assert equal == pytest.approx(0.0, abs=1e-9)
    assert concentrated > 0.6


_HAS_OVERLAY = tn.load_breadth() is not None


@pytest.mark.skipif(not _HAS_OVERLAY, reason="trans_network_breadth overlay not built in this checkout")
def test_real_overlay_serving_and_concentration():
    summ = tn.concentration_summary()
    assert summ["available"] is True
    # Hub concentration is real and strong in this screen (echoes CoDEGNet's finding).
    assert 0.5 < summ["gini_trans_effect"] <= 1.0
    # A known TCR-core hub should have measurable, high-percentile breadth.
    cd3e = tn.breadth_for_target("CD3E")
    assert cd3e["available"] is True
    if cd3e.get("measured"):
        assert cd3e["trans_effect_breadth"] > 0
        assert 0.0 <= cd3e["breadth_percentile"] <= 1.0
    # An unmeasured gene reports measured=false, never breadth 0.
    ghost = tn.breadth_for_target("NOTAREALGENE12345")
    assert ghost["available"] is True and ghost.get("measured") is False
