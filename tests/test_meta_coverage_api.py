"""API test for GET /api/meta/coverage/{dataset_id} (docs/ux_trust_fix_plan.md Wave 1c).

Known-answer test: the computed coverage counts must match the numbers
independently tabulated by hand in docs/REPRODUCIBILITY.md (§3) -- this is
the check that the endpoint's join logic (ensembl_id for gnomAD/GTEx,
gene_symbol for disease associations) reproduces the same real numbers a
human already verified, not a coincidentally-plausible different number.
Uses the git-tracked reference dataset (e7ecd8d5-...) so this runs in any
fresh clone, unlike the untracked a6bba17b dataset some other tests skip on.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src" / "3_DE_analysis"
DATASET_ID = "e7ecd8d5-5463-43e3-9bf1-6e8a15d3e137"
DATASET_DIR = REPO / "sources" / "target_tool_cache" / DATASET_ID

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

pytestmark = pytest.mark.skipif(not (DATASET_DIR / "target_cards.csv").exists(), reason="reference dataset not present")


def _client():
    from fastapi.testclient import TestClient
    import target_card_api as api

    return TestClient(api.app)


def test_coverage_matches_reproducibility_md_known_values():
    body = _client().get(f"/api/meta/coverage/{DATASET_ID}").json()
    assert body["total_targets"] == 11526

    gnomad = body["domains"]["gnomad_constraint"]
    assert gnomad["available"] is True
    assert gnomad["covered"] == 15
    assert gnomad["total"] == 11526

    gtex = body["domains"]["gtex_tissue_breadth"]
    assert gtex["available"] is True
    assert gtex["covered"] == 5266
    assert round(gtex["pct"], 1) == 45.7

    disease = body["domains"]["disease_association"]
    assert disease["available"] is True
    assert disease["covered"] == 1977
    assert disease["n_diseases"] == 13

    lincs = body["domains"]["lincs"]
    assert lincs["available"] is True
    assert lincs["covered"] == 4
    assert lincs["total"] == 15


def test_denominator_basis_is_disclosed_and_lincs_has_its_own():
    body = _client().get(f"/api/meta/coverage/{DATASET_ID}").json()
    assert "denominator_basis" in body
    assert "denominator_basis" in body["domains"]["lincs"]
    # LINCS's tiny demo shortlist must never be silently compared against
    # total_targets -- that would make a 4/15 shortlist read as a
    # population-wide coverage number.
    assert body["domains"]["lincs"]["total"] != body["total_targets"]


def test_missing_dataset_404():
    assert _client().get("/api/meta/coverage/not-a-real-dataset-id").status_code == 404
