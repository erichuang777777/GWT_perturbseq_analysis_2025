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
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC

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
N_PERM = 5000  # 置換檢定的 shuffle 次數(分數固定、不重訓，所以能負擔大 n_perm)
CATEGORICAL_COLUMNS = ["delivery_modality", "polarity", "kinetic_archetype", "avoid_tier", "stimulation_gated"]
# 單一 SAFE 特徵基線:每個都當一個「只用這一欄排序」的 baseline，看多特徵 ML 有沒有贏過
# 自己最好的單一特徵。方向後驗挑選(取 AUROC 較高的方向)—— 這對單一特徵是「樂觀上限」，
# 只會讓「ML 沒加值」的論點更強，不會更弱。
SINGLE_FEATURE_BASELINES = [
    "loeuf", "pli", "positive_control_similarity", "crossdonor_correlation_mean",
    "crossguide_correlation", "guide_signif_ratio", "n_cells_target", "target_baseline_expression",
]


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


def _build_model(model_name: str, seed: int):
    """五個模型:linear tier(logistic / linear_svm)、非參數(knn)、tree ensemble
    (random_forest / hist_gbr)。除 hist_gbr 原生吃 NaN 外,其餘都用
    median 插補 + 明確缺失指示欄(unknown != 0),再標準化。"""
    if model_name == "logistic":
        return Pipeline(steps=[
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=seed)),
        ])
    if model_name == "linear_svm":
        # 線性 SVM;LinearSVC 沒有 predict_proba,用 decision_function 當連續分數(排序任務只需
        # 一個單調分數,不需機率校準)。
        return Pipeline(steps=[
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
            ("model", LinearSVC(class_weight="balanced", max_iter=5000, random_state=seed)),
        ])
    if model_name == "knn":
        return Pipeline(steps=[
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
            ("model", KNeighborsClassifier(n_neighbors=15)),
        ])
    if model_name == "random_forest":
        return Pipeline(steps=[
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("model", RandomForestClassifier(
                n_estimators=300, class_weight="balanced_subsample", random_state=seed, n_jobs=-1)),
        ])
    if model_name == "hist_gbr":
        # 原生支援 NaN，不插補 -- unknown 保持 unknown，不是 median 填補的推測值
        return HistGradientBoostingClassifier(
            random_state=seed, max_iter=200, learning_rate=0.05, class_weight="balanced")
    raise ValueError(model_name)


def _score_test(model, X_te) -> np.ndarray:
    """取連續分數:有 predict_proba 用正類機率,否則用 decision_function(LinearSVC)。"""
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X_te)[:, 1]
    return model.decision_function(X_te)


def _fit_predict_one_split(X_tr, X_te, y_tr, model_name: str, seed: int) -> np.ndarray:
    model = _build_model(model_name, seed)
    model.fit(X_tr, y_tr)
    return _score_test(model, X_te)


MODEL_NAMES = ["logistic", "linear_svm", "knn", "random_forest", "hist_gbr"]


def _ranking_metrics(y: np.ndarray, scores: np.ndarray) -> Dict:
    """對排序任務比 AUROC/AUPRC 更直覺的指標:precision@k、recall@50,以及 13 個正類各自
    的排名(1 = 分數最高)。NaN 分數排到最後(誠實:沒分數不能假裝排前面)。"""
    order = np.argsort(-np.nan_to_num(scores, nan=-np.inf), kind="stable")
    ranked_y = y[order]
    n_pos = int(y.sum())
    out: Dict = {}
    for k in (13, 25, 50):
        out[f"precision_at_{k}"] = float(ranked_y[:k].sum() / k)
    out["recall_at_50"] = float(ranked_y[:50].sum() / n_pos) if n_pos else float("nan")
    # 每個正類的排名(1-indexed)
    rank_of = np.empty(len(y), dtype=int)
    rank_of[order] = np.arange(1, len(y) + 1)
    pos_ranks = sorted(int(r) for r in rank_of[y == 1])
    out["positive_ranks"] = pos_ranks
    out["positive_rank_median"] = float(np.median(pos_ranks)) if pos_ranks else float("nan")
    return out


