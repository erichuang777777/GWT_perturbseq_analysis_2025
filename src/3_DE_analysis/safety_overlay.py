"""Membrane/tractability + safety-window overlays (§1.12 / ADC ingestion spec).

Supersedes the "concept only" status of
``docs/external_overlay_integration_concept.md`` for the membrane-protein
half: the project owner's private ADC target-discovery database
(``candidate_genes.parquet``) has been joined against this repo's real
11,526 GWT targets and checked in as
``docs/mvp-research/adc_overlay_gwt_overlap_full.csv`` (5,588 overlapping
genes, ~49% coverage; see
``docs/mvp-research/ADC_LOCAL_DATA_INGESTION_SPEC.md`` for the full data
audit). This module reads that real, checked-in overlap table.

The safety-window half (GTEx off-context expression breadth,
``gtex_per_tissue.parquet``) is NOT yet available in this checkout -- the raw
file lives only on the project owner's machine
(``~/Downloads/adc_web_data/``) and has not been placed under
``sources/target_tool_cache/_overlays/`` yet. ``load_gtex_safety_overlay``
follows the exact same honest-fallback contract as ``cre_schema.py``: until
that file is supplied, it returns an explicit ``available: False`` rather
than fabricating a safety score. Point ``settings.GTEX_PER_TISSUE_PATH`` at
the real file once it's added and this starts working with no other code
change.

Coverage is intentionally partial (~49% of GWT targets) -- a gene absent
from the overlay is genuinely unchecked, not "not druggable"/"not safe";
every lookup function here follows the same ``unknown`` contract as
``readiness_engine.py``'s existing ``_tractability``/``_human_genetic``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from config import settings

UNKNOWN = "unknown"

MEMBRANE_OVERLAY_PATH_DEFAULT = (
    settings.REPO_ROOT / "docs" / "mvp-research" / "adc_overlay_gwt_overlap_full.csv"
)
# Not yet supplied in this checkout -- see module docstring. Placeholder path
# only; load_gtex_safety_overlay degrades honestly until this file exists.
GTEX_PER_TISSUE_PATH_DEFAULT = settings.REPO_ROOT / "sources" / "target_tool_cache" / "_overlays" / "gtex_per_tissue.parquet"

MEMBRANE_OVERLAY_REQUIRED_COLUMNS = [
    "gene_symbol",
    "ensembl_id",
    "is_surface_protein",
    "has_transmembrane_domain",
    "has_extracellular_domain",
    "is_druggable",
    "druggable_pathway",
]

# Same modality vocabulary as build_target_cards.DRUGGABLE_CLASS_MODALITY, so
# this overlay's output is a drop-in for readiness_engine._tractability's
# return shape (modality, score).
MODALITY_ANTIBODY_SURFACE = "antibody (surface)"
MODALITY_ANTIBODY_BIOLOGIC = "antibody / biologic"
MODALITY_SMALL_MOLECULE = "small molecule"


def empty_membrane_overlay_table() -> pd.DataFrame:
    return pd.DataFrame(columns=MEMBRANE_OVERLAY_REQUIRED_COLUMNS)


def load_membrane_tractability_overlay(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the real ADC-derived membrane/tractability overlay (join key: Ensembl gene ID).

    Returns ``{"available": bool, "reason": str|None, "table": DataFrame}``.
    Never raises; a missing or malformed file produces an explicit
    ``available: False`` with an empty table.
    """
    resolved = Path(path) if path is not None else MEMBRANE_OVERLAY_PATH_DEFAULT
    if not resolved.exists():
        return {
            "available": False,
            "reason": f"membrane overlay file not found: {resolved}",
            "table": empty_membrane_overlay_table(),
        }
    df = pd.read_csv(resolved)
    missing = [c for c in MEMBRANE_OVERLAY_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return {
            "available": False,
            "reason": f"membrane overlay file missing required columns: {missing}",
            "table": empty_membrane_overlay_table(),
        }
    return {"available": True, "reason": None, "table": df}


def load_gtex_safety_overlay(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load per-gene GTEx off-context expression breadth for safety_window_score.

    Not yet available in this checkout (see module docstring) -- returns an
    honest ``available: False`` until ``gtex_per_tissue.parquet`` is supplied
    at ``GTEX_PER_TISSUE_PATH_DEFAULT`` (or an explicit ``path``).
    """
    resolved = Path(path) if path is not None else GTEX_PER_TISSUE_PATH_DEFAULT
    if not resolved.exists():
        return {
            "available": False,
            "reason": f"GTEx per-tissue expression file not found: {resolved} "
            "(not yet placed in this checkout -- see docs/mvp-research/ADC_LOCAL_DATA_INGESTION_SPEC.md §3)",
            "table": pd.DataFrame(columns=["ensembl_id", "n_tissues_expressed", "max_expression_outside_cd4_context"]),
        }
    df = pd.read_parquet(resolved)
    return {"available": True, "reason": None, "table": df}


def tractability_from_membrane_overlay(gene_ensembl: str, overlay: Dict[str, Any]) -> Tuple[str, Any]:
    """(modality, score) from the real membrane/tractability overlay, else ``(unknown, unknown)``.

    Mirrors readiness_engine._tractability's three-state contract:
    gene absent from the overlay -> unknown (not checked, not "undruggable");
    gene present but no membrane/druggability signal -> ("none", 0);
    gene present with a signal -> a real modality + score 3.
    """
    if not overlay.get("available") or not gene_ensembl:
        return UNKNOWN, UNKNOWN
    table = overlay["table"]
    row = table[table["ensembl_id"] == gene_ensembl]
    if row.empty:
        return UNKNOWN, UNKNOWN
    r = row.iloc[0]
    is_surface = bool(r["is_surface_protein"])
    has_extracellular = bool(r["has_extracellular_domain"])
    has_transmembrane = bool(r["has_transmembrane_domain"])
    is_druggable = bool(r["is_druggable"])

    if is_surface and has_extracellular:
        return MODALITY_ANTIBODY_SURFACE, 3
    if is_surface or has_transmembrane:
        return MODALITY_ANTIBODY_BIOLOGIC, 3
    if is_druggable:
        return MODALITY_SMALL_MOLECULE, 3
    return "none", 0


def safety_window_from_gtex(gene_ensembl: str, overlay: Dict[str, Any]) -> Any:
    """Off-context expression-breadth-derived safety signal, else ``unknown``.

    Always returns ``unknown`` until ``load_gtex_safety_overlay`` has real
    data (see that function's docstring) -- this is the honest, current
    behavior in this checkout, not a bug.
    """
    if not overlay.get("available") or not gene_ensembl:
        return UNKNOWN
    table = overlay["table"]
    row = table[table["ensembl_id"] == gene_ensembl]
    if row.empty:
        return UNKNOWN
    return int(row.iloc[0]["n_tissues_expressed"])
