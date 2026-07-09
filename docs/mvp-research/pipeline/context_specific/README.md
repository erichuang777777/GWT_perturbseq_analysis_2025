# Context-specific 標的短名單

**日期：** 2026-07-09 · **來源：** 1,235 gate-passing 標的（真實 GWT DE 統計 + concept_annotation 模組標註）

## 篩選邏輯（對齊平台複查 §3.1 + 雲端 concept_annotation.py）
單看「DE 基因廣度」會把泛效應的染色質/代謝敲低推到頂端、埋掉免疫調控子。本短名單改用 **context-specificity** 篩選：

一個標的入選 context-specific 短名單，若滿足任一：
1. **stimulation_gated = True** — Rest 靜息（≤50 DE）但 Stim 活化（≥500 DE），即敲低表型只在 T 細胞活化時顯現（72 個）
2. **屬 ≥1 CD4 免疫概念模組**（35 個）

排序：先 concept 模組數，再 context-specific DE 廣度（Stim − Rest）。

## 結果：96 個 context-specific 候選 / 1,235

短名單乾淨地回收了已知 CD4 T 細胞調控架構：
- **TCR 訊號體**：CD3E, LAT, PLCG1, VAV1, CD247, BCL10, ITK, CD28, MALT1
- **Th 分化 TF**：STAT6, IL4R, STAT3, GATA3, TBX21
- **共刺激**：ICOS, CD28

### 模組分佈（Top 命中）
- TCR_Proximal_Signaling: 6
- IFN_Response: 4
- Th2_Polarization: 4
- NFkB_Axis: 4
- Metabolic_Switch: 3

## Top 20（依 context-specific DE 廣度）
| 基因 | 概念模組 | stim-gated | Rest→Stim8hr→Stim48hr DE | LOEUF | 可成藥性 |
|---|---|---|---|---|---|
| CD3E | TCR_Core_Receptor | ✓ | 4→5711→1586 | 0.7007847405093005 | 10 |
| LAT | TCR_Proximal_Signaling | ✓ | 4→5536→3187 | n/a | 7 |
| PLCG1 | TCR_Proximal_Signaling | ✓ | 3→5033→2218 | 0.4865636818969194 | 7 |
| VAV1 | TCR_Proximal_Signaling |  | 70→4898→3575 | 0.3444029706478581 | 5 |
| CD247 | TCR_Core_Receptor | ✓ | 5→4330→828 | 0.6885845464824588 | 6 |
| BCL10 | TCR_Proximal_Signaling | ✓ | 1→3456→2980 | 0.5462126708195334 | — |
| ITK | TCR_Proximal_Signaling | ✓ | 2→3393→2566 | 0.6583348217168689 | — |
| LRBA | nan | ✓ | 5→2993→223 | 0.6044274850704704 | — |
| FITM2 | nan | ✓ | 21→2607→336 | 1.0450714524369302 | — |
| SLC3A2 | nan | ✓ | 3→2492→52 | 0.8854389501607435 | — |
| ACLY | nan | ✓ | 13→1321→2432 | 0.400071926771869 | — |
| CALCOCO2 | nan | ✓ | 5→2352→484 | 0.8696402064773731 | — |
| TMX1 | nan | ✓ | 1→2347→1960 | 0.953116590555264 | — |
| NDUFAF3 | nan | ✓ | 6→3→1923 | 1.3390337239482806 | — |
| MTG1 | nan | ✓ | 10→8→1894 | n/a | — |
| GRSF1 | nan | ✓ | 2→22→1849 | 1.238268357002918 | — |
| CD28 | Costimulation | ✓ | 5→1506→1798 | 0.6754854307844184 | — |
| MALT1 | TCR_Proximal_Signaling | ✓ | 3→1640→1412 | 0.5559133450604872 | — |
| POLG | nan | ✓ | 40→266→1601 | 0.8291352903695456 | — |
| UBE2E2 | nan | ✓ | 4→1524→128 | 0.4786828092559536 | — |

## 誠實邊界
- 篩選用的 stimulation_gated / concept module 標註為描述性，不進 readiness 決策（守 `unknown != 0`）。
- LOEUF / 可成藥性有缺值（gnomAD 無記錄 / OT 未取得），顯示 n/a 不補 0。
- 這是**基於既有 DE 廣度統計**的 context-specific 篩選；真正的 per-gene signed DE 矩陣需任務 A（GB10 + OAK）才有，屆時可再精化。
