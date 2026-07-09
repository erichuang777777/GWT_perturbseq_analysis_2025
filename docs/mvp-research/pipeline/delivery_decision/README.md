# 免疫藥物遞送決策層（Delivery Decision Layer）

**日期：** 2026-07-09 · **不需 GB10** · **資料：** GWT 1,235 gate 標的 × 本地 ADC server 遞送註記 × 聚合極性

## 這是什麼 —— 換框，不是加功能
現有排名回答「哪個基因**重要**」；本層回答「哪個標的**今天能做成哪種藥、往哪個治療方向**」。
把三個既有訊號交叉：
1. **重要性** — context-specific（stimulation-gated OR 免疫概念模組），96/1,235
2. **可遞送性** — 分子位置決定藥物模態（本地 ADC server：is_surface_protein / extracellular_domain / druggable_pathway，與 GWT 重疊 604/1,235）
3. **方向性** — 聚合極性（n_up/n_down）：敲低後下游主要上調=煞車(免疫放大)、主要下調=油門(免疫壓制)。**100% gate 標的可算，不需 GB10。**

## 模態分類規則
- **CAR-T / ADC / 抗體** = 細胞表面 + 有胞外域（extracellular_length≥20aa）
- **抗體** = 表面但胞外域有限
- **小分子** = 胞內可成藥口袋（kinase/protease/enzyme pathway 或 druggable 非表面）
- **待新模態** = 無已知遞送方式（誠實標記，不強行歸類）

## 結果：96 context-specific 中 39 個今天可遞送

| 模態 | 數量 |
|---|---|
| CAR-T / ADC / 抗體（表面）| 18 |
| 抗體（表面胞外有限）| 6 |
| 小分子（胞內口袋）| 15 |
| 待新模態 | 57 |

### CAR-T / ADC / 抗體 候選（細胞表面）
| 基因 | 極性 | 概念模組 | ctx-DE | LOEUF |
|---|---|---|---|---|
| CD3E | repressor | mod 1 | 5707 | 0.7007847405093005 |
| LAT | repressor | mod 1 | 5532 | n/a |
| CD247 | repressor | mod 1 | 4325 | 0.6885845464824588 |
| SLC3A2 | repressor | mod 0 | 2489 | 0.8854389501607435 |
| TMX1 | mixed | mod 0 | 2346 | 0.953116590555264 |
| CD28 | mixed | mod 1 | 1793 | 0.6754854307844184 |
| ORAI1 | repressor | mod 0 | 1247 | n/a |
| CD5 | mixed | mod 0 | 1193 | n/a |
| RNFT2 | mixed | mod 0 | 1075 | n/a |
| CD2 | mixed | mod 0 | 985 | n/a |
| NDFIP2 | repressor | mod 0 | 833 | n/a |
| IL4R | mixed | mod 1 | 726 | n/a |
| ICOS | repressor | mod 2 | 669 | n/a |
| IL23R | mixed | mod 1 | 256 | n/a |
| IFNGR1 | mixed | mod 1 | 109 | n/a |
| IFNGR2 | activator | mod 1 | 66 | n/a |
| IFNAR1 | activator | mod 1 | 11 | n/a |
| IL7R | activator | mod 1 | 0 | n/a |

### 小分子候選（胞內可成藥）
| 基因 | 極性 | 概念模組 | ctx-DE | LOEUF |
|---|---|---|---|---|
| PLCG1 | repressor | mod 1 | 5030 | 0.4865636818969194 |
| VAV1 | mixed | mod 1 | 4828 | 0.3444029706478581 |
| ACLY | mixed | mod 0 | 2419 | 0.400071926771869 |
| STAT6 | mixed | mod 1 | 1125 | n/a |
| ACACA | mixed | mod 0 | 909 | n/a |
| COQ6 | mixed | mod 0 | 780 | n/a |
| STAT3 | mixed | mod 1 | 668 | n/a |
| MYC | mixed | mod 1 | 637 | n/a |
| INPP5D | repressor | mod 0 | 533 | n/a |
| RPTOR | repressor | mod 1 | 517 | n/a |
| IKBKB | mixed | mod 1 | 292 | n/a |
| SMARCA4 | mixed | mod 1 | 261 | n/a |
| GZMB | repressor | mod 1 | 255 | n/a |
| CCND3 | mixed | mod 1 | 199 | n/a |
| NFKB1 | mixed | mod 1 | 115 | n/a |

### 抗體候選（表面胞外有限）
| 基因 | 極性 | 概念模組 | ctx-DE | LOEUF |
|---|---|---|---|---|
| FITM2 | repressor | mod 0 | 2586 | 1.0450714524369302 |
| HACD2 | mixed | mod 0 | 1420 | 0.7454421044138124 |
| INSIG1 | mixed | mod 0 | 709 | n/a |
| MMGT1 | mixed | mod 0 | 699 | n/a |
| MTCH2 | mixed | mod 0 | 687 | n/a |
| HACD4 | repressor | mod 0 | 542 | n/a |


## 怎麼讀 —— 以 PLCG1 為例
- 現有平台：context-specific top、TCR_Proximal_Signaling 模組、LOEUF 0.487、Angioedema 安全訊號
- 遞送層：胞內酶 → **小分子**模態；極性 repressor → 敲低放大免疫；已知 Angioedema → **小分子而非 CAR-T，需監測血管性水腫**

## 誠實邊界
- 極性為**聚合**方向（整體上/下調比例），非 per-gene signed。真正的方向性相關（哪個下游基因往哪走）仍需任務 A 的 signed 矩陣。
- ADC 遞送註記覆蓋 604/1,235（49%）；缺註記者模態標「待確認」不強分。
- 模態分類為**篩選輔助**，非藥物開發保證——最終需濕實驗驗證表位可及性與功能。
