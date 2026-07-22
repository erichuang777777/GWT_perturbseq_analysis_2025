"""Tests for the pre-flight QC gate (development plan P2-A)."""

from __future__ import annotations

import pandas as pd

from upload.import_manager import qc_preflight


def _check(report, key):
    return next(c for c in report["checks"] if c["key"] == key)


def test_healthy_upload_passes():
    df = pd.DataFrame({
        "gene": ["A", "B", "C"],
        "n_cells": [500, 600, 700],
        "n_total_de_genes": [80, 120, 90],
        "n_guides": [4, 4, 4],
        "donor": ["d1", "d2", "d3"],
    })
    r = qc_preflight(df, "target_evidence")
    assert r["gate"] == "pass"
    assert _check(r, "n_cells")["status"] == "pass"
    assert _check(r, "n_donors")["n_donors"] == 3


def test_low_cells_median_blocks():
    df = pd.DataFrame({"gene": ["A", "B"], "n_cells": [50, 80], "n_total_de_genes": [80, 90]})
    r = qc_preflight(df, "target_evidence", min_cells=200)
    assert r["gate"] == "block"
    assert _check(r, "n_cells")["status"] == "block"


def test_some_below_floor_warns():
    df = pd.DataFrame({"gene": ["A", "B", "C"], "n_cells": [500, 600, 50], "n_total_de_genes": [80, 90, 100]})
    r = qc_preflight(df, "target_evidence", min_cells=200)
    assert r["gate"] == "warn"
    assert _check(r, "n_cells")["n_below_floor"] == 1


def test_absent_gate_column_is_unknown_not_zero():
    # No n_cells column at all — must be "unknown", never scored as a fail/pass 0.
    df = pd.DataFrame({"gene": ["A", "B"], "n_total_de_genes": [80, 90]})
    r = qc_preflight(df, "target_evidence")
    cells = _check(r, "n_cells")
    assert cells["present"] is False and cells["status"] == "unknown"


def test_guideless_upload_flags_not_assessed():
    df = pd.DataFrame({"gene": ["A"], "n_cells": [500], "n_total_de_genes": [80]})
    r = qc_preflight(df, "target_evidence")
    guides = _check(r, "n_guides")
    assert guides["present"] is False and guides["status"] == "unknown"


def test_single_donor_warns():
    df = pd.DataFrame({"gene": ["A", "B"], "n_cells": [500, 600], "n_total_de_genes": [80, 90], "donor": ["d1", "d1"]})
    r = qc_preflight(df, "target_evidence")
    assert _check(r, "n_donors")["n_donors"] == 1
    assert r["gate"] == "warn"


def test_empty_preview_is_unknown_gate():
    assert qc_preflight(None, "target_evidence")["gate"] == "unknown"
    assert qc_preflight(pd.DataFrame(), "target_evidence")["gate"] == "unknown"
