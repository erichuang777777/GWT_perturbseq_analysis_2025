"""Whole-repo freeze + isolation guards (unified v2).

Locks in the 9-phase structuralization so a future edit that silently moves a
module's frozen content — or contaminates a neighbouring phase — fails CI.

- `test_unified_freeze_verifies`: every module in FREEZE_MANIFEST_UNIFIED.csv
  still matches its pinned freeze value (`validate_freeze_unified.py` exits 0).
- `test_partition_is_disjoint`: no repo file is owned by two modules (isolation
  by construction — editing one module cannot move another's value).
- `test_partition_is_total`: every repo file (except the manifest itself) has
  exactly one owning module (no orphan files outside the structure).
"""
from __future__ import annotations

import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "validate_freeze_unified.py"
MANIFEST = REPO / "docs" / "structure" / "FREEZE_MANIFEST_UNIFIED.csv"

pytestmark = pytest.mark.skipif(
    not (SCRIPT.exists() and MANIFEST.exists()),
    reason="unified freeze manifest/script not present",
)


def _load_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("vfu", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_unified_freeze_verifies():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, cwd=str(REPO)
    )
    assert proc.returncode == 0, f"freeze drift / contamination:\n{proc.stdout}\n{proc.stderr}"
    assert "0 unexpected drift" in proc.stdout and "0 missing" in proc.stdout


def test_partition_is_disjoint():
    vfu = _load_module()
    import csv
    rows = list(csv.DictReader(open(MANIFEST)))
    owned = vfu.partition(rows)
    counts = Counter(str(f) for files in owned.values() for f in files)
    dupes = {f: c for f, c in counts.items() if c > 1}
    assert not dupes, f"{len(dupes)} files owned by >1 module (isolation broken): {list(dupes)[:5]}"


def test_partition_is_total():
    vfu = _load_module()
    import csv
    rows = list(csv.DictReader(open(MANIFEST)))
    owned = vfu.partition(rows)
    claimed = {str(f) for files in owned.values() for f in files}
    allf = {str(f) for f in vfu._all_repo_files()}
    orphans = allf - claimed
    # the manifest cannot freeze its own hash; that one file is the only allowed orphan
    orphans = {o for o in orphans if not o.endswith("FREEZE_MANIFEST_UNIFIED.csv")}
    assert not orphans, f"{len(orphans)} repo files outside the module structure: {list(orphans)[:5]}"
