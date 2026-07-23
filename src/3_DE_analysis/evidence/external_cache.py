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
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

try:
    import requests
except ImportError:  # pragma: no cover - requests is a project dependency
    requests = None  # type: ignore

from common import degrade, timeutil
from config import settings

CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"
PUBMED_ESEARCH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
OPEN_TARGETS_GRAPHQL_API = "https://api.platform.opentargets.org/api/v4/graphql"

SOURCE_VERSION = "external_evidence_cache/v1"
DEFAULT_TIMEOUT = 15
TTL_SECONDS_DEFAULT = 30 * 24 * 3600  # 30 days; external evidence changes slowly

# Offline fallback for _clinicaltrials_count_for_drug: a pre-development literature-scan
# snapshot (327 rows, 36 immunomodulatory drugs, captured before this connector existed) that
# sat unused since its initial commit -- confirmed via full git-history search, see
# docs/data_governance_checklist.md §6. Engaged ONLY when the live API call fails; never
# presented as live data (source_status: "offline_snapshot", not "ok").
CLINICALTRIALS_OFFLINE_SNAPSHOT_PATH = settings.REPO_ROOT / "sources" / "topic13_clinicaltrials_flat.csv"

# Immune indications used to scope trial/literature searches to CD4/autoimmune context,
# consistent with the tool's disease-relevance vocabulary (topic05 benchmark axes).
IMMUNE_CONDITIONS = ["autoimmune", "rheumatoid arthritis", "lupus", "inflammatory bowel disease", "psoriasis"]


# Re-export for backward compatibility -- canonical implementations now live
# in common/timeutil.py and common/degrade.py (architecture refactor Phase 1;
# see those modules' docstrings for the duplication this consolidates).
_now = timeutil.utc_now


def _unavailable(reason: str) -> Dict[str, Any]:
    return degrade.unavailable_source(reason)


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


# Absolute, documented, re-derivable literature-count -> novelty tier thresholds.
# These are on the total PubMed hit count for "<gene>[Title/Abstract] AND <context>",
# NOT the (<=max_results) items actually pulled back. A tier is deliberately an
# absolute cut (no cohort needed) so a single gene's novelty is a self-contained,
# reproducible fact; a cohort *percentile* can be layered on at export time on top
# of the raw ``total_count`` when the whole covered set is in hand.
#   unknown  -> fetch failed / count not measured (unknown != 0, never a silent 0)
#   no_record-> the query genuinely returned 0 hits (a real zero, not "unknown")
#   understudied / moderate / well_studied -> increasing literature depth
NOVELTY_TIER_THRESHOLDS = ((10, "understudied"), (100, "moderate"))


def novelty_from_literature_count(total_count: Optional[int]) -> Dict[str, Any]:
    """Pure, deterministic novelty descriptor from a PubMed total hit count.

    ``total_count is None`` -> ``{"tier": "unknown", ...}`` (the fetch failed or the
    count was never measured -- honest unknown, never 0). ``total_count == 0`` ->
    ``no_record`` (a genuine zero: the query ran and found nothing). Otherwise a
    tier from ``NOVELTY_TIER_THRESHOLDS`` plus a monotonic ``novelty_score`` in
    (0, 1] where HIGHER = more novel (fewer papers): ``1 / (1 + log10(count + 1))``.
    Descriptive only -- never read by the readiness engine.
    """
    if total_count is None:
        return {"tier": "unknown", "total_count": None, "novelty_score": None}
    count = int(total_count)
    if count <= 0:
        # A measured zero is the MOST novel end of the scale, but still honestly
        # distinguished from "unknown" so downstream never conflates the two.
        return {"tier": "no_record", "total_count": 0, "novelty_score": 1.0}
    tier = "well_studied"
    for ceiling, name in NOVELTY_TIER_THRESHOLDS:
        if count <= ceiling:
            tier = name
            break
    score = 1.0 / (1.0 + math.log10(count + 1))
    return {"tier": tier, "total_count": count, "novelty_score": round(score, 4)}


