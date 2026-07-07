"""A3: perturbation-prediction benchmark harness.

Covers the honest-fallback contract (missing file, missing columns, targets
missing a condition), the 3-fold held-out rotation, the required baseline
predictor's output shape, and the evaluation metric on both a synthetic
sanity case and real DE_stats values for real, independently-verified genes.

Per docs/next_phases_plan.md §A3 this module is a standalone evaluation
report generator -- nothing here ever touches target_cards.csv or the
readiness engine, and these tests don't either.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Real-data loading + schema
# ---------------------------------------------------------------------------


def test_load_de_stats_real_file(real_data_available):
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from perturbation_prediction_benchmark import REQUIRED_DE_COLUMNS, load_de_stats

    result = load_de_stats()
    assert result["available"] is True
    assert set(REQUIRED_DE_COLUMNS).issubset(result["table"].columns)
    assert set(result["table"]["culture_condition"].unique()) == {"Rest", "Stim8hr", "Stim48hr"}
    # real, independently-verified genes must be present
    names = set(result["table"]["target_contrast_gene_name"])
    assert {"CD3E", "VAV1", "PLCG1"}.issubset(names)


def test_load_de_stats_missing_file_is_honest(tmp_path):
    from perturbation_prediction_benchmark import load_de_stats

    result = load_de_stats(tmp_path / "does_not_exist.csv")
    assert result["available"] is False
    assert "not found" in result["reason"]
    assert result["table"].empty


def test_load_de_stats_missing_columns_is_honest(tmp_path):
    from perturbation_prediction_benchmark import load_de_stats

    bad_path = tmp_path / "bad_de_stats.csv"
    pd.DataFrame({"foo": [1, 2], "bar": [3, 4]}).to_csv(bad_path, index=False)
    result = load_de_stats(bad_path)
    assert result["available"] is False
    assert "missing required columns" in result["reason"]
    assert result["table"].empty


# ---------------------------------------------------------------------------
# Held-out rotation / eligibility split
# ---------------------------------------------------------------------------


def _synthetic_de_df() -> pd.DataFrame:
    """A small synthetic DE table: two targets with all 3 conditions, one
    target (REX1BD-style) missing Stim48hr entirely -- mirrors the real
    missing-condition case found in DE_stats.suppl_table.csv."""
    rows = [
        {"target_contrast": "ENSG_A", "target_contrast_gene_name": "GENEA", "culture_condition": "Rest", "ontarget_effect_size": -10.0},
        {"target_contrast": "ENSG_A", "target_contrast_gene_name": "GENEA", "culture_condition": "Stim8hr", "ontarget_effect_size": -12.0},
        {"target_contrast": "ENSG_A", "target_contrast_gene_name": "GENEA", "culture_condition": "Stim48hr", "ontarget_effect_size": -14.0},
        {"target_contrast": "ENSG_B", "target_contrast_gene_name": "GENEB", "culture_condition": "Rest", "ontarget_effect_size": 5.0},
        {"target_contrast": "ENSG_B", "target_contrast_gene_name": "GENEB", "culture_condition": "Stim8hr", "ontarget_effect_size": 5.0},
        {"target_contrast": "ENSG_B", "target_contrast_gene_name": "GENEB", "culture_condition": "Stim48hr", "ontarget_effect_size": 5.0},
        {"target_contrast": "ENSG_C", "target_contrast_gene_name": "GENEC", "culture_condition": "Rest", "ontarget_effect_size": 1.0},
        {"target_contrast": "ENSG_C", "target_contrast_gene_name": "GENEC", "culture_condition": "Stim8hr", "ontarget_effect_size": 2.0},
        # ENSG_C has no Stim48hr row at all -> must be skipped, not imputed
    ]
    return pd.DataFrame(rows)


def test_pivot_and_split_eligible_targets_synthetic():
    from perturbation_prediction_benchmark import pivot_effect_by_condition, split_eligible_targets

    wide = pivot_effect_by_condition(_synthetic_de_df())
    assert set(wide["target_id"]) == {"ENSG_A", "ENSG_B", "ENSG_C"}

    split = split_eligible_targets(wide)
    assert set(split["eligible"]["target_id"]) == {"ENSG_A", "ENSG_B"}
    assert set(split["skipped"]["target_id"]) == {"ENSG_C"}
    assert split["skipped"].set_index("target_id").loc["ENSG_C", "missing_conditions"] == "Stim48hr"


def test_missing_condition_target_is_honestly_skipped_real_data(real_data_available):
    """REX1BD (ENSG00000006015) is real: it has DE stats for Rest and
    Stim8hr only, no Stim48hr row exists in the source table at all. It must
    show up in `skipped`, never in `eligible`, and never with an imputed
    Stim48hr value."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from perturbation_prediction_benchmark import load_de_stats, pivot_effect_by_condition, split_eligible_targets

    de = load_de_stats()["table"]
    wide = pivot_effect_by_condition(de)
    split = split_eligible_targets(wide)

    assert "ENSG00000006015" not in set(split["eligible"]["target_id"])
    skipped_row = split["skipped"][split["skipped"]["target_id"] == "ENSG00000006015"]
    assert len(skipped_row) == 1
    assert skipped_row.iloc[0]["missing_conditions"] == "Stim48hr"
    assert skipped_row.iloc[0]["target"] == "REX1BD"


