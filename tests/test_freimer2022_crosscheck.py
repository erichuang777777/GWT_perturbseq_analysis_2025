"""Cross-checking GWT targets against Freimer et al. 2022's screen -- known-answer + unknown!=0."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "3_DE_analysis"
sys.path.insert(0, str(SRC))

import freimer2022_crosscheck as fc  # noqa: E402

_HAVE = fc.FREIMER_CSV.exists()


@pytest.mark.skipif(not _HAVE, reason="Freimer2022_Screen.csv not present")
def test_ctla4_recovers_its_own_eponymous_screen_hit():
    """Construct-validity anchor: the CTLA4 screen's #1 positive-selection hit is CTLA4 itself."""
    res = fc.freimer2022_crosscheck_for_target("CTLA4")
    assert res["available"] is True
    assert res["in_screen_scope"] is True
    ctla4_hits = [h for h in res["hits"] if h["screen"] == "CTLA4" and h["direction"] == "enriched"]
    assert ctla4_hits, "CTLA4 gene missing its own CTLA4-screen enriched-direction row"
    assert ctla4_hits[0]["rank"] == 1
    assert ctla4_hits[0]["significant"] is True
    assert "CTLA4" in res["significant_screens"]


@pytest.mark.skipif(not _HAVE, reason="Freimer2022_Screen.csv not present")
def test_hits_carry_strength_and_direction():
    res = fc.freimer2022_crosscheck_for_target("CTLA4")
    top = res["hits"][0]
    for key in ("screen", "direction", "fdr", "rank", "lfc", "significant"):
        assert key in top
    assert top["direction"] in ("depleted", "enriched")
    assert 0.0 <= top["fdr"] <= 1.0


@pytest.mark.skipif(not _HAVE, reason="Freimer2022_Screen.csv not present")
def test_gene_outside_subpool_is_out_of_scope_not_a_negative_result():
    # a gene almost certainly outside the ~1,350-gene subpool
    res = fc.freimer2022_crosscheck_for_target("NOT_A_REAL_GENE_XYZ")
    assert res["available"] is True
    assert res["in_screen_scope"] is False           # out of scope, not "tested and negative"
    assert res["hits"] == []                          # absence, never a fabricated non-hit
    assert res["n_significant"] == 0


@pytest.mark.skipif(not _HAVE, reason="Freimer2022_Screen.csv not present")
def test_non_targeting_control_row_is_excluded():
    # the CSV's "Non-Targeting" control row must never be servable as a gene
    res = fc.freimer2022_crosscheck_for_target("Non-Targeting")
    assert res["in_screen_scope"] is False


@pytest.mark.skipif(not _HAVE, reason="Freimer2022_Screen.csv not present")
def test_scope_size_is_disclosed():
    res = fc.freimer2022_crosscheck_for_target("CTLA4")
    assert res["n_genes_in_scope"] == fc.n_genes_in_scope()
    assert res["n_genes_in_scope"] and res["n_genes_in_scope"] < 2000  # a subpool, not genome-scale
