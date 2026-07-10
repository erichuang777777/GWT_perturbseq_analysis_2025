#!/usr/bin/env python3
"""
用官方 `cell-gears` 套件訓練 GEARS 模型：GO 共同註解相似度圖 +
co-expression 相似度圖 + GNN，預測未見過基因擾動後的完整表現量 profile。

**評估設計（跟 `../genept_baseline/train_baseline.py` 對齊，才能誠實比較）：**
- `split='simulation_single'`：held-out 的基因在訓練時完全沒被當成擾動看過
  （zero-shot），對應 GenePT 基線同樣「沒看過這個基因的擾動」的設定。
- 官方 `gears.inference.compute_metrics` 給兩個標準指標：
  `pearson`（全部測量基因）、`pearson_de`（只看該擾動的顯著差異表現基因）。
- **額外算一個誠實的均值基線**（GEARS 官方 codebase 不包含這個對照）：
  用訓練集所有擾動的平均 post-perturbation profile 當預測值，跟
  GEARS 模型的 pearson 一起報告——這正是 2025-2026 文獻
  （Ahlmann-Eltze et al.）反覆强调必須放進來的對照組。

CPU-only（見 `../README.md`/`gears_model/README.md` 的說明），epochs 刻意
先設小（見 EPOCHS）做第一輪誠實驗證，不代表模型已充分收斂——若要追求
更高分數需要更多 epoch/調參，但那是下一步，不在本次「誠實跑一次基準」
的範圍內。
"""

import json
import time
from pathlib import Path

import numpy as np
import torch
from scipy.stats import pearsonr

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "src/10_ml_perturbation_prediction/data"
RESULTS_DIR = REPO_ROOT / "src/10_ml_perturbation_prediction/results"
GEARS_DATA_H5AD = DATA_DIR / "gears_ready_Rest.h5ad"
PERT_DATA_CACHE = DATA_DIR / "gears_pert_data_cache"
EPOCHS = 10
SEED = 1
TRAIN_GENE_SET_SIZE = 0.75


def main():
    from gears import PertData, GEARS
    from gears.inference import evaluate, compute_metrics

    if not GEARS_DATA_H5AD.exists():
        raise SystemExit(f"找不到 {GEARS_DATA_H5AD}，請先跑 build_gears_dataset.py")

    PERT_DATA_CACHE.mkdir(parents=True, exist_ok=True)

    print(f"讀取 {GEARS_DATA_H5AD} ...")
    import anndata as ad
    adata = ad.read_h5ad(GEARS_DATA_H5AD)
    print(f"obs={adata.n_obs}, var={adata.n_vars}, 唯一 condition={adata.obs['condition'].nunique()}")

    pert_data = PertData(str(PERT_DATA_CACHE))
    pert_data.new_data_process(dataset_name="cd4i_rest", adata=adata)

    print("準備 simulation_single（zero-shot 未見基因）split ...")
    pert_data.prepare_split(split="simulation_single", seed=SEED, train_gene_set_size=TRAIN_GENE_SET_SIZE)
    pert_data.get_dataloader(batch_size=32, test_batch_size=128)

    print("初始化 GEARS 模型（CPU）...")
    gears_model = GEARS(pert_data, device="cpu", weight_bias_track=False)
    gears_model.model_initialize(hidden_size=64)

    print(f"訓練 {EPOCHS} epochs ...")
    start = time.time()
    gears_model.train(epochs=EPOCHS, lr=1e-3)
    train_elapsed = time.time() - start
    print(f"訓練完成，用時 {train_elapsed/60:.1f} 分鐘")

    test_loader = pert_data.dataloader["test_loader"]
    results = evaluate(test_loader, gears_model.best_model, False, "cpu")
    metrics, metrics_pert = compute_metrics(results)

    # 誠實的均值基線對照（GEARS 官方 codebase 未內建，這裡補上）
    train_loader = pert_data.dataloader["train_loader"]
    train_truth = []
    for batch in train_loader:
        train_truth.append(batch.y.numpy())
    train_mean_profile = np.concatenate(train_truth, axis=0).mean(axis=0)

    baseline_corrs = []
    for pert in np.unique(results["pert_cat"]):
        idx = np.where(results["pert_cat"] == pert)[0]
        truth_mean = results["truth"][idx].mean(0)
        r, _ = pearsonr(train_mean_profile, truth_mean)
        baseline_corrs.append(0.0 if np.isnan(r) else r)
    baseline_mean_corr = float(np.mean(baseline_corrs))

    report = {
        "method": "GEARS (cell-gears official package): GO co-annotation graph + co-expression graph + GNN",
        "split": "simulation_single (zero-shot held-out genes)",
        "train_gene_set_size": TRAIN_GENE_SET_SIZE,
        "epochs": EPOCHS,
        "seed": SEED,
        "train_elapsed_minutes": train_elapsed / 60,
        "n_test_perturbations": int(len(np.unique(results["pert_cat"]))),
        "gears_pearson_all_genes": float(metrics["pearson"]),
        "gears_pearson_de_genes": float(metrics["pearson_de"]),
        "mean_baseline_pearson_all_genes": baseline_mean_corr,
        "gears_beats_mean_baseline": bool(metrics["pearson"] > baseline_mean_corr),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "gears_benchmark.json"
    out_path.write_text(json.dumps(report, indent=2))

    print("\n=== 結果 ===")
    print(f"GEARS pearson (全部基因)      : {report['gears_pearson_all_genes']:.4f}")
    print(f"GEARS pearson (顯著差異基因)  : {report['gears_pearson_de_genes']:.4f}")
    print(f"均值基線 pearson (全部基因)   : {report['mean_baseline_pearson_all_genes']:.4f}")
    print(f"GEARS 贏了均值基線嗎？        : {report['gears_beats_mean_baseline']}")
    print(f"\n✅ 報告寫入 {out_path}")


if __name__ == "__main__":
    main()
