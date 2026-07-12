"""Integrated multi-axis triage card (follow-up direction F).

Read-only *composition* of the descriptive overlays that the second-round
exploration surfaced -- it reimplements none of them:

  * ``concept_annotation``            -- CD4 immune-concept modules +
    ``stimulation_gated`` (join on ``target`` symbol).
  * ``stimulation_switch_explorer``   -- stimulation-dependent switch class.
  * ``common/overlay_lookup`` (+ ``evidence/safety_overlay`` loaders) -- gnomAD
    LoF-constraint flag, GTEx off-context breadth, and the composed on-target
    safety-**liability** tier (join on the Ensembl ``target_id``).
  * ``robust_ranking`` (direction D)   -- three-state robustness tier.
  * ``genetic_double_support`` (direction E) -- disease x population genetic
    double support.

The exploration found only **six multi-axis winners** among the candidates
(PIK3R1 / PLCG1 / CD3E / CD247 / IL4R / ITK); only CD3E/CD247 carry a proven-
favorable safety window, and LAT -- strong on the immune/gated axes -- is
correctly demoted by the safety axis (LOEUF-constrained AND broadly expressed
off-context = high on-target liability). This module lays every axis out on one
card so that trade-off is visible instead of buried.

DISCIPLINE (enforced, not aspirational -- identical to the modules it composes):
  * ``unknown != 0`` -- the sparse axes (safety is populated on only ~15 genes,
    the gnomAD seed) are ``"unknown"`` for every uncovered gene and when the
    overlays are absent; ``unknown`` safety is NEVER coerced to safe/0 and NEVER
    credited in the score. A gene in no concept module gets ``0`` modules
    honestly; ``stimulation_gated`` stays ``None`` when the per-condition data is
    missing.
  * descriptive-vs-decision separation -- NOTHING here feeds ``readiness_call`` /
    ``overall_readiness_stage`` / ``statistical_evidence_grade`` / ``_stage()``.
    ``build_triage`` returns a fresh frame of additive descriptive columns; an
    ``inert`` regression test (``tests/test_triage_view.py``) runs a frame
    carrying every triage column through ``compute_readiness`` and asserts
    byte-identical output vs the plain frame.
  * sparse axes must not dominate -- the safety axis (~15 genes) contributes to
    the score ONLY when a real signal is present (favorable window ADDS a modest
    bonus, high liability SUBTRACTS); an unknown safety value contributes
    exactly 0, so the 11,500-odd genes with no gnomAD coverage are neither
    rewarded nor punished for the absence of data. Coverage counts are echoed in
    the response ``provenance`` block so a consumer can see how thin the axis is.
  * provenance -- ``concept_set_version``, gnomAD source, and GTEx source are
    stamped on every ``triage_rank`` response.

Join keys: concept/switch/robustness join on ``target`` (gene symbol); safety
joins on the Ensembl ``target_id`` (never the symbol). Both columns live on the
same cards frame; the composite is assembled per ``target``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

import concept_annotation
import genetic_double_support
import robust_ranking
import stimulation_switch_explorer
from common.overlay_lookup import (
    UNKNOWN,
    composite_safety_liability,
    gnomad_flag_from_constraint,
    safety_window_from_gtex,
)
from individual_concept_profile import concept_set_version

_TARGET_COL = "target"
_TARGET_ID_COL = "target_id"
_EFFECT_COL = "ontarget_effect_size"

# Columns required on the cards frame for the composite to be meaningful. The
# per-axis modules each degrade honestly on their own, but without a target /
# target_id key there is nothing to compose.
REQUIRED_COLUMNS = (_TARGET_COL, _TARGET_ID_COL)

# --- Transparent, documented multi-axis weights ----------------------------
# These are DISPLAY/RANKING weights only -- moving them changes what floats to
# the top of a descriptive short-list, never any readiness call. Each attractive
# axis contributes a fixed positive weight; the safety axis is the only one that
# can go negative, and it does so ONLY on a KNOWN-high liability (never on an
# unknown/uncovered gene). ``|effect|`` is deliberately NOT part of the score --
# it is a tiebreaker (see ``triage_rank``) so a single huge-effect but otherwise
# thin target cannot outrank a genuinely multi-axis one.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "concept": 1.0,               # in >=1 CD4 immune concept module
    "stimulation_gated": 1.0,     # quiet at Rest, active on Stim
    "switch": 1.0,                # a stimulation-dependent switch target
    "druggable": 1.0,             # carries a druggable_class
    "robustness_high": 1.5,       # robustness_tier == high_confidence (D)
    "double_support": 1.5,        # disease x population genetic double support (E)
    "safety_favorable": 1.0,      # KNOWN-favorable (low) on-target liability window
    "safety_high_liability": -2.0,  # KNOWN-high on-target liability -> DEMOTE
}


def _dedup_strongest_effect(annotated: pd.DataFrame) -> pd.DataFrame:
    """One row per target: its strongest-|effect| condition (like immune_interest_rank).

    Targets whose effect is entirely NaN are kept (first row) so nothing silently
    vanishes -- their |effect| tiebreaker is simply unknown.
    """
    df = annotated.copy()
    df["_abs_effect"] = pd.to_numeric(df.get(_EFFECT_COL), errors="coerce").abs()
    idx = df.groupby(_TARGET_COL)["_abs_effect"].idxmax().dropna()
    per_target = df.loc[idx].copy()
    seen = set(per_target[_TARGET_COL].astype(str).str.upper())
    missing = set(df[_TARGET_COL].astype(str).str.upper()) - seen
    if missing:
        extra = df[df[_TARGET_COL].astype(str).str.upper().isin(missing)].drop_duplicates(_TARGET_COL)
        per_target = pd.concat([per_target, extra], ignore_index=True)
    return per_target.reset_index(drop=True)


def _druggable_present(value: Any) -> bool:
    """True when a real druggable_class is present (not NaN / none / unknown)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    token = str(value).strip().lower()
    return token not in {"", "nan", "none", UNKNOWN}


