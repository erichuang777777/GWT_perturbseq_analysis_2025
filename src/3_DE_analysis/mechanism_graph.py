"""A2: target-centered mechanism graph (Reactome pathway membership + STRING
interaction partners + this platform's own evidence, overlaid for human
interpretation).

**What this is:** a purely descriptive visualization layer. It reads the
already-fetched, already-cached pathway/network snapshot produced by
``pathway_network_cache.py`` (Reactome pathway membership + STRING interaction
partners for one gene) and assembles it into a node/edge graph shape, with an
optional overlay of this platform's own evidence (``target_cards.csv`` /
readiness-frame columns) onto each gene node.

**What this explicitly does NOT do** (guardrail, per
``docs/next_phases_plan.md`` §A2):
- Never fetches live. This module only reads what ``pathway_network_cache.py``
  has already cached to disk (same "offline batch job, never live in the
  request path" pattern as the rest of the evidence layer) -- if no snapshot
  exists yet for a gene, the honest result is ``available: False``, not a
  live fetch and not a fabricated graph.
- Never invents an edge or a node. Every Reactome pathway node and every
  STRING interaction partner/score comes verbatim from the cached snapshot.
  A Reactome pathway is modeled as its own graph node (not expanded into a
  list of "co-member genes"), because ``fetch_reactome_pathways`` only
  returns *which pathways contain the query gene*, not *which other genes are
  in each of those pathways* -- claiming co-member gene nodes would be
  fabricating data this cache does not actually hold.
- Never feeds ``readiness_call`` / ``overall_readiness_stage`` /
  ``statistical_evidence_grade``. The evidence overlay on each node is a
  read-only join for display; nothing here writes back into the readiness
  engine or the cards pipeline.
- Never fabricates evidence for a neighbor gene absent from the supplied
  ``cards``/``readiness`` tables -- such nodes simply omit the evidence
  fields (``evidence_available: False``), never a guessed value.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

import pathway_network_cache as pnc

PathLike = Union[str, Path]


def _gene_evidence(gene: str, cards: Optional[pd.DataFrame], readiness: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """Real per-condition evidence for one gene, pulled only from real columns.

    Returns ``{"evidence_available": False}`` if the gene is absent from both
    tables (or neither table was supplied) -- never a fabricated value for a
    gene that isn't actually in the dataset.
    """
    gene_u = gene.upper()
    per_condition: Dict[str, Dict[str, Any]] = {}

    if cards is not None and not cards.empty and "target" in cards.columns:
        sub = cards[cards["target"].astype(str).str.upper() == gene_u]
        for _, row in sub.iterrows():
            cond = str(row.get("condition", "unknown"))
            entry = per_condition.setdefault(cond, {})
            if "kd_status" in row.index:
                entry["kd_status"] = row.get("kd_status")
            if "tractability_modality" in row.index:
                entry["tractability_modality"] = row.get("tractability_modality")

    if readiness is not None and not readiness.empty and "target" in readiness.columns:
        sub = readiness[readiness["target"].astype(str).str.upper() == gene_u]
        for _, row in sub.iterrows():
            cond = str(row.get("condition", "unknown"))
            entry = per_condition.setdefault(cond, {})
            if "readiness_call" in row.index:
                entry["readiness_call"] = row.get("readiness_call")
            if "overall_readiness_stage" in row.index:
                entry["overall_readiness_stage"] = row.get("overall_readiness_stage")
            if "red_flag_override" in row.index:
                entry["red_flag_override"] = row.get("red_flag_override")
            if "cd4_immune_red_flags" in row.index:
                flags = str(row.get("cd4_immune_red_flags", "") or "")
                entry["broad_effect_flag"] = "broad_effect" in [f.strip() for f in flags.split(",")]
            if "tractability_modality" in row.index and "tractability_modality" not in entry:
                entry["tractability_modality"] = row.get("tractability_modality")

    if not per_condition:
        return {"evidence_available": False}
    return {
        "evidence_available": True,
        "evidence": [{"condition": cond, **values} for cond, values in sorted(per_condition.items())],
    }


def _unavailable_graph(gene: str, reason: str) -> Dict[str, Any]:
    return {
        "gene": gene.upper(),
        "available": False,
        "reason": reason,
        "nodes": [],
        "edges": [],
    }


def build_mechanism_graph(
    gene: str,
    cache_dir: PathLike,
    cards: Optional[pd.DataFrame] = None,
    readiness: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """Assemble a target-centered mechanism graph from a cached pathway/network snapshot.

    ``cache_dir`` is the directory ``pathway_network_cache.build_pathway_network_for_gene``
    writes snapshots into (default ``sources/target_tool_cache/_pathway``). This
    function only *reads* ``pnc.load_snapshot`` -- it never calls the live
    fetchers, so a gene with no snapshot yet returns an honest
    ``available: False`` result rather than blocking a request on a network call.

    ``cards``/``readiness`` are optional ``target_cards.csv`` / readiness-frame
    DataFrames (see ``docs/data_dictionary.md`` §2/§3) used to enrich each gene
    node with this platform's own evidence. Omit them to get the bare
    pathway/network graph with no evidence overlay.

    Return shape::

        {
            "gene": "CD3E",
            "available": True,
            "reason": None,               # or a partial-failure explanation
            "fetched_at": "...",
            "source_version": "...",
            "reactome_status": "ok" | "unavailable",
            "string_status": "ok" | "unavailable",
            "nodes": [...],
            "edges": [...],
        }
    """
    if not gene or not str(gene).strip():
        return _unavailable_graph(str(gene or ""), "empty gene query")

    snapshot = pnc.load_snapshot(Path(cache_dir), gene)
    if snapshot is None:
        return _unavailable_graph(
            gene,
            f"no cached pathway/network snapshot for {gene.upper()} in {cache_dir} -- "
            "run pathway_network_cache.py as an offline batch job first",
        )

    center_symbol = str(snapshot.get("gene") or gene.upper())
    nodes: Dict[str, Dict[str, Any]] = {}
    edges: List[Dict[str, Any]] = []

    center_node: Dict[str, Any] = {"id": center_symbol, "type": "gene", "role": "query"}
    center_node.update(_gene_evidence(center_symbol, cards, readiness))
    nodes[center_symbol] = center_node

    sources = snapshot.get("sources", {}) or {}
    reactome = sources.get("reactome_pathways", {}) or {}
    string_net = sources.get("string_network", {}) or {}
    reactome_status = reactome.get("source_status")
    string_status = string_net.get("source_status")

    if reactome_status == "ok":
        for item in reactome.get("items", []):
            pathway_id = item.get("pathway_id")
            pathway_name = item.get("pathway_name")
            node_id = f"pathway:{pathway_id or pathway_name}"
            if node_id not in nodes:
                nodes[node_id] = {
                    "id": node_id,
                    "type": "pathway",
                    "pathway_id": pathway_id,
                    "pathway_name": pathway_name,
                    "is_in_disease": item.get("is_in_disease"),
                }
            edges.append(
                {
                    "source": center_symbol,
                    "target": node_id,
                    "relationship": "reactome_pathway_comembership",
                    "pathway_id": pathway_id,
                    "pathway_name": pathway_name,
                }
            )

    if string_status == "ok":
        for item in string_net.get("items", []):
            partner = item.get("partner")
            if not partner:
                continue
            if partner not in nodes:
                partner_node: Dict[str, Any] = {"id": partner, "type": "gene", "role": "string_partner"}
                partner_node.update(_gene_evidence(partner, cards, readiness))
                nodes[partner] = partner_node
            edges.append(
                {
                    "source": center_symbol,
                    "target": partner,
                    "relationship": "string_interaction",
                    "score": item.get("score"),
                }
            )

    reasons = []
    if reactome_status != "ok":
        reasons.append(f"reactome_pathways: {reactome.get('reason', reactome_status)}")
    if string_status != "ok":
        reasons.append(f"string_network: {string_net.get('reason', string_status)}")

    return {
        "gene": center_symbol,
        "available": True,
        "reason": "; ".join(reasons) if reasons else None,
        "fetched_at": snapshot.get("fetched_at"),
        "source_version": snapshot.get("source_version"),
        "reactome_status": reactome_status,
        "string_status": string_status,
        "nodes": list(nodes.values()),
        "edges": edges,
    }
