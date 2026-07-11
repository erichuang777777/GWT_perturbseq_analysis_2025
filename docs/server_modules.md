# Server 模組參考 Server Module Reference

> 一頁集中說明 API server 的**所有功能模組**:每個模組的用途、主要端點、輸入/輸出與注意事項。server 由 `api/app.py` 組裝,**每個 router 各自 try/except 載入**——單一模組載入失敗不會拖垮整個 API,`GET /api/health` 會逐能力回報 available/degraded。互動式 OpenAPI 文件在執行後的 `/docs`。
>
> 啟動:`uvicorn api.app:app --app-dir src/3_DE_analysis`(或相容 shim `target_card_api:app`)。
> 相關:消費端 quickstart `docs/API.md`;分層架構 `docs/architecture_refactor_plan.md` 與 `wiki/Manual.md` §2.2;方法學 `docs/technical_methods.md`。

---

## 0. 全域約定(所有模組適用)

- **資料集為不可變快照**:每次 build 產生新的 `dataset_id`(UUID);多數讀取端點以 `/{dataset_id}` 定址。
- **四層版本**:`engine_version` / `dataset_version` / `schema_version` / `signature_set_version`,附於產出與 `/api/health`。
- **`unknown ≠ 0`**:未建置的證據領域回明確 `"unknown"` + 覆蓋率,絕不補 0。
- **紅旗覆蓋**:`readiness` 的決策不論統計強弱,命中 essential / broad-effect / off-target / kd 未確認 / 批次混淆即封頂。
- **描述性 vs 決策性分離**:`mechanism`、`individual_concept`(概念層 M01–M20)、safety overlay 等**永不餵**就緒度決策,僅供人類解讀。
- **外部證據 cache-first**:預設 30 天 TTL;受限環境回 `source_status: "unavailable"` 而非崩潰。
- **上傳隔離**:使用者上傳資料集以 `usr_` 命名空間隔離,永不混入 GWT 參考集。

---

## 1. 功能模組(`src/3_DE_analysis/api/routers/`)

### 1.1 `build` — 資料集建構
把上游 supplementary tables 建成標靶卡片資料集。
| 端點 | 說明 |
|---|---|
| `POST /api/run/target-card` | 建構新資料集 → 回傳新 `dataset_id`(不可變) |
| `GET /api/datasets` | 列出已建資料集 |
| `GET /api/status/{dataset_id}` | 建構狀態 / metadata(含版本戳記) |

### 1.2 `cards` — 標靶卡片與檢視
資料集的核心讀取層:排序、分流、單標靶 dossier、匯出。
| 端點 | 說明 |
|---|---|
| `GET /api/targets/{dataset_id}` · `/{target_id}` | 卡片清單 / 單一標靶完整卡片 |
| `GET /api/immune_ranked/{dataset_id}` | 免疫相關排序 |
| `GET /api/robust_ranked/{dataset_id}` | 穩健性排序(跨 donor/guide) |
| `GET /api/switches/{dataset_id}` | 情境切換(condition-specific)標的 |
| `GET /api/triage/{dataset_id}` · `/{target}` | 分流視圖 / 單標靶分流 |
| `GET /api/modules/{dataset_id}` | 概念模組 overlap 分數(M01–M20,二元 overlap) |
| `GET /api/summary/{dataset_id}` · `/api/options/{dataset_id}` | 摘要統計 / 篩選選項 |
| `GET /api/exports/{dataset_id}` · `/api/reports/{dataset_id}` | 匯出(含 provenance) / 報告 |

### 1.3 `readiness` — 就緒度引擎
| 端點 | 說明 |
|---|---|
| `GET /api/readiness/{dataset_id}` | 12 領域評分 → R0–R5 → 紅旗覆蓋 → 決策(advance/validate/watchlist/deprioritize),附 `score_cap_reason` / `next_step` |

### 1.4 `calibration` — 校準 harness
| 端點 | 說明 |
|---|---|
| `GET /api/calibration/{dataset_id}` | 正對照回復、負對照(`not_measurable`)封頂、藥物軸富集、排序穩定度 |

### 1.5 `evidence` — 外部證據層(cache-first)
| 端點 | 說明 |
|---|---|
| `GET /api/evidence/{gene}` | 單基因的 ClinicalTrials/PubMed/Open Targets 快照(附 `fetched_at`) |
| `POST /api/evidence/build` | 批次建證據(上限 `MAX_EVIDENCE_GENES=50`,背景任務,可 `force=True`) |

### 1.6 `disease` — 疾病轉譯
| 端點 | 說明 |
|---|---|
| `GET /api/disease` | 支援的適應症清單(13 個自體免疫) |
| `GET /api/disease/{disease_name}/targets/{dataset_id}` | 依疾病-基因關聯(Open Targets 匯出)排序標的 |
| `GET /api/genetic_double_support/{dataset_id}` | 遺傳學雙重支持標的 |

### 1.7 `disease_drug` — 疾病-藥物證據配對
| 端點 | 說明 |
|---|---|
| `GET /api/disease-drug-evidence` | 標的對接疾病與已知藥物證據(含 drug class) |

