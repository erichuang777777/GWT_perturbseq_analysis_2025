# CD4 Perturb-seq 競爭群體逐一對照 + 移植可行性評估

**狀態:** 稽核用文件 · **日期:** 2026-07-23 · **範圍:** hackathon gallery 36 個同資料集(primary human CD4+ T-cell Perturb-seq)競爭專案

## 本文件在做什麼

把使用者提供的「36-repo 全競爭群體」清單**逐一對照**本 portal:每個 repo 一句話「在做什麼 / 我們有沒有對應功能 / 值不值得搬」,再對**還沒搬、但有價值**的技術做一次可行性評估。

**誠實界線(必讀):**
- 「在做什麼」欄位**只採用各隊自述**(使用者提供的 gallery 描述)。有自述細節的 repo 才寫具體內容;**只有陣營歸類、無自述細節**的 repo,明確標為 `(僅陣營分類,無自述)` —— 不臆造。
- 「我們有沒有」欄位對照本 repo 實際存在的模組(見 `src/3_DE_analysis/`)。
- 「值不值得搬」是**判斷**,非事實,理由一併寫出。
- 我實際 clone 精讀過原始碼的只有第二節列的那批(G-perturb / PerturbGate / Th1-Th2 Map / CoDEGNet / Predictability Audit / Bench2Biobank / T-CTRL);其餘僅憑自述判讀。

---

## 一、A 陣營 — 靶點發現流水線(跟我們最像,正面對決)

| repo | 一句話在做什麼(自述) | 我們有沒有對應 | 值不值得搬 |
|---|---|---|---|
| **#163 The Nineteen** | 6 條正交發現 lens → 整合 scorecard → 單細胞驗證 → 結構/遺傳/化學 dossier;34,000→19 靶點,每靶附 KD%、concordance r、PDB、ChEMBL、GWAS 數 | ✅ 部分:target card + readiness + trans_network + 外部證據 dossier(Open Targets/STRING/HIV) | ❌ 不搬 —— 它是 HPC 一次性 pipeline,無可重用 API;結構層(PDB/redocking)需 AF2/docking,超出範圍 |
| **#81 Reversing autoimmunity** | Connectivity-Map 式 weighted-GSEA「反轉疾病特徵」→ permutation null + BH-FDR;11,281 KD × 3 疾病 → 2 universal;**有方向性** | ✅✅ **已有** `disease_reversal.py`(把 KD signed-DE 對任意疾病 signature 做反轉評分),概念等價 | ⚪ 已覆蓋 —— 可考慮補「permutation null + BH-FDR」的顯著性層(見第五節評估) |
| **#123 Bench to Biobank** | 5 層 config-driven,跑任何 screen;驗證到**個人層級基因組**(All of Us/FinnGen/GWAS Catalog/BioBank Japan);**主動抓自己的假陽性**(MHC/nearest-gene down-weight) | ⚠️ 部分:外部證據(Open Targets GWAS + UKBB LoF burden)有;**自我假陽性框架沒有** | 🔶 **值得評估(第五節重點)** —— 假陽性框架是本 portal 最缺的一塊;個人基因組層驗證則需外部資料,不搬 |
| **#190 Perturb2Target** | 4 層 agentic:GWAS fine-mapping → 細胞圖譜 → CRISPRi 反轉 → AF2 結構 | ⚠️ 部分:有 genetic_double_support + disease_reversal;無 fine-mapping、無 AF2 結構層 | ❌ 不搬 —— fine-mapping/AF2 需要重外部資源;反轉層我們已有 |
| **#224 Sézary** | 反轉分數 = KD 特徵 vs 疾病特徵加權 cosine 取負;**先反選「哪個疾病最適合這個資產」** | ✅ 部分:`disease_reversal.py` 可對多個 signature 評分 | ⚪ 概念已有 —— 「反選疾病」是好框架,可作 disease_reversal 的一個 ranking view(低成本,第五節提及) |
| **#223 Atopic dermatitis** | cosine + 獨立監督分類器;獨立病灶皮膚 scRNA(GSE147424)驗證;STAT6/GATA3 rank-1 內建對照 | ✅ 類比:我們有獨立 CRISPRa HIV 篩選(GSE318876)concordance + 金標準基因 | ❌ 不搬 —— 驗證策略我們已有等價物,特定疾病資料無關 |
| **#227 ICB-resistance** | 訓練模型重現 responder/non-responder 特徵 → 排 KD | ⚪ 相關:disease_reversal 可吃 responder-vs-nonresponder signature | ❌ 不搬 —— 特定 ICB 情境;通用反轉引擎已能處理 |
| **#240 Th1/Th2 Map** | 兩軸打分,但**先對標作者發表係數再排名**(polarization ρ=0.72 保留,activation ρ=0.13 降 exploratory);AUROC 0.92 | ✅✅ **已移植** `axis_validator.py` + `/api/axis_validation`(PR #112) | ✔️ 已完成 |
| **#198** | p38 透過 NR4A3 等平行 TF 支撐 Treg 程式 —— 人類資料的可測試機制 | ✅ 概念:`mechanism_graph.py` + hypothesis 生成 | ❌ 不搬 —— 這是一個「發現」非工具;無可移植程式 |
| **#115 CD4 Regulator Atlas** | 8 條證據層 → 加法 regulator_score(0–9);**按 Rest/Stim8/Stim48 分層,絕不 pool**;「把任何 Perturb-seq 變 regulator map」模板 | ✅ 有:per-condition 統計 + `stimulation_switch_explorer.py` + `stimulationGated` 旗標 | ⚪ 大致等價 —— 值得做的是一條**測試**確認我們全程未跨刺激狀態 pool(第五節提及) |
| **#234 HumanCD4CoDEGNet** | power/edge/KD/detectability 混雜控制;K562 換細胞型複製;確認 Pritchard 2026 拓撲;「網路 shape-invariant 但 identity-labile」 | ✅✅ **方法已移植** `controlled_enrichment.py`(covariate-matched permutation + partial-Spearman,PR #112) | ✔️ 已完成(本體是 HPC 腳本,只搬方法) |
| **#275** | (僅陣營分類,無自述) | — | ⚪ 資訊不足,無法判斷 |
| **#15** | (僅陣營分類,無自述) | — | ⚪ 資訊不足,無法判斷 |

