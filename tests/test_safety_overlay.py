"""Membrane/tractability + safety-window overlays (§1.12 / ADC ingestion spec).

Regression-pins the real, checked-in ADC-derived membrane overlay
(docs/mvp-research/adc_overlay_gwt_overlap_full.csv) and confirms the GTEx
safety-window half honestly degrades until that file is supplied (it is not
yet present in this checkout).
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


def test_load_gtex_safety_overlay_is_honestly_unavailable_in_this_checkout():
    """gtex_per_tissue.parquet has not been supplied yet (lives only on the
    project owner's machine) -- this must degrade honestly, not fabricate a
    safety score. Regression guard: if this ever flips to True, the wiring
    that assumed 'always unavailable today' should be revisited."""
    from safety_overlay import load_gtex_safety_overlay

    result = load_gtex_safety_overlay()
    assert result["available"] is False
    assert "not yet" in result["reason"] or "not found" in result["reason"]


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
    from safety_overlay import UNKNOWN, load_gtex_safety_overlay, safety_window_from_gtex

    overlay = load_gtex_safety_overlay()
    assert safety_window_from_gtex("ENSG00000198851", overlay) == UNKNOWN


def test_readiness_engine_membrane_overlay_is_a_pure_upgrade_never_a_regression(real_cards, real_data_available):
    """The membrane overlay must only ever help, never hurt: domains causally
    independent of tractability (biology, translation, biomarker, disease
    relevance, genetics, safety) stay byte-identical, and readiness_call may
    only move toward MORE advanced (R2->R3 etc.) for genes whose tractability
    improved from unknown to a real modality -- never the reverse.
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
        "safety_window_score",
    ]
    for col in independent_cols:
        assert (baseline[col].astype(str) == upgraded[col].astype(str)).all(), f"{col} must be unaffected by the membrane overlay"

    call_rank = {c: i for i, c in enumerate(CALL_ORDER)}
    b_rank = baseline["readiness_call"].map(call_rank)
    u_rank = upgraded["readiness_call"].map(call_rank)
    assert (u_rank >= b_rank).all(), "membrane overlay must never make a readiness_call less advanced"
    assert (u_rank > b_rank).any(), "membrane overlay should improve at least one real gene's call (sanity check the overlay is wired up)"

    cd3e_before = baseline[baseline["target"] == "CD3E"].iloc[0]
    cd3e_after = upgraded[upgraded["target"] == "CD3E"].iloc[0]
    assert cd3e_before["tractability_modality"] == "unknown"
    assert cd3e_after["tractability_modality"] == "antibody (surface)"


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
