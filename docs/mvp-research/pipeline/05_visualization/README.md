# 05_visualization — 視覺化階段文件

> GWT CD4⁺ T Perturb-seq 標的發現 MVP · 視覺化階段整編文件（繁體中文）
> 整編日期：2026-07-08

---

## 1. 視覺化階段在 pipeline 的定位

本階段（`05_visualization`）是標的發現 pipeline 的**輸出呈現層**，不產生新的統計量，而是把上游三層資料整編為可判讀的圖形與 3D 結構，支援標的優先排序決策。資料流向如下：

```
01_raw → 02_curated → 03_processed → 04_statistical → 05_visualization
                (逐標的×條件)   (條件彙總)    (全域摘要)      (本階段)
```

**本階段讀取的上游欄位：**

| 上游階段 | 檔案 | 本階段讀取的關鍵欄位 | 用途 |
|---|---|---|---|
| **02_curated** | `curated_targets.csv`（33,983 列 = 11,526 標的 × 3 條件） | `target_contrast_gene_name`、`culture_condition`、`n_total_de_genes`、`n_up_genes`、`n_down_genes`、`ontarget_effect_size`、`n_cells_target`、`ontarget_significant`、`offtarget_flag`、`passes_gate`、`ontarget_effect_category`、`logDE` | 逐列（標的×條件）繪圖的主要來源；分佈、排序、散點、熱圖 |
| **03_processed** | `condition_stats`（3 列 = 3 培養條件） | `culture_condition`、`n_up_genes_sum`、`n_down_genes_sum`、`n_targets` | 條件層彙總：分組長條、堆疊組成、條件比較 |
| **04_statistical** | `summary_statistics.csv`（18 個指標） | `n_gate_passing_unique_targets`、`nde_median`、`nde_max`、`effect_min/median/max`、`corr_nde_ndownstream`、`frac_logde_lt1` 等 | 圖表標註、門檻線、篩選漏斗計數、全域敘事 |

**三培養條件的資料規模（來自 03_processed / 04_statistical）：**

| 條件 | 列數 | 上調基因總和 | 下調基因總和 | 標的數 |
|---|---|---|---|---|
| Rest | 11,287 | 371,945 | 227,402 | 11,287 |
| Stim8hr | 11,415 | 506,326 | 280,429 | 11,415 |
| Stim48hr | 11,281 | 392,533 | 277,789 | 11,281 |

**全域關鍵統計（04_statistical，供圖表標註與敘事）：**

- 總列數 `n_rows` = **33,983**；唯一標的 `n_unique_targets` = **11,526**
- on-target 顯著列 `n_ontarget_significant` = **21,216**；off-target 旗標 `n_offtarget_flag` = **2,837**
- 通過品質門檻的列 `n_gate_passing_rows` = **2,131**，對應唯一標的 `n_gate_passing_unique_targets` = **1,235**
- 下游 DE 基因數 `n_total_de_genes`：中位 **2**、最大 **5,920**（右偏嚴重，故分佈圖多取 log10）
- on-target 效應量 `ontarget_effect_size`：範圍 **-58.5 ~ 7.1**、中位 **-6.3**
- `n_total_de_genes` 與 `n_downstream` 相關係數 = **1.0000**（近乎共線）；`logDE < 1` 的比例 = **75.6%**

---

## 2. 2D 圖表清單（53 張）

每張圖以**上游欄位與統計量**判讀其資料意義（非看圖描述）。所有圖的底層資料同一份：`DE_stats.suppl_table.csv`（公開 S3，33,983 列 = 11,526 標的 × 3 培養條件；每列＝一個標的在一個條件下的差異表現統計），經 02_curated 整理後逐列取用。

圖檔本體見本專案 artifact（`gallery_1_distributions.png` … `gallery_7b_upset.png`、`COVER_target_ranking.png`、`viz_dotplot_3d.png` 等）；完整目錄另見 `2D_CHART_CATALOG_完整目錄.md`。

### 2.1 分佈類（Distributions）— 單變量分佈（10 張）

