# 技術方法與驗證說明文件
## CD4⁺ T 細胞 Perturb-seq 標靶優先排序平台 — Methods, Data Provenance & Validation

| | |
|---|---|
| **文件類型** | 技術方法說明(peer-review 等級) |
| **版本 / 日期** | v1.0 · 2026-07 |
| **範疇** | 本文件描述 `src/3_DE_analysis/` 標靶探索工具的資料出處、方法學、驗證與限制。它**消費**上游 GWT 資料集已發表、已驗證的計算,**不重算** DE、pseudobulk 或 NTC 基線。 |
| **權威來源** | 本文件為 `docs/` 內規格(`de_and_baseline_spec.md`、`data_dictionary.md`、`cache_and_versioning_policy.md`、`data_governance_checklist.md`、`IMPLEMENTATION_PLAN.md`)之整合;數字衝突時以該等規格與 supplementary tables 逐欄定義為準。 |
| **主資料集** | Zhu R., Dann E. et al. (2025) genome-scale Perturb-seq in primary human CD4⁺ T cells,bioRxiv `10.64898/2025.12.23.696273` [1] |

---

## 摘要 Abstract

本平台把一個在**原代人類 CD4⁺ T 細胞**上執行的全基因體 CRISPRi Perturb-seq 篩選 [1] 的差異表現(differential expression, DE)結果,轉換為結構化、可稽核的「標靶卡片(target card)」,並輸出四級決策(advance / validate / watchlist / deprioritize)。核心設計為:(i) 以敲低(knockdown, KD)因果閘區分「可因果判讀」與「不可因果判讀」的擾動;(ii) 以紅旗覆蓋(red-flag override)確保必需基因(essential)、廣泛效應基因(broad-effect)、脫靶(off-target)、批次混淆與敲低未確認之標靶,無論下游統計多強皆被封頂;(iii) 以正/負對照校準(calibration)量化排序是否回復已知生物學;(iv) 以四層版本戳記與不可變 `dataset_id` 保證可重現。本文件陳述每一項的資料出處、精確定義、統計基礎、驗證數字與明確的範疇限制(descope),使外部審查者能逐項稽核。

---

## 1. 引言與範疇 Introduction & Scope

Perturb-seq 將池化 CRISPR 擾動與單細胞 RNA 定序結合,可在單一實驗中量測數千個基因擾動各自的轉錄後果 [2,3,4]。多數大規模資源建立在易培養的癌細胞株上;本平台的主資料集 [1] 之特殊性在於使用**原代人類 CD4⁺ T 細胞**、涵蓋全基因體、並在三種培養條件(`Rest` / `Stim8hr` / `Stim48hr`)與多位捐贈者下重複,使結論具備情境專一性與較高的轉譯相關性,呼應近年原代 T 細胞擾動研究 [5,6,7,8]。

本平台**不是**新的定序或 DE 方法;它是建立在既有 DE 輸出之上的**決策支援層**。其明確目標是把 33,983 列「擾動 × 條件」DE 統計 [1] 轉為研究者可辯護的標靶優先序,並在每一步保留出處與不確定性。

---

## 2. 資料出處與治理 Data Provenance & Governance

### 2.1 主資料集(GWT Perturb-seq)

- **實驗設計**:4 位捐贈者(D1–D4)× 3 種培養條件 × 2 個處理批次(R1/R2);CRISPRi 擾動,單細胞 3′ 定序後經 guide 指派、pseudobulk 彙整與 DESeq2 DE [1,9]。
- **供本平台消費的 supplementary tables**(`metadata/suppl_tables/`):
  - `DE_stats.suppl_table.csv` — 每「標靶 × 條件」一列(`n_obs = 33,983`),含 `ontarget_effect_size`、`ontarget_significant`、`n_up/down/total_de_genes`(10% FDR)、`crossdonor_correlation_mean/min`、`crossguide_correlation`、`offtarget_flag` 等。
  - `guide_kd_efficiency.suppl_table.csv` — 每 guide × 條件的敲低 Welch t 檢定(`t_statistic`、`adj_p_value`、`signif_knockdown`、`high_confidence_no_effect_guides`)。
  - `sgrna_library_metadata.suppl_table.csv` — guide 設計、TSS 距離、脫靶與雙向啟動子註記。
  - `sample_metadata.suppl_table.csv` — 捐贈者人口學與批次,用於推導混淆條件。
