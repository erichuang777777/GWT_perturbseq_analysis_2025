# 完整手冊 Manual — 引用文獻 · 數據來源 · 文件索引 · Commit 紀錄 · 架構圖

> 這是**整合型參考手冊**:把整個專案的引用文獻、數據來源、說明/開發文件、commit 紀錄集中在一頁,並用 ASCII 畫出完整架構。所有清單對應 repo 內真實檔案;逐字權威規格仍在各 `docs/` 專頁,本手冊是索引與地圖。
>
> 想快速上手開發 → **[開發說明 Development Guide](Development-Guide)**;想看能力總覽 → **[介紹 Home](Home)**。

---

## 目錄

1. [專案總覽](#1-專案總覽)
2. [完整架構圖(ASCII)](#2-完整架構圖ascii)
3. [數據來源 Data Sources](#3-數據來源-data-sources)
4. [引用文獻 References](#4-引用文獻-references)
5. [說明文件與開發文件索引](#5-說明文件與開發文件索引)
6. [Commit 紀錄摘要](#6-commit-紀錄摘要)
7. [附錄:關鍵常數與縮寫](#7-附錄關鍵常數與縮寫)

---

## 1. 專案總覽

在 **Marson lab genome-scale CD4⁺ T 細胞 Perturb-seq 篩選資料**(bioRxiv `10.64898/2025.12.23.696273v1`,Zhu R., Dann E. et al. 2025)之上,建一套**藥物標靶優先排序工具**:把大規模 CRISPRi 擾動的差異表現(DE)結果,轉成研究者能直接判讀的「標靶卡片(target card)」,並給出可辯護的 **推進 / 驗證 / 觀察 / 降級**(advance / validate / watchlist / deprioritize)決策。

- **主 repo**:論文原始分析流程(`src/1–8`)+ 標靶探索工具(`src/3_DE_analysis/`)+ 細胞層級延伸(`src/9`)。
- **資料規模**:DE 統計 33,983 列(每「標靶 × 條件」一列)、10,282 個被測基因、3 種培養條件(Rest / Stim8hr / Stim48hr)、4 位捐贈者(D1–D4)、2 個處理批次(R1/R2)。
- **原始定序資料**:SRA `SRP643211` / GEO `GSE314342`;處理後資料經 **Biohub Virtual Cells Platform**(CZI)公開。

---

## 2. 完整架構圖(ASCII)

### 2.1 端到端資料流(資料 → 卡片 → 決策 → 對外)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         原始 Perturb-seq 實驗(論文)                            │
│   4 donors × 3 conditions × 2 runs → cellranger → guide 指派 → pseudobulk       │
│   → DESeq2 差異表現 → 跨 donor/guide 穩健性 → guide 敲低 t 檢定                   │
└───────────────────────────────────┬────────────────────────────────────────────┘
                                     │  supplementary tables (公開 S3 / VCP)
                                     ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│  輸入層 (metadata/suppl_tables/)                                                  │
│   • DE_stats (33,983 列)      • guide_kd_efficiency      • sgrna_library_metadata │
│   • sample_metadata            • benchmark / disease_gene_associations            │
└───────────────────────────────────┬──────────────────────────────────────────────┘
                                     ▼
┌────────────────────────────── src/3_DE_analysis ─────────────────────────────────┐
│                                                                                  │
│  build_target_cards.py ──► 標靶卡片 (每「標靶×條件」一列, 1–4 級證據強度)          │
│        │  kd_status 因果閘 (confirmed / weak / not_measurable / not_assessed)      │
│        ▼                                                                          │
│  readiness_engine.py ──► 12 領域評分 → R0–R5 階段 → 紅旗覆蓋 → 決策呼叫            │
│        │        ▲                                                                 │
│        │        └── overlay: broad_effect(239 基因)/ druggability / safety        │
│        ▼                                                                          │
│  calibration.py ──► 正對照(TCR 近端)recovery + 藥物軸富集 + 排序穩定度            │
│                                                                                  │
│  external_evidence_cache.py ──► ClinicalTrials / PubMed / Open Targets(快取優先) │
│  disease_translator (routers) ─► 13 適應症 × 7,528 基因關聯(Open Targets 匯出)   │
│  population_hypothesis.py / mechanism_graph.py / signature_explorer.py …          │
└───────────────────────────────────┬──────────────────────────────────────────────┘
                                     ▼
┌───────────────── 對外介面 ─────────────────┐   ┌────────── 上傳路徑 ──────────┐
│  api/  (FastAPI, 每資源一 router)           │◄──┤ upload/import_manager.py     │
│   /api/build /cards /readiness /calibration │   │ 暫存→欄位對應→核准→合併→卡片  │
│   /evidence /disease /genes /population …   │   │ usr_ 命名空間隔離            │
│   GET /api/health(逐能力 available/degraded)│   └──────────────────────────────┘
└───────────────────┬─────────────────────────┘
                    │ HTTP / JSON(唯一契約)
                    ▼
┌──────────────────────────────────────────────┐
│  frontend/ (Streamlit 儀表板, 獨立可部署)      │
│   標靶瀏覽 · target dossier · QC funnel · 校準  │
└──────────────────────────────────────────────┘
```

### 2.2 後端分層架構(架構重構後)

```
                         api/app.py  (組裝: 每 router 各自 try/except import,
                                       單一 router 掛掉不會拖垮整個 API)
                                 │
        ┌────────────────────────┼─────────────────────────────┐
        ▼                        ▼                             ▼
   api/routers/*           api/deps.py                    config/
   build  cards            (共用路徑/版本常數,             settings.py
   readiness calibration    cached resolver / overlay,      thresholds.py
   evidence disease         per-dataset helpers)            versions.py (4 層版本)
   genes population
   imports mechanism
        │
        ▼
   核心邏輯 (build_target_cards / readiness_engine / calibration / disease / …)
        │
        ▼
   common/  ── coerce(型別轉換) · degrade(優雅降級) · timeutil(fetched_at 戳記)
             · overlay_lookup(overlay 查表) · evidence_grading(證據分級)
        │
        ▼
   resolve/ ── resolver.py(Ensembl 主鍵 + 別名表) · search.py(difflib 模糊搜尋)
             · cre.py(CRE schema 佔位)
```

### 2.3 就緒度決策流(readiness_engine.py)

```
  標靶卡片一列
      │
      ▼
  12 領域評分 ──► 統計強度 / 穩健性 / 敲低確認 / 藥物可成性 / 安全 / 遺傳學 / 疾病 / … 
      │           (未建置領域 = "unknown", 絕不給 0)
      ▼
  R0 ─ R1 ─ R2 ─ R3 ─ R4 ─ R5   (就緒度階段)
      │
      ▼
  紅旗覆蓋 (不論統計多強, 命中即封頂):
      essential ─┐
      broad_effect ─┤  kd_not_measurable ─┐
      off_target ─┤  batch_confounded ─┤ ──► 封頂 watchlist / validate
      direction_unknown ─┘               ─┘
      │
      ▼
  決策呼叫: advance / validate / watchlist / deprioritize
      (+ score_cap_reason, next_step, provenance footer)
```

### 2.4 Repository 地圖

```
GWT_perturbseq_analysis_2025/
├── src/
│   ├── 1_preprocess/            ingest + 前處理(cellranger → 物件)
│   ├── 2_embedding/             細胞狀態嵌入
│   ├── 3_DE_analysis/           ★ 標靶探索工具主體(api/ resolve/ upload/ common/ config/ report/)
│   ├── 4_polarization_signatures/  極化訊號分析
│   ├── 5_cytokine_regulators/   細胞激素調控子
│   ├── 6_functional_interaction/ 功能交互作用
│   ├── 7_1k1k_analysis/         1k1k 資料集分析
│   ├── 8_lymphocyte_counts_LoF/ 淋巴球數 LoF
│   ├── 9_cell_integration/      細胞層級(h5ad)延伸(程式就緒,真實資料委外跑)
│   └── _misc/                   雜項工具
├── metadata/                    ★ 樣本/實驗 metadata、config、基因清單、suppl_tables/
├── docs/                        ★ 權威規格與計劃(+ mvp-research/)
├── frontend/                    獨立前端(Streamlit 儀表板,只走 API)
├── sources/                     研究/證據快照(topic01–16)+ 快取 target_tool_cache/
├── tests/                       18 個測試檔(177 個 test 函式)
├── wiki/                        本 Wiki 原始檔(對應 .wiki.git)
├── README.md  LICENSE  environment.yaml  pytest.ini  .gitignore
```

---

## 3. 數據來源 Data Sources

### 3.1 主資料(GWT Perturb-seq,本專案的 ground truth)

| 檔案 / 物件 | 內容 | 規模 | 取得 |
|---|---|---|---|
| `GWCD4i.DE_stats.h5ad` | 全基因體 DE 結果(logFC/pval/adj_p/zscore/lfcSE layers) | 16.8 GB,`n_obs=33,983` × `n_vars=10,282` | 公開 S3(no-sign) |
| `GWCD4i.pseudobulk_merged.h5ad` | pseudobulk(依 guide×donor×condition 彙整) | 44.6 GB,`n_vars=18,129` | 公開 S3 |
| `GWCD4i.DE_stats.by_guide/by_donors.h5mu` | guide/donor 拆分穩健性 | 29.4 / 16.9 GB | 公開 S3 |
| `D*_*.assigned_guide.h5ad`(12 檔) | 細胞層級表現 + guide 指派 | ~118–173 GB/檔(**~1.7 TB 全量**) | 公開 S3 |
| **suppl_tables/**(卡片建構實際輸入) | `DE_stats` / `guide_kd_efficiency` / `sgrna_library_metadata` / `sample_metadata` + 極化/aging/autoimmune 富集表 | CSV,MB 級 | repo `metadata/suppl_tables/` |

- **公開入口**:Biohub Virtual Cells Platform(CZI)— `virtualcellmodels.cziscience.com/dataset/genome-scale-tcell-perturb-seq`;S3 探索:`aws s3 ls --no-sign-request s3://genome-scale-tcell-perturb-seq/marson2025_data/`
- **原始定序**:SRA `SRP643211` / GEO `GSE314342`
- 每個 suppl table 的**逐欄定義**在 `metadata/data_sharing_readme.md` 與 `docs/data_dictionary.md`。

### 3.2 in-repo 參考資料集與基因清單

外部篩選 / 研究資料(`metadata/`,多以第一作者+年份命名,對應 §4 引用):

| 檔案 | 來源研究 |
|---|---|
| `Lambert_2018_HumanTF.csv` | Lambert et al. 2018 人類轉錄因子 |
| `Freimer2022_Screen.csv` / `Freimer_et_al_raw.csv` | Freimer et al. 2022 T 細胞效應篩選 |
| `Schmidt2022_hits_Supplementary_table_2.xlsx` / `SchmidtSteinhart2022_CRISPRi_screen_gene_phenotypes.csv` | Schmidt et al. 2022 CRISPRa/i 篩選 |
| `Arce2024_…DESeq2_output….csv` / `Arce2025_Screen.csv` | Arce et al. 2024/2025 rest/activation |
| `TableS4_weinstock_et_al_DE.csv` | Weinstock et al. CD4 GRN |
| `Umhoefer2025_FOXP3_Teff.csv` | Umhoefer et al. 2025 FOXP3 Teff |
| `aging_DE_analysis/Terekhova2023_DEgenes.csv` / `Wells2025_variance_decomp.csv` | Terekhova 2023 / Wells 2025 aging |
| `Replogle2022_TableS3_perturb_clusters.xlsx` | Replogle et al. 2022 genome-scale Perturb-seq |
| `Tahoe100M_cellline_stats.csv` | Tahoe-100M / Arc Virtual Cell Atlas |

基因清單 overlay(`metadata/gene_lists/` 與根層):`core_essentials_hart.tsv`(Hart et al. 核心必需基因)、`kinases/gpcr_union/enzymes/ion_channels/nuclear_receptors/transporters/…`(可成藥性分類)、`gwascatalog.tsv`、`clinvar_path_likelypath.tsv`、`IUIS-IEI-list-July-2024V2.csv`(先天免疫缺陷)、`immune_effector_genes.csv`、`cytokine_receptors.tsv`、`th1_th2_known_regulators.yaml`、`protein_sumoylation_GO0016925.txt`。人類蛋白質圖譜(HPA)組織表現:`rna_tissue_consensus / rna_single_cell_*` (`.tsv.zip`)。

### 3.3 外部證據 API / 資料庫(證據層與 overlay)

| 資料庫 | 角色 | 取用狀態 |
|---|---|---|
| **Open Targets Platform** | tractability、遺傳關聯、已知藥物、safety liabilities | 快取優先;疾病轉譯用其匯出(13 適應症 / 7,528 列) |
| **ChEMBL** | bioactivity、機制、ADMET | 外部 API |
| **ClinicalTrials.gov v2** | 依標靶/適應症/期別的試驗 | 快取快照 `topic13_clinicaltrials_flat.csv` + live |
| **PubMed / PMC** | 每個標靶的文獻證據 | 快取優先 fetcher |
| **GWAS Catalog + eQTL / PheWAS** | 人類遺傳支持 | 外部 API |
| **gnomAD v4 / ClinVar / dbSNP** | 約束(LOEUF/pLI)、致病變異 | LOEUF 門檻 0.6;overlay 已種入 |
| **GTEx** | 組織表現 + eQTL(safety window) | overlay 快照 |
| **LINCS / CMap L1000** | 藥物訊號反轉(signature-to-compound) | 978-gene demo signatures 已種入 |
| **Reactome + STRING** | 機制圖(pathway + PPI) | 離線快照 `pathway_network_cache` |
| **AlphaFold** | broad-effect 標靶結構(`.cif`) | 已種入(CD3E/LAT/PLCG1/VAV1/CD247) |
| **CORUM** | 染色質/轉錄複合體 → broad_effect 清單 | `sources/broad_effect_genes.txt`(239 基因) |
| **CELLxGENE Discover / Census**(CZI) | baseline 表現與 atlas 情境 | 概念整合(§1.12) |

> ⚠️ 快取與版本規則見 `docs/cache_and_versioning_policy.md`:外部證據預設 **30 天 TTL**;標靶卡片每個 `dataset_id` 為**不可變凍結快照**。受限沙盒可能封鎖對外連線,此時 fetcher 回 `source_status: "unavailable"` 而非崩潰。

---

## 4. 引用文獻 References

> 完整清單與「如何用於驗證」在 `sources/topic07_key_papers_and_pmids_summary.md`。下表為精選;每項附 PMID/DOI。

### 4.1 主錨點與 primary T 細胞驗證
| 研究 | PMID / DOI | 角色 |
|---|---|---|
| Zhu / Dann et al.,genome-scale Perturb-seq in primary human CD4⁺ T cells | DOI `10.64898/2025.12.23.696273`(preprint) | **本專案 ground truth** |
| Shifrut et al.,primary human T-cell SLICE/CROP-seq | PMID `30449619` / `10.1016/j.cell.2018.10.024` | primary T 細胞擾動基準(GSE119450) |
| Schmidt et al.,CRISPRa/i in primary human T cells | PMID `35113687` / `10.1126/science.abj4008` | IL-2/IFN-γ 方向性基準(GSE190604) |
| Arce et al.,T-cell rest/activation circuits | PMID `39663454` / `10.1038/s41586-024-08314-y` | Rest vs Stim 驗證集 |
| Weinstock et al.,CD4 GRN inference | PMID `39395408` / `10.1016/j.xgen.2024.100671` | 網路邊 / JAK-STAT / IEI 驗證 |
| Freimer et al.,T-cell effector screens | PMID `36356142` / `10.1126/science.abn5647` | 效應/細胞激素調控子交叉核對 |
| Ho et al.,autoimmune variants + CD4 MPRA/CRISPRi | PMID `40968290` / `10.1038/s41588-025-02301-3` | 自體免疫致病變異連結 |
| Zhou et al.,in vivo T-cell CRISPR fate regulomes | PMID `37968405` / `10.1038/s41586-023-06733-x` | in-vivo 對照 |
| Knudsen et al.,CAR T modifiers | PMID `40993381` / `10.1038/s41586-025-09489-8` | 轉譯對照(FITdb) |

### 4.2 安全性與方向性參考(藥理對照)
| 藥物 / 主題 | PMID / DOI | 意義 |
|---|---|---|
| Ibalizumab(anti-CD4,HIV) | PMID `30110589` / `10.1056/NEJMoa1711460` | CD4 可成藥,但成功在抗病毒進入阻斷 |
| Teplizumab(anti-CD3,T1D) | PMID `31180194` / `10.1056/NEJMoa1902226` | T 細胞耐受;CRS/淋巴球減少警示 |
| Abatacept(CD80/86–CD28) | PMID `16785475` | 共刺激阻斷基準 |
| Cyclosporine(calcineurin/NFAT) | PMID `6350878` | 強 TCR 抑制,窄治療窗 |
| Tofacitinib ORAL Surveillance(JAK) | PMID `35081280` / `10.1056/NEJMoa2109927` | JAK 類訊號安全上限(MACE/癌/感染) |
| Fingolimod(S1P,MS) | PMID `20089952` | 運輸效應不被 in-vitro RNA 捕捉 |
| Ipilimumab(checkpoint) | PMID `20525992` | 免疫增強方向對照 |

### 4.3 方法學與統計(pipeline 驗證)
Perturb-seq PMID `27984732`(`10.1016/j.cell.2016.11.038`)· CRISP-seq `27984734` · CROP-seq `28099430`(`10.1038/nmeth.4177`)· ECCITE-seq `31011186` · direct guide capture `32231336` · Replogle genome-scale `35688146`(`10.1016/j.cell.2022.05.013`)· Norman genetic interactions `31395745` · Mixscape/Papalexi `33649593` · Perturb-CITE-seq/Frangieh `33649592` · scMAGeCK `31980032` · **SCEPTRE** `34930414` · SCEPTRE low-MOI `38760839` · **pertpy** `41476114`。

### 4.4 藥物 / 疾病 / 標靶證據
LINCS/CMap L1000 `29195078`(`10.1016/j.cell.2017.10.049`)· sci-Plex3 `31806696` · Open Problems benchmark `40595413` · OneK1K eQTL `35389779` · DICE `30449622` · Lupus PBMC atlas `35389781` · UC colon atlas `31348891` · Crohn anti-TNF `31474370` · RA synovium AMP `31061532` / phase II `37938773` · Ota perturbation+genetics `41372418`。

### 4.5 資料庫與資源
Open Targets `39657122` · ChEMBL 2023 `37933841` · CELLxGENE Discover/Census `39607691`(`10.1093/nar/gkae1142`)· scPerturb `38279009` · PerturBase `39377396` · PerturbDB `39265120` · PerturbSeq.db `40381983` · TCPGdb `41270225` · Tahoe-100M/Arc(`10.1101/2025.02.20.639398`,preprint)。

> repo 內另有機器可讀的原始查詢結果:`sources/topic0*_pubmed_*.json`、`topic13_clinicaltrials_*.json`、`topic01_openalex_round1.json` 等,可回溯每個 PMID 的檢索脈絡。

---

## 5. 說明文件與開發文件索引

### 5.1 `docs/`(權威規格與計劃)
| 檔案 | 內容 |
|---|---|
| `IMPLEMENTATION_PLAN.md` | **活的實作計劃**(每個 Wave 完成/驗證表,權威狀態) |
| `DRUG_DISCOVERY_TOOL_DEVELOPMENT_PLAN.md` | 策略層:為什麼做、功能面 |
| `data_dictionary.md` | 每個產出欄位逐欄定義 |
| `de_and_baseline_spec.md` | NTC 基線與 DE 方法學 |
| `data_governance_checklist.md` | 資料治理與授權(`unknown≠0` 原則) |
| `cache_and_versioning_policy.md` | 快取與版本失效政策 |
| `external_overlay_integration_concept.md` | 安全性 + 膜蛋白 overlay 整合概念(§1.12) |
| `architecture_refactor_plan.md` | API 分層/模組拆分重構計劃 |
| `next_phases_plan.md` / `improvement_roadmap.md` | 後續階段與改進路線 |
| `server_northstar.md` | 對外服務/資料入口 north-star |
| `concept_dictionary.md` / `compass_concept_integration_plan.md` | 概念字典 / COMPASS 概念整合 |
| `sandbox_blocked_tasks.md` | 沙盒受限、需在他處執行的任務 |
| `API.md` | 消費端 API quickstart |
| `mvp-research/` | MVP 研究交接:資料清單、候選 shortlist、PR10 執行報告、LINCS/ADC/pathway 資料來源建議、視覺化與 pipeline 子資料夾 |

### 5.2 Wiki(導覽層,本資料夾)
`Home`(介紹)· `Development-Guide`(開發說明)· `Manual`(本頁)· `Maintenance`(維護)· `Roadmap`(路線圖)· `Plan`(計劃)· `Tech-Debt`(技術債)· `_Sidebar` · `README`。

### 5.3 `sources/` 研究主題索引(topic01–16)
| Topic | 主題 |
|---|---|
| 01 | 本地可成藥標靶 / CD4 藥物開發總結 |
| 02 | 既有工具盤點 tool inventory |
| 03 | 開放資料盤點與策略 open data inventory |
| 04 | 藥物開發需求與就緒度檢查清單 |
| 05 | 成功藥物 benchmark |
| 06 | 工具箱架構總結 |
| 07 | **關鍵論文與 PMID**(§4 來源) |
| 08 | 批次效應校正 |
| 09 | EDA 報告與輸出 |
| 10 | 廣泛掃描相關資訊 |
| 11 | 突破方向與工具箱機會 |
| 12 | 臨床試驗痛點 / 論文限制與未來工作 |
| 13 | CD4 臨床試驗進度 + ClinicalTrials 快照 |
| 14 | 方法學核心 / target card 規格 / scRNA 生統驗證方法 |
| 15 | CD4 上下游框架 + seed modules |
| 16 | 藥物開發工具規格 |
其他:`project_decision_log.md`(決策日誌)、`project_roadmap.md`、`release_notes_m3_5_upload_import.md`、`broad_effect_genes.txt`(239 基因)、`target_tool_cache/`(建構快取,含 `_evidence/<gene>.json` 種子)。

---

## 6. Commit 紀錄摘要

- **總 commit 數**:229(2026-07-05 初始快照 → 2026-07-08 開發說明頁)
- **已合併 PR**:15(#1–#15,主要開發分支 `claude/drug-discovery-tool-plan-258jof`)
- **作者**:erichuang777777(151)、Claude(78)
- **變更熱區(依路徑 commit 數)**:`docs/` 141 · `tests/` 31 · `sources/` 27 · `src/3_DE_analysis/` 11 · `frontend/` 3 · `wiki/` 3

### 開發波次時間線(對應 Roadmap)
| PR / 波次 | 主題 |
|---|---|
| Initial snapshot | 論文原始分析流程 + metadata + sources 研究基礎 |
| PR #1 · Wave 1 | 可 import 卡片建構、就緒度引擎(R0–R5)、上傳合併迴圈、儀表板串接 |
| Wave 2 | broad-effect 隔離(239 基因)、druggability/safety overlay、校準 harness |
| Wave 3 | 外部證據層(CT/PubMed/Open Targets)、provenance footer、§1.5 誠實 descope |
| Wave 4 | 疾病轉譯器(13 適應症 / 7,528 關聯) |
| Wave 5 | 儀表板視覺化(QC funnel / 穩健性散點 / 證據組成) |
| Wave 6 | 基因識別解析、三態 result_status、CRE schema、模糊搜尋、測試、資料字典、治理/版本政策 |
| PR #10 | 外部證據快照(Open Targets/CT/PubMed)、Reactome+STRING 機制圖、gnomAD v4、AlphaFold 結構 |
| 架構重構 Phase 0–4 | config/contracts 單一來源、common/ 去重、API god-module 拆成 per-resource routers、前端獨立化 |
| 後續 | LINCS 連結器、機制圖、族群假設引擎、個體概念剖面(COMPASS-analog)、圖表精修(53 張)、改進路線圖 |
| 近期 | Wiki 初始化(zh-TW 五頁)+ 開發說明頁 + 本手冊 |

> 完整逐筆:`git log --oneline`;決策脈絡:`sources/project_decision_log.md`。

---

## 7. 附錄:關鍵常數與縮寫

**關鍵常數**
- `KD_NOT_MEASURABLE_EXPRESSION_FLOOR = 0.001`(重用資料集 `high_confidence_no_effect_guides` 定義)
- 外部證據 `TTL_SECONDS_DEFAULT = 30 天`;批次證據端點上限 `MAX_EVIDENCE_GENES = 50`
- gnomAD LOEUF 門檻 `0.6`;broad-effect 清單 239 基因
- 四層版本:`engine_version` / `dataset_version` / `schema_version` / `signature_set_version`

**縮寫**
DE = 差異表現;NTC = 非標靶對照(non-targeting control);kd = 敲低(knockdown);CRISPRi = CRISPR 干擾;GRN = 基因調控網路;TSS = 轉錄起始位點;LOEUF/pLI = gnomAD 基因約束指標;MOI = 感染複數;IEI = 先天免疫缺陷;VCP = Virtual Cells Platform(CZI)。

**決策語彙**:advance(推進)/ validate(驗證)/ watchlist(觀察)/ deprioritize(降級);就緒度 R0–R5;kd_status = confirmed / weak / not_measurable / not_assessed。

---

> 本手冊為索引與地圖。任何數字或宣稱如與 `docs/` 或 suppl table 逐欄定義衝突,以後者為準,並請開 Issue 回報。
