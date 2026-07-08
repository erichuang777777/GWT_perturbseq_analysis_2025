"""GET /api/exports/{dataset_id}?fmt=json — provenance stamp + NaN-safety.

Pins two things on the bulk JSON export (north-star 支柱二 資料明確 / bulk
download): the downloaded snapshot is self-describing (carries a provenance /
version block alongside the target records), and it no longer crashes on
datasets with missing cells (the pre-existing `df.to_dict` NaN path is replaced
by the JSON-compliant `_json_records`).
"""
from __future__ import annotations

import pytest


def _client():
    from fastapi.testclient import TestClient
    import target_card_api as api

    return TestClient(api.app)


def _a_dataset_id(client):
    datasets = client.get("/api/datasets").json()
    if not datasets:
        pytest.skip("no built dataset available in this checkout")
    return datasets[0]["dataset_id"]


def test_json_export_is_nan_safe_and_stamps_provenance():
    client = _client()
    dsid = _a_dataset_id(client)
    resp = client.get(f"/api/exports/{dsid}", params={"fmt": "json"})
    # Must not 500 on NaN cells (the pre-existing bug this fixes).
    assert resp.status_code == 200
    body = resp.json()
    # Pre-existing keys unchanged (additive), plus the new provenance block.
    assert body["dataset_id"] == dsid
    assert isinstance(body["targets"], list) and body["targets"]
    prov = body["provenance"]
    for key in ("engine_version", "schema_version"):
        assert prov.get(key)


def test_csv_export_still_works():
    client = _client()
    dsid = _a_dataset_id(client)
    resp = client.get(f"/api/exports/{dsid}", params={"fmt": "csv"})
    assert resp.status_code == 200