- **深層物件**(公開 S3,雲端):`GWCD4i.DE_stats.h5ad`(含 `log_fc`/`p_value`/`adj_p_value`/`lfcSE`/`zscore` layers)、`GWCD4i.pseudobulk_merged.h5ad`、`*.h5mu`(guide/donor 拆分)、細胞層級 `D*_*.assigned_guide.h5ad`(全量約 1.7 TiB)。
- **公開入口與 accession**:CZI Virtual Cells Platform;原始定序 SRA `SRP643211` / GEO `GSE314342`。逐欄定義見 `metadata/data_sharing_readme.md` 與 `docs/data_dictionary.md`。

### 2.2 參考資料集與 overlay(in-repo)

外部篩選與基因清單用於 overlay 與交叉核對:人類轉錄因子 [26]、核心必需基因(Hart et al.)[15]、可成藥性分類(kinase/GPCR/enzyme/ion-channel/nuclear-receptor/transporter 清單)、GWAS catalog、ClinVar 致病變異、IUIS 先天免疫缺陷清單、免疫效應基因、細胞激素受體、以及 Human Protein Atlas 組織表現。廣泛效應清單 `sources/broad_effect_genes.txt` 由 EDA 指認之 offender 與 CORUM 染色質/轉錄複合體聯集而成(239 基因)。

### 2.3 外部證據來源(證據層)

以快取優先(cache-first)方式整合,並記錄 `fetched_at` 版本戳記:Open Targets Platform [16]、ClinicalTrials.gov [25]、PubMed/PMC、gnomAD(LOEUF/pLI,v4 門檻 0.6)[17]、GTEx(組織表現安全窗口)[18]、LINCS/CMap L1000(訊號反轉)[19]、Reactome [20] + STRING [21](機制圖)、AlphaFold [22](結構)、CELLxGENE Census [23]、ChEMBL [24]。

### 2.4 授權、倫理與治理

主資料為公開發表資料集 [1];本平台不處理可識別個資(捐贈者僅以去識別化人口學欄位存在於 supplementary table)。使用者上傳資料一律命名空間隔離(`usr_` 前綴)、絕不混入 GWT 參考集;平台目前為單人/file-cache 研究用途,**無存取控制**,`usr_` 命名僅防止意外混料而非授權隔離。治理原則(尤以 `unknown ≠ 0`)見 `docs/data_governance_checklist.md`。**本平台輸出為研究用標靶優先排序,非臨床或用藥建議。**

---

## 3. 方法 Methods

### 3.1 上游 DE 與 NTC 基線(消費而非重算)

所有效應量、DE 呼叫與敲低判斷皆相對於**非標靶對照(non-targeting control, NTC)基線**;若不精確陳述其組成,數字即不可比較 [`de_and_baseline_spec.md`]。

- **NTC pool 為條件配對(condition-matched)**:對每個 `(perturbed_gene_id, culture_condition)`,`ntc_mean_expr/std/n` 由**同一 culture_condition 內**的 NTC 細胞計算;經本 repo 實證,37,578 個群組中 0 個群組的 `ntc_mean_expr` 在同一 `(gene, condition)` 內出現一個以上相異值,確認 NTC pool 為條件配對而非個別 guide 的細胞配對。
- **效應量**:以 **DESeq2** [9] 對 pseudobulk 聚合(單位 = `guide × donor × culture_condition`)計算;`ontarget_effect_size` 為標靶基因自身在其敲低對比 vs 條件配對 NTC pseudobulk 基線之 log₂FC。
- **納入閘**:pseudobulk 層以布林旗(`keep_min_cells`、`keep_effective_guides`、`keep_total_counts`、`keep_for_DE`、`keep_test_genes`)決定是否納入;本平台的 `min_cells`/`min_de_genes` 為**其上的第二道較粗過濾**,不取代上游閘。
- **FDR**:`n_up/down/total_de_genes` 一致採 **10% FDR**(Benjamini–Hochberg [10]),定義見 `data_sharing_readme.md`。

### 3.2 標靶卡片建構與證據分級

