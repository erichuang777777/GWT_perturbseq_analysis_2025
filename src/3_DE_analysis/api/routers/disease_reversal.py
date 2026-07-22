"""Disease-signature reversal endpoints (development plan P0-K, the system core).

Descriptive-only. Answers "does knocking this target down push cells AWAY from a
disease state?" over the in-repo signed DE table (`full_signed_DE`). A signature is
a set of disease-UP and disease-DOWN genes; a knockdown REVERSES it if it drives the
up-genes down and the down-genes up. See `disease_reversal.py` for the method and
honesty constraints (`unknown != 0`, CRISPRi != pharmacology, context-mismatch).

Two entry points, mirroring the two evidence idioms already in this API:
* ``GET  /api/disease_reversal/{gene}`` — a fixed **builtin** signature (snapshot-like,
  a named in-repo contrast), per-target profile across conditions.
* ``POST /api/disease_reversal`` — a **user-supplied** signature (open-ended, like
  ``/api/disease-drug-evidence``'s live disease param), ranked across all targets.

Never a readiness input; does not cap any readiness call.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import disease_reversal

router = APIRouter(tags=["Disease reversal (research use)"])


class SignatureRequest(BaseModel):
    up: List[str] = []            # genes UP in the disease/contrast
    down: List[str] = []          # genes DOWN in the disease/contrast
    condition: Optional[str] = None   # Rest | Stim8hr | Stim48hr | None (all)
    top: int = 50
    min_hits: int = 3


@router.get(
    "/api/disease_reversal/signatures",
    summary="List the builtin in-repo disease/contrast signatures",
)
def list_signatures() -> Dict[str, Any]:
    out = []
    for sig_id, spec in disease_reversal.BUILTIN_SIGNATURES.items():
        entry: Dict[str, Any] = {"id": sig_id, "label": spec.get("label", sig_id)}
        try:
            sig = disease_reversal.load_builtin_signature(sig_id)
            entry["n_up"] = len(sig["up"])
            entry["n_down"] = len(sig["down"])
            entry["available"] = True
        except Exception as exc:  # noqa: BLE001 -- honest per-signature degrade
            entry["available"] = False
            entry["reason"] = f"{type(exc).__name__}: {exc}"
        out.append(entry)
    return {"signatures": out}


@router.get(
    "/api/disease_reversal/_rank_builtin",
    summary="Rank all targets by reversal of a builtin signature (descriptive)",
)
def rank_builtin_signature(
    signature: str = Query(default="th2_vs_th1_polarization", description="a builtin signature id"),
    condition: Optional[str] = Query(default=None),
    top: int = Query(default=50, ge=1, le=1000),
    min_hits: int = Query(default=3, ge=1),
) -> Dict[str, Any]:
    """Cohort ranking for a builtin signature (the GET twin of the POST route).

    Lets the live tool rank every perturbation against a named in-repo signature
    without shipping its (large) gene list to the client. Descriptive only.
    """
    try:
        sig = disease_reversal.load_builtin_signature(signature)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    out = disease_reversal.rank_reversal(sig, condition=condition or None, top=top, min_hits=min_hits)
    out["signature"] = signature
    return out


@router.get(
    "/api/disease_reversal/{gene}",
    summary="Per-target disease-reversal profile against a builtin signature (descriptive)",
)
def get_reversal_for_target(
    gene: str,
    signature: str = Query(default="th2_vs_th1_polarization", description="a builtin signature id"),
) -> Dict[str, Any]:
    """Does knocking down this target REVERSE or WORSEN the named disease signature?

    `unknown != 0`: condition rows with no measured signature gene downstream are
    absent, never 0. `n_signature_hit`/`n_signature_total` travel with each score.
    Descriptive only — not a readiness input.
    """
    try:
        sig = disease_reversal.load_builtin_signature(signature)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    out = disease_reversal.reversal_for_target(gene, sig)
    out["signature"] = signature
    return out


@router.post(
    "/api/disease_reversal",
    summary="Rank all targets by reversal of a user-supplied disease signature (descriptive)",
)
def rank_user_signature(req: SignatureRequest) -> Dict[str, Any]:
    """Bring your own disease signature (up/down gene sets) and rank every
    perturbation by how strongly its knockdown reverses it.

    Honest empty when the signed-DE table isn't present. `min_hits` (reported back)
    drops low-support rows before ranking. Descriptive only — never a readiness input.
    """
    if not req.up and not req.down:
        raise HTTPException(status_code=422, detail="signature is empty: provide at least one up or down gene")
    signature = {"up": set(req.up), "down": set(req.down)}
    return disease_reversal.rank_reversal(
        signature, condition=req.condition, top=req.top, min_hits=req.min_hits
    )
