# T1-rework 真實 DE 特徵基線 — 結果（微弱正面，但別過度解讀）

**任務：** 跟 `genept_baseline` 完全相同——用被擾動基因的特徵，預測該擾動對下游基因的
反應 profile——**唯一變數是 X 的來源**：把 GenePT 的外部文字嵌入（跟這份資料完全無關的
「這個基因功能是什麼」的通用描述）換成**被擾動基因自己在同一 culture_condition 下的
真實實驗量測值**（`n_cells_target`、`n_guides`、cross-donor/guide correlation、
guide-level robustness、baseline expression 等 10 個特徵，全部來自 `target_cards.csv`，
**刻意不含 `n_total_de_genes`／`ontarget_effect_size` 這類 DE 幅度摘要**——那是 response
本身的摘要，當特徵是 leakage）。

**基線：** 訓練集平均 response profile（完全忽略被擾動的是哪個基因）——跟 `genept_baseline`
用同一個誠實、難打贏的基線。

## 資料來源限制（誠實揭露，影響結果解讀）

本環境沒有 `genept_baseline` 用的密集矩陣 `GWCD4i.DE_stats.h5ad`（~15.6GB，S3-only，
未進 git）。Y 改用已提交的 `metadata/suppl_tables/full_signed_DE/`（只收錄 adj_p<0.1 的
顯著配對），限制在 **前 500 個最常顯著的 landmark 下游基因**，非顯著配對填 0.0（=「沒偵測
到顯著變化」的合理 floor，不是捏造值，但比密集矩陣粗）。所以這裡的數字**不能直接跟
`genept_baseline` 的 ~0.18 相提並論**——landmark 集、0-floor、response 維度都不同，是
兩個不完全可比的設定；能比的是**各自「有沒有贏過自己的均值基線」**。

## 結果（5-fold KFold，target-level，每個 held-out 標的的 predicted vs true profile 的 Pearson r）

| 條件 | 真實特徵 Ridge | 真實特徵 HistGBR | 均值基線 | Ridge 贏基線？ | HistGBR 贏基線？ |
|---|---|---|---|---|---|
| Rest | 0.1030 | 0.0705 | 0.0922 | ✅（+0.011） | ❌ |
| Stim8hr | 0.1087 | 0.0757 | 0.1001 | ✅（+0.009） | ❌ |
| Stim48hr | 0.1083 | 0.0826 | 0.1006 | ✅（+0.008） | ❌ |

完整數字見 `real_features_baseline_benchmark.json`。

## 怎麼誠實解讀這個結果

**跟 GenePT 的對比是有意義的：** `genept_baseline` 的外部文字嵌入在三個條件全部**輸給**
均值基線；這裡換成被擾動基因**自己的真實實驗特徵**後，**Ridge 在三個條件都微幅贏過**
均值基線。這是一個方向性的訊號——「基因自己的實驗量測（有多少細胞、guide/donor 一不
一致、baseline 表現量多少）」確實比「基因功能的通用文字描述」更能預測它的下游反應
profile，即使只多一點點。這符合直覺，也是一個乾淨的對照實驗結論。

**但這個「贏」小到不該被當成突破：**

1. **margin 只有 +0.008 ~ +0.011**，而且**絕對相關性只有 ~0.10**——模型解釋的變異量
   非常低，離「可用的預測器」還很遠。這是「基線之上有一絲可辨識的訊號」，不是
   「學到了擾動特異性」。
2. **只有 linear（Ridge）贏，非線性的 HistGBR 反而輸給基線**（0.07-0.08 < 0.09-0.10）
   ——這通常代表可用的訊號非常淺（近乎線性、且弱到非線性模型的額外彈性只會過擬合
   雜訊）。跟 T2 的情況剛好相反（那裡是 Random Forest 贏、linear 輸），說明「哪個
   模型家族適合」完全取決於任務，沒有普適的贏家。
3. **landmark-500 + 0-floor 的設定本身偏簡單。** 因為大多數 (target, landmark) 配對
   都是 0（未達顯著），Y 矩陣很稀疏，均值基線本身就抓到了「大部分基因不太動」這個
   共享結構——在這種設定下贏基線的門檻，跟密集矩陣、全基因組的設定不一樣，數字
   不能外推到「全基因組 profile 預測」。

## 誠實的下一步（不在本次做）

- 若之後能取得密集的 `GWCD4i.DE_stats.h5ad`，用跟 `genept_baseline` **完全相同的
  response 矩陣**重跑這個真實特徵版本，才能做真正 apples-to-apples 的「real features
  vs GenePT embedding」對比（目前受限於 landmark-500/0-floor，只能各自跟自己的基線比）。
- 這個 +0.01 的微弱訊號值不值得繼續，取決於它在密集設定下是否還在——很可能會被更強的
  密集均值基線吸收掉。誠實的預期是：**這是一個「方向對、但幅度可能不穩」的觀察，
  不是一個站得住腳的預測能力宣稱。**

跟本目錄所有 ML 探索一樣，這個結果只寫進 benchmark report，不進 `target_cards.csv` 或
readiness。
