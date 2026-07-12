"""Descriptive genetic-support + composite-safety-liability enrichment (roadmap Phase 1).

Covers the three additive, DESCRIPTIVE fields added in Phase 1 (P1.1/P1.2/P1.3):

* ``genetic_support_confidence`` (+ ``genetic_support_max_genetic_score``) --
  graded from the real, committed per-gene Open Targets evidence snapshots at
  ``sources/target_tool_cache/_evidence/<gene>.json``.
* ``composite_safety_liability`` -- composes the two real overlays (gnomAD
  LOEUF/pLI constraint + GTEx off-context expression breadth) into one disclosed
  on-target LIABILITY tier.
* ``trait_liability_similarity`` (+ reason) -- honest-fallback stub (no
  adverse-event reference vocabulary is committed in this repo).

Plus the load-bearing invariant: none of these descriptive fields may move
``readiness_call`` / ``overall_readiness_stage`` (same causal-independence
property enforced for ``safety_window_score`` and the gnomAD overlay).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = REPO_ROOT / "sources" / "target_tool_cache" / "_evidence"


# Ensembl IDs for the real shortlist genes used below (from the committed
# gnomAD seed / GTEx overlay / evidence snapshots).
ENSEMBL = {
    "VAV1": "ENSG00000141968",
    "MED12": "ENSG00000184634",
    "PLCG1": "ENSG00000124181",
    "CD3E": "ENSG00000198851",
    "LAT": "ENSG00000213658",
    "IL2RA": "ENSG00000134460",
}


def _snapshot(gene: str):
    from evidence.external_cache import load_snapshot

    return load_snapshot(EVIDENCE_DIR, gene)


def _has_evidence(gene: str) -> bool:
    return (EVIDENCE_DIR / f"{gene}.json").exists()


# --------------------------------------------------------------------------- #
# P1.1 / P1.2 -- genetic_support_confidence tiers on REAL evidence snapshots    #
# --------------------------------------------------------------------------- #


def test_genetic_support_strong_on_real_med12_snapshot():
    """MED12's real Open Targets snapshot carries genetic_association_score ~0.8-0.9
    across several diseases -> strong_genetic_association."""
    if not _has_evidence("MED12"):
        pytest.skip("MED12 evidence snapshot not present in this checkout")
    from common.evidence_grading import genetic_support_confidence_from_evidence

    tier, score = genetic_support_confidence_from_evidence(_snapshot("MED12"))
    assert tier == "strong_genetic_association"
    assert isinstance(score, float) and score >= 0.5


def test_genetic_support_strong_on_real_plcg1_snapshot():
    if not _has_evidence("PLCG1"):
        pytest.skip("PLCG1 evidence snapshot not present in this checkout")
    from common.evidence_grading import genetic_support_confidence_from_evidence

    tier, score = genetic_support_confidence_from_evidence(_snapshot("PLCG1"))
    assert tier == "strong_genetic_association"
    assert score == pytest.approx(0.6606478352198834)


def test_genetic_support_none_on_real_vav1_snapshot():
    """VAV1's real snapshot is Open-Targets-OK with the gene resolved, but every
    associated disease's genetic_association_score is null/0 (its high overall
    scores are cancer literature/somatic, NOT germline genetics) -> a real
    'no_genetic_association' verdict with max genetic score 0.0, never a
    fabricated strong tier."""
    if not _has_evidence("VAV1"):
        pytest.skip("VAV1 evidence snapshot not present in this checkout")
    from common.evidence_grading import genetic_support_confidence_from_evidence

    tier, score = genetic_support_confidence_from_evidence(_snapshot("VAV1"))
    assert tier == "no_genetic_association"
    assert score == 0.0


def test_genetic_support_unknown_when_open_targets_unavailable_real_il2ra():
    """IL2RA's real snapshot has open_targets source_status='unavailable' (the
    sandbox couldn't reach Open Targets) -> unknown, never 'no' (unmeasured != none)."""
    if not _has_evidence("IL2RA"):
        pytest.skip("IL2RA evidence snapshot not present in this checkout")
    from common.evidence_grading import genetic_support_confidence_from_evidence

    tier, score = genetic_support_confidence_from_evidence(_snapshot("IL2RA"))
    assert tier == "unknown"
    assert score == "unknown"


def test_genetic_support_unknown_when_no_snapshot_at_all():
    """A gene with no committed snapshot -> unknown (unmeasured), never a
    fabricated tier or a silent 'none'."""
    from common.evidence_grading import genetic_support_confidence_from_evidence

    assert genetic_support_confidence_from_evidence(None) == ("unknown", "unknown")


def test_genetic_support_moderate_tier_threshold():
    """A positive-but-sub-0.5 genetic_association_score grades to 'moderate',
    distinct from 'strong' -- pins the disclosed STRONG_GENETIC_THRESHOLD cut."""
    from common.evidence_grading import genetic_support_confidence_from_evidence

    snap = {
        "sources": {
            "open_targets": {
                "source_status": "ok",
                "items": [{"id": "ENSG_X", "name": "X"}],
                "associated_diseases": [{"disease": "d", "genetic_association_score": 0.3}],
            }
        }
    }
    tier, score = genetic_support_confidence_from_evidence(snap)
    assert tier == "moderate_genetic_association"
    assert score == pytest.approx(0.3)