### 1.8 `genes` — 基因識別與搜尋
| 端點 | 說明 |
|---|---|
| `GET/POST /api/genes/resolve` | 以 Ensembl gene ID 為主鍵解析別名 |
| `GET /api/genes/status` | 解析器狀態 / 覆蓋率 |
| `GET /api/search` | difflib 模糊搜尋(容錯) |
| `GET /api/cre/{gene_query}` | CRE schema 佔位查詢(repo 內無 CRE 資料時回空但有效契約) |

### 1.9 `mechanism` — 機制圖
| 端點 | 說明 |
|---|---|
| `GET /api/mechanism-graph/{gene}` | Reactome + STRING 機制/交互作用圖(**描述性,永不餵決策**) |

### 1.10 `population` — 族群 LoF 假設引擎
| 端點 | 說明 |
|---|---|
| `GET /api/population-hypothesis/{gene}` | 以族群 LoF-burden 產生假設(研究用) |

### 1.11 `imports` — 使用者上傳(暫存優先)
研究者上傳自有 DE → 欄位對應 → 核准 → 合併成卡片,全程 `usr_` 命名空間隔離。
| 端點 | 說明 |
|---|---|
| `POST /api/imports` · `GET /api/imports` · `/{import_id}` | 建立上傳 / 列表 / 查詢 |
| `GET /api/imports/{id}/preview` | 預覽 |
| `GET /api/imports/{id}/mapping/suggestion` · `POST …/mapping` | 欄位對應建議 / 提交對應 |
| `POST /api/imports/{id}/approve` · `POST …/merge` | 核准 / 合併成 `usr_` 卡片 |

### 1.12 `individual_concept` — 個體概念剖面(COMPASS-analog)
| 端點 | 說明 |
|---|---|
| `POST /api/individual-concept-profile` | 將樣本投影到 20 個概念模組(M01–M20)的概念活化剖面(**描述性,永不餵決策**;見 §2) |

### 1.13 `meta` — 覆蓋率 / 系統
| 端點 | 說明 |
|---|---|
| `GET /api/meta/coverage/{dataset_id}` | 各證據領域覆蓋率 |
| `GET /api/health`(app 層) | 整體狀態、逐能力 available/degraded、engine/schema 版本 |

---

## 2. 概念層 — 免疫概念模組 M01–M20

`cards` 的 `/api/modules` 與 `individual_concept` 都用到這 20 個 **CD4 T 細胞免疫概念模組**(concept-bottleneck layer,COMPASS-analog)。它們把每個標的/樣本投影到有生物學意義的免疫概念(seed-gene overlap 計分,可手算稽核)。

**權威文件**:[`concept_dictionary.md`](concept_dictionary.md)(逐模組 seed genes、primary_question、生物學意義)。
**來源**:`sources/topic15_cd4_tcell_upstream_downstream_seed_modules.csv`;解析 `api/deps.py::_load_modules`/`_module_scores`;結構驗證 `contracts/concept_schema.py`。
**關鍵不變量**:概念分數**永不餵** `readiness_call`/`_stage()`——純描述性。

| ID | 名稱 | 類別 | ID | 名稱 | 類別 |
|---|---|---|---|---|---|
| M01 | TCR_Core_Receptor | Upstream | M11 | NFkB_Axis | Downstream |
| M02 | TCR_Proximal_Signaling | Upstream | M12 | AP1_NFAT_Activation | Downstream |
| M03 | Costimulation | Upstream | M13 | PI3K_AKT_mTOR | Upstream |
| M04 | Checkpoint_Module | Upstream | M14 | Metabolic_Switch | Downstream |
| M05 | IL2R_JAKSTAT | Upstream | M15 | Maturation_Memory_Trafficking | Downstream |
| M06 | IFN_Response | Upstream | M16 | Chemotaxis_Tissue_Infiltration | Downstream |
| M07 | Th1_Polarization | Downstream | M17 | Cytotoxic_Like_Differentiation | Downstream |
| M08 | Th2_Polarization | Downstream | M18 | Exhaustion_Escape | Downstream |
| M09 | Th17_Polarization | Downstream | M19 | Memory_Fate_Program | Downstream |
| M10 | Treg_Modulation | Downstream | M20 | Cell_Cycle_Proliferation | Downstream |

---

## 3. 載入與容錯

`api/app.py` 依序載入 13 個 router(`build, cards, readiness, calibration, evidence, disease, genes, population, imports, mechanism, individual_concept, disease_drug, meta`),每個各自 `try/except`:某模組因缺選用相依或 bug 而 import 失敗時,其餘 API 仍正常上線,`GET /api/health` 標記該能力為 degraded(「一條壞邊不拖垮核心」原則,對應架構重構 Phase 4)。

> 端點路徑取自 `src/3_DE_analysis/api/routers/*.py` 的 `@router` 定義;如與程式衝突,以程式與執行後 `/docs` 的 OpenAPI 為準。
