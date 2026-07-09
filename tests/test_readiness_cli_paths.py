"""Regression lock for the readiness CLI cwd-footgun fix (exploration follow-up B).

The CLI ``__main__`` default overlay paths are anchored to the repo root (via
``_REPO_ROOT = Path(__file__).resolve().parents[3]``), NOT the process cwd, so
``python -m core.readiness cards.csv`` loads the druggability / essentials /
broad-effect gene sets from any directory. Before the fix, running from any cwd
other than the repo root silently loaded ZERO overlays (missing files degrade to
``"unknown"`` with no error), collapsing the advance tier (495 -> 22 in the real
data). These tests pin:

  1. ``_REPO_ROOT`` is cwd-independent and its anchored default paths resolve to
     real files.
  2. The CLI emits a loud ``RuntimeWarning`` when it still loads zero overlays,
     yet never crashes (honest-degradation preserved).

The warning lives ONLY at the CLI call site, never inside the shared
``load_overlays`` (which the API also calls and must keep quiet).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src" / "3_DE_analysis"
REAL_CARDS = REPO / "sources" / "target_tool_cache" / "a6bba17b-f194-4a50-8cf8-96e03eededd6" / "target_cards.csv"


def test_repo_root_is_cwd_independent_and_anchors_real_files(tmp_path, monkeypatch):
    """_REPO_ROOT is derived from __file__ (not cwd) and its default overlay
    paths point at files that actually exist -- the core of the footgun fix."""
    sys.path.insert(0, str(SRC))
    from core.readiness import _REPO_ROOT

    # Move cwd somewhere unrelated: _REPO_ROOT must not move with it.
    monkeypatch.chdir(tmp_path)
    assert _REPO_ROOT == REPO
    assert (_REPO_ROOT / "metadata" / "gene_lists").is_dir()
    assert (_REPO_ROOT / "metadata" / "gene_lists" / "core_essentials_hart.tsv").exists()
    assert (_REPO_ROOT / "sources" / "broad_effect_genes.txt").exists()


def _tiny_cards(tmp_path) -> Path:
    """A small real-schema cards slice (fast to score) written under tmp."""
    df = pd.read_csv(REAL_CARDS, nrows=30)
    out = tmp_path / "tiny_cards.csv"
    df.to_csv(out, index=False)
    return out


def _run_cli(cards: Path, cwd: Path, extra_args: list[str]) -> subprocess.CompletedProcess:
    env = {"PYTHONPATH": str(SRC), "PYTHONWARNINGS": "default"}
    import os

    full_env = {**os.environ, **env}
    return subprocess.run(
        [sys.executable, "-m", "core.readiness", str(cards), *extra_args],
        cwd=str(cwd),
        env=full_env,
        capture_output=True,
        text=True,
        timeout=180,
    )


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_cli_loads_overlays_from_foreign_cwd_without_warning(tmp_path):
    """Run the CLI from an unrelated cwd with default (anchored) paths: it must
    succeed and NOT emit the zero-overlay warning -- proving the anchoring
    actually loads the gene sets regardless of where the process starts."""
    cards = _tiny_cards(tmp_path)
    proc = _run_cli(cards, cwd=tmp_path, extra_args=[])
    assert proc.returncode == 0, proc.stderr
    assert "returned 0 gene sets" not in proc.stderr


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_cli_warns_loudly_but_does_not_crash_on_zero_overlays(tmp_path):
    """Point --gene-lists at a nonexistent dir: the CLI must WARN (no longer
    silent) yet still exit 0 -- the honest-degradation contract is preserved,
    the failure is just made visible."""
    cards = _tiny_cards(tmp_path)
    proc = _run_cli(cards, cwd=tmp_path, extra_args=["--gene-lists", str(tmp_path / "nonexistent")])
    assert proc.returncode == 0, proc.stderr
    assert "returned 0 gene sets" in proc.stderr
    assert "advance tier will be under-called" in proc.stderr
