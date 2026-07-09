"""Stimulation-dependent switch explorer (exploration follow-up C).

The cross-condition exploration surfaced a small, high-value class of targets
whose knockdown phenotype *changes direction* with T-cell activation state: the
sign of ``median_logFC`` reverses across Rest / Stim8hr / Stim48hr (IKZF1,
NFATC2, RHOH, SMAD3, IL21, ...). These "stimulation-dependent switches" are the
most interesting context-dependent candidates in the screen, but nothing in the
toolkit surfaced them -- the ``effect_direction_flip_flag`` column already
exists on every card yet no endpoint or view reads it.

This module makes that latent signal visible. It is READ-ONLY and PURELY
DESCRIPTIVE: it reshapes already-built cards to expose per-condition signed
effects, classifies each flagged target, and tags concept membership (reusing
``concept_annotation``). It touches no readiness call -- ``effect_direction_flip_flag``
was never a readiness input and remains one only for display here.

Classification (thresholds pinned + documented; descriptive only):
  * ``true_sign_flip`` -- at least two conditions carry a *strong* effect
    (``|median_logFC| >= SIGN_FLIP_MIN_ABS_LOGFC``) with opposite sign: a
    genuine directional reversal. This is a re-derivable definition; on the
    reference cards it yields ~28 targets (the cross-condition exploration
    reported ~27 under a near-identical rule -- treat the exact count as a soft
    sanity range, not a golden number).
  * ``on_off_switch`` -- flagged by ``effect_direction_flip_flag`` but not a true
    sign flip: a presence/absence switch (strong in one condition, ~0 in
    another) rather than a directional reversal.

``unknown != 0``: a target missing the Rest row or all Stim rows, or with
non-numeric ``median_logFC``, is simply not classified (absent from the output),
never coerced to a fabricated 0/False.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from concept_annotation import build_gene_to_modules
from individual_concept_profile import concept_set_version

# A "strong" effect for the sign-flip test: below this |logFC| a sign is treated
# as noise, not a real directional call. 1.0 (a one-log2FC effect) is the same
# bar the cross-condition exploration used.
SIGN_FLIP_MIN_ABS_LOGFC = 1.0

_TARGET_COL = "target"
_CONDITION_COL = "condition"
_LOGFC_COL = "median_logFC"
_FLAG_COL = "effect_direction_flip_flag"
_ORDERED_CONDITIONS = ["Rest", "Stim8hr", "Stim48hr"]

REQUIRED_COLUMNS = {_TARGET_COL, _CONDITION_COL, _LOGFC_COL, _FLAG_COL}


def _is_true_sign_flip(values: List[float], thr: float = SIGN_FLIP_MIN_ABS_LOGFC) -> bool:
    strong_signs = {int(np.sign(v)) for v in values if pd.notna(v) and abs(v) >= thr and v != 0}
    return len(strong_signs) > 1


def list_switches(cards_df: pd.DataFrame, seed_path: Optional[Path] = None) -> pd.DataFrame:
    """Return one row per stimulation-switch target, ranked by switch magnitude.

    Columns: ``target``, ``switch_type`` (true_sign_flip | on_off_switch),
    ``logFC_Rest`` / ``logFC_Stim8hr`` / ``logFC_Stim48hr`` (signed, NaN if
    absent), ``switch_magnitude`` (span = max-min signed logFC across present
    conditions), ``n_concept_modules``, ``concept_modules`` (list of module_id).

    Empty frame (with the right columns) if the required columns are absent --
    honest-fallback, not a crash.
    """
    out_cols = [
        _TARGET_COL,
        "switch_type",
        "logFC_Rest",
        "logFC_Stim8hr",
        "logFC_Stim48hr",
        "switch_magnitude",
        "n_concept_modules",
        "concept_modules",
    ]
    if not REQUIRED_COLUMNS.issubset(cards_df.columns):
        return pd.DataFrame(columns=out_cols)

    df = cards_df.copy()
    df[_TARGET_COL] = df[_TARGET_COL].astype(str)
    df["_logfc"] = pd.to_numeric(df[_LOGFC_COL], errors="coerce")
    df["_flag"] = df[_FLAG_COL].fillna(False).astype(bool)

    logfc_by_cond = df.pivot_table(index=_TARGET_COL, columns=_CONDITION_COL, values="_logfc", aggfunc="first", dropna=False)
    flagged_by_target = df.groupby(_TARGET_COL)["_flag"].any()
    gene_to_modules = build_gene_to_modules()

    records: List[Dict[str, Any]] = []
    for target, row in logfc_by_cond.iterrows():
        present = {c: row.get(c, np.nan) for c in _ORDERED_CONDITIONS}
        vals = [v for v in present.values() if pd.notna(v)]
        rest = present.get("Rest", np.nan)
        stim_present = [present.get(c, np.nan) for c in ("Stim8hr", "Stim48hr")]
        stim_present = [v for v in stim_present if pd.notna(v)]
        # need Rest + at least one Stim to talk about a stimulation switch
        if pd.isna(rest) or not stim_present or len(vals) < 2:
            continue

        true_flip = _is_true_sign_flip(vals)
        flagged = bool(flagged_by_target.get(target, False))
        if true_flip:
            switch_type = "true_sign_flip"
        elif flagged:
            switch_type = "on_off_switch"
        else:
            continue  # not a switch

        modules = gene_to_modules.get(target.upper(), [])
        records.append(
            {
                _TARGET_COL: target,
                "switch_type": switch_type,
                "logFC_Rest": float(present["Rest"]) if pd.notna(present["Rest"]) else np.nan,
                "logFC_Stim8hr": float(present["Stim8hr"]) if pd.notna(present["Stim8hr"]) else np.nan,
                "logFC_Stim48hr": float(present["Stim48hr"]) if pd.notna(present["Stim48hr"]) else np.nan,
                "switch_magnitude": float(max(vals) - min(vals)),
                "n_concept_modules": len(modules),
                "concept_modules": [m["module_id"] for m in modules],
            }
        )

    result = pd.DataFrame(records, columns=out_cols)
    if result.empty:
        return result
    # true sign flips first, then by magnitude -- deterministic, stable
    result["_type_rank"] = (result["switch_type"] == "true_sign_flip").astype(int)
    result = result.sort_values(by=["_type_rank", "switch_magnitude"], ascending=[False, False], kind="mergesort")
    return result.drop(columns=["_type_rank"]).reset_index(drop=True)


def switch_report(cards_df: pd.DataFrame, top_n: Optional[int] = None, seed_path: Optional[Path] = None) -> Dict[str, Any]:
    """API-friendly wrapper: honest ``available`` flag, counts, provenance, rows."""
    if not REQUIRED_COLUMNS.issubset(cards_df.columns):
        missing = sorted(REQUIRED_COLUMNS - set(cards_df.columns))
        return {
            "available": False,
            "reason": f"cards missing required columns: {missing}",
            "concept_set_version": concept_set_version(seed_path),
            "switches": [],
        }
    switches = list_switches(cards_df, seed_path=seed_path)
    counts = switches["switch_type"].value_counts().to_dict() if not switches.empty else {}
    shown = switches.head(top_n) if top_n else switches
    return {
        "available": True,
        "sign_flip_threshold_abs_logfc": SIGN_FLIP_MIN_ABS_LOGFC,
        "concept_set_version": concept_set_version(seed_path),
        "n_true_sign_flip": int(counts.get("true_sign_flip", 0)),
        "n_on_off_switch": int(counts.get("on_off_switch", 0)),
        "n_switches": int(len(switches)),
        "returned": int(len(shown)),
        "switches": shown.to_dict(orient="records"),
    }
