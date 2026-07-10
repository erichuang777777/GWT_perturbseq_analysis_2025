# 10 — ML Perturbation Prediction (探索性、隔離)

**這個目錄是完全隔離的機器學習實驗場。它絕不匯入 `src/3_DE_analysis` 的任何 production
路徑,production 路徑（`build_target_cards.py`、`readiness_engine.py`、任何寫
`target_cards.csv`/readiness 的程式）也絕不 import 這個目錄下的任何東西。**
這是刻意的邊界,不是疏漏——目的是讓探索性 ML 實驗可以自由嘗試、失敗、重來,
不會有任何路徑意外把未經驗證的模型輸出寫進使用者看到的卡片或 readiness 判斷。

## 為什麼獨立出來（背景）

`src/3_DE_analysis/perturbation_prediction_ml.py` 已經有一個經過深思熟慮的監督式
ML 基準模組，但範圍刻意限縮在「用兩個已知條件預測第三個條件的效應量」——因為
在任務 A（全基因組帶符號 DE 矩陣萃取，見
`docs/mvp-research/TASK_A_GB10_HANDOFF.md`）完成之前，repo 內唯一夠大、夠真實的
標籤集就是這個。

任務 A 完成後，`metadata/suppl_tables/full_signed_DE/`（205 萬個顯著
target×gene 配對，10,851 個標的）與 `metadata/suppl_tables/gate_passing_signed_DE.suppl_table.csv.gz`
解鎖了新的監督式任務：**預測「哪些下游基因會被顯著影響」，而非只是「影響幾個」**。
這個目錄就是探索這個新任務空間的地方——用戶要求「探索所有可能」，包含由簡到繁
的兩條路線（GenePert 風格的簡單基線、GEARS 風格的圖神經網路），所以需要一個
不會弄髒 production 程式碼的獨立空間。

## 護欄（沿用 `perturbation_prediction_ml.py` 的既有紀律，非新發明）

1. **絕不餵決策。** 這裡的任何模型輸出都不寫入 `target_cards.csv`、
   readiness、或任何卡片/dashboard 讀取的檔案。只寫進本目錄下的 `results/`。
2. **`unknown != 0`。** 缺失的特徵絕不悄悄補 0；用模型原生支援 NaN
   （如 `HistGradientBoostingRegressor`）或明確的缺失指示欄位。
3. **決定性（deterministic）。** 固定 `random_state`；跨標的分組的
   `GroupKFold`（同一個標的的資料不會同時出現在 train 和 test，避免洩漏）。
4. **誠實回報。** 每個模型都要跟「均值基線」（mean-of-known-baseline）比較，
   輸不過就老實說輸不過——這正是 2025-2026 年的基準測試文獻（Ahlmann-Eltze
   et al., *Nature Methods* 2025）反覆證實的：多數深度學習模型目前打不過簡單
   基線。**本目錄的目標是誠實探索，不是製造一個好看的分數。**
5. **不進 `environment.yaml`。** 本目錄的依賴寫在自己的 `requirements.txt`，
   用獨立 venv 安裝（沙盒沒有 conda，見下）；不動 repo 根目錄的
   `environment.yaml`，避免把探索性、可能很重（torch 等）的依賴污染主環境。

## 目錄結構

```
src/10_ml_perturbation_prediction/
├── README.md                    ← 本檔
├── requirements.txt              ← 本目錄專屬依賴（獨立於 environment.yaml）
├── data/                         ← 由 metadata/suppl_tables/ 載入/快取的中介特徵（不進 git，見 .gitignore）
├── genept_baseline/              ← 簡單路線：基因特徵/嵌入 + 岭回歸/梯度提升
│   ├── build_gene_features.py
│   ├── train_baseline.py
│   └── evaluate.py
├── gears_model/                  ← 進階路線：GO 知識圖譜 + 圖神經網路
│   └── (見該目錄 README，規模較大，逐步實作)
└── results/                      ← 基準測試報告（json/csv/md），只描述性，不進決策
```

## 資料來源

- `metadata/suppl_tables/full_signed_DE/`（全量，205 萬列，parquet）
- `metadata/suppl_tables/gate_passing_signed_DE.suppl_table.csv.gz`（門檻子集，107 萬列）
- 兩者 schema 一致：`target_gene, target_ensembl_id, culture_condition, downstream_gene, downstream_ensembl_id, log_fc, adj_p_value, baseMean, zscore`

## 結果摘要（兩條路線都已完成，皆為誠實負面結果）

| 方法 | Pearson（全部基因） | Pearson（顯著差異基因） | 贏了均值基線？ |
|---|---|---|---|
| GenePT embedding + Ridge regression | ~0.18（Rest/Stim8hr/Stim48hr 皆未贏） | *(未計算此指標)* | ❌ |
| GEARS（GO 圖 + GNN，官方套件） | 0.9916 | **0.0210** | ❌ |

兩個架構迥異的方法（簡單線性 vs. 複雜圖神經網路）都誠實地打不過「訓練集
平均 profile」這個基線，方向一致，呼應 2025-2026 年文獻共識
（Ahlmann-Eltze et al., *Nature Methods* 2025）。詳細討論見
`genept_baseline/`（`../results/genept_baseline_README.md`）與
`gears_model/`（`../results/gears_benchmark_README.md`）。