def fetch_pubmed_literature(gene: str, context: Optional[str] = None, max_results: int = 10) -> Dict[str, Any]:
    """Query PubMed (NCBI E-utilities) for literature on ``gene`` in the given context.

    ``context`` defaults to the deployment's domain context
    (``domain_context.pubmed_context()`` — ``"CD4 T cell"`` unless overridden via
    ``GWT_PUBMED_CONTEXT``), so a non-CD4 dataset measures novelty in ITS context.

    Returns the (<=``max_results``) most relevant ``items`` AND ``total_count`` --
    the full esearch hit count, which is the actual novelty signal (see
    ``novelty_from_literature_count``). ``total_count`` is a genuine measurement:
    ``0`` means the query ran and matched nothing, distinct from a failed fetch
    (``source_status: unavailable``, no ``total_count``).
    """
    if requests is None:
        return _unavailable("requests library not installed")
    if context is None:
        from domain_context import pubmed_context

        context = pubmed_context()
    query = f"{gene}[Title/Abstract] AND {context}"
    try:
        search = requests.get(
            PUBMED_ESEARCH_API,
            params={"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"},
            timeout=DEFAULT_TIMEOUT,
        )
        search.raise_for_status()
        esearch = search.json().get("esearchresult", {})
        ids = esearch.get("idlist", [])
        try:
            total_count = int(esearch.get("count"))
        except (TypeError, ValueError):
            total_count = len(ids)  # fall back to what we can see rather than fabricate
        novelty = novelty_from_literature_count(total_count)
        if not ids:
            return {"source_status": "ok", "items": [], "total_count": total_count, "novelty": novelty}
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
    return {"source_status": "ok", "items": items, "total_count": total_count, "novelty": novelty}


