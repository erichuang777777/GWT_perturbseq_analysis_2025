# 技術債 Tech-Debt

本頁記錄已知的正確性問題、刻意的 descope,以及清理項目。**正確性問題**來自對 `main` 合併後程式碼的一次結構化 code review;每一項都附檔案:行號與具體失效情境。標記 🔴 = 建議優先修、🟡 = 中等、⚪ = 清理。

---

## A. 正確性問題(code review 發現)

### ✅ 1.（已解決)`_kd_status` 把「從未測量」當成「測量後失敗」— 每個上傳資料集都被封頂
> **RESOLVED** — `kd_status/v2`(`core/kd_status.py`)已區分 NaN 基線 → `not_assessed`(genuinely unknown,不封頂)與已測量 sub-floor → `not_measurable`。守護測試:`tests/test_empty_states.py::test_guideless_upload_is_not_assessed_not_fabricated_not_measurable`(綠)。此項曾建議為上傳功能合併前阻擋項,阻擋前提現已滿足並移除。以下為歷史問題描述。
- **位置**:`build_target_cards.py:351`(及 `:509`)
- 使用者上傳走 `build_cards_frame(..., guide_df=None, schema="generic")`。無 guide 表時 `target_baseline_expression` 從未設定,被回填為 NaN。`_kd_status` 命中 `if pd.isna(baseline) or baseline <= FLOOR: return "not_measurable"`,於是**每個上傳資料集的每一列**都變成 `not_measurable`。
- **後果**:每張卡片的 `score_cap_reason` 都加上 `kd_not_measurable`,readiness 整個上傳封頂在 watchlist,next step 顯示「NTC 表現過低無法評估敲低」— 這是捏造的,因為上傳根本沒有 NTC 細胞。
- 這**直接違反** repo 自己 `docs/data_governance_checklist.md` §3 的 `unknown ≠ 0` 原則。NaN(未知)應與「已測量的低於 floor」是不同態。
- **建議修法**:在 `_kd_status` 區分 NaN 基線(→ 新的 `unknown` / `not_assessed` 態)與 sub-floor;讓純上傳資料不被當成敲低失敗。

### ✅ 2.（已解決)已對應的上傳結構性遺失 `n_total_de_genes` → 等級與校準退化
> **RESOLVED** — `n_total_de_genes` 已納入 canonical 上傳 schema,`import_manager.suggested_mapping` 會把別名(如 `num_de_genes`)對應到它,`build_mapped_view` 不再丟棄。守護測試:`tests/test_empty_states.py::test_mapped_upload_preserves_n_total_de_genes`(綠)。以下為歷史問題描述。
- **位置**:`build_target_cards.py:233` + `import_manager.py` 對應層
- `adapt_generic_de` 讀 `col("n_total_de_genes")`,但 `n_total_de_genes` **不是** `REQUIRED_COLUMNS`/`RECOMMENDED_COLUMNS`/`GENERIC_TARGET_FIELDS` 裡的 canonical 欄位。`build_mapped_view` 只保留有對應的 canonical 欄位,所以欄位對應精靈跑完後這欄一定被丟掉 → `np.nan`。
- **後果**:每個對應過的上傳 `n_total_de_genes` 全 NaN → `_make_score` replicate 閘失敗、biomarker=0、`calibration.qc_funnel` 第一階段就丟掉所有列。即使使用者有這欄並對應了也過不去。
- **建議修法**:把 `n_total_de_genes` 加入 canonical 上傳 schema,讓對應精靈能傳遞它。

### 🟡 3. `_next_step` 寫死參考資料集的條件名
- **位置**:`readiness_engine.py:225`
- `return "replicate Stim48hr in an independent run..."`。上游全是資料驅動(`confounded_conditions()` 從 sample metadata 推導混淆條件集),但這句面向使用者的建議寫死一個字面條件。
- **後果**:上傳資料若混淆條件是 `Stim72hr`,會被正確標記,卻被叫去「replicate Stim48hr」— 一個他們資料裡不存在的條件。
- **建議修法**:改用 `row.get("condition")` 內插。

### 🟡 4. `get_calibration` 使用過期或缺失的 `readiness.csv` 且無新鮮度檢查
- **位置**:`target_card_api.py:657`(`get_disease_targets` `:755` 同樣)
- 只檢查 `calibration.json` mtime vs `target_cards.csv`;`readiness_df = pd.read_csv(...) if exists else None` 對卡片沒有做過期檢查。重建資料集後若舊 `readiness.csv` 還在,負對照安全指標(`test_known_answer.py` 斷言必須 0.0)就用過期 readiness 算。若 `readiness.csv` 從未產生,calibration 靜默以 `readiness=None` 執行、跳過 readiness 層檢查,報告看似通過只因護欄從未被評估。
- **建議修法**:對 `readiness.csv` 做 vs 卡片的過期檢查;缺失時重新產生而非跳過。

