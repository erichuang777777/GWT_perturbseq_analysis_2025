#!/usr/bin/env python3
"""
T1-rework：用真實 DE 特徵（而非 GenePT 外部文字嵌入）重做「用被擾動基因的特徵預測
其下游反應 profile」這個任務,快取進 ../data/(gitignored,可重建)。

**跟既有 GenePT 基線的差異（唯一的變數）：** `genept_baseline/` 用的 X 是跟這份資料
完全無關的外部文字嵌入（PCA-128）。這裡的 X 換成**被擾動基因自己在同一個
culture_condition 下的真實實驗量測值**——`n_cells_target`、`n_guides`、
`crossdonor_correlation_mean/min`、`crossguide_correlation`、`guide_signif_ratio`、
`guide_fdr_min`、`guide_t_abs_median`、`positive_control_similarity`、
`target_baseline_expression`（全部來自 `target_cards.csv`）。**刻意排除**
`n_total_de_genes`／`n_up_genes`／`n_down_genes`／`ontarget_effect_size` 這些
DE 幅度摘要——那些本質上就是要預測的 response profile 的摘要統計，拿來當特徵
會是同一種 leakage（呼應 `known_regulator_classifier/build_features.py` 的
CIRCULAR_COLUMNS 稽核紀律，這裡是同一個原則的另一個應用場景）。任務結構、
KFold-by-target-within-condition、mean-profile 基線比較，都跟 `genept_baseline/`
完全一致，只換 X 的來源——這樣「real features vs GenePT embedding」才是唯一變數,
其他都對照組不變。

**Y（response profile）的資料來源限制,誠實記錄：** 本環境沒有 `GWCD4i.DE_stats.h5ad`
（密集矩陣,~15.6GB,S3-only,未進 git,見 `docs/mvp-research/TASK_A_GB10_HANDOFF.md`）,
所以無法比照 `genept_baseline/` 用完整密集 log_fc 矩陣。改用已提交進 git 的
`metadata/suppl_tables/full_signed_DE/`(只收錄 adj_p_value<0.1 的顯著配對,
2,056,424 列)。Y 限制在 **landmark 基因集**(全資料中最常被列為顯著下游基因的
前 N_LANDMARK 個下游基因,確保矩陣夠密),對每個 (target, condition, landmark 基因)：
若該組合在 full_signed_DE 裡有顯著紀錄,Y = 真實 log_fc；否則 Y = 0.0
——**這個 0 不是「未量測」,是「該基因在這個擾動下沒有偵測到 adj_p<0.1 的顯著變化」,
是一個誠實的、有明確定義的 floor,不是 unknown != 0 原則要防的那種「缺失被悄悄
當成安全值」**（跟 `genept_baseline/build_gene_features.py` 用完整密集矩陣時
「量測到但不顯著 = 真值,不是 unknown」的論述是同一個原則,只是這裡的資料來源
本身就只保留顯著配對,沒有密集矩陣可用,所以 0-floor 是本環境能做到的最接近版本,
比密集矩陣更粗——這個限制在 README 明確揭露,不是隱藏)。
"""

from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
SIGNED_DE_DIR = REPO_ROOT / "metadata/suppl_tables/full_signed_DE"
CARDS_PATH = REPO_ROOT / "sources/target_tool_cache/a792d68c-7adc-46a6-964a-35770e5adbde/target_cards.csv"
OUT_DIR = REPO_ROOT / "src/10_ml_perturbation_prediction/data"
CONDITIONS = ["Rest", "Stim8hr", "Stim48hr"]
N_LANDMARK = 500  # 最常見顯著下游基因數，跟 genept_baseline 的 ~10,185 個測量基因量級不同
                   # 級（本表只收錄顯著配對，全量下游基因矩陣會太稀疏而不可學），已在
                   # README 揭露這個規模差異。

# 被擾動基因「自身」的真實實驗特徵（同一 condition 下）——實驗設計/robustness/獨立
# 相似度，刻意不含任何 DE 幅度摘要（n_total_de_genes 等，那是 response 本身的摘要，
# 用來當特徵是 leakage，同 T2 的 CIRCULAR_COLUMNS 稽核原則）。
FEATURE_COLUMNS = [
    "n_cells_target", "n_guides",
    "crossdonor_correlation_mean", "crossdonor_correlation_min", "crossguide_correlation",
    "guide_signif_ratio", "guide_fdr_min", "guide_t_abs_median",
    "positive_control_similarity", "target_baseline_expression",
]


def _load_signed_de() -> pd.DataFrame:
    files = sorted(glob.glob(str(SIGNED_DE_DIR / "part-*.parquet")))
    if not files:
        raise SystemExit(f"找不到 {SIGNED_DE_DIR}/part-*.parquet -- Task A 的萃取產出未在此 checkout")
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sde = _load_signed_de()
    cards = pd.read_csv(CARDS_PATH, low_memory=False)

    landmark_genes = sde["downstream_gene"].value_counts().head(N_LANDMARK).index.to_numpy()
    print(f"landmark 下游基因（前 {N_LANDMARK} 個最常顯著）: {landmark_genes[:5].tolist()} ...")

    landmark_set = set(landmark_genes)
    sde_landmark = sde[sde["downstream_gene"].isin(landmark_set)]

    for condition in CONDITIONS:
        cond_cards = cards[cards["condition"] == condition].set_index("target")
        cond_sde = sde_landmark[sde_landmark["culture_condition"] == condition]

        # 只保留在這個 condition 下有真實特徵可用的標的（X 的存在性條件，不含 Y 是否
        # 有顯著命中——0 是合法的 Y 值，不能拿來篩掉標的，那樣才不會系統性排除
        # 「這個擾動沒有下游顯著效應」這個誠實的真值）
        eligible_targets = [t for t in cond_cards.index if cond_cards.loc[t, FEATURE_COLUMNS].notna().any()]
        eligible_targets = sorted(set(eligible_targets))
        n = len(eligible_targets)
        print(f"[{condition}] {n} 個標的（在此 condition 下至少有 1 個真實特徵非 NaN）")

        X = cond_cards.loc[eligible_targets, FEATURE_COLUMNS].to_numpy(dtype=float)

        target_to_row = {t: i for i, t in enumerate(eligible_targets)}
        landmark_to_col = {g: j for j, g in enumerate(landmark_genes)}
        Y = np.zeros((n, N_LANDMARK), dtype=np.float32)  # 0.0 = 未達顯著（見上方 docstring 的誠實揭露）
        hits = cond_sde[cond_sde["target_gene"].isin(target_to_row)]
        for tgt, gene, lfc in zip(hits["target_gene"], hits["downstream_gene"], hits["log_fc"]):
            Y[target_to_row[tgt], landmark_to_col[gene]] = lfc

        n_nonzero_rows = int((Y != 0).any(axis=1).sum())
        print(f"  Y: {Y.shape}, {n_nonzero_rows}/{n} 列至少有 1 個非零(顯著)下游基因")

        np.savez_compressed(
            OUT_DIR / f"real_features_response_{condition}.npz",
            target_genes=np.array(eligible_targets),
            feature_columns=np.array(FEATURE_COLUMNS),
            landmark_genes=landmark_genes,
            X=X.astype(np.float32),
            Y=Y,
        )
        print(f"  ✅ 寫出 real_features_response_{condition}.npz")


if __name__ == "__main__":
    build()