---

## 二、B 陣營 — 可靠性 / 審計優先(我們自認的賣點,對手雲集)

| repo | 一句話在做什麼(自述) | 我們有沒有對應 | 值不值得搬 |
|---|---|---|---|
| **#23 T-CTRL** | ISCI 指數:問「在 effect size **之後**,方向性 + 跨捐獻者重複性還加不加資訊」;M→M+C 增量測試(+0.357 AUPRC);明確 scope map(哪裡成立/失敗) | ⚠️ 部分:`reliability.py`(R_dep)量了跨 guide/donor 重現,但**沒有**「增量資訊」的 AUPRC 測試 | 🔶 **值得評估(第五節)** —— 「重現性是否在 effect 之外還加資訊」是很硬的正當性,可用金標準基因當 label |
| **#133 G-perturb** | generalizability theory 給每靶一個可靠度係數,按 effect×dependability 排;方法被對抗式 red-team | ✅✅ **已移植** `reliability.py`(R_dep = 跨 guide×跨 donor 合成,`S_t=effect×R_dep`,PR #112) | ✔️ 已完成 |
| **#261 Predictability Audit** | 7 個預註冊調查,6 個失敗 → 失敗就是發現;只有 ~17% KD 可信(SNR>3) | ⚠️ 部分:`readiness_selfcheck.py`(忠實性自檢)已搬;**SNR>3 predictability flag 沒搬** | 🔶 部分可行 —— SNR flag 需 control-cell variance,卡片未帶(第五節說明阻塞點) |
| **#191** | (僅陣營分類,無自述) | — | ⚪ 資訊不足 |
| **#266 Prospect** | 量化模型「47.9% 矛盾率」;每筆結果 accepted=false 直到人用 **Ed25519 金鑰簽署**,模型無法簽 | ⚠️ 部分:有 provenance 戳記 + readiness_selfcheck 的一致性檢查;無密碼學簽核 | ❌ 不搬密碼學簽核(治理功能,對單機分析 portal 過重);「矛盾率」指標概念上已被 selfcheck 覆蓋 |
| **#229 Th2 Suppressor That Wasn't** | 找到訊號後**主動摧毀它**(+0.54→+0.18 是 artifact,FDR≈1);整個項目是誠實負結果 | ✅✅ **已有** `self_falsification.py`(MED12 大 footprint 看似 master-regulator 實為假陽性的自我證偽 demo) | ✔️ 概念已覆蓋 |
| **#271** | (僅陣營分類,無自述) | — | ⚪ 資訊不足 |
| **#155 PerturbGate** | donor-paired,6/6 leave-one-donor-out;獨立 JIA 世代(+0.165);**誠實三元組**(PAK2 拒絕 / RIPK1 未支持 / RICTOR 保留為假說),negatives 是 first-class | ✅✅ **已移植** `evidence_class.py`(型別化 evidence-class + 守恆不變式,PR #112) | ✔️ 已完成 |

