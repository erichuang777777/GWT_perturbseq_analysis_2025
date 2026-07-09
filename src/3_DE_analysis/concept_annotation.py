"""Descriptive immune-concept annotation + immune-interest ranking of target cards.

Motivation (exploration follow-up A). The default target-card ordering is by
differential-expression breadth (``n_total_de_genes``), which surfaces
pleiotropic chromatin / housekeeping / metabolic knockdowns (NSD1, SETDB1,
UFM1, PKM, ...) at the top and buries the immunologically meaningful hits
(PLCG1, CD247, ITK, CD28, MALT1, STAT3, GATA3, CBLB) that a CD4 T-cell target
hunter actually wants to see first. The cross-condition exploration also showed
the strongest biological signal in the whole screen -- the TCR-proximal
signalosome -- is stimulation-gated and therefore invisible in a breadth sort.

This module adds a **purely descriptive** overlay: it tags each target with the
CD4 immune concept module(s) whose seed set contains that gene (reusing the 20
COMPASS-analog modules from ``individual_concept_profile.load_concept_modules``)
and offers an immune-interest ranking. It is read-time annotation of
already-built cards.

DISCIPLINE (enforced, not aspirational):
  * ``unknown`` != ``0``: a gene in no module gets ``concept_modules == []``
    (empty, honest), never an error; ``stimulation_gated`` is ``None`` (unknown)
    when the underlying per-condition data is missing, never ``False``.
  * Descriptive vs decision separation: NOTHING here feeds ``readiness_call`` /
    ``overall_readiness_stage`` / ``statistical_evidence_grade`` / ``_stage()``.
    The concept columns are additive metadata; ``annotate_targets`` never
    mutates an existing column. ``tests/test_concept_annotation.py`` locks this
    by running an annotated frame through ``compute_readiness`` and asserting
    byte-identical output vs the un-annotated frame.
  * Provenance: a ``concept_set_version`` fingerprint stamps every annotated
    frame so a consumer can tell which seed-module revision produced the tags.

Join key: the concept seed genes are HGNC **symbols** (upper-cased). The cards
carry both ``target`` (symbol, e.g. ``PLCG1``) and ``target_id`` (Ensembl, e.g.
``ENSG...``). The concept join is therefore on ``target`` (upper-cased),
**never** ``target_id`` -- joining on the Ensembl column would silently tag
every gene as belonging to no module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from individual_concept_profile import concept_set_version, load_concept_modules

# --- stimulation-gated thresholds (pinned + documented; descriptive only) ------
# A target is "stimulation-gated" when its knockdown is near-silent in the
# resting state and strong under stimulation -- the TCR-proximal signalosome
# pattern from the cross-condition exploration (CD3E/LAT/ZAP70/PLCG1 go from ~0
# DE genes at Rest to thousands at Stim8hr). These cutoffs are deliberately
# conservative and are NOT a decision input -- they only annotate a row for
# display/filtering. Changing them changes what gets *labelled*, never any
# readiness call.
STIM_GATED_REST_QUIET_MAX_DE = 50    # Rest n_total_de_genes <= this  => "quiet at rest"
STIM_GATED_STIM_ACTIVE_MIN_DE = 500  # max Stim n_total_de_genes >= this => "active on stim"
REST_CONDITION = "Rest"
STIM_CONDITIONS = ("Stim8hr", "Stim48hr")

_TARGET_COL = "target"
_EFFECT_COL = "ontarget_effect_size"
_DE_COL = "n_total_de_genes"
_CONDITION_COL = "condition"


def build_gene_to_modules(modules: Optional[List[Dict[str, Any]]] = None) -> Dict[str, List[Dict[str, str]]]:
    """Invert the module list into ``SYMBOL -> [{module_id, module_name, category}]``.

    ``load_concept_modules`` returns a *list* of module dicts (each with a
    ``seed_genes`` list of upper-cased symbols); we iterate it to build the
    reverse index a per-gene annotation needs. A gene may map to several modules
    (e.g. LAG3 -> Checkpoint + Exhaustion), so values are lists.
    """
    if modules is None:
        modules = load_concept_modules()
    index: Dict[str, List[Dict[str, str]]] = {}
    for module in modules:
        meta = {
            "module_id": module.get("module_id", ""),
            "module_name": module.get("module_name", ""),
            "category": module.get("category", ""),
        }
        for gene in module.get("seed_genes", []):
            index.setdefault(gene.upper(), []).append(meta)
    return index


def stimulation_gated_by_target(cards_df: pd.DataFrame) -> Dict[str, Optional[bool]]:
    """Per-target ``stimulation_gated`` flag (quiet at Rest, active on Stim).

    Returns ``target -> bool|None``. ``None`` (unknown) whenever the Rest row or
    both Stim rows are missing / non-numeric -- honoring ``unknown != 0`` rather
    than defaulting a genuinely-unmeasured target to ``False``.
    """
    result: Dict[str, Optional[bool]] = {}
    if not {_TARGET_COL, _CONDITION_COL, _DE_COL}.issubset(cards_df.columns):
        return result
    de = pd.to_numeric(cards_df[_DE_COL], errors="coerce")
    frame = pd.DataFrame(
        {
            _TARGET_COL: cards_df[_TARGET_COL].astype(str).str.upper(),
            _CONDITION_COL: cards_df[_CONDITION_COL].astype(str),
            "_de": de,
        }
    )
    for target, grp in frame.groupby(_TARGET_COL):
        by_cond = grp.set_index(_CONDITION_COL)["_de"]
        rest = by_cond.get(REST_CONDITION, np.nan)
        stim_vals = [by_cond.get(c, np.nan) for c in STIM_CONDITIONS]
        stim_present = [v for v in stim_vals if pd.notna(v)]
        if pd.isna(rest) or not stim_present:
            result[target] = None  # unknown, not False
            continue
        result[target] = bool(rest <= STIM_GATED_REST_QUIET_MAX_DE and max(stim_present) >= STIM_GATED_STIM_ACTIVE_MIN_DE)
    return result


def annotate_targets(
    cards_df: pd.DataFrame,
    modules: Optional[List[Dict[str, Any]]] = None,
    seed_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Return a COPY of ``cards_df`` with additive concept-annotation columns.

    Adds (never overwrites): ``concept_modules`` (list of
    ``{module_id, module_name, category}`` dicts; ``[]`` if the gene is in no
    module), ``n_concept_modules`` (int), ``stimulation_gated`` (bool|None), and
    ``concept_set_version`` (provenance fingerprint, constant per frame).

    Join is on ``target`` (symbol), upper-cased -- never ``target_id``.
    """
    if _TARGET_COL not in cards_df.columns:
        raise ValueError(f"cards_df must have a {_TARGET_COL!r} (gene-symbol) column to annotate concepts")
    if modules is None:
        modules = load_concept_modules(seed_path)
    gene_to_modules = build_gene_to_modules(modules)
    gated = stimulation_gated_by_target(cards_df)

    out = cards_df.copy()
    symbols = out[_TARGET_COL].astype(str).str.upper()
    out["concept_modules"] = [list(gene_to_modules.get(sym, [])) for sym in symbols]
    out["n_concept_modules"] = out["concept_modules"].map(len)
    out["stimulation_gated"] = [gated.get(sym) for sym in symbols]
    out["concept_set_version"] = concept_set_version(seed_path)
    return out


