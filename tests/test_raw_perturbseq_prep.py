"""P3 — accept raw scRNA: h5ad -> portal CSVs (pure DE core tested without anndata)."""

from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd
import pytest

import raw_perturbseq_prep as prep
import signed_de_io


def _synthetic():
    """3 genes; 20 control cells, 20 cells where target TA drives G0 up and G1 down."""
    rng = np.random.RandomState(0)
    n = 20
    # small biological noise so the Welch t-test is well-defined (non-degenerate)
    ctrl = 5.0 + rng.normal(0, 0.3, (n, 3))                       # baseline ~5
    ta = np.column_stack([                                        # TA perturbs G0 up, G1 down
        20.0 + rng.normal(0, 0.3, n),
        1.0 + rng.normal(0, 0.1, n),
        5.0 + rng.normal(0, 0.3, n),
    ])
    X = np.vstack([ctrl, ta]).clip(min=0)
    genes = ["G0", "G1", "G2"]
    targets = ["NTC"] * n + ["TA"] * n
    return X, genes, targets


def test_pseudobulk_de_directions_and_counts():
    X, genes, targets = _synthetic()
    signed, evid = prep.pseudobulk_de(X, genes, targets, control_label="NTC", min_cells=5)
    # TA should have G0 up and G1 down as significant signed edges
    ta = signed[signed["target_gene"] == "TA"].set_index("downstream_gene")
    assert ta.loc["G0", "log_fc"] > 0
    assert ta.loc["G1", "log_fc"] < 0
    assert "TA" in set(evid["target"])
    row = evid[evid["target"] == "TA"].iloc[0]
    assert row["n_up_genes"] >= 1 and row["n_down_genes"] >= 1
    assert row["n_cells"] == 20


def test_min_cells_skips_small_groups_no_fabrication():
    X, genes, targets = _synthetic()
    # require more cells than exist per group -> nothing emitted (never imputed)
    signed, evid = prep.pseudobulk_de(X, genes, targets, min_cells=1000)
    assert signed.empty and evid.empty


def test_output_feeds_the_signed_de_reader(tmp_path):
    X, genes, targets = _synthetic()
    signed, _ = prep.pseudobulk_de(X, genes, targets, min_cells=5)
    p = tmp_path / "signed_de.csv"
    signed.to_csv(p, index=False)
    # the P1 reader must accept the prep tool's own output unchanged
    df, notes = signed_de_io.read_signed_de_table(p)
    assert {"target_gene", "downstream_gene", "log_fc", "culture_condition", "adj_p_value"}.issubset(df.columns)
    assert notes["n_targets"] >= 1


def test_bh_fdr_monotone():
    p = np.array([0.001, 0.01, 0.02, 0.5])
    adj = prep._bh_fdr(p)
    assert (adj >= p).all() and (adj <= 1).all()


@pytest.mark.skipif(importlib.util.find_spec("anndata") is None, reason="anndata not installed (offline-only dep)")
def test_prep_h5ad_roundtrip(tmp_path):
    import anndata

    X, genes, targets = _synthetic()
    adata = anndata.AnnData(X=X, obs=pd.DataFrame({"target": targets}), var=pd.DataFrame(index=genes))
    h5 = tmp_path / "raw.h5ad"
    adata.write_h5ad(str(h5))
    manifest = prep.prep_h5ad(h5, tmp_path / "out", target_col="target", control_label="NTC", min_cells=5)
    assert manifest["n_cells"] == 40 and manifest["n_targets"] >= 1
    assert (tmp_path / "out" / "signed_de.csv").exists()
    assert (tmp_path / "out" / "target_evidence.csv").exists()
