#!/usr/bin/env python3
"""
T1-rework：用被擾動基因「自己的」真實實驗特徵（而非 GenePT 外部文字嵌入）預測
其下游反應 profile（landmark 基因的 log_fc 向量），linear（Ridge）vs ML
（HistGradientBoostingRegressor，逐維訓練，因為它不支援 multi-output）。

**跟 `genept_baseline/train_baseline.py` 的差異只有一個：X 的來源。** 其餘完全
比照——KFold 交叉驗證（target-level，同一標的不會同時是 train 又是 test）、
每個 held-out 標的都跟「訓練集 response 向量的平均」比較（同一個誠實、難打贏的
基線）、評估指標是 Pearson correlation、固定 random_state、結果只寫進
`../results/`。

**Ridge 需要插補缺失值（median + 明確缺失指示欄，unknown != 0）；
HistGradientBoostingRegressor 逐維訓練、原生吃 NaN，不插補。**
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "src/10_ml_perturbation_prediction/data"
RESULTS_DIR = REPO_ROOT / "src/10_ml_perturbation_prediction/results"
CONDITIONS = ["Rest", "Stim8hr", "Stim48hr"]
N_SPLITS = 5
RIDGE_ALPHA = 10.0  # 跟 genept_baseline 用同一個值，方便比較（不是為了贏而調）
RANDOM_STATE = 0


def safe_corr(a, b):
    if np.std(a) == 0 or np.std(b) == 0:
        return np.nan
    r, _ = pearsonr(a, b)
    return r


def evaluate_condition(condition: str) -> dict:
    npz = np.load(DATA_DIR / f"real_features_response_{condition}.npz", allow_pickle=True)
    target_genes = npz["target_genes"]
    X_raw = npz["X"]  # (n_targets, n_features), 可能含 NaN
    Y = npz["Y"]  # (n_targets, n_landmark), 0.0 = 未達顯著（非 unknown）

    n = len(target_genes)
    print(f"\n=== {condition} === n_targets={n}, n_features={X_raw.shape[1]}, n_landmark={Y.shape[1]}")

    kf = KFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    ridge_corrs, gbr_corrs, baseline_corrs = [], [], []
    for tr_idx, te_idx in kf.split(X_raw):
        X_tr, X_te = X_raw[tr_idx], X_raw[te_idx]
        Y_tr, Y_te = Y[tr_idx], Y[te_idx]

        ridge = Pipeline(steps=[
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
            ("model", Ridge(alpha=RIDGE_ALPHA, random_state=RANDOM_STATE)),
        ])
        ridge.fit(X_tr, Y_tr)
        Y_pred_ridge = ridge.predict(X_te)

        # HistGBR 不支援 multi-output，逐維訓練（landmark 基因數不大，500 維可接受）
        Y_pred_gbr = np.zeros_like(Y_te)
        for j in range(Y.shape[1]):
            gbr = HistGradientBoostingRegressor(random_state=RANDOM_STATE, max_iter=100, learning_rate=0.1)
            gbr.fit(X_tr, Y_tr[:, j])
            Y_pred_gbr[:, j] = gbr.predict(X_te)

        mean_profile = Y_tr.mean(axis=0)

        for i in range(len(te_idx)):
            ridge_corrs.append(safe_corr(Y_pred_ridge[i], Y_te[i]))
            gbr_corrs.append(safe_corr(Y_pred_gbr[i], Y_te[i]))
            baseline_corrs.append(safe_corr(mean_profile, Y_te[i]))

    ridge_corrs = np.array(ridge_corrs, dtype=float)
    gbr_corrs = np.array(gbr_corrs, dtype=float)
    baseline_corrs = np.array(baseline_corrs, dtype=float)

    report = {
        "condition": condition,
        "n_targets": int(n),
        "n_features": int(X_raw.shape[1]),
        "n_landmark_genes": int(Y.shape[1]),
        "n_splits": N_SPLITS,
        "ridge_alpha": RIDGE_ALPHA,
        "ridge_mean_corr": float(np.nanmean(ridge_corrs)),
        "ridge_median_corr": float(np.nanmedian(ridge_corrs)),
        "hist_gbr_mean_corr": float(np.nanmean(gbr_corrs)),
        "hist_gbr_median_corr": float(np.nanmedian(gbr_corrs)),
        "baseline_mean_corr": float(np.nanmean(baseline_corrs)),
        "baseline_median_corr": float(np.nanmedian(baseline_corrs)),
        "ridge_beats_baseline": bool(np.nanmean(ridge_corrs) > np.nanmean(baseline_corrs)),
        "hist_gbr_beats_baseline": bool(np.nanmean(gbr_corrs) > np.nanmean(baseline_corrs)),
    }
    print(f"  real-features Ridge   : mean r = {report['ridge_mean_corr']:.4f}")
    print(f"  real-features HistGBR : mean r = {report['hist_gbr_mean_corr']:.4f}")
    print(f"  mean-baseline         : mean r = {report['baseline_mean_corr']:.4f}")
    print(f"  ridge beats baseline: {report['ridge_beats_baseline']}, "
          f"hist_gbr beats baseline: {report['hist_gbr_beats_baseline']}")
    return report


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    start = time.time()
    reports = [evaluate_condition(c) for c in CONDITIONS]

    out = {
        "method": "target's own real experimental features (n_cells, cross-donor/guide correlation, "
                   "guide-level robustness, baseline expression) + Ridge (linear) / HistGradientBoosting "
                   "(ML) -- predicting the target's own downstream log_fc profile over the 500 most "
                   "frequently significant landmark genes",
        "baseline": "mean training-set response profile (ignores which gene was perturbed) -- same "
                    "honest baseline used by genept_baseline",
        "response_source_caveat": "GWCD4i.DE_stats.h5ad (the dense response matrix genept_baseline used) "
                                   "is not present in this checkout (S3-only, ~15.6GB, not committed). "
                                   "Y is instead built from metadata/suppl_tables/full_signed_DE/ (adj_p<0.1 "
                                   "significant pairs only), landmark genes = top-500 most frequently "
                                   "significant downstream genes, 0.0 for non-significant pairs (a defensible "
                                   "floor -- adj_p>=0.1 means no significant change detected -- not a "
                                   "fabricated value, but coarser than the dense matrix).",
        "elapsed_seconds": time.time() - start,
        "per_condition": reports,
    }
    out_path = RESULTS_DIR / "real_features_baseline_benchmark.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\n✅ 報告寫入 {out_path}")


if __name__ == "__main__":
    main()
