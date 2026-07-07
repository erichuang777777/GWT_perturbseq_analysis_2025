"""External-evidence endpoints (architecture refactor Phase 4, §4.1)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from api import deps
from evidence.external_cache import build_evidence_for_genes, load_snapshot as load_evidence_snapshot

router = APIRouter(tags=["evidence"])


class EvidenceBuildRequest(BaseModel):
    dataset_id: Optional[str] = None
    genes: Optional[List[str]] = None
    top_n: int = 20
    force: bool = False


@router.get("/api/evidence/{gene}")
def get_evidence(gene: str) -> Dict[str, Any]:
    snapshot = load_evidence_snapshot(deps.EVIDENCE_CACHE_DIR, gene)
    if snapshot is None:
        raise HTTPException(status_code=404, detail=f"no evidence snapshot fetched yet for {gene}")
    return snapshot


@router.post("/api/evidence/build")
def build_evidence(req: EvidenceBuildRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    genes = list(req.genes or [])
    if req.dataset_id:
        out_csv = deps._dataset_path(req.dataset_id) / "target_cards.csv"
        if not out_csv.exists():
            raise HTTPException(status_code=404, detail="dataset_id not found")
        df = deps._load_cards(out_csv)
        df = df.sort_values(
            by=[c for c in ["statistical_evidence_grade", "n_total_de_genes"] if c in df.columns],
            ascending=False,
        )
        genes.extend(df["target"].dropna().astype(str).str.upper().unique().tolist()[: req.top_n])
    genes = list(dict.fromkeys(g.upper() for g in genes if g))[: deps.MAX_EVIDENCE_GENES]
    if not genes:
        raise HTTPException(status_code=400, detail="no genes to build evidence for (pass dataset_id or genes)")

    # Report what is already cached synchronously (no network); schedule only the
    # missing/forced genes as a BACKGROUND task so the request returns promptly
    # and external fetches never block the HTTP response (external_evidence_cache
    # is designed as an offline batch job, not a request-path call).
    cached: Dict[str, Any] = {}
    to_fetch = []
    for gene in genes:
        snap = load_evidence_snapshot(deps.EVIDENCE_CACHE_DIR, gene)
        if snap is not None and not req.force:
            cached[gene] = {name: src.get("source_status") for name, src in snap.get("sources", {}).items()}
        else:
            to_fetch.append(gene)

    if to_fetch:
        background_tasks.add_task(build_evidence_for_genes, to_fetch, deps.EVIDENCE_CACHE_DIR, force=req.force)

    return {
        "genes": genes,
        "cache_dir": str(deps.EVIDENCE_CACHE_DIR),
        "cached": cached,
        "scheduled": to_fetch,
        "note": "scheduled genes are fetched in the background; poll GET /api/evidence/{gene} for results",
    }
