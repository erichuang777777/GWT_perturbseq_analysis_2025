# Topic 14 - Target Card 規格（可直接對接 GWT）

## A. 輸入與輸出

- 輸入資料（由上游結果派生）
  - `DE_stats.suppl_table.csv`
  - `guide_kd_efficiency.suppl_table.csv`
  - `sgrna_library_metadata.suppl_table.csv`
  - `sgrna_per_cell.csv` 或對應 cell metadata
- 輸出
  - 每一列一個 `target_condition` 的 target card（可為 CSV + JSON）

## B. 必備欄位（最小 24 欄）

- `target`
- `condition`
- `n_cells_target`
- `n_guides`
- `n_donors`
- `knockdown_effect`
- `ontarget_significant`
- `offtarget_flag`
- `n_total_de_genes`
- `n_up_de_genes`
- `n_down_de_genes`
- `median_logFC`
- `max_abs_logFC`
- `fdr_min`
- `crossguide_correlation`
- `crossdonor_correlation_mean`
- `crossdonor_correlation_min`
- `replicate_pass_flag`
- `batch_sensitivity_flag`
- `positive_control_similarity`
- `pathway_axis`
- `condition_specificity_score`
- `clinical_axis`
- `nearest_success_drug`
- `nearest_failure_or_warning`
- `statistical_evidence_grade`
- `score_cap_reason`

## C. 核心篩選（MVP gate）

- 必填條件
  - `n_cells_target >= 200`
  - `ontarget_significant == True`
  - `offtarget_flag == False`
  - `n_total_de_genes >= 50`
- 穩健條件
  - `crossdonor_correlation_mean >= 0.20`
  - `crossguide_correlation >= 0.20`
- 條件特異性（可選）
  - 任一條件中 `condition_specificity_score >= 0.30`

這是一組高信心 perturbation signal，非直接藥物可行性保證。

## D. statistical_evidence_grade

- `4 = A級`: 全部門檻通過，且有 2+ positive control 對齊信號
- `3 = B級`: 通過基本門檻，有高於 median 的可重複性（至少一個 cross metric >=0.3）
- `2 = C級`: 部分門檻通過，需要 h5ad 驗證補強
- `1 = D級`: 僅有原始 DE signal，暫不進入高風險候選池

## E. score_cap_reason（為何降階）

- `low_cells`
- `weak_replicability`
- `high_offtarget`
- `batch_sensitive`
- `guides_inconsistent`
- `single_donor_dominance`
- `direction_unclear`

## F. 先做幾個關鍵圖

- `QC_funnel`：原始 target -> ontology -> high-confidence flow
- `crossguide_vs_crossdonor_scatter`
- `condition_specificity_heatmap`
- `control_null_overlay`（non-targeting/negative control）
- `clinical_axis_radar`（success / warning 軸）
- `target_card_waterfall`（每卡片 5~8 個關鍵證據分項）

## G. 執行順序（建議）

1. `DE_stats` join `guide_kd` 與 `library metadata`
2. 套用門檻生出 `replicate_pass_flag`
3. 先輸出 CSV-first score（排序、Top-N 清單）
4. 將 Top-N 匯入 h5ad 流程做
   - pseudobulk + mixed model
   - batch sensitivity
   - pathway/reproducibility cross-check
   - biological controls 重新驗證

## H. 與第 15 題的對接

- `seed_modules.csv` 的 `seed_genes` 只作為 module-level 驗證與 hypothesis scaffold
- 可直接把每個 `target_condition` 與各模組做 module score 對位，納入 `pathway_axis` 欄位

## I. 實作指令（CSV-first）

建議直接跑以下指令產出第一版 target card：

```bash
python src/3_DE_analysis/build_target_cards.py \
  --de-stats metadata/suppl_tables/DE_stats.suppl_table.csv \
  --guide-kd metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv \
  --library-metadata metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv \
  --clinical-benchmark sources/topic05_successful_drug_benchmarks.csv \
  --output sources/topic14_target_cards.csv
```

輸出欄位會包含：`target`, `condition`, `target_id`, `n_cells_target`, `n_guides`, `n_donors`, `n_total_de_genes`, `n_up_genes`, `n_down_genes`, `ontarget_effect_size`, `ontarget_significant`, `offtarget_flag`, `median_logFC`, `max_abs_logFC`, `fdr_min`, `crossdonor_correlation_mean`, `crossdonor_correlation_min`, `crossguide_correlation`, `replicate_pass_flag`, `batch_sensitivity_flag`, `pathway_axis`, `condition_specificity_score`, `clinical_axis`, `nearest_success_drug`, `nearest_failure_or_warning`, `statistical_evidence_grade`, `score_cap_reason`.
