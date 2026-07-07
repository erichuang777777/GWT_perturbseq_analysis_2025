"""Unit tests for match_disease_drug_evidence (Module 3, part B).

Network-dependent (calls the public Open Targets / ClinicalTrials.gov APIs
directly, consistent with external_evidence_cache.py's existing design).
Skipped automatically if outbound network is unavailable.
"""
import sys
sys.path.insert(0, "src/3_DE_analysis")

import pytest
import external_evidence_cache as eec


def _network_available():
    try:
        r = eec._open_targets_resolve_ensembl_id("IL2RA")
        return r is not None
    except Exception:
        return False


NETWORK_OK = _network_available()
pytestmark = pytest.mark.skipif(not NETWORK_OK, reason="Open Targets API unreachable from this environment")


def test_known_gene_known_disease_returns_available():
    result = eec.match_disease_drug_evidence("IL2RA", "rheumatoid arthritis")
    assert result["available"] is True
    assert result["n_known_drugs_for_gene"] > 0
    assert "caveat" in result and "not a treatment recommendation" in result["caveat"]


def test_drug_real_indication_shows_nonzero_trials_wrong_indication_shows_zero():
    """basiliximab is approved for kidney-transplant rejection, not RA. The
    function must not hide or smooth over that mismatch."""
    result = eec.match_disease_drug_evidence("IL2RA", "rheumatoid arthritis")
    basiliximab = next((d for d in result["drugs"] if d["drug_name"] == "BASILIXIMAB"), None)
    assert basiliximab is not None
    assert basiliximab["trials_for_this_disease"]["n_trials"] == 0

    result2 = eec.match_disease_drug_evidence("IL2RA", "kidney transplant")
    basiliximab2 = next((d for d in result2["drugs"] if d["drug_name"] == "BASILIXIMAB"), None)
    assert basiliximab2["trials_for_this_disease"]["n_trials"] > 0


def test_gene_with_no_known_drugs_returns_available_with_zero_drugs():
    result = eec.match_disease_drug_evidence("PLCG1", "systemic lupus erythematosus")
    assert result["available"] is True
    assert result["n_known_drugs_for_gene"] == 0
    assert result["drugs"] == []


def test_unknown_gene_returns_unavailable_not_fabricated():
    result = eec.match_disease_drug_evidence("NOTAREALGENE123", "rheumatoid arthritis")
    assert result["available"] is False
    assert "not found" in result["reason"]
