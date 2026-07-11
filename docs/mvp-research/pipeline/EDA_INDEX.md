# EDA index — per-stage freeze inventory

每個 pipeline 階段一份 EDA 盤點報告,附「本階段目標」、shape、逐欄缺失率、關鍵分佈、md5(對 `FREEZE_MANIFEST.csv`)與重現指令。全部由 `scripts/generate_stage_eda.py` deterministically 產生。

| # | Stage | Report |
|---|---|---|
| 01_raw | 原始資料 · Raw data | [`01_raw/EDA_01_raw.md`](01_raw/EDA_01_raw.md) |
| 02_curated | 清理資料 · Curated | [`02_curated/EDA_02_curated.md`](02_curated/EDA_02_curated.md) |
| 03_processed | 處理後資料 · Processed | [`03_processed/EDA_03_processed.md`](03_processed/EDA_03_processed.md) |
| 04_results_target_cards | 初步結果 · Target cards (canonical 39-col) | [`04_statistical/EDA_04a_target_cards.md`](04_statistical/EDA_04a_target_cards.md) |
| 04_statistical | 統計檢定 · Statistical summaries + validation | [`04_statistical/EDA_04b_statistical.md`](04_statistical/EDA_04b_statistical.md) |
| 05_visualization | 視覺化 · Visualization catalog | [`05_visualization/EDA_05_visualization.md`](05_visualization/EDA_05_visualization.md) |

視覺化下游的 **前端(React static portal)** 與 **06_animation** 為展示層,其盤點見 `docs/mvp-research/pipeline/07_dashboard/` 與 `frontend/webserver/README.md`;上傳功能(即時)為獨立工具,見其自身 PR。
