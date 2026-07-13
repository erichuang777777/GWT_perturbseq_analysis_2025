# Provenance 登錄表 Provenance Registry

> **一個集中欄位,登錄三類東西:資料來源 × 執行運算的演算法 × 參考文獻。** 這頁補上先前「有記錄、但散在各處」的缺口——把 `config/versions.py` 的版本常數、`evidence/*` 的逐筆來源欄位、盤點 CSV、以及 `technical_methods.md` §8 的引用,對齊到**同一組固定欄位**。機器可讀版:[`provenance_registry.csv`](provenance_registry.csv)。
>
> **固定欄位**:`component · type · identifier · version · source_url_or_id · produced_by · notes`
> **維護規則**:新增資料來源/演算法/參考時,同步在此登錄一列;版本字串以 `config/versions.py` 與各 `SOURCE_VERSION` 為準(此處為對照,衝突時以程式與 `docs/` 規格為準)。
> **既有相關**:程式層的 provider 註冊在 `src/3_DE_analysis/evidence/registry.py`(swap-by-name);圖表逐張產生腳本在 `docs/mvp-research/pipeline/reproducibility_audit/figure_registry.md`;本頁是跨三類的**文件層總表**。

---

## 0. 版本層(演算法/資料集身分的權威來源)

| 版本常數 | 值 | 意義 | 位置 |
|---|---|---|---|
| `ENGINE_VERSION` | `1.3.0` | 本工具評分/readiness/calibration 邏輯 | `config/versions.py` |
| `DATASET_VERSION` | `gwt_marson2025/bioRxiv-10.64898-2025.12.23.696273v1` | 主資料集身分 | `config/versions.py` |
| `CARD_SCHEMA_VERSION` | `card_schema/v2` | 卡片欄位契約 | `config/versions.py` |
| `KD_THRESHOLD_VERSION` | `kd_status/v2` | 敲低因果閘門檻 | `config/versions.py`(亦為逐列卡片欄位 `kd_threshold_version`) |
| `SOURCE_VERSION`(external) | `external_evidence_cache/v1` | 外部證據 fetcher | `evidence/external_cache.py` |
| `SOURCE_VERSION`(pathway) | `pathway_network_cache/v1` | 機制圖快取 | `evidence/pathway_cache.py` |
| `data_version` | 每次 build 的 MD5 指紋 | 上游 CSV 內容指紋 | build metadata |

---

## 1. 資料來源 Data Sources

### 1.1 主資料(消費而非重算)
| component | identifier / version | source_url_or_id | produced_by | notes |
|---|---|---|---|---|
| GWT CD4 Perturb-seq(主) | `DATASET_VERSION` | bioRxiv 10.64898/2025.12.23.696273 · SRA `SRP643211` · GEO `GSE314342` · CZI VCP | upstream | 4 donors×3 conditions×2 runs |
| `DE_stats.suppl_table.csv` | `data_version`(MD5) | metadata/suppl_tables/ | upstream DESeq2 | 33,983 列 |
| `guide_kd_efficiency.suppl_table.csv` | `data_version` | metadata/suppl_tables/ | upstream Welch t | 73,765 列;NTC 條件配對 |
| `sgrna_library_metadata.suppl_table.csv` | `data_version` | metadata/suppl_tables/ | upstream | guide 設計/TSS/脫靶 |
| `sample_metadata.suppl_table.csv` | `data_version` | metadata/suppl_tables/ | upstream | 捐贈者/批次 |
| cell-level h5ad | `DATASET_VERSION` | CZI VCP S3 | upstream | ~1.7 TiB;沙盒未跑 |

