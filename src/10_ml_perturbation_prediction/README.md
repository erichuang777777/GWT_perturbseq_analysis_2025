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

`genept_baseline`/`gears_model` 兩條路線跑完（皆誠實負面）後，使用者接續要求
「建立一個 ML/linear 等多模型比較的結果，即使 ML 不好也沒關係，也是一種發現」，
延伸出兩條新路線：**`known_regulator_classifier/`**（linear vs ML 挑戰現有的
已知調控子排序基線——移除 leakage 欄位並補上 AUPRC 後為誠實負面，見下方結果）與
**`real_features_baseline/`**（把 `genept_baseline` 的外部 GenePT 文字嵌入換成
被擾動基因自己的真實實驗特徵，其餘任務結構不變，唯一變數是特徵來源）。

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
├── known_regulator_classifier/   ← T2：已知調控子分類（linear vs ML 挑戰簡單排序基線）
│   ├── build_features.py
│   └── train_compare.py
├── real_features_baseline/       ← T1-rework：genept_baseline 換成真實 DE 特徵
│   ├── build_real_features.py
│   └── train_real_features.py
└── results/                      ← 基準測試報告（json/csv/md），只描述性，不進決策
```

## 資料來源

- `metadata/suppl_tables/full_signed_DE/`（全量，205 萬列，parquet）
- `metadata/suppl_tables/gate_passing_signed_DE.suppl_table.csv.gz`（門檻子集，107 萬列）
- 兩者 schema 一致：`target_gene, target_ensembl_id, culture_condition, downstream_gene, downstream_ensembl_id, log_fc, adj_p_value, baseMean, zscore`

## 結果摘要（四條路線：T2 誠實負面、T1 兩個負面 + 一個微弱方向性訊號）

> 註：T2 曾一度被記為「唯一正面發現」，但使用者指出應補上 AUPRC——補上後發現原本的
> AUROC「贏」是 1% prevalence 下的假象，T2 的誠實結論是**負面**（見下方 T2 段落）。
> 目前四條路線裡沒有任何一個在正確指標下穩定贏過簡單基線；唯一非負面的是 T1-rework
> Ridge 的 +0.01 微弱方向性訊號。

**T1（用被擾動基因的特徵，預測其下游反應 profile）：**

| 方法 | Pearson（全部基因） | Pearson（顯著差異基因） | 贏了均值基線？ |
|---|---|---|---|
| GenePT embedding + Ridge regression | ~0.18（Rest/Stim8hr/Stim48hr 皆未贏） | *(未計算此指標)* | ❌ |
| GEARS（GO 圖 + GNN，官方套件） | 0.9916 | **0.0210** | ❌ |
| 真實 DE 特徵 + Ridge（T1-rework，landmark-500 設定） | Rest 0.103 / Stim8hr 0.109 / Stim48hr 0.108 | — | ✅ 微幅（+0.008~0.011）|
| 真實 DE 特徵 + HistGBR（T1-rework，landmark-500 設定） | Rest 0.071 / Stim8hr 0.076 / Stim48hr 0.083 | — | ❌ |

> T1-rework 註：把 GenePT 外部文字嵌入換成被擾動基因**自己的真實實驗特徵**後，Ridge
> 從「全輸」變成「三個條件都微幅贏過均值基線」——方向性訊號成立（基因自己的量測比通用
> 文字描述更能預測其下游反應），**但 margin 只有 ~0.01、絕對相關僅 ~0.10，且非線性
> HistGBR 反而輸**，不是突破。且 landmark-500/0-floor 設定與 GenePT 的密集矩陣不完全
> 可比，數字只能各自跟自己的基線比。完整誠實討論見
> `../results/real_features_baseline_README.md`。

**T2（已知調控子分類，`known_regulator_classifier/`）：誠實負面（AUPRC 推翻了 AUROC 假象）**

現有簡單排序基線（`ctx_specific_de` 排序）AUROC = 0.8458、**AUPRC = 0.4744**。因為正類
prevalence 只有 13/1225 ≈ 1%，**AUROC 會過度樂觀，必須同時看對稀有正類敏感的 AUPRC**。
10x 重複 5-fold StratifiedKFold，ablated（排除 leakage 欄位）特徵集：

| 模型 | ablated AUROC | 贏基線 | **ablated AUPRC** | **贏基線** |
|---|---|---|---|---|
| Logistic Regression | 0.7595±0.0301 | 0/10 | 0.2864 | 0/10 ❌ |
| Random Forest | 0.8763±0.0145 | 10/10 | **0.3733** | **0/10** ⚠️ |
| HistGradientBoosting | 0.8020±0.0469 | 2/10 | 0.2006 | 0/10 ❌ |

**關鍵：Random Forest 的 AUROC「贏」（0.876 > 0.846）是 1% prevalence 下的假象——它的
AUPRC 只有 0.373，反而輸給基線的 0.474。** 也就是說，移除 leakage 欄位、再用正確的
指標後，**沒有任何 model 贏過簡單的 `ctx_specific_de` 基線**：在「真的把 13 個已知調控子
推到最前排」這件事上，簡單基線比所有 ML 模型都好。這是一個乾淨的、符合 2025-2026 文獻
共識的負面結果，完整的「leakage × 指標 2×2」討論見
`../results/known_regulator_classifier_README.md`。

T1 的兩個既有嘗試（GenePT、GEARS）都誠實地打不過「訓練集平均 profile」這個基線，
呼應 2025-2026 年文獻共識（Ahlmann-Eltze et al., *Nature Methods* 2025）。詳細討論見
`genept_baseline/`（`../results/genept_baseline_README.md`）與
`gears_model/`（`../results/gears_benchmark_README.md`）。
