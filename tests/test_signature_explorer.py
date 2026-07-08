"""A1a (signature-to-compound infrastructure, internal-validation half) + A4
(combination explorer). All tests use real, in-repo data -- see
``src/3_DE_analysis/signature_explorer.py``'s module docstring for the
data-availability finding this module is built around (no genome-wide
per-downstream-gene DE table is checked into this repo, so query signatures
are honestly single-gene / on-target-only).
"""
from __future__ import annotations

import pandas as pd
import pytest


def test_load_reference_signature_th2_vs_th1_real_file(real_data_available):
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from signature_explorer import load_reference_signature

    result = load_reference_signature("th2_vs_th1")
    assert result["available"] is True
    # combined_Th2_vs_Th1_signature.csv: 9,206 unique genes (verified by inspection).
    assert len(result["signature"]) == 9206
    assert "GATA3" in result["signature"]
    assert "TBX21" in result["signature"]


def test_load_reference_signature_cd4t_aging_real_file(real_data_available):
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from signature_explorer import load_reference_signature

    result = load_reference_signature("cd4t_aging")
    assert result["available"] is True
    assert len(result["signature"]) == 10000


def test_load_reference_signature_unknown_name_is_honest():
    from signature_explorer import load_reference_signature

    result = load_reference_signature("not_a_real_signature")
    assert result["available"] is False
    assert "not_a_real_signature" in result["reason"]
    assert result["signature"] == {}


def test_load_reference_signature_missing_file_is_honest(tmp_path):
    from signature_explorer import load_reference_signature

    result = load_reference_signature("th2_vs_th1", path=tmp_path / "does_not_exist.csv")
    assert result["available"] is False
    assert result["signature"] == {}


# --- build_query_signature: real DE stats, honest single-gene scope ------------


def test_build_query_signature_shape_and_scope(real_data_available):
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    import pandas as pd

    from signature_explorer import build_query_signature

    de = pd.read_csv("metadata/suppl_tables/DE_stats.suppl_table.csv")
    result = build_query_signature("GATA3", de)
    assert result["available"] is True
    assert result["scope"] == "on_target_gene_only"
    assert set(result["signature"].keys()) == {"GATA3"}
    assert isinstance(result["signature"]["GATA3"], float)
    # GATA3 has real DE stats in all three culture conditions.
    assert set(result["conditions_used"]) == {"Rest", "Stim8hr", "Stim48hr"}
    assert len(result["per_condition"]) == 3


def test_build_query_signature_unknown_target_is_honest(real_data_available):
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    import pandas as pd

    from signature_explorer import build_query_signature

    de = pd.read_csv("metadata/suppl_tables/DE_stats.suppl_table.csv")
    result = build_query_signature("NOT_A_REAL_GENE_XYZ", de)
    assert result["available"] is False
    assert result["signature"] == {}
    assert "NOT_A_REAL_GENE_XYZ" in result["reason"]


def test_build_query_signature_missing_columns_is_honest():
    from signature_explorer import build_query_signature

    bad_de = pd.DataFrame({"some_other_column": [1, 2, 3]})
    result = build_query_signature("GATA3", bad_de)
    assert result["available"] is False
    assert "missing required columns" in result["reason"]


# --- connectivity_score: self-similarity + honest-fallback ----------------------


def test_connectivity_score_self_similarity_is_maximal(real_data_available):
    """Cheap, always-true sanity check: a signature compared to itself must
    hit the maximum of the score range (cosine similarity of a vector with
    itself is exactly 1.0)."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    import pandas as pd

    from signature_explorer import build_query_signature, connectivity_score

    de = pd.read_csv("metadata/suppl_tables/DE_stats.suppl_table.csv")
    query = build_query_signature("GATA3", de)
    result = connectivity_score(query["signature"], query["signature"])
    assert result["available"] is True
    assert result["score"] == pytest.approx(1.0)
    assert result["n_shared_genes"] == 1


def test_connectivity_score_reference_self_similarity_is_maximal(real_data_available):
    """Same check at genome-wide scale: the real Th2-vs-Th1 reference
    signature compared to itself over all 9,206 genes must also hit 1.0."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    from signature_explorer import connectivity_score, load_reference_signature

    ref = load_reference_signature("th2_vs_th1")
    result = connectivity_score(ref["signature"], ref["signature"])
    assert result["available"] is True
    assert result["score"] == pytest.approx(1.0)
    assert result["n_shared_genes"] == 9206


def test_connectivity_score_no_overlap_is_honest():
    from signature_explorer import connectivity_score

    result = connectivity_score({"GENE_A": 1.0}, {"GENE_B": -1.0})
    assert result["available"] is False
    assert result["n_shared_genes"] == 0
    assert result["score"] is None


