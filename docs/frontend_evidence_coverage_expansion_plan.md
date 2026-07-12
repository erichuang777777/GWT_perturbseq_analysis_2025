# 前端深度證據覆蓋率擴充規劃

**狀態更新（已執行軸線 A、B，以及後續追加發現的兩個零網路資料源）**：

| 軸線 | 狀態 | 實際結果 |
|---|---|---|
| A：ADC 膜蛋白 + GTEx overlay | ✅ 已完成 | `membraneOverlay` 覆蓋 3,637/7,249（50.2%）；`safetyWindowScore`/`compositeSafetyLiability` 覆蓋 3,412/3,261（47.1%/45.0%） |
| B：gnomAD 全基因組 | ✅ 已完成 | 下載 gnomAD v4.1 constraint metrics（17,473 基因），LOEUF/pLI 覆蓋從 15 基因跳到 6,834/7,249（94.3%） |
| D（追加）：本地疾病關聯表 | ✅ 已完成 | `src/6_functional_interaction/results/disease_gene_associations_detailed.csv`（13 種自體免疫/發炎疾病，零網路）併入 `diseases` 欄位，疾病關聯覆蓋從 15 個基因跳到 1,266/7,249（17.5%） |
| E（追加）：UK Biobank 淋巴球 LoF burden | ✅ 已完成 | `evidence/population.py`（零網路，已註冊在 registry.py 卻沒人接線）新增 `populationBurden` 欄位，覆蓋 7,140/7,249（98.5%） |
| F（追加）：本 repo 自己的 signed 足跡再分析 | ✅ 已完成 | `signed_ranking_v2.csv`（零網路）新增 `downstreamFootprint` 欄位，覆蓋 7,246/7,249（~100%），完整保留原檔「這是淨足跡方向、不是分子活化/抑制角色判定」的警語 |
| G（追加）：4 個已發表外部 screen 交叉驗證 | ✅ 已完成 | SchmidtSteinhart2022/Arce2025/Freimer2022/Umhoefer2025（零網路）新增 `externalScreens` 欄位，合併覆蓋 6,921/7,249（95.5%） |
| H（追加）：本 repo 先前的避免/給藥編輯建議 | ✅ 已完成 | `kinetics_avoid/target_master_table.csv`（零網路）新增 `avoidAssessment` 欄位，**UI 上明確標示「editorial」、與原始證據來源視覺區隔**，覆蓋 1,235/7,249（17.0%） |
| I（追加）：功能複合體分群 | ✅ 已完成 | `clustering_results_and_annotations.csv`（零網路，只取 50 個非 unknown 的分群）新增 `functionalComplexes` 欄位，覆蓋 611/7,249（8.4%） |
| C：Open Targets / ClinicalTrials.gov / PubMed | 📝 規劃已寫下，未執行（本 session 網路政策封鎖三個 API） | 見下方軸線 C 章節 |

D、E 兩軸是在使用者追問「除了這些資料還缺什麼可以補」（第一次）時找到的；F、G、H、I 四軸是第二次追問「請你檢查一遍是否有整理好的資料但是沒有接進來展示的」時，動用 subagent 徹底掃過 `docs/mvp-research/` 全部子目錄、`sources/topic*`、`metadata/` 找到並逐一驗證覆蓋率後接上的。全部六個追加軸線都是**已經在硬碟上、完全不需要網路呼叫**的真實資料。

軸線 A、B、D、E、F、G、H、I 的實作、驗證（Playwright 抽測多個基因確認新欄位正確顯示、無覆蓋的基因誠實顯示 unknown、真實重複值如 CD3E 同時屬於兩個標註相同的功能分群已去重）、`export_real_data.py`/`types.ts`/`Dossier.tsx`/README 更新都已完成並可 commit。以下維持原始規劃內容供參考，軸線 C 尚未執行。

