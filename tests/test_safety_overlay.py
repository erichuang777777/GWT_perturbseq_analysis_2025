"""Membrane/tractability + safety-window overlays (§1.12 / ADC ingestion spec).

Regression-pins the real, checked-in ADC-derived membrane overlay
(docs/mvp-research/adc_overlay_gwt_overlap_full.csv) and the real GTEx
per-tissue expression overlay
(sources/target_tool_cache/_overlays/gtex_per_tissue.parquet) -- both are now
present in this checkout, so both halves of §1.12 are covered with live data,
not honest-fallback placeholders.

Also covers the gnomAD LOEUF/pLI constraint overlay (§C of
docs/next_phases_plan.md): now an authentic full-genome gnomAD v2.1.1 by-gene
snapshot (sources/target_tool_cache/_overlays/gnomad_constraint_seed.csv,
~19k genes, one row per gene, chrX included), built by
src/3_DE_analysis/data_acquisition/build_gnomad_constraint_overlay.py -- it
replaced the earlier 15-gene demo shortlist derived from
docs/mvp-research/connector_enrichment_demo.csv.
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


def test_readiness_engine_essential_gene_still_gets_real_gtex_safety_window_score(real_data_available):
    """Regression pin for a confirmed bug: safety_window_score used to
    hard-code 0 for any essential gene, discarding real GTEx off-context
    data and showing the *safest-looking* value (0 on this metric's own
    higher-is-riskier scale) for exactly the gene class that most needs
    honest reporting. Essentiality is already fully handled by the separate
    essential_gene red-flag/watchlist cap below -- safety_window_score must
    report the real overlay value (or honest "unknown") unconditionally,
    per this repo's unknown != 0 invariant."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from readiness_engine import compute_readiness
    from safety_overlay import load_gtex_safety_overlay

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
    gtex = load_gtex_safety_overlay()
    result = compute_readiness(cards, overlays=None, essentials={"CD3E"}, broad_effect_genes=None, gtex_overlay=gtex)
    row = result.iloc[0]

    # The real, non-fabricated GTEx value for CD3E (21/30 off-context tissues)
    # must flow through even though CD3E is marked essential here.
    assert row["safety_window_score"] == 21
    # Essentiality is still fully enforced -- just via the dedicated red-flag
    # mechanism, not by corrupting safety_window_score.
    assert "essential_gene" in row["red_flag_override"]
    assert row["readiness_call"] in ("watchlist", "deprioritize")


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


# --- gnomAD LOEUF/pLI constraint overlay (§C of docs/next_phases_plan.md) ---


def test_load_gnomad_constraint_overlay_real_seed_file():
    """The overlay (now the full-genome gnomAD v2.1.1 by-gene LOEUF/pLI
    snapshot, expanded from the earlier 15-gene demo shortlist to the whole
    genome) loads with the whole-genome gene count and the exact required
    columns."""
    from safety_overlay import load_gnomad_constraint_overlay

    result = load_gnomad_constraint_overlay()
    assert result["available"] is True
    table = result["table"]
    # full-genome gnomAD v2.1.1 by-gene snapshot (~19k genes, one row per gene)
    assert len(table) == 19155
    assert set(["ensembl_id", "gene_symbol", "loeuf", "pli"]).issubset(table.columns)


def test_gnomad_constraint_seed_is_valid_and_pins_known_v211_values():
    """Validates the overlay directly (now an authentic full-genome gnomAD
    v2.1.1 by-gene snapshot, no longer the demo shortlist derived from
    connector_enrichment_demo.csv): valid schema, no nulls, no duplicate ids,
    values in the metrics' real ranges, and a regression pin on known genes'
    real v2.1.1 values so a future rebuild can't silently drift. Includes
    FOXP3 (chrX) to guard against an autosomes-only source silently dropping
    the master Treg regulator."""
    from safety_overlay import load_gnomad_constraint_overlay

    seed = load_gnomad_constraint_overlay()["table"]
    # schema + integrity
    assert not seed["ensembl_id"].duplicated().any()
    assert not seed[["ensembl_id", "gene_symbol", "loeuf", "pli"]].isna().any().any()
    # LOEUF is a non-negative observed/expected ratio; pLI is a probability in [0, 1]
    assert (seed["loeuf"].astype(float) >= 0).all()
    assert ((seed["pli"].astype(float) >= 0) & (seed["pli"].astype(float) <= 1)).all()
    # regression pins on real gnomAD v2.1.1 oe_lof_upper (LOEUF) values
    by_gene = seed.set_index("gene_symbol")
    assert by_gene.loc["CD3E", "loeuf"] == pytest.approx(0.923)
    assert by_gene.loc["VAV1", "loeuf"] == pytest.approx(0.226)
    assert by_gene.loc["MED12", "loeuf"] == pytest.approx(0.071)   # chrX, constrained
    assert by_gene.loc["FOXP3", "loeuf"] == pytest.approx(0.195)   # chrX, must not be dropped


