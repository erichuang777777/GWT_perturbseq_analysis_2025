# T2 已知調控子分類器 — 結果（誠實負面：AUPRC 推翻了 AUROC 的假象）

**任務：** `benchmark_results.csv` 的 `truth_class`（13 個 `positive`、1 個 `negative`
[HPRT1]、1,211 個 `rest`/未標註）能否被一個監督式分類器學出來，且贏過現有的簡單
排序基線（只用 `ctx_specific_de` 排序）？

**資料：** 標籤來自 `methodological_validation/benchmark_results.csv`；特徵來自
`kinetics_avoid/target_master_table.csv`（100% 覆蓋 1,225 個標籤基因）+
`target_cards.csv`（v2, 39 欄，聚合到 gene 粒度）。

## ⚠️ 為什麼一定要同時看 AUPRC（本次最重要的方法學修正）

正類 prevalence 只有 **13/1225 ≈ 1.06%**。在這種極端不平衡下，**AUROC 會過度樂觀**：
負類有 1,212 個，false-positive-rate 的分母極大，所以模型只要在排序尾端稍微把正類
往前挪一點，AUROC 就會漂亮地上升——即使它**根本沒有把那 13 個正類真的推到最前排**。

**AUPRC（precision-recall 曲線下面積 / average precision）才是對稀有正類誠實的指標**：
它直接衡量「排在前面的到底是不是正類」，而且它的「無資訊參考線」= prevalence ≈ 0.0106
（不像 AUROC 的參考線恆為 0.5，跟稀有度無關）。現有基線的
`methodological_validation/README.md` 本來就有報 average precision 0.47，所以加 AUPRC
對照也是 apples-to-apples。

## Leakage 稽核（本次實驗的第二個核心）

用 CD3E 的真實數字核對過 `ctx_specific_de = max(|de_Stim8hr-de_Rest|, |de_Stim48hr-de_Rest|)`
的公式（de_Rest=4, de_Stim8hr=5711, de_Stim48hr=1586 → 5707，完全吻合）。因此把候選
特徵分成兩組分別跑：**full**（含公式字面輸入 `de_Rest/de_Stim8hr/de_Stim48hr/
breadth_max_de/is_ctx_specific` 與標籤相關的 `n_concept_modules`）與 **ablated**（排除
上述 6 欄）。**只有 ablated × AUPRC 才是誠實答案。**

## 結果（10x 重複 5-fold StratifiedKFold；13 個正類，單次切分雜訊太大）

基線（`ctx_specific_de` 排序）：**AUROC = 0.8458，AUPRC = 0.4744**（AUPRC 無資訊參考線 ≈ 0.0106）

### full（含 leakage 欄位）

| 模型 | AUROC | 贏基線 | AUPRC | 贏基線 |
|---|---|---|---|---|
| Logistic（linear） | 0.9174±0.0040 | 10/10 | 0.5043±0.0831 | 6/10 |
| Random Forest（ML） | 0.9469±0.0027 | 10/10 | 0.7458±0.0344 | 10/10 |
| HistGBR（ML） | 0.9503±0.0051 | 10/10 | 0.6408±0.0690 | 10/10 |

### ablated（排除 leakage 欄位）← **誠實答案**

| 模型 | AUROC | 贏基線 | **AUPRC** | **贏基線** | 裁決 |
|---|---|---|---|---|---|
| Logistic（linear） | 0.7595±0.0301 | 0/10 | 0.2864±0.0282 | **0/10** | ❌ 兩指標都輸 |
| Random Forest（ML） | 0.8763±0.0145 | 10/10 | **0.3733±0.0480** | **0/10** | ⚠️ AUROC 贏但 **AUPRC 輸**——AUROC 是假象 |
| HistGBR（ML） | 0.8020±0.0469 | 2/10 | 0.2006±0.0438 | **0/10** | ❌ 兩指標都輸 |

完整數字（每次重複的個別 AUROC/AUPRC、被排除的 100%-missing 欄位 `n_donors`）見
`known_regulator_classifier_benchmark.json`。

## 結論：移除 leakage + 看正確的指標後，沒有任何 model 贏過簡單基線

**這推翻了本檔先前版本的「Random Forest 是通過稽核的真訊號」的說法**，而且推翻它的正是
使用者指出該補的 AUPRC：

- Random Forest 在 ablated 集上 **AUROC 0.876 > 基線 0.846（10/10 贏）**，乍看是真訊號。
- 但它的 **AUPRC 只有 0.373 < 基線 0.474（0/10 贏）**。也就是說——RF 只是在 1,212 個
  負類的排序尾端稍微好一點（撐高了對稀有度不敏感的 AUROC），**但在「真的把那 13 個
  已知調控子推到最前排」這件事上，簡單的 `ctx_specific_de` 排序反而比所有 ML 模型都好。**
- 這正是 AUROC 在 1% prevalence 下的典型陷阱，也正是這次探索最有價值的方法學教訓：
  **在極端不平衡的排序任務上，只報 AUROC 會製造出「ML 贏了」的假象；補上 AUPRC 後，
  真實答案是誠實負面——簡單基線目前無法被這批特徵 + 這些模型打敗。**

這跟 `genept_baseline`（T1）、`gears_model`（T1）的方向一致：**三個不同任務、五個不同
模型，移除 leakage、用對指標之後，都沒有穩定贏過各自的簡單基線**——這本身就是符合
2025–2026 基準測試文獻共識的、可靠的負面發現，不是失敗。

## 一個乾淨的教學對照：leakage × 指標的 2×2

| | AUROC | AUPRC |
|---|---|---|
| **full（含 leakage）** | RF/HistGBR 贏（0.95）| RF/HistGBR 贏（0.75/0.64）|
| **ablated（無 leakage）** | RF「贏」0.876（**假象**）| RF 輸 0.373（**真相**）|

只有把「移除 leakage 特徵」與「改用 prevalence-appropriate 指標」**兩件事都做**，才會
看到誠實答案。少做任何一件，都會得到「ML 贏了」的錯誤樂觀結論。

## 誠實的下一步（不在本次做，留給後續）

- 這個負面結果不代表「基因身分/特徵永遠無用」，而是「這批特徵 + 這些現成模型，在
  這個 1% prevalence 的排序任務上，贏不過那個剛好很強的 `ctx_specific_de` 基線」。
  值得試的變體：只用真正獨立的 SAFE 特徵子集（gnomAD constraint + guide robustness）
  做 feature-importance 導向的建模，看有沒有哪一小組特徵能在 AUPRC 上贏基線。
- 用一組完全獨立的 held-out 已知調控子（不是這 13 個）驗證——排除「13 個正類剛好
  對某組特徵友善」的過擬合疑慮。
- 目前這個結果**只寫在這份 benchmark report 裡，不寫入 `target_cards.csv` 或
  readiness**——跟 repo 既有的所有 ML 探索一樣，這是研究發現，不是驗證過的產品功能。
