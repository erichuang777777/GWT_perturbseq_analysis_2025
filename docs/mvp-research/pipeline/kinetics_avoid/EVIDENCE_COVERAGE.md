# 外部證據覆蓋補齊（gnomAD 6% → 97%）

## 問題
先前 gnomAD LOEUF/pLI 只覆蓋 71/1,235（6%）——因為用 **per-gene API 抓取**（~8s/基因，1,235 個需 90 分鐘，被中止）。

## 解法：bulk 下載，而非更快 crawl
gnomAD v2.1.1 by-gene 約束表（單檔 4.6MB，含全基因組 `oe_lof_upper`=LOEUF + pLI）。
- gene symbol 直接映射：6% → 94%
- Ensembl ID 橋接改名基因（NSD2=WHSC1、H2AZ1=H2AFZ、GBA1=GBA…）：94% → **97%**
- 最終仍缺 37/1,235：gnomAD 確無記錄（粒線體編碼 ATP5*、新命名小 ORF），非抓取失敗——**這是該軸的真天花板**

## 各軸最終覆蓋（1,235 gate 標的）
| 證據軸 | 覆蓋 | 來源 |
|---|---|---|
| 極性（煞車/油門）| 100% | 內生 n_up/n_down |
| 動力學原型 | 99% | 內生三時間點 |
| gnomAD LOEUF/pLI | **97%** | bulk 下載（本次補齊）|
| 遞送模態 | 28%（有 ADC 註記者）| 本地 ADC server |
| context-specific | 96 個 | 概念模組 + stimulation-gated |

## 覆蓋提升揭露隱藏風險
避雷清單 ≥2 風險訊號：**27 → 387**。之前不是「風險低」，是「大多數基因缺 LOEUF 無法評估」。新揭露的高風險中 29 個是 context-specific 免疫標的（VAV1/STAT3/NFKB1/BCL10…）——真實生物學：好的免疫標的往往遺傳約束高。

## 誠實邊界
- 用 gnomAD **v2.1.1**（by-gene 表最穩定完整）；v4.1 的等價單檔在 bucket 中路徑未發布為 flat TSV。LOEUF 定義一致。
- 遞送模態覆蓋仍受 ADC server 註記限制（本地資產範圍），非可用 bulk 補齊者。
- 這是**外部證據**覆蓋，與任務 A（內生 per-gene signed DE）是兩回事——後者仍需 GB10。
