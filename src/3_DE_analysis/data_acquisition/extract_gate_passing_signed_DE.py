#!/usr/bin/env python3
"""
從已下載的 GWCD4i.DE_stats.h5ad（原始資料提供者預先算好的 target×gene
帶符號 DE 矩陣，obs=33,983 target×condition、var=10,282 genes）萃取出
「1,235 個通過 MVP 門檻標的」的長表：
    target_gene, target_ensembl_id, culture_condition, downstream_gene,
    downstream_ensembl_id, log_fc, adj_p_value, baseMean, zscore

只保留顯著基因（adj_p_value < 0.1），否則 1235 target × 10282 gene 的
全叉積會有上千萬列，不利放進 repo 且大多是雜訊。

篩選名單來源：docs/mvp-research/pipeline/03_processed/data/gate_passing_targets.csv
（`target_contrast` = Ensembl ID，`passes_gate` 欄位已標好）。

輸出：metadata/suppl_tables/gate_passing_signed_DE.suppl_table.csv
（對應 TASK_A_RUNBOOK_GB10.md「產出後如何放回 repo」一節的建議格式）
"""

import sys
from pathlib import Path

import anndata as ad
import h5py
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
H5AD_PATH = REPO_ROOT / "data" / "marson2025_data" / "GWCD4i.DE_stats.h5ad"
GATE_LIST_PATH = REPO_ROOT / "docs/mvp-research/pipeline/03_processed/data/gate_passing_targets.csv"
OUT_PATH = REPO_ROOT / "metadata/suppl_tables/gate_passing_signed_DE.suppl_table.csv.gz"
FDR_THRESHOLD = 0.1


def main():
    if not H5AD_PATH.exists():
        sys.exit(f"找不到 {H5AD_PATH}，請先完成下載（download_precomputed_DE.py）")

    gate_df = pd.read_csv(GATE_LIST_PATH)
    gate_df = gate_df[gate_df["passes_gate"] == True]  # noqa: E712
    gate_keys = set(gate_df["target_contrast"] + "_" + gate_df["culture_condition"])
    print(f"門檻名單：{gate_df['target_contrast'].nunique()} 個唯一標的，"
          f"{len(gate_keys)} 個 target×condition 列通過 gate")

    print(f"讀取 {H5AD_PATH} (backed 模式，避免整檔載入記憶體)...")
    adata = ad.read_h5ad(H5AD_PATH, backed="r")
    print(f"obs={adata.n_obs}, var={adata.n_vars}")
    print("obs columns:", list(adata.obs.columns))
    print("layers:", list(adata.layers.keys()))

    obs = adata.obs
    obs_keys = obs["target_contrast"].astype(str) + "_" + obs["culture_condition"].astype(str)
    mask = obs_keys.isin(gate_keys).to_numpy()
    row_idx_selected = np.where(mask)[0]  # 遞增排序，符合 h5py fancy-index 的要求
    n_selected = len(row_idx_selected)
    print(f"h5ad 中匹配到門檻名單的列數：{n_selected} / {adata.n_obs}")

    if n_selected == 0:
        sys.exit("沒有任何列匹配到門檻名單，請檢查 target_contrast/culture_condition 的格式是否一致")

    var = adata.var
    gene_ids = var["gene_ids"].to_numpy() if "gene_ids" in var else var.index.to_numpy()
    gene_names = var["gene_name"].to_numpy() if "gene_name" in var else var.index.to_numpy()

    # X 本身是刻意留空的 null dataset（實際資料都在 layers），anndata 的
    # `.to_memory()` 會嘗試一併 subset X 而在此崩潰（"Empty datasets cannot
    # be sliced"）。改用 h5py 直接對需要的 layers 做行索引讀取，繞過此問題，
    # 同時也只讀取篩選後的列（遠小於整個 33983×10282 矩陣）。
    adata.file.close()  # 釋放 anndata 的 backed handle，避免與底下的 h5py handle 衝突
    with h5py.File(H5AD_PATH, "r") as f:
        layers = f["layers"]
        log_fc = layers["log_fc"][row_idx_selected, :]
        adj_p = layers["adj_p_value"][row_idx_selected, :]
        base_mean = layers["baseMean"][row_idx_selected, :]
        zscore = layers["zscore"][row_idx_selected, :]

    sig_mask = adj_p < FDR_THRESHOLD
    row_idx, col_idx = np.where(sig_mask)
    print(f"顯著 (adj_p_value < {FDR_THRESHOLD}) 的 target×gene 配對數：{len(row_idx)}")

    obs_sub = obs.iloc[row_idx_selected].reset_index(drop=True)

    out = pd.DataFrame({
        "target_gene": obs_sub["target_contrast_gene_name"].to_numpy()[row_idx],
        "target_ensembl_id": obs_sub["target_contrast"].to_numpy()[row_idx],
        "culture_condition": obs_sub["culture_condition"].to_numpy()[row_idx],
        "downstream_gene": gene_names[col_idx],
        "downstream_ensembl_id": gene_ids[col_idx],
        "log_fc": log_fc[row_idx, col_idx],
        "adj_p_value": adj_p[row_idx, col_idx],
        "baseMean": base_mean[row_idx, col_idx],
        "zscore": zscore[row_idx, col_idx],
    })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False)
    print(f"\n✅ 寫出 {len(out):,} 列 → {OUT_PATH}")
    print(f"   涵蓋 {out['target_ensembl_id'].nunique()} 個標的 × "
          f"{out['culture_condition'].nunique()} 個條件 × "
          f"{out['downstream_gene'].nunique()} 個下游基因身分")


if __name__ == "__main__":
    main()
