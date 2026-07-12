"""Signed module-effect scoring — known-answer + unknown!=0 guards.

Locks in that the directional readout (built from the in-repo signed DE table)
recovers known master regulators with the correct sign, and that missing coverage
is reported as absence, never a fabricated 0.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "3_DE_analysis"
sys.path.insert(0, str(SRC))

import signed_module_effect as sme  # noqa: E402

OVERLAY = sme.DEFAULT_OUTPUT


# --------------------------- pure-function tests --------------------------- #
def test_direction_convention_is_crispri_signed():
    # knockdown lowers markers (neg) => target ACTIVATES the module
    assert sme._direction(-2.0) == "activator"
    assert sme._direction(2.0) == "repressor"
    assert sme._direction(0.1) == "weak_or_mixed"
    assert sme._direction(float("nan")) == "unknown"


def test_compute_is_signed_and_unknown_is_absent_not_zero():
    modules = [
        {"module_id": "M08", "module_name": "Th2_Polarization", "category": "Downstream",
         "seed_genes": ["IL4", "IL5", "IL13"]},
    ]
    signed = pd.DataFrame({
        "target_gene": ["GATA3", "GATA3", "OTHER"],
        "culture_condition": ["Rest", "Rest", "Rest"],
        "downstream_gene": ["IL4", "IL13", "SOMETHINGELSE"],  # OTHER hits no module seed
        "log_fc": [-2.0, -3.0, 1.5],
        "zscore": [-8.0, -9.0, 4.0],
    })
    out = sme.compute_signed_module_effects(signed, modules)
    # GATA3 -> Th2 present, signed negative (activator), 2 of 3 seeds hit
    g = out[out["target_gene"] == "GATA3"].iloc[0]
    assert g["direction"] == "activator"
    assert g["mean_logfc"] == pytest.approx(-2.5)
    assert g["n_downstream_hit"] == 2
    assert g["n_module_seed_total"] == 3
    # OTHER perturbed no module seed gene => ABSENT (unknown != 0), never a 0-row
    assert "OTHER" not in set(out["target_gene"])


# --------------------- real-data known-answer (if built) ------------------- #
@pytest.mark.skipif(not OVERLAY.exists(), reason="signed_module_effect overlay not built")
@pytest.mark.parametrize("gene,module_substr", [
    ("GATA3", "Th2"),   # Th2 master regulator
    ("TBX21", "Th1"),   # Th1 master regulator (T-bet)
    ("FOXP3", "Treg"),  # Treg master regulator
])
def test_master_regulators_recovered_as_activators(gene, module_substr):
    res = sme.effects_for_target(gene)
    assert res["available"] is True
    hits = [m for m in res["modules"] if module_substr in m["module_name"]]
    assert hits, f"{gene} had no {module_substr} module hit"
    # every measured condition should show the master regulator ACTIVATING its module
    # (knockdown lowers the module's markers => negative mean_logfc)
    assert all(m["mean_logfc"] < 0 for m in hits), [(m["condition"], m["mean_logfc"]) for m in hits]
    assert all(m["direction"] == "activator" for m in hits)


@pytest.mark.skipif(not OVERLAY.exists(), reason="signed_module_effect overlay not built")
def test_unknown_gene_returns_empty_not_zeros():
    res = sme.effects_for_target("NOT_A_REAL_GENE_XYZ")
    assert res["available"] is True
    assert res["modules"] == []  # absence, never fabricated 0-effect rows
