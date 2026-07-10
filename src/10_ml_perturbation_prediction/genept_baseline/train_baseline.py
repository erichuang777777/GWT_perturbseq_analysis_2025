#!/usr/bin/env python3
"""
GenePT 風格基線：用被擾動基因的 GenePT 文字嵌入（PCA 降到 128 維）
預測該擾動的下游全基因表現變化 profile（log_fc 向量），
用 multi-output Ridge regression（矩陣化：W 從 embedding 空間映射到
response 空間，跨所有訓練標的共用權重——不對測試標的做任何 one-hot
或身分編碼，這是它相對於 CPA 能泛化到「訓練時沒見過的基因」的關鍵）。

**誠實護欄（README.md 已述，這裡重申）：**
- KFold 交叉驗證，target-level（每個 condition 內每個標的只出現一次，
  不會同時是 train 又是 test）。
- 每個 held-out 標的都跟「均值基線」（訓練集 response 向量的平均，
  完全忽略被擾動的是哪個基因）比較——這正是 2025-2026 文獻
  （Ahlmann-Eltze et al. *Nature Methods* 2025）反覆指出深度學習模型
  打不贏的基線。輸了就老實報輸了。
- 評估指標：每個 held-out 標的的 predicted vs. true response 向量的
  Pearson correlation（文獻標準做法），跨標的取中位數/平均數。
- 固定 random_state，deterministic。
- 結果只寫進 ../results/，不接觸任何 production 路徑。
"""

import json
import time
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "src/10_ml_perturbation_prediction/data"
RESULTS_DIR = REPO_ROOT / "src/10_ml_perturbation_prediction/results"
CONDITIONS = ["Rest", "Stim8hr", "Stim48hr"]
N_SPLITS = 5
ALPHA = 10.0  # ridge regularization strength; fixed (not tuned on test) for honesty
RANDOM_STATE = 0


def safe_corr(a, b):
    if np.std(a) == 0 or np.std(b) == 0:
        return np.nan
    r, _ = pearsonr(a, b)
    return r


def evaluate_condition(condition):
    resp_path = DATA_DIR / f"response_matrix_{condition}.npz"
    emb_path = DATA_DIR / "gene_embeddings_pca.npz"

    resp = np.load(resp_path, allow_pickle=True)
    emb = np.load(emb_path, allow_pickle=True)

    target_genes = resp["target_genes"]
    log_fc = resp["log_fc"]  # (n_targets, n_response_genes)

    gene_to_emb = dict(zip(emb["gene_symbols"], emb["embeddings"]))
    X = np.stack([gene_to_emb[g] for g in target_genes])  # (n_targets, 128)
    Y = log_fc

    n = len(target_genes)
    print(f"\n=== {condition} ===  n_targets={n}, n_response_genes={Y.shape[1]}")

    kf = KFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    model_corrs, baseline_corrs = [], []
    for fold, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        Y_train, Y_test = Y[train_idx], Y[test_idx]

        model = Ridge(alpha=ALPHA, random_state=RANDOM_STATE)
        model.fit(X_train, Y_train)
        Y_pred = model.predict(X_test)

        mean_profile = Y_train.mean(axis=0)  # the honest, hard-to-beat baseline

        for i in range(len(test_idx)):
            model_corrs.append(safe_corr(Y_pred[i], Y_test[i]))
            baseline_corrs.append(safe_corr(mean_profile, Y_test[i]))

    model_corrs = np.array(model_corrs, dtype=float)
    baseline_corrs = np.array(baseline_corrs, dtype=float)

    report = {
        "condition": condition,
        "n_targets": int(n),
        "n_response_genes": int(Y.shape[1]),
        "n_splits": N_SPLITS,
        "ridge_alpha": ALPHA,
        "model_mean_corr": float(np.nanmean(model_corrs)),
        "model_median_corr": float(np.nanmedian(model_corrs)),
        "baseline_mean_corr": float(np.nanmean(baseline_corrs)),
        "baseline_median_corr": float(np.nanmedian(baseline_corrs)),
        "model_beats_baseline": bool(np.nanmean(model_corrs) > np.nanmean(baseline_corrs)),
        "n_nan_model": int(np.isnan(model_corrs).sum()),
        "n_nan_baseline": int(np.isnan(baseline_corrs).sum()),
    }
    print(f"  GenePT-ridge  : mean r = {report['model_mean_corr']:.4f}, median r = {report['model_median_corr']:.4f}")
    print(f"  mean-baseline : mean r = {report['baseline_mean_corr']:.4f}, median r = {report['baseline_median_corr']:.4f}")
    print(f"  model beats baseline: {report['model_beats_baseline']}")
    return report


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    start = time.time()
    for condition in CONDITIONS:
        reports.append(evaluate_condition(condition))

    out = {
        "method": "GenePT ada-002 embeddings (PCA-128) + multi-output Ridge regression",
        "baseline": "mean training-set response profile (ignores which gene was perturbed)",
        "elapsed_seconds": time.time() - start,
        "per_condition": reports,
    }
    out_path = RESULTS_DIR / "genept_baseline_benchmark.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\n✅ 報告寫入 {out_path}")


if __name__ == "__main__":
    main()
