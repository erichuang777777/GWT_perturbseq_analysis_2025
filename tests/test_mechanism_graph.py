"""A2: target-centered mechanism graph (mechanism_graph.py).

mechanism_graph.py only ever *reads* pathway_network_cache.py's cached
snapshot -- it never fetches live. So these tests write cached-snapshot
fixture JSON directly (the same on-disk shape ``build_pathway_network_for_gene``
produces), rather than hitting Reactome/STRING over the network (which
tests/test_pathway_network_cache.py already independently confirms; this
sandbox's egress proxy blocks reactome.org/string-db.org, so those
network-dependent tests skip here).

The gene/pathway identities below are not invented: they are the real,
already-verified values pinned by tests/test_pathway_network_cache.py --
CD3E's real Reactome TCR-signaling pathway membership and its real STRING
partners (CD247, CD3D, CD3G are asserted there), and MED12's STRING partners
being dominated by other real Mediator-complex subunits (MED*). Only the
numeric STRING scores are synthetic placeholders (this sandbox cannot make a
live STRING call to read the real score values) -- the test comments below
call this out explicitly; no test asserts a specific score value as if it
were a confirmed real number.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "src/3_DE_analysis")

import pandas as pd
import pytest

import mechanism_graph as mg
import pathway_network_cache as pnc


def _write_snapshot(cache_dir: Path, snapshot: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    pnc._cache_path(cache_dir, snapshot["gene"]).write_text(json.dumps(snapshot), encoding="utf-8")


@pytest.fixture
def cd3e_snapshot() -> dict:
    # Pathway names and STRING partners are the real values independently
    # confirmed by tests/test_pathway_network_cache.py::
    #   test_cd3e_reactome_hits_tcr_signaling
    #   test_cd3e_string_network_includes_real_tcr_complex_partners
    # Scores are synthetic placeholders (see module docstring).
    return {
        "gene": "CD3E",
        "ensembl_id": "ENSG00000198851",
        "fetched_at": "2026-07-01T00:00:00+00:00",
        "source_version": pnc.SOURCE_VERSION,
        "sources": {
            "reactome_pathways": {
                "source_status": "ok",
                "items": [
                    {"pathway_id": "R-HSA-202403", "pathway_name": "TCR signaling", "is_in_disease": False},
                    {
                        "pathway_id": "R-HSA-198933",
                        "pathway_name": "Immunoregulatory interactions between a Lymphoid and a non-Lymphoid cell",
                        "is_in_disease": False,
                    },
                ],
            },
            "string_network": {
                "source_status": "ok",
                "items": [
                    {"partner": "CD247", "score": 990},
                    {"partner": "CD3D", "score": 999},
                    {"partner": "CD3G", "score": 999},
                    {"partner": "CD4", "score": 950},
                    {"partner": "SYK", "score": 900},
                ],
            },
        },
    }


@pytest.fixture
def med12_snapshot() -> dict:
    # STRING partners dominated by real Mediator-complex subunits, confirmed by
    # tests/test_pathway_network_cache.py::test_med12_string_network_dominated_by_mediator_complex.
    # Scores are synthetic placeholders (see module docstring).
    return {
        "gene": "MED12",
        "ensembl_id": "ENSG00000184634",
        "fetched_at": "2026-07-01T00:00:00+00:00",
        "source_version": pnc.SOURCE_VERSION,
        "sources": {
            "reactome_pathways": {
                "source_status": "unavailable",
                "reason": "no ensembl_id available for this gene",
                "items": [],
            },
            "string_network": {
                "source_status": "ok",
                "items": [
                    {"partner": "MED1", "score": 950},
                    {"partner": "MED13", "score": 960},
                    {"partner": "MED23", "score": 940},
                    {"partner": "CDK8", "score": 900},
                ],
            },
        },
    }


def test_cd3e_graph_has_real_tcr_neighbors(tmp_path, cd3e_snapshot):
    _write_snapshot(tmp_path, cd3e_snapshot)
    graph = mg.build_mechanism_graph("CD3E", tmp_path)

    assert graph["available"] is True
    assert graph["gene"] == "CD3E"
    assert graph["reactome_status"] == "ok"
    assert graph["string_status"] == "ok"

    node_ids = {n["id"] for n in graph["nodes"]}
    # Real TCR-complex STRING partners (confirmed in test_pathway_network_cache.py)
    assert {"CD247", "CD3D", "CD3G"}.issubset(node_ids)
    # Real Reactome pathway membership, modeled as pathway nodes (not
    # fabricated co-member gene nodes -- the cache doesn't hold that data).
    pathway_names = {n["pathway_name"] for n in graph["nodes"] if n["type"] == "pathway"}
    assert any("TCR" in name for name in pathway_names)

    # center + 2 pathways + 5 STRING partners
    assert len(graph["nodes"]) == 8
    # 2 pathway-membership edges + 5 STRING-interaction edges
    assert len(graph["edges"]) == 7
    relationships = {e["relationship"] for e in graph["edges"]}
    assert relationships == {"reactome_pathway_comembership", "string_interaction"}


def test_med12_graph_neighbors_are_mediator_subunits(tmp_path, med12_snapshot):
    _write_snapshot(tmp_path, med12_snapshot)
    graph = mg.build_mechanism_graph("MED12", tmp_path)

    assert graph["available"] is True
    # Reactome was honestly unavailable (no ensembl id upstream in this
    # fixture) -- the graph still returns, with the partial-failure reason
    # surfaced rather than silently dropped.
    assert graph["reactome_status"] == "unavailable"
    assert graph["reason"] is not None and "reactome_pathways" in graph["reason"]
    assert graph["string_status"] == "ok"

    string_partners = {n["id"] for n in graph["nodes"] if n["type"] == "gene" and n["role"] == "string_partner"}
    mediator_subunits = {p for p in string_partners if p.startswith("MED")}
    assert len(mediator_subunits) >= 3
    # No pathway nodes at all, since Reactome was unavailable.
    assert not any(n["type"] == "pathway" for n in graph["nodes"])


def test_gene_with_no_cached_snapshot_is_honest_not_a_crash(tmp_path):
    graph = mg.build_mechanism_graph("SOMEUNCACHEDGENE", tmp_path)
    assert graph["available"] is False
    assert graph["nodes"] == []
    assert graph["edges"] == []
    assert "no cached pathway/network snapshot" in graph["reason"]


def test_empty_gene_query_is_honest():
    graph = mg.build_mechanism_graph("", "/tmp/does-not-matter")
    assert graph["available"] is False
    assert graph["nodes"] == []


def test_evidence_overlay_pulls_real_columns_never_fabricates_for_missing_gene(tmp_path, cd3e_snapshot):
    _write_snapshot(tmp_path, cd3e_snapshot)
    cards = pd.DataFrame(
        {
            "target": ["CD3E", "CD3E"],
            "condition": ["Rest", "Stim48hr"],
            "kd_status": ["confirmed", "confirmed"],
            "tractability_modality": ["antibody (surface)", "antibody (surface)"],
        }
    )
    readiness = pd.DataFrame(
        {
            "target": ["CD3E", "CD3E"],
            "condition": ["Rest", "Stim48hr"],
            "readiness_call": ["validate", "advance"],
            "overall_readiness_stage": ["R2", "R3"],
            "red_flag_override": ["none", "none"],
            "cd4_immune_red_flags": ["none", "none"],
        }
    )
    graph = mg.build_mechanism_graph("CD3E", tmp_path, cards=cards, readiness=readiness)
    by_id = {n["id"]: n for n in graph["nodes"]}

    center = by_id["CD3E"]
    assert center["evidence_available"] is True
    assert len(center["evidence"]) == 2
    conditions = {e["condition"] for e in center["evidence"]}
    assert conditions == {"Rest", "Stim48hr"}
    stim = next(e for e in center["evidence"] if e["condition"] == "Stim48hr")
    assert stim["readiness_call"] == "advance"
    assert stim["kd_status"] == "confirmed"
    assert stim["broad_effect_flag"] is False

    # SYK is a real STRING partner but is not in the cards/readiness tables
    # supplied above -- must never get a fabricated evidence value.
    syk = by_id["SYK"]
    assert syk["evidence_available"] is False
    assert "evidence" not in syk


def test_no_cards_or_readiness_supplied_gives_bare_graph(tmp_path, cd3e_snapshot):
    _write_snapshot(tmp_path, cd3e_snapshot)
    graph = mg.build_mechanism_graph("CD3E", tmp_path)
    for node in graph["nodes"]:
        if node["type"] == "gene":
            assert node["evidence_available"] is False


def test_mechanism_graph_api_endpoint_no_dataset():
    """TestClient smoke test for GET /api/mechanism-graph/{gene}, following the
    same read-only resolve-then-lookup pattern as /api/population-hypothesis/{gene}."""
    from fastapi.testclient import TestClient
    import target_card_api as api

    client = TestClient(api.app)
    # ZAP70 resolves via the gene resolver but has no committed _pathway
    # snapshot in this checkout (the 15 shortlist snapshots added in PR #11 do
    # not include it) -- so the endpoint must return an honest unavailable
    # response (never a 500, never a fabricated graph). Uses a snapshot-less
    # gene deliberately: CD3E and the other shortlist genes now DO have real
    # cached snapshots, so the available path is covered separately by
    # test_mechanism_graph_api_endpoint_reads_real_cache_dir.
    resp = client.get("/api/mechanism-graph/ZAP70")
    assert resp.status_code == 200
    body = resp.json()
    assert body["gene_query"] == "ZAP70"
    assert "resolution" in body
    assert body["available"] is False
    assert "reason" in body


def test_mechanism_graph_api_endpoint_unknown_dataset_id_is_404():
    from fastapi.testclient import TestClient
    import target_card_api as api

    client = TestClient(api.app)
    resp = client.get("/api/mechanism-graph/CD3E", params={"dataset_id": "not-a-real-dataset-id"})
    assert resp.status_code == 404


def test_mechanism_graph_api_endpoint_reads_real_cache_dir(tmp_path, cd3e_snapshot, monkeypatch):
    """Point the API's PATHWAY_CACHE_DIR at a fixture cache dir and confirm the
    endpoint plumbs a real cached snapshot through end to end."""
    from fastapi.testclient import TestClient
    import target_card_api as api
    # architecture refactor Phase 4: the mechanism-graph route handler now
    # lives in api/routers/mechanism.py and reads PATHWAY_CACHE_DIR via
    # `deps.PATHWAY_CACHE_DIR` module-attribute access, so the value must be
    # monkeypatched on api.deps (its true home) -- a plain attribute set on
    # target_card_api.py's shim or on api.app (both of which only hold a
    # separate re-exported snapshot import) would not be seen by the running
    # handler. See target_card_api.py's module docstring and
    # api/deps.py's module docstring for why.
    from api import deps as api_deps

    _write_snapshot(tmp_path, cd3e_snapshot)
    monkeypatch.setattr(api_deps, "PATHWAY_CACHE_DIR", tmp_path)

    client = TestClient(api.app)
    resp = client.get("/api/mechanism-graph/CD3E")
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    assert body["gene"] == "CD3E"
    node_ids = {n["id"] for n in body["nodes"]}
    assert {"CD247", "CD3D", "CD3G"}.issubset(node_ids)
