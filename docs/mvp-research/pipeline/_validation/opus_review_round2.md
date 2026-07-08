# Opus 第二輪確認複查報告

> GWT CD4⁺ T Perturb-seq 標的發現 MVP · 文件層兩輪複查最終確認
> 審查者：獨立資深審查者（Opus，第二輪）
> 日期：2026-07-08
> 範圍：確認第一輪 3 個文件描述層警告的修正是否解決，且未引入新矛盾

---

## 一、複查方法

本輪為**確認性複查**：讀取全部 4 份修正後文件（05/06 README、data_dictionary、README_03），
並**實際載入 3 份 CSV**（effect_matrix、summary_statistics、curated_targets）驗證維度描述與真實資料一致，
最後交叉對照 06 與 05 README 對相同靜態圖的資料歸屬是否一致。

實測資料維度（本輪親自載入驗證）：

| 檔案 | 實測維度 | 欄位 |
|---|---|---|
| effect_matrix.csv | **(11526, 4)** | `target_contrast_gene_name`, `Rest`, `Stim8hr`, `Stim48hr` |
| summary_statistics.csv | (18, 2) | `metric`, `value`（18 個全域指標，無逐標的欄位） |
| curated_targets.csv | (33983, 18) | 33,983 列 = 11,526 標的 × 3 條件 |

---

## 二、逐個 warn 確認結果

### Warn 1 — 05_visualization README 參考文獻標題誤植 → ✅ 已解決

- 第 4 節參考文獻第 1 條已改為真實標題：
  「Genome-scale perturb-seq in primary human CD4+ T cells maps context-specific
  regulators of T cell programs and human immune traits」，作者標為 Zhu R., Dann E. et al. (2025), *bioRxiv*。
- **未補 DOI**：修正者判斷原 `10.64898` 前綴不符 bioRxiv `10.1101` 慣例、且無可查證來源，故留白。
  **本審查者認可此誠實判斷**——寧可缺一個無法查證的 DOI，也不應臆造或硬填一個可疑前綴的識別碼。這符合資料誠信原則。
- 全文其餘出現的引用（data_dictionary、README_03 的參考文獻段）均使用一致的簡短格式，無標題矛盾。

### Warn 2 — 06_animation 逐標的動畫來源誤標 04_statistical → ✅ 已解決

- 06 README 動畫清單中，所有**逐標的**動畫（anim01/03/04/05/07/08/09/10）現一律標為
  **02_curated（curated_targets.csv，逐標的/逐列）**，並在需門檻或最終計數標註處註明
  「summary_statistics.csv 僅供門檻/標註」。
- 兩個**條件層**動畫（anim02 條件補間 dot plot、anim06 長條競賽）正確標為 **03_processed (condition_stats)**。
- **已無任何動畫錯標 04_statistical 為逐標的資料來源。**
- 修正理由與本輪實測相符：summary_statistics.csv 僅 18 列全域 metric、無逐標的欄位，
  確實不可能是逐標的動畫的資料來源。

**06 與 05 對相同靜態圖的歸屬一致性（交叉核對）：**

| 動畫 | 對應 05 靜態圖 | 05 標註來源 | 06 標註來源 | 一致性 |
|---|---|---|---|---|
| anim01 Lollipop | R1 Lollipop | 02_curated + 04_statistical | 02_curated（逐標的）+ summary 標註 | 一致 |
| anim03 QC 漏斗 | C3 QC funnel | 02_curated + 04_statistical | 02_curated（逐列篩選）+ summary 標註 | 一致 |
| anim04 泡泡 | R5 Bubble | 02_curated（逐列） | 02_curated（逐標的） | 一致 |
| anim05 ECDF | D5 ECDF | 02_curated + 04_statistical | 02_curated（逐標的）+ summary 標註 | 一致 |
| anim07 相關熱圖 | M1 相關性熱圖 | 02_curated（逐列） | 02_curated（欄位相關） | 一致 |
| anim08 3D UMAP | V3 UMAP | 02_curated（逐列） | 02_curated（逐標的降維） | 一致 |
| anim09 瀑布 | R4 Waterfall | 02_curated + 04_statistical | 02_curated（逐標的） | 一致（06 略去 04 標註，非衝突） |
| anim10 分歧長條 | R2 Diverging bar | 02_curated + 03_processed | 02_curated（逐標的 n_up/n_down） | 一致 |

兩份 README 對「逐標的資料來自 02_curated、summary_statistics 僅供全域標註」的定位完全一致，**無殘留衝突敘述**。

### Warn 3 — pivot 維度 11,526×3 → 11,526×4 → ✅ 已解決（且經實測驗證正確）

- data_dictionary.md 與 README_03_processed.md 均已改為
  **11,526 × 4（1 個 index 欄 `target_contrast_gene_name` + 3 個條件值欄 Rest/Stim8hr/Stim48hr）**。
- **本輪實際載入 effect_matrix.csv：shape = (11526, 4)，欄位恰為 1 個標的名欄 + 3 個條件欄。**
  修正後描述與真實檔案完全相符——確認是「改正確」而非「又改錯」。
- de_matrix.csv 依相同 pivot 邏輯產生，兩份文件對其描述亦為 11,526 × 4，結構一致。

---

## 三、有無新引入的問題

**無。** 本輪逐項檢查修正是否帶來新矛盾：

- 05 參考文獻標題修正：未影響文中其他數字或敘述；引用格式跨文件一致。
- 06 來源歸屬修正：改後與 05 完全一致，且未動搖第四節「資料誠信註記」（anim04 假火山圖修正、anim08 UMAP 解讀）之正確內容。
- 維度修正：data_dictionary 與 README_03 兩處措辭完全一致，且與 CSV 實測相符；summary_statistics 的 18 個指標描述與實測 18 列吻合。
- 全域統計數字（33,983 列 / 11,526 唯一標的 / 2,131 通過門檻列 / 1,235 唯一標的）在 05、data_dictionary、README_03 三處交叉一致。

---

## 四、最終判定

| 項目 | 結果 |
|---|---|
| Warn 1（參考文獻標題） | ✅ 已解決 |
| Warn 2（動畫來源歸屬） | ✅ 已解決，06/05 一致無衝突 |
| Warn 3（pivot 維度） | ✅ 已解決，經實測驗證正確 |
| 新引入問題 | 無 |
| 資料層錯誤（第一輪即 0） | 維持 0 |

### 判定：**pipeline 通過兩輪複查（PASS）**

第一輪找到的 3 個文件描述層警告已全數修正，修正內容經本輪實際載入資料驗證屬實，
且未引入任何新矛盾。文件層與資料層描述一致、跨文件數字互洽。
就文件正確性與資料誠信而言，本 pipeline 通過兩輪獨立複查。
