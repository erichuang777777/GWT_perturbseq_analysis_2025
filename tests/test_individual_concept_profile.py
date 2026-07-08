"""P2/P3 tests for individual_concept_profile.py + the request-only endpoint.

Covers (plan §7):
  (a) projection correctness on the REAL Th2-vs-Th1 signature (M08 up, M07 opposite);
  (b) honest coverage reporting;
  (c) unknown != 0 for a concept with no overlapping genes;
  (d) fixed non-empty caveat on every report;
  (e) no-persist audit: the endpoint writes NO new file under target_tool_cache/;
  (f) the concept profile never changes readiness_call/overall_readiness_stage.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src" / "3_DE_analysis"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import individual_concept_profile as icp

TH2_SIGNATURE_CSV = (
    REPO_ROOT / "src" / "4_polarization_signatures" / "results" / "combined_Th2_vs_Th1_signature.csv"
)
CACHE_ROOT = REPO_ROOT / "sources" / "target_tool_cache"


def _load_th2_sample() -> dict:
    """The real Th2-vs-Th1 signature as a {gene: signed_score} sample vector.

    A Th2-vs-Th1 contrast IS effectively a sample shifted toward Th2, so
    projecting it must light up M08 (Th2) and push M07 (Th1) the other way.
    """
    df = pd.read_csv(TH2_SIGNATURE_CSV)
    zcols = ["zscore_hollbacher", "zscore_ota", "zscore_Diff043"]
    df = df.dropna(subset=["gene_name"]).drop_duplicates(subset=["gene_name"])
    score = df[zcols].mean(axis=1, skipna=True)
    return {str(g): float(s) for g, s in zip(df["gene_name"], score) if not np.isnan(s)}


# --- (a) projection correctness -------------------------------------------------


def test_th2_signature_lights_up_th2_and_reverses_th1():
    modules = icp.load_concept_modules()
    assert len(modules) == 20
    sample = _load_th2_sample()
    profile = icp.project_sample_onto_concepts(sample, modules)
    by_id = {p["module_id"]: p for p in profile}

    m08 = by_id["M08"]  # Th2_Polarization
    m07 = by_id["M07"]  # Th1_Polarization

    assert m08["module_name"] == "Th2_Polarization"
    assert m07["module_name"] == "Th1_Polarization"

    # Th2 concept is clearly activated (positive) in a Th2-shifted sample.
    assert m08["activation"] is not None and m08["activation"] > 1.0
    assert m08["direction"] == "up"
    # Th1 concept is pushed the opposite way (negative), and much lower than Th2.
    assert m07["activation"] is not None and m07["activation"] < 0.0
    assert m07["direction"] == "down"
    assert m08["activation"] - m07["activation"] > 2.0
    # Both are flagged aberrant at the default threshold.
    assert m08["aberrant"] and m07["aberrant"]


# --- (b) honest coverage --------------------------------------------------------


def test_coverage_reported_honestly():
    modules = icp.load_concept_modules()
    sample = _load_th2_sample()
    profile = icp.project_sample_onto_concepts(sample, modules)
    for p in profile:
        # coverage is exactly the present/seed fraction -- hand-checkable.
        assert p["coverage"] == pytest.approx(p["n_present_genes"] / p["n_seed_genes"])
        assert 0.0 <= p["coverage"] <= 1.0
        assert len(p["present_genes"]) == p["n_present_genes"]

    by_id = {p["module_id"]: p for p in profile}
    # M08 seed = {GATA3,IL4,IL13,IL4R,STAT6,IRF4}; IL4 is absent from the
    # signature file, so coverage is honestly 5/6, not silently 1.0.
    m08 = by_id["M08"]
    assert m08["n_seed_genes"] == 6
    assert 0 < m08["n_present_genes"] < 6
    assert "IL4" not in m08["present_genes"]


# --- (c) unknown != 0 -----------------------------------------------------------


def test_concept_with_no_overlap_is_unknown_never_zero():
    modules = icp.load_concept_modules()
    # A sample whose genes match NO module seed gene at all.
    sample = {"FAKEGENE_AAA": 3.14, "FAKEGENE_BBB": -2.71, "FAKEGENE_CCC": 0.5}
    profile = icp.project_sample_onto_concepts(sample, modules)
    assert profile  # 20 concepts still returned
    for p in profile:
        assert p["n_present_genes"] == 0
        assert p["coverage"] == 0.0
        assert p["direction"] == "unknown"
        # The headline invariant: missing concept is NOT a zero concept.
        assert p["activation"] is None
        assert p["activation"] != 0
        assert p["aberrant"] is False


# --- (d) fixed non-empty caveat -------------------------------------------------


def test_every_report_carries_a_nonempty_caveat():
    modules = icp.load_concept_modules()
    sample = _load_th2_sample()
    report = icp.build_individual_concept_report(sample, modules=modules, computed_at="2026-07-08T00:00:00+00:00")
    assert isinstance(report["caveat"], str) and report["caveat"].strip()
    assert "NOT diagnosis" in report["caveat"]
    # Even an empty/degenerate input still returns the fixed caveat.
    empty_report = icp.build_individual_concept_report({}, modules=modules, computed_at="2026-07-08T00:00:00+00:00")
    assert empty_report["caveat"] == icp.CAVEAT_TEXT
    assert empty_report["caveat"].strip()
    # computed_at is passed in, never stamped inside the pure builder.
    assert report["provenance"]["computed_at"] == "2026-07-08T00:00:00+00:00"


# --- (e) no-persist audit -------------------------------------------------------


def _snapshot_cache_files() -> set:
    if not CACHE_ROOT.exists():
        return set()
    return {str(p) for p in CACHE_ROOT.rglob("*") if p.is_file()}


def test_endpoint_persists_nothing_under_target_tool_cache():
    from fastapi.testclient import TestClient
    import target_card_api as api

    client = TestClient(api.app)
    sample = _load_th2_sample()

    before = _snapshot_cache_files()
    resp = client.post("/api/individual-concept-profile", json=sample)
    after = _snapshot_cache_files()

    assert resp.status_code == 200
    body = resp.json()
    assert body["caveat"].strip()
    assert len(body["concept_profile"]) == 20
    # The raw input expression vector must never be written to disk.
    assert after == before, f"endpoint created files: {sorted(after - before)}"


def test_endpoint_with_dataset_id_still_persists_nothing():
    from fastapi.testclient import TestClient
    import target_card_api as api

    # Only run against a real built dataset if one is present in this checkout.
    dataset_dirs = [
        d for d in CACHE_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "target_cards.csv").exists()
    ] if CACHE_ROOT.exists() else []
    if not dataset_dirs:
        pytest.skip("no built dataset with target_cards.csv in this checkout")
    dataset_id = dataset_dirs[0].name

    client = TestClient(api.app)
    sample = _load_th2_sample()
    before = _snapshot_cache_files()
    resp = client.post("/api/individual-concept-profile", params={"dataset_id": dataset_id}, json=sample)
    after = _snapshot_cache_files()

    assert resp.status_code == 200
    assert after == before, f"endpoint created files: {sorted(after - before)}"


# --- (f) descriptive-only: never changes readiness -----------------------------


def test_hypotheses_read_readiness_verbatim_never_recompute():
    """connect_concepts_to_screen_targets must ECHO the readiness_call it is
    handed, not derive a new one -- proving the concept profile is read-only
    with respect to the readiness path."""
    modules = icp.load_concept_modules()
    # Aberrant M08 concept, with GATA3 (an M08 seed gene) as a screened target.
    profile = [
        {"module_id": "M08", "module_name": "Th2_Polarization", "activation": 2.5,
         "coverage": 1.0, "direction": "up", "aberrant": True},
    ]
    cards = pd.DataFrame({"target": ["GATA3"], "condition": ["Stim48hr"], "ontarget_effect_size": [-12.3]})
    sentinel = "SENTINEL_CALL_DO_NOT_RECOMPUTE"
    readiness = pd.DataFrame({
        "target": ["GATA3"], "condition": ["Stim48hr"],
        "readiness_call": [sentinel], "overall_readiness_stage": ["R9_SENTINEL"],
    })
    hyps = icp.connect_concepts_to_screen_targets(profile, cards, readiness, modules=modules)
    assert len(hyps) == 1
    h = hyps[0]
    assert h["gene"] == "GATA3"
    assert h["readiness_call"] == sentinel  # echoed verbatim, not recomputed
    assert h["overall_readiness_stage"] == "R9_SENTINEL"
    assert h["screen_direction"] == "down"  # sign of ontarget_effect_size
    assert h["caveat"].strip()


def test_endpoint_does_not_mutate_existing_readiness_csv():
    from fastapi.testclient import TestClient
    import target_card_api as api

    dataset_dirs = [
        d for d in CACHE_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "readiness.csv").exists()
    ] if CACHE_ROOT.exists() else []
    if not dataset_dirs:
        pytest.skip("no built dataset with readiness.csv in this checkout")
    readiness_csv = dataset_dirs[0] / "readiness.csv"
    dataset_id = dataset_dirs[0].name

    before_bytes = readiness_csv.read_bytes()
    client = TestClient(api.app)
    resp = client.post("/api/individual-concept-profile", params={"dataset_id": dataset_id}, json=_load_th2_sample())
    assert resp.status_code == 200
    # The endpoint only READS readiness -- the file must be byte-identical after.
    assert readiness_csv.read_bytes() == before_bytes


def test_report_never_emits_a_top_level_readiness_decision():
    """The concept report is a separate output: it must not surface a
    readiness_call/overall_readiness_stage as if the profile produced one."""
    modules = icp.load_concept_modules()
    report = icp.build_individual_concept_report(_load_th2_sample(), modules=modules, computed_at="t")
    assert "readiness_call" not in report
    assert "overall_readiness_stage" not in report
    assert "statistical_evidence_grade" not in report
