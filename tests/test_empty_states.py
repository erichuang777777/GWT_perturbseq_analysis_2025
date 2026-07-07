"""Empty/edge-state tests: the four result_status states for any gene query,
and every empty-input path (empty dataset, unmatched query, missing overlay)
must degrade to an explicit, documented state -- never raise, never silently
return 0/empty where "unknown" is the honest answer.
"""
from __future__ import annotations

import pandas as pd
import pytest


# --- B2: four-state result_status ------------------------------------------------

def test_result_status_not_in_library_for_unknown_query(golden_resolver, golden_de_stats):
    from gene_identifier_resolver import result_status

    result = result_status(golden_resolver, "TOTALLY_MADE_UP_GENE_XYZ", golden_de_stats, target_col="target_contrast_gene_name")
    assert result["result_status"] == "not_in_library"
    assert result["matched"] is False


def test_result_status_not_expressed_below_kd_floor(golden_resolver, golden_de_stats):
    from gene_identifier_resolver import result_status

    result = result_status(golden_resolver, "LOWEXPR1", golden_de_stats, target_col="target_contrast_gene_name")
    assert result["result_status"] == "not_expressed"
    assert result["matched"] is True


def test_result_status_no_significant_effect_when_expressed_but_not_significant(golden_resolver, golden_de_stats):
    from gene_identifier_resolver import result_status

    result = result_status(golden_resolver, "NOEFFECT1", golden_de_stats, target_col="target_contrast_gene_name")
    assert result["result_status"] == "no_significant_effect"


def test_result_status_has_effect_for_positive_control(golden_resolver, golden_de_stats):
    from gene_identifier_resolver import result_status

    result = result_status(golden_resolver, "ZAP70", golden_de_stats, target_col="target_contrast_gene_name")
    assert result["result_status"] == "has_effect"
    assert result["n_condition_rows"] == 2


def test_resolver_never_raises_on_empty_or_none_query(golden_resolver):
    for bad_query in ("", "   ", None):
        result = golden_resolver.resolve(bad_query)
        assert result["matched"] is False


def test_resolver_alias_resolution_uses_real_sgrna_vs_curated_symbol_pattern(golden_resolver):
    result = golden_resolver.resolve("OLDALIAS1")
    assert result["matched"] is True
    assert result["resolution_path"] == "exact_alias_symbol"
    assert result["canonical_symbol"] == "ALIASGENE1"


# --- empty-dataset paths -----------------------------------------------------------

def test_build_cards_frame_on_empty_de_table_does_not_raise():
    from build_target_cards import build_cards_frame

    empty_de = pd.DataFrame(
        columns=[
            "target_contrast_gene_name", "culture_condition", "target_contrast",
            "n_cells_target", "n_up_genes", "n_down_genes", "n_total_de_genes",
            "ontarget_effect_size", "ontarget_significant", "offtarget_flag",
            "crossdonor_correlation_mean", "crossdonor_correlation_min", "crossguide_correlation",
        ]
    )
    cards = build_cards_frame(empty_de, None, lib_map=None, benchmark=None, sample_meta=None)
    assert len(cards) == 0
    assert "statistical_evidence_grade" in cards.columns


def test_readiness_summary_empty_branch_matches_populated_key_set(golden_cards):
    from readiness_engine import compute_readiness, readiness_summary

    populated = compute_readiness(golden_cards, overlays=None, essentials=None, broad_effect_genes=None)
    empty = compute_readiness(pd.DataFrame(), overlays=None, essentials=None, broad_effect_genes=None)

    populated_summary = readiness_summary(populated)
    empty_summary = readiness_summary(empty)
    assert set(populated_summary.keys()) == set(empty_summary.keys())
    assert empty_summary["rows"] == 0


def test_control_panel_calibration_on_dataset_without_kd_status_column_is_explicit():
    from calibration import control_panel_calibration

    cards = pd.DataFrame({"target": ["ZAP70"], "statistical_evidence_grade": [4]})
    result = control_panel_calibration(cards)
    assert result["negative_controls"] == {"available": False, "reason": "no kd_status column in cards"}


def test_control_panel_calibration_on_dataset_missing_required_columns_reports_unavailable():
    from calibration import control_panel_calibration

    result = control_panel_calibration(pd.DataFrame({"foo": [1, 2, 3]}))
    assert result == {"available": False}


def test_cre_schema_reports_honest_not_loaded_when_no_file_present(tmp_path):
    from cre_schema import load_cre_elements

    result = load_cre_elements(path=tmp_path / "does_not_exist.csv")
    assert result["available"] is False
    assert "elements" in result


def test_gene_search_empty_query_returns_no_results(golden_resolver):
    from gene_search import search_genes

    assert search_genes(golden_resolver, "") == []
    assert search_genes(golden_resolver, "   ") == []


def test_gene_search_garbage_query_returns_no_results_not_everything(golden_resolver):
    from gene_search import search_genes

    results = search_genes(golden_resolver, "###!!!ZZZZQQQQ###")
    assert results == []