---

## 三、C 陣營 — 工具 / Builder(我們的產品面)

| repo | 一句話在做什麼(自述) | 我們有沒有對應 | 值不值得搬 |
|---|---|---|---|
| **#5 ShiftScope** ⭐(Builder 得獎) | condition-agnostic,任何兩群細胞即可跑;「已知 regulator 下沉,被忽視的染色質基因浮現」 | ✅ 部分:CSV 上傳路徑 + `signed_de_io.py` + import_manager | ⚪ 產品定位參考,非技術移植 —— 我們的上傳引擎已是同類強項 |
| **#136 Spot** | 任何 immune profiling RNAseq;產出上傳 HuggingFace | ✅ 部分:上傳/匯入路徑有;HF 匯出無 | ❌ 不搬 HF 匯出(無需求) |
| **#173 Sera** | Claude 只能「指」不能「寫事實」;controls-first gate 先重現已知生物學才顯示新命中 | ✅ 類比:金標準基因(ZAP70/MED12)+ known-answer 測試 = 「先重現已知才信」 | ⚪ 紀律已有 —— 可把「controls-first」明文化成一個 gate 說明(文件層,非程式) |
| **#214 Louis** | MCP + Slack bot 活在 Claude 裡;**殺掉自己的 flagship**(DOT1L 是 cross-disease artifact) | ✅ 「殺 flagship」概念在 `self_falsification.py`;MCP/Slack 不適用 | ❌ 不搬 MCP/Slack(交付形態不同) |
| **#210** | (僅陣營分類,無自述) | — | ⚪ 資訊不足 |
| **#107** | (僅陣營分類,無自述) | — | ⚪ 資訊不足 |

---

## 四、D 陣營(方法新穎/利基)+ E 陣營(邊緣提及 CD4)

| repo | 陣營 | 狀態 |
|---|---|---|
| **#92, #49, #56, #86, #105, #160** | D 方法新穎/利基 | (僅陣營分類,無自述) —— 資訊不足,無法逐一判斷;不同賽道,與本 portal 直接衝突低 |
| **#7, #165** | E 邊緣提及 CD4 | 非直接競爭,無移植價值 |

> 這 8 個 repo 使用者當初只給了陣營歸類、沒有一句話自述。若要補完,需要各隊的 gallery 原始描述 —— **我不臆造它們在做什麼**。

---

## 五、還沒搬、但有價值者 —— 移植可行性評估

依「填補本 portal 具體缺口 × 可用現有資料實作」兩軸排序。

### 🥇 5.1 Bench2Biobank 自我假陽性框架(#123)—— 最有價值,部分可行

**它做什麼:** 對每個命中主動問「這是不是偽陽性」,用三類對照 down-weight:① 落在 **MHC region**(chr6:~25–34 Mb,LD 極強、關聯氾濫)② **nearest-gene 陷阱**(GWAS 訊號其實指向鄰近的名基因)③ **phenome-category** 過廣(到處都關聯 = 不特異)。旗艦 hit ATP2B1 因映射到隔壁名基因而被誠實 down-weight。

**為何有價值:** 這正是本 portal 最缺的一環 —— 我們的驗證多是「證明我對」,缺「主動抓我哪裡錯」。且與既有紀律(descriptive≠decision、self_falsification)完全同源。

**可行性拆解:**

| 子檢查 | 需要的資料 | 我們有嗎 | 判定 |
|---|---|---|---|
| **phenome-category 過廣** | 每基因的疾病關聯數 / 跨類別廣度 | ✅ 有 `externalEvidence.gwas`(nImmuneGeneticAssoc、topAnyDisease、footprintClass) | ✅ **可直接做** —— 加一個「關聯過廣 → 特異性低」的 descriptive flag |
| **MHC-region 旗標** | 染色體座標(chr6:25–34Mb) | ❌ 卡片無座標;有 Ensembl ID | 🔶 **需補一張離線 Ensembl→染色體位置對照**(靜態、可快取),之後純查表 |
| **nearest-gene 陷阱** | GWAS lead SNP → 最近基因映射 | ❌ 無 SNP 級資料;有 gene-level `gwascatalog.tsv` | ⚠️ **不完全可行** —— 沒有 SNP 座標無法判「最近基因」;只能做較弱的代理(gene 是否本身在 GWAS catalog) |

