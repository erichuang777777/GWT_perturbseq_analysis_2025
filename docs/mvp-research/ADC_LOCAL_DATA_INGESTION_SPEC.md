# ADC 本地資料 Ingestion 規格
### 取代 `docs/external_overlay_integration_concept.md` 的「概念/等待」狀態 —— 真實檔案已核對

**觸發：** 使用者確認本地 `~/Downloads/adc_web_data/`（15GB）與 `~/Downloads/raw_cellxgene_result_zips_2026_06_20/`（155MB）為 concept 文件描述的兩個 overlay 來源（ADC target server + CellxGene 安全性驗證）。
**本文件目的：** 把 concept 文件列的「開放問題」逐一核對真實檔案後回答,並定出最小可行的 `safety_overlay.py` ingestion 規格。

---

## 1. 開放問題核對結果（concept 文件 §2/§3 的三個 blocker）

| concept 文件的開放問題 | 核對結果 |
|---|---|
| 識別碼系統：symbol vs Ensembl ID？ | **兩者都有。** `gene_scores.parquet`、`candidate_genes.parquet` 同時帶 `gene_symbol` 與 `ensembl_id`，可直接用 Ensembl ID join，不需 `gene_identifier_resolver.py` 額外解析。 |
| 是原始表現矩陣還是已算好的 verdict/tier？ | **已算好的 verdict。** `gene_scores.parquet` 有 `s2_normal_safety_score`(連續值)、`critical_tissue_flag`/`critical_tissue_tier`(布林/分級)、`gtex_max_normal_tissue`(組織名)——不需自己算表現廣度。 |
| 部分覆蓋可接受？ | **是,且已量化：** 與 GWT 11,526 個標的重疊 **5,678–5,588 個基因(約49%)**,覆蓋率足夠有意義,不影響 additive-only 原則。 |

**額外發現(concept 文件沒預期到的):**
- 版本戳記已內建：`db_version` (`v1.9.2-s3-prioritization-evidence`)、`computed_at`,直接符合 `docs/cache_and_versioning_policy.md` 的要求,不需額外包裝。
- CellxGene 那份資料本身就有明確的**方法論免責聲明**寫在 `MembraneFM_v0_4_..._validation_report.md`：「This validates normal-cell expression risk only; it does not validate ADC internalization, payload tolerability, or therapeutic window by itself」——這段話應直接沿用進本平台的 caveat 文字。
- `raw_cellxgene_result_zips` 裡的 `blood_segment_01_t_nk_results` 直接查詢過 **"CD4-positive, alpha-beta T cell"** 這個 cell type 的正常表現風險 — 與本平台情境高度相關,但**解讀方向要反過來**：ADC 情境下「CD4 T 細胞高表現」= off-target 風險（因為 ADC 標靶通常是腫瘤,不該打中 T 細胞）；GWT CD4 平台情境下「這個基因本來就在 CD4 T 細胞表現」是正常生物學,不是風險。**這條反轉在下面 §3 的 ingestion 邏輯中要處理,不能照搬 ADC 的分數方向。**

---

## 2. 兩個檔案 → 兩個 readiness 領域的對應（沿用 concept 文件既定設計）

### 2a. `candidate_genes.parquet`(11,311 列,無 cancer_type 混淆,乾淨的 gene-level 表)→ `tractability_modality`
最省力路徑成立：`is_surface_protein`、`has_transmembrane_domain`、`has_extracellular_domain`、`extracellular_length`、`is_druggable`、`druggable_pathway` 可直接 join 進 `_tractability()`。

實測樣本(Top-15 候選中的 5 個重疊基因)：

| gene | is_surface_protein | has_transmembrane | extracellular_length | is_druggable | druggable_pathway |
|---|---|---|---|---|---|
| CD3E | True | True | 104.0 | True | DRUGGABLE GENOME;EXTERNAL SIDE OF PLASMA MEMBRANE;KINASE |
| CD247 | True | True | 9.0 | True | DRUGGABLE GENOME;ENZYME;KINASE |
| LAT | True | True | 4.0 | False | — |
| MED12 | False | False | NaN | True | CLINICALLY ACTIONABLE;KINASE;TRANSCRIPTION FACTOR |
| CCNC | False | False | NaN | False | — |

這與先前的免疫/broad_effect 分層獨立一致：CD3E/CD247/LAT 是真正的表面受體複合體組件；MED12/CCNC(broad_effect 隔離對象)不是膜蛋白。**這是第三個獨立證據來源支持 C7 隔離的正確性**(先前已有 Open Targets 可成藥性、gnomAD 約束兩個來源)。

