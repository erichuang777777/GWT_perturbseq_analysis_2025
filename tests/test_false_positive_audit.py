"""Tests for false_positive_audit.py (Bench2Biobank #123 phenome-breadth port)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "3_DE_analysis"))

import false_positive_audit as fpa  # noqa: E402


def test_unmeasured_is_unknown_not_pass():
    # unknown != 0: no track-A row -> verdict "unknown", risk None (NOT a clean pass)
    r = fpa.phenome_breadth(None, None)
    assert r["verdict"] == "unknown"
    assert r["elevated_fp_risk"] is None
    assert r["n_genetic_assoc_diseases"] is None


def test_zero_associations_is_measured_no_association():
    # measured 0 is distinct from unmeasured
    r = fpa.phenome_breadth(0, 0)
    assert r["verdict"] == "no_association"
    assert r["elevated_fp_risk"] is False
    assert r["n_genetic_assoc_diseases"] == 0


def test_broad_low_immune_specificity_flags_elevated_risk():
    # many diseases, very few immune -> elevated FP risk (pleiotropic footprint)
    r = fpa.phenome_breadth(n_assoc=20, n_immune=1, top_any_score=0.7, top_immune_score=0.1)
    assert r["verdict"] == "broad_low_immune_specificity"
    assert r["elevated_fp_risk"] is True
    assert r["phenome_breadth_tier"] == "broad"
    assert r["immune_fraction"] == round(1 / 20, 4)


def test_immune_focused_is_low_risk():
    # associations concentrated in immune disease -> not elevated
    r = fpa.phenome_breadth(n_assoc=6, n_immune=5, top_immune_score=0.8)
    assert r["verdict"] == "immune_focused"
    assert r["elevated_fp_risk"] is False


def test_focused_single_immune_hit_is_low_risk():
    # <= FOCUSED_N diseases with an immune hit -> immune_focused
    r = fpa.phenome_breadth(n_assoc=2, n_immune=1)
    assert r["verdict"] == "immune_focused"
    assert r["elevated_fp_risk"] is False


def test_broad_but_immune_heavy_is_not_flagged():
    # broad footprint but immune fraction high -> not the low-specificity case
    r = fpa.phenome_breadth(n_assoc=15, n_immune=9)
    assert r["verdict"] == "immune_focused"
    assert r["elevated_fp_risk"] is False


def test_mixed_when_no_strong_signal():
    # moderate breadth, immune fraction between the cuts -> mixed, not elevated
    r = fpa.phenome_breadth(n_assoc=8, n_immune=2)  # frac 0.25, not broad (<=10)
    assert r["verdict"] == "mixed"
    assert r["elevated_fp_risk"] is False


def test_immune_fraction_none_when_immune_unmeasured():
    # n_assoc known but n_immune missing -> fraction None, cannot be the low-immune case
    r = fpa.phenome_breadth(n_assoc=20, n_immune=None)
    assert r["immune_fraction"] is None
    assert r["elevated_fp_risk"] is False
    assert r["verdict"] == "mixed"


def test_full_audit_stubs_are_honest_measured_false():
    r = fpa.full_audit(n_assoc=20, n_immune=1)
    for sub in ("mhc_region", "nearest_gene"):
        assert r[sub]["measured"] is False
        assert r[sub]["flagged"] is None
        assert "requires" in r[sub] and r[sub]["requires"]
    # top-line risk mirrors the one check we can actually run
    assert r["elevated_fp_risk"] == r["phenome_breadth"]["elevated_fp_risk"] is True


def test_audit_gwas_row_maps_track_a_columns():
    row = {
        "n_genetic_assoc_diseases": 25,
        "n_immune_genetic_assoc": 7,
        "top_any_GA_score": 0.72,
        "top_immune_GA_score": 0.72,
    }
    r = fpa.audit_gwas_row(row)
    # 7/25 = 0.28 >= LOW_IMMUNE_FRAC(0.2) so broad but not low-immune -> not flagged
    assert r["phenome_breadth"]["n_genetic_assoc_diseases"] == 25
    assert r["elevated_fp_risk"] is False
