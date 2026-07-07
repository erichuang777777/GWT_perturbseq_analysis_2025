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

The safety-window half is now also real: ``gtex_per_tissue.parquet`` at
``sources/target_tool_cache/_overlays/gtex_per_tissue.parquet`` is a
pre-aggregated, per-gene table (``ensembl_id``, ``gene_symbol``,
``n_tissues_expressed``, ``max_expression_outside_cd4_context``), derived
from public GTEx per-tissue median TPM. Critically, the aggregation already
excludes CD4-relevant tissues (Blood/Spleen) from both fields -- this
addresses the context-inversion problem the ADC ingestion spec flagged
(§1): "CD4 T cell high expression" is an *off-target* risk signal in the
ADC/oncology context the source database was built for, but is normal,
expected biology on this CD4 platform, so it must not count against a
gene's safety window here. ``load_gtex_safety_overlay`` reads this table as
already-aggregated -- no further aggregation needed. If the file is ever
removed or replaced with a differently-shaped one, this follows the exact
same honest-fallback contract as ``cre_schema.py`` -- an explicit
``available: False`` rather than a fabricated safety score.

Coverage is intentionally partial (~49% of GWT targets) -- a gene absent
from the overlay is genuinely unchecked, not "not druggable"/"not safe";
every lookup function here follows the same ``unknown`` contract as
``readiness_engine.py``'s existing ``_tractability``/``_human_genetic``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from common import degrade
from config import settings

UNKNOWN = "unknown"

MEMBRANE_OVERLAY_PATH_DEFAULT = (
    settings.REPO_ROOT / "docs" / "mvp-research" / "adc_overlay_gwt_overlap_full.csv"
)
GTEX_PER_TISSUE_PATH_DEFAULT = settings.REPO_ROOT / "sources" / "target_tool_cache" / "_overlays" / "gtex_per_tissue.parquet"

GTEX_REQUIRED_COLUMNS = ["ensembl_id", "gene_symbol", "n_tissues_expressed", "max_expression_outside_cd4_context"]

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
        return degrade.unavailable_available(
            f"membrane overlay file not found: {resolved}", data_key="table", empty=empty_membrane_overlay_table()
        )
    df = pd.read_csv(resolved)
    missing = [c for c in MEMBRANE_OVERLAY_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return degrade.unavailable_available(
            f"membrane overlay file missing required columns: {missing}",
            data_key="table",
            empty=empty_membrane_overlay_table(),
        )
    return {"available": True, "reason": None, "table": df}


def _empty_gtex_summary() -> pd.DataFrame:
    return pd.DataFrame(columns=GTEX_REQUIRED_COLUMNS)


def load_gtex_safety_overlay(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the pre-aggregated, off-context-excluding GTEx safety-window overlay.

    Returns ``{"available": bool, "reason": str|None, "table": DataFrame}``.
    Never raises; a missing or malformed file produces an explicit
    ``available: False`` with an empty table -- never a fabricated breadth
    count.
    """
    resolved = Path(path) if path is not None else GTEX_PER_TISSUE_PATH_DEFAULT
    if not resolved.exists():
        return degrade.unavailable_available(
            f"GTEx per-tissue expression file not found: {resolved}", data_key="table", empty=_empty_gtex_summary()
        )
    df = pd.read_parquet(resolved)
    missing = [c for c in GTEX_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return degrade.unavailable_available(
            f"GTEx overlay file missing required columns: {missing}", data_key="table", empty=_empty_gtex_summary()
        )
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
    """Count of off-context GTEx tissues (Blood/Spleen excluded) where this
    gene clears the expression threshold, else ``unknown``. Keyed by Ensembl
    gene ID, same convention as ``tractability_from_membrane_overlay``.

    Higher = more broadly expressed across normal, non-CD4-context tissues =
    plausibly a narrower safety window for systemic inhibition; lower =
    narrower off-context expression = plausibly wider. This module does not
    collapse that into a categorical tier (tight/moderate/wide) -- the raw
    count is returned so the interpretation stays visible and revisable, not
    baked into a lossy label; ``readiness_engine.py`` currently surfaces it
    as-is, not as a red-flag trigger (soft signal, not a cap -- see
    docs/mvp-research/ENHANCEMENT_連結器加強建議.md's guardrail note on this
    exact point for the analogous gnomAD-constraint signal).

    Coverage is ~9,718 genes; a gene absent from the overlay is unchecked,
    not "safe" -- returns ``unknown``, never `0`.
    """
    if not overlay.get("available") or not gene_ensembl:
        return UNKNOWN
    table = overlay["table"]
    row = table[table["ensembl_id"] == gene_ensembl]
    if row.empty:
        return UNKNOWN
    return int(row.iloc[0]["n_tissues_expressed"])
