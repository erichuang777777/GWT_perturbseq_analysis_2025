"""Tests for the WP3 one-command validation report runner
(src/3_DE_analysis/validation/run_all_validation.py).

These tests run the recompute functions against the REAL in-repo CSVs under
docs/mvp-research/level4_external_validation/ (they are present in this
checkout), and assert the documented expected values from
docs/perturbation_validation_plan.md / LEVEL4_EXTERNAL_VALIDATION.md.

If a required CSV is genuinely absent from a checkout, the corresponding
assertion is skipped (not hard-failed) -- matching the runner's own
honest-degradation contract (status="skipped", never a fabricated number).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from validation.run_all_validation import (
    DEFAULT_TARGET_SET,
    DEFAULT_TRACK_A,
    DEFAULT_TRACK_B,
    DEFAULT_TRACK_C,
    build_manifest,
    recompute_l4,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_PATHS = {
    "target_set": DEFAULT_TARGET_SET,
    "track_a": DEFAULT_TRACK_A,
    "track_b": DEFAULT_TRACK_B,
    "track_c": DEFAULT_TRACK_C,
}


@pytest.fixture(scope="module")
def l4_results():
    return recompute_l4(DEFAULT_PATHS)


def test_track_a_immune_assoc_count(l4_results):
    r = l4_results["track_a_immune_assoc"]
    if r.status == "skipped":
        pytest.skip(f"track_a CSV missing: {r.source_file}")
    assert r.value == "26/55"
    assert r.match == "MATCH"


def test_track_a_autoimmune_count(l4_results):
    r = l4_results["track_a_autoimmune"]
    if r.status == "skipped":
        pytest.skip(f"track_a CSV missing: {r.source_file}")
    assert r.value == "22/55"
    assert r.match == "MATCH"


def test_track_c_coverage(l4_results):
    r = l4_results["track_c_coverage"]
    if r.status == "skipped":
        pytest.skip(f"track_c / target_set CSV missing: {r.source_file}")
    assert r.value == "52/55"
    assert r.match == "MATCH"


def test_track_b_vav1_recovery_rounds_to_62(l4_results):
    r = l4_results["track_b_vav1_recovery"]
    if r.status == "skipped":
        pytest.skip(f"track_b CSV missing / VAV1 not found: {r.source_file}")
    assert r.value.startswith("62%")
    assert r.match == "MATCH"


def test_track_b_cd3e_recovery_rounds_to_58(l4_results):
    r = l4_results["track_b_cd3e_recovery"]
    if r.status == "skipped":
        pytest.skip(f"track_b CSV missing / CD3E not found: {r.source_file}")
    assert r.value.startswith("58%")
    assert r.match == "MATCH"


def test_all_input_csvs_present_in_this_checkout():
    """Sanity check documenting that this checkout is expected to have all
    four input CSVs -- if this fails, the skips above are the honest,
    expected behaviour rather than a bug.
    """
    for key, path in DEFAULT_PATHS.items():
        assert Path(path).exists(), f"expected {key} CSV to exist at {path}"


def test_build_manifest_has_five_ladder_levels_with_expected_statuses(l4_results):
    rows = build_manifest(l4_results)
    ladder_keys = [
        "L1_reproducibility",
        "L2_statistical_robustness",
        "L3_internal_directional_consistency",
        "L4_orthogonal_computational_validation",
        "L5_wet_lab_validation",
    ]
    by_key = {r["level_or_check"]: r for r in rows}

    for key in ladder_keys:
        assert key in by_key, f"missing ladder level {key} in manifest"

    statuses = [by_key[key]["status"] for key in ladder_keys]
    assert statuses == ["met", "met", "met", "partial", "gap"]


def test_build_manifest_has_calibration_entry(l4_results):
    rows = build_manifest(l4_results)
    by_key = {r["level_or_check"]: r for r in rows}
    assert "calibration" in by_key
    calibration = by_key["calibration"]
    assert calibration["status"] == "met"
    assert "AUROC" in calibration["metric"]
    assert "technical_methods.md" in calibration["source_file"]


def test_build_manifest_includes_l4_sub_checks_traceable_to_source_csvs(l4_results):
    rows = build_manifest(l4_results)
    by_key = {r["level_or_check"]: r for r in rows}
    l4_sub_keys = [
        "L4_track_a_immune_assoc",
        "L4_track_a_autoimmune",
        "L4_track_b_vav1_recovery",
        "L4_track_b_cd3e_recovery",
        "L4_track_c_coverage",
    ]
    for key in l4_sub_keys:
        assert key in by_key
        assert by_key[key]["source_file"], f"{key} must carry a source_file"


def test_recompute_l4_skips_honestly_when_csv_missing(tmp_path):
    """Feed a nonexistent path and confirm the check is marked 'skipped' with
    a reason, never fabricated.
    """
    missing_path = tmp_path / "does_not_exist.csv"
    paths = dict(DEFAULT_PATHS)
    paths["track_a"] = missing_path

    results = recompute_l4(paths)

    assert results["track_a_immune_assoc"].status == "skipped"
    assert results["track_a_immune_assoc"].value is None
    assert "MISSING" in results["track_a_immune_assoc"].source_file
    assert results["track_a_autoimmune"].status == "skipped"