| ID | 標題 | 圖表類型 | 輸入資料（層／欄位） | 資料意義 |
|---|---|---|---|---|
| D1 | Violin 小提琴圖 | 單變量分佈 | 02_curated (逐列) + 03_processed (condition_stats) | 三條件下 log10(DE基因+1) 的分佈密度，寬度=該效應廣度的標的數。 吃 n_total_de_genes（取 log10）與 culture_condition 兩欄。log 轉換是因原始值右偏嚴重（中位僅 2、最大 5,920）。三條件各約 1.1 萬列（Rest 11,287/Stim8hr 11,415/Stim48hr 11,281）。 |
| D2 | Box 箱型圖 | 單變量分佈 | 02_curated (逐列) + 03_processed (condition_stats) | 同資料的中位數與四分位距，比小提琴精簡。 同 D1 的 n_total_de_genes×condition。箱體=IQR、線=中位。原始中位數低（2 個 DE 基因）反映多數擾動無廣泛效應。 |
| D3 | Ridgeline 堆疊密度 | 單變量分佈 | 02_curated (逐列) + 03_processed (condition_stats) | 三條件密度曲線垂直錯開，避免重疊遮擋。 同 D1 資料，各條件獨立核密度估計。條件數多時比重疊圖清楚。 |
| D4 | Histogram 直方圖 | 單變量分佈 | 02_curated (逐列) + 03_processed (condition_stats) | 三條件效應廣度直方圖疊合，顯示絕對計數。 同 D1，但 y 軸是計數非密度。76% 的列 log10(DE+1)<1。 |
| D5 | ECDF 累積分佈 | 單變量分佈 | 02_curated + 04_statistical | x 值以下標的的累積比例。 對 n_total_de_genes 排序後計算累積比例。可直接讀出 76% 標的 log DE<1（<10 個 DE 基因）。 |
| D6 | Strip 抖動散點 | 單變量分佈 | 02_curated (逐列) | 每標的一點、水平抖動，各條件抽 400。 同 D1 抽樣版。保留個別點，適合看離群值。 |
| D7 | Swarm 蜂群圖 | 單變量分佈 | 02_curated (逐列) | 點不重疊排列，每條件抽 150。 同 D1 抽樣版，用不重疊佈局。因原始資料 3.4 萬列過密，必須抽樣。 |
| D8 | Raincloud 雨雲圖 | 單變量分佈 | 02_curated (逐列) | 半小提琴+box+strip 三合一。 同 D1，三種呈現疊加：分佈形狀+摘要統計+個別點。 |
| D9 | 1D KDE 密度曲線 | 單變量分佈 | 02_curated (逐列) + 03_processed (condition_stats) | 三條件單變數核密度平滑曲線。 對 logDE 做核密度。三條件曲線幾乎重合，說明分佈本質不隨活化改變。 |
| D10 | Q-Q plot 常態檢查 | 單變量分佈 | 02_curated (逐列) | Stim48hr 敲低效應 vs 理論常態分位。 吃 ontarget_effect_size（Stim48hr）。偏離對角線=非常態，左尾重（min -58.5）反映少數極強敲低。 |

### 2.2 矩陣／關聯類（Matrices）— 二維關聯與熱圖（10 張）

| ID | 標題 | 圖表類型 | 輸入資料（層／欄位） | 資料意義 |
|---|---|---|---|---|
| M1 | 相關性熱圖 | 二維/矩陣關聯 | 02_curated (逐列) | 7 個數值特徵兩兩 Pearson 相關。 吃 n_up/n_down/n_total_de_genes、n_downstream、ontarget_effect_size、n_cells_target、target_baseMean。揭露冗餘：n_total_de_genes 與 n_downstream 相關 1.00（幾乎重複）。 |
| M2 | 階層聚類熱圖 | 二維/矩陣關聯 | 02_curated + 04_statistical | top 標的×特徵矩陣（z 標準化），ward 聚類排序。 top 12 標的的 5 特徵均值，逐欄 z 標準化後聚類。相似行為的標的聚在一起。 |
| M3 | Hexbin 六角密度 | 二維/矩陣關聯 | 02_curated (逐列) | 敲低效應 vs 效應廣度的六角格計數。 吃 ontarget_effect_size×logDE，33,983 點用六角格避免過度繪製。 |
| M4 | 2D density 密度散點 | 二維/矩陣關聯 | 02_curated (逐列) | 同 M3 但連續核密度著色。 同 M3 兩欄，適合中等點數。 |
| M5 | Scatter matrix 散點矩陣 | 二維/矩陣關聯 | 02_curated (逐列) | 3 特徵兩兩散點+對角直方圖。 吃 3 個數值特徵，看所有兩兩關係。認知負擔高，僅探索用。 |
| M6 | 條件×指標熱圖 | 二維/矩陣關聯 | 02_curated (逐列) + 03_processed (condition_stats) | 每指標在三條件的平均（逐列 z 標準化）。 7 指標×3 條件的平均值矩陣。看哪些指標隨活化改變。 |
| M7 | Joint scatter 邊際散點 | 二維/矩陣關聯 | 02_curated (逐列) | 散點+上/右邊際直方圖。 吃 ontarget_effect_size×logDE，邊際直方圖顯示各自分佈。 |
| M8 | Dendrogram 聚類樹 | 二維/矩陣關聯 | 02_curated + 04_statistical | top 標的階層聚類的獨立樹狀圖。 top 12 標的 5 特徵 z 分數的 ward 連結。樹高=合併距離。 |
| M9 | Contour 等高線 | 二維/矩陣關聯 | 02_curated (逐列) | 敲低效應 vs 廣度的密度等高線，抽 3000。 同 M3 兩欄的核密度等高線，填色表密度。 |
| M10 | Gene×condition DE 熱圖 | 二維/矩陣關聯 | 02_curated + 04_statistical | top 標的在三條件的 DE 基因數（原始值）。 吃 n_total_de_genes 的 pivot（標的×條件），viridis 著色。非相關、是原始計數。 |

