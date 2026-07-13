"""Track D phenotype-matched cross-check — synthetic fixture + honest SKIP guard.

Locks in that:
  - `crosscheck()` computes a rank-rank Spearman, a Mann-Whitney-identity AUROC,
    and a flagship direction-agreement fraction from a small synthetic fixture
    engineered to have a KNOWN positive rank<->effect relationship.
  - calling the CLI entrypoint with no --external prints a SKIP report, writes
    NO output files, and exits 0 (never fabricates numbers from absent data).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

MODULE_DIR = (
    Path(__file__).resolve().parent.parent
    / "docs" / "mvp-research" / "level4_external_validation"
)
sys.path.insert(0, str(MODULE_DIR))

import phenotype_matched_crosscheck as pmc  # noqa: E402


# --------------------------------------------------------------------------- #
# Synthetic fixtures
# --------------------------------------------------------------------------- #
def _tiny_ranking() -> pd.DataFrame:
    # 8 genes, primary_rank 1 (top) .. 8 (bottom). signed_net sign encodes
    # KO-derepressed (+) vs KO-repressed (-) footprint.
    genes = ["VAV1", "CD3E", "PLCG1", "LCK", "ZAP70", "GENEF", "GENEG", "GENEH"]
    return pd.DataFrame({
        "target_gene": genes,
        "primary_rank": [1, 2, 3, 4, 5, 6, 7, 8],
        "directionality_index": [0.9, 0.8, 0.7, 0.6, 0.5, -0.5, -0.6, -0.7],
        "signed_net": [500, 400, 300, 200, 100, -100, -200, -300],
        "footprint_class": ["net_derepressed_on_KO"] * 5 + ["net_reduced_on_KO"] * 3,
    })


def _tiny_external_positive() -> pd.DataFrame:
    # Constructed so effect_score DECREASES monotonically as primary_rank increases
    # (i.e. top-ranked genes have the LARGEST external effect) -> we expect a
    # NEGATIVE Spearman between primary_rank and effect_score, i.e. a POSITIVE
    # relationship between "top rank" and "external effect". Top 4 genes are
    # significant hits (fdr < 0.1); bottom 4 are not.
    genes = ["VAV1", "CD3E", "PLCG1", "LCK", "ZAP70", "GENEF", "GENEG", "GENEH"]
    effect = [9.0, 8.0, 7.0, 6.0, 2.0, 1.5, 1.0, 0.5]
    fdr = [0.001, 0.002, 0.01, 0.05, 0.5, 0.6, 0.7, 0.8]
    # Flagship direction: VAV1/CD3E/PLCG1/LCK agree with our sign (+1, footprint
    # net_derepressed_on_KO -> signed_net>0); ZAP70 deliberately disagrees.
    hit_direction = [1, 1, 1, 1, -1, 1, -1, -1]
    return pd.DataFrame({
        "gene": genes,
        "effect_score": effect,
        "fdr": fdr,
        "hit_direction": hit_direction,
    })


# --------------------------------------------------------------------------- #
# crosscheck() correctness on the synthetic positive-signal fixture
# --------------------------------------------------------------------------- #
def test_crosscheck_spearman_sign_and_n():
    ranking = _tiny_ranking()
    external = _tiny_external_positive()
    result = pmc.crosscheck(ranking, external)

    assert result["n_merged"] == 8
    # primary_rank (1=top) is anti-correlated with effect_score by construction
    # -> Spearman rho between primary_rank and effect_score must be NEGATIVE.
    assert result["spearman_n"] == 8
    assert result["spearman_rho"] < 0
    assert not np.isnan(result["spearman_p"])


def test_crosscheck_auroc_in_range_and_above_chance():
    ranking = _tiny_ranking()
    external = _tiny_external_positive()
    result = pmc.crosscheck(ranking, external)

    assert 0.0 <= result["auroc"] <= 1.0
    # Top-4-ranked genes are exactly the 4 fdr<0.1 hits -> perfect separation -> AUROC 1.0
    assert result["auroc"] > 0.5
    assert result["auroc_n_pos"] == 4
    assert result["auroc_n_neg"] == 4


def test_crosscheck_direction_agreement_matches_construction():
    ranking = _tiny_ranking()
    external = _tiny_external_positive()
    result = pmc.crosscheck(ranking, external)

    # Flagships present: VAV1, CD3E, PLCG1, LCK, ZAP70 (all 5 in fixture).
    assert result["direction_n_total"] == 5
    # VAV1, CD3E, PLCG1, LCK agree (our sign +1 == hit_direction +1); ZAP70 disagrees.
    assert result["direction_n_agree"] == 4
    assert result["direction_frac"] == pytest.approx(4 / 5)

    detail = {g: agree for g, _, _, agree in result["direction_detail"]}
    assert detail["VAV1"] is True
    assert detail["CD3E"] is True
    assert detail["PLCG1"] is True
    assert detail["LCK"] is True
    assert detail["ZAP70"] is False


def test_crosscheck_handles_missing_hit_direction_honestly():
    ranking = _tiny_ranking()
    external = _tiny_external_positive().drop(columns=["hit_direction"])
    result = pmc.crosscheck(ranking, external)

    # No hit_direction column supplied -> direction stat is honestly 0/0, not fabricated.
    assert result["direction_n_total"] == 0
    assert result["direction_n_agree"] == 0
    assert np.isnan(result["direction_frac"])


# --------------------------------------------------------------------------- #
# End-to-end via tmp_path: write_outputs() + main() with a real --external file
# --------------------------------------------------------------------------- #
def test_write_outputs_creates_csv_and_md(tmp_path):
    ranking = _tiny_ranking()
    external = _tiny_external_positive()
    result = pmc.crosscheck(ranking, external)

    out_csv = tmp_path / "track_d.csv"
    out_md = tmp_path / "track_d.md"
    pmc.write_outputs(result, out_csv=out_csv, out_md=out_md)

    assert out_csv.exists()
    assert out_md.exists()
    merged = pd.read_csv(out_csv)
    assert len(merged) == 8
    md_text = out_md.read_text()
    assert "Corroborative, not confirmatory" in md_text
    assert "AUROC" in md_text


def test_main_end_to_end_with_synthetic_files(tmp_path, monkeypatch):
    ranking = _tiny_ranking()
    external = _tiny_external_positive()
    ranking_path = tmp_path / "ranking.csv"
    external_path = tmp_path / "external.csv"
    ranking.to_csv(ranking_path, index=False)
    external.to_csv(external_path, index=False)

    # Run main() with output redirected into tmp_path by monkeypatching the
    # module-level OUT_CSV / OUT_MD constants (main() calls write_outputs()
    # with its defaults).
    monkeypatch.setattr(pmc, "OUT_CSV", tmp_path / "out.csv")
    monkeypatch.setattr(pmc, "OUT_MD", tmp_path / "out.md")

    rc = pmc.main(["--ranking", str(ranking_path), "--external", str(external_path)])
    assert rc == 0
    assert (tmp_path / "out.csv").exists()
    assert (tmp_path / "out.md").exists()


# --------------------------------------------------------------------------- #
# SKIP path: honest assert-or-SKIP, never fabricate
# --------------------------------------------------------------------------- #
def test_load_external_returns_none_when_missing(tmp_path):
    missing_path = tmp_path / "does_not_exist.csv"
    assert pmc.load_external(missing_path) is None


def test_load_external_returns_none_when_columns_missing(tmp_path):
    bad = tmp_path / "bad_external.csv"
    pd.DataFrame({"gene": ["VAV1"], "some_other_col": [1.0]}).to_csv(bad, index=False)
    assert pmc.load_external(bad) is None


def test_main_skips_with_no_external_and_writes_nothing(tmp_path, monkeypatch, capsys):
    out_csv = tmp_path / "should_not_exist.csv"
    out_md = tmp_path / "should_not_exist.md"
    monkeypatch.setattr(pmc, "OUT_CSV", out_csv)
    monkeypatch.setattr(pmc, "OUT_MD", out_md)

    rc = pmc.main([])
    captured = capsys.readouterr()

    assert rc == 0
    assert "SKIP" in captured.out
    assert not out_csv.exists()
    assert not out_md.exists()


def test_main_skips_when_external_path_does_not_exist(tmp_path, monkeypatch, capsys):
    out_csv = tmp_path / "should_not_exist2.csv"
    out_md = tmp_path / "should_not_exist2.md"
    monkeypatch.setattr(pmc, "OUT_CSV", out_csv)
    monkeypatch.setattr(pmc, "OUT_MD", out_md)

    rc = pmc.main(["--external", str(tmp_path / "nope.csv")])
    captured = capsys.readouterr()

    assert rc == 0
    assert "SKIP" in captured.out
    assert not out_csv.exists()
    assert not out_md.exists()