### 🟡 5. 格式錯誤的 guide 表被靜默吞掉
- **位置**:`build_target_cards.py:489`
- `has_guides` 要求 `"signif_knockdown" in guide_df.columns`。舊行為:缺該欄會在 `_build_guide_summary` 大聲 `KeyError`。新行為:真實 guide 表若該欄改名/缺失,`has_guides` 為 False,落到 generic 路徑,產生看似合理但靜默退化的卡片(guide 欄全 NaN、全 `not_measurable`、等級封頂 2),不報錯。
- **建議修法**:當 guide 表存在但缺必要欄位時,拋出明確錯誤而非退化。

### ⚪ 6. `enrichment_ratio` 的 falsy-zero 守衛藏掉真實 0.0 訊號
- **位置**:`calibration.py:102`
- `... if high_grade_rate and overall_rate else None`。當資料集有 grade≥3 列但都無 `clinical_axis`,`high_grade_rate == 0.0`,守衛為 False → 回 `None`。真實 0.0(top 標靶藥物軸強烈耗竭,一個有意義的校準失敗)變得與「無法計算」無法區分。
- **建議修法**:守衛改用 `is not None` 而非 truthiness。

### ⚪ 7. `readiness_engine` 對可能是 object-dtype 的旗標用裸 `bool()`
- **位置**:`readiness_engine.py:174`(及 `:178`, `:92`)
- 獨立 CLI 路徑(`python readiness_engine.py cards.csv`)以純 `pd.read_csv` 讀入、無 cell 正規化。若任一 bool 旗標欄是 object-dtype(一個空白 cell 就會讓 pandas 保留字串),`bool("False")` 為 `True`,反轉 off-target / replicate 邏輯。`calibration.py` 加了 `_as_bool` 正是為避免這個,readiness 沒有。觸發面窄(工具產出的 CSV 是乾淨 bool),但對外部產生/手動編輯的卡片檔是真實不一致。

---

## B. 效能清理(非正確性,但在 34k 列上是真實成本)

### ⚪ 8. 每次 build 對 34k 列做多次逐列 apply / iterrows
- **位置**:`build_target_cards.py:511, 589, 606` + `readiness_engine.py:281`
- `apply(_kd_status, axis=1)`、`apply(_make_score, axis=1)`、`apply(_cap_reason, axis=1)` 都只讀少數純量欄,是教科書級 `np.select` / 布林遮罩案例;`compute_readiness` 以 `iterrows()` 逐列呼叫約 8 個 Python 輔助函式。向量化是大而安全的收益。

### ⚪ 9. 每次請求重讀靜態 CSV
- **位置**:`target_card_api.py:567, 72`
- `get_readiness` 每次請求(含 cache-hit)無條件呼叫 `_overlays()` → 讀約 12 個 TSV;`_disease_associations()` 每次 `/api/disease*` 重新 parse 疾病 CSV。已有 `_GENE_RESOLVER` 全域快取樣式(`:79`)可比照套用。

---

## C. 重用 / 重複(維護成本)

### ⚪ 10. 已存在、只差一個 import 的重複輔助函式
- `readiness_engine.load_overlays`(`:45`)= `build_target_cards.load_druggable_overlays` 的逐字複製
- `readiness_engine._num`(`:66`)重複 `_to_float`,且更弱(不 strip 空白,`" 3.0 "` 在兩條評分路徑會不同)
- `external_evidence_cache._now`(`:49`)= `import_manager.utc_now`
- `calibration._as_bool` 重新寫死 `_to_bool` 的 truthy token 集
- **建議**:`readiness_engine` 已 import 自 `build_target_cards`,直接呼叫既有函式,避免契約悄悄分歧。

---

## D. 刻意的 descope(不是 bug,是資料限制)

這些在 repo 文件中已明確記錄,列於此避免被誤認為遺漏:

- **§1.5 Signed CD4 module scoring**:`DE_stats` 只有 up/down 計數、無 per-gene 方向,signed 分數會是捏造 → 放棄。目前 `/api/modules` 維持二元 overlap 分數。
- **SCEPTRE**:以誠實外部 hook(若 R 存在則 shell out,否則優雅退化)而非重寫 — SCEPTRE 的校準是非平凡的條件重採樣,天真 Python 重寫會重現它本要修的 miscalibration。
- **pertpy / Mixscape**:`pertpy` 因 `blitzgsea` 建置失敗無法安裝 → 用 scikit-learn(PCA 差異均值軸 + 2-component GMM)直接重寫,程式註解明載為刻意替代。
- **Open Targets genetics(此沙盒)**:無 GraphQL fetch 工具可用;自動 fetcher 已接好,等有直接網路的佈署。
- **細胞層級真實資料執行**:1.68 TiB 超過沙盒磁碟,委由負責人自跑(`RUN_ON_REAL_DATA.md`)。「程式對 schema 忠實的合成 fixture 已測試」與「已處理真實資料」是不同宣稱,只有前者為真。

---

## E. 驗證缺口(已知)

- **Streamlit 未安裝於本沙盒** → 儀表板變更僅 py_compile / AST 驗證,未視覺渲染。合併前建議手動 `streamlit run`。
- 上述效能與重用項目未阻擋功能,但在真實工作負載是真實成本。

---

> 修正建議的優先序:**A.1 與 A.2(研究者上傳核心路徑)已解決並有守護測試(見上方 ✅),不再是合併前阻擋項——上傳功能已正式支援。** 其餘可在不動架構下逐步修。