`build_target_cards.py` 將 guide 級敲低與 DE 統計彙整為每「標靶 × 條件」一列的卡片,並賦予 `statistical_evidence_grade`(1–4)與 `score_cap_reason`——一道建立在上游 `keep_for_DE` 之上的可重現性閘(最小細胞數、跨捐贈者/跨 guide 相關、脫靶旗)。分級為**保守封頂**設計:缺 guide 資料封頂於 grade 2。

### 3.3 敲低因果閘 `kd_status`(核心設計)

CRISPRi 的因果鏈為「標靶被抑制 → 下游轉錄改變」;若標靶自身敲低未確認,下游 DE 不可因果判讀 [11,13]。本平台以四態 `kd_status`(`KD_THRESHOLD_VERSION = "kd_status/v2"`)彙整 guide 級 Welch t 檢定:

| 狀態 | 條件 | 判讀 |
|---|---|---|
| `confirmed` | `guide_signif_ratio ≥ 0.5` 且 `guide_fdr_min ≤ 0.05` | 敲低確認,下游可因果判讀 |
| `weak` | 有訊號但未達確認門檻 | 下游可疑,封頂 validate |
| `not_measurable` | 已測量之 NTC 基線 `≤ 0.001` | 連敲低都無法評估,封頂 watchlist |
| `not_assessed` | 基線從未測量(NaN) | 真正未知,**不懲罰**(`unknown ≠ 0`) |

`KD_NOT_MEASURABLE_EXPRESSION_FLOOR = 0.001` 直接重用資料集自身文件化的 `high_confidence_no_effect_guides` 定義(「非顯著敲低、>10 細胞、NTC 表現 >0.001」),而非新發明門檻。`not_measurable`(已測量的失敗)與 `not_assessed`(從未測量的未知)為**不同失效模式**,刻意分開處理 [`de_and_baseline_spec.md` §3]。

### 3.4 穩健性 Robustness

每列攜帶 `crossdonor_correlation_mean/min`(不相交捐贈者對之間 logFC 效應的 Pearson 相關)與 `crossguide_correlation`(個別 gRNA 之間)。缺該資料時顯示明確 caveat(`weak_replicability` / `missing_crossdonor_data`),不以 0 填補。`replicate_pass_flag` 要求跨捐贈者與跨 guide 同時穩健(且 ≥2 guides)。

### 3.5 就緒度引擎與紅旗覆蓋 `readiness_engine`(`core/readiness.py`)

引擎自約 12 個證據面向評分(統計等級、複製穩健性、敲低確認、pathway/clinical 軸與正對照相似度、臨床試驗、Open Targets 關聯、遺傳學 `clinvar`/`gwascatalog`、gnomAD `loeuf`/`pli`、最接近的成功藥物軸等),排入 `R0–R5` 成熟度階梯,並套用**紅旗覆蓋**——無論統計強弱,命中即封頂:

| 紅旗 | 觸發 | 封頂至 |
|---|---|---|
| `essential_gene` | 必需基因 | watchlist |
| `broad_effect` | 廣泛效應(239 基因清單) | watchlist |
| `high_offtarget` | `offtarget_flag`(TSS 10 kb 內顯著下調) | watchlist |
| `kd_not_measurable` | `kd_status = not_measurable` | watchlist |
| `uncertain_direction` | `ontarget_significant` 為否 / 方向不明 | validate |
| `batch_confounded` | `batch_sensitivity_flag = sensitive` | validate |
| `kd_weak` | `kd_status = weak` | validate |

必需基因另不得捏造 `safety_window_score`(修正過的行為:essential 不再假造 0 安全分)。未建置的證據面向一律回 `"unknown"`,不計為 0。

### 3.6 決策呼叫 Decision calling

`STAGE_TO_CALL` 將就緒度階段映射為 `advance` / `validate` / `watchlist` / `deprioritize`,再由上述紅旗封頂;每列輸出 `score_cap_reason` 與 `next_step`,並附 provenance footer。

### 3.7 情境專一性(明確聲明為 heuristic)

`condition_specificity_score` / `_zscore` 為**比值式啟發式**,**非**統計交互作用檢定;程式註解明載:嚴謹的 condition × perturbation 交互作用檢定需要本平台不具備的 per-guide/per-cell 模型,故列為範疇外。此聲明本身即是避免過度解讀的設計。

### 3.8 外部證據整合(cache-first)

