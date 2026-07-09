"""Robustness-first ranking of target cards (filter-then-rank, follow-up D).

Motivation (calibration-agent finding). Ranking targets by raw
differential-expression breadth (``n_total_de_genes``) recovers the biology
(positive controls enter the top decile, negatives are suppressed, drug axes
enrich 2-3.5x) but the resulting short-list is **not robust**: under strict
replicate / batch / donor filtering the top-N churns 74-85%, and high-raw-DE
rows are disproportionately the unstable ones. Only 1,102 of 33,983 rows
(~3%) pass ``replicate_pass_flag``. The fix the calibration surfaced is
**filter-then-rank**, not rank-on-raw-DE (post-filter Spearman is 0.943, so the
ordering itself is fine once the unstable rows are removed first).

This module adds a **purely descriptive, read-only** overlay: a three-state
robustness tier per row and a filter-then-rank short-list. It never mutates a
card, never scores anything, and NOTHING here feeds ``readiness_call`` /
``overall_readiness_stage`` / ``statistical_evidence_grade`` / ``_stage()``.

DISCIPLINE (enforced, not aspirational):
  * ``unknown`` != ``0``: a row whose robustness fields are NaN (unmeasured --
    cross-donor is populated on only ~14% of rows, cross-guide ~9%) is tiered
    ``unresolved`` -- NEVER silently counted as a pass (``high_confidence``) or
    a fail (``low_confidence``). ``tests/test_robust_ranking.py`` locks the
    NaN -> ``unresolved`` rule.
  * Descriptive vs decision separation: the tier is annotation. An ``inert``
    regression test runs a frame carrying ``robustness_tier`` through
    ``compute_readiness`` and asserts byte-identical output vs the plain frame,
    proving the tier cannot leak into any call.
  * Provenance: the pinned thresholds and the ``strict``/``lenient`` flags are
    returned in every ``robust_rank`` response so a consumer can tell exactly
    what "high-confidence" meant for that call.

Pinned thresholds (aligned with the calibration harness). Changing them changes
only which tier a row is *labelled*, never any readiness call.

Empirically measured on the reference cards (33,983 rows):
  * default (``not_flagged`` only, CROSS_MIN=0.2): 725 high_confidence.
  * ``lenient=True`` (also accept ``confounded_but_robust``): 1,097 -- this is
    the ~1,102 figure the calibration reported (1,102 replicate-passing rows
    minus 5 that are ``batch_sensitivity_flag == 'sensitive'``). The plan's
    "still 1,102 after the other filters" arithmetic omitted the batch flag;
    the conservative default therefore lands at 725, not 1,102.
  * ``strict=True`` (CROSS_MIN=0.5): 400 (default) / 612 (lenient).
In all variants ~30,989 rows are ``unresolved`` (a robustness field is NaN),
honoring ``unknown != 0``.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd

# --- Pinned, documented thresholds -----------------------------------------
# Aligned with the calibration harness. These are labelling thresholds only:
# moving them changes which tier a row is tagged, never any decision/call.
CROSS_MIN = 0.2          # min cross-donor AND cross-guide correlation (default)
CROSS_MIN_STRICT = 0.5   # strict variant
MIN_CELLS = 200          # min n_cells_target

_TARGET_COL = "target"
_GRADE_COL = "statistical_evidence_grade"
_DE_COL = "n_total_de_genes"
_CELLS_COL = "n_cells_target"

# Robustness fields the tier reads. A NaN/missing value in ANY of these makes a
# row ``unresolved`` (unmeasured), never ``low_confidence``.
_BOOL_FIELDS = ("replicate_pass_flag", "offtarget_flag")
_NUM_FIELDS = ("crossdonor_correlation_mean", "crossguide_correlation", _CELLS_COL)
_BATCH_FIELD = "batch_sensitivity_flag"
# batch_sensitivity_flag has THREE values (measured on the reference cards):
#   not_flagged (22,702) / sensitive (10,108) / confounded_but_robust (1,173).
# Default high_confidence accepts only ``not_flagged`` (conservative, aligned
# with calibration). ``confounded_but_robust`` was confounded at some point, so
# it is NOT high_confidence by default; ``lenient=True`` additionally accepts it.
_BATCH_PASS_DEFAULT = frozenset({"not_flagged"})
_BATCH_PASS_LENIENT = frozenset({"not_flagged", "confounded_but_robust"})

TIER_HIGH = "high_confidence"
TIER_UNRESOLVED = "unresolved"
TIER_LOW = "low_confidence"

REQUIRED_COLUMNS = (_TARGET_COL, "replicate_pass_flag")


def _coerce_bool_tristate(series: pd.Series) -> pd.Series:
    """Coerce to a True / False / NaN tri-state (honoring ``unknown != 0``).

    A plain ``.astype(str).isin({'true', ...})`` would map NaN (unmeasured) to
    ``False`` -- silently turning "unknown" into "fails", the exact anti-pattern
    the discipline forbids. This keeps NaN as NaN so the tier can call it
    ``unresolved``.
    """

    def convert(value: Any) -> Any:
        if pd.isna(value):
            return np.nan
        if isinstance(value, (bool, np.bool_)):
            return bool(value)
        token = str(value).strip().lower()
        if token in {"true", "1", "yes", "y", "t"}:
            return True
        if token in {"false", "0", "no", "n", "f"}:
            return False
        return np.nan  # unrecognized -> unknown, never a silent False

    return series.map(convert)


def robustness_tier(cards_df: pd.DataFrame, strict: bool = False, lenient: bool = False) -> pd.Series:
    """Three-state robustness tier per row: high_confidence / unresolved / low_confidence.

    * ``high_confidence`` -- ALL measurable robustness checks pass:
      ``replicate_pass_flag == True`` AND ``batch_sensitivity_flag`` is an
      accepted value (``not_flagged``; plus ``confounded_but_robust`` when
      ``lenient``) AND ``offtarget_flag == False`` AND
      ``crossdonor_correlation_mean >= CROSS`` AND
      ``crossguide_correlation >= CROSS`` AND ``n_cells_target >= MIN_CELLS``,
      where ``CROSS`` is ``CROSS_MIN`` (or ``CROSS_MIN_STRICT`` when ``strict``).
    * ``unresolved`` -- ANY required robustness field is NaN/missing
      (unmeasured). NOT high, NOT low -- honors ``unknown != 0``.
    * ``low_confidence`` -- every required field is measurable but at least one
      check fails.

    Returns a ``pd.Series[str]`` aligned to ``cards_df.index``. Purely
    descriptive: this value never feeds any readiness call.
    """
    n = len(cards_df)
    cross_min = CROSS_MIN_STRICT if strict else CROSS_MIN
    batch_ok_values = _BATCH_PASS_LENIENT if lenient else _BATCH_PASS_DEFAULT

    # A missing column is treated as all-NaN (unmeasured) -> everything unresolved
    # on that axis, never a fabricated pass.
    def _col(name: str) -> pd.Series:
        if name in cards_df.columns:
            return cards_df[name]
        return pd.Series([np.nan] * n, index=cards_df.index)

    rep = _coerce_bool_tristate(_col("replicate_pass_flag"))
    off = _coerce_bool_tristate(_col("offtarget_flag"))
    cd = pd.to_numeric(_col("crossdonor_correlation_mean"), errors="coerce")
    cg = pd.to_numeric(_col("crossguide_correlation"), errors="coerce")
    nc = pd.to_numeric(_col(_CELLS_COL), errors="coerce")

    batch_raw = _col(_BATCH_FIELD)
    batch_missing = batch_raw.isna()
    batch_str = batch_raw.astype(str)

    missing = (
        rep.isna()
        | off.isna()
        | cd.isna()
        | cg.isna()
        | nc.isna()
        | batch_missing
    )

    passes = (
        (rep == True)  # noqa: E712 -- object dtype; `is True` won't vectorize
        & batch_str.isin(batch_ok_values)
        & (off == False)  # noqa: E712
        & (cd >= cross_min)
        & (cg >= cross_min)
        & (nc >= MIN_CELLS)
    )

    tier = np.where(
        missing.to_numpy(),
        TIER_UNRESOLVED,
        np.where(passes.to_numpy(), TIER_HIGH, TIER_LOW),
    )
    return pd.Series(tier, index=cards_df.index, name="robustness_tier")


def high_confidence_mask(cards_df: pd.DataFrame, strict: bool = False, lenient: bool = False) -> pd.Series:
    """Boolean mask of rows tiered ``high_confidence`` (all measurable checks pass)."""
    return robustness_tier(cards_df, strict=strict, lenient=lenient) == TIER_HIGH


def _thresholds_block(strict: bool, lenient: bool) -> Dict[str, Any]:
    return {
        "cross_min": CROSS_MIN_STRICT if strict else CROSS_MIN,
        "min_cells": MIN_CELLS,
        "strict": strict,
        "lenient": lenient,
        "batch_pass_values": sorted(_BATCH_PASS_LENIENT if lenient else _BATCH_PASS_DEFAULT),
        "descriptive_only": True,
        "note": (
            "filter-then-rank: rows are filtered to high_confidence BEFORE "
            "ordering; unresolved rows (a robustness field is NaN) are never "
            "counted as pass or fail (unknown != 0)."
        ),
    }


def robust_rank(cards_df: pd.DataFrame, top_n: int = 100, strict: bool = False, lenient: bool = False) -> Dict[str, Any]:
    """Filter-then-rank short-list: high_confidence rows only, ranked, de-duped to target.

    Filters to ``high_confidence`` FIRST, then sorts the survivors by
    ``(statistical_evidence_grade, n_total_de_genes, n_cells_target)`` descending
    and de-duplicates to one row per ``target`` (each target's strongest-grade
    row), then truncates to ``top_n``.

    Returns a dict with transparent survivor counts so the churn the calibration
    surfaced is visible::

        {available, n_total, n_high_confidence, n_unresolved, returned,
         targets, thresholds}

    Honest-fallback: ``available: False`` (with zeroed counts) when the required
    columns (``target``, ``replicate_pass_flag``) are absent.
    """
    thresholds = _thresholds_block(strict, lenient)
    if not all(col in cards_df.columns for col in REQUIRED_COLUMNS):
        return {
            "available": False,
            "n_total": int(len(cards_df)),
            "n_high_confidence": 0,
            "n_unresolved": 0,
            "returned": 0,
            "targets": [],
            "thresholds": thresholds,
        }

    tier = robustness_tier(cards_df, strict=strict, lenient=lenient)
    n_total = int(len(cards_df))
    n_high = int((tier == TIER_HIGH).sum())
    n_unresolved = int((tier == TIER_UNRESOLVED).sum())

    high = cards_df[tier == TIER_HIGH].copy()
    high["robustness_tier"] = TIER_HIGH  # transparent, additive tag on the survivors

    # Deterministic filter-then-rank ordering. Missing sort columns coerce to
    # NaN and sort last; a stable sort keeps ties reproducible.
    for col in (_GRADE_COL, _DE_COL, _CELLS_COL):
        high[f"_sort_{col}"] = pd.to_numeric(high.get(col), errors="coerce")
    high = high.sort_values(
        by=[f"_sort_{_GRADE_COL}", f"_sort_{_DE_COL}", f"_sort_{_CELLS_COL}"],
        ascending=[False, False, False],
        kind="mergesort",
        na_position="last",
    )
    # one row per target: its strongest-grade (then breadth, then cells) row
    ranked = high.drop_duplicates(subset=[_TARGET_COL], keep="first")
    ranked = ranked.drop(columns=[c for c in ranked.columns if c.startswith("_sort_")])

    if top_n and top_n > 0:
        ranked = ranked.head(top_n)

    targets = _json_records(ranked)
    return {
        "available": True,
        "n_total": n_total,
        "n_high_confidence": n_high,
        "n_unresolved": n_unresolved,
        "returned": len(ranked),
        "targets": targets,
        "thresholds": thresholds,
    }


def _json_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """NaN/inf -> null JSON-compliant records (mirrors ``api.deps._json_records``)."""
    import json

    return json.loads(df.where(pd.notna(df), None).to_json(orient="records"))
