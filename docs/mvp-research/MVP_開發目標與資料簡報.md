# MVP 開發簡報：一基底 · 三系統
### CD4 T 細胞 Perturb-seq 標的探索工具（原型，目的＝證明可行）

**定位：** 最小可用原型（MVP），目標是**展示這三件事做得到**，非真實臨床決策。
**分工：** 本文件負責「開發目標 + 資料蒐集 + 架構方向」；實作在雲端（GitHub）進行。
**對接：** 擴充 `docs/DRUG_DISCOVERY_TOOL_DEVELOPMENT_PLAN.md` 與 `docs/IMPLEMENTATION_PLAN.md`，不重建。
**可行性狀態：** 三套系統的資料鏈本地全部實測貫通（見 §5 證據）。

---

## 1. MVP 要證明的三件事（成功標準）

| 系統 | 一句話目標 | MVP「證明可行」的驗收 |
|---|---|---|
| **系統一** 用現有資料找新標的 | 從 GWT DE 資料自動產出可信、可追溯、已分級的標的候選卡 | 從公開 DE 表產出排序 target cards；泛效應/必需基因被紅旗封頂在 watchlist；真免疫基因仍可 advance |
| **系統二** 使用者上傳資料 | 使用者上傳自己的 DE/guide 表或 h5ad，用**同一套規則**被評分 | generic upload → 欄位對映 → 核准 → 併入 → 產出 `usr_` 卡片 → 跑同一 readiness engine，端到端可跑 |
| **系統三** 臨床/人群證據整合 | 把每個標的對應到人類遺傳、可成藥性、臨床試驗證據，回答「離臨床多遠」 | 對候選標的即時拉 Open Targets/ChEMBL/GWAS/ClinicalTrials，填補 readiness 的 `unknown` domain |

**產品紅線（原型即遵守，寫進 UI 與 scoring）：** 不宣稱藥物發現／已驗證標的／臨床就緒／病人分層／療效安全預測。CRISPRi 敲低 ≠ 藥理干預。系統三只輸出「證據 + 假設 + 下一步驗證計畫」，不輸出處方。病人層決策留一個**架構隔離、預設關閉**的擴充點。

---

## 2. 資料資源（已盤點，見 data_resource_inventory.csv）

### 2a. 核心輸入（MVP 直接可用，本地已下載驗證）
公開 S3 資料桶 `s3://genome-scale-tcell-perturb-seq/marson2025_data/`（匿名可讀，論文 Zhu & Dann 2025 / CZ Biohub）：
- `suppl_tables/DE_stats.suppl_table.csv` — **4.82 MB，33,983 個 perturbation×condition，11,526 個獨特標的**，16 欄位直接對應 target-card schema。
- `suppl_tables/sgrna_library_metadata.suppl_table.csv` — 9.94 MB，26,504 guides，含 off-target / TSS 距離。
- `suppl_tables/sample_metadata.suppl_table.csv` — 12 樣本，含 donor demographics（age/sex/ethnicity/batch）。

### 2b. 深度輸入（雲端重運算，MVP 可選）
同資料桶的 h5ad/h5mu：`GWCD4i.DE_stats.h5ad`(16.8GB)、`GWCD4i.pseudobulk_merged.h5ad`(44.6GB)、`by_guide/by_donors.h5mu`(29/17GB)、12 個 cell-level `D*_*.assigned_guide.h5ad`(**合計約 1.7 TB**)。→ 系統二重運算路徑與系統一深度驗證用；不進 MVP 請求路徑。

### 2c. 外部證據（系統三，平台連結器，本地實測可連）
| 連結器 | 涵蓋 | 狀態 |
|---|---|---|
| `mcp-clinical-genomics` | Open Targets（tractability/遺傳關聯/已知藥）+ ClinGen + CIViC | ✓ 實測（IL2RA 回 28 tract bucket、1469 疾病） |
| `mcp-chembl` | 生物活性、機轉、ADMET | ✓ 200 |
| `mcp-clinical-trials` | ClinicalTrials.gov v2 | ✓ 200 |
| `mcp-human-genetics` | GWAS Catalog、eQTL、FinnGen/BBJ PheWAS | ✓ 200 |
| `mcp-variants` | gnomAD constraint、ClinVar、dbSNP | 可用 |
| `mcp-expression` | GTEx 表現 + eQTL | 可用 |
| `mcp-drug-regulatory` | Drugs@FDA、SPL labels | 可用 |
| `mcp-pubmed` | PubMed / PMC 文獻 | 可用 |

