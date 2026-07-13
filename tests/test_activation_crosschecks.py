"""
Tests for the Track D activation-screen cross-check runner
(docs/mvp-research/level4_external_validation/run_activation_crosschecks.py).

These run against the REAL cached activation screens in metadata/. They lock in
the honest findings of the actual run:
  - the pre-registered directionality AUROC is a NULL (below the 0.65 acceptance
    criterion) for the phenotype-matched screens, and
  - the post-hoc footprint-magnitude concordance is a weak but highly significant
    POSITIVE signal.
If a cached screen file is absent, the relevant test skips (never fabricates).
"""
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "docs" / "mvp-research" / "level4_external_validation" / "run_activation_crosschecks.py"
RANKING = REPO / "docs" / "mvp-research" / "signed_de_application" / "signed_ranking_v2.csv"
SCHMIDT = REPO / "metadata" / "SchmidtSteinhart2022_CRISPRi_screen_gene_phenotypes.csv"
FREIMER = REPO / "metadata" / "Freimer2022_Screen.csv"

pd = pytest.importorskip("pandas")
pytest.importorskip("scipy")


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_activation_crosschecks", RUNNER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    if not RUNNER.exists():
        pytest.skip("runner not present")
    return _load_runner()


@pytest.fixture(scope="module")
def ranking():
    if not RANKING.exists():
        pytest.skip("signed_ranking_v2.csv not present")
    return pd.read_csv(RANKING, comment="#")


def test_schmidt_adapter_maps_vav1_as_positive_regulator(mod):
    if not SCHMIDT.exists():
        pytest.skip("Schmidt screen not cached")
    c = mod.load_schmidt("CD4+ IL2")
    assert c is not None and not c.empty
    assert {"gene", "effect_score", "fdr", "hit_direction"} <= set(c.columns)
    vav1 = c[c["gene"] == "VAV1"]
    assert len(vav1) == 1
    # VAV1 knockdown depletes the IL2-high pool -> decreases activation -> hit_direction -1
    assert int(vav1["hit_direction"].iloc[0]) == -1
    assert float(vav1["fdr"].iloc[0]) < 0.01


def test_schmidt_cd4il2_crosscheck_is_a_null_below_acceptance(mod, ranking):
    if not SCHMIDT.exists():
        pytest.skip("Schmidt screen not cached")
    c = mod.load_schmidt("CD4+ IL2")
    res = mod.crosscheck(ranking, c)
    assert res["n_merged"] > 9000                      # large overlap
    assert 0.0 <= res["auroc"] <= 1.0
    # HONEST FINDING: the pre-registered directionality AUROC does NOT meet the
    # >=0.65 acceptance criterion (it is ~0.47). This test documents the null.
    assert res["auroc"] < 0.65


def test_magnitude_concordance_is_weak_but_significant_positive(mod, ranking):
    if not SCHMIDT.exists():
        pytest.skip("Schmidt screen not cached")
    c = mod.load_schmidt("CD4+ IL2")
    mag = mod.magnitude_concordance(ranking, c)
    # footprint breadth vs screen significance: weak but highly significant positive
    assert mag["rho"] > 0
    assert mag["p"] < 1e-10
    assert mag["n"] > 9000


def test_essential_dropout_explains_missing_hits(mod, ranking):
    if not SCHMIDT.exists():
        pytest.skip("Schmidt screen not cached")
    c = mod.load_schmidt("CD4+ IL2")
    drop = mod.essential_dropout_among_top_hits(ranking, c, mod.load_essentials(), top_n=50)
    assert drop["top_n"] == 50
    # a substantial share of the screen's top activation hits are simply absent
    # from our ranking (viability dropout) -> explains the null enrichment
    assert drop["n_absent_from_ranking"] >= 10


def test_magnitude_aligned_fair_axis_passes_and_is_robust_to_essentials(mod, ranking):
    if not SCHMIDT.exists():
        pytest.skip("Schmidt screen not cached")
    c = mod.load_schmidt("CD4+ IL2")
    ma = mod.magnitude_aligned_crosscheck(ranking, c, mod.load_essentials())
    # SECONDARY (exploratory) finding: scoring by footprint magnitude (not directionality)
    # clears the 0.65 acceptance bar, and excluding Hart essentials barely moves it
    # (so the signal is not a generic essential-gene artefact).
    assert ma["all"]["auroc"] > 0.65
    assert ma["no_essential"]["auroc"] > 0.65
    assert abs(ma["all"]["auroc"] - ma["no_essential"]["auroc"]) < 0.05
    assert ma["no_essential"]["perm_p"] < 0.05


def test_freimer_adapter_aggregates_per_gene(mod):
    if not FREIMER.exists():
        pytest.skip("Freimer screen not cached")
    c = mod.load_freimer()
    assert c is not None and not c.empty
    assert c["gene"].is_unique                     # aggregated to one row per gene
    assert "NON-TARGETING" not in set(c["gene"].str.upper())
