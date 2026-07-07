"""Unit tests for pathway_network_cache (Reactome + STRING, offline-batch)."""
import sys
sys.path.insert(0, "src/3_DE_analysis")

import pytest
import pathway_network_cache as pnc


def _network_available():
    try:
        r = pnc.fetch_string_network("CD3E")
        return r.get("source_status") == "ok"
    except Exception:
        return False


NETWORK_OK = _network_available()
pytestmark = pytest.mark.skipif(not NETWORK_OK, reason="Reactome/STRING unreachable from this environment")


def test_cd3e_reactome_hits_tcr_signaling():
    result = pnc.fetch_reactome_pathways("ENSG00000198851")
    assert result["source_status"] == "ok"
    names = [p["pathway_name"] for p in result["items"]]
    assert any("TCR" in n or "T cell" in n or "Lymphoid" in n for n in names)


def test_cd3e_string_network_includes_real_tcr_complex_partners():
    result = pnc.fetch_string_network("CD3E")
    assert result["source_status"] == "ok"
    partners = {p["partner"] for p in result["items"]}
    assert {"CD247", "CD3D", "CD3G"} & partners


def test_med12_string_network_dominated_by_mediator_complex():
    """Independent evidence for the C7 broad-effect quarantine: MED12's
    interaction partners should be other Mediator complex subunits, not
    immune-specific genes."""
    result = pnc.fetch_string_network("MED12")
    assert result["source_status"] == "ok"
    partners = {p["partner"] for p in result["items"]}
    mediator_subunits = {p for p in partners if p.startswith("MED")}
    assert len(mediator_subunits) >= 3


def test_no_ensembl_id_skips_reactome_honestly():
    cache_dir = "/tmp/test_pathway_cache_no_ensembl"
    snap = pnc.build_pathway_network_for_gene("SOMEGENE", None, cache_dir, force=True)
    assert snap["sources"]["reactome_pathways"]["source_status"] == "unavailable"
    assert "no ensembl_id" in snap["sources"]["reactome_pathways"]["reason"]