### 1.2 外部證據資料庫(evidence 層,逐筆帶 source/url/fetched_at)
| component | version | source_url_or_id | produced_by | notes |
|---|---|---|---|---|
| Open Targets | `external_evidence_cache/v1` | platform.opentargets.org · PMID 39657122 | `evidence/external_cache.py` + `evidence/disease.py` | tractability/genetics/drugs;30 天 TTL |
| ClinicalTrials.gov v2 | `external_evidence_cache/v1` | clinicaltrials.gov | `evidence/external_cache.py` | 試驗 |
| PubMed/PMC | `external_evidence_cache/v1` | pubmed.ncbi.nlm.nih.gov | `evidence/external_cache.py` | 文獻 |
| gnomAD v2.1.1 | — | gnomad.broadinstitute.org · PMID 32461654 | `evidence/safety_overlay.py` | LOEUF/pLI 全基因組(19,155 基因);門檻 0.6 |
| GTEx | — | gtexportal.org · PMID 32913098 | `evidence/safety_overlay.py` | 組織表現安全窗口 |
| LINCS/CMap L1000 | — | clue.io · PMID 29195078 | `evidence/lincs_reference_cache.py` | 訊號反轉 |
| Reactome | `pathway_network_cache/v1` | reactome.org · PMID 34788843 | `evidence/pathway_cache.py` · `mechanism_graph.py` | 機制圖 |
| STRING v12 | `pathway_network_cache/v1` | string-db.org · PMID 36370105 | `evidence/pathway_cache.py` · `mechanism_graph.py` | PPI |
| AlphaFold DB | — | alphafold.ebi.ac.uk · PMID 34265844 | committed `.cif` | broad-effect 結構 |
| ChEMBL | — | ebi.ac.uk/chembl · PMID 37933841 | evidence 層 | bioactivity |
| CELLxGENE Census | — | cellxgene.cziscience.com · PMID 39607691 | concept overlay | baseline 表現 |
| Human Protein Atlas | — | proteinatlas.org | `metadata/rna_tissue_consensus.tsv.zip` | 組織表現 |

