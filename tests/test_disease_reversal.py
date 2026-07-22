"""Tests for disease-signature reversal scoring (development plan P0-K).

A fully synthetic known-answer core (no data files) pins the sign convention and
the unknown != 0 / low-support discipline; a real-data sanity test runs against
``full_signed_DE`` when present and otherwise skips (never fails).
"""

from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd
import pytest

import disease_reversal as dr


def _signed(rows):
    return pd.DataFrame(rows, columns=["target_gene", "culture_condition", "downstream_gene", "log_fc"])


def test_reverser_scores_positive_worsener_negative():
    """A KD that drives a disease-UP gene DOWN and a disease-DOWN gene UP reverses
    the signature (score > 0); the opposite worsens it (score < 0)."""
    signature = {"up": ["UPGENE"], "down": ["DOWNGENE"]}
    signed = _signed([
        # REVERSER: up-gene pushed down (-2), down-gene pushed up (+2) -> +2 mean
        ("GOODKD", "Rest", "UPGENE", -2.0),
        ("GOODKD", "Rest", "DOWNGENE", 2.0),
        # WORSENER: up-gene pushed further up (+2), down-gene pushed down (-2) -> -2 mean
        ("BADKD", "Rest", "UPGENE", 2.0),
        ("BADKD", "Rest", "DOWNGENE", -2.0),
    ])
    out = dr.compute_reversal(signed, signature)
    by_gene = {r["target_gene"]: r for r in out.to_dict("records")}
    assert by_gene["GOODKD"]["reversal_score"] == pytest.approx(2.0)
    assert by_gene["GOODKD"]["direction"] == "reverses_disease"
    assert by_gene["GOODKD"]["n_signature_hit"] == 2
    assert by_gene["GOODKD"]["n_up_hit"] == 1 and by_gene["GOODKD"]["n_down_hit"] == 1
    assert by_gene["BADKD"]["reversal_score"] == pytest.approx(-2.0)
    assert by_gene["BADKD"]["direction"] == "worsens_disease"
    # n_signature_total counts the whole signature, not just the hits.
    assert by_gene["GOODKD"]["n_signature_total"] == 2


def test_neutral_band_and_unknown_not_zero():
    signature = {"up": ["UPGENE"], "down": ["DOWNGENE"]}
    signed = _signed([
        ("MEHKD", "Rest", "UPGENE", -0.2),   # |contrib| 0.2 < 0.5 band -> neutral
        # A target that perturbs NOTHING in the signature must be ABSENT, not 0.
        ("GHOSTKD", "Rest", "SOMEOTHERGENE", 5.0),
    ])
    out = dr.compute_reversal(signed, signature)
    genes = set(out["target_gene"])
    assert "MEHKD" in genes
    assert "GHOSTKD" not in genes  # unknown != 0
    assert out[out["target_gene"] == "MEHKD"].iloc[0]["direction"] == "neutral"


def test_empty_signature_returns_empty():
    out = dr.compute_reversal(_signed([("A", "Rest", "G", 1.0)]), {"up": [], "down": []})
    assert out.empty


def test_signature_from_de_table_thresholds():
    de = pd.DataFrame({
        "variable": ["A", "B", "C", "D"],
        "log_fc": [2.0, -2.0, 0.3, 2.0],
        "adj_p_value": [0.001, 0.001, 0.001, 0.5],  # D fails padj
    })
    sig = dr.signature_from_de_table(de, gene_col="variable", min_abs_lfc=1.0, max_padj=0.05)
    assert sig["up"] == {"A"}       # B is down, C below lfc, D fails padj
    assert sig["down"] == {"B"}


def test_rank_min_hits_is_reported_not_silent():
    signature = {"up": ["U1", "U2", "U3"], "down": []}
    signed = _signed([
        ("HIKD", "Rest", "U1", -1.0), ("HIKD", "Rest", "U2", -1.0), ("HIKD", "Rest", "U3", -1.0),
        ("LOKD", "Rest", "U1", -3.0),  # only 1 hit
    ])
    out = dr.compute_reversal(signed, signature)
    hi = out[out["target_gene"] == "HIKD"].iloc[0]
    lo = out[out["target_gene"] == "LOKD"].iloc[0]
    assert hi["n_signature_hit"] == 3 and lo["n_signature_hit"] == 1
    # LOKD has the larger raw score but rests on 1 gene; a min_hits filter would drop it.
    assert lo["reversal_score"] > hi["reversal_score"]


_HAS_SIGNED = bool(glob.glob(dr.SIGNED_DE_GLOB))


@pytest.mark.skipif(not _HAS_SIGNED, reason="full_signed_DE parquet not present in this checkout")
def test_real_data_builtin_signature_ranks():
    sig = dr.load_builtin_signature("th2_vs_th1_polarization")
    assert len(sig["up"]) > 100 and len(sig["down"]) > 100
    out = dr.rank_reversal(sig, top=10, min_hits=5)
    assert out["available"] is True
    assert out["min_hits"] == 5
    assert out["n_below_min_hits"] >= 0
    assert len(out["results"]) <= 10
    # every surfaced row respects the min_hits floor and carries its support counts
    for r in out["results"]:
        assert r["n_signature_hit"] >= 5
        assert r["direction"] in {"reverses_disease", "worsens_disease", "neutral"}