**建議落地(增量、descriptive-only):** 新增 `false_positive_audit.py`,先實作**完全可行的 phenome-breadth 特異性旗標**(用現成 GWAS evidence),把 MHC 與 nearest-gene 標為 `measured:false / requires: gene-coordinate table`(honest `unknown≠0`,不假裝有)。之後若補上離線座標表,再點亮 MHC 檢查。**絕不折進 readiness call** —— 只作 dossier 上的「特異性/假陽性風險」descriptive 徽章。

**成本:** phenome-breadth 旗標 ~半天(資料現成);MHC 需先做座標對照表(~1 天,一次性);nearest-gene 建議**不做**(資料前提缺)。

### 🥈 5.2 T-CTRL ISCI 增量資訊測試(#23)—— 中價值,可行

**它做什麼:** 不只報「重現性高」,而是量化「在 effect size **之後**,加入方向性+跨捐獻者重現性,對區分真/假靶點還加不加資訊」—— 用 M(只有 effect)vs M+C(加重現性)的 **AUPRC 增量**(+0.357)證明重現性不是冗餘。

**為何有價值:** 它給我們的 `R_dep` 一個**正當性證明**。目前 R_dep 是「合理的合成」,但沒證明它在 effect size 之外真的加資訊。ISCI 正好補這一刀。

**可行性:** ✅ **可行。** 需要一組 ground-truth label(真/假靶點)來算 AUPRC —— 我們有**金標準基因**(ZAP70 應高、MED12 應被 broad-effect 標記)可當種子,亦可用外部 concordance(HIV 篩選、STRING recovery)當 proxy label。做法:比較「只用 |effect| 排序」vs「用 S_t=effect×R_dep 排序」對 label 的 AUPRC/AUROC 差。落點 `reliability_increment.py`(或併入 `reliability.py`),descriptive-only 的一份報告輸出。

**成本:** ~1 天。**風險:** label set 偏小(金標準基因少),AUPRC 增量估計不穩 —— 需誠實報 CI,或標為 exploratory。

### 🥉 5.3 #261 SNR>3 predictability flag —— 有價值但被資料阻塞

**它做什麼:** 只把 **SNR(signal-to-noise)>3** 的 KD 視為「可預測/可信」,結論是資料只有 ~17% KD 過關。

**可行性:** ❌ **目前阻塞。** SNR 需要 **control-cell variance**(非擾動細胞的基因表現變異),而 target card 只帶了 cross-guide/cross-donor 相關,**沒帶 control 變異**。要搬需回到上游 pseudobulk 階段(`make_pseudobulk.py`)多輸出一欄 control variance —— 是 pipeline 變更,非加法。**建議:** 記錄為「已知缺口」,待未來重跑 pipeline 時一併補上游欄位。

### 其他(低優先 / 不建議)

- **#224 反選疾病 view**:低成本、概念已在 `disease_reversal.py`。可作一個 ranking view(對多個 disease signature 排「哪個最被此靶點反轉」)。~半天,錦上添花。
- **#81 permutation null + BH-FDR**:給 disease_reversal 的反轉分數補顯著性層。中價值、可行(~1 天),但要小心與既有 `controlled_enrichment.py` 的 permutation 工具不重複造輪子 —— 應**複用** `matched_permutation_test`。
- **#115 no-pool 測試**:加一條測試守住「全程不跨 Rest/Stim8/Stim48 pool」。~2 小時,純防呆,低風險高紀律值。
- **#266 Ed25519 簽核 / #214 MCP-Slack / #163 AF2 結構**:交付形態或資源前提不符,**不建議搬**。

---

## 六、一頁總結

| 類別 | repo | 動作 |
|---|---|---|
| ✔️ 已移植(PR #112) | #133, #155, #240, #234, #261(自檢部分) | 完成 |
| ✔️ 概念已有 | #81, #224, #229, #214(殺 flagship)| `disease_reversal.py` / `self_falsification.py` |
| 🔶 建議評估後移植 | **#123 假陽性框架(phenome-breadth 先做)**、**#23 ISCI 增量測試** | 第五節 |
| ⏸ 資料阻塞,記為缺口 | #261 SNR flag(需 control variance)| 待上游 pipeline |
| ❌ 不建議搬 | #163(HPC/AF2)、#190(fine-map/AF2)、#266(密碼學)、#214(MCP)、#136(HF) | 形態/資源不符 |
| ⚪ 資訊不足 | #275 #15 #191 #271 #210 #107 + D/E 陣營 | 無自述,不臆造 |

**下一步建議(若要動手):** 先做 **5.1 的 phenome-breadth 假陽性旗標**(資料現成、缺口最大、與既有紀律同源),再做 **5.2 ISCI 增量測試**(給 R_dep 正當性)。兩者都是 descriptive-only、加法式、可加測試,零 pipeline 變更。