`external_evidence_cache.py` 以基因為單位快取,預設 **30 天 TTL**;過期由比對 `fetched_at` 判定並於下次 fetch 重抓,可 `force=True` 強制刷新。批次端點上限 `MAX_EVIDENCE_GENES = 50` 且走背景任務。受限沙盒無對外連線時,fetcher 回 `source_status: "unavailable"` 而非崩潰(優雅降級)。政策見 `docs/cache_and_versioning_policy.md`。

### 3.9 疾病轉譯 Disease translation

`disease_translator` 對接 repo 內既有 Open Targets 基因關聯匯出(13 個自體免疫適應症、7,528 列)[16],對標靶卡片做疾病相關排序,不需新 fetch。

### 3.10 版本化與可重現 Versioning & Reproducibility

每個資料集攜帶四層版本:`engine_version` / `dataset_version` / `schema_version` / `signature_set_version`。每次 `POST /api/build` 產生新的不可變 `dataset_id`(UUID)並寫入新目錄,**不原地覆寫**;舊 `dataset_id` 為凍結快照,即使版本 bump 也不回溯重算,使已分享連結永遠回傳相同數字。重建時機(上游 CSV 指紋變動、`ENGINE_VERSION`/`CARD_SCHEMA_VERSION` bump)見 `cache_and_versioning_policy.md`。

---

## 4. 驗證與校準 Validation & Calibration

`calibration.py::control_panel_calibration()` 在真實參考資料集上雙向檢驗(`src/3_DE_analysis/calibration.py`;數字來源 `de_and_baseline_spec.md` §5):

- **負對照**(`kd_status = not_measurable`,4,774 列):**99.96%** 正確落在 grade 1;**0%** 錯誤達 grade ≥3;**0%** 達 `advance`/`validate`。(列數為 4,774 而非早期 5,084,因 `kd_status/v2` 將 310 個 never-measured NaN 基線重分類為 `not_assessed`。)
- **正對照**(21 基因,已確立之 CD4 表型:CD3D/E/G、CD28、ICOS、CTLA4、CD80/86、IL2RA、IL2RB、IL7R、LCK、ZAP70、JAK3、PTPN2、FOXP3、PTGER4、STAT5A/B、TNFRSF9):僅 **20%** 達嚴格 `statistical_evidence_grade ≥ 3`(需在特定條件同時跨捐贈者與跨 guide 穩健、≥2 guides),但 **93.1%** 未被就緒度引擎 `deprioritize`。
- **誠實詮釋**:grade 3/4 刻意是「此條件列一切吻合」的窄門,**不是**「是否為生物學上真標靶」的代理。低 grade 搭配未降級的 readiness 呼叫本身即具資訊量;為使正對照好看而放寬門檻,等於把指標校準到答案而非驗證它——故不為之。
- **排序穩定度**:天真的「以 DE breadth 取 top-50」與嚴格過濾 top-50 僅 13/50 重疊(Spearman r = 0.943),為一項誠實發現:天真排序本身不具穩健性保證。
- **正對照回復**:在 Stim8hr,校準回復全部 8 個 TCR/近端正對照於 top decile。

單元測試涵蓋 golden-file(逐值比對)、join-integrity(彙整列數守恆)、known-answer(對真實 33,983 列回歸釘選)、empty-state;`tests/` 共 18 檔;缺 `metadata/suppl_tables/*.csv` 時真實資料測試 skip 而非 fail。

---

## 5. 限制與明確 descope Limitations & Explicit Descopes

以下為**刻意記錄**的限制,避免被誤認為疏漏:

