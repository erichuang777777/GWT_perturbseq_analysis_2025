"""Endpoint cross-checking a GWT target against an independent CRISPR screen, per gene.

Descriptive-only. Freimer2022_Screen.csv (PMID 36356142) sat in this repo unread since its
initial commit despite being registered in `docs/provenance_registry.csv` as a stated
cross-check source (see `docs/data_governance_checklist.md` §6). Never a readiness input. See
`freimer2022_crosscheck.py` for provenance and honesty constraints (`unknown != 0`).
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

import freimer2022_crosscheck

router = APIRouter(tags=["Concept profile (demo)"])


@router.get(
    "/api/freimer2022_crosscheck/{gene}",
    summary="Independent CRISPR-screen concordance for this gene (Freimer et al. 2022, descriptive)",
)
def get_freimer2022_crosscheck(gene: str) -> Dict[str, Any]:
    """Is this target also a hit in an independent CRISPR screen from a different lab/assay?

    Surfaces Freimer et al. 2022's own FACS-sort CRISPR screen statistics (IL2RA/IL2/CTLA4
    Treg/IL-2-axis readouts) for this gene, keyed by gene symbol: per screen, the `fdr`,
    `rank`, `lfc`, and `direction` (depleted/enriched) in both the negative- and
    positive-selection tail.

    This is a genuinely independent dataset (different lab, assay, and readout from this
    repo's own Perturb-seq) — real orthogonal corroboration, not a restatement.
    `significant` = `fdr < 0.05`. `in_screen_scope=False` means the gene was never tested
    (Freimer's screen covers ~1,350 genes, not the genome) — not a tested-and-negative
    result. `unknown != 0`: absence from `hits` never means a fabricated non-hit.
    Descriptive only — not a readiness input.
    """
    return freimer2022_crosscheck.freimer2022_crosscheck_for_target(gene)