def _permutation_pvalue(y: np.ndarray, scores: np.ndarray, metric: str, n_perm: int, rng) -> Dict:
    """置換檢定:固定分數向量,把標籤 shuffle n_perm 次,算 null 分佈與經驗 p-value。
    回答「這個排序在只有 13 個正類下,是否顯著優於隨機標籤」——分數固定所以不需重訓,便宜。
    p = (1 + #{null >= observed}) / (n_perm + 1)。"""
    score_fn = average_precision_score if metric == "auprc" else roc_auc_score
    s = np.nan_to_num(scores, nan=np.nanmin(scores) - 1.0 if np.isfinite(np.nanmin(scores)) else 0.0)
    observed = float(score_fn(y, s))
    y_perm = y.copy()
    null = np.empty(n_perm)
    for i in range(n_perm):
        rng.shuffle(y_perm)
        null[i] = score_fn(y_perm, s)
    pval = float((1 + int(np.sum(null >= observed))) / (n_perm + 1))
    return {
        "observed": observed,
        "null_mean": float(null.mean()),
        "null_p95": float(np.percentile(null, 95)),
        "p_value": pval,
        "n_perm": n_perm,
    }


def _repeated_cv_metrics(X: pd.DataFrame, y: np.ndarray, model_name: str) -> Dict:
    """RepeatedStratifiedKFold（N_REPEATS 次不同切分，每次都算一個 out-of-fold 分數）—
    只有 13 個正類時，單一次切分的估計雜訊很大，重複多次切分、報告 mean/std 才不會被
    一次幸運的切分誤導。**同時算 AUROC 與 AUPRC**：13/1225≈1% 的極端不平衡下，AUROC
    會過度樂觀（1,212 個負類讓 FPR 分母很大），AUPRC（對稀有正類敏感、直接懲罰
    「排很高卻不是正類」）才是這種 prevalence 下該看的主指標。"""
    rskf = RepeatedStratifiedKFold(n_splits=N_SPLITS, n_repeats=N_REPEATS, random_state=RANDOM_STATE)
    per_repeat_auroc: List[float] = []
    per_repeat_auprc: List[float] = []
    # 也累加每個基因跨 repeat 的 OOF 分數平均 -- 給 precision@k / 置換檢定用一個穩定的
    # 單一分數向量(每個基因在每個 repeat 被當 test 剛好一次)。
    oof_sum = np.zeros(len(y))
    oof_count = np.zeros(len(y))
    oof = np.full(len(y), np.nan)
    current_repeat_idx = -1
    for split_idx, (tr_idx, te_idx) in enumerate(rskf.split(X, y)):
        repeat_idx = split_idx // N_SPLITS
        if repeat_idx != current_repeat_idx:
            if current_repeat_idx >= 0:
                per_repeat_auroc.append(float(roc_auc_score(y, oof)))
                per_repeat_auprc.append(float(average_precision_score(y, oof)))
            oof = np.full(len(y), np.nan)
            current_repeat_idx = repeat_idx
        X_tr, X_te = X.iloc[tr_idx], X.iloc[te_idx]
        preds = _fit_predict_one_split(X_tr, X_te, y[tr_idx], model_name, seed=RANDOM_STATE + repeat_idx)
        oof[te_idx] = preds
        oof_sum[te_idx] += preds
        oof_count[te_idx] += 1
    per_repeat_auroc.append(float(roc_auc_score(y, oof)))
    per_repeat_auprc.append(float(average_precision_score(y, oof)))

    mean_oof = np.divide(oof_sum, oof_count, out=np.full(len(y), np.nan), where=oof_count > 0)
    roc = np.asarray(per_repeat_auroc)
    prc = np.asarray(per_repeat_auprc)
    return {
        "mean_oof": mean_oof,
        "auroc_mean": float(roc.mean()),
        "auroc_std": float(roc.std()),
        "auroc_per_repeat": per_repeat_auroc,
        "auprc_mean": float(prc.mean()),
        "auprc_std": float(prc.std()),
        "auprc_per_repeat": per_repeat_auprc,
        "n_repeats": N_REPEATS,
    }


def _single_feature_baselines(df: pd.DataFrame, y: np.ndarray, rng) -> Dict:
    """每個 SAFE 特徵單獨當排序基線(方向後驗挑選 = 樂觀上限),加一個 random dummy。
    看多特徵 ML 有沒有贏過自己最好的單一特徵、以及是否任何單一特徵能贏 ctx_specific_de。"""
    out: Dict[str, Dict] = {}
    for feat in SINGLE_FEATURE_BASELINES:
        if feat not in df.columns:
            continue
        raw = df[feat].to_numpy(dtype=float)
        if np.isnan(raw).all():
            continue
        # 兩個方向都算 AUROC，取較高者(單一特徵的樂觀上限)
        a_pos = float(roc_auc_score(y, np.nan_to_num(raw, nan=np.nanmin(raw) - 1)))
        direction = 1 if a_pos >= 0.5 else -1
        scores = direction * raw
        out[feat] = {
            "direction": "higher_is_positive" if direction == 1 else "lower_is_positive",
            "auroc": float(roc_auc_score(y, np.nan_to_num(scores, nan=np.nanmin(scores) - 1))),
            "auprc": float(average_precision_score(y, np.nan_to_num(scores, nan=np.nanmin(scores) - 1))),
            **_ranking_metrics(y, scores),
        }
    # random dummy：確認 AUPRC 的無資訊線經驗上 ≈ prevalence、AUROC ≈ 0.5
    dummy = rng.random(len(y))
    out["_random_dummy"] = {
        "direction": "random",
        "auroc": float(roc_auc_score(y, dummy)),
        "auprc": float(average_precision_score(y, dummy)),
        **_ranking_metrics(y, dummy),
    }
    return out


