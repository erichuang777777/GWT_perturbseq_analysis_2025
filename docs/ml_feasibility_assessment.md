# ML / DL 可行性評估 — GB10 CD4 Perturb-seq 資料

**日期：** 2026-07-11 · **範圍：** 只做可行性評估,不建 model(本輪交付物 = 這份文件)。
**紀律沿用全 repo 既有規則:** benchmark-vs-baseline、`unknown != 0`、絕不餵決策、誠實負面結果是有效結果。

---

## §0 TL;DR / 結論先講

**問「能不能用這批資料訓練一個 ML / DL model」——答案分三層,而且其中最關鍵的一層已經有實測答案了:**

1. **最有價值、也最「深度學習」的那個任務(用基因身分預測未見擾動的下游反應 profile),本週期已經被
   實測過了,而且是誠實的負面結果。** 另一個 workstream 已在 `src/10_ml_perturbation_prediction/`
   用兩個架構完全不同的方法各跑了一遍:GenePT 文字嵌入 + Ridge(簡單線性)、以及官方 `cell-gears`
   套件的 GO 知識圖譜 + GNN(複雜)。**兩者都打不過「訓練集平均 profile」這個天真基線**,方向一致,
   直接呼應 2025–2026 文獻共識(Ahlmann-Eltze et al., *Nature Methods* 2025)。所以「能不能訓練一個
   *有用的、贏過基線的* 擾動反應預測器」這題,**現階段的實證答案是:用目前的標準方法,不行**——這不是
   失敗,是一個有價值的、已經拿到的結論。

2. **Classical ML 今天就能在這個環境跑。** sandbox 內 `scikit-learn 1.9.0` 可用;既有的
   `src/3_DE_analysis/perturbation_prediction_ml.py` 本 session 實跑通過(見 §4)。DL 也已被證明可跑
   ——GEARS 的 GNN 就是在本 sandbox 用獨立 venv(torch)跑完 92 分鐘的,不需要 GPU 也能出結果
   (只是慢、且要子抽樣)。

3. **真正還沒被回答、值得下一個 build round 做的,是另外兩題:** (T2) **已知調控子分類器**——有真實
   ground-truth 標籤(`benchmark_results.csv` 的 `truth_class`,現有簡單排序基線 AUROC 0.85),但**尚未
   有人訓練過監督式分類器去挑戰它**;(T3) **自監督 target/gene embedding** 當描述性特徵。這兩個 classical
   ML 就能做,今天的環境足夠。

**一句話建議:** 不要再用天真方式重做 T1(答案已經在了)。若要再投入,**優先做 T2**(有硬標籤、有明確
基線、是最貼近「這個工具在乎的科學問題」的一題),但**必須先把 leakage / circularity 講清楚**(見 §6),
否則一個「贏過 0.85」的數字會是假象。DL(torch/GEARS)已證明可跑,但既然兩個方法都已誠實輸給基線,
在 classical 沒把天花板頂到之前,不建議再投更多 DL 算力。

---

## §1 GB10 改變了什麼

在 Task A(全基因組帶符號 DE 矩陣萃取,見 `docs/mvp-research/TASK_A_GB10_HANDOFF.md`)完成之前,repo 內
唯一夠大的 ML 標籤來源是聚合的 `metadata/suppl_tables/DE_stats.suppl_table.csv`(33,983 × ~19,只有
「被影響幾個基因」的計數 + 一個純量 on-target 效應量,**沒有基因身分**)。

GB10 交付的新資產是 `metadata/suppl_tables/full_signed_DE/`(**2,056,424** 個顯著 target×gene 配對,
帶 `log_fc`/`zscore`/`adj_p_value`,涵蓋 10,851 個至少有一個顯著命中的標的、10,273 個唯一下游基因;
schema 見該目錄 `README.md`)。這是 repo 內**第一個支援「基因層級(向量)擾動反應建模」**的資產——也正是
它讓 §0 那兩個誠實基準測試得以存在。門檻子集版是
`metadata/suppl_tables/gate_passing_signed_DE.suppl_table.csv.gz`(1,067,181 列,1,235 個過 MVP 門檻標的)。

---

## §2 ML 相關資料盤點

### 在磁碟上、ML-ready(committed,總計約 250 MB)

