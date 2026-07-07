"""Offline-batch external-evidence cache: ClinicalTrials.gov, PubMed, Open Targets.

Design (see docs/IMPLEMENTATION_PLAN.md Module C):

- Cache-first, connector-backed. External APIs drift and rate-limit; every
  response is snapshotted to ``sources/target_tool_cache/_evidence/<gene>.json``
  with ``fetched_at`` + ``source_version``, and reused until a TTL expires.
- This module is an OFFLINE BATCH JOB, never called from a request handler.
  The dashboard/API only ever read the cached snapshot (see
  ``target_card_api.py``'s ``/api/evidence/*`` endpoints).
- Every fetcher degrades to ``source_status: "unavailable"`` on any network
  failure (blocked proxy, timeout, non-2xx, malformed response) instead of
  raising. A deployment without outbound network access to these APIs (for
  example, a sandboxed CI environment with an allowlisted egress proxy)
  still produces a valid, honest cache -- it just marks each source
  unavailable rather than crashing the batch job.

Hitting the public REST/GraphQL APIs directly (not the Claude-session MCP
connectors) is deliberate: this module runs inside the FastAPI backend as a
plain Python process, with no access to session-scoped MCP tools.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:  # pragma: no cover - requests is a project dependency
    requests = None  # type: ignore

CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"
PUBMED_ESEARCH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
OPEN_TARGETS_GRAPHQL_API = "https://api.platform.opentargets.org/api/v4/graphql"

SOURCE_VERSION = "external_evidence_cache/v1"
DEFAULT_TIMEOUT = 15
TTL_SECONDS_DEFAULT = 30 * 24 * 3600  # 30 days; external evidence changes slowly

# Immune indications used to scope trial/literature searches to CD4/autoimmune context,
# consistent with the tool's disease-relevance vocabulary (topic05 benchmark axes).
IMMUNE_CONDITIONS = ["autoimmune", "rheumatoid arthritis", "lupus", "inflammatory bowel disease", "psoriasis"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _unavailable(reason: str) -> Dict[str, Any]:
    return {"source_status": "unavailable", "reason": reason, "items": []}


def fetch_trials(gene: str, conditions: Optional[List[str]] = None, max_results: int = 10) -> Dict[str, Any]:
    """Query ClinicalTrials.gov API v2 for trials naming ``gene`` as an intervention."""
    if requests is None:
        return _unavailable("requests library not installed")
    conditions = conditions or IMMUNE_CONDITIONS
    try:
        resp = requests.get(
            CLINICALTRIALS_API,
            params={
                "query.intr": gene,
                "query.cond": " OR ".join(conditions),
                "pageSize": max_results,
                "fields": "NCTId,BriefTitle,Phase,OverallStatus,Condition,InterventionName",
            },
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # network, proxy, HTTP, or JSON errors all degrade gracefully
        return _unavailable(f"{type(exc).__name__}: {exc}")

    items = []
    for study in data.get("studies", []):
        protocol = study.get("protocolSection", {})
        ident = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        design = protocol.get("designModule", {})
        cond = protocol.get("conditionsModule", {})
        items.append(
            {
                "nct_id": ident.get("nctId"),
                "title": ident.get("briefTitle"),
                "phase": (design.get("phases") or [None])[0],
                "status": status.get("overallStatus"),
                "conditions": cond.get("conditions", []),
                "url": f"https://clinicaltrials.gov/study/{ident.get('nctId')}" if ident.get("nctId") else None,
            }
        )
    return {"source_status": "ok", "items": items}


def fetch_pubmed_literature(gene: str, context: str = "CD4 T cell", max_results: int = 10) -> Dict[str, Any]:
    """Query PubMed (NCBI E-utilities) for literature on ``gene`` in the given context."""
    if requests is None:
        return _unavailable("requests library not installed")
    query = f"{gene}[Title/Abstract] AND {context}"
    try:
        search = requests.get(
            PUBMED_ESEARCH_API,
            params={"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"},
            timeout=DEFAULT_TIMEOUT,
        )
        search.raise_for_status()
        ids = search.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return {"source_status": "ok", "items": []}
        summary = requests.get(
            PUBMED_ESUMMARY_API,
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
            timeout=DEFAULT_TIMEOUT,
        )
        summary.raise_for_status()
        result = summary.json().get("result", {})
    except Exception as exc:
        return _unavailable(f"{type(exc).__name__}: {exc}")

    items = []
    for pmid in ids:
        rec = result.get(pmid, {})
        if not rec:
            continue
        items.append(
            {
                "pmid": pmid,
                "title": rec.get("title"),
                "year": (rec.get("pubdate") or "")[:4],
                "journal": rec.get("fulljournalname") or rec.get("source"),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            }
        )
    return {"source_status": "ok", "items": items}


def fetch_open_targets(gene: str) -> Dict[str, Any]:
    """Query the Open Targets Platform GraphQL API for tractability/genetics/safety."""
    if requests is None:
        return _unavailable("requests library not installed")
    query = """
    query TargetEvidence($sym: String!) {
      search(queryString: $sym, entityNames: ["target"]) {
        hits { id name }
      }
    }
    """
    try:
        resp = requests.post(
            OPEN_TARGETS_GRAPHQL_API,
            json={"query": query, "variables": {"sym": gene}},
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return _unavailable(f"{type(exc).__name__}: {exc}")

    hits = (data.get("data", {}) or {}).get("search", {}).get("hits", [])
    return {"source_status": "ok", "items": hits}


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
    age = (datetime.now(timezone.utc) - fetched).total_seconds()
    return age > ttl_seconds


def build_evidence_for_gene(
    gene: str,
    cache_dir: Path,
    force: bool = False,
    ttl_seconds: int = TTL_SECONDS_DEFAULT,
) -> Dict[str, Any]:
    """Fetch (or reuse a cached) evidence snapshot for a single gene."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    existing = load_snapshot(cache_dir, gene)
    if existing and not force and not _is_stale(existing, ttl_seconds):
        return existing

    snapshot = {
        "gene": gene.upper(),
        "fetched_at": _now(),
        "source_version": SOURCE_VERSION,
        "sources": {
            "clinical_trials": fetch_trials(gene),
            "literature": fetch_pubmed_literature(gene),
            "open_targets": fetch_open_targets(gene),
        },
    }
    _cache_path(cache_dir, gene).write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return snapshot


def build_evidence_for_genes(
    genes: List[str],
    cache_dir: Path,
    force: bool = False,
    ttl_seconds: int = TTL_SECONDS_DEFAULT,
) -> Dict[str, Path]:
    """Batch build evidence snapshots for a gene list. Returns {gene: cache_path}."""
    out: Dict[str, Path] = {}
    for gene in genes:
        build_evidence_for_gene(gene, cache_dir, force=force, ttl_seconds=ttl_seconds)
        out[gene] = _cache_path(cache_dir, gene)
    return out


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch-build external evidence snapshots for a gene list.")
    parser.add_argument("genes", nargs="+", help="Gene symbols to fetch evidence for.")
    parser.add_argument("--cache-dir", type=Path, default=Path("sources/target_tool_cache/_evidence"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    results = build_evidence_for_genes(args.genes, args.cache_dir, force=args.force)
    for gene, path in results.items():
        snap = json.loads(path.read_text(encoding="utf-8"))
        statuses = {name: src.get("source_status") for name, src in snap["sources"].items()}
        print(f"{gene}: {statuses}")
