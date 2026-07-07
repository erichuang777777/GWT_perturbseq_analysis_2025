"""Join-integrity tests: guide->target aggregation and card->readiness linkage
must never silently drop or duplicate rows across the merge boundaries in
build_target_cards.py / readiness_engine.py.
"""
from __future__ import annotations

import pandas as pd


def test_guide_summary_n_guides_matches_real_guide_count(golden_de_stats, golden_guide_kd):
    from build_target_cards import build_cards_frame

    cards = build_cards_frame(golden_de_stats, golden_guide_kd, lib_map=None, benchmark=None, sample_meta=None)
    expected_n_guides = {
        ("ZAP70", "Rest"): 2,
        ("ZAP70", "Stim8hr"): 2,
        ("MED12", "Rest"): 2,
        ("LOWEXPR1", "Rest"): 1,
        ("NOEFFECT1", "Rest"): 1,
    }
    for (target, condition), n in expected_n_guides.items():
        row = cards[(cards["target"] == target) & (cards["condition"] == condition)].iloc[0]
        assert row["n_guides"] == n, f"{target}/{condition}: expected {n} guides, got {row['n_guides']}"


def test_card_build_never_drops_or_duplicates_de_rows(golden_de_stats, golden_guide_kd):
    """The DE table is the row-defining side of the merge (left join on guide
    summary); every DE row must survive exactly once regardless of guide-KD
    coverage.
    """
    from build_target_cards import build_cards_frame

    cards = build_cards_frame(golden_de_stats, golden_guide_kd, lib_map=None, benchmark=None, sample_meta=None)
    assert len(cards) == len(golden_de_stats)
    pairs = list(zip(cards["target"], cards["condition"]))
    assert len(pairs) == len(set(pairs)), "duplicate target/condition rows after guide-KD merge"


def test_guide_kd_row_missing_for_a_target_condition_degrades_not_crashes(golden_de_stats, golden_guide_kd):
    """A target/condition present in DE but entirely absent from guide-KD must
    still produce a row (n_guides=0), not raise or silently vanish.
    """
    from build_target_cards import build_cards_frame

    de = golden_de_stats.copy()
    guide = golden_guide_kd[golden_guide_kd["perturbed_gene_id"] != "ENSG_NOEFFECT1"].copy()
    cards = build_cards_frame(de, guide, lib_map=None, benchmark=None, sample_meta=None)
    row = cards[(cards["target"] == "NOEFFECT1") & (cards["condition"] == "Rest")]
    assert len(row) == 1
    assert row.iloc[0]["n_guides"] == 0
    # No guide-KD row -> baseline expression was never measured (NaN) -> kd_status
    # is "not_assessed" (genuinely unknown), NOT "not_measurable" (which means
    # measured-and-below-floor, a real failure). unknown != a measured failure.
    assert row.iloc[0]["kd_status"] == "not_assessed"


def test_cards_to_readiness_row_linkage_is_one_to_one(golden_cards):
    from readiness_engine import compute_readiness

    readiness = compute_readiness(golden_cards, overlays=None, essentials=None, broad_effect_genes={"MED12"})
    assert len(readiness) == len(golden_cards)
    card_pairs = set(zip(golden_cards["target"], golden_cards["condition"]))
    readiness_pairs = set(zip(readiness["target"], readiness["condition"]))
    assert card_pairs == readiness_pairs


def test_readiness_broad_effect_red_flag_caps_med12_despite_grade_4(golden_cards):
    from readiness_engine import compute_readiness

    readiness = compute_readiness(golden_cards, overlays=None, essentials=None, broad_effect_genes={"MED12"})
    row = readiness[(readiness["target"] == "MED12") & (readiness["condition"] == "Rest")].iloc[0]
    assert row["readiness_call"] == "watchlist"
    assert "broad_effect" in row["red_flag_override"]


def test_readiness_without_broad_effect_set_med12_is_not_capped(golden_cards):
    """Sanity check on the test design itself: the cap above must come from the
    broad_effect_genes set, not from some other property of the MED12 row.
    """
    from readiness_engine import compute_readiness

    readiness = compute_readiness(golden_cards, overlays=None, essentials=None, broad_effect_genes=set())
    row = readiness[(readiness["target"] == "MED12") & (readiness["condition"] == "Rest")].iloc[0]
    assert row["red_flag_override"] == "none"
    assert row["readiness_call"] == "validate"