| 資產 | 路徑 | 形狀 | 格式 | ML 角色 |
|---|---|---|---|---|
| 全量帶符號 DE | `metadata/suppl_tables/full_signed_DE/` | 2,056,424 × 9 | parquet(2 part) | 基因層級反應預測 / embedding 的主要原料 |
| 門檻子集帶符號 DE | `metadata/suppl_tables/gate_passing_signed_DE.suppl_table.csv.gz` | 1,067,181 × 9 | gzip csv | 上者聚焦 1,235 門檻標的的子集 |
| 聚合 DE_stats | `metadata/suppl_tables/DE_stats.suppl_table.csv` | 33,983 × ~19 | csv | 既有純量 benchmark 的特徵/標籤來源 |
| target_cards(v2) | `sources/target_tool_cache/a6bba17b-.../target_cards.csv` | 33,983 × 39 | csv | 富特徵 + 描述性標籤(grade/druggable/safety…) |
| target_cards(legacy) | `sources/target_tool_cache/e7ecd8d5-.../target_cards.csv` | 33,983 × 31 | csv | 舊版(schema drift,見 human_validation_protocol OF-1) |
| 已知調控子標籤 | `docs/mvp-research/pipeline/methodological_validation/benchmark_results.csv` | 1,225 × 4 | csv | `truth_class` = T2 的 ground truth |
| 基因 constraint / dropout | `.../methodological_validation/dropout_diagnosis.csv` | 11,526 | csv | LOEUF/pLI/essentiality 特徵與標籤 |
| 疾病 / 群體遺傳基因集 | `metadata/gene_lists/*.tsv` | 各數百–數千 | tsv | 潛在監督標籤 / 特徵 |

### S3-only / 本 checkout 沒有(但可下載)

| 資產 | 大小 | 狀態 |
|---|---|---|
| 12 個原始單細胞 `*.assigned_guide.h5ad` | ~1.67 TB | S3-only,index 在 `data/marson2025_data/manifest.csv` |
| `GWCD4i.DE_stats.h5ad`(帶符號 DE 來源) | 15.6 GB | S3-only,Task A 下載後未進 git |
| `GWCD4i.pseudobulk_merged.h5ad` | 41.5 GB | **GEARS run 實際下載並使用過**(見 §4 T1)——證明本環境可取得 |
| `*.by_guide.h5mu` / `*.by_donors.h5mu` | 29 / 17 GB | S3-only,per-guide/per-donor 顆粒度,尚未用到 |

> 註:`pseudobulk_merged.h5ad` 原本我列為「absent」,但 GEARS 基準測試的 README 記錄它實際被下載並用於
> 訓練資料建構——所以「S3-only」不等於「拿不到」,只是不在 git、需重新下載。這也修正了「raw-ish 資料
> 在本環境不可行」的假設:可行,只是大檔、慢、不進 repo。

---

## §3 限制:哪些是硬邊界

**(a) 專案紅線(全部沿用,不是本文件新發明):**
- `unknown != 0`:缺失特徵絕不補 0(用原生支援 NaN 的模型或明確 missing indicator)。
- **絕不餵決策**:任何 model 輸出都不寫 `target_cards.csv` / readiness / 任何卡片或 dashboard 讀的檔;
  只寫 `src/10_ml_perturbation_prediction/results/`。這條已由既有的 `src/10_...` 隔離空間強制執行
  (production 與 ML 目錄互不 import)。
- benchmark-vs-baseline:每個 model 都要跟簡單基線比,輸了就老實說輸了。
- 加法式:新東西不改既有 production 行為。

**(b) 環境現實(本 session 實測):**
- `scikit-learn 1.9.0` 在 sandbox 可 import → classical ML 今天就能跑。
- **無 GPU**,但 torch/GEARS 已證明能在 CPU 跑(§4 T1,92 分鐘/10 epochs/2,000 標的子抽樣)——DL 不是
  「不可行」,是「慢且需子抽樣」。
- 光量級 API `src/3_DE_analysis/requirements.txt` **不含 sklearn**(刻意),所以既有 benchmark 在純 API
  環境會 honest-fallback;完整 ML stack 在 `environment.yaml`(含 scikit-learn/scanpy/pertpy/scvi)或
  `src/10_ml_perturbation_prediction/requirements.txt`(獨立 venv)。

**(c) 近天花板基線問題(講白):** 這個領域的核心陷阱是——很多任務的簡單基線已經很強,一個「贏了」的
數字可能只是雜訊,或是全基因組尺度上的假樂觀(見 §4 T1 GEARS 的 0.99 vs 0.02 對照)。所以任何 model 都
必須報告「在真正重要的子集(顯著差異基因 / 平衡的負類)上」的指標,不能只看全域 Pearson/AUROC。