### 2d. 已在 repo 內的 overlay（離線可用）
`topic05_successful_drug_benchmarks.csv`、`metadata/gene_lists/*`（druggable class）、`topic13_clinicaltrials_flat.csv`、`IUIS-IEI-list`、`immune_effector_genes.csv`、1k1k + 淋巴球 LoF 結果。

---

## 3. 架構：一基底 + 三入口

```
  系統一 內部DE ─┐
  系統二 上傳    ─┼─► [正規化為 target-card schema] ─► [證據分解] ─► [readiness R0–R5]
  系統三 臨床證據 ┘        （同一契約）             （同一規則）     （紅旗封頂）
                                                                        │
                                                     排序 target cards + 下一步驗證計畫
```
基底＝統一的 `target × condition` 卡片契約 + 證據分解引擎 + readiness engine + provenance/版本戳。三系統只是「證據來源」不同，評分規則唯一。已存在的實作：`build_target_cards.py`、`readiness_engine.py`、`target_card_api.py`、`target_card_dashboard.py`、`import_manager.py`、`9_cell_integration/`。

---

## 4. 雲端開發目標（按 ROI 排序，每項獨立可交付）

1. **系統一 — C7 泛效應/必需基因隔離**（小、純離線）：`readiness_engine.py` 加獨立 `broad_effect` 紅旗，封頂 watchlist。基因集＝`core_essentials_hart.tsv` + CORUM 染色質/轉錄複合體 + EDA 點名清單。**驗收：** MED12/CREBBP/KDM1A 不再 advance，PLCG1/CD247/ITK 仍可。
2. **系統二 — 確認上傳合併主線可跑**（IMPLEMENTATION_PLAN 標記 U4/U5 已在分支 done）：確認 PR #1 合併、主線重跑端到端（upload→map→approve→merge→`usr_` cards→readiness）、補邊界情況。
3. **系統三 — 本地譯譯 overlay**（小、離線）：把 `metadata/gene_lists/*` 的 druggable class 暴露成卡片欄位（`druggable_class`/`tractability_modality`）。
4. **系統三 — external_evidence_cache**（連結器、cache-first、離線批次、絕不進請求路徑）：`external_evidence_cache.py`，用上述 MCP 連結器抓 Open Targets/GWAS/ClinicalTrials/ChEMBL，寫 `sources/target_tool_cache/_evidence/<gene>.json`（帶 `fetched_at`/`source_version`，連結器缺席時降級 `source_status:"unavailable"` 不崩）。填補 readiness 的 `unknown` domain，解鎖 R3→R4。
5. **系統三 — 病人層擴充點佔位**：只建隔離介面 + 關閉開關，不實作決策邏輯。

---

## 5. 可行性證據（本地實測，非推測）

- **系統一資料鏈：** 從 DE 表套 MVP 核心門檻（n_cells≥200 & on-target 顯著 & 無 off-target & DE≥50）→ **2,131 列通過、1,235 個獨特標的**，三條件均衡（Rest 712 / Stim8hr 711 / Stim48hr 708）。見 candidate_shortlist_top15.csv。
- **C7 必要性被真實資料證明：** 以 trans-effect 廣度排名的 Top-15，前段被染色質機器基因（TADA2B/SGF29/MED12/CCNC/SUPT20H/TADA1/DENR）主導，混在真 TCR 訊號基因（CD3E/LAT/PLCG1/VAV1/CD247）之間 → 沒有 `broad_effect` 封頂，泛效應基因會假性領先。
- **系統三證據鏈 + 佐證 C7：** 對候選拉真實 Open Targets——CD247/PLCG1 關聯免疫疾病且有小分子/抗體可成藥性；MED12 可成藥性近零、關聯發育綜合症（FG syndrome）而非免疫 → 外部證據**獨立**支持把 MED12 隔離。
- **系統二：** `import_manager.py` staging→驗證→context→審核閘門已存在；IMPLEMENTATION_PLAN 記錄合併迴圈 U4/U5 已在分支端到端測過（TestClient）。

---

## 6. 交付物清單

- `MVP_開發目標與資料簡報.md`（本文件）
- `candidate_shortlist_top15.csv` — 系統一候選標的（含 broad_effect 標註）
- `data_resource_inventory.csv` — 20 項資料/證據資源盤點（含存取方式、規模、驗證狀態）
