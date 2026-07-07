# 加強建議：用平台連結器補實 readiness 的空領域
### 對接 main（Wave 1–6 已完成）· 定位：不重複既有 Tech-Debt review，補上「連結器實測」新證據層

**產出者：** 本地研究 session · **對接 commit：** main @ 69f5b3fc（PR #2 已合併）· **相關 open PR：** #3（wiki + mvp-research）
**方法：** 讀取 main 全部相關原始碼 + wiki 五頁 + IMPLEMENTATION_PLAN，並用平台 MCP 連結器對 8 個候選標的實跑富集，驗證哪些「descope/卡住」項目現在可解。

---

## 0. 先確認：我沒有要重做的部分

repo 的 `wiki/Tech-Debt.md` 已有一份紮實的 10 項 code review（A.1–A.7 正確性、B.8–9 效能、C.10 重複、D descope、E 驗證缺口）。**那份 review 我認同，不重複。** 尤其 A.1（`_kd_status` 把 NaN 基線當敲低失敗，違反 repo 自己的 `unknown≠0`）確實應列為上傳功能的合併前阻擋項。

本報告只加它沒涵蓋的一件事：**用連結器實跑，證明被標為「卡住/等佈署」的證據領域，現在就能填。**

---

## 1. 核心發現：`fetch_open_targets` 的 docstring 與實作不符（新問題，Tech-Debt 未列）

- **位置：** `src/3_DE_analysis/external_evidence_cache.py` · `fetch_open_targets`
- **問題：** docstring 寫「Query ... for tractability/genetics/safety」，但實際 GraphQL query 只做 `search(entityNames:["target"]){hits{id name}}` —— **只回傳 target 的 id/name，完全沒有拉 tractability、遺傳關聯、安全性欄位。**
- **後果：** `readiness_engine` 的 `_tractability` / `_human_genetic` / `safety_window_score` 因此拿不到外部值，只能靠本機 `metadata/gene_lists/*` overlay，大量停在 `"unknown"`。Wave 3 宣稱「外部證據層」落地，但 Open Targets 這條的實質內容並未進入 readiness。
- **這不是 descope：** Tech-Debt §D 只說「此沙盒無 Open Targets fetch 工具，等佈署」。但真正的 gap 是 query 本身寫得太淺——即使有網路也拉不到那些欄位。

---

## 2. 實測證據：descope 「Open Targets genetics（等佈署）」現在可解除

我從**這個沙盒**直接測試，四個外部來源全部可連（HTTP 200）：Open Targets GraphQL、ChEMBL、ClinicalTrials.gov v2、GWAS Catalog。平台另有封裝好的 MCP 連結器（`mcp-clinical-genomics` 含 Open Targets、`mcp-chembl`、`mcp-clinical-trials`、`mcp-human-genetics`、`mcp-variants`、`mcp-expression`、`mcp-drug-regulatory`、`mcp-pubmed`），比裸打 API 穩定。

用連結器對 top-8 候選實跑，三個原本空/半空的 readiness 領域都填出有意義的分層（見 `connector_enrichment_demo.csv`）：

| gene | flag | 可小分子 | 可抗體 | OT 遺傳關聯 | gnomAD LOEUF | 安全窗口 |
|---|---|---|---|---|---|---|
| CD3E | immune | ✓ | ✓ | **0.915** | 0.701 | wider |
| LAT | immune | ✗ | ✓ | 0.744 | 0.497 | moderate |
| PLCG1 | immune | ✓ | ✓ | 0.661 | 0.487 | moderate |
| VAV1 | immune | ✓ | ✓ | 0.000 | **0.344** | **tight** ⚠ |
| TADA2B | broad_effect | ✗ | ✗ | 0.421 | 0.599 | moderate |
| SGF29 | broad_effect | ✓ | ✗ | 0.362 | 0.606 | wider |
| SENP5 | broad_effect | ✗ | ✗ | 0.393 | 0.407 | moderate |
| UBXN1 | broad_effect | ✗ | ✗ | 0.042 | 0.719 | wider |

**三個可立即填的 readiness 領域：**
1. **`tractability_modality`** ← Open Targets tractability bucket（SM/AB/PROTAC…）。目前只靠本機 druggable-class 清單，覆蓋率有限。
2. **`human_genetic_support`** ← Open Targets `associatedDiseases` 的 `genetic_association` datatype 分數。CD3E 0.915 vs UBXN1 0.042 是真實的分層訊號，目前 readiness 拿不到。
3. **`safety_window_score`** ← gnomAD LOEUF/pLI。**這是 repo 目前完全沒有的維度。** VAV1（LOEUF 0.344、pLI≈1.0）被標為安全窗口窄——一個對「抑制某標的是否安全」極關鍵、且免費可得的訊號。