---

## §4 候選任務逐一評估

> 評分維度:標籤來源 · 標註數 · 要打敗的基線 · 磁碟資料 · 需要的環境 · 難度 · 過度詮釋/leakage 風險 · 判定。
> **本 session 實測的數字標「(實跑)」;引用既有文件/測試的標「(引用)」——never-fabricate。**

### T1 — 基因層級(向量)擾動反應預測 · 判定:**已實測 · 誠實負面 · 不建議天真重做**

預測「一個(訓練時沒見過的)被擾動基因,會對整個下游 transcriptome 造成什麼 profile」。**這是 GB10 唯一
獨家解鎖、也最像深度學習的一題,而且本週期已經被做完了**(`src/10_ml_perturbation_prediction/`):

| 方法 | 全基因組 Pearson | 顯著差異基因 Pearson | 贏基線? | 出處(實跑) |
|---|---|---|---|---|
| GenePT ada-002 嵌入(PCA-128)+ multi-output Ridge | Rest 0.179 / Stim8hr 0.191 / Stim48hr 0.167 | —— | ❌(基線 0.182 / 0.194 / 0.170) | `results/genept_baseline_benchmark.json` |
| GEARS(GO 圖 + co-expr 圖 + GNN,官方套件) | **0.9916** | **0.0210** | ❌(均值基線 0.9956) | `results/gears_benchmark.json` |

**關鍵洞察(GEARS README 已寫得很清楚):** 全基因組 Pearson 0.99 是誤導性高分——因為 pseudobulk 裡絕大多數
基因根本沒被顯著影響,只要預測「一個大致合理的平均 profile」就能拿到 0.99(這正是均值基線 0.9956 的來源)。
真正衡量「有沒有學到擾動特異性」的官方 `pearson_de` 只有 **0.021,幾乎等於零**。兩個架構迥異的方法方向一致
地輸,比任何單一正面結果都更有參考價值。

- **難度:** 高(本質困難:用通用基因描述預測沒直接量測過的完整 profile)。
- **判定:** 這題的可行性**已有實證答案**:資料完全 ready、環境完全能跑,但**現階段標準方法產不出贏過基線的
  model**。不要因為第一版輸就調到贏為止(那是 p-hacking)。若要再碰,唯一誠實的方向是 GenePT README 自己
  列的兩階段做法(先分類「哪些基因會有反應」,再對有反應的回歸)——但那要重新誠實跑一次,見 §6。

### T2 — 已知調控子分類器 · 判定:**尚未做 · 真正還開放 · 建議下一步優先**

用 `benchmark_results.csv`(`gene, ctx_rank, ctx_specific_de, truth_class`,**1,225 列**,實查表頭確認)的
`truth_class` 當標籤,訓練一個監督式分類器,吃 DE breadth / effect / robustness / constraint 特徵,問:**能不能
贏過現有那個「用單一 `ctx_specific_de` 排序」的簡單基線?**

- **現有基線(引用 `methodological_validation/README.md:30`):** AUROC **0.85**(positives vs 1,211 個
  unlabelled 'rest' 基因);positives 中位 rank 36 vs housekeeping 964;top-50 hypergeometric p=1.8e-7。
- **標籤來源:** 一組硬編碼的 canonical CD4 T-cell 調控子(TCR proximal、Th-lineage TF、costim/cytokine)vs
  housekeeping,**刻意獨立於 platform 的 concept 模組**(避免 score→label circularity)。
- **⚠️ leakage / circularity 風險(這題的成敗關鍵):** README 自己就標註兩個坑——(1) 12/27 canonical
  positives 也出現在 platform 的 concept 模組裡,「獨立」只是「metric 沒看過 label」,不是「label 與
  platform 生物學無關」;(2) housekeeping 負類 11 個裡有 10 個已被 n≥200 gate 濾掉,AUROC 0.85 其實是
  「positives vs rest」而非平衡負類。**一個監督式分類器如果吃的特徵正是決定 `ctx_specific_de` 的那些量,
  它「贏過 0.85」可能只是把同一個訊號換個包裝——必須嚴格 hold out、並報告平衡負類上的指標。**
- **判定:** classical ML 今天就能做,有硬 ground truth,是最貼近「這工具在乎的科學問題」的一題,**但只有在
  leakage 被誠實處理時才有意義**。這是我推薦的下一個 build round 第一站。

