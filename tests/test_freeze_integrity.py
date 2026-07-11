"""Release-freeze guards.

These lock in the freeze deliverables so a future edit that silently breaks them
fails CI:
- every asset pinned in FREEZE_MANIFEST.csv still matches its frozen md5
  (`scripts/freeze_pipeline.py` exits 0);
- the per-stage EDA reports are regenerable and up to date
  (`scripts/generate_stage_eda.py --check` exits 0);
- the OF-1 resolution holds: the 39-col build is canonical and the legacy 31-col
  build is flagged deprecated by the dataset listing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, cwd=str(REPO),
    )


@pytest.mark.skipif(
    not (REPO / "docs/mvp-research/pipeline/FREEZE_MANIFEST.csv").exists(),
    reason="freeze manifest not present",
)
def test_freeze_manifest_pins_all_verify():
    proc = _run("freeze_pipeline.py")
    assert proc.returncode == 0, f"freeze drift detected:\n{proc.stdout}\n{proc.stderr}"
    assert "0 drifted, 0 missing" in proc.stdout


def test_stage_eda_reports_are_up_to_date():
    proc = _run("generate_stage_eda.py", "--check")
    assert proc.returncode == 0, (
        "EDA reports are stale — run `python scripts/generate_stage_eda.py`:\n" + proc.stdout
    )


def test_of1_canonical_and_legacy_flags():
    sys.path.insert(0, str(REPO / "src" / "3_DE_analysis"))
    from api.routers.build import (  # noqa: E402
        CANONICAL_DATASET_ID,
        DEPRECATED_DATASET_IDS,
        list_datasets,
    )

    records = {r["dataset_id"]: r for r in list_datasets()}
    if CANONICAL_DATASET_ID in records:
        assert records[CANONICAL_DATASET_ID]["canonical"] is True
        assert records[CANONICAL_DATASET_ID]["deprecated"] is False
    for legacy in DEPRECATED_DATASET_IDS:
        if legacy in records:
            assert records[legacy]["deprecated"] is True
            assert records[legacy]["canonical"] is False
    # Canonical must never sort after a deprecated dataset (default-pick safety).
    order = [r["dataset_id"] for r in list_datasets()]
    if CANONICAL_DATASET_ID in order:
        canon_idx = order.index(CANONICAL_DATASET_ID)
        for legacy in DEPRECATED_DATASET_IDS:
            if legacy in order:
                assert canon_idx < order.index(legacy)
