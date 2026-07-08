"""Tests for evidence/lincs_reference_cache.py -- the committed LINCS knockdown
reference signatures (Task F) and the honest wiring of what actually landed.

The repo committed genetic-perturbation (shRNA knockdown) L1000 signatures from
GSE106127 for the 4 shortlist genes that had LINCS coverage (PLCG1, SENP5, CCNC,
PMVK) -- NOT compound signatures. These tests pin that reality: the covered
genes load real 978-landmark vectors, uncovered genes degrade honestly, the
Spearman connectivity self-scores to 1.0, and low overlap is NaN (never 0).
"""
from __future__ import annotations

import pandas as pd
import pytest

from evidence.lincs_reference_cache import (
    COVERED_GENES,
    knockdown_reference,
    lincs_connectivity_score,
    load_coverage,
    load_demo_signatures,
)


def test_load_demo_signatures_real_file():
    """The committed 4-gene demo file loads: 978 L1000 landmark genes x the 4
    covered shortlist genes, real z-scores."""
    result = load_demo_signatures()
    assert result["available"] is True
    table = result["table"]
    assert table.shape == (978, 4)
    assert set(table.columns) == set(COVERED_GENES)
    # real z-scores, not a fabricated constant column
    assert table["PLCG1"].std() > 0


def test_load_demo_signatures_missing_file_is_honest(tmp_path):
    result = load_demo_signatures(path=tmp_path / "nope.csv")
    assert result["available"] is False
    assert result["table"].empty


def test_knockdown_reference_covered_gene_returns_real_vector():
    kd = knockdown_reference("PLCG1")
    assert kd["available"] is True
    assert kd["gene"] == "PLCG1"
    assert isinstance(kd["signature"], pd.Series)
    assert len(kd["signature"]) == 978
    assert kd["caveat"]  # forced non-empty caveat


def test_knockdown_reference_uncovered_gene_is_honest_unavailable():
    """CD3E is a shortlist gene but has ZERO committed LINCS signatures --
    must return unavailable, never a fabricated vector (unknown != 0)."""
    kd = knockdown_reference("CD3E")
    assert kd["available"] is False
    assert kd["signature"] is None
    assert "no committed LINCS" in kd["reason"]
    assert kd["caveat"]


def test_knockdown_reference_is_case_insensitive():
    assert knockdown_reference("plcg1")["available"] is True


def test_lincs_connectivity_self_score_is_one():
    """A signature is perfectly rank-concordant with itself -> +1.0."""
    kd = knockdown_reference("PLCG1")["signature"]
    assert lincs_connectivity_score(kd, kd) == pytest.approx(1.0)


def test_lincs_connectivity_reverse_is_negative_one():
    kd = knockdown_reference("SENP5")["signature"]
    assert lincs_connectivity_score(kd, -kd) == pytest.approx(-1.0)


def test_lincs_connectivity_low_overlap_is_nan_not_zero():
    """Fewer than 20 shared landmark genes -> honest NaN, never a fake 0."""
    import numpy as np

    a = pd.Series({"G1": 1.0, "G2": 2.0, "G3": 3.0})
    b = pd.Series({"G1": 1.0, "G2": 2.0, "G3": 3.0})
    assert np.isnan(lincs_connectivity_score(a, b))


def test_coverage_table_matches_committed_reality():
    """The coverage table honestly records 4/15 covered; PLCG1 covered (immune),
    CD3E not covered."""
    cov = load_coverage()
    assert cov["available"] is True
    t = cov["table"].set_index("gene")
    assert t.loc["PLCG1", "lincs_covered"] == "yes"
    assert t.loc["CD3E", "lincs_covered"] == "no"
    assert int((t["lincs_covered"] == "yes").sum()) == len(COVERED_GENES)
