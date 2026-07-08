"""OpenAPI-metadata enrichment (server north-star Phase 1, decision-invariant).

Pins the /docs + /redoc-facing OpenAPI schema: rich app-level metadata
(description, summary, license, contact), a documented tag group per resource
area, and every endpoint assigned to exactly one declared group. This is a
docs-only surface -- these tests must NOT assert anything about response
bodies (Phase 1 changed no payload shape).
"""
from __future__ import annotations


def _schema():
    import target_card_api as api

    return api.app.openapi()


def test_app_level_metadata_is_populated():
    info = _schema()["info"]
    assert info["title"] == "GWT Target Card API"
    assert info["version"] == "0.2.0"
    assert info.get("summary")
    # research-use / not-clinical + unknown!=0 discipline surfaced to API consumers
    desc = info.get("description") or ""
    assert "NOT clinical software" in desc
    assert "`unknown` != `0`" in desc or "unknown` != `0" in desc
    assert info.get("license")  # license_info block present (GWT dataset TBD disclosed)
    assert info.get("contact")


def test_every_endpoint_has_exactly_one_declared_tag_group():
    schema = _schema()
    declared = {t["name"] for t in schema.get("tags", [])}
    assert declared, "expected documented OpenAPI tag groups"
    offenders = []
    for path, methods in schema["paths"].items():
        for method, op in methods.items():
            tags = op.get("tags", [])
            if len(tags) != 1 or tags[0] not in declared:
                offenders.append((path, method, tags))
    assert offenders == [], f"endpoints with missing/duplicate/undeclared tag: {offenders}"


def test_key_resource_groups_are_present():
    declared = {t["name"] for t in _schema().get("tags", [])}
    for expected in {"System", "Target cards", "Readiness", "External evidence", "Concept profile (demo)"}:
        assert expected in declared


def test_tag_groups_all_have_descriptions():
    for t in _schema().get("tags", []):
        assert t.get("description"), f"tag group {t['name']!r} missing a description"


def test_health_surfaces_versions_additively():
    """/api/health keeps its pre-existing status + capabilities keys (existing
    callers unaffected) and additively surfaces engine/dataset/schema versions
    so an API consumer can tell what release they are querying."""
    from fastapi.testclient import TestClient
    import target_card_api as api

    body = TestClient(api.app).get("/api/health").json()
    assert "status" in body and "capabilities" in body  # unchanged, additive
    v = body["versions"]
    assert v["api"] == "0.2.0"
    for key in ("engine_version", "dataset_version", "schema_version"):
        assert v.get(key)  # non-empty real provenance value
