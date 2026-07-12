"""ClinicalTrials.gov offline-snapshot fallback -- deterministic, network-independent.

Unlike tests/test_disease_drug_evidence.py (network-gated), these force the live path to
fail via monkeypatch so they run identically whether or not clinicaltrials.gov is reachable
from this environment -- exercising the exact fallback path a blocked sandbox hits for real.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "3_DE_analysis"
sys.path.insert(0, str(SRC))

import evidence.external_cache as eec  # noqa: E402

_HAVE_SNAPSHOT = eec.CLINICALTRIALS_OFFLINE_SNAPSHOT_PATH.exists()


def _break_live_api(monkeypatch):
    """Force requests.get to raise, simulating an unreachable live API."""

    def _raise(*args, **kwargs):
        raise ConnectionError("simulated: live ClinicalTrials.gov API unreachable")

    monkeypatch.setattr(eec.requests, "get", _raise)


@pytest.mark.skipif(not _HAVE_SNAPSHOT, reason="topic13_clinicaltrials_flat.csv not present")
def test_known_drug_falls_back_to_offline_snapshot(monkeypatch):
    _break_live_api(monkeypatch)
    result = eec._clinicaltrials_count_for_drug("abatacept", "Rheumatoid Arthritis")
    assert result["source_status"] == "offline_snapshot"
    assert result["n_trials"] > 0
    assert "snapshot" in result["snapshot_note"].lower()


@pytest.mark.skipif(not _HAVE_SNAPSHOT, reason="topic13_clinicaltrials_flat.csv not present")
def test_offline_snapshot_never_masquerades_as_live():
    """source_status must be distinguishable from 'ok' -- never silently presented as live."""
    assert "offline_snapshot" != "ok"


@pytest.mark.skipif(not _HAVE_SNAPSHOT, reason="topic13_clinicaltrials_flat.csv not present")
def test_drug_outside_snapshot_coverage_falls_through_to_unavailable(monkeypatch):
    _break_live_api(monkeypatch)
    result = eec._clinicaltrials_count_for_drug("some_totally_unknown_drug_xyz", "some disease")
    assert result["source_status"] == "unavailable"
    assert result["n_trials"] is None


def test_live_api_success_path_is_unaffected(monkeypatch):
    """The offline fallback must never engage when the live call succeeds."""

    class _FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"totalCount": 7}

    monkeypatch.setattr(eec.requests, "get", lambda *a, **k: _FakeResp())
    result = eec._clinicaltrials_count_for_drug("abatacept", "Rheumatoid Arthritis")
    assert result == {"source_status": "ok", "n_trials": 7}


def test_missing_snapshot_file_degrades_honestly(tmp_path, monkeypatch):
    monkeypatch.setattr(eec, "CLINICALTRIALS_OFFLINE_SNAPSHOT_PATH", tmp_path / "does_not_exist.csv")
    monkeypatch.setattr(eec, "_OFFLINE_SNAPSHOT_LOADED", False)
    monkeypatch.setattr(eec, "_OFFLINE_SNAPSHOT_CACHE", {})
    _break_live_api(monkeypatch)
    result = eec._clinicaltrials_count_for_drug("abatacept", "Rheumatoid Arthritis")
    assert result["source_status"] == "unavailable"