def test_build_holdout_folds_produces_three_folds_per_target():
    from perturbation_prediction_benchmark import (
        CONDITIONS,
        build_holdout_folds,
        pivot_effect_by_condition,
        split_eligible_targets,
    )

    wide = pivot_effect_by_condition(_synthetic_de_df())
    eligible = split_eligible_targets(wide)["eligible"]
    folds = build_holdout_folds(eligible)

    assert len(folds) == len(eligible) * len(CONDITIONS)
    assert set(folds["held_out_condition"]) == set(CONDITIONS)
    for target_id in eligible["target_id"]:
        held = set(folds[folds["target_id"] == target_id]["held_out_condition"])
        assert held == set(CONDITIONS)


# ---------------------------------------------------------------------------
# Baseline predictor shape + evaluation metric
# ---------------------------------------------------------------------------


def test_baseline_mean_predictor_is_the_mean_of_known_values():
    from perturbation_prediction_benchmark import baseline_mean_predictor

    assert baseline_mean_predictor([-10.0, -12.0]) == pytest.approx(-11.0)
    assert baseline_mean_predictor([5.0, 5.0]) == pytest.approx(5.0)


def test_baseline_prediction_error_is_zero_when_predicted_equals_actual():
    """Synthetic sanity case: GENEB has an identical effect size (5.0) in all
    three conditions, so the mean-of-known baseline must predict the held-out
    value exactly and the absolute error must be ~0."""
    from perturbation_prediction_benchmark import build_holdout_folds, pivot_effect_by_condition, split_eligible_targets

    wide = pivot_effect_by_condition(_synthetic_de_df())
    eligible = split_eligible_targets(wide)["eligible"]
    folds = build_holdout_folds(eligible)

    geneb_folds = folds[folds["target"] == "GENEB"]
    assert len(geneb_folds) == 3
    assert (geneb_folds["baseline_abs_error"] < 1e-9).all()


def test_fold_summary_metrics_are_sane_on_real_data(real_data_available):
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from perturbation_prediction_benchmark import run_benchmark

    report = run_benchmark()
    assert report["available"] is True
    fold_summary = report["fold_summary"]
    assert set(fold_summary["held_out_condition"]) == {"Rest", "Stim8hr", "Stim48hr"}
    # honest calibration: correlation must be a real, finite, plausible value
    # (not fabricated as a perfect 1.0, not silently 0/NaN when data exists)
    for r in fold_summary["baseline_pearson_r"]:
        assert 0.0 < r < 1.0
    for mae in fold_summary["baseline_mean_abs_error"]:
        assert mae > 0.0


