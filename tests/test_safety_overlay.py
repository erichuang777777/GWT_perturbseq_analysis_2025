"""Membrane/tractability + safety-window overlays (§1.12 / ADC ingestion spec).

Regression-pins the real, checked-in ADC-derived membrane overlay
(docs/mvp-research/adc_overlay_gwt_overlap_full.csv) and the real GTEx
per-tissue expression overlay
(sources/target_tool_cache/_overlays/gtex_per_tissue.parquet) -- both are now
present in this checkout, so both halves of §1.12 are covered with live data,
not honest-fallback placeholders.
"""
from __future__ import annotations

import pandas as pd
import pytest


def test_load_membrane_overlay_real_file():
    from safety_overlay import load_membrane_tractability_overlay

    result = load_membrane_tractability_overlay()
    assert result["available"] is True
    assert len(result["table"]) == 5588
    assert "ensembl_id" in result["table"].columns


def test_load_membrane_overlay_missing_file_is_honest(tmp_path):
    from safety_overlay import load_membrane_tractability_overlay

    result = load_membrane_tractability_overlay(path=tmp_path / "does_not_exist.csv")
    assert result["available"] is False
    assert result["table"].empty


def test_load_gtex_safety_overlay_real_file():
    from safety_overlay import load_gtex_safety_overlay

    result = load_gtex_safety_overlay()
    assert result["available"] is True
    assert len(result["table"]) == 9718
    assert set(["ensembl_id", "gene_symbol", "n_tissues_expressed", "max_expression_outside_cd4_context"]).issubset(
        result["table"].columns
    )


def test_load_gtex_safety_overlay_missing_file_is_honest(tmp_path):
    from safety_overlay import load_gtex_safety_overlay

    result = load_gtex_safety_overlay(path=tmp_path / "does_not_exist.parquet")
    assert result["available"] is False
    assert result["table"].empty


def test_tractability_from_membrane_overlay_matches_real_verified_values():
    """Regression-pins the exact real values independently verified during
    development, and cross-checked against the ADC ingestion spec's own
    table (docs/mvp-research/ADC_LOCAL_DATA_INGESTION_SPEC.md §2a)."""
    from safety_overlay import load_membrane_tractability_overlay, tractability_from_membrane_overlay

    overlay = load_membrane_tractability_overlay()
    # surface + extracellular domain -> antibody (surface)
    assert tractability_from_membrane_overlay("ENSG00000198851", overlay) == ("antibody (surface)", 3)  # CD3E
    assert tractability_from_membrane_overlay("ENSG00000198821", overlay) == ("antibody (surface)", 3)  # CD247
    assert tractability_from_membrane_overlay("ENSG00000213658", overlay) == ("antibody (surface)", 3)  # LAT
    # druggable but not membrane -> small molecule
    assert tractability_from_membrane_overlay("ENSG00000184634", overlay) == ("small molecule", 3)  # MED12
    # neither membrane nor druggable -> a real "none" verdict, not unknown
    assert tractability_from_membrane_overlay("ENSG00000112237", overlay) == ("none", 0)  # CCNC


def test_tractability_from_membrane_overlay_gene_absent_is_unknown_not_none():
    """A gene absent from the ~49%-coverage overlay is unchecked, not
    'not druggable' -- must be unknown, never silently 0/'none'."""
    from safety_overlay import UNKNOWN, load_membrane_tractability_overlay, tractability_from_membrane_overlay

    overlay = load_membrane_tractability_overlay()
    modality, score = tractability_from_membrane_overlay("ENSG00000000000_NOT_A_REAL_GENE", overlay)
    assert modality == UNKNOWN
    assert score == UNKNOWN


def test_tractability_from_membrane_overlay_unavailable_overlay_is_unknown():
    from safety_overlay import UNKNOWN, tractability_from_membrane_overlay

    unavailable = {"available": False, "reason": "x", "table": pd.DataFrame()}
    assert tractability_from_membrane_overlay("ENSG00000198851", unavailable) == (UNKNOWN, UNKNOWN)


def test_safety_window_from_gtex_is_unknown_when_overlay_unavailable():
    from safety_overlay import UNKNOWN, safety_window_from_gtex

    unavailable = {"available": False, "reason": "x", "table": pd.DataFrame()}
    assert safety_window_from_gtex("ENSG00000198851", unavailable) == UNKNOWN


def test_safety_window_from_gtex_matches_real_verified_values():
    """Regression-pins the real, independently spot-checked off-context
    aggregation (Blood/Spleen excluded, per the ADC ingestion spec's
    context-inversion note): CD3E is off-context-expressed in 21/30 tissues;
    MED12 (a Mediator-complex subunit, plausibly housekeeping) in 28/30 --
    consistent with MED12 also being the C7 broad_effect quarantine's
    textbook example.
    """
    from safety_overlay import load_gtex_safety_overlay, safety_window_from_gtex

    overlay = load_gtex_safety_overlay()
    assert safety_window_from_gtex("ENSG00000198851", overlay) == 21  # CD3E
    assert safety_window_from_gtex("ENSG00000184634", overlay) == 28  # MED12


