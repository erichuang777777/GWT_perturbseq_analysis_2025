"""Tests for concept_annotation.py -- descriptive immune-concept overlay (follow-up A).

Locks the four things that matter: (1) real known-answer inversion of the seed
modules (PLCG1->M02, LAG3->M04+M18); (2) a POSITIVE annotation on the real cards
so a wrong join key (Ensembl instead of symbol) can't pass by tagging everything
``[]``; (3) unknown != 0 for both the empty-module and missing-stimulation cases;
(4) the descriptive-vs-decision lock -- an annotated frame run through
``compute_readiness`` yields byte-identical readiness output vs the un-annotated
frame, proving the concept columns cannot leak into any call.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from concept_annotation import (
    annotate_targets,
    annotation_provenance,
    build_gene_to_modules,
    immune_interest_rank,
    stimulation_gated_by_target,
)

REPO = Path(__file__).resolve().parent.parent
REAL_CARDS = REPO / "sources" / "target_tool_cache" / "a6bba17b-f194-4a50-8cf8-96e03eededd6" / "target_cards.csv"


def test_gene_to_modules_known_answers():
    idx = build_gene_to_modules()
    assert [m["module_id"] for m in idx["PLCG1"]] == ["M02"]
    assert {m["module_id"] for m in idx["LAG3"]} == {"M04", "M18"}  # multi-concept node
    assert "NSD1" not in idx  # a high-breadth chromatin gene in no immune module
    # every value carries display metadata the dashboard chips need
    assert idx["CD28"][0]["module_name"]
    assert idx["CD28"][0]["category"]


def _mini_cards() -> pd.DataFrame:
    """A tiny hand-built cards frame with the columns the annotation reads."""
    rows = []
    # PLCG1: quiet at Rest, loud on Stim -> stimulation-gated True
    rows += [
        {"target": "PLCG1", "target_id": "ENSG_PLCG1", "condition": "Rest", "n_total_de_genes": 3, "ontarget_effect_size": 1.0},
        {"target": "PLCG1", "target_id": "ENSG_PLCG1", "condition": "Stim8hr", "n_total_de_genes": 5033, "ontarget_effect_size": 14.1},
        {"target": "PLCG1", "target_id": "ENSG_PLCG1", "condition": "Stim48hr", "n_total_de_genes": 2218, "ontarget_effect_size": 10.8},
    ]
    # TADA2B: pan-condition, in no module, not gated
    rows += [
        {"target": "TADA2B", "target_id": "ENSG_TADA2B", "condition": "Rest", "n_total_de_genes": 4681, "ontarget_effect_size": 20.0},
        {"target": "TADA2B", "target_id": "ENSG_TADA2B", "condition": "Stim8hr", "n_total_de_genes": 5920, "ontarget_effect_size": 22.0},
    ]
    # LAG3: multi-concept; Rest present but no Stim rows -> gated unknown (None)
    rows += [
        {"target": "LAG3", "target_id": "ENSG_LAG3", "condition": "Rest", "n_total_de_genes": 10, "ontarget_effect_size": 2.0},
    ]
    return pd.DataFrame(rows)


def test_annotate_is_additive_and_honors_unknown():
    df = _mini_cards()
    out = annotate_targets(df)
    # additive: every original column survives unchanged
    for col in df.columns:
        assert col in out.columns
        assert (out[col].reset_index(drop=True) == df[col].reset_index(drop=True)).all()
    # concept membership
    plcg1 = out[out["target"] == "PLCG1"].iloc[0]
    assert [m["module_id"] for m in plcg1["concept_modules"]] == ["M02"]
    assert plcg1["n_concept_modules"] == 1
    # unknown != 0: a non-module gene is [] / 0, never an error
    tada = out[out["target"] == "TADA2B"].iloc[0]
    assert tada["concept_modules"] == []
    assert tada["n_concept_modules"] == 0
    # provenance column present and real
    assert out["concept_set_version"].nunique() == 1
    assert out["concept_set_version"].iloc[0] not in ("", "unknown")


def test_stimulation_gated_unknown_is_none_not_false():
    gated = stimulation_gated_by_target(_mini_cards())
    assert gated["PLCG1"] is True            # quiet Rest, loud Stim
    assert gated["TADA2B"] is False          # loud everywhere -> not gated
    assert gated["LAG3"] is None             # Rest present, no Stim -> unknown, NOT False


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_positive_annotation_on_real_cards_locks_join_key():
    """The join must be on `target` (symbol). On the REAL cards, immune seed
    genes MUST annotate non-empty -- this catches a wrong `target_id` (Ensembl)
    join, which would silently tag every gene [] and still pass the negative
    test above."""
    cards = pd.read_csv(REAL_CARDS)
    out = annotate_targets(cards)
    # at least the well-known immune seed genes present in the screen are tagged
    tagged = out[out["n_concept_modules"] > 0]["target"].str.upper().unique()
    for gene in ("PLCG1", "CD247", "CD28", "LAG3", "STAT3"):
        assert gene in tagged, f"{gene} should be concept-annotated on the real cards"
    # and a genome-wide sanity floor: many targets are tagged (not a []-everywhere bug)
    assert out["n_concept_modules"].sum() > 100


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_annotation_is_inert_through_compute_readiness():
    """THE decision-separation lock: annotating the cards must not change ANY
    readiness output. Run compute_readiness on the plain frame and on the
    annotated frame; every column compute_readiness produces must be identical."""
    from core.readiness import compute_readiness

    cards = pd.read_csv(REAL_CARDS, nrows=60)
    base = compute_readiness(cards)
    annotated_in = annotate_targets(cards)
    ann = compute_readiness(annotated_in)

    readiness_cols = [c for c in base.columns if c not in cards.columns]
    assert "readiness_call" in readiness_cols
    for col in readiness_cols:
        left = base[col].reset_index(drop=True)
        right = ann[col].reset_index(drop=True)
        # NaN-safe equality
        assert left.equals(right), f"concept annotation changed readiness column {col!r}"


@pytest.mark.skipif(not REAL_CARDS.exists(), reason="pre-built cards not present in this checkout")
def test_immune_interest_rank_dedups_to_target_and_prioritizes_concepts():
    cards = pd.read_csv(REAL_CARDS)
    ranked = immune_interest_rank(cards)
    # dedup: one row per target
    assert ranked["target"].is_unique
    assert len(ranked) == cards["target"].nunique()
    # multi-concept, real-effect immune nodes rank ahead of the median target
    top_200 = set(ranked.head(200)["target"].str.upper())
    for gene in ("LAG3", "CD247", "PLCG1"):
        assert gene in top_200
    # the ranking is non-increasing in concept-module count
    ncm = ranked["n_concept_modules"].to_numpy()
    assert (ncm[:-1] >= ncm[1:]).all()


def test_annotation_provenance_block():
    prov = annotation_provenance()
    assert prov["n_modules"] == 20
    assert prov["n_seed_genes"] == 115
    assert prov["descriptive_only"] is True
    assert "symbol" in prov["join_key"]
