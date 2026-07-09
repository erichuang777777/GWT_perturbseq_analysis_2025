# 動力學原型 + 臨床避雷清單（idea 3 & 4，皆不需 GB10）

## idea 3 — 動力學原型（kinetic archetypes）
用三時間點 DE 廣度（Rest→Stim8hr→Stim48hr）把 1,235 標的分型，回答「標的在活化的**哪個階段**起作用」：
- **早期瞬態**（273）：8hr 峰、48hr 回落 — 如 CD3E, MYC
- **晚期持續**（464）：48hr 最高 — 如 STAT6, GATA3, IKBKB
- **刺激開關**（6）：Rest 沉默、Stim 暴增
- 其他（482）/ unknown（10）

意義：決定「什麼時候給藥」——早期瞬態標的適合急性介入，晚期持續適合維持治療。

## idea 4 — 臨床避雷清單（clinical avoid-list）
用三個獨立風險訊號標記**不該碰**的標的（去風險工具，餵給 Entry B 臨床端）：
1. **泛效應**：breadth top 10% → 敲低影響太廣、脫靶毒性風險
2. **高遺傳約束**：LOEUF < 0.35 → 人類演化不容忍失去
3. **劑量敏感**：pLI ≥ 0.9 → haploinsufficient

分層：clear 1,111 / caution 97 / high_risk 12 / avoid 15。

**27 個 ≥2 風險訊號** 為避雷候選。最高風險（三旗全中）：MED12（LOEUF 0.10 / pLI 1.0）、SETDB1、SMARCA5、SMG1、ARF1、CREBBP 等——皆為染色質/必需基因，生物學上重要但不可成藥。

## 誠實邊界
- 動力學型基於 DE **廣度**形狀，非 per-gene signed 軌跡；真正的方向性動力學需任務 A。
- 避雷清單為風險**篩選輔助**，非臨床禁忌判定；最終需個案評估。
- 兩者皆為聚合層分析，GB10 全量 signed 矩陣回來後可精化。

見 `target_master_table.csv`（1,235 標的 × 遞送/極性/動力學/避雷全軸）。
