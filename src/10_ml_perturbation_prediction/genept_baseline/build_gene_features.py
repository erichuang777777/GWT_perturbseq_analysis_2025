#!/usr/bin/env python3
"""
建立 GenePT 風格基線所需的兩個矩陣，快取進 ../data/（gitignored，可重建）：

1. **gene_embeddings.npz** —— 每個被擾動基因（target）的 GenePT ada-002
   文字嵌入（1536 維，來自 honicky/genept-composable-embeddings，複現
   Chen & Zou 2023 原始 GenePT 論文的嵌入，不需要 OpenAI API key），
   PCA 降到 N_COMPONENTS 維（穩定 ridge regression、也是文獻常見做法）。
2. **response_matrix_<condition>.npz** —— dense 的 target × measured-gene
   log_fc 矩陣（不是只有顯著的——用本地 GWCD4i.DE_stats.h5ad 的完整
   layers，因為要學「連續的下游表現變化 profile」，不能把未達顯著性的
   訊號也砍成 0，那樣既損失資訊也違反 repo 的 `unknown != 0` 原則；這裡
   是「量測到但不顯著」= 真實的小/零效應，不是「未量測」，所以用真值，
   不是 unknown）。

兩者用基因 symbol 對齊（GenePT 的 index 就是 symbol，h5ad 的
target_contrast_gene_name / var.gene_name 也是 symbol）。
"""

import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

REPO_ROOT = Path(__file__).resolve().parents[3]
H5AD_PATH = REPO_ROOT / "data" / "marson2025_data" / "GWCD4i.DE_stats.h5ad"
GENEPT_PATH = REPO_ROOT / "src/10_ml_perturbation_prediction/data/genept_ada_text_embeddings.parquet"
OUT_DIR = REPO_ROOT / "src/10_ml_perturbation_prediction/data"
N_COMPONENTS = 128
CONDITIONS = ["Rest", "Stim8hr", "Stim48hr"]


def build_embeddings():
    print(f"讀取 GenePT 嵌入 {GENEPT_PATH} ...")
    genept = pd.read_parquet(GENEPT_PATH)
    print(f"  原始: {genept.shape[0]} 基因 × {genept.shape[1]} 維")

    pca = PCA(n_components=N_COMPONENTS, random_state=0)
    reduced = pca.fit_transform(genept.values)
    explained = pca.explained_variance_ratio_.sum()
    print(f"  PCA → {N_COMPONENTS} 維，保留 {explained:.1%} 變異量")

    np.savez_compressed(
        OUT_DIR / "gene_embeddings_pca.npz",
        gene_symbols=genept.index.to_numpy(),
        embeddings=reduced.astype(np.float32),
    )
    print(f"  ✅ 寫出 {OUT_DIR / 'gene_embeddings_pca.npz'}")
    return set(genept.index)


def build_response_matrices(embedded_genes):
    if not H5AD_PATH.exists():
        sys.exit(
            f"找不到 {H5AD_PATH}——本地快取的原始 DE_stats.h5ad 不在。"
            "重新用 src/3_DE_analysis/data_acquisition/download_precomputed_DE.py 下載。"
        )

    with h5py.File(H5AD_PATH, "r") as f:
        obs_target_gene = f["obs"]["target_contrast_gene_name"]["categories"][:].astype(str)
        obs_target_gene_codes = f["obs"]["target_contrast_gene_name"]["codes"][:]
        obs_condition = f["obs"]["culture_condition"]["categories"][:].astype(str)
        obs_condition_codes = f["obs"]["culture_condition"]["codes"][:]

        var_gene_name = f["var"]["gene_name"][:]
        if var_gene_name.dtype.kind in ("S", "O"):
            var_gene_name = np.array([g.decode() if isinstance(g, bytes) else g for g in var_gene_name])

        target_names_all = obs_target_gene[obs_target_gene_codes]
        condition_all = obs_condition[obs_condition_codes]

        # 只保留下游基因欄位也在 GenePT 嵌入裡的（response 的維度需要固定、
        # 跨 target 一致，才能訓練共用的 multi-output regressor）
        gene_mask = np.array([g in embedded_genes for g in var_gene_name])
        n_response_genes = gene_mask.sum()
        print(f"下游基因欄位：{len(var_gene_name)} 個測量基因中，{n_response_genes} 個在 GenePT 嵌入詞彙內")
        response_gene_names = var_gene_name[gene_mask]
        col_idx = np.where(gene_mask)[0]

        for condition in CONDITIONS:
            cond_mask = condition_all == condition
            target_mask = cond_mask & np.array([g in embedded_genes for g in target_names_all])
            row_idx = np.where(target_mask)[0]
            print(f"[{condition}] {len(row_idx)} 個標的（且標的本身也在 GenePT 詞彙內）")

            if len(row_idx) == 0:
                continue

            log_fc = f["layers"]["log_fc"][row_idx, :][:, col_idx]

            np.savez_compressed(
                OUT_DIR / f"response_matrix_{condition}.npz",
                target_genes=target_names_all[row_idx],
                response_genes=response_gene_names,
                log_fc=log_fc.astype(np.float32),
            )
            print(f"  ✅ 寫出 response_matrix_{condition}.npz: {log_fc.shape}")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    embedded_genes = build_embeddings()
    build_response_matrices(embedded_genes)


if __name__ == "__main__":
    main()
