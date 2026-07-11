"""Standalone live-upload tool (`GET /upload`) — page + end-to-end flow.

Locks in the "approach C" upload feature: the page is served, and the full
staging flow it drives (upload -> mapping -> approve -> merge -> real readiness)
works end to end against the live API, honouring `unknown != 0`
(guide-less upload -> kd_status not_assessed) and preserving `n_total_de_genes`.
"""

from __future__ import annotations

import base64
import shutil
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "3_DE_analysis"
sys.path.insert(0, str(SRC))

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from api.app import app  # noqa: E402
from api import deps  # noqa: E402

client = TestClient(app)


def test_upload_page_is_served():
    r = client.get("/upload")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    body = r.text
    # Drives the existing staging endpoints, and keeps the honesty disclosures.
    assert "/api/imports" in body
    assert "never as" in body and "unknown" in body  # unknown != 0 banner
    assert "Research / hypothesis-generating use only" in body


def test_upload_ui_capability_available():
    caps = client.get("/api/health").json()["capabilities"]
    assert caps.get("upload_ui") == "available"


def test_upload_flow_end_to_end_reaches_real_readiness():
    csv = (
        "gene,culture_condition,log2fc,padj,n_cells,num_de_genes\n"
        "IL2RA,Stim8hr,-2.4,0.0004,620,340\n"
        "CTLA4,Stim8hr,-1.8,0.002,410,150\n"
    )
    b64 = base64.b64encode(csv.encode()).decode()
    created = client.post("/api/imports", json={
        "source_name": "CD4 T-cell Perturb-seq screen (test)",
        "filename": "cd4_test.csv",
        "content_base64": b64,
        "declared_source_type": "target_evidence",
        "mode": "strict",
    })
    assert created.status_code == 200, created.text
    import_id = created.json()["import_id"]
    dataset_id = None
    try:
        # strict + CD4 context reads as a clean, approvable staged import
        assert created.json()["merge_status"] == "staged"

        sug = client.get(f"/api/imports/{import_id}/mapping/suggestion").json()["suggested"]
        # A.2: the non-canonical column name is mapped to n_total_de_genes
        assert sug.get("n_total_de_genes") == "num_de_genes"
        client.post(f"/api/imports/{import_id}/mapping", json={"map": sug})

        client.post(f"/api/imports/{import_id}/approve", json={"approved_by": "test"})
        merged = client.post(f"/api/imports/{import_id}/merge", json={})
        assert merged.status_code == 200, merged.text
        dataset_id = merged.json()["dataset_id"]
        assert merged.json()["rows"] == 2

        rd = client.get(f"/api/readiness/{dataset_id}")
        assert rd.status_code == 200
        payload = rd.json()
        assert payload["dataset_id"] == dataset_id
        # real readiness engine ran; missing overlays reported (unknown != 0)
        assert "call_counts" in payload
        assert "overlays_missing" in payload

        # A.1: guide-less upload -> kd_status not_assessed (not not_measurable).
        # Read from the merge preview (cards records), which carries kd_status.
        preview = merged.json().get("preview", [])
        statuses = {row.get("kd_status") for row in preview}
        assert statuses == {"not_assessed"}, statuses
    finally:
        # keep the test cache clean
        for d in [deps.CACHE_ROOT / dataset_id if dataset_id else None,
                  deps.CACHE_ROOT / "imports" / import_id]:
            if d and d.exists():
                shutil.rmtree(d, ignore_errors=True)
