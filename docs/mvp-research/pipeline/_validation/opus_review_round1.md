# Opus 第一輪全流程複查報告 — GWT Perturb-seq 標的發現 Pipeline

**審查者**：獨立資深審查者（Opus）
**審查範圍**：七階段重整 pipeline（raw→curated→processed→statistical→visualization→animation→dashboard）＋ R 交叉驗證
**審查方式**：以 Python 實際載入原始資料與全部衍生產出，**逐項重算抽查**（非只讀文件）
**日期**：2026-07-08

---

## 總結

- **失敗（fail）：0**
- **警告（warn）：3**（皆為文件層面問題，不影響底層資料正確性）

底層資料與所有數值化產出**完全通過**：33,983 列原始資料、全部衍生欄、pivot 矩陣、門檻子集、18 項摘要統計、條件統計、篩選漏斗與集合大小，皆能從原始檔逐位元重現。R × Python 交叉驗證為**真實逐項比對**，非假通過。發現的 3 個警告全部集中在**文件描述**（一處引用標題錯誤、一處動畫資料來源歸屬錯誤、一處 pivot 維度標示不精確），不涉及任何數字錯誤。

---

## 逐項審查結果

### 1. 資料正確性 — ✅ 通過

實際以 Python 重算抽查，全部吻合：

| 抽查項目 | 定義 | 重算結果 | 檔案值 | 判定 |
|---|---|---|---|---|
| `logDE` | `log10(n_total_de_genes+1)` | 逐列相符（max abs diff 4.4e-16） | — | ✅ |
| `passes_gate` | `(n_cells≥200)&sig&(~offtarget)&(nde≥50)` | 0 筆不符，True=2131 | 2131 | ✅ |
| gate 唯一標的 | 通過門檻列的 `target_contrast` distinct | 1235 | 1235 | ✅ |
| `effect_matrix` pivot | `ontarget_effect_size` 標的×條件 | 與檔案 allclose（含 NaN） | — | ✅ |
| `de_matrix` pivot | `n_total_de_genes` 標的×條件 | 與檔案 allclose（含 NaN） | — | ✅ |
| `gate_passing_targets` | curated 中 `passes_gate=True` 子集 | 行集合（index）完全一致，2131×18 | 2131×18 | ✅ |
| `condition_stats` | 各條件 up/down 加總、唯一標的數 | 三條件三欄全數相符 | — | ✅ |

### 2. 關鍵預期值 — ✅ 通過（18/18 全中）

所有 18 項 `summary_statistics.csv` 數值皆由原始／curated 資料重算，逐項相符：

| metric | 重算值 | 檔案值 | 判定 |
|---|---|---|---|
| n_rows | 33983 | 33983 | ✅ |
| n_unique_targets | 11526 | 11526 | ✅ |
| n_ontarget_significant | 21216 | 21216 | ✅ |
| n_offtarget_flag | 2837 | 2837 | ✅ |
| n_gate_passing_rows | 2131 | 2131 | ✅ |
| n_gate_passing_unique_targets | 1235 | 1235 | ✅ |
| count_Rest / Stim8hr / Stim48hr | 11287 / 11415 / 11281 | 同 | ✅ |
| nde_median / nde_max | 2 / 5920 | 同 | ✅ |
| effect_min / median / max | -58.547977 / -6.304637 / 7.091938 | 同 | ✅ |
| ncells_median | 539 | 539 | ✅ |
| corr_nde_ndownstream | 0.99999847 | 0.99999847 | ✅ |
| frac_logde_lt1 | 0.756143 | 0.756143 | ✅ |
| set_significant_genelevel | 7913 | 7913 | ✅ |

原始檔 **MD5 實測 = `f5cf2e070bc8a2fb2ce0c584b3277c4c`**，與文件記載一致。

### 3. R / Python 等價 — ✅ 通過（真實比對）