---

## 3. 建議（按 ROI 排序，每項獨立可交付，全部遵守既有護欄）

### 🔴 建議 1 — 修 `fetch_open_targets` query，真正拉 tractability + genetics（小，解鎖最大價值）
- 把 query 從 `search{hits{id name}}` 換成用 `ensemblId` 查 `target{ tractability{modality value label} associatedDiseases{rows{score datatypeScores{id score}}} }`（我上面實跑的 query 可直接用）。
- 需要 gene symbol → Ensembl ID：repo 已有 `gene_identifier_resolver.py`（Wave 6 B1），直接串。
- 把結果餵進 `readiness_engine` 的 `_tractability` / `_human_genetic` overlay，讓這兩領域從 `unknown` 升級。
- **驗收：** CD3E/PLCG1 的 `tractability_modality` 非空、`human_genetic_support` 為真實分數；連結器缺席時維持既有 `source_status:"unavailable"` 降級不崩。

### 🔴 建議 2 — 新增 `safety_window_score` 的 gnomAD 約束來源（小，補一個全新維度）
- `readiness_engine` 目前 `safety_window_score` 幾乎全 `unknown`。加一個 gnomAD LOEUF/pLI fetcher（本報告是用連結器 `mcp-variants` 的 `gene_constraint` 實測取得；裸 gnomAD GraphQL 為部署時的替代管道，本輪未實測）。
- 解讀規則（保守、可辯護）：LOEUF < 0.35 → `tight`（LoF 高度不耐，抑制安全窗口窄）加一個 **soft 註記**，不自動封頂（因為 LoF 不耐 ≠ 藥理抑制不耐，只是風險提示）。
- **與 §1.12 對接：** wiki Roadmap 提到負責人有 CellxGene 安全性資料與內部膜蛋白庫要填這領域。gnomAD 約束可作為**在那些私有資料到位前的免費 baseline**，不衝突、可疊加。
- **驗收：** 每張卡片有 `gnomad_loeuf` / `gnomad_pli` 欄位與 `safety_window` 分級；VAV1 被標 tight。

### 🟡 建議 3 — 外部證據獨立佐證 C7 broad_effect，可作為校準檢查
- 實測顯示 broad_effect 基因（TADA2B/SENP5/UBXN1）在外部證據上一致偏弱：可成藥性低、遺傳關聯低、關聯疾病少或非免疫。這與 C7 紅旗**獨立一致**。
- 建議在 `calibration.py` 加一條檢查：「被 broad_effect 隔離的基因，其 Open Targets 遺傳關聯分數分佈應顯著低於 immune_candidate」——若某天資料變動讓這條不成立，是隔離清單需複查的訊號。
- **驗收：** calibration 報告多一列 broad_effect vs immune 的外部證據對比。

### 🟡 建議 4 — 補富集後的臨床試驗/文獻連結（Wave 3 已接骨架，補實內容）
- `fetch_trials` / `fetch_pubmed_literature` 的實作看來完整，只是同樣受「等佈署網路」限制。用連結器 `mcp-clinical-trials` / `mcp-pubmed` 可在 build 階段離線批次種入 top-N 基因的真實試驗/文獻，填滿卡片的 trials/literature 子面板。

---

## 4. 對護欄的遵守（重要）

上述全部遵守 repo 既有五原則：
- **`unknown≠0`**：連結器缺席時維持 `source_status:"unavailable"`，不塞 0。
- **紅旗覆蓋**：safety gnomAD 只加 soft 註記，不僭越既有封頂邏輯；C7 隔離不動。
- **CRISPRi≠藥理學**：tractability/safety 是「標的層屬性」證據，卡片注意事項不變。
- **provenance 是欄位**：每個連結器抓的值都帶 `fetched_at` + 來源版本（沿用 external_evidence_cache 既有快照格式）。
- **cache-first、離線批次、絕不進請求路徑**：全部在 build 階段跑，dashboard 只讀快照。

---

## 5. 交付物
- `ENHANCEMENT_連結器加強建議.md`（本文件）
- `connector_enrichment_demo.csv` — 8 個候選標的的實測富集結果（tractability/genetic/gnomAD），證明三領域可填
