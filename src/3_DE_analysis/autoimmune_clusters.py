"""Surface the paper's OWN cluster-level autoimmune-enrichment result, keyed by gene.

The source paper (Zhu, Dann, …, Marson — bioRxiv 10.64898/2025.12.23.696273) implicates
context-specific gene-regulatory pathways in autoimmune-disease risk by testing whether the
downstream/regulator gene-sets of its perturbation clusters are enriched for autoimmune GWAS
disease genes. It ships that result as
`metadata/suppl_tables/cluster_autoimmune_enrichment_results.suppl_table.csv`
(5,236 cluster × disease rows) — which this toolkit never read.

That table is **cluster-indexed**, not gene-indexed. This module explodes its
`intersecting_genes` lists once (cached) so a dossier can ask: *does this target sit in a
perturbation cluster the paper found enriched for an autoimmune disease, in which context,
at what odds ratio?*

Honest framing (this is weaker than a direct gene→disease association, and is stated as such):
  * This is **guilt-by-cluster-membership**: the gene is a member of a cluster whose gene-set
    is enriched for a disease's GWAS genes — NOT a claim that the gene itself is causal for,
    or directly associated with, that disease.
  * **Negative-control disease rows are excluded** (`negative_control_disease == True`, 924
    rows) — they exist precisely to calibrate the enrichment and must not read as findings.
  * Each enrichment carries `odds_ratio`, CI, `p_adj_fdr`, `cluster_size`, and the perturbation
    `context` (which gene-set: downstream at Rest/Stim8hr/Stim48hr, or regulators) so strength
    and context are never flattened. `significant` = `p_adj_fdr < 0.05`.
  * `unknown != 0`: a gene in no cluster's intersecting-gene list is ABSENT, never returned
    with a 0 odds ratio. Descriptive only — never a readiness input.

Sanity anchors (textbook autoimmune genes recovered against textbook diseases, asserted in the
test): CTLA4 → Hashimoto's / rheumatoid arthritis / celiac; IL2RA → Crohn's / asthma.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
ENRICH_CSV = (
    _ROOT / "metadata" / "suppl_tables" / "cluster_autoimmune_enrichment_results.suppl_table.csv"
)
SIGNIFICANT_FDR = 0.05

_INDEX: Optional[Dict[str, List[Dict[str, Any]]]] = None
_LOADED = False


def _parse_genes(cell: Any) -> List[str]:
    if not isinstance(cell, str):
        return []
    try:
        val = ast.literal_eval(cell)
        return [str(g) for g in val] if isinstance(val, (list, tuple)) else []
    except (ValueError, SyntaxError):
        return []


def _load_index() -> Optional[Dict[str, List[Dict[str, Any]]]]:
    global _INDEX, _LOADED
    if _LOADED:
        return _INDEX
    _LOADED = True
    if not ENRICH_CSV.exists():
        _INDEX = None
        return None
    df = pd.read_csv(ENRICH_CSV, low_memory=False)
    # exclude negative-control disease rows: they calibrate the test, they are not findings
    if "negative_control_disease" in df.columns:
        df = df[~df["negative_control_disease"].fillna(False).astype(bool)]
    index: Dict[str, List[Dict[str, Any]]] = {}
    for _, r in df.iterrows():
        genes = _parse_genes(r.get("intersecting_genes"))
        if not genes:
            continue
        fdr = r.get("p_adj_fdr")
        rec = {
            "disease": r.get("disease"),
            "cluster": None if pd.isna(r.get("cluster")) else int(r["cluster"]),
            "context": r.get("gene_set"),  # downstream_Rest/Stim8hr/Stim48hr | regulators
            "odds_ratio": None if pd.isna(r.get("odds_ratio")) else float(r["odds_ratio"]),
            "ci_low": None if pd.isna(r.get("ci_low")) else float(r["ci_low"]),
            "ci_high": None if pd.isna(r.get("ci_high")) else float(r["ci_high"]),
            "p_adj_fdr": None if pd.isna(fdr) else float(fdr),
            "cluster_size": None if pd.isna(r.get("cluster_size")) else int(r["cluster_size"]),
            "significant": bool(fdr < SIGNIFICANT_FDR) if not pd.isna(fdr) else False,
        }
        for g in genes:
            index.setdefault(g.upper(), []).append(rec)
    _INDEX = index
    return index


def autoimmune_clusters_for_target(gene: str) -> Dict[str, Any]:
    """The paper's autoimmune-cluster enrichments this gene participates in. Honest empty."""
    index = _load_index()
    if index is None:
        return {"gene": gene, "available": False,
                "reason": "cluster_autoimmune_enrichment table not present", "enrichments": []}
    recs = list(index.get(str(gene).strip().upper(), []))
    # deterministic: significant first, then by ascending FDR
    recs.sort(key=lambda x: (not x["significant"], x["p_adj_fdr"] if x["p_adj_fdr"] is not None else 1.0))
    sig = [r for r in recs if r["significant"]]
    return {
        "gene": gene,
        "available": True,
        "n_enrichments": len(recs),
        "n_significant": len(sig),
        "significant_diseases": sorted({r["disease"] for r in sig if r["disease"]}),
        "interpretation": (
            "guilt-by-cluster-membership: this gene is a member of a perturbation cluster whose "
            "gene-set is enriched for the listed autoimmune disease's GWAS genes — NOT a direct "
            "gene->disease association or a causal claim. Negative-control diseases are excluded. "
            "significant = p_adj_fdr < 0.05. unknown != 0: absence means not in any cluster's "
            "intersecting-gene list, never a 0. Descriptive only — not a readiness input."
        ),
        "enrichments": recs,
    }


def is_loaded_ok() -> bool:
    return _load_index() is not None
