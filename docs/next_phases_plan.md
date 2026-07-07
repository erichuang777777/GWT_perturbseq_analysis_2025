# 下一階段開發規劃(四個方向)

**狀態:** 規劃(尚未實作) · **語言:** 繁體中文 · **對照:** `main` @ `a85d52b`(PR #3/#4 已合併)

三大 MVP 模組已全部落在 `main` 上、測試通過。本文件詳細規劃四個真正還開著的方向,每個都先實地核對 repo 現況(不是紙上談兵),給出接地氣的設計、資料可用性、分階段步驟、驗收標準與風險。

**四個方向的成熟度速覽(依「離可交付多近」排序):**

| 方向 | 現有基礎 | 缺口 | 建議優先序 |
|---|---|---|---|
| **C. gnomAD 安全性補強** | `safety_window_score` 已接 GTEx;連結器建議 §2 已定規則 | 需 gnomAD LOEUF/pLI 資料快照 | 🥇 最小、最獨立 |
| **B. 架構重構 Phase 1–4** | Phase 0 已完成(`config/`+`contracts/`);Phase 1–4 骨架已在 `architecture_refactor_plan.md` | 需逐階段執行 + 納入平行 session 新增的檔案 | 🥈 純結構、零行為變更 |
| **A2. 機制圖(§1.10 之一)** | `pathway_network_cache.py`(Reactome+STRING)已是 60% 基礎 | 需把節點/邊組成圖 + 疊加證據 | 🥉 補完既有基礎 |
| **A1/A3/A4. signature→compound、擾動預測、組合探索** | query 側 signature repo 內已有 | compound 側(LINCS/CMap)不在 repo;預測需 benchmark harness | 🔬 最研究性、需外部資料 |

---

## C. gnomAD LOEUF/pLI 安全性補強 *(最小、最獨立,建議先做)*

### 目標
`safety_window_score` 目前只有兩態:essential gene → `0`、有 GTEx overlay → off-context 組織數、否則 `unknown`。gnomAD 的 LoF 約束(LOEUF / pLI)是**與 GTEx 表現廣度互補、且免費可得**的第二個安全訊號:LOEUF 低 = LoF 高度不耐 = 抑制該基因的安全窗口可能較窄。連結器建議 `ENHANCEMENT_連結器加強建議.md` §2 已定好保守規則。

### 現況核對(實測)
- `readiness_engine.py` 完全沒有 gnomAD/LOEUF/pLI 任何引用(grep 為空)。
- `docs/mvp-research/connector_enrichment_demo.csv` 已有 8 個基因的 `gnomAD_LOEUF`/`gnomAD_pLI` 實測值(CD3E LOEUF 0.701、VAV1 0.344 tight)——**目標欄位格式與真實值都已存在**,可直接當種子/測試資料。
- 沙盒無法直連 gnomAD(egress proxy 403,與 Open Targets 同);gnomAD GraphQL 為部署時管道。

### 設計(沿用既有 overlay 模式)
1. **資料**:比照 `safety_overlay.py` 的 GTEx parquet,產一個 `sources/target_tool_cache/_overlays/gnomad_constraint.parquet`(`ensembl_id`, `gene_symbol`, `loeuf`, `pli`)。研究者本機用連結器 `mcp-variants` 的 `gene_constraint`(建議文件已實測)或裸 gnomAD GraphQL 產出後放進 repo。**沙盒這端先寫 loader + honest-fallback + 用 `connector_enrichment_demo.csv` 的 8 基因當測試種子**,真實全量檔由本機補。
2. **`safety_overlay.py` 新增** `load_gnomad_constraint_overlay(path)` 與 `gnomad_flag_from_constraint(gene_ensembl, overlay)`,honest-fallback 契約與現有兩個 loader 一致。
3. **規則(保守、可辯護,照建議文件 §2)**:LOEUF < 0.35 → soft 註記 `loss_intolerant`(LoF 不耐,抑制安全窗口窄的風險提示),**不自動封頂 readiness call**(因為 LoF 不耐 ≠ 藥理抑制不耐,只是風險旗標)。這與 GTEx 一樣是**描述性欄位,不進 `_stage()`**。
4. **新增卡片欄位** `gnomad_loeuf` / `gnomad_pli` / `safety_constraint_flag`;`readiness_engine` 的 `safety_window_score` 維持 GTEx 邏輯不變,gnomAD 走獨立欄位(兩個安全訊號並列,不互相覆蓋)。

### 分階段
- **C1**:`safety_overlay.py` 加 gnomAD loader + flag 函式 + honest-fallback;用 8 基因種子測試(LOEUF/pLI 已知值)。
- **C2**:接進 `readiness_engine.compute_readiness`(新 `gnomad_overlay` 參數,additive)+ `build_target_cards` 卡片欄位。
- **C3**:golden-file 測試(VAV1 tight、CD3E wider);更新 `data_dictionary.md`、`data_governance_checklist.md`(gnomAD 是公開、無病人層識別資料)。

### 驗收
- VAV1(LOEUF 0.344)標 `loss_intolerant`;CD3E(0.701)不標。
- gnomAD overlay 缺席時 `safety_constraint_flag` = `unknown`,不崩、不封頂。
- 純加分:接 gnomAD overlay 前後,`readiness_call`/`overall_readiness_stage` 逐位元不變(gnomAD 只動自己的欄位)。

### 風險/工作量
小。與 GTEx overlay 幾乎同構,已有現成模式可抄。唯一外部依賴(全量 gnomAD 檔)可由本機補,沙盒端用 8 基因種子先完成程式與測試。

---

## B. 架構重構 Phase 1–4 *(純結構、零行為變更)*

Phase 0(`config/` 單一來源 + `contracts/card_schema.py`)已完成並合併。Phase 1–4 的骨架已在 `docs/architecture_refactor_plan.md` §5;此處補上「Phase 0 落地後」的具體細節,並納入平行 session 新增的檔案。

### 需納入的新現況(平行 session 已加的檔案)
`main` 上現在多了 `population_hypothesis.py`、`pathway_network_cache.py`、`safety_overlay.py`、`external_evidence_cache.py`(含 `match_disease_drug_evidence`)。這些都要一起納入重構:它們目前也各自散落常數/重複 helper。

### Phase 1 — 抽 `common/`(低風險)
- 建 `common/coerce.py`(`_to_bool`/`_to_float`/`_as_bool` 合一)、`common/timeutil.py`(`utc_now`,消滅 `external_evidence_cache._now`、`pathway_network_cache._now` 兩份重複——**平行 session 又各加了一份 `_now`**,現在至少三份)、`common/degrade.py`(統一 `{"available"/"source_status": ...}` 的 unavailable 包裝,現在 `cre_schema`/`safety_overlay`/`external_evidence_cache`/`pathway_network_cache` 各寫一份)。
- 各模組改 import common。code review 已列的重複(`readiness_engine.load_overlays` vs `build_target_cards.load_druggable_overlays`、`_num` vs `_to_float`)一併收斂。
- **驗收**:`grep` 確認 `_now`/`_unavailable`/`_to_bool` 各只剩一個定義;全套測試綠。

### Phase 2 — package 化 + re-export shim(中風險,動最多檔)
- 把 17+ 個扁平模組歸進 §3 套件(`core/`、`data/`、`resolve/`、`evidence/`、`report/`、`api/` 等),每層加 `__init__.py`。
- **關鍵過渡**:每個舊模組位置留一個 re-export shim(`from core.cards import *`),讓 `from build_target_cards import X` 與 `tests/conftest.py` 的 `sys.path` 設定繼續有效,再逐檔遷移 import。
- **驗收**:每搬一個模組跑一次全套測試;`conftest.py` sys.path 同步更新。

### Phase 3 — Protocol 介面 + registry + 關鍵解耦(中風險)
- `contracts/interfaces.py` 定義 `CardBuilder`/`ReadinessEngine`/`EvidenceProvider` Protocol。
- **關鍵解耦**:`readiness_engine` 目前 import `external_evidence_cache`(核心→脆弱邊緣的危險依賴)+ 現在又 import `safety_overlay`。改成**由外部注入** evidence/overlay 結果,而非 import 模組。這一步讓核心真正零脆弱依賴。
- registry:evidence/overlay/scorer 用名稱註冊、config 選用。
- **驗收**:`core/` 內 grep 不到 `import evidence`/`fastapi`/`requests`;停用任一 provider,build+readiness+calibration 仍跑完。

### Phase 4 — API god-module 拆 router(中風險)
- `target_card_api.py` 現在已破千行(且平行 session 又加了 `/api/population-hypothesis`、evidence build 等端點)。拆成 `api/routers/{build,cards,readiness,calibration,evidence,disease,genes,population,imports}.py` + `api/deps.py`(DI:快取 resolver/overlay/settings)+ `api/app.py`(組裝)。
- router 惰性載入 + 各自錯誤邊界 + `/health` 回報各能力可用/降級。
- **驗收**:一個 router import 失敗不拖垮整個 app;每個端點的 TestClient 測試不變。

### 風險/工作量
中。Phase 1 低risk 可先做;Phase 2 動最多檔但有 shim+測試護航;Phase 3–4 是真正提升「可安全抽換」的部分。全程零行為變更——若動到任何數字即為 bug,golden-file/known-answer 測試會擋。

---

## A. §1.10 v2 假設產生器(guarded)

原計畫列四項:signature-to-compound、機制圖、擾動預測、組合探索。實地核對後,成熟度差異很大,**拆開規劃**。

### A2. 機制圖 *(離可交付最近——補完既有基礎)*
**現況**:`pathway_network_cache.py` 已有 `fetch_reactome_pathways`、`fetch_string_network`、`build_pathway_network_for_gene(s)`,且已驗證(CD3E→TCR 訊號通路、MED12→Mediator 複合體)。這已經是機制圖的**節點+邊資料層**。
**缺口**:把它組成一張「標的為中心」的圖 + 疊加平台既有證據(readiness 分數、C7 flag、疾病關聯、tractability),讓使用者看到「這個標的透過哪條通路、連到哪些鄰居、各鄰居的證據強度」。
**設計**:
- 新 `mechanism_graph.py`:`build_mechanism_graph(target, pathway_cache, cards, readiness) -> {nodes, edges}`。節點=標的+STRING 鄰居+Reactome 通路;邊=STRING 交互(帶 score)+ 通路成員關係;節點屬性疊加 readiness call / broad_effect flag / kd_status。
- API:`GET /api/mechanism-graph/{gene}`(唯讀,讀 pathway 快照 + cards)。
- Dashboard:一個網路圖 tab(用既有 dataviz skill 的配色)。
**驗收**:CD3E 的圖含 CD3D/CD3G/CD247 鄰居,各節點正確標其 readiness call;MED12 的圖鄰居清一色 Mediator 成員且都帶 broad_effect flag(視覺化呈現 C7 隔離的合理性)。
**護欄**:純證據呈現,不產生新的「預測」;不餵 readiness 決策。
**工作量**:小–中(資料層已完成)。

### A1. signature-to-compound *(需外部資料,研究性)*
**現況**:query 側 repo 內已有——`combined_Th2_vs_Th1_signature.csv`(9,207 基因,帶 zscore 方向)、`CD4T_aging_signature`、以及每個標的的 DE 方向(`n_up_genes`/`n_down_genes`/`ontarget_effect_size`)。**這是 connectivity-map 方法的「疾病/擾動 signature」query 側,已齊備。**
**缺口**:compound 側的參考 signature(LINCS L1000 / CMap)**不在 repo**,且沙盒無法連 LINCS。這是硬缺口。
**設計(分兩段,先可離線的部分)**:
- **A1a(可先做)**:signature 基礎建設——把「一個標的的 downstream DE 方向向量」正規化成可比對的 query signature 格式(`build_query_signature(target, de_stats) -> {gene: signed_score}`),並實作 connectivity score 演算法(加權 Kolmogorov–Smirnov 或簡單的加權 cosine),先**用平台內部 signature 互比**驗證演算法正確(例:某標的的 signature 與 Th1/Th2 極化 signature 的連結性),不需外部資料。
- **A1b(需資料)**:接 LINCS 參考 signature(研究者本機下載 L1000 Level 5 子集,或部署時連 CLUE API),用 A1a 的演算法查「哪些化合物的 signature 反轉這個標的的 downstream signature」。honest-fallback:無 LINCS 資料時 `source_status: "unavailable"`。
**護欄(§1.10 明訂)**:輸出是「假設性化合物線索 + 連結性分數」,不是「這個藥有效」;附方法學 caveat。
**工作量**:A1a 中(純演算法+內部驗證);A1b 卡在外部資料。

### A3. 擾動預測 benchmark harness *(最研究性)*
**§1.10 明訂**:「先對 baseline 做 benchmark;永不餵 readiness 決策」。
**設計**:這不是「做一個預測模型」,而是「做一個**能誠實比較預測模型 vs baseline** 的評測框架」。用 repo 內既有的多條件 DE 資料(Rest/Stim8hr/Stim48hr)做 held-out:給定一個標的在兩個條件的 DE,預測第三個條件,對比 baseline(如「用平均效應」)。輸出是校準的預測誤差,不是卡片分數。
**護欄**:結果只進 benchmark 報告,**絕不寫入 `target_cards.csv` 或 readiness**。
**工作量**:中–大;價值在「證明/證偽預測可行性」而非產出決策。建議最後做或按需做。

### A4. 組合探索 *(僅研究,最低優先)*
兩兩標的的 downstream signature 是否加成/拮抗。純研究探索,無臨床宣稱。建議按需。

---

## 建議總排序

```
1. C   gnomAD 安全補強          （最小、獨立、有現成模式與種子資料）
2. B1  抽 common/               （低風險、立即降低平行開發的重複與衝突）
3. A2  機制圖                    （補完 pathway_network_cache 的既有基礎,高展示價值）
4. B2–B4 架構 package 化 + 拆 router（提升可抽換性,零行為變更）
5. A1a signature 演算法+內部驗證  （可離線,為 A1b 鋪路）
6. A1b/A3/A4                     （卡外部資料或最研究性,按需）
```

理由:C 和 B1 都小、獨立、能立刻降低多 session 平行開發的摩擦(B1 消滅已經三份的 `_now` 重複正是平行開發造成的);A2 用既有資料層就能產出高價值展示;架構 package 化(B2–B4)是中期投資,零行為風險;signature/預測(A1/A3)最研究性、且部分卡外部資料,放後面。

## 共用護欄(每個方向都遵守)

- `unknown ≠ 0`:新領域無資料一律 honest-fallback,不塞 0。
- 描述性 vs 決策性分離:gnomAD/機制圖/signature 都是**描述性證據**,不進 `_stage()`/不封頂 readiness call(除非有明確、可辯護的因果理由)。
- CRISPRi ≠ 藥理學;signature-to-compound 與擾動預測的輸出都是「假設+線索」,附方法學 caveat,不是療效宣稱。
- 每階段:全套測試綠 + `py_compile` + 獨立 commit,零行為變更的重構若動到數字即為 bug。