也評估過但**不建議接**的資料源：LINCS/CMap L1000（`evidence/lincs_reference_cache.py`，只有 4 個基因、且全部是癌細胞株，模組自己的文件都寫明只能當弱假說參考）；`docs/mvp-research/level4_external_validation/` 的驗證用資料（只涵蓋約 55 個 flagship 基因，規模太小）；`sources/topic13_clinicaltrials_flat.csv`（用藥物名稱索引，不是基因，跟 Dossier 頁的缺口無關）；`downstream_enrichment_v2.csv`／`lincs_concordance.csv`（signed_ranking_v2 的姊妹檔，但只涵蓋 5 個或標明「DEMO-level」的 4 個基因）；`dropout_diagnosis.csv`／`gene_gate_diagnosis.csv`（雖涵蓋全部 11,526 基因，但內容是品管診斷不是 dossier 內容）；`T_activation_regulators.csv`（291 基因，偏小）；`track_c_gse318876_target_evidence.csv`（HIV 宿主因子 screen，跟 CD4 藥物標的受眾關聯性邊緣）；幾個 ~96 基因的 blindspot_fixes 檔案（太窄）；`TableS4_weinstock_et_al_DE.csv`（實際被剔除的基因只有 84 個，其餘是下游讀出而非標的）。

---

**原始現況（規劃當下）**：7,249 個標的都有真實統計量 + 真實 readiness call，但「深度外部證據」——疾病關聯、可成藥性、臨床試驗、文獻、gnomAD 族群遺傳約束——只覆蓋 21 個基因（`sources/target_tool_cache/_evidence/*.json`）與 16 個基因（`gnomad_constraint_seed.csv`）。這份文件規劃如何在**不違反「unknown ≠ 0/ 不捏造」原則**的前提下，把覆蓋率擴大到接近全部 7,249 個標的。

## 重要發現：repo 裡已經有兩組真實資料，但前端從沒接上

在規劃「怎麼抓更多資料」之前，先確認了一件事：`core/readiness.py` 的 `compute_readiness()` 本來就接受三個 overlay 參數：

```python
def compute_readiness(cards, overlays=None, essentials=None, broad_effect_genes=None,
                       evidence_lookup=None,
                       membrane_overlay=None,   # <- 現有，從未傳入
                       gtex_overlay=None,       # <- 現有，從未傳入
                       gnomad_overlay=None):    # <- 現有，從未傳入
```

而 `frontend/webserver/scripts/export_real_data.py` 呼叫 `compute_readiness()` 時，這三個參數**一個都沒傳**（見該檔案第 196-202 行）。也就是說，repo 裡已經有兩份大範圍的真實資料，運算引擎也已經支援讀取它們，純粹是匯出腳本沒有把線接上：

| 資料源 | 檔案 | 真實筆數 | 與目前 7,249 個標的重疊 | 目前狀態 |
|---|---|---|---|---|
| ADC 膜蛋白／可成藥性 overlay | `docs/mvp-research/adc_overlay_gwt_overlap_full.csv` | 5,588 基因 | **3,627 個（50%）** | 完全沒接 |
| GTEx 組織表現量／安全窗 overlay | `sources/target_tool_cache/_overlays/gtex_per_tissue.parquet` | 9,718 基因 | **3,453 個（48%）** | 完全沒接 |
| gnomAD v4 LOEUF/pLI（現有 seed） | `sources/target_tool_cache/_overlays/gnomad_constraint_seed.csv` | 16 基因 | 15 個 | 已接，但樣本極小 |

這代表**擴充可以分成三條獨立的軸線**，優先度、成本、風險完全不同，不該混為一談。

## 三條擴充軸線

### 軸線 A：可成藥性 + 安全窗（ADC + GTEx overlay）— 零新增網路請求，現在就能做

**做法**：在 `export_real_data.py` 裡呼叫已存在的 loader，接進 `compute_readiness()`：

```python
from evidence.safety_overlay import (
    load_membrane_tractability_overlay,
    load_gtex_safety_overlay,
    load_gnomad_constraint_overlay,
)

membrane = load_membrane_tractability_overlay()   # ADC overlay，已在 repo
gtex = load_gtex_safety_overlay()                  # GTEx overlay，已在 repo
gnomad_ov = load_gnomad_constraint_overlay()        # 目前仍是 16-gene seed（軸線 B 會擴大這個）

readiness = compute_readiness(
    cards,
    overlays=overlays,
    essentials=essentials,
    broad_effect_genes=broad_effect,
    evidence_lookup=evidence_lookup,
    membrane_overlay=membrane["table"] if membrane["available"] else None,
    gtex_overlay=gtex["table"] if gtex["available"] else None,
    gnomad_overlay=gnomad_ov["table"] if gnomad_ov["available"] else None,
)
```