### T3 — 自監督 target/gene embedding · 判定:**部分觸及 · 可行 · 純描述性**

對 200 萬邊的帶符號二部圖(target → downstream gene)做 truncated SVD / NMF / node2vec,得到 dense target
embedding,當**描述性特徵**或 T1 的 substrate。

- GenePT 那條線已間接觸及「基因嵌入當特徵」,但用的是外部文字嵌入,不是從本資料的反應矩陣自監督學出來的。
- **判定:** classical、無需標籤、今天可跑。但產物**純描述性**,絕不能進決策(和既有 concept/pathway 描述軸
  同級)。價值在於當 T1/T2 的輸入特徵,不是獨立交付物。

### T4 — DL on 衍生矩陣(GNN / autoencoder) · 判定:**已由 GEARS 代表性地做過一次**

GEARS(§4 T1)就是這一類的官方代表實作,已在本環境跑完並輸給基線。要再深入(換架構、全量標的、更多 epoch、
GPU)在技術上可行,但既然代表性方法已誠實負面,**在 classical 沒把天花板頂到之前不建議再投 DL 算力**。

### T5 — Foundation model on 原始單細胞(scGPT / Geneformer / scVI / CPA) · 判定:**本環境不划算**

需要 1.67 TB 原始 h5ad + 認真的 GPU 叢集。技術上資料可下載(§2),但這是一個獨立的大型算力承諾,且上游
證據(§4 T1、2025–26 文獻)顯示 foundation model 目前也不穩定贏過簡單基線。**除非有明確 GPU 資源與研究
問題,否則不建議。** 要做的話,下載工具 `src/3_DE_analysis/data_acquisition/download_precomputed_DE.py`
(requests + Range header 併發)已存在可複用。

### 明確排除(引用 `perturbation_prediction_ml.py` docstring,避免被默默重議)
- **監督式 target 優先排序(ML-GPS 風格):** repo 內沒有可用標籤集(只有 ~13 個 curated drug benchmark),
  N 太小。
- **病人反應分類器:** 需要病人 outcome 標籤,repo 完全沒有。

### 既有純量基線(T1 的前身,本 session 實跑)
`src/3_DE_analysis/perturbation_prediction_ml.py`——用同一標的另外兩個已知條件預測第三個條件的**純量** on-target
效應。本 session 對真實 `DE_stats` 實跑(sklearn 1.9.0):

```
targets=11086 rows=33258 splits=5
  baseline_mean  pearson=0.9300 mae=1.7722
  ridge          pearson=0.9341 mae=1.8044
  hist_gbr       pearson=0.9376 mae=1.6748  ← 唯一在 Pearson 與 MAE 都微幅贏基線
```

注意:這題「用自己的其他量測預測自己」本質上容易得多(基線就 0.93),和 T1「用基因功能描述預測沒量測過的
profile」不能直接比。hist_gbr 的微幅贏是真的,但幅度小到只能當「方法學上 learnable 訊號存在」的證據,
不是一個有決策價值的預測器。

---

## §5 一頁式 Scorecard

| 任務 | 標籤 | 標註數 | 要打敗的基線 | 磁碟資料 | 環境 | 難度 | 主要風險 | 判定 |
|---|---|---|---|---|---|---|---|---|
| T1 基因層級反應預測 | 自身 log_fc | 200 萬邊 | 均值 profile | ✅ | classical✅ / DL✅(已跑) | 高 | 全域指標假樂觀 | **已實測 · 負面 · 別重做** |
| T2 已知調控子分類 | `truth_class` | 1,225 | AUROC 0.85 | ✅ | classical✅ | 中 | **leakage/circularity** | **開放 · 建議優先** |
| T3 自監督 embedding | 無(自監督) | — | (描述性,無) | ✅ | classical✅ | 中低 | 純描述,勿進決策 | 可行 · 當特徵用 |
| T4 DL on 衍生矩陣 | 自身 log_fc | 200 萬邊 | 均值 profile | ✅ | DL✅(已跑) | 高 | 同 T1 | 代表性做過 · 暫緩 |
| T5 foundation model on raw | 原始 counts | 1.67 TB | — | ❌(需下載) | 需 GPU 叢集 | 極高 | 算力/再現性 | 本環境不划算 |
| (排除)監督 target 排序 | ~13 藥 | 極少 | — | — | — | — | N 太小 | 不做 |
| (排除)病人反應 | 無 | 0 | — | — | — | — | 無標籤 | 不做 |