### 1.3 in-repo overlay / 基因清單 / 外部篩選
| component | source_url_or_id | notes |
|---|---|---|
| `broad_effect_genes.txt` | sources/ (EDA + CORUM) | **239 基因**;broad_effect 紅旗 |
| `core_essentials_hart.tsv` | PMID 26627737 | essential 紅旗(Hart 2015) |
| druggability class lists | metadata/gene_lists/*.tsv | kinase/GPCR/enzyme/ion-channel… |
| GWAS catalog · ClinVar | metadata/gene_lists/ | 遺傳支持 |
| IUIS-IEI list | metadata/IUIS-IEI-list-July-2024V2.csv | 先天免疫缺陷 |
| Open Targets 疾病關聯 | metadata(OT 匯出) | 13 適應症 / 7,528 列 |
| Lambert 2018 TFs | PMID 30290144 | 轉錄因子 |
| 外部篩選 | Freimer2022 / Schmidt2022 / Arce2024-25 / Weinstock / Umhoefer2025 / Terekhova2023 / Wells2025 / Replogle2022 / Tahoe100M | 交叉核對(PMID 見 CSV) |

---

## 2. 執行運算的演算法 Algorithms / Computations

| component | produced_by(module) | version | notes |
|---|---|---|---|
| DESeq2 DE(上游) | upstream | — | 消費不重算;10% FDR(BH) |
| pseudobulk 聚合(上游) | upstream | — | 單位 guide×donor×condition |
| guide 敲低檢定(上游) | upstream | — | Welch t vs 條件配對 NTC |
| **kd_status 因果閘** | `core/kd_status.py` | `kd_status/v2` | 4 態;floor 0.001 |
| 卡片建構 + 證據分級 | `core/cards.py` | `1.3.0` / `card_schema/v2` | grade 1–4;保守封頂 |
| 情境專一性(heuristic) | `core/cards.py` | `1.3.0` | **HEURISTIC,非交互作用檢定** |
| 穩健性(跨 donor/guide) | `core/cards.py` | 上游欄位 | `replicate_pass_flag` |
| **就緒度引擎(12 領域→R0–R5)** | `core/readiness.py` | `1.3.0` | + 紅旗覆蓋 |
| 評分輔助 | `core/scoring.py` | `1.3.0` | 領域評分 |
| **校準 harness** | `core/calibration.py` | `1.3.0` | 正/負對照 |
| 疾病轉譯 | `evidence/disease.py` | — | Open Targets 匯出排序 |
| 機制圖 | `evidence/mechanism_graph.py` | — | Reactome+STRING;**描述性** |
| 族群 LoF 假設 | `evidence/population.py` | — | 研究用 |
| **概念模組 M01–M20** | `api/deps.py::_module_scores` | — | seed-gene overlap;**永不餵決策** |
| 基因解析 + 模糊搜尋 | `resolve/resolver.py` · `search.py` | — | Ensembl 主鍵 + difflib |
| 外部證據 fetcher | `evidence/external_cache.py` | `external_evidence_cache/v1` | cache-first;30 天 TTL |
| pathway/network 快取 | `evidence/pathway_cache.py` | `pathway_network_cache/v1` | 離線 |
| safety/tractability overlay | `evidence/safety_overlay.py` | — | gnomAD/GTEx/膜蛋白 |
| SCEPTRE(外部 hook) | R shell-out | — | 未重寫(descope);PMID 34930414 |
| Mixscape 式分類 | `src/9_cell_integration/` | — | scikit-learn PCA+GMM(刻意替代);PMID 33649593 |

---

## 3. 參考文獻 References

> 權威編號清單在 `technical_methods.md` §8;此處對齊同一組固定欄位(完整 28 條在 CSV `category=reference`)。

| # | 引用 | PMID / DOI | 角色 |
|---|---|---|---|
| 1 | Zhu & Dann et al. 2025 | DOI 10.64898/2025.12.23.696273 | 主資料集 |
| 2 | Dixit et al. 2016 Perturb-seq | PMID 27984732 | 方法起源 |
| 3 | Datlinger 2017 CROP-seq | PMID 28099430 | 方法 |
| 5 | Shifrut 2018 | PMID 30449619 | primary T 細胞驗證 |
| 6 | Schmidt 2022 | PMID 35113687 | primary T 細胞驗證 |
| 9 | Love 2014 DESeq2 | PMID 25516281 | DE 方法 |
| 10 | Benjamini–Hochberg 1995 | DOI 10.1111/…tb02031.x | FDR |
| 11 | Barry 2021 SCEPTRE | PMID 34930414 | scCRISPR 校準 |
| 13 | Papalexi 2021 Mixscape | PMID 33649593 | 擾動 QC |
| 15 | Hart 2015 essential genes | PMID 26627737 | essential overlay |
| 16 | Ochoa 2024 Open Targets | PMID 39657122 | 標靶-疾病 |
| 17 | Karczewski 2020 gnomAD | PMID 32461654 | 約束 |
| 18 | GTEx 2020 | PMID 32913098 | 組織表現 |
| 19 | Subramanian 2017 LINCS | PMID 29195078 | 藥物訊號 |
| 20 | Gillespie 2022 Reactome | PMID 34788843 | pathway |
| 21 | Szklarczyk 2023 STRING | PMID 36370105 | PPI |
| 22 | Jumper 2021 AlphaFold | PMID 34265844 | 結構 |
| 26 | Lambert 2018 TFs | PMID 30290144 | 轉錄因子 |
| 27 | ORAL Surveillance 2022 | PMID 35081280 | JAK 安全 |
| 28 | Herold 2019 Teplizumab | PMID 31180194 | anti-CD3 安全 |

*(4/7/8/12/14/23/24/25 見 CSV 與 `technical_methods.md` §8。)*

---

> 本頁為文件層總表;逐欄定義見 `data_dictionary.md`,方法脈絡見 `technical_methods.md`,圖表逐張見 `figure_registry.md`,版本語意見 `cache_and_versioning_policy.md`。