# --------------------------------------------------------------------------- #
# P1.3 -- composite_safety_liability composing the two REAL overlays            #
# --------------------------------------------------------------------------- #


def test_composite_high_when_both_risk_signals_present():
    """loss-intolerant constraint + broad off-context breadth (>= median 26) ->
    highest liability tier."""
    from safety_overlay import composite_safety_liability

    assert composite_safety_liability("loss_intolerant", 28) == "high"


def test_composite_moderate_when_exactly_one_risk_signal():
    from safety_overlay import composite_safety_liability

    assert composite_safety_liability("loss_intolerant", 10) == "moderate"  # constraint only
    assert composite_safety_liability("none", 28) == "moderate"  # breadth only


def test_composite_low_when_neither_risk_signal():
    from safety_overlay import composite_safety_liability

    assert composite_safety_liability("none", 10) == "low"


def test_composite_unknown_when_either_component_unknown():
    """unknown != 0: if EITHER overlay didn't cover the gene, the composite is
    unknown -- it never treats an unmeasured component as 'no risk'."""
    from safety_overlay import composite_safety_liability

    assert composite_safety_liability("unknown", 28) == "unknown"  # gnomAD missing
    assert composite_safety_liability("loss_intolerant", "unknown") == "unknown"  # GTEx missing
    assert composite_safety_liability("unknown", "unknown") == "unknown"


def test_composite_on_real_overlays_med12_high_vav1_unknown_cd3e_low():
    """End-to-end on the REAL committed overlays (authentic gnomAD v2.1.1):
    MED12 (LOEUF 0.071 -> loss intolerant; GTEx breadth 28) -> high; CD3E
    (LOEUF 0.923 -> none; breadth 21 < 26) -> low; VAV1 (loss intolerant but
    ABSENT from the GTEx overlay) -> unknown, demonstrating honest availability
    propagation."""
    from safety_overlay import (
        composite_safety_liability,
        gnomad_flag_from_constraint,
        load_gnomad_constraint_overlay,
        load_gtex_safety_overlay,
        safety_window_from_gtex,
    )

    gnomad = load_gnomad_constraint_overlay()
    gtex = load_gtex_safety_overlay()

    def composite(gene):
        flag = gnomad_flag_from_constraint(ENSEMBL[gene], gnomad)
        window = safety_window_from_gtex(ENSEMBL[gene], gtex)
        return composite_safety_liability(flag, window)

    assert composite("MED12") == "high"
    assert composite("CD3E") == "low"
    assert composite("VAV1") == "unknown"


# --------------------------------------------------------------------------- #
# P1.3 -- trait_liability_similarity honest-fallback stub                       #
# --------------------------------------------------------------------------- #


def test_trait_similarity_unknown_with_reason_when_no_reference_vocab():
    """No adverse-event reference vocabulary is committed in this repo, so the
    default path returns unknown + an explicit reason -- never a fabricated
    similarity score."""
    from common.evidence_grading import trait_liability_similarity

    tier, reason = trait_liability_similarity(_snapshot("MED12") if _has_evidence("MED12") else None)
    assert tier == "unknown"
    assert "adverse-event reference vocabulary" in reason
    assert reason  # non-empty


def test_trait_similarity_matches_only_when_a_vocab_is_supplied():
    """If a caller ever supplies a real adverse-event vocabulary, the stub
    matches the target's associated traits against it (proving it is wired to
    real data, not a hard-coded unknown)."""
    from common.evidence_grading import trait_liability_similarity

    snap = {
        "sources": {
            "open_targets": {
                "source_status": "ok",
                "items": [{"id": "X", "name": "X"}],
                "associated_diseases": [{"disease": "Cancer"}, {"disease": "colitis"}],
            }
        }
    }
    tier, reason = trait_liability_similarity(snap, adverse_vocab={"colitis"})
    assert tier == "match"
    assert "colitis" in reason
    tier2, _ = trait_liability_similarity(snap, adverse_vocab={"pancreatitis"})
    assert tier2 == "no_match"


# --------------------------------------------------------------------------- #
# Wiring into compute_readiness -- columns present + honest defaults            #
# --------------------------------------------------------------------------- #


