#!/usr/bin/env python3
"""
從 GWCD4i.DE_stats.h5ad 萃取「全量」per-target × gene 帶符號 DE 長表——
不像 extract_gate_passing_signed_DE.py 只取 1,235 個門檻標的，這裡處理
全部 33,983 個 target×condition 列（= repo 現有 DE_stats.suppl_table.csv
的完整列數，涵蓋全部 ~11,526 個標的）。

只保留顯著配對（adj_p_value < 0.1），否則 33,983 × 10,282 全叉積 = 3.49 億
列不可能放進 repo。即使篩完，全量預期 ~1,700 萬列，單一 CSV/Parquet 仍會
超過 GitHub 100MB 單檔限制，因此用 ParquetWriter 依列數門檻自動切成多個
part 檔（見 ROWS_PER_PART）。

分批（batch）處理 h5ad 的列，每批只把該批的 layers 讀進記憶體
（batch_size 列 × 10,282 基因 × 4 layers × 8 bytes），避免一次載入
33,983 × 10,282 的全矩陣（單一 layer 就 ~2.8GB，四個 layer 同時在記憶體
會逼近本沙盒 ~21GB 可用記憶體的上限）。
"""

import sys
import time
from pathlib import Path

import anndata as ad
import h5py
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[3]
H5AD_PATH = REPO_ROOT / "data" / "marson2025_data" / "GWCD4i.DE_stats.h5ad"
OUT_DIR = REPO_ROOT / "metadata" / "suppl_tables" / "full_signed_DE"
FDR_THRESHOLD = 0.1
BATCH_SIZE = 3000          # 列（target×condition），控制單批記憶體用量
ROWS_PER_PART = 1_400_000  # 每個 parquet part 檔的列數上限（實測估算 ~45MB/part，安全低於 100MB）


def format_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def main():
    if not H5AD_PATH.exists():
        sys.exit(f"找不到 {H5AD_PATH}，請先執行 download_precomputed_DE.py")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("part-*.parquet"):
        old.unlink()

    print(f"讀取 {H5AD_PATH} (backed 模式)...")
    adata = ad.read_h5ad(H5AD_PATH, backed="r")
    n_obs, n_var = adata.n_obs, adata.n_vars
    print(f"obs={n_obs}, var={n_var}")

    obs = adata.obs.reset_index(drop=True)
    var = adata.var
    gene_ids_all = (var["gene_ids"].to_numpy() if "gene_ids" in var else var.index.to_numpy())
    gene_names_all = (var["gene_name"].to_numpy() if "gene_name" in var else var.index.to_numpy())

    adata.file.close()  # 見 extract_gate_passing_signed_DE.py 的說明：X 是空 dataset，
                        # 避免任何 anndata 端的整體 subset 操作，全程改用 h5py 直接讀 layers。

    target_gene_all = obs["target_contrast_gene_name"].to_numpy()
    target_ensembl_all = obs["target_contrast"].to_numpy()
    condition_all = obs["culture_condition"].to_numpy()

    part_idx = 0
    rows_in_current_part = 0
    writer = None
    total_sig_rows = 0
    start_t = time.time()

    def open_new_writer(schema):
        nonlocal writer, part_idx, rows_in_current_part
        if writer is not None:
            writer.close()
        part_path = OUT_DIR / f"part-{part_idx:03d}.parquet"
        writer = pq.ParquetWriter(part_path, schema, compression="zstd")
        rows_in_current_part = 0
        part_idx += 1

    schema = pa.schema([
        ("target_gene", pa.string()),
        ("target_ensembl_id", pa.string()),
        ("culture_condition", pa.string()),
        ("downstream_gene", pa.string()),
        ("downstream_ensembl_id", pa.string()),
        ("log_fc", pa.float64()),
        ("adj_p_value", pa.float64()),
        ("baseMean", pa.float64()),
        ("zscore", pa.float64()),
    ])
    open_new_writer(schema)

    with h5py.File(H5AD_PATH, "r") as f:
        layers = f["layers"]
        n_batches = (n_obs + BATCH_SIZE - 1) // BATCH_SIZE
        for b in range(n_batches):
            r0, r1 = b * BATCH_SIZE, min((b + 1) * BATCH_SIZE, n_obs)

            log_fc = layers["log_fc"][r0:r1, :]
            adj_p = layers["adj_p_value"][r0:r1, :]
            base_mean = layers["baseMean"][r0:r1, :]
            zscore = layers["zscore"][r0:r1, :]

            sig_mask = adj_p < FDR_THRESHOLD
            row_idx, col_idx = np.where(sig_mask)
            if len(row_idx) == 0:
                continue

            batch_table = pa.table({
                "target_gene": target_gene_all[r0:r1][row_idx],
                "target_ensembl_id": target_ensembl_all[r0:r1][row_idx],
                "culture_condition": condition_all[r0:r1][row_idx],
                "downstream_gene": gene_names_all[col_idx],
                "downstream_ensembl_id": gene_ids_all[col_idx],
                "log_fc": log_fc[row_idx, col_idx],
                "adj_p_value": adj_p[row_idx, col_idx],
                "baseMean": base_mean[row_idx, col_idx],
                "zscore": zscore[row_idx, col_idx],
            }, schema=schema)

            # 若這批會讓目前 part 超過門檻，先把這批切成兩截分別寫進舊/新 part
            remaining_capacity = ROWS_PER_PART - rows_in_current_part
            if len(batch_table) > remaining_capacity:
                writer.write_table(batch_table.slice(0, remaining_capacity))
                open_new_writer(schema)
                writer.write_table(batch_table.slice(remaining_capacity))
                rows_in_current_part = len(batch_table) - remaining_capacity
            else:
                writer.write_table(batch_table)
                rows_in_current_part += len(batch_table)

            total_sig_rows += len(batch_table)

            if (b + 1) % 5 == 0 or (b + 1) == n_batches:
                elapsed = time.time() - start_t
                pct = (r1 / n_obs) * 100
                print(f"  {pct:.0f}% ({r1}/{n_obs} 列已掃描, {total_sig_rows:,} 顯著配對, {elapsed:.0f}s)", flush=True)

    writer.close()

    part_files = sorted(OUT_DIR.glob("part-*.parquet"))
    total_size = sum(p.stat().st_size for p in part_files)
    print(f"\n✅ 完成：{total_sig_rows:,} 列顯著配對，寫成 {len(part_files)} 個 parquet part")
    for p in part_files:
        print(f"   {p.name}: {format_size(p.stat().st_size)}")
    print(f"   合計: {format_size(total_size)}")
    print(f"   位置: {OUT_DIR}")


if __name__ == "__main__":
    main()
