# GenePT 風格基線 — 結果（誠實負面結果）

**任務：** 給定被擾動基因的 GenePT ada-002 文字嵌入（PCA 降到 128 維，
與被擾動基因本身的實驗數據完全無關，純粹是「這個基因功能是什麼」的
文字描述嵌入），用 multi-output Ridge regression 預測該擾動對全部
~10,185 個下游基因的 log_fc 表現變化 profile。

**資料：** `metadata/suppl_tables/full_signed_DE/` 背後的原始 dense
`GWCD4i.DE_stats.h5ad`（非只有顯著命中——這裡刻意用完整、連續的 log_fc
值，見 `genept_baseline/build_gene_features.py` 的說明）。分別對
Rest / Stim8hr / Stim48hr 三個條件獨立訓練評估，各 ~11,100-11,300 個
標的、5-fold KFold（target-level，同一標的不會同時在 train/test）。

## 結果

| 條件 | GenePT-Ridge 平均 r | 均值基線平均 r | 模型贏了嗎 |
|---|---|---|---|
| Rest | 0.1787 | 0.1823 | ❌ 沒有 |
| Stim8hr | 0.1914 | 0.1943 | ❌ 沒有 |
| Stim48hr | 0.1673 | 0.1699 | ❌ 沒有 |

**結論：GenePT 嵌入 + Ridge regression 在三個條件都沒有打贏「訓練集
平均 response profile」這個簡單基線。**

完整數字見 `genept_baseline_benchmark.json`（含 median、NaN 計數等）。

## 這是 bug 嗎？不是——這是誠實結果，且符合當前文獻共識

2025-2026 年多篇基準測試論文（最顯著的是 Ahlmann-Eltze, Huber, Anders,
*Nature Methods* 2025：「Deep-learning-based gene perturbation effect
prediction does not yet outperform simple linear baselines」）反覆證實：
**用基因身分/嵌入去預測未見過擾動的表現變化 profile，目前的模型
（不論深度學習或簡單迴歸）大多打不過訓練集平均值這個基線**——因為
bulk/pseudobulk 層級的擾動反應中，「大部分擾動看起來都差不多」這個
共享訊號本身就占了 profile 變異的一大部分，個別基因身分帶來的邊際
訊息很有限，尤其是像 GenePT 這種**完全不依賴目標基因自身實驗數據**
的通用文字嵌入。

**本專案既有的 `src/3_DE_analysis/perturbation_prediction_ml.py`**
测的是完全不同、也容易很多的任務（用同一個標的另外兩個已知條件的
「自己的」實驗量測值去預測第三個條件，均值基線本身就有 Pearson r≈0.93）
——那是「用自己的其他量測預測自己」，這裡是「用基因功能的通用描述
預測從沒直接量測過的完整下游 profile」，後者本質上難得多，數字不能
直接比較。

## 誠實的下一步（不在本次做，留給後續）

- 均值基線贏，不代表「基因身分無用」，可能代表：(1) 128 維 PCA 砍太多
  資訊、(2) Ridge 的線性假設太簡單、(3) 需要更貼近目標基因所屬通路/
  網路鄰居的資訊（GEARS 用 GO 知識圖譜正是想解決這個——見
  `../gears_model/`）、(4) 需要把「哪些基因會被顯著影響」拆成獨立的
  二元分類子任務（文獻建議的兩階段做法：先分類「有沒有反應」，
  再對有反應的做回歸），而不是一次回歸整個 10,185 維 profile。
- 這些都是可以驗證的假設，但每一個都要重新誠實跑一次基準測試，
  不能因為第一版打輸就調整到贏為止（那是 p-hacking，不是誠實探索）。