def _open_targets_resolve_ensembl_id(gene: str) -> Optional[str]:
    """Resolve a gene symbol to its Ensembl target id via Open Targets search.

    Returns None (not an exception) when no target hit is found -- callers
    treat that as "gene not found in Open Targets", distinct from a network
    failure.
    """
    query = """
    query SearchGene($sym: String!) {
      search(queryString: $sym, entityNames: ["target"]) {
        hits { id name }
      }
    }
    """
    resp = requests.post(
        OPEN_TARGETS_GRAPHQL_API,
        json={"query": query, "variables": {"sym": gene}},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    hits = (resp.json().get("data", {}) or {}).get("search", {}).get("hits", [])
    for hit in hits:
        if hit.get("name", "").upper() == gene.upper():
            return hit.get("id")
    return hits[0].get("id") if hits else None


def fetch_open_targets(gene: str) -> Dict[str, Any]:
    """Query the Open Targets Platform GraphQL API for tractability/genetics/safety.

    Fixed 2026-07: the previous implementation only ran the ``search`` query
    (entity lookup by name) and never followed up with a ``target(...)``
    query, so despite the docstring, no tractability/genetics/safety field
    was ever actually fetched -- every snapshot silently carried empty
    evidence. This version resolves the gene to its Ensembl id, then pulls:

    - ``tractability``: small-molecule / antibody / PROTAC / other-modality
      buckets (feeds ``readiness_engine``'s ``tractability_score``, currently
      stuck at "unknown" for most genes).
    - ``associatedDiseases``: genetic-association evidence per disease,
      including the ``genetic_association`` datatype score (feeds
      ``human_genetic_support``).
    - ``safetyLiabilities``: known safety-liability events with affected
      tissues, when Open Targets has curated any for this target.
    """
    if requests is None:
        return _unavailable("requests library not installed")

    try:
        ensembl_id = _open_targets_resolve_ensembl_id(gene)
    except Exception as exc:
        return _unavailable(f"{type(exc).__name__}: {exc}")

    if ensembl_id is None:
        return {"source_status": "ok", "items": [], "tractability": [], "associated_diseases": [], "safety_liabilities": []}

    full_query = """
    query TargetEvidence($id: String!) {
      target(ensemblId: $id) {
        approvedSymbol
        tractability { label modality value }
        safetyLiabilities { event eventId biosamples { tissueLabel } }
        knownDrugs(size: 20) {
          count
          rows {
            phase
            status
            drug { id name isApproved maximumClinicalTrialPhase }
          }
        }
        associatedDiseases(page: {index: 0, size: 15}) {
          count
          rows {
            disease { id name }
            score
            datatypeScores { id score }
          }
        }
      }
    }
    """
    try:
        resp = requests.post(
            OPEN_TARGETS_GRAPHQL_API,
            json={"query": full_query, "variables": {"id": ensembl_id}},
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return _unavailable(f"{type(exc).__name__}: {exc}")

    target = (data.get("data", {}) or {}).get("target") or {}
    if not target:
        errors = data.get("errors")
        return _unavailable(f"GraphQL error or unknown ensembl id {ensembl_id}: {errors}")

    tractability = target.get("tractability") or []
    diseases_block = target.get("associatedDiseases") or {}
    associated_diseases = [
        {
            "disease": (row.get("disease") or {}).get("name"),
            "disease_id": (row.get("disease") or {}).get("id"),
            "overall_score": row.get("score"),
            "genetic_association_score": next(
                (d.get("score") for d in (row.get("datatypeScores") or []) if d.get("id") == "genetic_association"),
                None,
            ),
        }
        for row in (diseases_block.get("rows") or [])
    ]
    safety_liabilities = [
        {
            "event": item.get("event"),
            "event_id": item.get("eventId"),
            "tissues": [b.get("tissueLabel") for b in (item.get("biosamples") or [])],
        }
        for item in (target.get("safetyLiabilities") or [])
    ]

    known_drugs = _summarize_known_drugs(target.get("knownDrugs") or {})

    return {
        "source_status": "ok",
        "items": [{"id": ensembl_id, "name": target.get("approvedSymbol")}],
        "tractability": tractability,
        "known_drugs": known_drugs,
        "associated_diseases": associated_diseases,
        "safety_liabilities": safety_liabilities,
    }


# Open Targets clinical-trial phase is 0-4 (4 = approved); we surface the max
# and whether ANY known drug is marked approved, as a disease-AGNOSTIC per-target
# tractability summary (plan P1-L). This is a summary of drugs known to hit THIS
# target, NOT a claim that the target is druggable the same way here, and NOT a
# treatment recommendation -- the disease-specific check stays in the separate
# /api/disease-drug-evidence route (match_disease_drug_evidence).
def _summarize_known_drugs(known: Dict[str, Any]) -> Dict[str, Any]:
    rows = known.get("rows") or []
    drugs: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        drug = row.get("drug") or {}
        name = drug.get("name")
        if not name:
            continue
        phase = drug.get("maximumClinicalTrialPhase")
        if phase is None:
            phase = row.get("phase")
        prev = drugs.get(name)
        if prev is None or (phase is not None and (prev.get("max_phase") or -1) < phase):
            drugs[name] = {
                "name": name,
                "max_phase": phase,
                "is_approved": bool(drug.get("isApproved")),
                "status": row.get("status"),
            }
    drug_list = sorted(drugs.values(), key=lambda d: (d.get("max_phase") or -1), reverse=True)
    phases = [d["max_phase"] for d in drug_list if d["max_phase"] is not None]
    return {
        # `count` is Open Targets' total known-drug row count; `known_drug_count`
        # is our distinct-drug count from the (<=20) rows pulled.
        "count": known.get("count"),
        "known_drug_count": len(drug_list),
        "max_clinical_phase": max(phases) if phases else None,
        "any_approved": any(d["is_approved"] for d in drug_list),
        "drugs": drug_list[:10],
    }




KNOWN_T_CELL_ENGAGER_DRUGS = {
    "BLINATUMOMAB", "MOSUNETUZUMAB", "GLOFITAMAB", "TECLISTAMAB", "ELRANATAMAB",
    "TALQUETAMAB", "EPCORITAMAB", "ODRONEXTAMAB", "TARLATAMAB", "SOLITOMAB",
    "FLOTETUZUMAB", "CATUMAXOMAB", "ERTUMAXOMAB", "MEDI-565", "FBT-A05",
}  # curated from real Open Targets CD3E query results, not inferred from naming


def _drug_class(drug_name: Optional[str], drug_type: Optional[str]) -> str:
    """Classify a drug for CAR-T/immuno relevance -- honest, not exhaustive.

    Bispecific T-cell engagers (BiTE-class) share a mechanism with CAR-T's
    CD3-activation domain, so genes whose known drugs fall in this bucket
    are naturally CAR-T-adjacent targets. Membership is checked against a
    curated list (drugType alone can't distinguish a T-cell engager from an
    ordinary antibody), not guessed from name patterns.
    """
    if not drug_name:
        return "unknown"
    if drug_name.upper() in KNOWN_T_CELL_ENGAGER_DRUGS:
        return "bispecific_T_cell_engager"
    dt = (drug_type or "").lower()
    if dt == "antibody":
        return "monoclonal_antibody"
    if dt == "small molecule":
        return "small_molecule"
    if dt in ("protein", "enzyme"):
        return "protein_therapeutic"
    return "other_or_unknown"

def _open_targets_known_drugs(ensembl_id: str) -> List[Dict[str, Any]]:
    """Known/investigational drugs directly targeting this gene (Open Targets)."""
    query = """
    query TargetDrugs($id: String!) {
      target(ensemblId: $id) {
        drugAndClinicalCandidates {
          count
          rows { maxClinicalStage drug { id name drugType } }
        }
      }
    }
    """
    resp = requests.post(
        OPEN_TARGETS_GRAPHQL_API,
        json={"query": query, "variables": {"id": ensembl_id}},
        timeout=DEFAULT_TIMEOUT,
    )
    resp.raise_for_status()
    target = (resp.json().get("data", {}) or {}).get("target") or {}
    rows = ((target.get("drugAndClinicalCandidates") or {}).get("rows")) or []
    out = []
    for r in rows:
        name = (r.get("drug") or {}).get("name")
        dtype = (r.get("drug") or {}).get("drugType")
        out.append(
            {
                "drug_name": name,
                "drug_type": dtype,
                "drug_class": _drug_class(name, dtype),
                "max_clinical_stage": r.get("maxClinicalStage"),
            }
        )
    return out


_OFFLINE_SNAPSHOT_CACHE: Dict[str, Optional[pd.DataFrame]] = {}
_OFFLINE_SNAPSHOT_LOADED = False


def _load_clinicaltrials_offline_snapshot() -> Optional[pd.DataFrame]:
    """Load the pre-development ClinicalTrials.gov snapshot, once, cached.

    Returns ``None`` (not an exception) when the file is absent -- callers treat that as
    "no offline fallback available", never a crash.
    """
    global _OFFLINE_SNAPSHOT_LOADED
    if _OFFLINE_SNAPSHOT_LOADED:
        return _OFFLINE_SNAPSHOT_CACHE.get("df")
    _OFFLINE_SNAPSHOT_LOADED = True
    if not CLINICALTRIALS_OFFLINE_SNAPSHOT_PATH.exists():
        _OFFLINE_SNAPSHOT_CACHE["df"] = None
        return None
    df = pd.read_csv(CLINICALTRIALS_OFFLINE_SNAPSHOT_PATH)
    _OFFLINE_SNAPSHOT_CACHE["df"] = df
    return df


def _clinicaltrials_count_for_drug_offline(drug_name: str, disease_name: str) -> Optional[Dict[str, Any]]:
    """Offline fallback for ``_clinicaltrials_count_for_drug``, used only when the live API fails.

    Matches ``drug_name`` against the snapshot's ``search_term`` column (case-insensitive
    substring, since a few search terms are composite phrases like "CD25 daclizumab" rather
    than a bare drug name), then counts snapshot rows whose free-text ``conditions`` field
    contains ``disease_name`` as a substring -- an approximation of the live API's
    ``query.cond`` filter, not an identical query.

    Returns ``None`` (not a 0) when the drug is outside the snapshot's ~36-drug coverage --
    that is "no offline data available", never "zero trials found". Never returns
    ``source_status: "ok"`` -- this is stale, partial data, always labelled
    ``"offline_snapshot"`` with an explicit coverage caveat so a caller can't mistake it for
    a live count.
    """
    df = _load_clinicaltrials_offline_snapshot()
    if df is None:
        return None
    drug_lower = drug_name.strip().lower()
    matched = df[df["search_term"].astype(str).str.lower().apply(
        lambda term: drug_lower in term or term in drug_lower
    )]
    if matched.empty:
        return None
    disease_lower = disease_name.strip().lower()
    hits = matched[matched["conditions"].astype(str).str.lower().str.contains(disease_lower, na=False)]
    return {
        "source_status": "offline_snapshot",
        "n_trials": int(len(hits)),
        "reason": "live ClinicalTrials.gov API unreachable; using a pre-development snapshot",
        "snapshot_note": (
            "This count is from a static snapshot (sources/topic13_clinicaltrials_flat.csv, "
            "~36 pre-selected immunomodulatory drugs, captured before this connector existed), "
            "NOT a live query -- coverage is limited to drugs in that snapshot and the count is "
            "a substring match on free-text conditions, not the live API's structured filter. "
            "Treat as directional only; re-run when the live API is reachable for an authoritative count."
        ),
    }


def _clinicaltrials_count_for_drug(drug_name: str, disease_name: str) -> Dict[str, Any]:
    """Count ClinicalTrials.gov studies actually pairing this drug with this disease.

    This is the step that keeps evidence-matching honest: Open Targets says a
    drug targets a gene, but does not say the drug has ever been trialled for
    the *disease the user asked about*. A drug's real approved/trialled
    indication (e.g. basiliximab -> kidney transplant, not rheumatoid
    arthritis) must be checked against the disease actually queried, not
    assumed from the gene-disease genetic association alone.

    Falls back to a static offline snapshot (``_clinicaltrials_count_for_drug_offline``)
    ONLY when the live call fails and the drug happens to be in that snapshot's small
    coverage -- otherwise degrades to ``source_status: "unavailable"`` exactly as before.
    """
    try:
        resp = requests.get(
            CLINICALTRIALS_API,
            params={
                "query.intr": drug_name,
                "query.cond": disease_name,
                "pageSize": 1,
                "countTotal": "true",
                "fields": "NCTId",
            },
            timeout=DEFAULT_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return {"source_status": "ok", "n_trials": data.get("totalCount")}
    except Exception as exc:
        offline = _clinicaltrials_count_for_drug_offline(drug_name, disease_name)
        if offline is not None:
            return offline
        return {"source_status": "unavailable", "reason": f"{type(exc).__name__}: {exc}", "n_trials": None}


def match_disease_drug_evidence(gene: str, disease_name: str, max_drugs: int = 10) -> Dict[str, Any]:
    """Evidence-matching only -- NOT a treatment recommendation or efficacy prediction.

    Given a gene and a disease name, this answers two separate, checkable
    questions -- and keeps them separate rather than collapsing them into a
    single score:

    1. Does Open Targets know of any drug (approved or in clinical
       development) whose target is this gene?
    2. For each such drug, has it actually been trialled for *this* disease
       on ClinicalTrials.gov -- as opposed to some other indication entirely?

    A drug can legitimately target the right gene and still have zero
    trials for the disease asked about (e.g. IL2RA's approved antibody
    basiliximab is trialled extensively for kidney-transplant rejection, not
    for rheumatoid arthritis) -- that is not a bug in this function, it is
    the honest signal the tool exists to surface. Verified drug-indication
    pairings must still be confirmed against the drug label and a qualified
    physician; this function never outputs a dose, a drug choice, or a
    prediction of efficacy for any individual patient.

    Returns ``{"available": False, "reason": ...}`` when Open Targets has no
    entry for the gene or the network is unavailable -- never a fabricated
    match.
    """
    if requests is None:
        return {"available": False, "reason": "requests library not installed"}

    try:
        ensembl_id = _open_targets_resolve_ensembl_id(gene)
    except Exception as exc:
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}

    if ensembl_id is None:
        return {"available": False, "reason": f"gene '{gene}' not found in Open Targets"}

    try:
        drugs = _open_targets_known_drugs(ensembl_id)
    except Exception as exc:
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}

    drugs = drugs[:max_drugs]
    for d in drugs:
        if d["drug_name"]:
            d["trials_for_this_disease"] = _clinicaltrials_count_for_drug(d["drug_name"], disease_name)

    return {
        "available": True,
        "gene": gene.upper(),
        "disease_queried": disease_name,
        "ensembl_id": ensembl_id,
        "n_known_drugs_for_gene": len(drugs),
        "drugs": drugs,
        "caveat": (
            "evidence-matching only -- not a treatment recommendation or efficacy "
            "prediction; a nonzero drug count for this gene does not mean the drug "
            "has been trialled for the disease queried (see trials_for_this_disease "
            "per drug); verified drug-indication pairings must be confirmed against "
            "the drug label and a qualified physician"
        ),
        "fetched_at": _now(),
        "source_version": SOURCE_VERSION,
    }

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