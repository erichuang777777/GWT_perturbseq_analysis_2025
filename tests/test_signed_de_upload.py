"""P1 — accept any perturb-seq dataset: signed-DE upload -> reversal / breadth.

Covers the reader (signed_de_io), the new signed_de_evidence source type
detection, and the two from_upload endpoints running on a user's own uploaded
signed table (not the bundled screen).
"""

from __future__ import annotations

import base64
import sys

import pandas as pd
import pytest

sys.path.insert(0, "src/3_DE_analysis")

import signed_de_io
from upload.import_manager import infer_source_type


def test_reader_normalizes_aliases_and_defaults(tmp_path):
    # user columns use aliases + no condition + no padj
    df = pd.DataFrame({
        "gene": ["TARGA", "TARGA", "TARGB"],
        "downstream": ["G1", "G2", "G1"],
        "beta": [-2.0, 1.5, 0.3],
    })
    p = tmp_path / "signed.csv"
    df.to_csv(p, index=False)
    out, notes = signed_de_io.read_signed_de_table(p)
    assert set(["target_gene", "downstream_gene", "log_fc", "culture_condition", "adj_p_value"]).issubset(out.columns)
    assert (out["culture_condition"] == "all").all()          # synthesized, stated
    assert "condition_synthesized" in notes
    assert (out["adj_p_value"] == 0.0).all()                  # defaulted, stated
    assert "adj_p_value_defaulted" in notes
    assert notes["n_targets"] == 2


def test_reader_raises_on_missing_effect(tmp_path):
    p = tmp_path / "bad.csv"
    pd.DataFrame({"target": ["A"], "downstream_gene": ["G1"]}).to_csv(p, index=False)
    with pytest.raises(ValueError):
        signed_de_io.read_signed_de_table(p)


def test_infer_detects_signed_de_before_target_evidence(tmp_path):
    p = tmp_path / "x.csv"
    cols = ["target_gene", "culture_condition", "downstream_gene", "log_fc"]
    assert infer_source_type(p, cols, None) == "signed_de_evidence"


def _client():
    from fastapi.testclient import TestClient
    from api.app import app
    return TestClient(app)


def _register_signed_upload(client) -> str:
    # A tiny signed table: knocking TARGA down reverses a signature (UPG down, DOWNG up).
    df = pd.DataFrame({
        "target_gene": ["TARGA", "TARGA", "TARGB", "TARGB"],
        "culture_condition": ["Rest", "Rest", "Rest", "Rest"],
        "downstream_gene": ["UPG", "DOWNG", "UPG", "DOWNG"],
        "log_fc": [-2.0, 2.0, 2.0, -2.0],
        "adj_p_value": [0.001, 0.001, 0.001, 0.001],
    })
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    r = client.post("/api/imports", json={
        "source_name": "my_signed_screen", "filename": "signed.csv",
        "content_base64": b64, "declared_source_type": "signed_de_evidence",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["source_type"] == "signed_de_evidence"
    return body["import_id"]


def test_reversal_and_breadth_on_uploaded_screen():
    client = _client()
    import_id = _register_signed_upload(client)

    rev = client.post("/api/disease_reversal/from_upload", json={
        "import_id": import_id, "up": ["UPG"], "down": ["DOWNG"], "min_hits": 1, "top": 10,
    })
    assert rev.status_code == 200, rev.text
    body = rev.json()
    assert body["available"] is True
    by = {r["target_gene"]: r for r in body["results"]}
    assert by["TARGA"]["direction"] == "reverses_disease"     # KD moves UPG down, DOWNG up
    assert by["TARGB"]["direction"] == "worsens_disease"
    assert body["upload"]["import_id"] == import_id

    br = client.get(f"/api/trans_network/from_upload/{import_id}", params={"gene": "TARGA"})
    assert br.status_code == 200, br.text
    bb = br.json()
    assert bb["available"] is True and bb["measured_targets"] == 2
    assert bb["gene"]["measured"] is True and bb["gene"]["trans_effect_breadth"] == 2


def test_from_upload_rejects_wrong_type_and_missing():
    client = _client()
    assert client.get("/api/trans_network/from_upload/does-not-exist").status_code == 404
    assert client.post("/api/disease_reversal/from_upload", json={"import_id": "nope", "up": ["X"]}).status_code == 404
