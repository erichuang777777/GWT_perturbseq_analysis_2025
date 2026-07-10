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
import pandas as pd
import torch
from scipy.stats import pearsonr

# 相容性補丁：cell-gears（官方套件，見 model.py/pertdata.py）內部多處寫
# `series[0]` 期待「取第一列」，這在舊版 pandas 對非整數/非連續 index 的
# Series 會自動退回成位置索引；新版 pandas（本環境 3.0.3）已徹底移除這個
# 退回行為，label 0 若不存在就直接 KeyError（例如
# `pertdata.py::create_cell_graph_dataset` 的
# `adata_.obs['condition_name'][0]`，adata_ 是篩選單一 condition 後的子集，
# 其 obs index 幾乎不可能剛好包含整數標籤 0）。只在「整數 key 找不到對應
# label」時才退回 `.iloc`，不影響其他正常的標籤查找，把改動範圍限制到最小。
_orig_series_getitem = pd.Series.__getitem__


def _patched_series_getitem(self, key):
    if isinstance(key, int) and key not in self.index:
        return self.iloc[key]
    return _orig_series_getitem(self, key)


pd.Series.__getitem__ = _patched_series_getitem

# 第四個相容性問題：`gears.py::GEARS.__init__` 直接用布林 pandas Series
# 對 scipy sparse matrix 做索引（`self.adata.X[self.adata.obs.condition ==
# 'ctrl']`）。scipy 的 sparse indexing 內部會對傳入的索引物件呼叫
# `.nonzero()`——舊版 pandas Series 有這個方法（等同
# `np.asarray(self).nonzero()`），新版已移除，導致
# `AttributeError: 'Series' object has no attribute 'nonzero'`。補回這個
# 方法即可，是舊版 pandas API 的直接還原，不影響其他任何行為。
pd.Series.nonzero = lambda self: np.asarray(self).nonzero()

# 第五個相容性問題：`gears/utils.py::get_similarity_network()` 的 GO
# 分支做 `df_jaccard.groupby('target').apply(lambda x: x.nlargest(...))
# .reset_index(drop=True)`。實測（見下）：新版 pandas 的 groupby-apply
# 會把 'target' 這個分組欄位從結果中併掉（因為它現在被視為索引層級的一部
# 分），`reset_index(drop=True)` 又把這個索引直接丟棄而非還原成欄位，最終
# 結果**沒有 'target' 欄位**，導致後面 `GeneSimNetwork.__init__` 呼叫
# `nx.from_pandas_edgelist(..., target='target', ...)` 時 KeyError。
# 舊版 pandas 對同一段程式碼會保留 'target' 欄位。修法：`reset_index()`
# （不加 drop=True）把索引還原成欄位即可，這是兩者唯一差異。
# gears.py 用 `from .utils import get_similarity_network`，所以要 patch
# `gears.gears` 模組裡已經綁定的名字，patch `gears.utils` 沒用（import
# 當下就把參照複製過去了）。
import gears.utils as _gears_utils  # noqa: E402
import gears.gears as _gears_gears  # noqa: E402

_orig_get_similarity_network = _gears_utils.get_similarity_network


def _patched_get_similarity_network(*args, **kwargs):
    if kwargs.get("network_type") == "go":
        import os

        default_pert_graph = kwargs.get("default_pert_graph", True)
        data_path = kwargs["data_path"]
        k = kwargs["k"]
        if default_pert_graph:
            server_path = "https://dataverse.harvard.edu/api/access/datafile/6934319"
            _gears_utils.tar_data_download_wrapper(
                server_path, os.path.join(data_path, "go_essential_all"), data_path
            )
            df_jaccard = pd.read_csv(os.path.join(data_path, "go_essential_all/go_essential_all.csv"))
        else:
            df_jaccard = _gears_utils.make_GO(data_path, kwargs["pert_list"], kwargs["data_name"])

        return (
            df_jaccard.groupby("target")
            .apply(lambda x: x.nlargest(k + 1, ["importance"]))
            .reset_index()  # 這裡是唯一改動：不加 drop=True
        )
    return _orig_get_similarity_network(*args, **kwargs)


_gears_gears.get_similarity_network = _patched_get_similarity_network

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

    # 原本對全量 11,288 個 condition 分組跑 rank_genes_groups_by_cov +
    # get_dropout_non_zero_genes 時，記憶體從 20+GB 壓到 <1GB、swap 吃滿
    # 15GB，被安全監控自動 kill 過。當時試過 skip_calc_de=True 繞開，但
    # 後來發現 GEARS.__init__ 無條件讀取 `adata.uns['non_zeros_gene_idx']`
    # （只有 get_dropout_non_zero_genes 會產生這個 key），skip_calc_de=True
    # 反而讓模型初始化直接 KeyError——這個旗標並非真的可選。真正的解法是
    # build_gears_dataset.py 的 MAX_PERT_GENES 子抽樣（2000 個基因，見該
    # 檔說明）：分組數從 11,288 降到 2,001（~5.6x），同一段計算此時安全，
    # 不需要也不能跳過。
    pert_data = PertData(str(PERT_DATA_CACHE))
    pert_data.new_data_process(dataset_name="cd4i_rest", adata=adata)

    # 第三個 pandas 版本相容性問題：`get_DE_genes()` 會把 `adata.obs`
    # 整表轉成 category dtype（`adata.obs = adata.obs.astype('category')`）。
    # 後面 `prepare_split()` 對 'condition' 欄位做
    # `groupby('split').agg({'condition': lambda x: x})`——lambda 回傳的是
    # 整組原始值（非純量），舊版 pandas 對此就地接受成 object dtype；新版
    # pandas 會嘗試把非純量結果轉回原本的 Categorical dtype，因為轉不回去而
    # 丟 `TypeError: unhashable type: 'Categorical'`。轉成純字串 dtype 可以
    # 讓這段聚合照舊表現（回傳 object dtype 陣列），不觸發這個新版行為，且
    # 不影響任何下游邏輯（`.unique().tolist()` 不管底層 dtype 為何都一樣）。
    pert_data.adata.obs["condition"] = pert_data.adata.obs["condition"].astype(str)

    # 注意：split="simulation_single" 在目前這版 cell-gears 有 bug——
    # `pertdata.py::prepare_split()` 無條件 `adata, subgroup = DS.split_data(...)`，
    # 但 `DataSplitter.split_data()` 對 split_type=='simulation_single' 只回傳
    # 單一個 AnnData（不是 2-tuple），解包會炸「too many values to unpack」
    # （AnnData 被當成可疊代物件硬拆，並非真的有兩個回傳值）。改用
    # split="simulation"：這是官方更常用的主要路徑，同樣支援 zero-shot
    # 未見基因評估，且我們的資料集只有單基因擾動（沒有 combo），對這條路徑
    # 而言只是 combo 相關的中間結果為空，不影響正確性。
    print("準備 simulation（zero-shot 未見基因）split ...")
    pert_data.prepare_split(split="simulation", seed=SEED, train_gene_set_size=TRAIN_GENE_SET_SIZE)
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
        "split": "simulation (zero-shot held-out genes)",
        "train_gene_set_size": TRAIN_GENE_SET_SIZE,
        "epochs": EPOCHS,
        "seed": SEED,
        "train_elapsed_minutes": train_elapsed / 60,
        "n_test_perturbations": int(len(np.unique(results["pert_cat"]))),
        "gears_pearson_all_genes": float(metrics["pearson"]),
        "gears_pearson_de_genes": float(metrics["pearson_de"]),
        "max_pert_genes_subsample": 2000,
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
