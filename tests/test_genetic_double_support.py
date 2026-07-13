"""Tests for genetic_double_support.py -- disease x population double-support (E).

Locks the four things that matter: (1) real known-answer -- the exploration's
strongest double-support targets surface with the verified breadth (IL23R
n_diseases>=6, SH2B3 n_diseases==12, PTPN22 present); (2) the exclusion logic --
a target with disease support at grade>=2 whose population CI *includes* zero
(PTPN2) is EXCLUDED, so a wrong join / a dropped CI filter can't pass; (3)
honest-fallback -- a bogus disease-association path yields available:False,
never a fabricated list; (4) the population caveat is carried verbatim on every
returned row.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from genetic_double_support import (
    DISEASE_ASSOCIATIONS_PATH,
    double_support,
)
from evidence.population import CAVEAT_TEXT, TRAIT_PATHS

REPO = Path(__file__).resolve().parent.parent
REAL_CARDS = REPO / "sources" / "target_tool_cache" / "a792d68c-7adc-46a6-964a-35770e5adbde" / "target_cards.csv"
BURDEN_FILE = TRAIT_PATHS["lymphocyte_count"]

REAL_DATA = REAL_CARDS.exists() and DISEASE_ASSOCIATIONS_PATH.exists() and BURDEN_FILE.exists()
requires_real = pytest.mark.skipif(
    not REAL_DATA, reason="pre-built cards / disease-association / burden data not present in this checkout"
)


@pytest.fixture(scope="module")
def real_result():
    cards = pd.read_csv(REAL_CARDS, low_memory=False)
    return double_support(cards, min_grade=2, trait="lymphocyte_count")


@pytest.fixture(scope="module")
def by_target(real_result):
    return {row["target"]: row for row in real_result["targets"]}


@requires_real
def test_available_and_nonempty(real_result):
    assert real_result["available"] is True
    assert real_result["reason"] is None
    assert real_result["n_double_support"] == len(real_result["targets"]) > 0
    assert real_result["trait"] == "lymphocyte_count"


@requires_real
def test_known_answer_il23r(by_target):
    assert "IL23R" in by_target, "IL23R should surface as a double-support target"
    row = by_target["IL23R"]
    assert row["n_diseases"] >= 6
    # In-list membership already implies its population CI excludes zero.
    assert row["ci"][0] > 0 or row["ci"][1] < 0


@requires_real
def test_known_answer_sh2b3_breadth(by_target):
    assert "SH2B3" in by_target
    # Broadest coverage: all 12 specific indications (umbrella bucket excluded).
    assert by_target["SH2B3"]["n_diseases"] == 12


@requires_real
def test_known_answer_ptpn22_present(by_target):
    assert "PTPN22" in by_target
    assert by_target["PTPN22"]["n_diseases"] >= 6


@requires_real
def test_negative_ci_includes_zero_excluded(by_target):
    # PTPN2 has disease genetic support at grade>=2 and is present in the burden
    # table, but its lymphocyte-count 95% CI *includes* zero -> it must NOT be a
    # double-support target. Guards the CI-excludes-zero filter.
    assert "PTPN2" not in by_target


@requires_real
def test_every_row_carries_population_caveat(real_result):
    assert real_result["caveat"] == CAVEAT_TEXT
    for row in real_result["targets"]:
        assert row["caveat"] == CAVEAT_TEXT
        # Each row exposes the full double-support payload.
        assert set(row) >= {
            "target",
            "n_diseases",
            "diseases",
            "max_assoc",
            "population_effect_estimate",
            "ci",
            "direction",
            "caveat",
        }
        assert len(row["ci"]) == 2


@requires_real
def test_sorted_by_breadth_then_assoc(real_result):
    keys = [(r["n_diseases"], r["max_assoc"]) for r in real_result["targets"]]
    assert keys == sorted(keys, reverse=True)


def test_honest_fallback_bogus_associations_path():
    # A nonexistent disease-association path -> empty disease table -> the
    # honest-fallback branch, never a fabricated list. Needs no real data.
    cards = pd.DataFrame(
        {
            "target": ["IL23R", "SH2B3"],
            "target_id": ["ENSG00000162594", "ENSG00000111252"],
            "statistical_evidence_grade": [4, 2],
        }
    )
    result = double_support(cards, associations_path=REPO / "does" / "not" / "exist.csv")
    assert result["available"] is False
    assert result["reason"]
    assert result["n_double_support"] == 0
    assert result["targets"] == []
    assert result["caveat"] == CAVEAT_TEXT


@requires_real
def test_honest_fallback_unavailable_burden():
    # An unrecognized trait makes the population side unavailable -> the whole
    # result is honest-fallback (never a disease-only list).
    cards = pd.read_csv(REAL_CARDS, low_memory=False)
    result = double_support(cards, trait="no_such_trait_xyz")
    assert result["available"] is False
    assert result["reason"]
    assert result["targets"] == []
    assert result["caveat"] == CAVEAT_TEXT