`cross_validation_results.csv` 為**逐項真實比對**，非假通過。證據：
- 18 項每項附 R 端計算邏輯（`nrow(de)`、`n_distinct`、`sum`、`median`、`cor(method='pearson')`…），與 Python 定義一致。
- 容差設定合理：整數／中位／極值要求**絕對差=0**（精確相等）；浮點統計（corr、frac）容差 `abs<1e-6`。
- 唯一非零差為 `corr_nde_ndownstream` 的 4.44e-16（浮點機器精度層級，遠低於容差），其餘 17 項絕對差皆為 0。
- 報告明載「R 端統計均由公式直接作用於原始 `de` 資料框，未引用 Python 的 summary 數值」，且說明先印 Python 值再算 R 值以避免「先驗盲算」——方法學誠實。
- `frac_logde_lt1` 的 `log10(x+1)<1 ⇔ x<9` 換算經我重算確認（frac(nde<9)=0.7561，非 <10=0.7683，定義正確）。

### 4. 文件與資料一致 — ⚠️ 大致通過（2 處警告）

- **資料字典欄位 vs 實際 CSV**：raw 16 欄、curated 18 欄、summary（metric,value）、condition_stats 4 欄、gate_passing 2131×18 — 全部與實際檔案相符。✅
- **各層 README 輸入輸出**：01–04、07 的資料流向、維度、欄位描述與實際 artifact 一致。05 視覺化 README 的漏斗計數（33,983→30,515→19,297→16,998→2,131）、UpSet 集合大小（significant 7,913 / passes_gate 1,235 / has_offtarget 1,152 / broad 10）經我重算**全部精確吻合**。✅
- **警告 W2**（見發現清單）：06 動畫 README 的「資料來源階段」欄，把數個逐標的動畫錯歸為 `04_statistical (summary_statistics.csv)`。
- **警告 W3**（見發現清單）：pivot 維度標示為「11,526 × 3」，實際檔案為 11,526 × 4（含 index 欄）。

### 5. 資料來源驗證 — ⚠️ 通過但含 1 處引用錯誤（警告）

- **MD5**：於 data_dictionary、README_01/02/04/07 均記錄 `f5cf2e070bc8a2fb2ce0c584b3277c4c`，且我實測相符。✅
- **S3 桶**：`genome-scale-tcell-perturb-seq`（CZ Biohub 公開）在各文件一致。✅
- **參考文獻**：真實論文標題（經 bioRxiv/SSRN 核實）為
  *"Genome-scale perturb-seq in primary human CD4+ T cells maps context-specific regulators of T cell programs and human immune traits"*（Zhu R., Dann E. et al., 2025, bioRxiv, DOI 10.64898/2025.12.23.696273）。
  - 多數文件（data_dictionary、README_01/02/03/04/07）引用為「*Genome-scale perturb-seq in primary human CD4+ T cells*」——為真實標題的**正確截短前段**，可接受。✅
  - **但 05 視覺化 README 的參考文獻 #1** 標題寫成「*Perturb-seq across CD4⁺ T-cell states maps regulators of activation and differentiation*」——此標題**與真實論文不符，且與專案其餘文件不一致**。作者、年份、venue 正確，但標題錯誤。⚠️（警告 W1）

### 6. 內部矛盾 — ✅ 大致通過（AlphaFold 15 標的坑已避開）

- **AlphaFold 結構數**：05 README 明載「**15 個 AlphaFold 標的**」＝「**5 個 immune ＋ 10 個 broad-effect**」，並逐一列出。15 個基因（含 broad10、immune5）我已確認全數存在於原始資料，且 10 個 broad-effect 全部通過門檻（N3 文氏圖「broad-effect 全落在通過門檻內」之敘述正確）。**未見 15 誤植**。✅
- immune 平均 pLDDT ≈72.8、broad 平均 ≈75.7 — 與逐基因數值自洽。✅
- 效應量範圍（-58.5 ~ 7.1、中位 -6.3）、DE 中位 2／最大 5,920 等敘述在 04/05 README 一致。✅
- 07 儀表板 README 誠實標注 `readiness_engine.py` 不在 artifact store、R0–R5 語意為推論、`_evidence`/`_pathway` 為 15 基因——內部一致，無過度宣稱。✅
- 未發現同一數字在不同文件互相矛盾的情形（除 W2/W3 的來源歸屬與維度標示屬描述精確度問題，非數字衝突）。

---

## 發現清單