def evaluate_feature_set(df: pd.DataFrame, feature_columns: List[str], set_name: str,
                         with_deep_analysis: bool = False) -> Dict:
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

    baseline_score = df["ctx_specific_de"].to_numpy()
    baseline_auroc = float(roc_auc_score(y, baseline_score))
    baseline_auprc = float(average_precision_score(y, baseline_score))
    # AUPRC 的「無資訊」參考線 = 正類 prevalence（一個隨機分類器的 AUPRC≈prevalence）。
    # AUROC 的無資訊參考線恆為 0.5，跟 prevalence 無關——這正是為什麼在 1% 正類時
    # 一定要同時看 AUPRC：它把「稀有」這件事編進參考線裡。
    prevalence = float(y.mean())
    rng = np.random.default_rng(RANDOM_STATE)

    models: Dict[str, Dict] = {}
    for model_name in MODEL_NAMES:
        cv = _repeated_cv_metrics(X, y, model_name)
        mean_oof = cv.pop("mean_oof")  # 大向量,不進 JSON;只用來算 ranking / 置換
        roc_wins = sum(1 for a in cv["auroc_per_repeat"] if a > baseline_auroc)
        prc_wins = sum(1 for a in cv["auprc_per_repeat"] if a > baseline_auprc)
        entry = {
            **cv,
            "beats_baseline_auroc_on_mean": bool(cv["auroc_mean"] > baseline_auroc),
            "auroc_win_rate": roc_wins / cv["n_repeats"],
            "beats_baseline_auprc_on_mean": bool(cv["auprc_mean"] > baseline_auprc),
            "auprc_win_rate": prc_wins / cv["n_repeats"],
        }
        if with_deep_analysis:
            entry["ranking_on_mean_oof"] = _ranking_metrics(y, mean_oof)
            entry["permutation_auroc"] = _permutation_pvalue(y, mean_oof, "auroc", N_PERM, rng)
            entry["permutation_auprc"] = _permutation_pvalue(y, mean_oof, "auprc", N_PERM, rng)
        models[model_name] = entry

    report = {
        "feature_set": set_name,
        "n_features": int(X.shape[1]),
        "feature_columns": list(X.columns),
        "dropped_all_missing_columns": all_missing,
        "n_genes": int(len(df)),
        "n_positive": int(y.sum()),
        "n_negative_or_rest": int((~y.astype(bool)).sum()),
        "positive_prevalence": prevalence,
        "baseline_auroc_recomputed": baseline_auroc,
        "baseline_auprc_recomputed": baseline_auprc,
        "auprc_no_skill_reference": prevalence,
        "models": models,
    }
    if with_deep_analysis:
        # 基線自己也做 ranking + 置換檢定:回答「連 ctx_specific_de 0.474 在 13 個正類下
        # 是否顯著優於隨機標籤」——這是所有結論的統計把握度地基。
        report["baseline_ranking"] = _ranking_metrics(y, baseline_score)
        report["baseline_permutation_auroc"] = _permutation_pvalue(y, baseline_score, "auroc", N_PERM, rng)
        report["baseline_permutation_auprc"] = _permutation_pvalue(y, baseline_score, "auprc", N_PERM, rng)
        report["single_feature_baselines"] = _single_feature_baselines(df, y, rng)
    return report


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
    # ablated 才是誠實答案,所以深度分析(precision@k、置換檢定、單一特徵基線)只跑在它上面。
    ablated_report = evaluate_feature_set(
        df, ablated_cols, "ablated (excludes CIRCULAR + LABEL_ADJACENT)", with_deep_analysis=True)

    def _print_report(report: Dict, tag: str) -> None:
        print(f"\n=== {tag} === ({N_REPEATS}x repeated {N_SPLITS}-fold CV)  "
              f"prevalence={report['positive_prevalence']:.4f}")
        print(f"  baseline (ctx_specific_de ranking): "
              f"AUROC={report['baseline_auroc_recomputed']:.4f}  AUPRC={report['baseline_auprc_recomputed']:.4f}  "
              f"(AUPRC no-skill≈{report['auprc_no_skill_reference']:.4f})")
        for name, m in report["models"].items():
            print(f"  {name:14s} AUROC={m['auroc_mean']:.4f}±{m['auroc_std']:.4f} "
                  f"(win {int(m['auroc_win_rate']*m['n_repeats'])}/{m['n_repeats']})   "
                  f"AUPRC={m['auprc_mean']:.4f}±{m['auprc_std']:.4f} "
                  f"(win {int(m['auprc_win_rate']*m['n_repeats'])}/{m['n_repeats']})")

    _print_report(full_report, "full")
    _print_report(ablated_report, "ablated")

    # 誠實裁決現在需要兩個指標「都」在 ablated 存活才算真訊號——AUROC 贏但 AUPRC 沒贏，
    # 代表模型只是在稀有正類的排序尾端稍微好一點，對「真正把正類推上前排」沒有幫助。
    print("\n=== 裁決（AUROC 與 AUPRC 都要在 ablated 存活才算真訊號）===")
    for name, m in ablated_report["models"].items():
        roc_ok = m["beats_baseline_auroc_on_mean"]
        prc_ok = m["beats_baseline_auprc_on_mean"]
        full_roc = full_report["models"][name]["beats_baseline_auroc_on_mean"]
        if roc_ok and prc_ok:
            verdict = "✅ AUROC+AUPRC 都在 ablated 贏基線（最強的真訊號）"
        elif roc_ok and not prc_ok:
            verdict = "⚠️ 只有 AUROC 贏、AUPRC 沒贏（排序尾端略好，但沒真的把正類推上前排——AUPRC 才誠實）"
        elif full_roc and not roc_ok:
            verdict = "❌ 未在 ablated 存活（full 贏是 leakage 假象）"
        else:
            verdict = "❌ 未贏基線（誠實負面）"
        print(f"  {name:14s} -> {verdict}")

    # --- 深度分析(只在 ablated)---
    b_rank = ablated_report["baseline_ranking"]
    b_perm_roc = ablated_report["baseline_permutation_auroc"]
    b_perm_prc = ablated_report["baseline_permutation_auprc"]
    print(f"\n=== 置換檢定(n_perm={N_PERM};是否顯著優於隨機標籤，n=13 正類的統計把握度地基）===")
    print(f"  baseline: AUROC p={b_perm_roc['p_value']:.4g} (null≈{b_perm_roc['null_mean']:.3f})   "
          f"AUPRC p={b_perm_prc['p_value']:.4g} (null≈{b_perm_prc['null_mean']:.3f})")
    for name, m in ablated_report["models"].items():
        pr, pp = m["permutation_auroc"], m["permutation_auprc"]
        print(f"  {name:14s} AUROC p={pr['p_value']:.4g}   AUPRC p={pp['p_value']:.4g}")

    print("\n=== Precision@k / 正類排名（ablated；k=13 是正類總數）===")
    print(f"  baseline: P@13={b_rank['precision_at_13']:.3f}  P@25={b_rank['precision_at_25']:.3f}  "
          f"P@50={b_rank['precision_at_50']:.3f}  recall@50={b_rank['recall_at_50']:.3f}  "
          f"正類中位排名={b_rank['positive_rank_median']:.0f}")
    for name, m in ablated_report["models"].items():
        r = m["ranking_on_mean_oof"]
        print(f"  {name:14s} P@13={r['precision_at_13']:.3f}  P@25={r['precision_at_25']:.3f}  "
              f"P@50={r['precision_at_50']:.3f}  recall@50={r['recall_at_50']:.3f}  "
              f"正類中位排名={r['positive_rank_median']:.0f}")

    print("\n=== 單一 SAFE 特徵基線 + dummy（方向後驗挑選=樂觀上限；ablated）===")
    for feat, m in ablated_report["single_feature_baselines"].items():
        print(f"  {feat:28s} AUROC={m['auroc']:.3f}  AUPRC={m['auprc']:.3f}  "
              f"P@13={m['precision_at_13']:.3f}  ({m['direction']})")

    out = {
        "method": "known-regulator classifier: LogisticRegression / LinearSVC / kNN / RandomForest / "
                   "HistGradientBoosting vs the existing simple ctx_specific_de ranking (AUROC 0.85). "
                   "Deep analysis on the ablated set adds: AUPRC (prevalence-appropriate for 1% positives), "
                   "permutation null p-values (n_perm=5000, statistical power with only 13 positives), "
                   "precision@k + positive-rank distribution, and single-SAFE-feature + random-dummy baselines.",
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