1. **Signed CD4 module scoring(§1.5,放棄)**:`DE_stats` 僅有 up/down 計數、無 per-gene 方向,signed 分數會是捏造;`/api/modules` 維持二元 overlap 分數。
2. **SCEPTRE**:以誠實外部 hook(R 存在則 shell out,否則優雅退化)而非天真 Python 重寫——SCEPTRE 的條件重採樣校準非平凡,天真重寫會重現其本要修正的 miscalibration [11,12]。
3. **pertpy / Mixscape**:`pertpy` 因 `blitzgsea` 建置失敗無法安裝;回應者/逃逸者分類以 scikit-learn(PCA 差異均值軸 + 2-component GMM)重寫,程式註解明載為刻意替代 [13]。
4. **細胞層級真實資料**:全量約 1.7 TiB 超過沙盒磁碟;程式對 schema 忠實之合成 fixture 已驗證(分類準確率 81.8%),但**未宣稱**已處理真實資料——委由負責人於自有機器執行(`src/9_cell_integration/RUN_ON_REAL_DATA.md`)。「對合成 fixture 驗證」與「已處理真實資料」是不同宣稱。
5. **上傳路徑已知技術債**:純上傳(無 guide/NTC 表)在 `kd_status/v2` 前曾被誤判;另 `n_total_de_genes` 若非 canonical 上傳欄位會於對應後遺失(見 `Tech-Debt` A.1/A.2)。
6. **情境專一性**為 heuristic(§3.7),非交互作用檢定。
7. **驗證環境**:Streamlit 未安裝於開發沙盒,儀表板變更僅 py_compile/AST 驗證,未視覺渲染。

---

## 6. 可重現性與程式碼可得性 Reproducibility & Code Availability

- **程式碼**:`https://github.com/erichuang777777/GWT_perturbseq_analysis_2025`(`src/3_DE_analysis/`);環境 `environment.yaml`(Python 3.11)。
- **資料**:主資料公開(CZI VCP;SRA `SRP643211` / GEO `GSE314342`)。
- **決定論**:相同輸入 + 相同四層版本 → 相同輸出;`dataset_id` 為不可變快照。
- **測試**:`python -m pytest tests/ -q`。

---

## 7. 附錄:關鍵參數 Appendix — Key Parameters

| 參數 | 值 | 意義 |
|---|---|---|
| DE FDR | 10% (BH) | `n_up/down/total_de_genes` 門檻 [10] |
| `signif_knockdown` | `adj_p<0.1 且 t<0` | guide 級敲低顯著且方向正確 |
| `KD_NOT_MEASURABLE_EXPRESSION_FLOOR` | 0.001 | 敲低可評估性下限(重用資料集定義) |
| `replicate_pass_flag` | 跨 donor ∧ 跨 guide,≥2 guides | 嚴格穩健性閘 |
| broad-effect 清單 | 239 基因 | 廣泛效應紅旗 |
| gnomAD LOEUF 門檻 | 0.6 (v4) | 約束性安全指標 [17] |
| 外部證據 TTL | 30 天 | 快取失效 |
| `MAX_EVIDENCE_GENES` | 50 | 批次證據端點上限 |
| 版本層 | engine / dataset / schema / signature_set | 四層 provenance |

---

## 8. 參考文獻 References

> 主資料集與領域文獻之識別碼取自 repo 內 curated 清單 `sources/topic07_key_papers_and_pmids_summary.md`;方法學文獻(DESeq2、BH、gene essentiality、資料庫)之識別碼可經 PubMed/DOI 解析驗證。

