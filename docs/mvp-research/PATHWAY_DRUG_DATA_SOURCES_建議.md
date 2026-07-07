# 通路分析 + 藥物開發：資料源盤點與整合建議

**觸發問題：** 通路分析與藥物開發兩條下游任務,是否有更多專一性資料該納入,讓平台更完整。
**方法：** 核對 repo 現有基礎 + 實測平台連結器,只列出真正驗證可用的。

---

## 1. 通路分析——repo 已有能力,但停在 notebook,沒有產品化

**現狀確認：** `src/6_functional_interaction/downstream_go_enrichment.ipynb` 已經用 `gseapy` + Enrichr(`GO_Biological_Process_2025` 函式庫)+ STRING 做過富集分析,但這是探索性分析,**沒有接進** `build_target_cards.py` / `readiness_engine.py` / dashboard。也就是說能力存在,但每張標的卡片上看不到通路資訊。

**實測驗證(本地,真實資料)：** 用平台連結器對 CD3E / PLCG1 測試,結果生物學正確：
- **Reactome**(`mcp-genes-ontologies`)：CD3E 命中「Downstream TCR signaling」「Phosphorylation of CD3 and TCR zeta chains」；PLCG1 有 47 個低層級通路。
- **STRING**(`mcp-protein-annotation`)：CD3E 網路正確連到 CD247、CD3D(真實 TCR-CD3 複合體夥伴,score 0.999)。

**建議：把這兩個連結器接進卡片,不是重做 notebook 的事,是把已驗證能力搬進 pipeline。**

| 資料源 | 連結器 | 補什麼 |
|---|---|---|
| **Reactome** | `mcp-genes-ontologies` `map_reactome_pathways` | 每個標的所屬通路清單——可用來給"同通路標的"分組,或檢查候選標的是否落在預期的 TCR/cytokine 通路 |
| **STRING** | `mcp-protein-annotation` `get_string_network` | 標的的直接交互作用夥伴——可用來驗證 broad_effect 隔離的合理性(複合體夥伴應該一起被隔離或一起免疫相關) |
| **GO annotations** | `mcp-genes-ontologies` `get_go_annotations` | 補 GO term,供富集分析背景 |

**專一性資料補強建議：**
- `gseapy`/Enrichr notebook 已用的 `GO_Biological_Process_2025` 函式庫可保留在離線批次(不必即時查),但**建議額外納入 Hallmark/immunologic signature 類的 gene set**(如 MSigDB C7 immunologic signatures)——目前搜尋平台連結器沒有直接命中 MSigDB,若需要建議用 gseapy 離線抓取一次,存成 `metadata/gene_lists/`,走現有的 overlay 機制,不需要新連結器。

---

## 2. 藥物開發——已有的三層要收斂成一致管線

目前藥物開發相關證據分散在三個地方，這次盤點順便整理清楚各自角色：

| 現有模組 | 角色 |
|---|---|
| `disease_translator.py` | 標的 → 疾病關聯(Open Targets genetics) |
| `external_evidence_cache.py` | 標的 → 試驗/文獻快照 |
| 本次新增(先前討論)`match_disease_drug_evidence` | 疾病+藥物 → 證據匹配,含真實核准適應症核對(basiliximab 案例) |

**這次盤點新增的專一性資料建議：**

### 2a. 機轉/ADMET 深度——ChEMBL(已在用,可加深)
`mcp-chembl` 除了 `drug_search`/`compound_search`,還有 **`get_mechanism`**(機轉分類)、**`get_admet`**(吸收代謝分佈排除性質)。目前平台只用了藥物存在性查詢,沒拉機轉細節。對候選藥物加 `get_mechanism` 可以回答「這個藥是激動劑/拮抗劑/降解劑」——這對「CRISPRi 敲低 ≠ 藥理干預」的護欄特別重要：**如果已知藥物是激動劑而 CRISPRi 是敲低(功能喪失方向相反),這個配對在邏輯上就不成立,系統該標記出來,而不是含糊地說「有已知藥物」。**

### 2b. 藥物基因交互作用——DGIdb / PharmGKB(搜尋平台連結器未命中,需另外評估)
搜尋平台目錄沒有直接對到 DGIdb 或 PharmGKB 的連結器。這類資料庫補的是「已知藥物-基因交互作用的策展清單」，比 ChEMBL 原始生物活性資料更精簡。若需要，建議走**離線批次下載**(DGIdb 有公開 API/批量下載)存成本地 overlay，不必即時查詢。

### 2c. 可購買化學空間——ZINC(已確認可用,但用途要對應清楚)
`mcp-zinc` 可查 ZINC22 可購買化合物庫、SMILES 相似性搜尋。**這個工具的定位要說清楚：它服務的是「找相似化合物做虛擬篩選/對接」,不是「這個標的有沒有藥物」的問題**——後者是 ChEMBL/Open Targets 的角色。若平台未來要做「這個標的沒有已知藥物,但化學空間裡有沒有類似口袋的化合物可試」的探索,才用得到 ZINC,現階段 MVP 不建議納入,避免 scope creep。

### 2d. CAR-T/immuno 特定——先前已驗證的 CD3E 案例延伸
先前查詢已確認 CD3E 有 22 個已知藥物,其中多個是**雙特異性 T 細胞 engager(BiTE)**——blinatumomab、mosunetuzumab、glofitamab 等,這類藥物的結構原理與 CAR-T 的 CD3 活化域機轉同源。**這代表 GWT 篩選出的 TCR 近端訊號標的,天然對應到 CAR-T 領域最活躍的藥物類別。** 建議在 `match_disease_drug_evidence` 的藥物清單裡加一個 `drug_class` 分類欄位(標記 BiTE/CAR-T-related/small molecule/mAb),讓使用者一眼看出哪些候選標的已經是 CAR-T 領域的成熟靶點。

---

## 3. 整合建議優先序

| 建議 | 效益 | 複雜度 |
|---|---|---|
| 🔴 Reactome + STRING 接進卡片欄位 | 高——已驗證可用,填補通路資訊空白 | 小 |
| 🔴 ChEMBL `get_mechanism` 加進證據匹配,標記機轉方向衝突 | 高——直接強化護欄,避免誤導 | 小 |
| 🟡 `drug_class` 分類(BiTE/CAR-T/mAb/small molecule) | 中——對您的 CAR-T 應用情境特別有用 | 小 |
| 🟡 MSigDB immunologic signature gene set(離線批次) | 中——補免疫特異性通路,非平台連結器可得 | 中 |
| ⚪ DGIdb/PharmGKB(離線批次) | 低-中——錦上添花,ChEMBL 已覆蓋大部分需求 | 中 |
| ⚪ ZINC 化學空間搜尋 | 低(現階段)——服務不同問題,MVP 不建議納入 | — |

---

## 4. 交付物
- `PATHWAY_DRUG_DATA_SOURCES_建議.md`(本文件)