---

## §6 建議與排序

**若(且僅若)要再投入一個 build round,建議順序:**

1. **T2 已知調控子分類器——但先把 leakage 當第一等公民。** 具體:(a) 用**嚴格 target-level hold-out**;
   (b) 明確報告**平衡負類**(不能只報 positives-vs-rest)上的指標;(c) 把「和 `ctx_specific_de` 高度共線的
   特徵」單獨標出,做一個「移除這些特徵後還能不能贏 0.85」的 ablation——**如果只有吃了共線特徵才贏,那就是
   circularity,不是模型學到東西**。這一步做誠實了,才有資格說「ML 贏過現有排序」。

2. **T3 自監督 embedding 當 T2/T1 的輸入特徵**(不是獨立交付物)。從本資料的反應矩陣自監督學出的 target
   embedding,可能比 GenePT 的外部文字嵌入更貼近本 assay——但這是假設,要誠實跑基準,不能因為第一版輸就
   調到贏。

3. **T1 只在「兩階段 classify-then-regress」這個明確假設下重做**(GenePT README 自己列的方向):先分類
   「哪些下游基因會有反應」,再對有反應的回歸——而不是一次回歸整個 ~10,000 維 profile。這是唯一還沒被
   試過、且有文獻依據的變體。其餘天真重做沒有意義。

4. **DL(T4/T5)暫緩**,直到 classical 把天花板頂到、或有明確 GPU 資源 + 研究問題。

**所有步驟都留在 `src/10_ml_perturbation_prediction/`,只寫 `results/`,絕不進決策**——沿用既有隔離紀律。

---

## §7 誠實風險與紅線

- **近天花板基線:** 多數任務的簡單基線已強(T1 均值 0.93–0.996;T2 排序 0.85),一個「贏了」的小幅數字
  可能是雜訊。必須報告子集/平衡指標,不能只看全域分數。
- **T2 的 leakage/circularity:** 見 §4 T2 與 §6——這是唯一開放任務的成敗關鍵,處理不好整個結論作廢。
- **過度詮釋:** 這個工具的 dashboard 很 polished,任何 ML 分數放進去都會被讀成「權威」。所以 model 輸出
  只留在 benchmark report(`results/`),絕不進卡片/readiness——這條已由 `src/10_...` 隔離空間強制。
- **再現性:** 帶符號 DE 的來源 `GWCD4i.DE_stats.h5ad`(15.6 GB)、pseudobulk(41.5 GB)**都沒進 git**;
  任何用到原始/pseudobulk 的 DL 不能單靠本 checkout 再現,需重新下載(工具已存在,但要記錄版本)。
- **誠實負面是結論,不是待修 bug:** T1 兩個方法都輸,是符合 2025–26 文獻的真實發現;不應被「調到贏」掩蓋。

---

## §8 綠燈各層需要什麼

| 層級 | 需要什麼 | 現況 |
|---|---|---|
| Classical ML(T2/T3) | 只需 `environment.yaml` 或 `src/10_.../requirements.txt` 的 sklearn | ✅ 環境已備,今天可跑 |
| DL on 衍生矩陣(T4) | torch/torch_geometric(獨立 venv);CPU 可跑但慢,GPU 更好 | ⚠️ 已證明可跑(GEARS),但暫緩 |
| Foundation model on raw(T5) | 下載 1.67 TB(工具已存在)+ GPU 叢集 + 明確研究問題 | ❌ 本環境不划算 |

---

## 附錄:本文件引用來源(全部可追溯,未捏造)

- 實跑數字:既有純量 benchmark(本 session `python perturbation_prediction_ml.py`)、
  `src/10_ml_perturbation_prediction/results/{gears_benchmark,genept_baseline_benchmark}.json`。
- 引用數字:`docs/mvp-research/pipeline/methodological_validation/README.md`(AUROC 0.85 及其 circularity
  caveat)、`benchmark_results.csv`(表頭與 1,225 列,實查)、`full_signed_DE/README.md`(2,056,424 列)、
  `TASK_A_GB10_HANDOFF.md`、`STAGE_SUMMARY_AND_FREEZE.md`、`environment.yaml`、
  `src/3_DE_analysis/requirements.txt`、`src/10_ml_perturbation_prediction/README.md`。
- 文獻:Ahlmann-Eltze, Huber, Anders, *Nature Methods* 2025(引自 `src/10_...` 的兩份 result README,
  本 session 未獨立向 PubMed 核對該引用)。
