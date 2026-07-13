# EDA — 初步結果 · Target cards (canonical 39-col)

> **本階段目標為何 · Stage goal**
>
> 把統計證據組裝成決策就緒的 target cards(39 欄:效應/顯著性/敲低狀態/穩健性/等級/藥理與疾病 overlay)。這是使用者實際看到的產品資料;kd_status 遵守 unknown≠0(not_assessed vs not_measurable)。
> Assemble per-target-per-condition decision-ready cards (the canonical 39-col product).

**輸入 · Inputs**
- metadata/suppl_tables/DE_stats.suppl_table.csv
- metadata/suppl_tables/guide_kd_efficiency.suppl_table.csv
- metadata/suppl_tables/sgrna_library_metadata.suppl_table.csv

**重現指令 · Reproduce**: cd src/3_DE_analysis && python build_target_cards.py --de-stats ... --output ...  (see docs/REPRODUCIBILITY.md §6.4)

> `unknown != 0`: 缺失以 missingness% 呈現,類別分佈保留 `(missing)` 桶;NaN 不會被當成 0。

## target_cards.csv (a6bba17b, canonical)

**MISSING on disk**: `sources/target_tool_cache/a6bba17b-f194-4a50-8cf8-96e03eededd6/target_cards.csv`

---
_Regenerate: `python scripts/generate_stage_eda.py`. Deterministic (no timestamp); guarded by `tests/test_generate_stage_eda.py`. Part of the release freeze — see `docs/mvp-research/pipeline/EDA_INDEX.md`._