### 2b. `gene_scores.parquet`(221,144 列,含 cancer_type)→ `safety_window_score`(需先聚合去除 cancer_type)
**注意：這份表是 per (gene, cancer_type) 列,`s2_normal_safety_score` 會隨 cancer_type 微調(不同基線常態組織)。** CD4 平台不應直接 join 帶著腫瘤情境的分數。正確做法：對每個基因取 **cancer-type-agnostic 聚合**(如 median 或 max,代表「不論哪種癌症情境,這個基因在正常組織的風險上限」),或改用 `gtex_per_tissue.parquet`(260,172 列,`gene_symbol`/`tissue`/`median_tpm`,完全無腫瘤學情境)重新算表現廣度。**建議採用後者**,更乾淨。

### 2c. `raw_cellxgene_result_zips` 的 `cellxgene_gene_normal_risk_summary.csv`(T/NK segment)→ `safety_window_score` 的細胞層級細化(選配)
含 `CD4-positive, alpha-beta T cell` 專屬的 `max_pct_positive`/`max_mean_expression`。可作為 GTEx 組織層級之外的細胞類型層級細化,但**優先度低於 2b**,因為這批資料是為 ADC 腫瘤學情境設計、字段語意需要反轉才能用於本平台,複雜度較高。

### 2d. TCGA(`xena_norm_count_tumor_normal_summary.parquet`)→ 不建分數(維持 concept 文件原判斷)
1,230,201 列,tumor vs normal log2 count,是 ADC 腫瘤學專用概念。**維持先前判斷：保留欄位、不建 CD4 安全分數。**

---

## 3. 最小可行 ingestion 規格

```python
# src/3_DE_analysis/safety_overlay.py  (新檔案,cre_schema.py 風格)

def load_membrane_tractability_overlay(path=None) -> dict:
    """讀 candidate_genes.parquet 的膜蛋白/可成藥性欄位。
    Returns {"available": bool, "reason": str, "table": pd.DataFrame|None}
    """
    # join key: ensembl_id (兩邊都有,不需符號解析)
    # 欄位: is_surface_protein, has_transmembrane_domain, has_extracellular_domain,
    #       extracellular_length, is_druggable, druggable_pathway

def load_gtex_safety_overlay(path=None) -> dict:
    """讀 gtex_per_tissue.parquet,算每基因的 off-context 表現廣度。
    聚合: n_tissues_expressed(median_tpm > threshold), max_expression_outside_cd4_context
    Returns 同上結構
    """

def _safety_window(gene_ensembl, safety_overlay, essential: bool):
    """與 readiness_engine._tractability() 同一契約：
    - 不在 overlay → "unknown"（不變)
    - essential → 仍為 0（essentiality 永遠優先)
    - 高 off-context 表現廣度 → 低分或新紅旗 broad_tissue_expression
    - 窄表現 → 真實正分,取代 "unknown"
    """
```

**版本戳記：** 沿用來源檔案自帶的 `db_version`/`computed_at`(§1 已確認存在),寫入 `fetched_at`/`source_version` 欄位,符合 `docs/cache_and_versioning_policy.md`。

**下一步(雲端執行)：**
1. 把 `candidate_genes.parquet`、`gtex_per_tissue.parquet` 兩個小檔(合計約 28MB,遠低於 GitHub 100MB 限制)作為版本化快照放進 `sources/target_tool_cache/_overlays/`。**`gene_scores.parquet`(27MB,含癌症情境)與 15GB 的 duckdb/zip 原始檔不進 repo**,只留 ingestion 腳本讀取路徑設定。
2. 寫 `safety_overlay.py`,接上述兩個 loader + `_safety_window()`。
3. 加 golden-file 測試(3 個基因：CD3E 窄表現+膜蛋白、MED12 廣表現無膜蛋白、一個不在 overlay 的基因)。
4. 更新 `docs/data_dictionary.md` 新增欄位;`docs/data_governance_checklist.md` 標注來源(HPA/UniProt/CSPA/GTEx 皆為公開資料庫衍生,無病人層識別資訊)。

---

## 4. 交付物
- `ADC_LOCAL_DATA_INGESTION_SPEC.md`(本文件)
- `adc_overlay_gwt_overlap_full.csv` — candidate_genes 與 GWT 11,526 標的的完整重疊表(5,588 列,含膜蛋白/可成藥性欄位)
