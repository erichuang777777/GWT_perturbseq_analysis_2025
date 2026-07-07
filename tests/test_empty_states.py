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


def test_guideless_upload_is_not_assessed_not_fabricated_not_measurable():
    """A guide-less generic upload has NaN baseline expression (there was never
    an NTC/guide table to measure it from). kd_status must be 'not_assessed'
    (genuinely unknown), NOT 'not_measurable' (which fabricates an 'NTC
    expression too low' claim about an upload that had no NTC cells). This is
    the unknown != 0 rule (docs/data_governance_checklist.md §3).
    """
    from build_target_cards import adapt_generic_de, build_cards_frame
    from readiness_engine import compute_readiness

    up = pd.DataFrame({
        "target": ["MYGENE1", "MYGENE2"],
        "condition": ["Rest", "Rest"],
        "effect_size": [-2.0, -1.5],
        "fdr": [0.001, 0.02],
        "n_cells": [500, 400],
        "n_total_de_genes": [120, 80],
    })
    cards = build_cards_frame(adapt_generic_de(up), guide_df=None, lib_map=None, benchmark=None, schema="generic", sample_meta=None)
    assert set(cards["kd_status"]) == {"not_assessed"}
    assert not cards["score_cap_reason"].str.contains("kd_not_measurable").any()

    readiness = compute_readiness(cards, overlays=None, essentials=None, broad_effect_genes=None)
    # No fabricated red flag, and none of the "NTC expression too low" next-step text.
    assert not readiness["red_flag_override"].str.contains("kd_not_measurable").any()
    assert not readiness["next_validation_step"].str.contains("NTC").any()


def test_mapped_upload_preserves_n_total_de_genes():
    """n_total_de_genes must survive the column-mapping wizard: it is canonical
    (adapt_generic_de reads it and grading/calibration gate on it), so
    build_mapped_view must not drop it. Regression for the mapped-upload
    degeneration bug where every mapped card got n_total_de_genes=NaN.
    """
    from build_target_cards import adapt_generic_de
    from import_manager import build_mapped_view, canonical_fields, suggested_mapping

    fields = canonical_fields("target_evidence")
    assert "n_total_de_genes" in (fields["required"] + fields["recommended"])

    raw = pd.DataFrame({
        "gene": ["MYGENE1"], "culture_condition": ["Rest"],
        "log2fc": [-2.0], "padj": [0.001], "n_cells": [500],
        "num_de_genes": [120],  # non-canonical name -> alias -> n_total_de_genes
    })
    mapping = suggested_mapping("target_evidence", list(raw.columns))
    assert mapping.get("n_total_de_genes") == "num_de_genes"
    view = build_mapped_view(raw, mapping)
    assert "n_total_de_genes" in view.columns
    adapted = adapt_generic_de(view)
    assert adapted["n_total_de_genes"].iloc[0] == 120


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