def immune_interest_rank(
    cards_df: pd.DataFrame,
    calls: Optional[List[str]] = None,
    seed_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Rank targets by immune interest: concept-module membership, then effect.

    Deduplicates to one row per target (cards are per target x condition, ~3
    rows/target) by keeping each target's strongest-|effect| row, then sorts by
    ``(n_concept_modules desc, |ontarget_effect_size| desc)``. Optionally filters
    to a set of ``readiness_call`` values first (when that column is present);
    the pre-built reference cards do not carry it, so ``calls`` is ignored unless
    the column exists.

    Purely a re-ordering + de-dup VIEW -- it changes no value and no call.
    """
    annotated = annotate_targets(cards_df, seed_path=seed_path)
    if calls and "readiness_call" in annotated.columns:
        annotated = annotated[annotated["readiness_call"].isin(calls)]

    annotated = annotated.copy()
    annotated["_abs_effect"] = pd.to_numeric(annotated.get(_EFFECT_COL), errors="coerce").abs()
    # one row per target: its strongest-effect condition
    idx = annotated.groupby(_TARGET_COL)["_abs_effect"].idxmax()
    idx = idx.dropna()
    per_target = annotated.loc[idx].copy()
    # targets whose effect is entirely NaN are dropped by idxmax; re-append them
    # (unknown effect, still show their concept membership) so nothing vanishes.
    missing = set(annotated[_TARGET_COL].astype(str).str.upper()) - set(per_target[_TARGET_COL].astype(str).str.upper())
    if missing:
        extra = annotated[annotated[_TARGET_COL].astype(str).str.upper().isin(missing)].drop_duplicates(_TARGET_COL)
        per_target = pd.concat([per_target, extra], ignore_index=True)

    per_target = per_target.sort_values(
        by=["n_concept_modules", "_abs_effect"],
        ascending=[False, False],
        kind="mergesort",  # stable, deterministic
        na_position="last",
    ).drop(columns=["_abs_effect"])
    return per_target.reset_index(drop=True)


def annotation_provenance(seed_path: Optional[Path] = None) -> Dict[str, Any]:
    """Small provenance block for API responses / reports."""
    modules = load_concept_modules(seed_path)
    return {
        "concept_set_version": concept_set_version(seed_path),
        "n_modules": len(modules),
        "n_seed_genes": len({g for m in modules for g in m.get("seed_genes", [])}),
        "join_key": "target (gene symbol, upper-cased)",
        "descriptive_only": True,
    }
