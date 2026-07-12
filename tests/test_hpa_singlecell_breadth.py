"""Single-cell-resolution off-context expression breadth (HPA) -- known-answer + unknown!=0."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "3_DE_analysis"
sys.path.insert(0, str(SRC))

import hpa_singlecell_breadth as hb  # noqa: E402
from evidence.safety_overlay import load_hpa_singlecell_breadth_overlay  # noqa: E402

_HAVE = load_hpa_singlecell_breadth_overlay()["available"]


@pytest.mark.skipif(not _HAVE, reason="hpa_singlecell_breadth_seed.parquet not present")
def test_cd3e_off_context_max_is_nk_cells_not_tcells():
    """CD3E's true peak (T-cells, nCPM 424.7) must be excluded; NK-cells (137.0) is next-highest."""
    res = hb.hpa_singlecell_breadth_for_target("CD3E")
    assert res["available"] is True
    assert res["in_overlay"] is True
    assert res["max_expression_outside_tcell_context"] == pytest.approx(137.0, abs=0.1)
    assert res["n_celltypes_expressed"] > 0


@pytest.mark.skipif(not _HAVE, reason="hpa_singlecell_breadth_seed.parquet not present")
def test_foxp3_is_narrowly_expressed_off_context():
    """FOXP3 is Treg-restricted -- narrow breadth even outside its T-cells peak."""
    res = hb.hpa_singlecell_breadth_for_target("FOXP3")
    assert res["available"] is True
    assert res["max_expression_outside_tcell_context"] == pytest.approx(4.0, abs=0.1)
    assert res["n_celltypes_expressed"] < 10


@pytest.mark.skipif(not _HAVE, reason="hpa_singlecell_breadth_seed.parquet not present")
def test_unknown_gene_is_unknown_not_zero():
    res = hb.hpa_singlecell_breadth_for_target("NOT_A_REAL_GENE_XYZ")
    assert res["available"] is True
    assert res["in_overlay"] is False
    assert res["n_celltypes_expressed"] == "unknown"
    assert res["max_expression_outside_tcell_context"] == "unknown"


def test_missing_overlay_file_is_honest(tmp_path, monkeypatch):
    import evidence.safety_overlay as so

    monkeypatch.setattr(so, "HPA_SINGLECELL_PATH_DEFAULT", tmp_path / "does_not_exist.parquet")
    result = so.load_hpa_singlecell_breadth_overlay()
    assert result["available"] is False
    assert result["table"].empty