def build_triage(
    cards_df: pd.DataFrame,
    gnomad_overlay: Optional[Dict[str, Any]] = None,
    gtex_overlay: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    """Return ONE row per target with every descriptive triage axis laid out.

    Deduplicates the per-target x condition cards to each target's strongest
    ``|ontarget_effect_size|`` condition (same rule as ``immune_interest_rank``),
    then attaches the additive axes:

      * concept: ``concept_modules``, ``n_concept_modules``, ``stimulation_gated``
      * switch: ``switch_type`` (``None`` when the target is not a switch)
      * safety: ``gnomad_constraint_flag``, ``gtex_breadth``,
        ``composite_safety_liability`` -- all ``"unknown"`` when the overlays are
        absent or the gene is uncovered (~15 gnomAD genes only). ``unknown`` is
        NEVER coerced to safe/0.
      * druggability: ``druggable_class``, ``tractability_modality`` (from cards)
      * robustness: ``robustness_tier`` (direction D)
      * double support: ``double_support`` (bool), ``n_diseases`` (direction E;
        ``0`` / ``False`` when a target is absent from the double-support list)

    ``gnomad_overlay`` / ``gtex_overlay`` are already-loaded overlay dicts (from
    ``evidence.safety_overlay.load_*`` / ``api.deps._gnomad_overlay`` etc.); when
    ``None`` the safety axis is uniformly ``"unknown"`` (honest, never 0).

    Purely descriptive: none of these columns is ever a readiness input.
    """
    if _TARGET_COL not in cards_df.columns:
        raise ValueError(f"cards_df must have a {_TARGET_COL!r} column to build a triage view")

    # --- concept axis (join on symbol) ------------------------------------
    annotated = concept_annotation.annotate_targets(cards_df)
    per_target = _dedup_strongest_effect(annotated)

    # --- switch axis (join on symbol) -------------------------------------
    switches = stimulation_switch_explorer.list_switches(cards_df)
    switch_by_target = (
        switches.set_index(_TARGET_COL)["switch_type"].to_dict() if not switches.empty else {}
    )
    per_target["switch_type"] = per_target[_TARGET_COL].map(lambda t: switch_by_target.get(str(t)))

    # --- robustness axis (D) ----------------------------------------------
    # A target's tier = its BEST tier across conditions (high_confidence if ANY
    # condition qualifies), computed on the full frame then reduced per target.
    tier_full = robust_ranking.robustness_tier(cards_df)
    tier_frame = pd.DataFrame(
        {_TARGET_COL: cards_df[_TARGET_COL].astype(str), "_tier": tier_full.to_numpy()}
    )
    _TIER_ORDER = {
        robust_ranking.TIER_HIGH: 2,
        robust_ranking.TIER_UNRESOLVED: 1,
        robust_ranking.TIER_LOW: 0,
    }
    tier_frame["_rank"] = tier_frame["_tier"].map(_TIER_ORDER).fillna(0)
    best_idx = tier_frame.groupby(_TARGET_COL)["_rank"].idxmax()
    tier_by_target = tier_frame.loc[best_idx].set_index(_TARGET_COL)["_tier"].to_dict()
    per_target["robustness_tier"] = per_target[_TARGET_COL].map(
        lambda t: tier_by_target.get(str(t), robust_ranking.TIER_UNRESOLVED)
    )

    # --- double-support axis (E, join on symbol) --------------------------
    ds = genetic_double_support.double_support(cards_df)
    ds_by_target: Dict[str, int] = {}
    if ds.get("available"):
        for rec in ds.get("targets", []):
            ds_by_target[str(rec["target"]).strip().upper()] = int(rec.get("n_diseases", 0))
    upper = per_target[_TARGET_COL].astype(str).str.strip().str.upper()
    per_target["double_support"] = upper.map(lambda s: s in ds_by_target)
    per_target["n_diseases"] = upper.map(lambda s: ds_by_target.get(s, 0))

    # --- safety axis (join on Ensembl target_id) --------------------------
    gnomad_flags: List[Any] = []
    gtex_breadths: List[Any] = []
    composites: List[Any] = []
    if _TARGET_ID_COL in per_target.columns:
        for eid in per_target[_TARGET_ID_COL]:
            ensembl = str(eid) if pd.notna(eid) else ""
            gf = gnomad_flag_from_constraint(ensembl, gnomad_overlay) if gnomad_overlay else UNKNOWN
            sw = safety_window_from_gtex(ensembl, gtex_overlay) if gtex_overlay else UNKNOWN
            gnomad_flags.append(gf)
            gtex_breadths.append(sw)
            composites.append(composite_safety_liability(gf, sw))
    else:
        gnomad_flags = [UNKNOWN] * len(per_target)
        gtex_breadths = [UNKNOWN] * len(per_target)
        composites = [UNKNOWN] * len(per_target)
    per_target["gnomad_constraint_flag"] = gnomad_flags
    per_target["gtex_breadth"] = gtex_breadths
    per_target["composite_safety_liability"] = composites

    # --- druggability axis (already on cards) -----------------------------
    if "druggable_class" not in per_target.columns:
        per_target["druggable_class"] = np.nan
    if "tractability_modality" not in per_target.columns:
        per_target["tractability_modality"] = np.nan

    return per_target


def _axis_hits(row: pd.Series) -> Dict[str, bool]:
    """Which axes a target is POSITIVELY attractive on (for ``n_axes`` / scoring).

    Safety counts as an attractive axis ONLY when a favorable (low) liability
    window is proven; a KNOWN-high liability is a negative (handled in the score,
    not counted here); an ``unknown`` safety value is neither.
    """
    concept = int(row.get("n_concept_modules") or 0) > 0
    gated = row.get("stimulation_gated") is True or row.get("stimulation_gated") == True  # noqa: E712
    switch = row.get("switch_type") not in (None, np.nan) and not (
        isinstance(row.get("switch_type"), float) and pd.isna(row.get("switch_type"))
    )
    druggable = _druggable_present(row.get("druggable_class"))
    robust_high = row.get("robustness_tier") == robust_ranking.TIER_HIGH
    double = bool(row.get("double_support"))
    safety_favorable = row.get("composite_safety_liability") == "low"
    return {
        "concept": bool(concept),
        "stimulation_gated": bool(gated),
        "switch": bool(switch),
        "druggable": bool(druggable),
        "robustness_high": bool(robust_high),
        "double_support": bool(double),
        "safety_favorable": bool(safety_favorable),
    }


def _score_row(row: pd.Series, weights: Dict[str, float]) -> Dict[str, Any]:
    hits = _axis_hits(row)
    total = 0.0
    for axis, present in hits.items():
        if present:
            total += weights.get(axis, 0.0)
    # Safety liability is the only demoting axis: a KNOWN-high on-target
    # liability subtracts; unknown safety contributes exactly 0 (never credited,
    # never punished) so the partially-covered composite axis (gnomAD is now
    # whole-genome but GTEx breadth is still ~5k genes) cannot dominate the ranking.
    if row.get("composite_safety_liability") == "high":
        total += weights.get("safety_high_liability", 0.0)
    n_axes = int(sum(hits.values()))
    return {"total_score": float(total), "n_axes": n_axes, "axis_hits": hits}


def triage_rank(
    cards_df: pd.DataFrame,
    gnomad_overlay: Optional[Dict[str, Any]] = None,
    gtex_overlay: Optional[Dict[str, Any]] = None,
    top_n: int = 100,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Transparent multi-axis triage short-list.

    Builds the composite (``build_triage``), scores each target with the
    documented ``DEFAULT_WEIGHTS`` (override via ``weights``), and sorts by
    ``(total_score, n_axes, |effect|)`` descending. ``n_axes`` = number of axes a
    target is positively attractive on (concept>0, gated, any switch, druggable,
    robustness high_confidence, double_support, KNOWN-favorable safety). Safety
    ADDS only on a proven favorable window; a KNOWN-high liability SUBTRACTS;
    ``unknown`` safety scores 0 (never credited).

    Returns::

        {available, n_total, returned, weights, provenance:{concept_set_version,
         gnomad_source, gtex_source, safety_coverage}, targets}

    Honest-fallback: ``available: False`` (with a ``reason``) when a required
    cards column (``target`` / ``target_id``) is absent.
    """
    resolved_weights = dict(DEFAULT_WEIGHTS if weights is None else weights)
    missing = [c for c in REQUIRED_COLUMNS if c not in cards_df.columns]
    if missing:
        return {
            "available": False,
            "reason": f"cards missing required columns: {missing}",
            "n_total": int(cards_df[_TARGET_COL].nunique()) if _TARGET_COL in cards_df.columns else 0,
            "returned": 0,
            "weights": resolved_weights,
            "provenance": _provenance_block(gnomad_overlay, gtex_overlay, None),
            "targets": [],
        }

    triage = build_triage(cards_df, gnomad_overlay=gnomad_overlay, gtex_overlay=gtex_overlay)

    scores = triage.apply(lambda r: _score_row(r, resolved_weights), axis=1)
    triage = triage.copy()
    triage["total_score"] = [s["total_score"] for s in scores]
    triage["n_axes"] = [s["n_axes"] for s in scores]
    triage["axis_hits"] = [s["axis_hits"] for s in scores]
    triage["_abs_effect"] = pd.to_numeric(triage.get(_EFFECT_COL), errors="coerce").abs()

    triage = triage.sort_values(
        by=["total_score", "n_axes", "_abs_effect"],
        ascending=[False, False, False],
        kind="mergesort",  # stable, deterministic
        na_position="last",
    )

    n_total = int(triage[_TARGET_COL].nunique())
    shown = triage.head(top_n) if top_n and top_n > 0 else triage
    shown = shown.drop(columns=["_abs_effect"])

    return {
        "available": True,
        "reason": None,
        "n_total": n_total,
        "returned": int(len(shown)),
        "weights": resolved_weights,
        "provenance": _provenance_block(gnomad_overlay, gtex_overlay, triage),
        "targets": _json_records(shown),
    }


def _provenance_block(
    gnomad_overlay: Optional[Dict[str, Any]],
    gtex_overlay: Optional[Dict[str, Any]],
    triage: Optional[pd.DataFrame],
) -> Dict[str, Any]:
    """Per-axis provenance + sparse-axis coverage disclosure (unknown != 0)."""

    def _source(overlay: Optional[Dict[str, Any]]) -> str:
        if not overlay:
            return "not loaded"
        if not overlay.get("available"):
            return f"unavailable ({overlay.get('reason')})"
        return "loaded"

    coverage: Dict[str, Any] = {}
    if triage is not None and "composite_safety_liability" in triage.columns:
        n_targets = int(len(triage))
        n_safety_known = int((triage["composite_safety_liability"] != UNKNOWN).sum())
        coverage = {
            "n_targets": n_targets,
            "safety_covered": n_safety_known,
            "safety_unknown": n_targets - n_safety_known,
            "note": (
                "composite safety needs BOTH gnomAD constraint (now whole-genome, "
                "~19k genes) AND GTEx breadth (~5k-gene partial overlay), so GTEx is "
                "the limiting axis; uncovered genes are 'unknown', never coerced to "
                "safe/0, and never scored."
            ),
        }
    return {
        "concept_set_version": concept_set_version(),
        "gnomad_source": _source(gnomad_overlay),
        "gtex_source": _source(gtex_overlay),
        "safety_coverage": coverage,
        "descriptive_only": True,
    }


def _json_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """NaN/inf -> null JSON-compliant records (mirrors ``api.deps._json_records``)."""
    import json

    return json.loads(df.where(pd.notna(df), None).to_json(orient="records"))
