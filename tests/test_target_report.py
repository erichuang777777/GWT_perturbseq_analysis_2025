"""Tests for the self-contained single-target HTML report (plan P2-D)."""

from __future__ import annotations

import pandas as pd

from report.generate import build_target_report_payload, render_target_html

CARDS = pd.DataFrame({
    "target": ["ZAP70", "ZAP70", "MED12"],
    "condition": ["Rest", "Stim8hr", "Rest"],
    "statistical_evidence_grade": [4, 3, 2],
    "n_cells_target": [500, 400, 300],
    "n_guides": [4, 4, 2],
    "n_total_de_genes": [120, 80, 60],
    "ontarget_effect_size": [2.1, 1.8, 0.5],
    "fdr_min": [1e-9, 1e-6, 0.01],
    "crossdonor_correlation_mean": [0.8, 0.7, 0.3],
    "crossguide_correlation": [0.7, 0.6, 0.2],
    "kd_status": ["confirmed", "confirmed", "weak"],
    "score_cap_reason": ["none", "none", "single_guide"],
    "target_id": ["ENSG1", "ENSG1", "ENSG2"],
    "pathway_axis": ["TCR_core", "TCR_core", "Mediator"],
})


def test_payload_picks_best_grade_primary_row():
    p = build_target_report_payload(CARDS, "zap70", dataset_id="t")
    assert p["target"] == "ZAP70"
    assert p["primary_condition"] == "Rest"       # grade 4 row wins
    assert len(p["conditions"]) == 2               # both ZAP70 rows, MED12 excluded


def test_missing_gene_returns_none():
    assert build_target_report_payload(CARDS, "NOTAGENE", dataset_id="t") is None


def test_html_is_self_contained_and_carries_extras():
    extras = {
        "hypothesis": {"available": True, "hypothesis": "Knocking down ZAP70 predicted to down-regulate the TCR program.", "suggested_validation": "replicate in a second donor"},
        "novelty": {"tier": "well_studied", "total_count": 530, "novelty_score": 0.27},
        "trans_effect_breadth": {"measured": True, "trans_effect_breadth": 5381, "breadth_percentile": 0.999, "broad_effect_candidate": True},
        "known_drugs": {"known_drug_count": 3, "max_clinical_phase": 4, "any_approved": True, "drugs": [{"name": "DrugX"}]},
    }
    html = render_target_html(build_target_report_payload(CARDS, "ZAP70", dataset_id="t", extras=extras))
    assert html.lower().startswith("<!doctype html>")
    for must in ("ZAP70", "Testable hypothesis", "PubMed novelty", "Trans-effect breadth", "Known drugs", "not clinical software"):
        assert must in html
    # fully self-contained: no external hosts, scripts, or asset references
    assert "http://" not in html and "https://" not in html
    assert "src=" not in html and "<script" not in html


def test_html_omits_absent_extras_no_fabrication():
    # No extras at all -> no descriptive-signals section, and no fabricated values.
    html = render_target_html(build_target_report_payload(CARDS, "ZAP70", dataset_id="t"))
    assert "Descriptive signals" not in html
    assert "PubMed novelty" not in html