def test_load_gnomad_constraint_overlay_missing_file_is_honest(tmp_path):
    from safety_overlay import load_gnomad_constraint_overlay

    result = load_gnomad_constraint_overlay(path=tmp_path / "does_not_exist.csv")
    assert result["available"] is False
    assert result["table"].empty


def test_gnomad_flag_from_constraint_vav1_is_loss_intolerant():
    """VAV1: LOEUF 0.226 < 0.6 threshold -> loss_intolerant."""
    from safety_overlay import gnomad_flag_from_constraint, load_gnomad_constraint_overlay

    overlay = load_gnomad_constraint_overlay()
    assert gnomad_flag_from_constraint("ENSG00000141968", overlay) == "loss_intolerant"  # VAV1


def test_gnomad_flag_from_constraint_cd3e_is_none():
    """CD3E: LOEUF 0.923 >= 0.6 threshold -> present but not flagged ('none')."""
    from safety_overlay import gnomad_flag_from_constraint, load_gnomad_constraint_overlay

    overlay = load_gnomad_constraint_overlay()
    assert gnomad_flag_from_constraint("ENSG00000198851", overlay) == "none"  # CD3E


def test_gnomad_flag_from_constraint_absent_gene_is_unknown():
    """A gene absent from the seed is unchecked, not 'safe' -- unknown, never 0/'none'."""
    from safety_overlay import UNKNOWN, gnomad_flag_from_constraint, load_gnomad_constraint_overlay

    overlay = load_gnomad_constraint_overlay()
    # a synthetic Ensembl id present in no gnomAD release -> genuinely unchecked
    assert gnomad_flag_from_constraint("ENSG00000000000", overlay) == UNKNOWN


def test_gnomad_flag_from_constraint_unavailable_overlay_is_unknown():
    from safety_overlay import UNKNOWN, gnomad_flag_from_constraint

    unavailable = {"available": False, "reason": "x", "table": pd.DataFrame()}
    assert gnomad_flag_from_constraint("ENSG00000141968", unavailable) == UNKNOWN


def test_readiness_engine_gnomad_overlay_alone_does_not_change_readiness_call(real_cards, real_data_available):
    """Passing gnomad_overlay must not move readiness_call/overall_readiness_stage
    by even one row -- it is a purely descriptive, causally-independent signal
    (same property as safety_window_score/gtex_overlay). Every other domain
    stays untouched too; only the new gnomad_* columns differ."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from readiness_engine import compute_readiness
    from safety_overlay import load_gnomad_constraint_overlay

    baseline = compute_readiness(real_cards, overlays=None, essentials=None, broad_effect_genes=None)
    gnomad = load_gnomad_constraint_overlay()
    gnomad_only = compute_readiness(
        real_cards, overlays=None, essentials=None, broad_effect_genes=None, gnomad_overlay=gnomad
    )
    assert len(baseline) == len(gnomad_only)

    shared_cols = [
        "biology_causality_score",
        "translation_score",
        "biomarker_score",
        "disease_relevance_score",
        "human_genetic_support",
        "tractability_modality",
        "tractability_score",
        "safety_window_score",
        "overall_readiness_stage",
        "readiness_call",
    ]
    for col in shared_cols:
        assert (baseline[col].astype(str) == gnomad_only[col].astype(str)).all(), f"{col} must be unaffected by gnomad_overlay"

    # Sanity-check the overlay is actually wired up: VAV1 is a real target in
    # this dataset and should pick up the loss_intolerant flag + passthrough values.
    vav1_rows = gnomad_only[gnomad_only["target"] == "VAV1"]
    if not vav1_rows.empty:
        vav1 = vav1_rows.iloc[0]
        assert vav1["gnomad_constraint_flag"] == "loss_intolerant"
        assert vav1["gnomad_loeuf"] == pytest.approx(0.226)   # gnomAD v2.1.1
        assert vav1["gnomad_pli"] == pytest.approx(0.9999)


def test_readiness_engine_without_gnomad_overlay_columns_are_unknown_regression():
    """Omitting gnomad_overlay entirely still populates the new columns with
    the honest 'unknown' default -- never a silent 0 or missing column."""
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
    assert result.iloc[0]["gnomad_constraint_flag"] == "unknown"
    assert result.iloc[0]["gnomad_loeuf"] == "unknown"
    assert result.iloc[0]["gnomad_pli"] == "unknown"
