"""Module 3 part A: population subgroup hypothesis engine.

Regression-pins the real UK Biobank LoF-burden values used to design this
module (see docs/mvp-research/MODULE3_病人層假設引擎_DEMO設計.md), and covers
the honest-fallback contract (missing file, unknown trait, empty input).
"""
from __future__ import annotations

import pandas as pd
import pytest


def test_load_burden_estimates_real_file(real_data_available):
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from population_hypothesis import load_burden_estimates

    result = load_burden_estimates("lymphocyte_count")
    assert result["available"] is True
    assert len(result["estimates"]) == 18543
    assert set(["ensg", "post_mean", "lower_95", "upper_95"]).issubset(result["estimates"].columns)


def test_load_burden_estimates_unknown_trait_is_honest():
    from population_hypothesis import load_burden_estimates

    result = load_burden_estimates("not_a_real_trait")
    assert result["available"] is False
    assert "not_a_real_trait" in result["reason"]
    assert result["estimates"].empty


def test_load_burden_estimates_missing_file_is_honest(tmp_path):
    from population_hypothesis import load_burden_estimates

    result = load_burden_estimates("lymphocyte_count", path=tmp_path / "does_not_exist.tsv")
    assert result["available"] is False
    assert result["estimates"].empty


def test_population_hypothesis_card_matches_real_demo_values(real_cards, real_data_available):
    """Regression-pins the exact real values independently verified during
    development: PLCG1/VAV1/SENP5 all show a significant (CI-excludes-zero)
    higher-lymphocyte-count effect in LoF-burden carriers.
    """
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from population_hypothesis import build_population_hypothesis_card, load_burden_estimates

    burden = load_burden_estimates("lymphocyte_count")
    result = build_population_hypothesis_card(real_cards, burden["estimates"])
    by_gene = result.drop_duplicates("target").set_index("target")

    plcg1 = by_gene.loc["PLCG1"]
    assert plcg1["population_effect_estimate"] == pytest.approx(0.2947, abs=1e-3)
    assert plcg1["ci_excludes_zero"] == True  # noqa: E712
    assert plcg1["direction"] == "higher"

    vav1 = by_gene.loc["VAV1"]
    assert vav1["population_effect_estimate"] == pytest.approx(0.0704, abs=1e-3)
    assert vav1["ci_excludes_zero"] == True  # noqa: E712

    senp5 = by_gene.loc["SENP5"]
    assert senp5["population_effect_estimate"] == pytest.approx(0.0939, abs=1e-3)
    assert senp5["ci_excludes_zero"] == True  # noqa: E712


def test_population_hypothesis_card_always_carries_the_guardrail_caveat(real_cards, real_data_available):
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from population_hypothesis import CAVEAT_TEXT, build_population_hypothesis_card, load_burden_estimates

    burden = load_burden_estimates("lymphocyte_count")
    result = build_population_hypothesis_card(real_cards, burden["estimates"])
    assert (result["caveat"] == CAVEAT_TEXT).all()
    assert "not a patient-level prediction" in CAVEAT_TEXT


def test_population_hypothesis_card_on_empty_input_is_empty_not_crash():
    from population_hypothesis import build_population_hypothesis_card

    empty_cards = pd.DataFrame(columns=["target", "target_id"])
    empty_burden = pd.DataFrame(columns=["ensg", "post_mean", "lower_95", "upper_95"])
    result = build_population_hypothesis_card(empty_cards, empty_burden)
    assert result.empty
    assert "caveat" in result.columns


def test_ci_excludes_zero_is_computed_correctly_at_boundary():
    """A CI that touches zero exactly must count as NOT excluding zero (a
    boundary case the >= / <= comparisons must get right)."""
    from population_hypothesis import build_population_hypothesis_card

    cards = pd.DataFrame({"target": ["G1", "G2"], "target_id": ["ENSG1", "ENSG2"]})
    burden = pd.DataFrame(
        {
            "ensg": ["ENSG1", "ENSG2"],
            "post_mean": [0.1, -0.1],
            "lower_95": [0.0, -0.2],  # touches zero exactly -> does NOT exclude zero
            "upper_95": [0.2, 0.0],
        }
    )
    result = build_population_hypothesis_card(cards, burden).set_index("target")
    assert result.loc["G1", "ci_excludes_zero"] == False  # noqa: E712
    assert result.loc["G2", "ci_excludes_zero"] == False  # noqa: E712


def test_no_gene_absent_from_burden_table_gets_a_fabricated_row(real_cards, real_data_available):
    """Inner join: a target with no burden estimate must simply be absent
    from the output, never filled with an invented value."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from population_hypothesis import build_population_hypothesis_card, load_burden_estimates

    burden = load_burden_estimates("lymphocyte_count")
    result = build_population_hypothesis_card(real_cards, burden["estimates"])
    result_ids = set(result["target_id"])
    burden_ids = set(burden["estimates"]["ensg"])
    assert result_ids.issubset(burden_ids)
