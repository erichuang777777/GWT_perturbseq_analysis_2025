"""API test for the per-target descriptive-axes endpoint (dossier enrichment).

GET /api/triage/{dataset_id}/{target} returns the composite descriptive axes for
ONE target -- the entity-page companion to the ranked /api/triage list. Gated on
the pre-built reference dataset being present in the cache.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src" / "3_DE_analysis"
DATASET_ID = "a6bba17b-f194-4a50-8cf8-96e03eededd6"
DATASET_DIR = REPO / "sources" / "target_tool_cache" / DATASET_ID

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

pytestmark = pytest.mark.skipif(not (DATASET_DIR / "target_cards.csv").exists(), reason="reference dataset not present")


def _client():
    from fastapi.testclient import TestClient
    import target_card_api as api

    return TestClient(api.app)


def test_per_target_axes_known_answer_plcg1():
    body = _client().get(f"/api/triage/{DATASET_ID}/PLCG1").json()
    assert body["available"] is True
    assert body["descriptive_only"] is True
    axes = body["axes"]
    # concept: PLCG1 is in the TCR-proximal module M02
    assert any(m.get("module_id") == "M02" for m in axes["concept_modules"])
    # every descriptive axis is present on the composite
    for key in ("stimulation_gated", "switch_type", "robustness_tier", "double_support", "composite_safety_liability"):
        assert key in axes
    # unknown != 0: PLCG1 is not in the ~15-gene gnomAD seed -> safety is 'unknown', never a number/'safe'
    assert axes["composite_safety_liability"] == "unknown"
    assert body["provenance"].get("concept_set_version")


def test_case_insensitive_match():
    assert _client().get(f"/api/triage/{DATASET_ID}/plcg1").json()["available"] is True


def test_absent_target_is_honest_fallback():
    body = _client().get(f"/api/triage/{DATASET_ID}/NOT_A_REAL_GENE_XYZ").json()
    assert body["available"] is False
    assert body["reason"]


def test_missing_dataset_404():
    assert _client().get("/api/triage/not-a-real-dataset/PLCG1").status_code == 404