這會讓 `compute_readiness()` 額外吐出這些欄位（目前程式碼已經寫好，只是沒人餵資料進去）：
`safety_window_score`、`gnomad_constraint_flag`、`gnomad_loeuf`、`gnomad_pli`、`composite_safety_liability`（本來就有算，但因為 gnomad_flag/safety 兩個輸入都是 unknown，實質上對 99.7% 的基因永遠算出 unknown）、以及升級後的 `tractability_modality`/`tractability_score`（ADC overlay 優先於既有的 local gene-list fallback）。

**⚠️ 資料模型上要注意的一點**：ADC overlay 的可成藥性欄位（`is_surface_protein`/`has_transmembrane_domain`/`is_druggable`/`druggable_pathway`）跟 Open Targets 的可成藥性 bucket（SM/AB/PR/OC 四大類、每類再細分多個 flag）是**兩套不同的分類系統**，語意不能互換。目前 JSON 的 `tractabilityFlags` 欄位是照 Open Targets 的形狀設計的。建議：

- **不要把 ADC overlay 的欄位硬塞進 `tractabilityFlags`**（會誤導成「這是 Open Targets 說的」）
- 新增一個獨立欄位，例如 `membraneOverlay: { isSurfaceProtein, hasTransmembraneDomain, isDruggable, druggablePathway } | null`，Dossier 頁面另開一個小區塊，並註明資料源是「project owner 的私有 ADC 資料庫 vs GWT 11,526 基因交集」（`safety_overlay.py` 檔頭本來就這樣描述這份資料的來源）

**產出**：需要修改
- `scripts/export_real_data.py`：接 overlay、新增 JSON 欄位（`safetyWindowScore`、`membraneOverlay`）、`--force` 重跑一次快取（因為 `compute_readiness()` 的呼叫簽章變了）
- `src/data/types.ts`：新增對應型別
- `src/views/Dossier.tsx`：新增「Safety window (GTEx)」「Membrane / ADC overlay」兩個區塊，沒資料的基因照舊顯示 `unknown`
- README 兩處：揭露新覆蓋率（~48-50%，而非 21 個基因）

**預估工時**：不含前端 UI 大概 30-60 分鐘（純接線 + 欄位映射），validate 靠現有 Playwright 流程即可。**零網路依賴，零外部 API 風險。**

---

### 軸線 B：gnomAD LOEUF/pLI 擴大到近乎全基因組覆蓋 — 需要抓一個公開檔案，本 session 已驗證可連

目前 `gnomad_constraint_seed.csv` 只有 16 個基因，是手動填的種子檔。但 gnomAD 官方在 Google Cloud Storage 公開桶提供整個 v4.1 全基因組 constraint metrics：

```
https://storage.googleapis.com/gcp-public-data--gnomad/release/4.1/constraint/gnomad.v4.1.constraint_metrics.tsv
```

我在這個 session 裡實際測試過（`curl -I`），**這個網址可連、可下載**（~95.5 MB，`Content-Length` 已確認），欄位裡有：
- `gene`（symbol）、`gene_id`（Ensembl，注意有些列是佔位的假 ID 如 `"1"`，要挑 `gene_id` 以 `ENSG` 開頭的列）
- `mane_select`（true/false，挑 MANE Select 代表轉錄本，等同「這個基因的標準代表值」）
- `lof.oe_ci.upper` = **LOEUF**
- `lof.pLI` = **pLI**