### 2.3 排序類（Ranking）— 標的優先排序（10 張）

| ID | 標題 | 圖表類型 | 輸入資料（層／欄位） | 資料意義 |
|---|---|---|---|---|
| R1 | Lollipop 排序 | 排序/長條 | 02_curated + 04_statistical | top 標的按最大效應廣度排序，藍=免疫、紅=broad-effect。 吃每標的跨條件 max(n_total_de_genes)，取前 12。顏色來自 broad_effect 名單（10 個泛效應基因）。MVP 首頁首選圖。 |
| R2 | Diverging bar 分歧長條 | 排序/長條 | 02_curated (逐列) + 03_processed (condition_stats) | 每標的上調(右)/下調(左)基因數。 吃 n_up_genes/n_down_genes。三條件上調總數：Rest 371,945/Stim8hr 506,326/Stim48hr 392,533。 |
| R3 | Stacked bar 組成長條 | 排序/長條 | 02_curated + 04_statistical | 三條件通過門檻/僅顯著/不顯著的組成。 吃 _pass/_sig 分層計數。顯著 21,216 列、通過門檻 2,131 列。 |
| R4 | Waterfall 瀑布圖 | 排序/長條 | 02_curated + 04_statistical | 所有標的敲低效應排序後連續呈現。 吃 ontarget_effect_size 排序（min -58.5~max 7.1）。左側深負=強敲低。 |
| R5 | Bubble 泡泡圖 | 排序/長條 | 02_curated (逐列) | x=效應、y=廣度、大小=細胞數。 吃 ontarget_effect_size×n_total_de_genes，泡泡=n_cells_target（中位 539）。細胞數大=證據強。 |
| R6 | Grouped bar 分組長條 | 排序/長條 | 02_curated (逐列) + 03_processed (condition_stats) | 選定基因三條件效應並排。 吃 n_total_de_genes 按基因×條件分組。看條件特異性。 |
| R7 | Bar with error bars 誤差棒長條 | 排序/長條 | 02_curated + 04_statistical | top 標的跨條件均值±SD。 吃每標的三條件的 n_total_de_genes 均值與標準差。誤差棒大=條件間變異大。 |
| R8 | Point plot 點趨勢 | 排序/長條 | 02_curated (逐列) + 03_processed (condition_stats) | 選定基因跨三條件的趨勢線。 吃 n_total_de_genes 按基因×條件。連線顯示每基因的條件動態。 |
| R9 | MA plot | 排序/長條 | 02_curated (逐列) | 平均表現 vs 敲低效應。 吃 target_baseMean（log10）×ontarget_effect_size。診斷效應是否依賴表現量。 |
| R10 | Dot-plot matrix (scanpy式) | 排序/長條 | 02_curated (逐列) | 基因×條件點矩陣：大小=廣度、色=敲低。 吃 n_total_de_genes（大小）+ ontarget_effect_size（色）。單細胞領域標準呈現。 |

### 2.4 降維類（Dim-reduction）— 多變量降維（6 張）