def _minimal_card(gene: str, target_id: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "target": [gene],
            "condition": ["Rest"],
            "target_id": [target_id],
            "statistical_evidence_grade": [3],
            "pathway_axis": ["unassigned"],
            "replicate_pass_flag": [True],
            "crossdonor_correlation_mean": [0.4],
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


def test_new_columns_are_honest_unknown_without_overlays_or_evidence():
    """Omitting overlays/evidence entirely still emits every new column with the
    honest 'unknown' default -- never a missing column or a silent 0."""
    from readiness_engine import compute_readiness

    result = compute_readiness(
        _minimal_card("CD3E", ENSEMBL["CD3E"]), overlays=None, essentials=None, broad_effect_genes=None
    )
    row = result.iloc[0]
    assert row["genetic_support_confidence"] == "unknown"
    assert row["genetic_support_max_genetic_score"] == "unknown"
    assert row["composite_safety_liability"] == "unknown"
    assert row["trait_liability_similarity"] == "unknown"
    assert "adverse-event reference vocabulary" in row["trait_liability_similarity_reason"]


def test_compute_readiness_populates_new_columns_from_real_overlays_and_evidence():
    """With the real overlays + evidence_lookup wired, the new columns carry the
    real observed values (MED12 strong genetics + high composite liability)."""
    if not _has_evidence("MED12"):
        pytest.skip("MED12 evidence snapshot not present in this checkout")
    from evidence.external_cache import load_snapshot
    from readiness_engine import compute_readiness
    from safety_overlay import load_gnomad_constraint_overlay, load_gtex_safety_overlay

    result = compute_readiness(
        _minimal_card("MED12", ENSEMBL["MED12"]),
        overlays=None,
        essentials=None,
        broad_effect_genes=None,
        gnomad_overlay=load_gnomad_constraint_overlay(),
        gtex_overlay=load_gtex_safety_overlay(),
        evidence_lookup=lambda g: load_snapshot(EVIDENCE_DIR, g),
    )
    row = result.iloc[0]
    assert row["genetic_support_confidence"] == "strong_genetic_association"
    assert row["composite_safety_liability"] == "high"
    assert row["trait_liability_similarity"] == "unknown"


# --------------------------------------------------------------------------- #
# Load-bearing invariant -- new descriptive fields never move readiness_call    #
# --------------------------------------------------------------------------- #


def test_composite_liability_overlays_do_not_change_readiness_call(real_cards, real_data_available):
    """Adding the gnomAD + GTEx overlays populates composite_safety_liability but
    must not move readiness_call/overall_readiness_stage by even one row -- and
    every pre-existing domain column stays byte-identical too (only the new
    descriptive columns differ). Same causal-independence property as
    test_readiness_engine_gnomad_overlay_alone_does_not_change_readiness_call."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from readiness_engine import compute_readiness
    from safety_overlay import load_gnomad_constraint_overlay, load_gtex_safety_overlay

    baseline = compute_readiness(real_cards, overlays=None, essentials=None, broad_effect_genes=None)
    enriched = compute_readiness(
        real_cards,
        overlays=None,
        essentials=None,
        broad_effect_genes=None,
        gnomad_overlay=load_gnomad_constraint_overlay(),
        gtex_overlay=load_gtex_safety_overlay(),
    )
    assert len(baseline) == len(enriched)

    unchanged = [
        "biology_causality_score",
        "translation_score",
        "biomarker_score",
        "disease_relevance_score",
        "human_genetic_support",
        "genetic_support_confidence",  # unchanged: no evidence_lookup passed either way
        "overall_readiness_stage",
        "readiness_call",
    ]
    for col in unchanged:
        assert (baseline[col].astype(str) == enriched[col].astype(str)).all(), f"{col} must be unaffected"

    # Sanity-check the composite is actually wired and varies across real genes.
    assert set(enriched["composite_safety_liability"].unique()) & {"high", "moderate", "low"}


def test_genetic_support_confidence_column_is_not_read_by_stage():
    """Two runs whose ONLY difference is genetic_support_confidence (strong vs
    none) -- with human_genetic_support and every _stage() input held identical
    -- must produce identical readiness_call/overall_readiness_stage. This
    proves genetic_support_confidence is descriptive-only: _stage() reads
    human_genetic_support, never the new graded tier."""
    from readiness_engine import compute_readiness

    # Both snapshots resolve the gene in Open Targets (items present) so
    # human_genetic_support == 'yes' in BOTH; only the genetic_association_score
    # differs, so only genetic_support_confidence differs.
    strong = {
        "sources": {
            "open_targets": {
                "source_status": "ok",
                "items": [{"id": "X", "name": "X"}],
                "associated_diseases": [{"disease": "d", "genetic_association_score": 0.9}],
            }
        }
    }
    none = {
        "sources": {
            "open_targets": {
                "source_status": "ok",
                "items": [{"id": "X", "name": "X"}],
                "associated_diseases": [{"disease": "d", "genetic_association_score": 0.0}],
            }
        }
    }
    card = _minimal_card("CD3E", ENSEMBL["CD3E"])
    r_strong = compute_readiness(card, overlays=None, essentials=None, broad_effect_genes=None, evidence_lookup=lambda g: strong)
    r_none = compute_readiness(card, overlays=None, essentials=None, broad_effect_genes=None, evidence_lookup=lambda g: none)

    assert r_strong.iloc[0]["genetic_support_confidence"] == "strong_genetic_association"
    assert r_none.iloc[0]["genetic_support_confidence"] == "no_genetic_association"
    # human_genetic_support identical ('yes') -> readiness identical.
    assert r_strong.iloc[0]["human_genetic_support"] == r_none.iloc[0]["human_genetic_support"] == "yes"
    assert r_strong.iloc[0]["readiness_call"] == r_none.iloc[0]["readiness_call"]
    assert r_strong.iloc[0]["overall_readiness_stage"] == r_none.iloc[0]["overall_readiness_stage"]