**做法**：
1. 下載該檔（一次性、離線步驟，不放進 export 腳本的每次執行路徑）
2. 篩選 `mane_select == "true"`（或找不到時退回 `canonical == "true"`）且 `transcript_type == "protein_coding"` 的列
3. 只取 `gene, gene_id, lof.oe_ci.upper as loeuf, lof.pLI as pli` 四欄，寫成新檔，**不要直接覆蓋掉現有 `gnomad_constraint_seed.csv`**（那個檔名/欄位語意是「v4 種子」，全基因組版本應該用新檔名如 `gnomad_v4.1_constraint_full.csv`，並更新 `evidence/safety_overlay.py` 的 `GNOMAD_CONSTRAINT_SEED_PATH_DEFAULT` 或在 export 腳本呼叫 `load_gnomad_constraint_overlay(path=新檔)` 時明確指定路徑）
4. 一支小腳本即可完成（pandas 讀 tsv、篩選、輸出 csv），不需要逐基因打 API

```python
import pandas as pd
df = pd.read_csv("gnomad.v4.1.constraint_metrics.tsv", sep="\t", low_memory=False)
df = df[(df["mane_select"] == "true") & (df["transcript_type"] == "protein_coding")]
out = df[["gene", "gene_id", "lof.oe_ci.upper", "lof.pLI"]].rename(
    columns={"gene": "gene_symbol", "gene_id": "ensembl_id", "lof.oe_ci.upper": "loeuf", "lof.pLI": "pli"}
)
out.to_csv("sources/target_tool_cache/_overlays/gnomad_v4.1_constraint_full.csv", index=False)
```

**預期覆蓋率**：gnomAD v4.1 涵蓋幾乎所有 protein-coding 基因（約 19,000+），跟我們 7,249 個標的的重疊預期會落在 90%+ 區間（少數是符號別名不匹配，需要走跟 `common/overlay_lookup.py` 一樣的 Ensembl ID join，不要用 symbol 直接比對——這個 repo 已經有 `gene_identifier_resolver.load_resolver()` 可用）。

**預估工時**：下載 + 轉檔約 15-30 分鐘（含驗證幾個已知基因的數值跟現有 16-gene seed 對得上）。**這條路線的網路依賴（GCS 靜態檔案下載）在本 session 裡已驗證可行，不受下面軸線 C 的網路限制影響。**

---

### 軸線 C：疾病關聯 + 臨床試驗 + 文獻（Open Targets／ClinicalTrials.gov／PubMed）— 真正需要新增網路請求，本 session 網路政策已封鎖

這是唯一「必須真的對外呼叫 API 才能擴充」的部分，用的是 repo 既有、已經產出現有 21 個基因證據快取的同一支程式：`evidence/external_cache.py::build_evidence_for_genes()`。三個 API 都不需要金鑰：

- ClinicalTrials.gov API v2（`clinicaltrials.gov/api/v2/studies`）
- PubMed E-utilities（`eutils.ncbi.nlm.nih.gov`）
- Open Targets GraphQL v4（`api.platform.opentargets.org`）

**我在這個 session 裡測試過這三個網址，全部回傳 403**（即使加上瀏覽器 User-Agent 也一樣；同一 session 對 `storage.googleapis.com` 卻能正常連線），研判是這個沙盒環境的出網政策沒有把這三個網域放進白名單——這跟 `evidence/external_cache.py` 檔頭註解裡寫的「the original sandbox had no egress to gnomAD, policy-blocked like Open Targets」是同一種限制，只是這次連 gnomAD 的 GraphQL API 也一樣會被擋（但 GCS 靜態檔案桶沒事，這也是軸線 B 選擇走靜態檔案下載而非 gnomAD API 的原因）。

**這代表軸線 C 沒辦法在目前這個 session 裡直接執行**，需要以下其中一種方式：

1. **您在有正常網路的環境（本機、CI、或允許這三個網域的 Claude Code 環境）執行**：
   ```bash
   cd src/3_DE_analysis
   python3 -m evidence.external_cache GENE1 GENE2 ... --cache-dir ../../sources/target_tool_cache/_evidence
   ```
   跑完後把新增的 `_evidence/*.json` 檔案 commit 進 repo，下次 `export_real_data.py` 就會自動讀到（`load_evidence()` 只是掃該目錄）。

2. **請求把這三個網域加入這個 Claude Code 環境的出網白名單**（如果目前用的網路政策支援調整——見「Environment configuration」文件連結，我可以協助說明如何設定，但沒有權限自己改）。