def test_connectivity_score_carries_caveat_unconditionally():
    from signature_explorer import CAVEAT_TEXT, connectivity_score

    available_result = connectivity_score({"G": 1.0}, {"G": 1.0})
    unavailable_result = connectivity_score({"G": 1.0}, {"H": 1.0})
    assert available_result["caveat"] == CAVEAT_TEXT
    assert unavailable_result["caveat"] == CAVEAT_TEXT
    assert "not a claim" in CAVEAT_TEXT.lower() or "not a claim" in CAVEAT_TEXT


# --- Internal validation: known Th1/Th2 regulators (real, in-repo annotation) ---
#
# metadata/suppl_tables/polarization_prediction_condition_comparison_regulator_coefficients.csv
# carries a real, pre-existing "regulator_type" annotation ("Th1 regulator" /
# "Th2 regulator") for a curated set of known regulators, independently of
# this module. GATA3 is annotated "Th2 regulator" (it is *the* canonical Th2
# master transcription factor) and TBX21 is annotated "Th1 regulator" (the
# canonical Th1 master TF) there. This is the "existing Th1/Th2-annotated
# candidate gene" the plan doc points at for a sanity check.


def test_gata3_th2_regulator_shows_correctly_signed_connectivity_to_th2_signature(real_data_available):
    """GATA3 (real, in-repo-annotated Th2 master regulator) is itself one of
    the 9,206 genes profiled in the real Th2-vs-Th1 signature, where it is
    strongly Th2-high (positive z-score). GATA3 knockdown reduces GATA3's
    own expression (real, signed, significant ontarget_effect_size < 0 in
    all 3 conditions) -- i.e. knocking down the Th2 master TF should look
    like it moves *away* from the Th2 signature. This module's connectivity
    score correctly captures that reversal: negative score."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    import pandas as pd

    from signature_explorer import score_target_against_reference

    de = pd.read_csv("metadata/suppl_tables/DE_stats.suppl_table.csv")
    result = score_target_against_reference("GATA3", de, "th2_vs_th1")
    assert result["available"] is True
    connectivity = result["connectivity"]
    assert connectivity["n_shared_genes"] == 1
    # Single-gene overlap -> cosine degenerates to exact sign concordance
    # (documented limitation, see module docstring): GATA3's own KD effect
    # is negative and its real Th2-vs-Th1 reference z-score is positive, so
    # the connectivity score is exactly -1.0 (a measurable, correctly-signed
    # reversal-like connectivity to the Th2 signature).
    assert connectivity["score"] == pytest.approx(-1.0)
    assert "reversal" in connectivity["interpretation"]


def test_tbx21_th1_regulator_shows_opposite_signed_connectivity_to_th2_signature(real_data_available):
    """TBX21 (real, in-repo-annotated Th1 master regulator) is the mirror
    case: its own real Th2-vs-Th1 reference z-score is strongly negative
    (Th1-high), and its own knockdown effect is also negative, so the
    connectivity score is +1.0 -- knocking down the Th1 master TF looks
    like it moves *toward* the Th2 signature, the opposite direction from
    GATA3 knockdown. The two master regulators must disagree in sign."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    import pandas as pd

    from signature_explorer import score_target_against_reference

    de = pd.read_csv("metadata/suppl_tables/DE_stats.suppl_table.csv")
    result = score_target_against_reference("TBX21", de, "th2_vs_th1")
    assert result["available"] is True
    connectivity = result["connectivity"]
    assert connectivity["score"] == pytest.approx(1.0)
    assert "same-direction" in connectivity["interpretation"]


