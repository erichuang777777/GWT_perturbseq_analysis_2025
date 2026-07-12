"""Endpoint surfacing the paper's cluster-level autoimmune-enrichment result, per gene.

Descriptive-only. Explodes the paper's `cluster_autoimmune_enrichment_results` table (which
this toolkit never read) so it is gene-queryable. Guilt-by-cluster-membership, not a direct
gene->disease association; negative-control diseases excluded; never a readiness input. See
`autoimmune_clusters.py` for provenance and honesty constraints (`unknown != 0`).
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

import autoimmune_clusters

router = APIRouter(tags=["Concept profile (demo)"])


@router.get(
    "/api/autoimmune_clusters/{gene}",
    summary="The paper's autoimmune-enriched perturbation clusters this gene participates in (descriptive)",
)
def get_autoimmune_clusters(gene: str) -> Dict[str, Any]:
    """Does this target sit in a perturbation cluster the paper found enriched for autoimmune disease?

    Surfaces the paper's own `cluster_autoimmune_enrichment_results` table, keyed by gene: per
    autoimmune disease × cluster × perturbation context, the `odds_ratio`, CI, `p_adj_fdr`, and
    `cluster_size`.

    **This is guilt-by-cluster-membership** — the gene is a member of a cluster whose gene-set is
    enriched for the disease's GWAS genes, NOT a direct gene->disease association or a causal
    claim. Negative-control disease rows are excluded. `significant` = `p_adj_fdr < 0.05`.
    `unknown != 0`: a gene in no cluster's intersecting-gene list returns `enrichments: []`,
    never a 0. Descriptive only — not a readiness input, and not a reproduction of the paper's
    enrichment testing (its output made queryable).
    """
    return autoimmune_clusters.autoimmune_clusters_for_target(gene)
