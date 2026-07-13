#!/usr/bin/env python3
"""
建立 T2「已知調控子分類器」的特徵表，快取進 ../data/（gitignored，可重建）。

**任務：** `benchmark_results.csv` 的 `truth_class`（13 個 positive、1 個 negative、
1,211 個 rest/未標註）是否能被一個監督式分類器（linear vs ML）學出來，且贏過現有的
簡單排序基線（只用 `ctx_specific_de` 排序，AUROC 0.85）？

**leakage 稽核（本檔的核心紀律，不是選配）：** `ctx_specific_de =
max(|de_Stim8hr - de_Rest|, |de_Stim48hr - de_Rest|)`（`target_master_table.csv`
欄位；已用 CD3E 的真實數字核對過公式：de_Rest=4, de_Stim8hr=5711, de_Stim48hr=1586 →
5707，與 ctx_specific_de 完全吻合）。任何跟這三個數字（或其單調變換，如
`n_total_de_genes`／`breadth_max_de`／`condition_specificity_*`／`max_abs_logFC`／
`median_logFC`／`ontarget_effect_size`）高度重疊的欄位，拿來當特徵訓練模型，
「贏過 0.85」很可能只是把同一個分數換個包裝，不是真的學到新東西。這裡把候選特徵
明確分成三組，`train_compare.py` 會分別報告「完整特徵」與「排除 circular 特徵後」
兩個版本的結果：

- **CIRCULAR_COLUMNS**：`ctx_specific_de` 公式的字面輸入，或跟它同一來源、幾乎
  單調對應的量。**full 特徵集保留，ablated 特徵集排除。**
- **LABEL_ADJACENT_COLUMNS**：跟「正類基因怎麼被選出來」相關但不是分數本身
  ——`n_concept_modules`（README 自述：27 個 canonical positive 裡有 12 個本來就
  出現在 platform 的 concept 模組標註中）。同樣 full 保留、ablated 排除。
- **EXCLUDED_DE_MAGNITUDE_DUPLICATES**：`target_cards.csv` 裡跟 CIRCULAR_COLUMNS
  本質同一量的近重複欄位。**兩個特徵集都不納入**（不是只從 ablated 排除）——
  CIRCULAR_COLUMNS 已經涵蓋公式的字面輸入，這裡再放一份近重複只會添多重共線
  雜訊，對 ablation 沒有額外意義。
- **SAFE_COLUMNS**：跟 DE 幅度公式無直接代數關係的量（gnomAD constraint、
  guide-level robustness、實驗設計 metadata、獨立的相似度分數）。兩個特徵集都保留。

**unknown != 0：** 缺失特徵維持 NaN（例如 `crossdonor_correlation_mean` 只覆蓋
~14% 的列、`crossguide_correlation` ~9%、`n_donors` 全部是 NaN——這些都如實留白，
不補值。target_cards 是 (gene, condition) 粒度，這裡用 `nanmean`（連續量）或
「跨 condition 至少一次為真」（`replicate_pass_flag`／`batch_sensitivity_flag`
布林旗標）聚合到 gene 粒度，缺失時仍是 NaN，不是 False。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
LABELS_PATH = REPO_ROOT / "docs/mvp-research/pipeline/methodological_validation/benchmark_results.csv"
MASTER_TABLE_PATH = REPO_ROOT / "docs/mvp-research/pipeline/kinetics_avoid/target_master_table.csv"
CARDS_PATH = REPO_ROOT / "sources/target_tool_cache/a792d68c-7adc-46a6-964a-35770e5adbde/target_cards.csv"
OUT_DIR = REPO_ROOT / "src/10_ml_perturbation_prediction/data"

# --- 字面上是 ctx_specific_de 公式輸入，或跟它幾乎單調對應的欄位（來自
# target_master_table.csv，會被實際載入為特徵；full 特徵集保留，ablated 排除） ---
CIRCULAR_COLUMNS = [
    "de_Rest", "de_Stim8hr", "de_Stim48hr", "breadth_max_de",
    "is_ctx_specific",  # 本身就是 ctx_specific_de 過門檻與否的旗標
]

# --- 跟「正類名單怎麼被選出來」相關，不是分數本身，但一樣是 leakage 風險
# （full 特徵集保留，ablated 排除） ---
LABEL_ADJACENT_COLUMNS = ["n_concept_modules"]

# --- target_cards.csv 裡跟上面同一量的近重複欄位（n_total_de_genes 系列本質上就是
# de_Rest/Stim8hr/Stim48hr 的另一種呈現）。兩個特徵集都不納入——CIRCULAR_COLUMNS
# 已經涵蓋了公式的字面輸入，這裡再加一份近重複只會增加多重共線的雜訊，
# 對 ablation 沒有額外意義，故整批排除，而非「只從 ablated 排除」。 ---
EXCLUDED_DE_MAGNITUDE_DUPLICATES = [
    "n_total_de_genes", "n_up_genes", "n_down_genes",
    "median_logFC", "max_abs_logFC",
    "condition_specificity_score", "condition_specificity_zscore",
    "ontarget_effect_size",
]

# --- 跟 DE 幅度公式無直接代數關係，兩個特徵集都保留 ---
SAFE_NUMERIC_COLUMNS = [
    # target_master_table.csv -- 外部 gnomAD constraint + druggability 旗標數
    "loeuf", "pli", "n_avoid_flags",
    # target_cards.csv (聚合到 gene 粒度) -- 實驗設計 / robustness / 獨立相似度
    "n_cells_target", "n_guides",
    "crossdonor_correlation_mean", "crossdonor_correlation_min", "crossguide_correlation",
    "guide_signif_ratio", "guide_fdr_min", "guide_t_abs_median",
    "positive_control_similarity", "target_baseline_expression", "n_donors",
]
SAFE_FLAG_COLUMNS = ["replicate_pass_flag_frac", "batch_sensitivity_flag_frac"]
SAFE_CATEGORICAL_COLUMNS = ["delivery_modality", "polarity", "kinetic_archetype", "avoid_tier", "stimulation_gated"]

# 這一版明確排除的欄位（範圍控制，不是漏掉）：statistical_evidence_grade（複合分數，
# 是否受 DE 幅度影響不明確，保守排除）、druggable_class/tractability_modality/
# safety_note/nearest_success_drug/nearest_failure_or_warning/pathway_axis/
# clinical_axis/kd_status/score_cap_reason（文字欄位需要更細緻的編碼，留給後續版本）。


def _aggregate_cards_to_gene_level(cards: pd.DataFrame) -> pd.DataFrame:
    """target_cards.csv 是 (target, condition) 粒度；聚合到 gene 粒度。
    連續量用 nanmean（缺失維持 NaN，不是 0）；布林旗標用「跨 condition 至少一次為真
    的比例」（同樣缺失維持 NaN，不是 False）。"""
    numeric_present = [c for c in SAFE_NUMERIC_COLUMNS if c in cards.columns]
    agg = cards.groupby("target")[numeric_present].mean(numeric_only=True)

    for flag_col, out_col in [("replicate_pass_flag", "replicate_pass_flag_frac"),
                               ("batch_sensitivity_flag", "batch_sensitivity_flag_frac")]:
        if flag_col not in cards.columns:
            continue
        s = cards[flag_col]
        if s.dtype == object:
            s = s.map({"True": True, "False": False, "not_flagged": False, "flagged": True}).where(s.notna())
        s = s.astype("float")  # bool/NaN -> 1.0/0.0/NaN, preserves unknown
        agg[out_col] = s.groupby(cards["target"]).mean()

    agg = agg.rename_axis("gene").reset_index()
    return agg


def build_features() -> pd.DataFrame:
    labels = pd.read_csv(LABELS_PATH)[["gene", "truth_class", "ctx_rank", "ctx_specific_de"]]
    master = pd.read_csv(MASTER_TABLE_PATH)
    cards = pd.read_csv(CARDS_PATH, low_memory=False)

    cards_gene = _aggregate_cards_to_gene_level(cards)

    master_cols = ["gene"] + [c for c in (CIRCULAR_COLUMNS + LABEL_ADJACENT_COLUMNS + SAFE_NUMERIC_COLUMNS
                                           + SAFE_CATEGORICAL_COLUMNS) if c in master.columns]
    df = labels.merge(master[master_cols].drop_duplicates("gene"), on="gene", how="left", suffixes=("", "_master"))
    df = df.merge(cards_gene, on="gene", how="left", suffixes=("", "_cards"))

    missing_from_master = labels["gene"][~labels["gene"].isin(master["gene"])]
    missing_from_cards = labels["gene"][~labels["gene"].isin(cards_gene["gene"])]
    print(f"標籤 {len(labels)} 個基因；{len(missing_from_master)} 個不在 target_master_table "
          f"(unknown, 保留 NaN)；{len(missing_from_cards)} 個不在 target_cards (unknown, 保留 NaN)。")

    return df


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = build_features()
    out_path = OUT_DIR / "known_regulator_features.parquet"
    df.to_parquet(out_path, index=False)
    print(f"✅ 寫出 {out_path}: {df.shape[0]} 個基因 x {df.shape[1]} 欄")
    print(f"   truth_class 分佈: {df['truth_class'].value_counts(dropna=False).to_dict()}")
    circular_present = [c for c in CIRCULAR_COLUMNS if c in df.columns]
    label_adj_present = [c for c in LABEL_ADJACENT_COLUMNS if c in df.columns]
    safe_present = [c for c in df.columns if c not in circular_present + label_adj_present
                    + ["gene", "truth_class", "ctx_rank", "ctx_specific_de"]]
    print(f"   CIRCULAR_COLUMNS(full-only): {circular_present}")
    print(f"   LABEL_ADJACENT_COLUMNS(full-only): {label_adj_present}")
    print(f"   SAFE_COLUMNS(both sets, {len(safe_present)}): {safe_present}")


if __name__ == "__main__":
    main()
