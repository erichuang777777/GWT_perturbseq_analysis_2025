# T2 已知調控子分類器 — 結果（真正的正面發現，通過 leakage 稽核）

**任務：** `benchmark_results.csv` 的 `truth_class`（13 個 `positive`、1 個 `negative`
[HPRT1]、1,211 個 `rest`/未標註）能否被一個監督式分類器學出來，且贏過現有的簡單
排序基線（只用 `ctx_specific_de` 排序，README 記載 AUROC 0.85）？

**資料：** 標籤來自 `methodological_validation/benchmark_results.csv`；特徵來自
`kinetics_avoid/target_master_table.csv`（100% 覆蓋 1,225 個標籤基因）+
`target_cards.csv`（v2, 39 欄，聚合到 gene 粒度）。

## Leakage 稽核（本次實驗的核心，不是選配步驟）

用 CD3E 的真實數字核對過 `ctx_specific_de = max(|de_Stim8hr-de_Rest|, |de_Stim48hr-de_Rest|)`
的公式（de_Rest=4, de_Stim8hr=5711, de_Stim48hr=1586 → 5707，與 `ctx_specific_de`
完全吻合）。因此把候選特徵分成兩組，**分別跑一次完整比較**：

- **full**（43 欄）：含 `de_Rest/de_Stim8hr/de_Stim48hr/breadth_max_de/is_ctx_specific`
  （公式字面輸入）與 `n_concept_modules`（與正類名單怎麼被選出來相關，README 自述
  27 個 canonical positive 裡有 12 個本來就出現在 platform 的 concept 模組標註中）。
- **ablated**（37 欄）：排除上述 6 欄，只留 gnomAD constraint、guide-level
  robustness、實驗設計 metadata、獨立相似度分數、druggability 分類等**跟 DE 幅度
  公式無直接代數關係**的量。

**只有 ablated 的結果才是誠實答案**——一個模型如果只在 full 贏、ablated 就輸回基線，
代表它贏的是「把 `ctx_specific_de` 換個包裝」，不是新訊號。

## 結果（10x 重複 5-fold StratifiedKFold，因為只有 13 個正類，單次切分雜訊太大）

基線（`ctx_specific_de` 排序，本次重新計算，跟 README 記載的 0.85 一致，驗證任務框架
無誤）：**AUROC = 0.8458**

| 模型 | full AUROC | full 贏基線次數 | **ablated AUROC** | **ablated 贏基線次數** | 結論 |
|---|---|---|---|---|---|
| Logistic Regression（linear） | 0.9174±0.0040 | 10/10 | **0.7595±0.0301** | **0/10** | ❌ 未在 ablated 存活——full 的贏是 leakage 假象 |
| Random Forest（ML） | 0.9469±0.0027 | 10/10 | **0.8763±0.0145** | **10/10** | ✅ **贏了且在 ablated 依然贏，10/10 次全贏——真訊號** |
| HistGradientBoosting（ML） | 0.9503±0.0051 | 10/10 | **0.8020±0.0469** | **2/10** | ❌ 未在 ablated 穩定存活（僅 2/10 次贏，且標準差是三者中最大） |

完整數字（含每次重複的個別 AUROC、被排除的 100%-missing 欄位 `n_donors`）見
`known_regulator_classifier_benchmark.json`。

## 這是本次探索目前為止唯一一個通過誠實稽核的正面結果

跟 `genept_baseline`（T1，全部輸）、`gears_model`（T1，全部輸）不同，**Random Forest
在排除所有跟 `ctx_specific_de` 公式直接相關的欄位後，仍然穩定贏過現有的簡單排序基線**
（0.876 vs 0.846，10 次獨立切分全贏，標準差只有 0.015）——這代表 gnomAD constraint、
guide-level robustness（cross-donor/guide correlation、guide FDR/signif ratio）、
druggability 分類這類**跟 DE 幅度公式無關的特徵組合**，確實承載了「這是不是已知調控子」
的一部分獨立訊號，不是單純重述 `ctx_specific_de` 本身。

**但這不是「已知調控子分類已解決」的結論，只是「這個方向值得繼續」的訊號**——原因：

1. **正類只有 13 個。** 即使跨 10 次獨立切分結果一致，13 個正類的統計把握度天生有限；
   這是一個小樣本下的穩健觀察，不是大樣本確證的結論。
2. **負類幾乎不存在（只有 1 個 HPRT1）。** `y=0` 實際上是「rest（未標註）+ 唯一 1 個
   確認負類」——任務的操作型定義完全比照現有基線（README 自己承認的
   「positives vs rest」框架），不是傳統平衡二分類。如果 `rest` 裡混有未被發現的
   真正調控子，這個 AUROC 會被低估；如果 `rest` 裡混有被現有 pipeline 錯誤放行的
   假警訊，AUROC 會被高估——兩個方向的誤差都無法用現有標籤量化。
3. **只做了單一模型家族的超參數（`n_estimators=300`, `class_weight="balanced_subsample"`,
   `random_state` 系列固定）**，沒有調參搜索——這是誠實的「第一輪驗證」，不是「已經
   榨乾這個方向的所有訊號」。
4. **Logistic Regression 和 HistGradientBoosting 都沒有穩定贏**，說明這個訊號不是
   隨便換個模型都找得到的——Random Forest 的隨機子空間+子抽樣特性可能剛好適合這種
   「多個弱、非線性、有缺失值的特徵組合出一個訊號」的場景，但這也代表這個發現
   對模型選擇敏感，不是一個放諸四海皆準的訊號。

## 誠實的下一步（不在本次做，留給後續）

- 用一組完全獨立的 held-out 已知調控子（不是這 13 個，例如從另一個資料庫或另一輪
  文獻篩選）驗證 Random Forest 的排序是否仍然贏基線——這是唯一能排除「13 個正類
  剛好對這組特徵友善」這個過擬合疑慮的方法。
- 對 Random Forest 做 feature importance 分析，看看到底是哪些 SAFE 特徵在驅動這個
  訊號（gnomAD constraint？guide robustness？druggability 分類？），才能把這個發現
  轉成一個可解釋、可驗證的生物學假設，而不只是一個黑盒分數。
- 目前這個結果**只寫在這份 benchmark report 裡，不寫入 `target_cards.csv` 或
  readiness**——跟 repo 既有的所有 ML 探索一樣，這是研究發現，不是驗證過的產品功能。
