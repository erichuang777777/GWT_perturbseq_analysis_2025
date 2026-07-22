"""Tests for the PubMed literature-count -> novelty descriptor (plan P0-E).

Covers the pure ``novelty_from_literature_count`` mapping and that
``fetch_pubmed_literature`` threads through a real ``total_count`` +
``novelty`` block, honestly distinguishing a measured 0 (``no_record``)
from a failed fetch (``unknown``). Network is stubbed -- no live calls.
"""

from __future__ import annotations

import evidence.external_cache as ec


def test_novelty_tiers_are_absolute_and_monotonic():
    # unknown != 0: a missing measurement is "unknown", never a fabricated 0.
    assert ec.novelty_from_literature_count(None)["tier"] == "unknown"
    assert ec.novelty_from_literature_count(None)["novelty_score"] is None

    # a genuine measured zero is the most-novel end, but distinct from unknown.
    zero = ec.novelty_from_literature_count(0)
    assert zero["tier"] == "no_record"
    assert zero["novelty_score"] == 1.0

    assert ec.novelty_from_literature_count(5)["tier"] == "understudied"
    assert ec.novelty_from_literature_count(10)["tier"] == "understudied"
    assert ec.novelty_from_literature_count(11)["tier"] == "moderate"
    assert ec.novelty_from_literature_count(100)["tier"] == "moderate"
    assert ec.novelty_from_literature_count(101)["tier"] == "well_studied"

    # HIGHER score = more novel (fewer papers): strictly decreasing in count.
    scores = [ec.novelty_from_literature_count(c)["novelty_score"] for c in (1, 10, 100, 1000)]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 < s <= 1.0 for s in scores)


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_fetch_pubmed_threads_total_count(monkeypatch):
    """esearch ``count`` (the true hit total) is captured even when only a few
    ids are pulled back, and surfaces as a novelty tier."""

    def fake_get(url, params=None, timeout=None):
        if url == ec.PUBMED_ESEARCH_API:
            # 37 total hits, but esearch only returns the first 2 ids.
            return _Resp({"esearchresult": {"count": "37", "idlist": ["1", "2"]}})
        return _Resp({"result": {"1": {"title": "A", "pubdate": "2020"}, "2": {"title": "B", "pubdate": "2021"}}})

    monkeypatch.setattr(ec, "requests", type("R", (), {"get": staticmethod(fake_get)}))
    out = ec.fetch_pubmed_literature("ZAP70")
    assert out["source_status"] == "ok"
    assert out["total_count"] == 37
    assert out["novelty"]["tier"] == "moderate"
    assert len(out["items"]) == 2


def test_fetch_pubmed_zero_hits_is_no_record(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return _Resp({"esearchresult": {"count": "0", "idlist": []}})

    monkeypatch.setattr(ec, "requests", type("R", (), {"get": staticmethod(fake_get)}))
    out = ec.fetch_pubmed_literature("OBSCUREGENE1")
    assert out["source_status"] == "ok"
    assert out["total_count"] == 0
    assert out["novelty"]["tier"] == "no_record"
    assert out["items"] == []


def test_fetch_pubmed_network_failure_is_unknown_not_zero(monkeypatch):
    def boom(url, params=None, timeout=None):
        raise RuntimeError("network blocked")

    monkeypatch.setattr(ec, "requests", type("R", (), {"get": staticmethod(boom)}))
    out = ec.fetch_pubmed_literature("ZAP70")
    assert out["source_status"] == "unavailable"
    # A failed fetch must NOT masquerade as a measured novelty.
    assert "total_count" not in out