1. Zhu R., Dann E., et al. Genome-scale Perturb-seq in primary human CD4⁺ T cells. *bioRxiv* (2025). doi:10.64898/2025.12.23.696273
2. Dixit A., et al. Perturb-Seq: dissecting molecular circuits with scalable single-cell RNA profiling of pooled genetic screens. *Cell* (2016). PMID 27984732; doi:10.1016/j.cell.2016.11.038
3. Datlinger P., et al. Pooled CRISPR screening with single-cell transcriptome readout (CROP-seq). *Nat Methods* (2017). PMID 28099430; doi:10.1038/nmeth.4177
4. Replogle J.M., et al. Mapping information-rich genotype–phenotype landscapes with genome-scale Perturb-seq. *Cell* (2022). PMID 35688146; doi:10.1016/j.cell.2022.05.013
5. Shifrut E., et al. Genome-wide CRISPR screens in primary human T cells reveal key regulators of immune function. *Cell* (2018). PMID 30449619; doi:10.1016/j.cell.2018.10.024
6. Schmidt R., et al. CRISPR activation and interference screens decode stimulation responses in primary human T cells. *Science* (2022). PMID 35113687; doi:10.1126/science.abj4008
7. Freimer J.W., et al. Systematic discovery and perturbation of regulatory genes in human T cells. *Science* (2022). PMID 36356142; doi:10.1126/science.abn5647
8. Weinstock et al. Gene regulatory network inference in primary human CD4⁺ T cells. *Cell Genomics* (2024). PMID 39395408; doi:10.1016/j.xgen.2024.100671
9. Love M.I., Huber W., Anders S. Moderated estimation of fold change and dispersion for RNA-seq data with DESeq2. *Genome Biology* (2014). PMID 25516281; doi:10.1186/s13059-014-0550-8
10. Benjamini Y., Hochberg Y. Controlling the false discovery rate. *J R Stat Soc B* (1995). doi:10.1111/j.2517-6161.1995.tb02031.x
11. Barry T., et al. SCEPTRE improves calibration and sensitivity in single-cell CRISPR screen analysis. *Genome Biology* (2021). PMID 34930414; doi:10.1186/s13059-021-02545-2
12. Barry T., et al. Robust differential expression testing for single-cell CRISPR screens at low MOI. *Genome Biology* (2024). PMID 38760839; doi:10.1186/s13059-024-03254-2
13. Papalexi E., et al. Characterizing the molecular regulation of inhibitory immune checkpoints with multimodal single-cell screens (Mixscape). *Nat Genetics* (2021). PMID 33649593; doi:10.1038/s41588-021-00778-2
14. Replogle J.M., et al. Combinatorial single-cell CRISPR screens by direct guide RNA capture. *Nat Biotechnol* (2020). PMID 32231336; doi:10.1038/s41587-020-0470-y
15. Hart T., et al. High-resolution CRISPR screens reveal fitness genes and genotype-specific cancer liabilities. *Cell* (2015). PMID 26627737; doi:10.1016/j.cell.2015.11.015
16. Ochoa D., et al. The Open Targets Platform. *Nucleic Acids Research* (2024). PMID 39657122; doi:10.1093/nar/gkae1128
17. Karczewski K.J., et al. The mutational constraint spectrum quantified from variation in 141,456 humans (gnomAD). *Nature* (2020). PMID 32461654; doi:10.1038/s41586-020-2308-7
18. GTEx Consortium. The GTEx project: genetic effects on gene expression across human tissues. *Science* (2020). PMID 32913098; doi:10.1126/science.aaz1776
19. Subramanian A., et al. A next generation connectivity map: L1000 platform (LINCS/CMap). *Cell* (2017). PMID 29195078; doi:10.1016/j.cell.2017.10.049
20. Gillespie M., et al. The Reactome pathway knowledgebase. *Nucleic Acids Research* (2022). PMID 34788843; doi:10.1093/nar/gkab1028
21. Szklarczyk D., et al. STRING v12: protein–protein association networks. *Nucleic Acids Research* (2023). PMID 36370105; doi:10.1093/nar/gkac1000
22. Jumper J., et al. Highly accurate protein structure prediction with AlphaFold. *Nature* (2021). PMID 34265844; doi:10.1038/s41586-021-03819-2 · AlphaFold DB: Varadi M., et al. *Nucleic Acids Research* (2022). doi:10.1093/nar/gkab1061
23. CZ CELLxGENE Discover / Census. *Nucleic Acids Research* (2024). PMID 39607691; doi:10.1093/nar/gkae1142
24. Zdrazil B., et al. The ChEMBL Database in 2023. *Nucleic Acids Research* (2024). PMID 37933841; doi:10.1093/nar/gkad1004
25. National Library of Medicine (NIH). ClinicalTrials.gov. https://clinicaltrials.gov
26. Lambert S.A., et al. The Human Transcription Factors. *Cell* (2018). PMID 30290144; doi:10.1016/j.cell.2018.01.029
27. Ytterberg S.R., et al. Cardiovascular and cancer risk with tofacitinib in rheumatoid arthritis (ORAL Surveillance). *N Engl J Med* (2022). PMID 35081280; doi:10.1056/NEJMoa2109927
28. Herold K.C., et al. An anti-CD3 antibody, teplizumab, in relatives at risk for type 1 diabetes. *N Engl J Med* (2019). PMID 31180194; doi:10.1056/NEJMoa1902226

---

*本文件為活文件;方法或門檻變更時,以 repo `docs/` 內對應規格與程式碼常數為準,並更新版本。稽核者可依 §8 識別碼直接查證每項外部宣稱,依 §2 accession 取得原始資料,依 §6 重現計算。*
