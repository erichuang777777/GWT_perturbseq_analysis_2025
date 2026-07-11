#!/usr/bin/env python3
"""
T2「已知調控子分類器」——linear vs ML，能否贏過現有的簡單排序基線？

**任務定義（跟現有基線同一操作型定義，才能公平比較）：** `methodological_validation/
README.md` 的 AUROC 0.85 是「positives vs 1,211 個 unlabelled rest 基因」（不是
平衡負類——10/11 個 curated housekeeping 負類早被 n>=200 gate 濾掉，只剩 1 個
HPRT1 存活）。這裡完全比照同一個操作型定義：`y = 1` 如果 `truth_class=='positive'`
（13 個），否則 `y = 0`（`rest` + 那唯一 1 個 `negative`，合計 1,212 個）——不是
傳統平衡二分類，是跟基線同條件的 ranking/AUROC 比較。

**CV 策略：** 13 個正類、5-fold StratifiedKFold（按 `y` 分層，每個 fold 約 2-3 個
正類），跨 fold 彙整 out-of-fold 分數後算整體 AUROC——避免用同一批資料訓練又評分
造成的樂觀偏誤。基線（`ctx_specific_de` 排序）完全不需要訓練，直接對全部 1,225
個基因算分數，是名符其實的「跟資料完全獨立」的基準，因此不需要 CV，
但為了公平比較，也在同一個 y 定義下算它的整體 AUROC——理論上應重現 README
記載的 0.85（sanity check：驗證這裡的任務框架跟既有基線一致）。

**兩個特徵集：** `full`（含 CIRCULAR_COLUMNS + LABEL_ADJACENT_COLUMNS）、`ablated`
（排除兩者）。誠實的結論只能來自 `ablated`——如果一個模型只有在 `full` 贏、
`ablated` 就輸回基線，代表它贏的是「重新包裝同一個分數」，不是新訊號。

**護欄（沿用 `src/10_ml_perturbation_prediction/README.md`，非新發明）：** 絕不餵
決策；`unknown != 0`（HistGradientBoostingClassifier 原生吃 NaN；Logistic/
RandomForest 用 median 插補 + 明確缺失指示欄，NaN 類別用 `dummy_na=True` 保留
「未知」這個類別，不是悄悄丟掉或當成某個具體類別）；固定 random_state，
deterministic；輸了老實報輸了；結果只寫進 `../results/`。
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from build_features import CIRCULAR_COLUMNS, LABEL_ADJACENT_COLUMNS, build_features

REPO_ROOT = Path(__file__).resolve().parents[3]
RESULTS_DIR = REPO_ROOT / "src/10_ml_perturbation_prediction/results"
N_SPLITS = 5
# 只有 13 個正類，單一次 5-fold 切分對 AUROC 的估計雜訊很大（一次「幸運」的切分
# 就可能把一個平庸模型捧成「贏家」）。重複 10 次不同切分、報告 mean/std/
# beats_baseline 的次數比例，才是對這麼小的正類數誠實的評估方式——不是為了
# p-hack 到贏，是為了不要被單一次切分的雜訊誤導。
N_REPEATS = 10
RANDOM_STATE = 0
CATEGORICAL_COLUMNS = ["delivery_modality", "polarity", "kinetic_archetype", "avoid_tier", "stimulation_gated"]


def _encode_features(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """One-hot 編碼類別欄（dummy_na=True 保留「未知」為獨立類別，不是丟棄或補值）；
    數值欄原樣保留（NaN 維持 NaN）。"""
    present = [c for c in columns if c in df.columns]
    cat_present = [c for c in present if c in CATEGORICAL_COLUMNS]
    num_present = [c for c in present if c not in CATEGORICAL_COLUMNS]
    parts = [df[num_present]]
    if cat_present:
        parts.append(pd.get_dummies(df[cat_present], dummy_na=True, prefix=cat_present))
    return pd.concat(parts, axis=1)


def _fit_predict_one_split(X_tr, X_te, y_tr, model_name: str, seed: int) -> np.ndarray:
    if model_name == "logistic":
        model = Pipeline(steps=[
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=seed)),
        ])
    elif model_name == "random_forest":
        model = Pipeline(steps=[
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("model", RandomForestClassifier(
                n_estimators=300, class_weight="balanced_subsample", random_state=seed, n_jobs=-1)),
        ])
    elif model_name == "hist_gbr":
        # 原生支援 NaN，不插補 -- unknown 保持 unknown，不是 median 填補的推測值
        model = HistGradientBoostingClassifier(
            random_state=seed, max_iter=200, learning_rate=0.05, class_weight="balanced")
    else:
        raise ValueError(model_name)
    model.fit(X_tr, y_tr)
    return model.predict_proba(X_te)[:, 1]


def _repeated_cv_auroc(X: pd.DataFrame, y: np.ndarray, model_name: str) -> Dict:
    """RepeatedStratifiedKFold（N_REPEATS 次不同切分，每次都算一個 out-of-fold AUROC）—
    只有 13 個正類時，單一次切分的 AUROC 估計雜訊很大，重複多次切分、報告
    mean/std/beats_baseline 的次數比例，才不會被一次幸運的切分誤導。"""
    rskf = RepeatedStratifiedKFold(n_splits=N_SPLITS, n_repeats=N_REPEATS, random_state=RANDOM_STATE)
    per_repeat_auroc: List[float] = []
    oof = np.full(len(y), np.nan)
    current_repeat_idx = -1
    for split_idx, (tr_idx, te_idx) in enumerate(rskf.split(X, y)):
        repeat_idx = split_idx // N_SPLITS
        if repeat_idx != current_repeat_idx:
            if current_repeat_idx >= 0:
                per_repeat_auroc.append(float(roc_auc_score(y, oof)))
            oof = np.full(len(y), np.nan)
            current_repeat_idx = repeat_idx
        X_tr, X_te = X.iloc[tr_idx], X.iloc[te_idx]
        oof[te_idx] = _fit_predict_one_split(X_tr, X_te, y[tr_idx], model_name, seed=RANDOM_STATE + repeat_idx)
    per_repeat_auroc.append(float(roc_auc_score(y, oof)))

    arr = np.asarray(per_repeat_auroc)
    return {
        "auroc_mean": float(arr.mean()),
        "auroc_std": float(arr.std()),
        "auroc_per_repeat": per_repeat_auroc,
        "n_repeats": N_REPEATS,
    }


def evaluate_feature_set(df: pd.DataFrame, feature_columns: List[str], set_name: str) -> Dict:
    y = (df["truth_class"] == "positive").astype(int).to_numpy()
    X = _encode_features(df, feature_columns)

    # 100%-missing 欄位（已知的 n_donors，見 human_validation_protocol.md OF-4）在整批資料裡
    # 沒有任何一格觀測值，不是「這個模型没學到」而是「這個欄位不存在可學的訊號」——連
    # HistGradientBoostingClassifier 原生 NaN 支援都會在 binning 階段對全 NaN 欄崩潰。
    # 誠實地整批排除（不是插補出一個假訊號），並在報告裡列出被排除的欄位。
    all_missing = [c for c in X.columns if X[c].isna().all()]
    if all_missing:
        print(f"  [{set_name}] 排除 100%-missing 欄位（無可學訊號）: {all_missing}")
        X = X.drop(columns=all_missing)

    baseline_auroc = float(roc_auc_score(y, df["ctx_specific_de"].to_numpy()))

    models: Dict[str, Dict] = {}
    for model_name in ["logistic", "random_forest", "hist_gbr"]:
        cv = _repeated_cv_auroc(X, y, model_name)
        n_wins = sum(1 for a in cv["auroc_per_repeat"] if a > baseline_auroc)
        models[model_name] = {
            **cv,
            "beats_baseline_on_mean": bool(cv["auroc_mean"] > baseline_auroc),
            "n_repeats_beating_baseline": n_wins,
            "win_rate": n_wins / cv["n_repeats"],
        }

    return {
        "feature_set": set_name,
        "n_features": int(X.shape[1]),
        "feature_columns": list(X.columns),
        "dropped_all_missing_columns": all_missing,
        "n_genes": int(len(df)),
        "n_positive": int(y.sum()),
        "n_negative_or_rest": int((~y.astype(bool)).sum()),
        "baseline_auroc_recomputed": baseline_auroc,
        "models": models,
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df = build_features()

    start = time.time()
    full_cols = CIRCULAR_COLUMNS + LABEL_ADJACENT_COLUMNS + [
        c for c in df.columns if c not in ["gene", "truth_class", "ctx_rank", "ctx_specific_de"]
        + CIRCULAR_COLUMNS + LABEL_ADJACENT_COLUMNS
    ]
    ablated_cols = [c for c in full_cols if c not in CIRCULAR_COLUMNS + LABEL_ADJACENT_COLUMNS]

    full_report = evaluate_feature_set(df, full_cols, "full (includes CIRCULAR + LABEL_ADJACENT)")
    ablated_report = evaluate_feature_set(df, ablated_cols, "ablated (excludes CIRCULAR + LABEL_ADJACENT)")

    print(f"\n=== full === baseline AUROC(recomputed)={full_report['baseline_auroc_recomputed']:.4f}  "
          f"({N_REPEATS}x repeated {N_SPLITS}-fold CV)")
    for name, m in full_report["models"].items():
        print(f"  {name:14s} AUROC={m['auroc_mean']:.4f}±{m['auroc_std']:.4f}  "
              f"win_rate={m['n_repeats_beating_baseline']}/{m['n_repeats']}")

    print(f"\n=== ablated === baseline AUROC(recomputed)={ablated_report['baseline_auroc_recomputed']:.4f}")
    for name, m in ablated_report["models"].items():
        print(f"  {name:14s} AUROC={m['auroc_mean']:.4f}±{m['auroc_std']:.4f}  "
              f"win_rate={m['n_repeats_beating_baseline']}/{m['n_repeats']}")
        full_won = full_report["models"][name]["beats_baseline_on_mean"]
        ablated_won = m["beats_baseline_on_mean"]
        if ablated_won:
            verdict = "贏了且在 ablated 依然贏（真訊號，非 leakage 假象）"
        elif full_won:
            verdict = "未在 ablated 存活（full 贏是 leakage 假象）"
        else:
            verdict = "未贏基線（誠實負面）"
        print(f"    -> {verdict}")

    out = {
        "method": "known-regulator classifier: LogisticRegression / RandomForest / HistGradientBoosting "
                   "vs the existing simple ctx_specific_de ranking (AUROC 0.85)",
        "task": "y = 1 if truth_class=='positive' (13 genes) else 0 (1,211 'rest' + 1 'negative' = 1,212) "
                "-- same operative definition as the existing baseline ('positives vs rest'), not a "
                "balanced classification task (only 1 confirmed negative survives the n>=200 cell gate).",
        "cv": f"RepeatedStratifiedKFold n_splits={N_SPLITS} x n_repeats={N_REPEATS}, "
              f"random_state={RANDOM_STATE}; reports auroc_mean/std across repeats and win_rate "
              f"(fraction of repeats beating the recomputed baseline) -- with only 13 positives, a "
              f"single split's AUROC is too noisy to trust on its own.",
        "leakage_note": "CIRCULAR_COLUMNS are literal inputs to the ctx_specific_de formula (verified via "
                         "CD3E's real numbers); LABEL_ADJACENT_COLUMNS (n_concept_modules) correlates with "
                         "how the canonical positive list was curated, not with the score. A model that "
                         "only wins with these included and loses once they're removed is reproducing the "
                         "baseline in disguise, not learning new signal -- see 'ablated' results for the "
                         "honest answer.",
        "elapsed_seconds": time.time() - start,
        "full": full_report,
        "ablated": ablated_report,
    }
    out_path = RESULTS_DIR / "known_regulator_classifier_benchmark.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\n✅ 報告寫入 {out_path}")


if __name__ == "__main__":
    main()
