"""Shared pytest fixtures for the target-card toolkit test suite.

Adds ``src/3_DE_analysis`` to ``sys.path`` so tests can ``import build_target_cards``
etc. directly, matching how the modules already import each other (flat, no package).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src" / "3_DE_analysis"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def golden_de_stats() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_DIR / "golden_de_stats.csv")


@pytest.fixture
def golden_guide_kd() -> pd.DataFrame:
    return pd.read_csv(FIXTURES_DIR / "golden_guide_kd.csv")


@pytest.fixture
def golden_resolver():
    from gene_identifier_resolver import load_resolver

    return load_resolver(
        library_path=FIXTURES_DIR / "golden_library.csv",
        guide_kd_path=FIXTURES_DIR / "golden_guide_kd.csv",
    )


@pytest.fixture
def golden_cards(golden_de_stats, golden_guide_kd):
    from build_target_cards import build_cards_frame

    return build_cards_frame(
        golden_de_stats,
        golden_guide_kd,
        lib_map=None,
        benchmark=None,
        sample_meta=None,
    )


@pytest.fixture(scope="session")
def real_data_available() -> bool:
    return (REPO_ROOT / "metadata" / "suppl_tables" / "DE_stats.suppl_table.csv").exists()


@pytest.fixture(scope="session")
def real_cards(real_data_available):
    """Cards built fresh from the real, in-repo reference dataset (~15s, once per session).

    Skips (rather than fails) when the real suppl_tables aren't present, so this
    test suite still runs green on a checkout without the large metadata files.
    """
    if not real_data_available:
        pytest.skip("metadata/suppl_tables/*.csv not present in this checkout")
    from build_target_cards import build_cards_frame

    de = pd.read_csv(REPO_ROOT / "metadata/suppl_tables/DE_stats.suppl_table.csv")
    guide = pd.read_csv(REPO_ROOT / "metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv")
    lib = pd.read_csv(REPO_ROOT / "metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv")
    sample_meta = pd.read_csv(REPO_ROOT / "metadata/suppl_tables/sample_metadata.suppl_table.csv")
    return build_cards_frame(de, guide, lib, None, sample_meta=sample_meta)


@pytest.fixture(scope="session")
def real_readiness(real_cards):
    from build_target_cards import load_gene_set
    from readiness_engine import compute_readiness

    broad = load_gene_set(REPO_ROOT / "sources/broad_effect_genes.txt")
    essentials = load_gene_set(REPO_ROOT / "metadata/gene_lists/core_essentials_hart.tsv")
    return compute_readiness(real_cards, overlays=None, essentials=essentials, broad_effect_genes=broad)