| ID | 標題 | 圖表類型 | 輸入資料（層／欄位） | 資料意義 |
|---|---|---|---|---|
| V1 | PCA 主成分 | 降維/多變量 | 02_curated (逐列) | 5 特徵降 2 維，色=廣度、紅環=broad-effect。 吃 3,098 標的×5 特徵（standardize 後）。PC 軸有方差解釋%。broad-effect 聚高廣度角落。 |
| V2 | t-SNE | 降維/多變量 | 02_curated (逐列) | 非線性降維，強調局部鄰域。 同 V1 輸入。軸無意義、簇間距離不可信，僅看分群。 |
| V3 | UMAP | 降維/多變量 | 02_curated (逐列) | 非線性降維，保留全域結構。 同 V1 輸入。perturb-seq 標準降維，三法結論一致。 |
| V4 | Radar 雷達圖 | 降維/多變量 | 02_curated + 04_statistical | 選定基因多指標輪廓。 吃 3 個標準化指標×4 基因。比較候選標的優缺輪廓。 |
| V5 | Circular bar 環形長條 | 降維/多變量 | 02_curated + 04_statistical | top 標的效應廣度極座標長條。 同 R1 資料的極座標版。形式優先場合用。 |
| V6 | PCA biplot 載荷雙標圖 | 降維/多變量 | 02_curated (逐列) | PCA 點雲+特徵載荷箭頭。 同 V1，疊加 5 特徵的 PC 載荷。看哪些特徵驅動分離。 |

### 2.5 網路／集合類（Networks & Sets）（7 張）

| ID | 標題 | 圖表類型 | 輸入資料（層／欄位） | 資料意義 |
|---|---|---|---|---|
| N1 | STRING 網路 | 網路/集合關係 | 02_curated + 04_statistical | 候選標的蛋白交互作用網路。 吃 STRING API 的 combined_score≥400 邊。免疫標的成 TCR 模組、broad-effect 成轉錄機器模組。 |
| N2 | Chord 環形網路 | 網路/集合關係 | 02_curated (逐列) | 基因排圓周、連線在圓內。 同 N1 邊資料，連線粗細=交互信心分數。 |
| N3 | Venn 文氏圖 | 網路/集合關係 | 02_curated + 04_statistical | 顯著/通過門檻/broad-effect 集合重疊。 吃基因層 _sig(7,913)、_pass(1,235)、broad(10) 集合。broad-effect 全落在通過門檻內。 |
| N4 | Manhattan 曼哈頓式 | 網路/集合關係 | 02_curated + 04_statistical | 標的依 chunk 排列、交替色、紅線=門檻。 吃 chunk 分組與 n_total_de_genes。檢查批次效應。 |
| N5 | Slope 斜率圖 | 網路/集合關係 | 02_curated (逐列) + 03_processed (condition_stats) | 每基因跨三條件效應連線。 吃 n_total_de_genes 按基因×條件。揭露多數標的 Stim8hr 高峰、Stim48hr 回落。 |
| N6 | Stacked area 堆疊面積 | 網路/集合關係 | 02_curated (逐列) + 03_processed (condition_stats) | 上/下調總 DE 沿三條件。 吃 n_up_genes/n_down_genes 加總。Stim8hr 上調總數最高（506,326）。 |
| N7 | UpSet plot 集合交集 | 網路/集合關係 | 02_curated + 04_statistical | 4 證據集合交集（>3 集合用）。 吃基因層 significant(7,913)、passes_gate(1,235)、has_offtarget(1,152)、broad_effect(10)。取代 Venn 處理多集合。 |

### 2.6 複合類（Composite）— 多面板組合（3 張）

| ID | 標題 | 圖表類型 | 輸入資料（層／欄位） | 資料意義 |
|---|---|---|---|---|
| C1 | 3D dot plot 三合一 | 多面板複合 | 02_curated (逐列) | 大小=廣度、色=敲低、外環=證據狀態。 吃 n_total_de_genes+ontarget_effect_size+_pass/broad_effect。使用者慣用三合一。 |
| C2 | Volcano 火山圖 | 多面板複合 | 02_curated (逐列) | 效應大小 vs 顯著性。 吃 ontarget_effect_size×顯著性指標。標準 DE 呈現。 |
| C3 | QC funnel 篩選漏斗 | 多面板複合 | 02_curated + 04_statistical | 逐步套用門檻的標的數遞減。 吃全部門檻：33,983→n_cells≥200→顯著→無脫靶→≥50 DE→2,131。 |

### 2.7 階層／流向類（Hierarchy & Flow，互動）（7 張）

