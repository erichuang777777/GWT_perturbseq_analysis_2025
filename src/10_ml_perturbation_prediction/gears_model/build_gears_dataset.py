#!/usr/bin/env python3
"""
把 GWCD4i.pseudobulk_merged.h5ad（原始 pseudobulk 表現量，非 DE 統計）轉成
GEARS (`cell-gears` 套件) 期待的格式：

- `.obs['condition']`：控制組（`guide_type == 'non-targeting'`）→ `"ctrl"`；
  單基因擾動 → `"{perturbed_gene_name}+ctrl"`（GEARS 慣例，見
  `gears/utils.py::get_genes_from_perts`）。
- 只取單一 culture_condition（預設 Rest，跟 `../genept_baseline/` 的
  per-condition 評估一致，避免把不同生理情境混在同一個訓練/GO 圖裡）。
- 只保留 `keep_for_DE == True` 的樣本（repo 既有的品質門檻，見
  `data_sharing_readme.md`）。
- **標準化（`sc.pp.normalize_total` + `sc.pp.log1p`）**：原始 `.X` 是
  pseudobulk UMI count 加總（量級可到數萬到數十萬）。GEARS
  的損失函數/預設學習率是照 log-normalize 過的表現量（典型範圍 0-10）調的
  ——第一次沒做標準化直接餵原始 count 進去，訓練 loss 從 10^13 一路衝到
  10^16（明顯發散，不是收斂），這裡補上標準流程的標準化，不是可有可無
  的裝飾。
- **對擾動基因做子抽樣（MAX_PERT_GENES）**：`cell-gears` 官方實作的
  `create_dataset_file()` 會把「每個擾動 × 每個 replicate × 配對的控制組
  細胞」全部建成 PyG Data 物件、存進一個大 dict，最後一次性 `pickle.dump`
  ——不是流式寫入。全量 11,287 個基因（73,700 個擾動樣本）在這台機器上
  實測會在 pickle 那一步把可用記憶體從 30GB 打到 <1.1GB，已經被安全監控
  自動 kill 過一次。子抽樣到 MAX_PERT_GENES 個基因（保留全部 ctrl 樣本）
  把物件數量壓到安全範圍，是繞開這個上游套件記憶體瓶頸的務實做法，
  在 gears_model/README.md 有誠實記錄，不是隱藏的限制。

輸出：`../data/gears_ready_<condition>.h5ad`（遠小於原始 41.5GB，只有選定
condition、通過品質門檻、且子抽樣後的樣本）。
"""

import sys
from pathlib import Path

import anndata as ad
import numpy as np
import scanpy as sc

REPO_ROOT = Path(__file__).resolve().parents[3]
PSEUDOBULK_PATH = REPO_ROOT / "data" / "marson2025_data" / "GWCD4i.pseudobulk_merged.h5ad"
OUT_DIR = REPO_ROOT / "src/10_ml_perturbation_prediction/data"
CULTURE_CONDITION = "Rest"
MAX_PERT_GENES = 2000  # 見上方模組說明；記憶體導向的務實子抽樣，非生物學考量
SUBSAMPLE_SEED = 0


def main():
    if not PSEUDOBULK_PATH.exists():
        sys.exit(f"找不到 {PSEUDOBULK_PATH}，請先跑 download_precomputed_DE.py 補上 GWCD4i.pseudobulk_merged.h5ad")

    print(f"讀取 {PSEUDOBULK_PATH} (backed 模式)...")
    adata = ad.read_h5ad(PSEUDOBULK_PATH, backed="r")
    print(f"obs={adata.n_obs}, var={adata.n_vars}")
    print("obs columns:", list(adata.obs.columns))

    obs = adata.obs
    mask = (
        (obs["culture_condition"] == CULTURE_CONDITION)
        & (obs["keep_for_DE"] == True)  # noqa: E712
    )
    print(f"篩選 culture_condition=={CULTURE_CONDITION} 且 keep_for_DE==True: {mask.sum()} / {adata.n_obs} 列")

    sub = adata[mask.to_numpy()].to_memory()

    print(f"標準化前 .X 範圍：min={sub.X.min():.1f}, max={sub.X.max():.1f}, mean={sub.X.mean():.1f}")
    sc.pp.normalize_total(sub)
    sc.pp.log1p(sub)
    print(f"標準化後 .X 範圍：min={sub.X.min():.3f}, max={sub.X.max():.3f}, mean={sub.X.mean():.3f}")

    guide_type = sub.obs["guide_type"].astype(str)
    perturbed_gene = sub.obs["perturbed_gene_name"].astype(str)

    condition = perturbed_gene.where(guide_type != "non-targeting", other="ctrl")
    condition = condition.where(guide_type == "non-targeting", other=perturbed_gene + "+ctrl")
    sub.obs["condition"] = condition.to_numpy()

    # GEARS 強制要求 obs 有 cell_type 欄位（它原本設計給多細胞型資料集用）。
    # 這個資料集全部都是 CD4+ T 細胞，單一值即可。
    sub.obs["cell_type"] = "CD4T"

    n_ctrl_full = (sub.obs["condition"] == "ctrl").sum()
    n_pert_full = (sub.obs["condition"] != "ctrl").sum()
    all_pert_genes = sorted(perturbed_gene[guide_type != "non-targeting"].unique())
    print(f"\n子抽樣前：ctrl 樣本數 {n_ctrl_full}，擾動樣本數 {n_pert_full}（{len(all_pert_genes)} 個唯一基因）")

    if len(all_pert_genes) > MAX_PERT_GENES:
        rng = np.random.default_rng(SUBSAMPLE_SEED)
        kept_genes = set(rng.choice(all_pert_genes, size=MAX_PERT_GENES, replace=False))
        keep_mask = ((sub.obs["condition"] == "ctrl") | perturbed_gene.isin(kept_genes)).to_numpy()
        sub = sub[keep_mask].copy()
        print(f"子抽樣至 MAX_PERT_GENES={MAX_PERT_GENES} 個基因（seed={SUBSAMPLE_SEED}）")

    print("\ncondition 分布（前 10）：")
    print(sub.obs["condition"].value_counts().head(10))
    n_ctrl = (sub.obs["condition"] == "ctrl").sum()
    n_pert = (sub.obs["condition"] != "ctrl").sum()
    print(f"\n子抽樣後：ctrl 樣本數：{n_ctrl}，擾動樣本數：{n_pert}（{sub.obs['condition'].nunique() - (1 if n_ctrl else 0)} 個唯一基因）")

    if n_ctrl == 0:
        sys.exit("沒有 ctrl 樣本——GEARS 需要控制組才能算擾動效應，請檢查 guide_type 欄位值是否為 'non-targeting'")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"gears_ready_{CULTURE_CONDITION}.h5ad"
    sub.write_h5ad(out_path)
    print(f"\n✅ 寫出 {out_path} ({sub.n_obs} obs × {sub.n_vars} var)")


if __name__ == "__main__":
    main()
