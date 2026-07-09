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

A third, independent safety signal (§C of ``docs/next_phases_plan.md``,
"gnomAD LOEUF/pLI 安全性補強") is gnomAD's loss-of-function constraint:
LOEUF (a low value = strongly LoF-intolerant) and pLI are complementary to
the GTEx expression-breadth signal above -- GTEx says *where* a gene is
expressed outside CD4 context, gnomAD says *how tolerant the human
population is* to losing a copy of it. Low LOEUF is a soft risk flag for a
narrower pharmacological safety window under systemic inhibition; it is
NOT the same claim as pharmacological (small-molecule/antibody) LoF
intolerance, so (exactly like ``safety_window_from_gtex``) this stays a
descriptive annotation and never caps ``readiness_call``/
``overall_readiness_stage``. The loss-intolerant flag fires when LOEUF is
below ``LOEUF_LOSS_INTOLERANT_THRESHOLD`` -- now 0.6, gnomAD **v4**'s
"constrained" cutoff (broadened from the v2.1.1-era 0.35 once the seed was
refreshed to real v4 LOEUF/pLI values; see ``common/overlay_lookup.py``).

``load_gnomad_constraint_overlay`` reads
``sources/target_tool_cache/_overlays/gnomad_constraint_seed.csv``
(columns ``ensembl_id``, ``gene_symbol``, ``loeuf``, ``pli``), with each
gene symbol resolved to its real Ensembl gene ID via
``gene_identifier_resolver.load_resolver()`` (no invented IDs). The seed now
carries **real gnomAD v4 constraint values for the 15 shortlist genes**
(a networked run supplied them, unblocking the earlier 8-gene demo seed --
the original sandbox had no egress to gnomAD, policy-blocked like Open
Targets). A full-genome gnomAD snapshot can widen coverage further by
dropping a larger file at the same path; the loader's honest-fallback
contract (below) is what makes that swap safe: a missing/malformed file
degrades to ``available: False``, never a fabricated LOEUF/pLI value.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from common import degrade
from common.overlay_lookup import (
    BREADTH_BROAD_THRESHOLD,
    LOEUF_LOSS_INTOLERANT_THRESHOLD,
    MODALITY_ANTIBODY_BIOLOGIC,
    MODALITY_ANTIBODY_SURFACE,
    MODALITY_SMALL_MOLECULE,
    UNKNOWN,
    composite_safety_liability,
    gnomad_flag_from_constraint,
    safety_window_from_gtex,
    tractability_from_membrane_overlay,
)
from config import settings

MEMBRANE_OVERLAY_PATH_DEFAULT = (
    settings.REPO_ROOT / "docs" / "mvp-research" / "adc_overlay_gwt_overlap_full.csv"
)
GTEX_PER_TISSUE_PATH_DEFAULT = settings.REPO_ROOT / "sources" / "target_tool_cache" / "_overlays" / "gtex_per_tissue.parquet"
GNOMAD_CONSTRAINT_SEED_PATH_DEFAULT = (
    settings.REPO_ROOT / "sources" / "target_tool_cache" / "_overlays" / "gnomad_constraint_seed.csv"
)

GTEX_REQUIRED_COLUMNS = ["ensembl_id", "gene_symbol", "n_tissues_expressed", "max_expression_outside_cd4_context"]
GNOMAD_REQUIRED_COLUMNS = ["ensembl_id", "gene_symbol", "loeuf", "pli"]

MEMBRANE_OVERLAY_REQUIRED_COLUMNS = [
    "gene_symbol",
    "ensembl_id",
    "is_surface_protein",
    "has_transmembrane_domain",
    "has_extracellular_domain",
    "is_druggable",
    "druggable_pathway",
]

# LOEUF_LOSS_INTOLERANT_THRESHOLD, MODALITY_ANTIBODY_SURFACE,
# MODALITY_ANTIBODY_BIOLOGIC, MODALITY_SMALL_MOLECULE are imported above from
# common.overlay_lookup (architecture refactor Phase 3 -- the pure
# interpretation half of this module moved there so core/readiness.py can
# use it without importing evidence/; see that module's docstring).


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


def _empty_gnomad_summary() -> pd.DataFrame:
    return pd.DataFrame(columns=GNOMAD_REQUIRED_COLUMNS)


def load_gnomad_constraint_overlay(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the gnomAD LOEUF/pLI constraint overlay (join key: Ensembl gene ID).

    Returns ``{"available": bool, "reason": str|None, "table": DataFrame}``.
    Never raises; a missing or malformed file produces an explicit
    ``available: False`` with an empty table -- never a fabricated
    constraint value.

    Defaults to the 8-gene seed file derived from
    ``docs/mvp-research/connector_enrichment_demo.csv`` (see module
    docstring); a full-genome gnomAD snapshot can be dropped in at the same
    path later with no code change required.
    """
    resolved = Path(path) if path is not None else GNOMAD_CONSTRAINT_SEED_PATH_DEFAULT
    if not resolved.exists():
        return {
            "available": False,
            "reason": f"gnomAD constraint overlay file not found: {resolved}",
            "table": _empty_gnomad_summary(),
        }
    df = pd.read_csv(resolved)
    missing = [c for c in GNOMAD_REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return {
            "available": False,
            "reason": f"gnomAD constraint overlay file missing required columns: {missing}",
            "table": _empty_gnomad_summary(),
        }
    return {"available": True, "reason": None, "table": df}


# tractability_from_membrane_overlay, safety_window_from_gtex,
# gnomad_flag_from_constraint, and composite_safety_liability (the pure
# overlay-interpretation functions) are imported above from
# common.overlay_lookup and re-exported under their original names here -- see
# this module's docstring and common/overlay_lookup.py's docstring
# (architecture refactor Phase 3). composite_safety_liability (roadmap P1.3)
# composes gnomAD constraint + GTEx breadth into one disclosed on-target
# safety-LIABILITY tier -- never a de-risking signal.