| 編號 | 嚴重度 | 位置（檔案） | 問題描述 | 建議修正 |
|---|---|---|---|---|
| **W1** | warn | 05_visualization/README.md（參考文獻 #1） | 論文標題寫成「Perturb-seq across CD4⁺ T-cell states maps regulators of activation and differentiation」，與真實標題（Genome-scale perturb-seq in primary human CD4+ T cells maps context-specific regulators of T cell programs and human immune traits）不符，也與專案其餘文件所用標題不一致。 | 統一改為真實標題（或各文件一致採用的截短版「Genome-scale perturb-seq in primary human CD4+ T cells」），並可補上 DOI 10.64898/2025.12.23.696273。 |
| **W2** | warn | 06_animation/README.md（動畫清單表「資料來源階段」欄） | anim01（lollipop 排名）、anim04（bubble）、anim05（ECDF）、anim07（相關性熱圖）、anim08（UMAP）、anim09（waterfall）、anim10（分歧長條）被標為來源 `04_statistical (summary_statistics.csv)`；但該檔僅 18 列全域 metric（欄位僅 metric,value），無任何逐標的欄位，物理上無法供給這些逐標的／逐列繪圖所需資料。05 視覺化 README 對相同靜態圖正確歸為 02_curated。 | 將這些動畫的資料來源改標為 `02_curated`（逐列資料），summary_statistics.csv 僅作為標註／門檻線來源。與 05 README 的歸屬對齊。 |
| **W3** | warn（低） | data_dictionary.md、README_03_processed.md | effect_matrix / de_matrix 維度標為「11,526 × 3」，實際 CSV 為 11,526 × 4（含 `target_contrast_gene_name` index 欄）。屬 pivot 慣用描述（3=條件值欄），有隨附欄位說明澄清，但嚴格看維度數字與實際不符。 | 標示為「11,526 × 4（index + 3 條件欄）」或明說「3 為條件值欄」以免誤讀。 |

> **附註（非 pipeline 缺陷，屬本次委派輸入）**：委派任務中 `07_dashboard/README` 的 artifact marker 版本 id 結尾為 `…89fea1e08e0f`，實際正確版本 id 為 `5df87462-bdea-46a7-a176-39ee03cd3896`。我已以正確 artifact 完成審查；建議下游更新引用以免連結失效。

---

## 我實際重算的抽查數字對照（節錄）

```
== 原始資料（MD5 f5cf2e070bc8a2fb2ce0c584b3277c4c，33983×16）==
n_ontarget_significant        21216   (預期 21216)  ✅
n_offtarget_flag               2837   (預期  2837)  ✅
count Rest/Stim8hr/Stim48hr   11287/11415/11281      ✅
corr(nde, ndownstream)        0.9999985 (≈1.0)       ✅
set_significant_genelevel      7913   (預期  7913)  ✅

== curated 衍生欄 ==
passes_gate True               2131   (預期  2131)  ✅  0 筆不符
gate unique targets            1235   (預期  1235)  ✅
logDE 逐列                     max diff 4.4e-16       ✅
frac_logde_lt1              0.756143   (預期 0.756)  ✅

== processed pivot ==
effect_matrix / de_matrix     與檔案 allclose        ✅

== 篩選漏斗（05 README 宣稱）==
33983 → 30515 → 19297 → 16998 → 2131   重算全中     ✅

== UpSet 集合（05 README 宣稱）==
significant 7913 / passes_gate 1235 / has_offtarget 1152 / broad 10  全中  ✅

== AlphaFold 15 標的 ==
broad-effect 10 + immune 5，皆存在於資料；broad 10 全數通過門檻  ✅
```

---

## 結論

本輪嚴格複查，**實際重算涵蓋資料層每一個關鍵數字**，未發現任何資料正確性、階段歸屬（數值面）、R/Python 等價或資料來源（MD5）方面的失敗。R 交叉驗證確為真實逐項比對。三個警告皆屬**文件描述層面**：一處參考文獻標題錯誤且與專案不一致（W1）、一處動畫資料來源歸屬與實際檔案能力矛盾（W2）、一處 pivot 維度標示不精確（W3）。三者修正成本低，且不影響底層科學結論或數字。

**本輪：0 fail、3 warn。**
