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

The safety-window half is now also real: ``gtex_per_tissue.parquet``
(public GTEx-derived, 9,727 genes x 30 tissues, median TPM per
gene-tissue pair) has been placed at
``sources/target_tool_cache/_overlays/gtex_per_tissue.parquet``.
``load_gtex_safety_overlay`` aggregates it to one row per gene
(``n_tissues_expressed`` = count of the 30 tissues where median TPM clears
``GTEX_EXPRESSED_TPM_THRESHOLD``), keyed by **gene symbol** (this file has no
Ensembl ID column, unlike the membrane overlay). If the file is ever removed
or replaced with a differently-shaped one, this follows the exact same
honest-fallback contract as ``cre_schema.py`` -- an explicit
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

from config import settings

UNKNOWN = "unknown"

MEMBRANE_OVERLAY_PATH_DEFAULT = (
    settings.REPO_ROOT / "docs" / "mvp-research" / "adc_overlay_gwt_overlap_full.csv"
)
GTEX_PER_TISSUE_PATH_DEFAULT = settings.REPO_ROOT / "sources" / "target_tool_cache" / "_overlays" / "gtex_per_tissue.parquet"

GTEX_REQUIRED_COLUMNS = ["gene_symbol", "tissue", "median_tpm"]
# Standard minimal-detectable-expression cutoff (TPM > 1 is the common GTEx
# convention for "expressed"). A tuning value, not a hard biological fact --
# revisit if the breadth counts prove too permissive/strict in practice.
GTEX_EXPRESSED_TPM_THRESHOLD = 1.0

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


def _empty_gtex_summary() -> pd.DataFrame:
    return pd.DataFrame(columns=["gene_symbol", "n_tissues_total", "n_tissues_expressed", "max_median_tpm"])


def load_gtex_safety_overlay(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load and aggregate GTEx per-tissue expression to one row per gene.

    Returns ``{"available": bool, "reason": str|None, "table": DataFrame}``
    with columns ``gene_symbol``/``n_tissues_total``/``n_tissues_expressed``/
    ``max_median_tpm``. Never raises; a missing or malformed file produces an
    explicit ``available: False`` with an empty table -- never a fabricated
    breadth count.
    """
    resolved = Path(path) if path is not None else GTEX_PER_TISSUE_PATH_DEFAULT
    if not resolved.exists():
        return {
            "available": False,
            "reason": f"GTEx per-tissue expression file not found: {resolved}",
            "table": _empty_gtex_summary(),
        }
    df = pd.read_parquet(resolved)
    missing = [c for c in GTEX_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return {
            "available": False,
            "reason": f"GTEx overlay file missing required columns: {missing}",
            "table": _empty_gtex_summary(),
        }
    summary = (
        df.assign(expressed=df["median_tpm"] > GTEX_EXPRESSED_TPM_THRESHOLD)
        .groupby("gene_symbol")
        .agg(
            n_tissues_total=("tissue", "nunique"),
            n_tissues_expressed=("expressed", "sum"),
            max_median_tpm=("median_tpm", "max"),
        )
        .reset_index()
    )
    return {"available": True, "reason": None, "table": summary}


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


def safety_window_from_gtex(gene_symbol: str, overlay: Dict[str, Any]) -> Any:
    """Count of (up to 30) GTEx tissues where this gene clears the expression
    threshold, else ``unknown``. Keyed by gene SYMBOL (this overlay has no
    Ensembl ID column) -- unlike ``tractability_from_membrane_overlay``.

    Higher = more broadly expressed across normal tissues = plausibly a
    narrower safety window for systemic inhibition (more tissues at risk of
    on-target-in-the-wrong-place effects); lower = narrower normal-tissue
    expression = plausibly wider. This module does not yet collapse that into
    a categorical tier (tight/moderate/wide) -- the raw count is returned so
    the interpretation stays visible and revisable, not baked into a lossy
    label; ``readiness_engine.py`` currently surfaces it as-is, not as a
    red-flag trigger (soft signal, not a cap -- see
    docs/mvp-research/ENHANCEMENT_連結器加強建議.md's guardrail note on this
    exact point for the analogous gnomAD-constraint signal).

    Coverage is ~9,727 genes (GTEx-tissue-panel-derived); a gene absent from
    the overlay is unchecked, not "safe" -- returns ``unknown``, never `0`.
    """
    if not overlay.get("available") or not gene_symbol:
        return UNKNOWN
    table = overlay["table"]
    row = table[table["gene_symbol"] == str(gene_symbol).upper()]
    if row.empty:
        return UNKNOWN
    return int(row.iloc[0]["n_tissues_expressed"])
