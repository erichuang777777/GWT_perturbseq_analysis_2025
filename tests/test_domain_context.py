"""P2 — de-CD4-ize: domain context is overridable, defaults preserved."""

from __future__ import annotations

import importlib

import domain_context as dc
import evidence.external_cache as ec


def test_defaults_are_cd4(monkeypatch):
    for v in ("GWT_PUBMED_CONTEXT", "GWT_POSITIVE_CONTROLS", "GWT_OFF_CONTEXT_TISSUES", "GWT_ENABLE_CONCEPT_MODULES"):
        monkeypatch.delenv(v, raising=False)
    assert dc.pubmed_context() == "CD4 T cell"
    assert "Blood" in dc.off_context_tissues() and "Spleen" in dc.off_context_tissues()
    assert dc.concept_modules_enabled() is True
    # default positive controls come from the in-repo TCR set
    assert "ZAP70" in dc.positive_controls()


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("GWT_PUBMED_CONTEXT", "hepatocyte")
    monkeypatch.setenv("GWT_POSITIVE_CONTROLS", "FOO, BAR ,baz")
    monkeypatch.setenv("GWT_OFF_CONTEXT_TISSUES", "Liver,Kidney")
    monkeypatch.setenv("GWT_ENABLE_CONCEPT_MODULES", "0")
    assert dc.pubmed_context() == "hepatocyte"
    assert dc.positive_controls() == {"FOO", "BAR", "BAZ"}
    assert dc.off_context_tissues() == {"Liver", "Kidney"}
    assert dc.concept_modules_enabled() is False


def test_pubmed_query_uses_domain_context(monkeypatch):
    monkeypatch.setenv("GWT_PUBMED_CONTEXT", "hepatocyte")
    captured = {}

    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"esearchresult": {"count": "3", "idlist": []}}

    def fake_get(url, params=None, timeout=None):
        captured["term"] = params.get("term")
        return _Resp()

    monkeypatch.setattr(ec, "requests", type("R", (), {"get": staticmethod(fake_get)}))
    out = ec.fetch_pubmed_literature("ALB")  # context defaults to domain context
    assert "hepatocyte" in captured["term"]           # non-CD4 context threaded through
    assert "CD4" not in captured["term"]
    assert out["total_count"] == 3


def test_describe_shape():
    d = dc.describe()
    for k in ("pubmed_context", "positive_controls_count", "off_context_tissues", "concept_modules_enabled"):
        assert k in d