def test_gene_absent_from_reference_signature_is_honest_not_fabricated(real_data_available):
    """MED12 (a real, broadly-essential Mediator-complex gene perturbed in
    this screen) is not among the 9,206 genes in the Th2-vs-Th1 reference
    signature panel -- the honest result is 'insufficient overlap', never a
    guessed connectivity score."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    import pandas as pd

    from signature_explorer import load_reference_signature, score_target_against_reference

    ref = load_reference_signature("th2_vs_th1")
    assert "MED12" not in ref["signature"]

    de = pd.read_csv("metadata/suppl_tables/DE_stats.suppl_table.csv")
    result = score_target_against_reference("MED12", de, "th2_vs_th1")
    assert result["available"] is False
    assert "shared gene" in result["reason"]


# --- A1b stub: honest-unavailable, never a fabricated compound match -----------


def test_match_reference_compounds_is_honestly_unavailable():
    from signature_explorer import match_reference_compounds

    result = match_reference_compounds("GATA3")
    assert result["source_status"] == "unavailable"
    assert "LINCS" in result["reason"] or "CMap" in result["reason"]
    assert result["items"] == []


def test_match_reference_compounds_never_fabricates_regardless_of_kwargs():
    """Even with extra kwargs a future caller might pass, the stub must stay
    honestly unavailable -- never silently start returning fake matches."""
    from signature_explorer import match_reference_compounds

    result = match_reference_compounds("TBX21", top_n=10, min_score=0.5)
    assert result["source_status"] == "unavailable"


def test_match_reference_compounds_unavailable_reason_points_at_compound_path():
    """The honest-unavailable reason must precisely name where a committed
    compound matrix would live (COMPOUND_SIGNATURES_PATH) and preserve the
    genetic-vs-compound distinction -- so no one mistakes the committed
    knockdown data for compound data."""
    from evidence.lincs_reference_cache import COMPOUND_SIGNATURES_PATH
    from signature_explorer import match_reference_compounds

    result = match_reference_compounds("PLCG1")  # a LINCS-covered gene, still no COMPOUND data
    assert result["source_status"] == "unavailable"
    assert str(COMPOUND_SIGNATURES_PATH) in result["reason"] or "GSE92742" in result["reason"]
    assert "knockdown" in result["reason"].lower() or "genetic-perturbation" in result["reason"].lower()


def test_match_reference_compounds_routes_when_compound_data_supplied():
    """When a compound matrix IS available (here: a SYNTHETIC in-memory fixture
    injected via compound_signatures -- NOT committed data), match_reference_compounds
    genuinely routes to the compound-reversal ranking and returns the available
    shape with the most-reversing compound first and the forced cell-context
    caveat. This proves the wiring is real, not a permanent stub, without
    fabricating any committed data."""
    import numpy as np

    from evidence.lincs_reference_cache import COMPOUND_CAVEAT_TEXT
    from signature_explorer import match_reference_compounds

    genes = [f"LMARK{i}" for i in range(25)]
    base = np.arange(25, dtype=float)
    query_signature = {g: float(v) for g, v in zip(genes, base)}
    compound_df = pd.DataFrame(
        {"REVERSER": -base, "MIMIC": base.copy()}, index=genes
    )

    result = match_reference_compounds(
        "SOME_TARGET",
        query_signature=query_signature,
        compound_signatures=compound_df,
    )
    assert result["source_status"] == "available"
    assert result["items"][0]["compound"] == "REVERSER"
    assert result["items"][0]["is_reversal"] is True
    assert result["caveat"] == COMPOUND_CAVEAT_TEXT


# --- A4: combination explorer ---------------------------------------------------


def test_explore_combination_runs_on_two_real_targets_and_carries_caveat(real_data_available):
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    import pandas as pd

    from signature_explorer import COMBINATION_CAVEAT_TEXT, explore_combination

    de = pd.read_csv("metadata/suppl_tables/DE_stats.suppl_table.csv")
    result = explore_combination("GATA3", "TBX21", de)
    assert result["caveat"] == COMBINATION_CAVEAT_TEXT
    assert result["target_a"] == "GATA3"
    assert result["target_b"] == "TBX21"
    # GATA3 (-1.0) and TBX21 (+1.0) connectivity to th2_vs_th1 disagree in
    # sign -> opposing directions on the shared readout.
    assert result["interaction_pattern"] == "opposing_directions"
    assert result["connectivity_a"]["score"] == pytest.approx(-1.0)
    assert result["connectivity_b"]["score"] == pytest.approx(1.0)


def test_explore_combination_same_target_twice_is_reinforcing(real_data_available):
    """A target combined with itself must reinforce, not oppose or go
    ambiguous -- a basic internal-consistency check on the heuristic."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    import pandas as pd

    from signature_explorer import explore_combination

    de = pd.read_csv("metadata/suppl_tables/DE_stats.suppl_table.csv")
    result = explore_combination("GATA3", "GATA3", de)
    assert result["interaction_pattern"] == "reinforcing_same_direction"
    assert result["combined_naive_sum"] == pytest.approx(-2.0)


def test_explore_combination_unknown_target_is_insufficient_data_not_crash(real_data_available):
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    import pandas as pd

    from signature_explorer import explore_combination

    de = pd.read_csv("metadata/suppl_tables/DE_stats.suppl_table.csv")
    result = explore_combination("GATA3", "NOT_A_REAL_GENE_XYZ", de)
    assert result["interaction_pattern"] == "insufficient_data"
    assert result["reason"] is not None


def test_explore_combination_accepts_explicit_reference_signature(real_data_available):
    """A caller can pass a reference_signature dict directly instead of a
    named in-repo reference (documented extension point, e.g. for a future
    externally-supplied signature)."""
    if not real_data_available:
        pytest.skip("real data not present in this checkout")
    import pandas as pd

    from signature_explorer import build_query_signature, explore_combination

    de = pd.read_csv("metadata/suppl_tables/DE_stats.suppl_table.csv")
    # A tiny, real (not fabricated) reference built from GATA3's own query
    # signature -- used only to prove the explicit-reference code path runs.
    tiny_ref = build_query_signature("GATA3", de)["signature"]
    result = explore_combination("GATA3", "TBX21", de, reference_signature=tiny_ref)
    assert result["reference_name"] == "th2_vs_th1"  # label unchanged (default), signature overridden
    assert result["interaction_pattern"] in {"reinforcing_same_direction", "opposing_directions", "insufficient_data"}
