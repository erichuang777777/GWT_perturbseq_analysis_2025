"""Offline-batch pathway/network cache: Reactome + STRING.

Follows the same design as external_evidence_cache.py:

- Cache-first, connector-backed. Every response is snapshotted to
  ``sources/target_tool_cache/_pathway/<gene>.json`` with ``fetched_at`` +
  ``source_version``, reused until a TTL expires.
- OFFLINE BATCH JOB, never called from a request handler -- the
  dashboard/API only ever reads the cached snapshot.
- Every fetcher degrades to ``source_status: "unavailable"`` on any network
  failure instead of raising.

Hitting the public REST APIs directly (not the Claude-session MCP
connectors) is deliberate, for the same reason as external_evidence_cache.py:
this runs inside the FastAPI backend as a plain Python process.

Verified locally (2026-07) against real gene queries:
- CD3E (Ensembl ENSG00000198851) -> Reactome "Immunoregulatory interactions
  between a Lymphoid and a non-Lymphoid cell", "Downstream TCR signaling".
- CD3E -> STRING network correctly includes CD3D, CD3G, CD4, SYK (real TCR
  complex partners), not arbitrary genes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore

from common import degrade, timeutil

REACTOME_MAPPING_API = "https://reactome.org/ContentService/data/mapping/ENSEMBL/{ensembl_id}/pathways"
STRING_NETWORK_API = "https://string-db.org/api/json/network"

SOURCE_VERSION = "pathway_network_cache/v1"
DEFAULT_TIMEOUT = 15
TTL_SECONDS_DEFAULT = 30 * 24 * 3600  # 30 days; pathway/network annotations change slowly


# Re-export for backward compatibility -- canonical implementations now live
# in common/timeutil.py and common/degrade.py (architecture refactor Phase 1;
# see those modules' docstrings for the duplication this consolidates).
_now = timeutil.utc_now


def _unavailable(reason: str) -> Dict[str, Any]:
    return degrade.unavailable_source(reason)


def fetch_reactome_pathways(ensembl_id: str, species: str = "9606") -> Dict[str, Any]:
    """Low-level Reactome pathways containing this gene (by Ensembl gene id).

    Requires an Ensembl gene id (not a symbol) -- GWT target cards already
    carry ``ensembl_id``, so no separate symbol resolution step is needed
    here, unlike external_evidence_cache.py's Open Targets fetchers.
    """
    if requests is None:
        return _unavailable("requests library not installed")
    try:
        resp = requests.get(
            REACTOME_MAPPING_API.format(ensembl_id=ensembl_id),
            params={"species": species},
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return _unavailable(f"{type(exc).__name__}: {exc}")

    if not isinstance(data, list):
        return {"source_status": "ok", "items": []}
    items = [
        {"pathway_id": p.get("stId"), "pathway_name": p.get("displayName"), "is_in_disease": p.get("isInDisease")}
        for p in data
    ]
    return {"source_status": "ok", "items": items}


def fetch_string_network(gene_symbol: str, species: int = 9606, required_score: int = 700, limit: int = 15) -> Dict[str, Any]:
    """Direct STRING interaction partners for a gene symbol, score-thresholded."""
    if requests is None:
        return _unavailable("requests library not installed")
    try:
        resp = requests.get(
            STRING_NETWORK_API,
            params={
                "identifiers": gene_symbol,
                "species": species,
                "required_score": required_score,
                "limit": limit,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        edges = resp.json()
    except Exception as exc:
        return _unavailable(f"{type(exc).__name__}: {exc}")

    if not isinstance(edges, list):
        return {"source_status": "ok", "items": []}
    partners = sorted(
        {
            (e.get("preferredName_B") if e.get("preferredName_A", "").upper() == gene_symbol.upper() else e.get("preferredName_A"))
            for e in edges
        }
        - {gene_symbol.upper(), gene_symbol}
    )
    items = [
        {"partner": p, "score": max((e.get("score", 0) for e in edges if p in (e.get("preferredName_A"), e.get("preferredName_B"))), default=None)}
        for p in partners
    ]
    return {"source_status": "ok", "items": items}


def _cache_path(cache_dir: Path, gene: str) -> Path:
    safe_gene = "".join(c if c.isalnum() or c in "-_" else "_" for c in gene.upper())
    return Path(cache_dir) / f"{safe_gene}.json"


def load_snapshot(cache_dir: Path, gene: str) -> Optional[Dict[str, Any]]:
    path = _cache_path(cache_dir, gene)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _is_stale(snapshot: Dict[str, Any], ttl_seconds: int) -> bool:
    fetched_at = snapshot.get("fetched_at")
    if not fetched_at:
        return True
    try:
        fetched = datetime.fromisoformat(fetched_at)
    except ValueError:
        return True
    return (datetime.now(timezone.utc) - fetched).total_seconds() > ttl_seconds


def build_pathway_network_for_gene(
    gene_symbol: str,
    ensembl_id: Optional[str],
    cache_dir: Path,
    force: bool = False,
    ttl_seconds: int = TTL_SECONDS_DEFAULT,
) -> Dict[str, Any]:
    """Fetch (or reuse a cached) pathway + network snapshot for one gene.

    ``ensembl_id`` may be None -- Reactome lookup is then skipped with an
    explicit "no ensembl_id available" reason rather than guessing an id.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    existing = load_snapshot(cache_dir, gene_symbol)
    if existing and not force and not _is_stale(existing, ttl_seconds):
        return existing

    reactome = (
        fetch_reactome_pathways(ensembl_id)
        if ensembl_id
        else _unavailable("no ensembl_id available for this gene")
    )
    snapshot = {
        "gene": gene_symbol.upper(),
        "ensembl_id": ensembl_id,
        "fetched_at": _now(),
        "source_version": SOURCE_VERSION,
        "sources": {
            "reactome_pathways": reactome,
            "string_network": fetch_string_network(gene_symbol),
        },
    }
    _cache_path(cache_dir, gene_symbol).write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return snapshot


def build_pathway_network_for_genes(
    gene_to_ensembl: Dict[str, Optional[str]],
    cache_dir: Path,
    force: bool = False,
    ttl_seconds: int = TTL_SECONDS_DEFAULT,
) -> Dict[str, Path]:
    """Batch build. ``gene_to_ensembl`` maps gene symbol -> Ensembl id (or None)."""
    out: Dict[str, Path] = {}
    for gene, ensembl_id in gene_to_ensembl.items():
        build_pathway_network_for_gene(gene, ensembl_id, cache_dir, force=force, ttl_seconds=ttl_seconds)
        out[gene] = _cache_path(cache_dir, gene)
    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch-build pathway/network snapshots for a gene list.")
    parser.add_argument("genes", nargs="+", help="Gene symbols to fetch pathway/network data for.")
    parser.add_argument("--ensembl-ids", nargs="*", default=[], help="Matching Ensembl ids, same order as genes (optional).")
    parser.add_argument("--cache-dir", type=Path, default=Path("sources/target_tool_cache/_pathway"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    ensembl_map = {g: (args.ensembl_ids[i] if i < len(args.ensembl_ids) else None) for i, g in enumerate(args.genes)}
    results = build_pathway_network_for_genes(ensembl_map, args.cache_dir, force=args.force)
    for gene, path in results.items():
        snap = json.loads(path.read_text(encoding="utf-8"))
        statuses = {name: src.get("source_status") for name, src in snap["sources"].items()}
        print(f"{gene}: {statuses}")
