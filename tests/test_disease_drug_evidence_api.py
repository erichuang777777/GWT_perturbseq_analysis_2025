"""API test for GET /api/disease-drug-evidence (docs/frontend_design.md §5.2).

Thin-wrapper route over the already-tested `match_disease_drug_evidence()`
(see tests/test_disease_drug_evidence.py for the underlying function's
contract tests). This file only checks the HTTP layer: status codes, query
params, and that the route returns the function's dict unmodified (no
reshaping, no fabrication on failure).

Network-dependent (live Open Targets / ClinicalTrials.gov calls, same as the
underlying function) -- skipped automatically if outbound network is
unavailable, consistent with tests/test_disease_drug_evidence.py's own gate.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src" / "3_DE_analysis"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evidence.external_cache import _open_targets_resolve_ensembl_id


def _network_available():
    try:
        return _open_targets_resolve_ensembl_id("IL2RA") is not None
    except Exception:
        return False


NETWORK_OK = _network_available()
pytestmark = pytest.mark.skipif(not NETWORK_OK, reason="Open Targets API unreachable from this environment")


def _client():
    from fastapi.testclient import TestClient
    import target_card_api as api

    return TestClient(api.app)


def test_known_gene_known_disease_returns_available():
    body = _client().get("/api/disease-drug-evidence", params={"gene": "IL2RA", "disease": "rheumatoid arthritis"}).json()
    assert body["available"] is True
    assert body["n_known_drugs_for_gene"] > 0
    assert "caveat" in body and "not a treatment recommendation" in body["caveat"]


def test_max_drugs_param_is_honored():
    body = _client().get(
        "/api/disease-drug-evidence",
        params={"gene": "IL2RA", "disease": "rheumatoid arthritis", "max_drugs": 1},
    ).json()
    assert body["available"] is True
    assert len(body["drugs"]) <= 1


def test_unknown_gene_is_honest_fallback_not_404():
    """available:False is a normal, valid response body -- not an HTTP error --
    since a caller (the frontend page) must render it as a state, not retry it."""
    resp = _client().get("/api/disease-drug-evidence", params={"gene": "NOTAREALGENE123", "disease": "rheumatoid arthritis"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert "not found" in body["reason"]


def test_response_carries_version_headers():
    resp = _client().get("/api/disease-drug-evidence", params={"gene": "IL2RA", "disease": "rheumatoid arthritis"})
    assert "X-Engine-Version" in resp.headers
    assert "X-Schema-Version" in resp.headers
