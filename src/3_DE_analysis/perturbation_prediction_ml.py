"""Supervised ML extension of the A3 perturbation-prediction benchmark.

**What this is:** an honest, cross-validated comparison of supervised regressors
against the A3 mean-effect baseline on the SAME held-out task -- given a target's
on-target knockdown effect in two of {Rest, Stim8hr, Stim48hr}, predict the third.
The A3 baseline (`perturbation_prediction_benchmark.baseline_mean_predictor`)
predicts the held-out effect as the mean of the two known conditions and already
scores Pearson r ~= 0.93. This module asks the one honest question worth asking:
**can a model that learns across targets beat that baseline, or not?** A negative
result (baseline already near-ceiling) is a real, reportable finding -- this
harness is built to surface that, not to manufacture a win.

**Why this is the right supervised direction for this repo (and others are not):**
it is the only supervised task with a large, real, in-repo label set (11,086
eligible targets x 3 held-out folds = 33,258 labeled rows, the held-out
`ontarget_effect_size` itself). Supervised target-*prioritization* (ML-GPS style)
has no usable in-repo label set (only ~13 curated drug benchmarks), and a
patient-response classifier needs patient outcome labels this repo does not have
-- both are out of scope, not built here.

**Guardrails (enforced):**
- **Never feeds decisions.** Results live only in the returned report dict; this
  module never writes ``target_cards.csv``, readiness, or any file a card/
  readiness path reads. It is a methodology benchmark, full stop (same rule as
  the A3 harness it extends).
- **``unknown != 0``.** Missing features are never silently zeroed. The gradient-
  boosting model (``HistGradientBoostingRegressor``) consumes NaN natively; the
  linear model uses median imputation **plus an explicit missingness indicator**
  (`add_indicator=True`) so "missing" is a real feature, not a fabricated 0. The
  genuinely sparse robustness covariates (cross-donor ~14%, cross-guide ~9%
  coverage) exercise this directly.
- **Deterministic.** Fixed ``random_state`` and ``GroupKFold`` (grouped by target,
  so no target leaks across train/test); no ``Date.now``/unseeded randomness.
- **Honest small-print.** Correlations degrade to NaN (never a fake 0) when a fold
  lacks variance; the report states per model whether it beat the baseline.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from perturbation_prediction_benchmark import (
    CONDITIONS,
    REQUIRED_DE_COLUMNS,
    _safe_corr,
    load_de_stats,
)

# Per-target-per-condition covariates used as features (aggregated over the two
# KNOWN conditions so the held-out condition's own row never leaks into X).
# All are real DE_stats columns; the sparse ones (crossdonor/crossguide) are the
# unknown != 0 stress test.
_COVARIATE_COLUMNS = [
    "n_cells_target",
    "n_total_de_genes",
    "crossdonor_correlation_mean",
    "crossguide_correlation",
    "target_baseMean",
]

CAVEAT_TEXT = (
    "methodology benchmark only -- an honest, cross-validated (GroupKFold by "
    "target) comparison of supervised regressors against the A3 mean-effect "
    "baseline on the held-out perturbation-prediction task. NOT a target score, "
    "NOT a prediction of drug efficacy; never written to target_cards.csv or the "
    "readiness engine. A baseline win (mean-of-known already ~0.93 Pearson) is a "
    "legitimate, reported outcome."
)

_MODEL_NAMES = ("baseline_mean", "ridge", "hist_gbr")


def _sklearn_available() -> Optional[str]:
    try:
        import sklearn  # noqa: F401

        return None
    except Exception as exc:  # noqa: BLE001 -- honest-fallback if the ML stack is absent
        return f"scikit-learn not importable: {exc}"


def build_feature_frame(de_df: pd.DataFrame, conditions: Sequence[str] = CONDITIONS) -> Dict[str, Any]:
    """Build the supervised (X, y, groups) frame from the real long-format DE table.

    One row per (eligible target, held-out condition). Features: the two known
    conditions' ``ontarget_effect_size`` (sorted by condition index), the
    mean-of-known baseline prediction, target covariates aggregated over the two
    KNOWN conditions only (leak-free), and a held-out-condition one-hot. Label:
    the held-out condition's real ``ontarget_effect_size``. Missing covariates
    are kept as NaN (never 0).
    """
    conditions = list(conditions)
    missing = [c for c in REQUIRED_DE_COLUMNS if c not in de_df.columns]
    if missing:
        return {"available": False, "reason": f"DE table missing columns: {missing}", "X": None, "y": None, "groups": None}

    present_cov = [c for c in _COVARIATE_COLUMNS if c in de_df.columns]
    keep = ["target_contrast", "culture_condition", "ontarget_effect_size"] + present_cov
    df = de_df[keep].dropna(subset=["ontarget_effect_size"]).copy()

    # effect per (target, condition)
    eff = df.pivot_table(index="target_contrast", columns="culture_condition", values="ontarget_effect_size", aggfunc="first")
    for c in conditions:
        if c not in eff.columns:
            eff[c] = np.nan
    eff = eff[conditions]
    eligible = eff.index[eff[conditions].notna().all(axis=1)]

    # covariates per (target, condition) -> lookup for aggregating over known conds.
    # Reindex to the full eligible x conditions grid so a target that is all-NaN
    # for a sparse covariate (cross-donor ~14%, cross-guide ~9%) stays present as
    # NaN rather than being dropped by pivot_table -- unknown != 0, never absent.
    cov_by_tc: Dict[str, pd.DataFrame] = {}
    for c in present_cov:
        piv = df.pivot_table(index="target_contrast", columns="culture_condition", values=c, aggfunc="first", dropna=False)
        cov_by_tc[c] = piv.reindex(index=eligible, columns=conditions)

    rows: List[Dict[str, Any]] = []
    for target in eligible:
        for held in conditions:
            known = [c for c in conditions if c != held]
            ka, kb = sorted(known, key=conditions.index)
            row: Dict[str, Any] = {
                "known_effect_a": float(eff.loc[target, ka]),
                "known_effect_b": float(eff.loc[target, kb]),
            }
            row["baseline_pred"] = float(np.mean([row["known_effect_a"], row["known_effect_b"]]))
            # covariates aggregated over the two KNOWN conditions only (nanmean;
            # stays NaN if both are missing -- unknown != 0)
            for c in present_cov:
                vals = [cov_by_tc[c].loc[target, k] if k in cov_by_tc[c].columns else np.nan for k in known]
                vals = [v for v in vals if pd.notna(v)]
                row[f"cov_{c}"] = float(np.mean(vals)) if vals else np.nan
            for c in conditions:
                row[f"heldout_is_{c}"] = 1.0 if c == held else 0.0
            row["_y"] = float(eff.loc[target, held])
            row["_group"] = str(target)
            rows.append(row)

    frame = pd.DataFrame(rows)
    if frame.empty:
        return {"available": False, "reason": "no eligible targets with all conditions", "X": None, "y": None, "groups": None}
    y = frame.pop("_y")
    groups = frame.pop("_group")
    return {"available": True, "reason": None, "X": frame, "y": y, "groups": groups, "n_targets": len(eligible)}


def _fit_predict_models(X_tr, y_tr, X_te):
    """Fit ridge (impute+indicator) and HistGBR (native NaN), return test preds."""
    from sklearn.compose import ColumnTransformer  # noqa: F401  (kept for clarity of intent)
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    preds: Dict[str, np.ndarray] = {}
    # Baseline needs no training: mean of the two known effects (== baseline_pred).
    preds["baseline_mean"] = X_te["baseline_pred"].to_numpy()

    # Ridge: median-impute + explicit missingness indicator (unknown != 0), scaled.
    ridge = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
            ("model", Ridge(alpha=1.0, random_state=0)),
        ]
    )
    ridge.fit(X_tr, y_tr)
    preds["ridge"] = ridge.predict(X_te)

    # Gradient boosting: consumes NaN natively (no imputation) -> honest unknowns.
    gbr = HistGradientBoostingRegressor(random_state=0, max_iter=200, learning_rate=0.05)
    gbr.fit(X_tr, y_tr)
    preds["hist_gbr"] = gbr.predict(X_te)
    return preds


def run_ml_benchmark(
    de_df: Optional[pd.DataFrame] = None,
    path: Optional[str] = None,
    n_splits: int = 5,
    conditions: Sequence[str] = CONDITIONS,
) -> Dict[str, Any]:
    """Cross-validated (GroupKFold by target) supervised-vs-baseline benchmark.

    Returns ``{"available", "reason", "n_targets", "n_rows", "n_splits",
    "models": {name: {pearson, spearman, mae, beats_baseline_pearson,
    beats_baseline_mae}}, "caveat"}``. Honest-fallback (``available: False``)
    if scikit-learn is absent or there is no usable data. Never writes anything.
    """
    reason = _sklearn_available()
    if reason is not None:
        return {"available": False, "reason": reason, "models": {}, "caveat": CAVEAT_TEXT}

    if de_df is None:
        loaded = load_de_stats(path)
        if not loaded["available"]:
            return {"available": False, "reason": loaded["reason"], "models": {}, "caveat": CAVEAT_TEXT}
        de_df = loaded["table"]

    built = build_feature_frame(de_df, conditions)
    if not built["available"]:
        return {"available": False, "reason": built["reason"], "models": {}, "caveat": CAVEAT_TEXT}

    from sklearn.model_selection import GroupKFold

    X, y, groups = built["X"], built["y"], built["groups"]
    n_groups = groups.nunique()
    splits = int(min(n_splits, n_groups))
    if splits < 2:
        return {"available": False, "reason": "need >= 2 target groups for CV", "models": {}, "caveat": CAVEAT_TEXT}

    per_fold: Dict[str, Dict[str, List[float]]] = {m: {"pearson": [], "spearman": [], "mae": []} for m in _MODEL_NAMES}
    gkf = GroupKFold(n_splits=splits)
    for tr_idx, te_idx in gkf.split(X, y, groups):
        X_tr, X_te = X.iloc[tr_idx], X.iloc[te_idx]
        y_tr, y_te = y.iloc[tr_idx], y.iloc[te_idx]
        preds = _fit_predict_models(X_tr, y_tr, X_te)
        actual = y_te.to_numpy()
        for m in _MODEL_NAMES:
            p = preds[m]
            per_fold[m]["pearson"].append(_safe_corr(actual, p, "pearson"))
            per_fold[m]["spearman"].append(_safe_corr(actual, p, "spearman"))
            per_fold[m]["mae"].append(float(np.mean(np.abs(p - actual))))

    def _agg(vals: List[float]) -> float:
        arr = np.asarray(vals, dtype=float)
        arr = arr[~np.isnan(arr)]
        return float(np.mean(arr)) if arr.size else float("nan")

    base_pearson = _agg(per_fold["baseline_mean"]["pearson"])
    base_mae = _agg(per_fold["baseline_mean"]["mae"])
    models: Dict[str, Any] = {}
    for m in _MODEL_NAMES:
        pe, mae = _agg(per_fold[m]["pearson"]), _agg(per_fold[m]["mae"])
        models[m] = {
            "pearson": pe,
            "spearman": _agg(per_fold[m]["spearman"]),
            "mae": mae,
            # honest verdict: a learned model must beat the mean-of-known baseline
            # on BOTH higher correlation and lower error to count as "better".
            "beats_baseline_pearson": bool(m != "baseline_mean" and pe > base_pearson),
            "beats_baseline_mae": bool(m != "baseline_mean" and mae < base_mae),
        }

    any_win = any(models[m]["beats_baseline_pearson"] and models[m]["beats_baseline_mae"] for m in _MODEL_NAMES if m != "baseline_mean")
    return {
        "available": True,
        "reason": None,
        "n_targets": built["n_targets"],
        "n_rows": int(len(X)),
        "n_splits": splits,
        "models": models,
        "any_model_beats_baseline": any_win,
        "caveat": CAVEAT_TEXT,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Supervised vs baseline perturbation-prediction benchmark (offline, methodology-only).")
    ap.add_argument("--de-stats", type=str, default=None)
    ap.add_argument("--splits", type=int, default=5)
    args = ap.parse_args()
    rep = run_ml_benchmark(path=args.de_stats, n_splits=args.splits)
    if not rep["available"]:
        print("unavailable:", rep["reason"])
    else:
        print(f"targets={rep['n_targets']} rows={rep['n_rows']} splits={rep['n_splits']}")
        for name, m in rep["models"].items():
            print(f"  {name:14s} pearson={m['pearson']:.4f} mae={m['mae']:.4f} "
                  f"beats_baseline={'Y' if (m['beats_baseline_pearson'] and m['beats_baseline_mae']) else '-'}")
        print("any model beats baseline:", rep["any_model_beats_baseline"])
        print("caveat:", rep["caveat"])
