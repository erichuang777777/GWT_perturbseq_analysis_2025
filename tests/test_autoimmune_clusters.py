"""Surfacing the paper's autoimmune-cluster enrichment per gene — known-answer + unknown!=0."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "3_DE_analysis"
sys.path.insert(0, str(SRC))

import autoimmune_clusters as ac  # noqa: E402

_HAVE = ac.ENRICH_CSV.exists()


@pytest.mark.skipif(not _HAVE, reason="cluster_autoimmune_enrichment table not present")
def test_ctla4_recovers_textbook_autoimmune_diseases():
    res = ac.autoimmune_clusters_for_target("CTLA4")
    assert res["available"] is True
    assert res["n_significant"] > 0
    diseases = set(res["significant_diseases"])
    # CTLA4 is a canonical autoimmune gene (abatacept target); at least one textbook match
    assert diseases & {"rheumatoid arthritis", "Hashimoto's thyroiditis", "celiac disease",
                       "type 1 diabetes mellitus", "systemic lupus erythematosus", "autoimmune disease"}


@pytest.mark.skipif(not _HAVE, reason="cluster_autoimmune_enrichment table not present")
def test_enrichments_carry_strength_and_context():
    top = ac.autoimmune_clusters_for_target("CTLA4")["enrichments"][0]
    for key in ("disease", "context", "odds_ratio", "p_adj_fdr", "cluster_size", "significant"):
        assert key in top
    assert top["p_adj_fdr"] is None or 0.0 <= top["p_adj_fdr"] <= 1.0


@pytest.mark.skipif(not _HAVE, reason="cluster_autoimmune_enrichment table not present")
def test_negative_control_diseases_are_excluded():
    # any disease flagged negative_control in the raw table must never appear in served results
    raw = pd.read_csv(ac.ENRICH_CSV, low_memory=False)
    negctrl_only = set(raw.loc[raw["negative_control_disease"] == True, "disease"]) - set(  # noqa: E712
        raw.loc[raw["negative_control_disease"] == False, "disease"]  # noqa: E712
    )
    idx = ac._load_index()
    served = {rec["disease"] for recs in idx.values() for rec in recs}
    assert not (served & negctrl_only), served & negctrl_only


@pytest.mark.skipif(not _HAVE, reason="cluster_autoimmune_enrichment table not present")
def test_unknown_gene_is_absent_not_zero():
    res = ac.autoimmune_clusters_for_target("NOT_A_REAL_GENE_XYZ")
    assert res["available"] is True
    assert res["enrichments"] == []          # absence, never a fabricated 0-odds row
    assert res["significant_diseases"] == []