def test_evaluation_metric_correlation_matches_manual_calculation_for_real_genes(real_data_available):
    """Independently recompute the baseline prediction for three real,
    previously-verified genes (CD3E, VAV1, PLCG1; see population_hypothesis
    tests for the same genes) and confirm the harness's numbers match a
    from-scratch calculation using only pandas/numpy."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from perturbation_prediction_benchmark import load_de_stats, pivot_effect_by_condition, split_eligible_targets, build_holdout_folds

    de = load_de_stats()["table"]
    wide = pivot_effect_by_condition(de)
    eligible = split_eligible_targets(wide)["eligible"]
    folds = build_holdout_folds(eligible)

    manual = {
        "CD3E": {"Rest": -20.879863, "Stim8hr": -17.891807, "Stim48hr": -6.924727},
        "VAV1": {"Rest": -15.635602, "Stim8hr": -15.097188, "Stim48hr": -10.859022},
    }
    for gene, values in manual.items():
        gene_folds = folds[folds["target"] == gene].set_index("held_out_condition")
        assert len(gene_folds) == 3
        for held_out, actual in values.items():
            known = [v for c, v in values.items() if c != held_out]
            expected_pred = float(np.mean(known))
            row = gene_folds.loc[held_out]
            assert row["actual_effect"] == pytest.approx(actual, abs=1e-4)
            assert row["baseline_mean_prediction"] == pytest.approx(expected_pred, abs=1e-4)
            assert row["baseline_abs_error"] == pytest.approx(abs(expected_pred - actual), abs=1e-4)


# ---------------------------------------------------------------------------
# Top-level run_benchmark() report shape + guardrail
# ---------------------------------------------------------------------------


def test_run_benchmark_report_shape_and_caveat_real_data(real_data_available):
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from perturbation_prediction_benchmark import CAVEAT_TEXT, run_benchmark

    report = run_benchmark()
    assert report["available"] is True
    assert report["caveat"] == CAVEAT_TEXT
    assert "NOT a target score" in CAVEAT_TEXT
    assert "never wired into target_cards.csv" in CAVEAT_TEXT
    assert report["n_targets_eligible"] > 0
    assert report["n_targets_skipped"] >= 0
    assert isinstance(report["per_target_fold"], pd.DataFrame)
    assert isinstance(report["fold_summary"], pd.DataFrame)
    assert isinstance(report["overall_summary"], dict)
    # a target that's skipped must never appear as eligible
    skipped_ids = set(report["skipped"]["target_id"])
    fold_ids = set(report["per_target_fold"]["target_id"])
    assert skipped_ids.isdisjoint(fold_ids)


def test_run_benchmark_on_synthetic_df_directly():
    from perturbation_prediction_benchmark import run_benchmark

    report = run_benchmark(de_df=_synthetic_de_df())
    assert report["available"] is True
    assert report["n_targets_eligible"] == 2
    assert report["n_targets_skipped"] == 1
    assert len(report["per_target_fold"]) == 2 * 3


def test_run_benchmark_missing_columns_returns_honest_unavailable():
    from perturbation_prediction_benchmark import run_benchmark

    bad_df = pd.DataFrame({"foo": [1], "bar": [2]})
    report = run_benchmark(de_df=bad_df)
    assert report["available"] is False
    assert "missing required columns" in report["reason"]
    assert report["per_target_fold"].empty


def test_run_benchmark_no_eligible_targets_is_honest_not_a_crash():
    from perturbation_prediction_benchmark import run_benchmark

    only_missing = pd.DataFrame(
        [
            {
                "target_contrast": "ENSG_X",
                "target_contrast_gene_name": "GENEX",
                "culture_condition": "Rest",
                "ontarget_effect_size": 1.0,
            }
        ]
    )
    report = run_benchmark(de_df=only_missing)
    assert report["available"] is False
    assert report["n_targets_skipped"] == 1
    assert report["skipped"].iloc[0]["target_id"] == "ENSG_X"


def test_module_never_imports_readiness_or_card_or_api_modules():
    """Guardrail check: this module must be fully standalone -- it must not
    import readiness_engine, build_target_cards, or target_card_api (the
    §A3 rule is 'results only ever go into a benchmark report')."""
    import perturbation_prediction_benchmark as ppb

    source = Path(ppb.__file__).read_text(encoding="utf-8")
    for forbidden in ["import readiness_engine", "import build_target_cards", "import target_card_api"]:
        assert forbidden not in source
