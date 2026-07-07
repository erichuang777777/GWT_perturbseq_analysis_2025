"""Lightweight, alias-tolerant gene/target search (B6).

The reviewed alternative was PostgreSQL trigram search (``pg_trgm``) plus an
alias table -- reasonable for a real multi-user platform, but that requires
provisioning a database service, which this project's owner has already
deprioritized (alongside multi-user persistence, §1.8 in
docs/IMPLEMENTATION_PLAN.md). For ~12,654 genes, a database is over-engineered
anyway per the review's own point ("對約兩萬個 gene + 少量 signature，這是過度工程").

This module gets the same practical outcome -- fast, alias-tolerant search
that survives typos and partial input -- using only the Python standard
library (``difflib``) plus the real alias table already built for gene
identifier resolution (B1, ``gene_identifier_resolver.py``). No new
dependency, no new infrastructure. If this ever becomes a true multi-user
platform with a real database, trigram search there is the natural
production upgrade -- noted, not built speculatively now.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Dict, List

from gene_identifier_resolver import GeneResolver

MATCH_TYPE_RANK = {"exact": 0, "alias": 1, "prefix": 2, "fuzzy": 3}


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def search_genes(resolver: GeneResolver, query: str, limit: int = 10, fuzzy_threshold: float = 0.6) -> List[Dict[str, Any]]:
    """Rank candidate genes for a (possibly partial/misspelled/aliased) query.

    Returns up to ``limit`` results, each with ``match_type`` (exact/alias/
    prefix/fuzzy) and a ``score`` in [0, 1], best first. Never raises; an
    empty or garbage query just returns no results rather than everything.
    """
    if not query or not str(query).strip():
        return []
    q = str(query).strip()
    q_upper = q.upper()

    results: Dict[str, Dict[str, Any]] = {}

    def _consider(gene_id: str, canonical: str, match_type: str, score: float) -> None:
        existing = results.get(gene_id)
        if existing is None or MATCH_TYPE_RANK[match_type] < MATCH_TYPE_RANK[existing["match_type"]] or (
            match_type == existing["match_type"] and score > existing["score"]
        ):
            results[gene_id] = {
                "ensembl_gene_id": gene_id,
                "canonical_symbol": canonical,
                "match_type": match_type,
                "score": round(score, 3),
            }

    # Tier 1: exact resolution (canonical, alias, Ensembl ID, case-insensitive) -- reuse B1 exactly.
    resolution = resolver.resolve(q)
    if resolution["matched"]:
        match_type = "alias" if "alias" in resolution["resolution_path"] else "exact"
        _consider(resolution["ensembl_gene_id"], resolution["canonical_symbol"], match_type, 1.0)

    canonical_map = resolver.canonical_symbols()
    alias_map = resolver.alias_symbols()

    # Tier 2: prefix match (the common "typed ZAP wanting ZAP70" case) over canonical symbols + aliases.
    for canonical, gene_id in canonical_map.items():
        if canonical.upper().startswith(q_upper):
            score = len(q_upper) / max(len(canonical), 1)
            _consider(gene_id, canonical, "prefix", 0.7 + 0.3 * score)
    for alias, gene_id in alias_map.items():
        if alias.upper().startswith(q_upper):
            canonical = resolver.canonical_symbol_for(gene_id)
            score = len(q_upper) / max(len(alias), 1)
            _consider(gene_id, canonical, "prefix", 0.6 + 0.3 * score)

    # Tier 3: fuzzy match (typo tolerance) over canonical symbols only -- aliases fuzzy-matched
    # too would risk too many low-quality hits for a 12k+ gene list.
    if len(results) < limit:
        for canonical, gene_id in canonical_map.items():
            sim = _similarity(q_upper, canonical.upper())
            if sim >= fuzzy_threshold:
                _consider(gene_id, canonical, "fuzzy", sim)

    ranked = sorted(results.values(), key=lambda r: (MATCH_TYPE_RANK[r["match_type"]], -r["score"]))
    return ranked[:limit]
