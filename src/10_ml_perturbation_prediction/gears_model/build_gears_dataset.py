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

輸出：`../data/gears_ready_<condition>.h5ad`（遠小於原始 41.5GB，只有選定
condition 且通過品質門檻的樣本）。
"""

import sys
from pathlib import Path

import anndata as ad

REPO_ROOT = Path(__file__).resolve().parents[3]
PSEUDOBULK_PATH = REPO_ROOT / "data" / "marson2025_data" / "GWCD4i.pseudobulk_merged.h5ad"
OUT_DIR = REPO_ROOT / "src/10_ml_perturbation_prediction/data"
CULTURE_CONDITION = "Rest"


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

    guide_type = sub.obs["guide_type"].astype(str)
    perturbed_gene = sub.obs["perturbed_gene_name"].astype(str)

    condition = perturbed_gene.where(guide_type != "non-targeting", other="ctrl")
    condition = condition.where(guide_type == "non-targeting", other=perturbed_gene + "+ctrl")
    sub.obs["condition"] = condition.to_numpy()

    print("\ncondition 分布（前 10）：")
    print(sub.obs["condition"].value_counts().head(10))
    n_ctrl = (sub.obs["condition"] == "ctrl").sum()
    n_pert = (sub.obs["condition"] != "ctrl").sum()
    print(f"\nctrl 樣本數：{n_ctrl}，擾動樣本數：{n_pert}（{sub.obs['condition'].nunique() - (1 if n_ctrl else 0)} 個唯一基因）")

    if n_ctrl == 0:
        sys.exit("沒有 ctrl 樣本——GEARS 需要控制組才能算擾動效應，請檢查 guide_type 欄位值是否為 'non-targeting'")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"gears_ready_{CULTURE_CONDITION}.h5ad"
    sub.write_h5ad(out_path)
    print(f"\n✅ 寫出 {out_path} ({sub.n_obs} obs × {sub.n_vars} var)")


if __name__ == "__main__":
    main()
