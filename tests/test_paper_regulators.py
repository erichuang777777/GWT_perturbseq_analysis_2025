"""Surfacing the paper's own regulator nominations — known-answer + unknown!=0."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "3_DE_analysis"
sys.path.insert(0, str(SRC))

import paper_regulators as pr  # noqa: E402

_HAVE_TABLES = pr.POLARIZATION_CSV.exists() or pr.AGING_CSV.exists()


@pytest.mark.skipif(not _HAVE_TABLES, reason="paper regulator-coefficient tables not present")
def test_gata3_is_top_ranked_known_polarization_regulator():
    res = pr.regulators_for_target("GATA3")
    assert res["available"] is True
    assert res["n_nominations"] > 0
    pol = [n for n in res["nominations"] if n["axis"] == "polarization"]
    assert pol, "GATA3 should be nominated in the polarization model"
    # the paper ranks GATA3 at the very top of polarization regulators, and calls it known
    best = max(pol, key=lambda n: n["coef_rank"])
    assert best["coef_rank"] > 0.99
    assert best["known_regulator"] is True


@pytest.mark.skipif(not _HAVE_TABLES, reason="paper regulator-coefficient tables not present")
def test_novel_nomination_flag_is_surfaced():
    # BCL6 is a high-rank polarization nomination the paper labels NOT previously-known
    res = pr.regulators_for_target("BCL6")
    pol = [n for n in res["nominations"] if n["axis"] == "polarization"]
    assert pol
    assert any(n["known_regulator"] is False for n in pol)
    assert res["nominated_novel"] is True


@pytest.mark.skipif(not _HAVE_TABLES, reason="paper regulator-coefficient tables not present")
def test_unknown_gene_is_absent_not_zero():
    res = pr.regulators_for_target("NOT_A_REAL_GENE_XYZ")
    assert res["available"] is True
    assert res["nominations"] == []            # absence, never a fabricated 0-coefficient row
    assert res["max_coef_rank"] is None
    assert res["is_known_regulator"] is None


@pytest.mark.skipif(not _HAVE_TABLES, reason="paper regulator-coefficient tables not present")
def test_nominations_are_verbatim_and_carry_context():
    res = pr.regulators_for_target("GATA3")
    n = res["nominations"][0]
    # every nomination keeps the paper's own axis / signature / context / known flag
    assert n["axis"] in {"polarization", "aging"}
    assert "context" in n and "signature" in n
    assert "known_regulator" in n
    # coef_rank is a 0-1 percentile
    assert n["coef_rank"] is None or 0.0 <= n["coef_rank"] <= 1.0
