"""Tests for the concept-module (seed-modules CSV) contract.

Covers the real ``topic15_...seed_modules.csv`` passing validation, a spot-check
that a known module carries its real seed genes, malformed CSVs being caught with
honest structured problems, and the ``strict`` raise/return contract.

``conftest.py`` puts ``src/3_DE_analysis`` on ``sys.path``, so the contract module
imports flat, matching how the other modules import each other.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from contracts.concept_schema import (
    CONCEPT_COLUMNS,
    CORE_REQUIRED_COLUMNS,
    count_modules,
    count_seed_genes,
    validate_concept_modules,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_MODULES_CSV = (
    REPO_ROOT / "sources" / "topic15_cd4_tcell_upstream_downstream_seed_modules.csv"
)


def _load_real_modules() -> pd.DataFrame:
    return pd.read_csv(SEED_MODULES_CSV, dtype=str)


# --- the real concept set --------------------------------------------------


def test_real_seed_modules_file_exists():
    assert SEED_MODULES_CSV.exists(), f"missing seed-modules CSV at {SEED_MODULES_CSV}"


def test_real_seed_modules_pass_validation():
    df = _load_real_modules()
    problems = validate_concept_modules(df)
    assert problems == [], f"real seed-modules CSV should validate cleanly, got: {problems}"
    # strict=True must not raise on the real, valid CSV.
    assert validate_concept_modules(df, strict=True) == []


def test_real_seed_modules_has_20_concepts():
    df = _load_real_modules()
    assert count_modules(df) == 20


def test_real_seed_modules_have_expected_columns():
    df = _load_real_modules()
    for col in CONCEPT_COLUMNS:
        assert col in df.columns, f"expected column {col!r} in seed-modules CSV"


def test_m08_th2_polarization_real_seed_genes():
    """Spot-check: M08 must carry its real, verbatim seed genes from the CSV."""
    df = _load_real_modules()
    row = df[df["module_id"] == "M08"]
    assert len(row) == 1
    assert row.iloc[0]["module_name"] == "Th2_Polarization"
    # Verbatim from sources/topic15_...seed_modules.csv, in file order.
    expected = ["GATA3", "IL4", "IL13", "IL4R", "STAT6", "IRF4"]
    genes = [g.strip() for g in row.iloc[0]["seed_genes"].split(",") if g.strip()]
    assert genes == expected


def test_count_seed_genes_helpers():
    df = _load_real_modules()
    # Every module has at least one seed gene, so total mentions > module count.
    assert count_seed_genes(df) > count_modules(df)
    # unique count never exceeds raw mention count (M10 repeats IKZF2 verbatim).
    assert count_seed_genes(df, unique=True) <= count_seed_genes(df)


# --- malformed concept sets ------------------------------------------------


def test_duplicate_module_id_is_caught():
    df = pd.DataFrame(
        {
            "module_id": ["M01", "M01"],
            "module_name": ["A", "B"],
            "seed_genes": ["CD3D,CD3E", "LCK,FYN"],
        }
    )
    problems = validate_concept_modules(df)
    assert any("duplicate module_id" in p for p in problems)


def test_empty_seed_genes_is_caught():
    df = pd.DataFrame(
        {
            "module_id": ["M01", "M02"],
            "module_name": ["A", "B"],
            "seed_genes": ["CD3D,CD3E", ""],
        }
    )
    problems = validate_concept_modules(df)
    assert any("no seed genes" in p for p in problems)
    assert any("M02" in p for p in problems)


def test_empty_module_name_is_caught():
    df = pd.DataFrame(
        {
            "module_id": ["M01"],
            "module_name": ["  "],
            "seed_genes": ["CD3D,CD3E"],
        }
    )
    problems = validate_concept_modules(df)
    assert any("module_name" in p for p in problems)


def test_missing_required_column_is_caught():
    df = pd.DataFrame({"module_id": ["M01"], "module_name": ["A"]})  # no seed_genes
    problems = validate_concept_modules(df)
    assert any("missing columns" in p for p in problems)
    assert any("seed_genes" in p for p in problems)


# --- strict raise / non-strict return contract -----------------------------


def test_strict_false_returns_problems_without_raising():
    df = pd.DataFrame(
        {
            "module_id": ["M01", "M01"],
            "module_name": ["A", "B"],
            "seed_genes": ["CD3D", ""],
        }
    )
    # Must not raise; must report both the duplicate id and the empty seed set.
    problems = validate_concept_modules(df, strict=False)
    assert len(problems) >= 2


def test_strict_true_raises_on_bad_data():
    df = pd.DataFrame(
        {
            "module_id": ["M01", "M01"],
            "module_name": ["A", "B"],
            "seed_genes": ["CD3D,CD3E", "LCK,FYN"],
        }
    )
    with pytest.raises(ValueError):
        validate_concept_modules(df, strict=True)


def test_core_required_columns_subset_of_concept_columns():
    assert set(CORE_REQUIRED_COLUMNS).issubset(set(CONCEPT_COLUMNS))
