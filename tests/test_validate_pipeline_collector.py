"""Smoke test for the read-only pipeline-validation collector (scripts/validate_pipeline.py).

The collector feeds docs/human_validation_protocol.md. It must (a) import and run
read-only without raising, and crucially (b) NOT crash on the legacy 31-column
reference dataset -- it must *report* the schema drift, not blow up on it. This
locks that "runs clean on real data, reports the legacy drift" behaviour that the
protocol's bootstrap depends on.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "validate_pipeline.py"


def test_collector_script_exists():
    assert SCRIPT.exists(), "scripts/validate_pipeline.py is missing"


def test_collector_runs_read_only_without_raising(capsys):
    """Executing the collector end-to-end must not raise -- including over the
    legacy 31-col dataset (it reports OF-1, never crashes)."""
    argv_backup = sys.argv[:]
    sys.argv = [str(SCRIPT)]
    try:
        # runpy executes the module's __main__ guard; SystemExit(0) is success.
        with pytest.raises(SystemExit) as exc:
            runpy.run_path(str(SCRIPT), run_name="__main__")
        assert exc.value.code == 0
    finally:
        sys.argv = argv_backup

    out = capsys.readouterr().out
    # It must have produced its headline collector banner and the thresholds block.
    assert "PIPELINE VALIDATION COLLECTOR" in out
    assert "LIVE THRESHOLDS" in out


def test_collector_reports_schema_drift_when_a_31col_dataset_is_present(capsys):
    """If the legacy 31-col dataset is on disk, the collector must surface OF-1
    (FAIL) rather than silently passing or raising. Skips if that dataset isn't
    checked out in this environment."""
    legacy = REPO / "sources" / "target_tool_cache" / "e7ecd8d5-5463-43e3-9bf1-6e8a15d3e137" / "target_cards.csv"
    if not legacy.exists():
        pytest.skip("legacy 31-col dataset not present in this checkout")

    argv_backup = sys.argv[:]
    sys.argv = [str(SCRIPT)]
    try:
        with pytest.raises(SystemExit):
            runpy.run_path(str(SCRIPT), run_name="__main__")
    finally:
        sys.argv = argv_backup

    out = capsys.readouterr().out
    assert "OF-1 schema drift" in out
    assert "FAIL" in out  # the legacy file must trip the drift line
