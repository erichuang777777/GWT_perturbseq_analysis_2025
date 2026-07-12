"""Tests for triage_view.py -- integrated multi-axis triage card (follow-up F).

Locks the things that matter:
  1. Composite integrity: ``build_triage`` emits every axis column and exactly
     one row per target (synthetic hard-lock + real-data skipif sanity).
  2. Real-data multi-axis ranking (skipif-gated, real overlays loaded): the six
     multi-axis winners (PIK3R1 / PLCG1 / CD3E / CD247 / IL4R / ITK) surface near
     the top (loose top-~40 bound, not exact ranks), and LAT -- strong on the
     immune/gated axes but a KNOWN-high on-target safety liability -- is demoted
     out of the top ~15 once the safety overlays are loaded.
  3. unknown != 0: a target uncovered by the gnomAD overlay has
     ``composite_safety_liability == 'unknown'`` -- never a number, never 'safe'.
  4. INERT lock: attaching every build_triage axis column to a cards copy and
     running ``compute_readiness`` yields byte-identical readiness output vs the
     plain frame -- proving no triage axis can leak into any call.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import triage_view
from triage_view import DEFAULT_WEIGHTS, build_triage, triage_rank

REPO = Path(__file__).resolve().parent.parent
REAL_CARDS = REPO / "sources" / "target_tool_cache" / "a6bba17b-f194-4a50-8cf8-96e03eededd6" / "target_cards.csv"

_AXIS_COLUMNS = [
    "concept_modules",
    "n_concept_modules",
    "stimulation_gated",
    "switch_type",
    "gnomad_constraint_flag",
    "gtex_breadth",
    "composite_safety_liability",
    "druggable_class",
    "tractability_modality",
    "robustness_tier",
    "double_support",
    "n_diseases",
]


def _synthetic_cards() -> pd.DataFrame:
    """Two targets across Rest/Stim conditions, exercising every axis branch."""
    rows = []
    # GATED_DRUG: quiet at rest, active on stim; in a concept module (PLCG1 is a
    # real seed gene), druggable, replicate-passing -> multi-axis attractive.
    for cond, de, logfc, eff in [
        ("Rest", 5, 0.0, 0.5),
        ("Stim8hr", 2000, 2.0, 12.0),
        ("Stim48hr", 1800, 2.1, 11.0),
    ]:
        rows.append(
            {
                "target": "PLCG1",
                "target_id": "ENSG00000124181",
                "condition": cond,
                "ontarget_effect_size": eff,
                "n_total_de_genes": de,
                "median_logFC": logfc,
                "effect_direction_flip_flag": False,
                "replicate_pass_flag": True,
                "batch_sensitivity_flag": "not_flagged",
                "offtarget_flag": False,
                "crossdonor_correlation_mean": 0.6,
                "crossguide_correlation": 0.5,
                "n_cells_target": 800,
                "statistical_evidence_grade": 3,
                "druggable_class": "enzymes",
                "tractability_modality": "small molecule",
            }
        )
    # NOBODY: not in any concept module, not druggable, unmeasured robustness.
    for cond, de, eff in [("Rest", 100, 1.0), ("Stim8hr", 120, 1.2)]:
        rows.append(
            {
                "target": "NOBODY",
                "target_id": "ENSG00000000000",
                "condition": cond,
                "ontarget_effect_size": eff,
                "n_total_de_genes": de,
                "median_logFC": 0.1,
                "effect_direction_flip_flag": False,
                "replicate_pass_flag": False,
                "batch_sensitivity_flag": "sensitive",
                "offtarget_flag": False,
                "crossdonor_correlation_mean": np.nan,
                "crossguide_correlation": np.nan,
                "n_cells_target": 50,
                "statistical_evidence_grade": 1,
                "druggable_class": np.nan,
                "tractability_modality": np.nan,
            }
        )
    return pd.DataFrame(rows)


# --- composite integrity (synthetic) ---------------------------------------


def test_build_triage_has_all_axes_and_one_row_per_target():
    df = _synthetic_cards()
    triage = build_triage(df)
    # every axis column present
    for col in _AXIS_COLUMNS:
        assert col in triage.columns, f"missing axis column {col!r}"
    # exactly one row per target
    assert triage["target"].is_unique
    assert set(triage["target"]) == {"PLCG1", "NOBODY"}

    plcg1 = triage[triage["target"] == "PLCG1"].iloc[0]
    # deduped to the strongest-|effect| condition (Stim8hr, eff=12.0)
    assert plcg1["ontarget_effect_size"] == 12.0
    assert plcg1["n_concept_modules"] >= 1
    assert plcg1["stimulation_gated"] == True  # noqa: E712 -- quiet Rest, active Stim
    assert plcg1["robustness_tier"] == "high_confidence"

    nobody = triage[triage["target"] == "NOBODY"].iloc[0]
    assert nobody["n_concept_modules"] == 0
    # no safety overlays passed -> unknown, never 0/safe
    assert nobody["composite_safety_liability"] == "unknown"


def test_triage_rank_honest_fallback_when_columns_missing():
    df = pd.DataFrame([{"foo": 1}])
    out = triage_rank(df)
    assert out["available"] is False
    assert out["targets"] == []
    assert out["weights"] == DEFAULT_WEIGHTS


def test_unknown_safety_when_gene_uncovered_by_overlay():
    """unknown != 0: a gene present but absent from the gnomAD table is
    'unknown' -- never a number, never coerced to 'safe'/low."""
    df = _synthetic_cards()
    # a real, available overlay that simply does NOT cover PLCG1's Ensembl id.
    gnomad = {
        "available": True,
        "reason": None,
        "table": pd.DataFrame(
            {"ensembl_id": ["ENSG99999999999"], "gene_symbol": ["OTHER"], "loeuf": [0.1], "pli": [1.0]}
        ),
    }
    gtex = {
        "available": True,
        "reason": None,
        "table": pd.DataFrame(
            {
                "ensembl_id": ["ENSG99999999999"],
                "gene_symbol": ["OTHER"],
                "n_tissues_expressed": [10],
                "max_expression_outside_cd4_context": [1.0],
            }
        ),
    }
    triage = build_triage(df, gnomad_overlay=gnomad, gtex_overlay=gtex)
    plcg1 = triage[triage["target"] == "PLCG1"].iloc[0]
    assert plcg1["gnomad_constraint_flag"] == "unknown"
    assert plcg1["composite_safety_liability"] == "unknown"
    assert not isinstance(plcg1["composite_safety_liability"], (int, float))


# --- real-data (skipif-gated) ----------------------------------------------


def _load_real_overlays():
    from evidence.safety_overlay import (
        load_gnomad_constraint_overlay,
        load_gtex_safety_overlay,
    )

    return load_gnomad_constraint_overlay(), load_gtex_safety_overlay()


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_real_data_composite_integrity():
    from api import deps

    cards = deps._normalize_cell_values(pd.read_csv(REAL_CARDS, low_memory=False))
    triage = build_triage(cards)
    for col in _AXIS_COLUMNS:
        assert col in triage.columns
    # one row per target
    assert triage["target"].is_unique
    assert len(triage) == cards["target"].nunique()


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_real_data_multi_axis_winners_surface_and_lat_demoted():
    from api import deps

    cards = deps._normalize_cell_values(pd.read_csv(REAL_CARDS, low_memory=False))
    gnomad, gtex = _load_real_overlays()
    assert gnomad.get("available") and gtex.get("available"), "real safety overlays must load for this test"

    out = triage_rank(cards, gnomad_overlay=gnomad, gtex_overlay=gtex, top_n=100)
    assert out["available"] is True
    ranked = [r["target"] for r in out["targets"]]

    # the six multi-axis winners appear in the top ~40 (loose bound, not exact ranks)
    top40 = set(ranked[:40])
    for winner in ["PIK3R1", "PLCG1", "CD3E", "CD247", "IL4R", "ITK"]:
        assert winner in top40, f"{winner} not in top 40: rank={ranked.index(winner)+1 if winner in ranked else 'absent'}"

    # LAT is broadly expressed (GTEx breadth 28) -> carries a safety liability
    # and is demoted out of the top ~15 once safety overlays are loaded. (Under
    # the authentic gnomAD v2.1.1 overlay LAT's LOEUF is 0.66, i.e. NOT
    # LoF-constrained -- its liability is expression-breadth, not constraint.)
    top15 = ranked[:15]
    assert "LAT" not in top15, f"LAT should be demoted by safety but is in top15: {top15}"

    # sparse-axis coverage disclosed (unknown != 0): the composite safety axis
    # needs BOTH gnomAD constraint (now whole-genome) AND GTEx breadth (still a
    # ~5k-gene partial overlay), so GTEx is the limiting axis -- most targets are
    # 'unknown', never coerced to safe/0, and never scored.
    cov = out["provenance"]["safety_coverage"]
    assert cov["safety_unknown"] > cov["safety_covered"]


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_stat3_safety_is_known_high_liability():
    """Anchor the demotion mechanism: STAT3's composite safety liability is
    'high' (LoF-constrained AND broadly expressed) under the authentic gnomAD
    v2.1.1 overlay -- not unknown, not low. (STAT3: LOEUF 0.095, GTEx breadth
    28; a textbook broadly-essential signaling gene. This replaces the earlier
    LAT anchor, whose demo-seed LOEUF wrongly read as constrained -- LAT's real
    v2.1.1 LOEUF is 0.66, i.e. not constrained.)"""
    from api import deps

    cards = deps._normalize_cell_values(pd.read_csv(REAL_CARDS, low_memory=False))
    gnomad, gtex = _load_real_overlays()
    triage = build_triage(cards, gnomad_overlay=gnomad, gtex_overlay=gtex)
    stat3 = triage[triage["target"] == "STAT3"].iloc[0]
    assert stat3["gnomad_constraint_flag"] == "loss_intolerant"
    assert stat3["composite_safety_liability"] == "high"


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_triage_axes_are_inert_through_compute_readiness():
    """THE decision-separation lock: attaching every triage axis column must not
    change ANY readiness output. Build the composite, merge its axis columns onto
    a cards copy, and run compute_readiness on the plain vs augmented frame;
    every readiness-produced column must be row-identical."""
    from core.readiness import compute_readiness

    cards = pd.read_csv(REAL_CARDS, nrows=80, low_memory=False)
    base = compute_readiness(cards)

    triage = build_triage(cards)
    new_cols = [c for c in triage.columns if c not in cards.columns]
    assert new_cols, "build_triage must add axis columns"
    add = triage[["target"] + new_cols].drop_duplicates("target")
    augmented = cards.merge(add, on="target", how="left")
    assert len(augmented) == len(cards)
    after = compute_readiness(augmented)

    readiness_cols = [c for c in base.columns if c not in cards.columns]
    assert "readiness_call" in readiness_cols
    for col in readiness_cols:
        left = base[col].reset_index(drop=True)
        right = after[col].reset_index(drop=True)
        assert left.equals(right), f"triage axis leaked into readiness column {col!r}"
