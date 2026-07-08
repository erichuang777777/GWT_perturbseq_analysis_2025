"""A3: perturbation-prediction benchmark harness (methodology evaluation only).

**What this is:** 這不是「做一個預測模型」,而是「做一個能誠實比較預測模型 vs
baseline 的評測框架」-- this is NOT "build a prediction model", it is "build a
harness that HONESTLY compares a prediction method against a baseline". It
uses this platform's own real, already-computed multi-condition DE statistics
(``metadata/suppl_tables/DE_stats.suppl_table.csv``: real ``Rest`` /
``Stim8hr`` / ``Stim48hr`` on-target knockdown effect sizes, one row per
target per condition) to run a held-out evaluation: for each target with real
DE stats in all three conditions, hold out one condition's effect size and
predict it from the other two, rotating which condition is held out (3
folds), then score the prediction against the *real* held-out value.

**Baseline predictor** (required, per ``docs/next_phases_plan.md`` §A3):
"用平均效應" -- predict the held-out condition's effect size as the mean of
the two known conditions' effect sizes for that target
(``baseline_mean_predictor``). An optional, slightly-smarter comparator
(``nearest_condition_predictor`` -- predict from whichever known condition is
temporally nearest to the held-out one) is also computed alongside it, purely
so the baseline's honesty can be judged against a second reference point, not
because either method is being proposed as a real predictive model.

**Guardrail (§A3, verbatim):** "結果只進 benchmark 報告,絕不寫入
`target_cards.csv` 或 readiness" -- results only ever go into a benchmark
report, and are NEVER written into ``target_cards.csv`` or the readiness
engine. This module is a fully standalone, read-only offline evaluation
report generator. It does not import, call, or modify
``readiness_engine.py``, ``build_target_cards.py``'s card-emitting logic, or
``target_card_api.py``, and nothing in this module writes any file that
those modules read.

**Honest-fallback contract:** a target missing real DE stats for any one of
the three conditions is skipped explicitly and recorded in the ``skipped``
table with the missing condition(s) named -- never imputed, never guessed,
never silently dropped without a record. See ``split_eligible_targets``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np
import pandas as pd
from scipy import stats

from config import settings

PathLike = Union[str, Path]

# The three real culture conditions this platform's DE_stats table covers
# (verbatim values of the real `culture_condition` column).
CONDITIONS: List[str] = ["Rest", "Stim8hr", "Stim48hr"]

# Ordinal "time" position used only by the optional nearest-condition
# comparator below -- Rest is the unstimulated baseline, Stim8hr/Stim48hr are
# 8h/48h post-stimulation, so Stim8hr is temporally closer to both neighbors
# than Rest and Stim48hr are to each other.
_CONDITION_ORDER: Dict[str, int] = {"Rest": 0, "Stim8hr": 1, "Stim48hr": 2}

# Real, verbatim column names in metadata/suppl_tables/DE_stats.suppl_table.csv
# (verified against the actual file -- not assumed).
REQUIRED_DE_COLUMNS = [
    "target_contrast",
    "target_contrast_gene_name",
    "culture_condition",
    "ontarget_effect_size",
]

CAVEAT_TEXT = (
    "methodology-benchmark output only -- an honest held-out comparison of a "
    "baseline predictor ('predict the mean of the two known conditions') "
    "against real on-target DE effect sizes across Rest/Stim8hr/Stim48hr; "
    "this is NOT a target score, NOT a prediction of drug efficacy, and is "
    "never wired into target_cards.csv or the readiness engine"
)

_SKIPPED_COLUMNS = ["target_id", "target", "missing_conditions"]
_FOLD_COLUMNS = [
    "target_id",
    "target",
    "held_out_condition",
    "known_conditions",
    "actual_effect",
    "baseline_mean_prediction",
    "baseline_abs_error",
    "nearest_condition_prediction",
    "nearest_condition_abs_error",
]
_FOLD_SUMMARY_COLUMNS = [
    "held_out_condition",
    "n_targets",
    "baseline_mean_abs_error",
    "baseline_pearson_r",
    "baseline_spearman_r",
    "nearest_condition_mean_abs_error",
    "nearest_condition_pearson_r",
]


def empty_benchmark_result(reason: str) -> Dict[str, Any]:
    """The honest-fallback shape returned whenever real data isn't usable.

    Never a fabricated benchmark -- always ``available: False`` plus the
    concrete ``reason`` (missing file, missing columns, or zero eligible
    targets), with the same table shapes the success path returns (empty).
    """
    return {
        "available": False,
        "reason": reason,
        "conditions": list(CONDITIONS),
        "n_targets_eligible": 0,
        "n_targets_skipped": 0,
        "skipped": pd.DataFrame(columns=_SKIPPED_COLUMNS),
        "per_target_fold": pd.DataFrame(columns=_FOLD_COLUMNS),
        "fold_summary": pd.DataFrame(columns=_FOLD_SUMMARY_COLUMNS),
        "overall_summary": {},
        "caveat": CAVEAT_TEXT,
    }


def load_de_stats(path: Optional[PathLike] = None) -> Dict[str, Any]:
    """Load the real DE_stats supplementary table.

    Defaults to ``config.settings.DE_STATS_PATH``
    (``metadata/suppl_tables/DE_stats.suppl_table.csv``). Returns
    ``{"available": bool, "reason": str|None, "table": DataFrame}``. A
    missing file or a file missing any of ``REQUIRED_DE_COLUMNS`` produces an
    explicit ``available: False`` with an empty table -- never a guessed
    schema.
    """
    resolved = Path(path) if path is not None else settings.DE_STATS_PATH
    if not resolved.exists():
        return {"available": False, "reason": f"DE_stats file not found: {resolved}", "table": pd.DataFrame()}
    df = pd.read_csv(resolved)
    missing = [c for c in REQUIRED_DE_COLUMNS if c not in df.columns]
    if missing:
        return {
            "available": False,
            "reason": f"DE_stats file missing required columns: {missing}",
            "table": pd.DataFrame(),
        }
    return {"available": True, "reason": None, "table": df}


def pivot_effect_by_condition(de_df: pd.DataFrame, conditions: Sequence[str] = CONDITIONS) -> pd.DataFrame:
    """Reshape the real long-format DE table into one row per target.

    Uses the real columns verbatim (``target_contrast`` = Ensembl gene ID,
    ``target_contrast_gene_name`` = gene symbol, ``culture_condition`` =
    Rest/Stim8hr/Stim48hr, ``ontarget_effect_size`` = the real on-target
    knockdown effect-size value). A target/condition combination absent from
    the source table becomes ``NaN`` here -- never filled with 0 or any other
    imputed value. Callers must check for ``NaN`` explicitly (see
    ``split_eligible_targets``) rather than treating a missing cell as a real
    zero effect.
    """
    name_map = (
        de_df[["target_contrast", "target_contrast_gene_name"]]
        .drop_duplicates("target_contrast")
        .set_index("target_contrast")["target_contrast_gene_name"]
    )
    wide = de_df.pivot_table(
        index="target_contrast",
        columns="culture_condition",
        values="ontarget_effect_size",
        aggfunc="first",
    )
    for c in conditions:
        if c not in wide.columns:
            wide[c] = np.nan
    wide = wide[list(conditions)]
    wide.insert(0, "target", name_map.reindex(wide.index))
    wide = wide.reset_index().rename(columns={"target_contrast": "target_id"})
    return wide


def split_eligible_targets(wide_df: pd.DataFrame, conditions: Sequence[str] = CONDITIONS) -> Dict[str, pd.DataFrame]:
    """Honest-fallback split of pivoted targets into eligible vs skipped.

    A target is "eligible" for the held-out benchmark only if it has a real,
    non-null ``ontarget_effect_size`` in every one of ``conditions``. Any
    target missing one or more conditions is placed in ``skipped`` with the
    exact missing condition name(s) recorded -- it is never imputed, and
    never silently dropped without a record of why.
    """
    conditions = list(conditions)
    has_all = wide_df[conditions].notna().all(axis=1)
    eligible = wide_df[has_all].reset_index(drop=True)

    skipped_rows = wide_df[~has_all].copy()
    if not skipped_rows.empty:
        skipped_rows["missing_conditions"] = skipped_rows[conditions].apply(
            lambda row: ",".join(c for c in conditions if pd.isna(row[c])), axis=1
        )
    else:
        skipped_rows["missing_conditions"] = pd.Series(dtype=str)
    skipped = skipped_rows.reindex(columns=_SKIPPED_COLUMNS).reset_index(drop=True)
    return {"eligible": eligible, "skipped": skipped}


def baseline_mean_predictor(known_values: Sequence[float]) -> float:
    """Required baseline: predict the held-out effect size as the mean of the
    known conditions' effect sizes ("用平均效應", per
    ``docs/next_phases_plan.md`` §A3)."""
    return float(np.mean(list(known_values)))


def nearest_condition_predictor(
    known: Dict[str, float], held_out: str, conditions: Sequence[str] = CONDITIONS
) -> float:
    """Optional secondary comparator: predict from whichever known condition
    is temporally nearest to the held-out one (see ``_CONDITION_ORDER``).
    Ties (e.g. holding out Stim8hr, equidistant from Rest and Stim48hr) fall
    back to the mean of the tied conditions. This is NOT proposed as a real
    predictive model -- it exists only to give the required baseline a
    second, equally-simple reference point for honest comparison.
    """
    del conditions  # kept for signature symmetry; ordering comes from _CONDITION_ORDER
    held_idx = _CONDITION_ORDER[held_out]
    dists = {c: abs(_CONDITION_ORDER[c] - held_idx) for c in known}
    min_dist = min(dists.values())
    nearest = [c for c, d in dists.items() if d == min_dist]
    return float(np.mean([known[c] for c in nearest]))


def build_holdout_folds(eligible_df: pd.DataFrame, conditions: Sequence[str] = CONDITIONS) -> pd.DataFrame:
    """Rotate which condition is held out (one fold per condition, 3 folds
    total for ``CONDITIONS``) and predict it from the other two, for every
    eligible target. Every ``actual_effect`` value is a real
    ``ontarget_effect_size`` already present in the DE_stats table -- nothing
    here is fabricated, only rearranged and compared.

    Returns a long-format table (one row per target per fold) with both the
    baseline (mean-of-known) and nearest-condition predictions plus their
    absolute errors against the real held-out value.
    """
    conditions = list(conditions)
    rows: List[Dict[str, Any]] = []
    for _, r in eligible_df.iterrows():
        known_all = {c: float(r[c]) for c in conditions}
        for held_out in conditions:
            known = {c: v for c, v in known_all.items() if c != held_out}
            actual = known_all[held_out]
            baseline_pred = baseline_mean_predictor(list(known.values()))
            nearest_pred = nearest_condition_predictor(known, held_out, conditions)
            rows.append(
                {
                    "target_id": r["target_id"],
                    "target": r["target"],
                    "held_out_condition": held_out,
                    "known_conditions": ",".join(sorted(known)),
                    "actual_effect": actual,
                    "baseline_mean_prediction": baseline_pred,
                    "baseline_abs_error": abs(baseline_pred - actual),
                    "nearest_condition_prediction": nearest_pred,
                    "nearest_condition_abs_error": abs(nearest_pred - actual),
                }
            )
    return pd.DataFrame(rows, columns=_FOLD_COLUMNS)


def _safe_corr(a: Sequence[float], b: Sequence[float], method: str) -> float:
    """Pearson/Spearman correlation that degrades honestly to NaN (never 0,
    never an exception) when there isn't enough data or variance to compute
    one -- e.g. fewer than 2 points, or a constant series."""
    a_arr = np.asarray(list(a), dtype=float)
    b_arr = np.asarray(list(b), dtype=float)
    if len(a_arr) < 2 or np.std(a_arr) == 0 or np.std(b_arr) == 0:
        return float("nan")
    if method == "pearson":
        r, _ = stats.pearsonr(a_arr, b_arr)
    else:
        r, _ = stats.spearmanr(a_arr, b_arr)
    return float(r)


def summarize_folds(per_target_fold: pd.DataFrame, conditions: Sequence[str] = CONDITIONS) -> pd.DataFrame:
    """Aggregate the per-target-per-fold table into one row per held-out
    condition: mean absolute error and correlation for both the baseline and
    the nearest-condition comparator, computed honestly per fold (a fold with
    fewer than 2 targets, or zero prediction variance, reports NaN
    correlation rather than a misleading number)."""
    rows: List[Dict[str, Any]] = []
    for held_out in conditions:
        sub = per_target_fold[per_target_fold["held_out_condition"] == held_out]
        if sub.empty:
            continue
        rows.append(
            {
                "held_out_condition": held_out,
                "n_targets": int(len(sub)),
                "baseline_mean_abs_error": float(sub["baseline_abs_error"].mean()),
                "baseline_pearson_r": _safe_corr(sub["actual_effect"], sub["baseline_mean_prediction"], "pearson"),
                "baseline_spearman_r": _safe_corr(sub["actual_effect"], sub["baseline_mean_prediction"], "spearman"),
                "nearest_condition_mean_abs_error": float(sub["nearest_condition_abs_error"].mean()),
                "nearest_condition_pearson_r": _safe_corr(
                    sub["actual_effect"], sub["nearest_condition_prediction"], "pearson"
                ),
            }
        )
    return pd.DataFrame(rows, columns=_FOLD_SUMMARY_COLUMNS)


def run_benchmark(
    de_df: Optional[pd.DataFrame] = None,
    path: Optional[PathLike] = None,
    conditions: Sequence[str] = CONDITIONS,
) -> Dict[str, Any]:
    """Top-level entry point: build the full held-out benchmark report.

    Either pass an already-loaded ``de_df`` (e.g. a golden-file fixture) or
    let this call ``load_de_stats(path)`` itself. Returns a dict:

    - ``available`` / ``reason``: honest-fallback status.
    - ``conditions``: the three real culture conditions evaluated.
    - ``n_targets_eligible`` / ``n_targets_skipped``: how many real targets
      had DE stats in all three conditions vs were honestly skipped.
    - ``skipped``: per-target record of which condition(s) were missing.
    - ``per_target_fold``: per-target, per-fold prediction + real error.
    - ``fold_summary``: per-condition (per-fold) aggregate error/correlation.
    - ``overall_summary``: aggregate across all folds/targets.
    - ``caveat``: ``CAVEAT_TEXT`` -- always present, methodology-only.

    This function performs no writes -- it returns a plain dict/DataFrame
    report. It never touches ``target_cards.csv``, any readiness output, or
    any file used by ``build_target_cards.py`` / ``readiness_engine.py`` /
    ``target_card_api.py``. Per the §A3 guardrail, results only ever belong
    in a benchmark report.
    """
    if de_df is None:
        loaded = load_de_stats(path)
        if not loaded["available"]:
            return empty_benchmark_result(loaded["reason"])
        de_df = loaded["table"]
    else:
        missing = [c for c in REQUIRED_DE_COLUMNS if c not in de_df.columns]
        if missing:
            return empty_benchmark_result(f"input DE table missing required columns: {missing}")

    wide = pivot_effect_by_condition(de_df, conditions)
    split = split_eligible_targets(wide, conditions)
    eligible, skipped = split["eligible"], split["skipped"]

    if eligible.empty:
        result = empty_benchmark_result("no targets have real DE stats in all required conditions")
        result["skipped"] = skipped
        result["n_targets_skipped"] = len(skipped)
        return result

    per_target_fold = build_holdout_folds(eligible, conditions)
    fold_summary = summarize_folds(per_target_fold, conditions)

    overall_summary = {
        "n_targets_eligible": int(len(eligible)),
        "n_targets_skipped": int(len(skipped)),
        "n_fold_rows": int(len(per_target_fold)),
        "baseline_mean_abs_error_overall": float(per_target_fold["baseline_abs_error"].mean()),
        "baseline_pearson_r_overall": _safe_corr(
            per_target_fold["actual_effect"], per_target_fold["baseline_mean_prediction"], "pearson"
        ),
        "baseline_spearman_r_overall": _safe_corr(
            per_target_fold["actual_effect"], per_target_fold["baseline_mean_prediction"], "spearman"
        ),
        "nearest_condition_mean_abs_error_overall": float(per_target_fold["nearest_condition_abs_error"].mean()),
        "nearest_condition_pearson_r_overall": _safe_corr(
            per_target_fold["actual_effect"], per_target_fold["nearest_condition_prediction"], "pearson"
        ),
    }

    return {
        "available": True,
        "reason": None,
        "conditions": list(conditions),
        "n_targets_eligible": int(len(eligible)),
        "n_targets_skipped": int(len(skipped)),
        "skipped": skipped,
        "per_target_fold": per_target_fold,
        "fold_summary": fold_summary,
        "overall_summary": overall_summary,
        "caveat": CAVEAT_TEXT,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Run the A3 perturbation-prediction benchmark harness (offline, "
            "methodology-only -- never writes target_cards.csv or readiness)."
        )
    )
    parser.add_argument("--de-stats", type=Path, default=None, help="Path to DE_stats.suppl_table.csv")
    parser.add_argument("--output-fold-detail", type=Path, default=None)
    parser.add_argument("--output-fold-summary", type=Path, default=None)
    args = parser.parse_args()

    report = run_benchmark(path=args.de_stats)
    if not report["available"]:
        print(f"benchmark unavailable: {report['reason']}")
    else:
        print(f"eligible targets: {report['n_targets_eligible']} (skipped: {report['n_targets_skipped']})")
        print(report["fold_summary"].to_string(index=False))
        print()
        print("overall_summary:", report["overall_summary"])
        print()
        print("caveat:", report["caveat"])
        if args.output_fold_detail:
            report["per_target_fold"].to_csv(args.output_fold_detail, index=False)
        if args.output_fold_summary:
            report["fold_summary"].to_csv(args.output_fold_summary, index=False)