def test_safety_window_from_gtex_gene_absent_is_unknown():
    """VAV1 is confirmed absent from this ~9,718-gene GTEx overlay -- must be
    unknown (unchecked), never a fabricated breadth count."""
    from safety_overlay import UNKNOWN, load_gtex_safety_overlay, safety_window_from_gtex

    overlay = load_gtex_safety_overlay()
    assert safety_window_from_gtex("ENSG00000141968", overlay) == UNKNOWN  # VAV1


def test_readiness_engine_overlays_are_a_pure_upgrade_never_a_regression(real_cards, real_data_available):
    """Both overlays together must only ever help, never hurt: domains
    causally independent of BOTH tractability and safety (biology,
    translation, biomarker, disease relevance, genetics) stay byte-identical.
    readiness_call/overall_readiness_stage are not a function of
    safety_window_score at all (see readiness_engine._stage's signature --
    it never takes a safety argument), so they may only move toward MORE
    advanced due to the membrane overlay's tractability upgrade, never the
    reverse, and are otherwise unaffected by the GTEx overlay.
    """
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from readiness_engine import CALL_ORDER, compute_readiness
    from safety_overlay import load_gtex_safety_overlay, load_membrane_tractability_overlay

    baseline = compute_readiness(real_cards, overlays=None, essentials=None, broad_effect_genes=None)
    membrane = load_membrane_tractability_overlay()
    gtex = load_gtex_safety_overlay()
    upgraded = compute_readiness(
        real_cards, overlays=None, essentials=None, broad_effect_genes=None, membrane_overlay=membrane, gtex_overlay=gtex
    )
    assert len(baseline) == len(upgraded)

    independent_cols = [
        "biology_causality_score",
        "translation_score",
        "biomarker_score",
        "disease_relevance_score",
        "human_genetic_support",
    ]
    for col in independent_cols:
        assert (baseline[col].astype(str) == upgraded[col].astype(str)).all(), f"{col} must be unaffected by either overlay"

    call_rank = {c: i for i, c in enumerate(CALL_ORDER)}
    b_rank = baseline["readiness_call"].map(call_rank)
    u_rank = upgraded["readiness_call"].map(call_rank)
    assert (u_rank >= b_rank).all(), "overlays must never make a readiness_call less advanced"
    assert (u_rank > b_rank).any(), "membrane overlay should improve at least one real gene's call (sanity check the overlay is wired up)"

    cd3e_before = baseline[baseline["target"] == "CD3E"].iloc[0]
    cd3e_after = upgraded[upgraded["target"] == "CD3E"].iloc[0]
    assert cd3e_before["tractability_modality"] == "unknown"
    assert cd3e_after["tractability_modality"] == "antibody (surface)"
    # safety_window_score is a real, non-essential-gated value now that both
    # overlays have real data -- confirms the GTEx wiring is actually live.
    assert cd3e_before["safety_window_score"] == "unknown"
    assert cd3e_after["safety_window_score"] == 21


def test_readiness_engine_gtex_overlay_alone_does_not_change_tractability(real_cards, real_data_available):
    """Passing only gtex_overlay (no membrane_overlay) must leave
    tractability_modality/score completely untouched -- the two overlays are
    independent upgrade paths, not coupled."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from readiness_engine import compute_readiness
    from safety_overlay import load_gtex_safety_overlay

    baseline = compute_readiness(real_cards, overlays=None, essentials=None, broad_effect_genes=None)
    gtex = load_gtex_safety_overlay()
    gtex_only = compute_readiness(
        real_cards, overlays=None, essentials=None, broad_effect_genes=None, gtex_overlay=gtex
    )
    for col in ["tractability_modality", "tractability_score", "readiness_call", "overall_readiness_stage"]:
        assert (baseline[col].astype(str) == gtex_only[col].astype(str)).all(), f"{col} must be unaffected by gtex_overlay alone"

    cd3e = gtex_only[gtex_only["target"] == "CD3E"].iloc[0]
    assert cd3e["safety_window_score"] == 21


def test_readiness_engine_without_overlays_is_unchanged_regression():
    """Omitting membrane_overlay/gtex_overlay entirely (the pre-existing call
    signature) must behave exactly as before this feature was added."""
    from readiness_engine import compute_readiness

    cards = pd.DataFrame(
        {
            "target": ["CD3E"],
            "condition": ["Rest"],
            "target_id": ["ENSG00000198851"],
            "statistical_evidence_grade": [4],
            "pathway_axis": ["unassigned"],
            "replicate_pass_flag": [True],
            "crossdonor_correlation_mean": [0.5],
            "n_total_de_genes": [60],
            "clinical_axis": ["unassigned"],
            "positive_control_similarity": [0],
            "offtarget_flag": [False],
            "batch_sensitivity_flag": ["not_flagged"],
            "score_cap_reason": ["none"],
            "ontarget_significant": [True],
            "kd_status": ["confirmed"],
        }
    )
    result = compute_readiness(cards, overlays=None, essentials=None, broad_effect_genes=None)
    assert result.iloc[0]["tractability_modality"] == "unknown"
    assert result.iloc[0]["tractability_score"] == "unknown"
