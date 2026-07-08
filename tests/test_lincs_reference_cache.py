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

import numpy as np

from evidence.lincs_reference_cache import (
    COMPOUND_CAVEAT_TEXT,
    COMPOUND_SIGNATURES_PATH,
    COVERED_GENES,
    compound_reversal_matches,
    knockdown_reference,
    lincs_connectivity_score,
    load_compound_signatures,
    load_coverage,
    load_demo_signatures,
)


# --- COMPOUND half: fixtures ----------------------------------------------------
#
# IMPORTANT (fixture-vs-real distinction): the compound signature matrix built
# in these fixtures is a SYNTHETIC unit-test construct assembled IN-MEMORY here
# to exercise the reversal-ranking logic. It is NOT committed repo data and is
# NOT a real LINCS L1000 compound profile -- no real compound signatures are
# committed to this repo (that is exactly what makes the production path
# honestly unavailable, see test_compound_reversal_matches_no_committed_data).
# Constructing an in-memory fixture to test ranking is legitimate; committing it
# as if it were real data would violate the never-fabricate rule.


def _synthetic_compound_matrix():
    """A clearly-labeled fixture: 25 fake landmark genes x 3 fake compounds.

    Returns ``(query_series, compound_df)``. Needs >= 20 shared landmarks so
    ``lincs_connectivity_score`` (Spearman) is defined. The compounds are
    designed so their reversal ordering is known:
      - STRONG_REVERSER: exact rank-reverse of the query  -> connectivity -1.0
      - PARTIAL_REVERSER: mostly-reversed w/ a sawtooth    -> negative, > -1
      - SELF_MIMIC: identical to the query                 -> connectivity +1.0
    """
    genes = [f"LMARK{i}" for i in range(25)]
    base = np.arange(25, dtype=float)
    query = pd.Series(base, index=genes)
    compound_df = pd.DataFrame(
        {
            "STRONG_REVERSER": -base,
            "PARTIAL_REVERSER": -base + 6.0 * (np.arange(25) % 5),
            "SELF_MIMIC": base.copy(),
        },
        index=genes,
    )
    return query, compound_df


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


# --- COMPOUND half: honest-fallback loader --------------------------------------


def test_load_compound_signatures_no_committed_data_is_honest():
    """No LINCS compound matrix is committed to this repo -> the default-path
    loader must degrade honestly to available: False with an empty table and a
    reason pointing at the missing COMPOUND_SIGNATURES_PATH, never a fabricated
    compound matrix."""
    result = load_compound_signatures()
    assert result["available"] is False
    assert result["table"].empty
    assert str(COMPOUND_SIGNATURES_PATH) in result["reason"]
    # coverage-mismatch honesty: reason names the compound-specific sources
    assert "GSE92742" in result["reason"] or "compound" in result["reason"].lower()


def test_load_compound_signatures_missing_explicit_path_is_honest(tmp_path):
    result = load_compound_signatures(path=tmp_path / "nope.csv")
    assert result["available"] is False
    assert result["table"].empty


# --- COMPOUND half: reversal ranking (synthetic in-memory fixture) --------------


def test_compound_reversal_matches_no_committed_data_is_honest():
    """With no compound matrix (default), the ranker degrades honestly, keeps
    matches empty, and STILL carries the forced cell-context caveat."""
    query = pd.Series({f"LMARK{i}": float(i) for i in range(25)})
    result = compound_reversal_matches(query)  # compound_signatures=None -> load default
    assert result["available"] is False
    assert result["matches"] == []
    assert result["caveat"] == COMPOUND_CAVEAT_TEXT


def test_compound_reversal_matches_ranks_most_reversing_first():
    """On the SYNTHETIC in-memory fixture (NOT committed data -- see module
    comment), the exact rank-reverse compound must sort first with is_reversal
    True, and the self-signature (SELF_MIMIC == query) must be non-reversing."""
    query, compound_df = _synthetic_compound_matrix()
    result = compound_reversal_matches(query, compound_signatures=compound_df)

    assert result["available"] is True
    assert result["n_compounds_scored"] == 3
    matches = result["matches"]

    # Most-reversing (most negative connectivity) ranks first.
    assert matches[0]["compound"] == "STRONG_REVERSER"
    assert matches[0]["is_reversal"] is True
    assert matches[0]["connectivity_score"] == pytest.approx(-1.0)

    # Scores are sorted ascending (most reversing -> least).
    scores = [m["connectivity_score"] for m in matches]
    assert scores == sorted(scores)

    # Self-signature is a MIMIC, i.e. explicitly NON-reversing (+1.0), and last.
    self_match = next(m for m in matches if m["compound"] == "SELF_MIMIC")
    assert self_match["is_reversal"] is False
    assert self_match["connectivity_score"] == pytest.approx(1.0)
    assert matches[-1]["compound"] == "SELF_MIMIC"


def test_compound_reversal_matches_forces_cell_context_caveat():
    """Every returned compound-reversal result must disclose the OQ3
    cell-context mismatch (cancer/immortalized lines, not primary CD4+ T) and
    stay hypothesis-only -- never a treatment claim."""
    query, compound_df = _synthetic_compound_matrix()
    result = compound_reversal_matches(query, compound_signatures=compound_df)
    assert result["caveat"] == COMPOUND_CAVEAT_TEXT
    assert "CD4" in COMPOUND_CAVEAT_TEXT
    assert "mismatch" in COMPOUND_CAVEAT_TEXT.lower()
    assert "treatment claim" in COMPOUND_CAVEAT_TEXT.lower()


def test_compound_reversal_matches_respects_top_n():
    query, compound_df = _synthetic_compound_matrix()
    result = compound_reversal_matches(query, compound_signatures=compound_df, top_n=1)
    assert len(result["matches"]) == 1
    assert result["matches"][0]["compound"] == "STRONG_REVERSER"
    # n_compounds_scored reflects ALL scored compounds, not the truncated view.
    assert result["n_compounds_scored"] == 3