**規模與節流評估**（如果拿到網路權限）：7,249 個基因全部抓一輪不現實——PubMed E-utilities 建議無金鑰時 ≤3 req/sec、ClinicalTrials.gov v2 沒公開明確速率限制但仍應節流、Open Targets GraphQL 也一樣。保守估計每個基因 2-4 次 HTTP round trip、每次含節流延遲抓 1-2 秒，全部 7,249 個基因跑完可能要 **數小時**（且中途任何一個 API 暫時失效，該基因就誠實記錄成 `unavailable`，不會中斷整批）。

**建議分批策略**（而不是一次全上）：

| 批次 | 範圍 | 基因數 | 理由 |
|---|---|---|---|
| Tier 1 | `readiness_call ∈ {advance, validate}` | **621** | 這些是使用者真正會點進去深入研究的標的（Explorer 預設排序最前面），投資報酬率最高，且 621 個基因在合理節流下抓一輪約 10-20 分鐘可完成 |
| Tier 2 | `readiness_call == watchlist` 且 `grade ∈ {A, B}` | 待統計（比 Tier 1 大但比全部 6,628 個 watchlist 小很多） | 次高優先，證據等級較高的 watchlist 基因 |
| Tier 3 | 其餘 watchlist 基因 | 剩餘 | 背景批次慢慢補，不阻塞任何交付 |

Tier 1 的 621 個基因清單已經在這次分析中算出來（`advance` 302 + `validate` 319），可以直接餵給 `build_evidence_for_genes()`。

---

## 三條軸線總覽

| 軸線 | 擴充內容 | 是否需要新網路請求 | 本 session 是否可執行 | 預估覆蓋率提升 | 預估工時 |
|---|---|---|---|---|---|
| A：ADC + GTEx overlay | 可成藥性（膜蛋白）、安全窗、複合安全負債 | 否（檔案已在 repo） | ✅ 可以 | 21 → ~3,450-3,627（48-50%） | 30-60 分鐘 |
| B：gnomAD 全基因組 | LOEUF / pLI | 是，但是靜態檔案下載，已驗證可連 | ✅ 可以 | 15 → 預期 90%+（需驗證實際 symbol 重疊率） | 15-30 分鐘 |
| C：Open Targets / ClinicalTrials.gov / PubMed | 疾病關聯、臨床試驗、文獻、Open Targets 版可成藥性 | 是，三個 API 都被本 session 網路政策擋掉（已用 curl 驗證 403） | ❌ 需要別的網路環境或白名單調整 | 21 → Tier 1 完成後 621（8.6%），全量則需要數小時分批 | Tier 1 約 10-20 分鐘執行時間（但需要可用的網路環境） |

## 建議的執行順序

1. **先做軸線 A + B**（今天就能完成，零外部依賴風險，覆蓋率從 21 個基因一口氣跳到近乎全部標的的一半以上，且 gnomAD 幾乎全覆蓋）
2. 更新 `types.ts` / `Dossier.tsx` / 兩份 README，誠實揭露新的覆蓋率數字（沿用目前「有資料就顯示，沒資料就 unknown」的規矩，不因為擴充了就放鬆這條線）
3. **軸線 C 需要您決定**：是要在別的環境跑 Tier 1（621 基因，約 10-20 分鐘）後把 `_evidence/*.json` commit 回來，還是要我協助申請把三個網域加入這個環境的出網白名單
4. 每個軸線做完都照現有流程驗證：重跑 `export_real_data.py --force`、`tsc -b --force`、`npm run build`、Playwright 抽測幾個基因的新欄位是否正確顯示，再 commit + push

## 不會做的事（維持既有紀律）

- 不會把 ADC overlay 的欄位塞進 Open Targets 語意的 `tractabilityFlags`（兩套系統，混了就是誤導）
- 不會用 symbol 字串比對取代 Ensembl ID join（同名基因、別名問題會撞資料）
- 沒抓到/沒匹配到的基因一律維持 `unknown`/`null`，不會因為「大部分基因都有了」就對剩下的基因用鄰居的數字去估
- 軸線 C 若真的因為網路政策跑不了，不會用假資料頂替，會誠實停在「21 個基因」並在 README 註明原因（如同這份文件所寫）
