# 計劃 Plan

本頁是實作計劃的導覽摘要。**權威的、活的計劃**在 `docs/IMPLEMENTATION_PLAN.md`;本頁只把它的結構與可執行規格來源整理出來,方便快速定位。

## 計劃的兩層文件

1. **策略層** — `docs/DRUG_DISCOVERY_TOOL_DEVELOPMENT_PLAN.md`(PR #1,已合併):為什麼要做、可能的功能面。
2. **可執行層** — `docs/IMPLEMENTATION_PLAN.md`:每一塊有具體規格、排序、工作量與驗收測試;每個資料宣稱都對應 repo 內檔案。

## 四個第一波模組(設計來源)

| 模組 | 目的 | 主要檔案 |
|---|---|---|
| A. 上傳合併迴圈(U3/U4/U5) | 完成研究者上傳需求(欄位對應精靈 → 合併到卡片 → score-my-dataset) | `import_manager.py` + API |
| B. 就緒度引擎(R1–R3)+ 真實 `batch_sensitivity_flag`(C4) | 把統計等級轉成決策 | `readiness_engine.py` |
| C. 外部證據層(T5/T6/T2) | 每張卡片附試驗/文獻/遺傳學-可成藥性 | `external_evidence_cache.py` |
| D. 儀表板 + 標靶卡片頁 | 多頁工作區與 per-target dossier | `target_card_dashboard.py` |

## 共用基礎(適用所有模組)

- **把 builder 重構為可 import 的函式** — `build_cards(...) -> pd.DataFrame`,讓合併迴圈與就緒度引擎能 in-process 呼叫,不再 subprocess。
- **資料集命名空間** — `metadata.json` 帶 `origin`:`gwt_reference` vs `user_upload`。使用者卡片永不混入參考集。
- **provenance 是欄位,不是註腳** — 每組卡片記錄 `data_version` / `engine_version` / 來源戳記,上傳另記合併血緣(import_id、欄位對應、時間戳)。
- **`unknown` ≠ `0`** — 任何無資料的證據領域明確標 `unknown`,絕不悄悄給 0 分。

## 關鍵資料事實(建構卡片時實際使用)

| 檔案 | 列數 | 用途 |
|---|---|---|
| `DE_stats.suppl_table.csv` | 33,983 | 每「標靶 × 條件」一列的 DESeq2 pseudobulk 結果 |
| `guide_kd_efficiency.suppl_table.csv` | 73,765 | 每 guide 每條件的敲低 t 檢定 vs 條件配對 NTC 池 |
| `sgrna_library_metadata.suppl_table.csv` | 31,109(12,654 唯一基因) | 別名表來源(設計時符號 vs curated 符號) |
| `sample_metadata.suppl_table.csv` | 11 | 偵測條件/run 混淆 |
| `broad_effect_genes.txt` | 239 基因 | `broad_effect` 紅旗 |
| `disease_gene_associations_detailed.csv` | 7,528(13 適應症) | 疾病轉譯器 |

## kd_status 因果閘(核心設計)

CRISPRi 的因果鏈是「標靶被抑制 → 下游轉錄改變」。若標靶本身未確認敲低,下游 DE 就不可因果判讀。因此有三態 `kd_status`:

- `confirmed` — 敲低確認(`guide_signif_ratio>=0.5 且 guide_fdr_min<=0.05`)
- `weak` — 有訊號但未達確認門檻
- `not_measurable` — NTC 基線表現 `<= 0.001`,連敲低都無法評估

`KD_NOT_MEASURABLE_EXPRESSION_FLOOR = 0.001` 直接重用資料集自己文件化的 `high_confidence_no_effect_guides` 定義,不是新發明的門檻。在 `readiness_engine.py` 中,`kd_not_measurable` 封頂在 watchlist、`kd_weak` 封頂在 validate。

> ⚠️ **注意**:目前 `not_measurable` 會把「NaN 基線(從未測量,例如純上傳資料)」與「已測量但低於 floor」視為同一態。這是已知技術債,見 **[技術債](Tech-Debt)** 第 1 項。

## 驗證策略(每個 Wave 都套用)

- 對真實 CSV 做離線單元檢查(批次旗分佈、readiness 封頂、校準recovery),不需啟動伺服器。
- 每個端點用 FastAPI `TestClient` 做整合測試。
- 儀表板用文件化的本機啟動做 smoke test(注意:本沙盒未裝 Streamlit,僅 py_compile 驗證)。
- provenance 斷言:每組卡片帶 `origin` / `data_version` / `engine_version`,上傳另帶合併血緣。

## 帶進每個 Wave 的護欄

- `unknown` ≠ `0`:未建置領域維持明確 `unknown`。
- 紅旗覆蓋不論統計強弱都封頂(essential、broad-effect、off-target、方向不明、批次混淆、kd 未確認)。
- 上傳資料集保持命名空間(`usr_`)並標籤,永不混入 GWT 參考集。
- CRISPRi ≠ 藥理學;體外 CD4 情境注意事項留在卡片上可見。