| ID | 標題 | 圖表類型 | 輸入資料（層／欄位） | 資料意義 |
|---|---|---|---|---|
| H1 | Treemap 矩形樹圖 | 階層/流向 | 02_curated + 04_statistical | 面積=效應廣度、色=敲低，階層 group→gene。 吃通過門檻標的的 breadth（面積）+ effect（色）+ group 分類。 |
| H2 | Sunburst 放射階層 | 階層/流向 | 02_curated (逐列) | 同 Treemap 的放射版。 同 H1 資料，放射圈層呈現階層。 |
| H3 | Icicle 冰柱階層 | 階層/流向 | 02_curated (逐列) | 同 Treemap 的冰柱版。 同 H1 資料，矩形冰柱呈現階層。 |
| H4 | Sankey 流向圖 | 階層/流向 | 02_curated (逐列) + 03_processed (condition_stats) | 條件→證據狀態的流量。 吃 condition×status 交叉計數（9 條流）。線寬=標的數。 |
| H5 | Funnel 互動漏斗 | 階層/流向 | 02_curated + 04_statistical | QC 篩選漏斗的 plotly 互動版。 同 C3 的五階段：33,983→30,515→19,297→16,998→2,131。 |
| H6 | Parallel coordinates 平行座標 | 階層/流向 | 02_curated + 04_statistical | 多特徵平行軸，紅=broad-effect，抽 500。 吃 n_up/n_down/effect/n_cells 四軸。可拖曳篩選各軸。 |
| H7 | Parallel categories 類別平行 | 階層/流向 | 02_curated (逐列) + 03_processed (condition_stats) | 條件×狀態×脫靶的類別流，抽 2000。 吃 culture_condition×status×offtarget 三類別維度。 |

---

## 3. 3D 結構清單（15 個 AlphaFold 標的）

由 AlphaFold Protein Structure Database 取得的預測單體結構（`.cif`），涵蓋 5 個免疫相關（immune）候選與 10 個泛效應（broad-effect）候選。pLDDT 為 AlphaFold 每殘基信賴度的全鏈平均（0–100，越高越可信）。

| 基因 | UniProt | pLDDT（平均） | 信賴等級 | 殘基長度 | 分組 |
|---|---|---|---|---|---|
| CD3E | P07766 | 73.1 | 高 (Confident) | 207 | immune |
| LAT | O43561 | 59.3 | 低 (Low) | 262 | immune |
| CD247 | P20963 | 62.4 | 低 (Low) | 164 | immune |
| PLCG1 | P19174 | 82.8 | 高 (Confident) | 1,290 | immune |
| VAV1 | P15498 | 86.4 | 高 (Confident) | 845 | immune |
| TADA2B | Q86TJ2 | 86.7 | 高 (Confident) | 420 | broad-effect |
| SENP5 | Q96HI0 | 54.9 | 低 (Low) | 755 | broad-effect |
| SGF29 | Q96ES7 | 91.8 | 非常高 (Very high) | 293 | broad-effect |
| UBXN1 | Q04323 | 76.4 | 高 (Confident) | 297 | broad-effect |
| MED12 | Q93074 | 65.1 | 低 (Low) | 2,177 | broad-effect |
| CCNC | P24863 | 91.4 | 非常高 (Very high) | 283 | broad-effect |
| SUPT20H | Q8NEM7 | 58.8 | 低 (Low) | 779 | broad-effect |
| TADA1 | Q96BN2 | 77.1 | 高 (Confident) | 335 | broad-effect |
| DENR | O43583 | 62.5 | 低 (Low) | 198 | broad-effect |
| PMVK | Q15126 | 92.4 | 非常高 (Very high) | 192 | broad-effect |

**分組摘要：**

- **immune（5）**：CD3E, LAT, CD247, PLCG1, VAV1；平均 pLDDT ≈ 72.8，殘基長度 164–1,290
- **broad-effect（10）**：TADA2B, SENP5, SGF29, UBXN1, MED12, CCNC, SUPT20H, TADA1, DENR, PMVK；平均 pLDDT ≈ 75.7，殘基長度 192–2,177

> pLDDT 判讀：≥90 非常高、70–90 高、50–70 低、<50 非常低。本清單中 3 個標的達非常高（PMVK、SGF29、CCNC…），0 個低於 50；SENP5（54.9）、SUPT20H（58.8）、LAT（59.3）信賴度偏低，多為含大量無序區（IDR）或多結構域柔性連接的蛋白，其低 pLDDT 區段應保守解讀。

3D 互動檢視另見本專案 3D 互動 HTML artifact。

---

## 4. 參考文獻

1. **Zhu R., Dann E., et al. (2025).** Genome-scale perturb-seq in primary human CD4+ T cells maps context-specific regulators of T cell programs and human immune traits. *bioRxiv*.（本專案 DE 統計底層資料來源）
2. **AlphaFold Protein Structure Database** — Jumper J. et al. (2021) *Nature* 596:583–589；Varadi M. et al. (2022/2024) *Nucleic Acids Research*（15 個標的的預測結構與 pLDDT 來源）。

