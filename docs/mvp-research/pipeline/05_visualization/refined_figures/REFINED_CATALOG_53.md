# 05_visualization — 精修圖表目錄（53 張，出版級）

**精修日期：** 2026-07-08 · 全部套用 figure-style §1–§9 出版級規則並逐張過 §9 render-then-verify

**底層資料：** DE_stats.suppl_table.csv（MD5 f5cf2e070bc8a2fb2ce0c584b3277c4c，33,983 列 = 11,526 標的 × 3 條件）

**三條件固定配色：** Rest=藍 / Stim 8hr=橙 / Stim 48hr=綠（全 53 張一致，§4.1 顏色綁定）

**參考文獻：** Zhu R., Dann E. et al. (2025) Genome-scale perturb-seq in primary human CD4+ T cells maps context-specific regulators of T cell programs and human immune traits. bioRxiv


關鍵 figure-style 修正原則：claim-title 對每列為真（§1.4，如 R1 標「14 of 15」誠實例外）；excluded/off-target 列以開口標記且不入摘要（§1.1）；log 軸用 k 記號不用填色長條（§3.3）；發散圖以語意零居中（§4.4）；C2 火山圖誠實標註「無 p-value，y 為 DE 基因數」。


## 分佈族（10 張）

| id | 標題 | 呈現內容 | artifact |
|---|---|---|---|
| D1 | Violin 小提琴圖 | 小提琴圖：三條件(Rest/Stim8hr/Stim48hr)的 logDE=log10(n_total_de_genes+1) 分佈，含中位/IQR。offtarget_flag | `19269b88-e5ff-4a18-b401-2894bff5f184` |
| D10 | Q-Q plot 常態檢查 | Q-Q 常態檢查：三條件 ontarget_effect_size(真實顯著敲低,非零) vs 常態分位數，R²≈0.90，尾端脫離顯示左偏重尾非常態。 | `7e46927a-0384-4461-b917-2b755b2af181` |
| D2 | Box 箱型圖 | 箱型圖：同 logDE 三條件並排，中位皆 2 個 DE 基因；離群點以淡灰散點表示。 | `f61466cc-b627-462c-9831-30f8ff8183e0` |
| D3 | Ridgeline 堆疊密度 | 堆疊密度(ridgeline)：三條件 logDE 密度曲線 + 中位線，形狀高度重疊。 | `8d897acd-1260-410f-b3fd-1346dd3905fb` |
| D4 | Histogram 直方圖 | 直方圖(step)：三條件 logDE 計數分佈，強烈右偏且三線幾乎完全重合。 | `3a3f07ec-18d5-4e79-9468-87dd7e95db16` |
| D5 | ECDF 累積分佈 | ECDF 累積分佈：三條件 logDE，標註 76.7%(所繪 offtarget-排除集)標的下游 DE≤8 基因(即 logDE<1)的位置。 | `18ccf225-c93b-4f73-804c-56f184433039` |
| D6 | Strip 抖動散點 | 抖動散點(strip)：15 個 shortlist 基因的 ontarget_effect_size 依三條件分組 + 中位橫線；n=14/13/15。 | `37131339-e868-423e-b66b-3dfe8a29e964` |
| D7 | Swarm 蜂群圖 | 蜂群圖(swarm)：同 shortlist 效應量非重疊佈局 + 中位橫線，密度反映敲低強度分佈。 | `173f4f7a-5273-4f2e-81d6-f0145d7ef13b` |
| D8 | Raincloud 雨雲圖 | 雨雲圖：三條件 logDE 的半小提琴(雲)+箱(5–95%鬚)+抖動點(雨)三層合一。 | `d224a787-4aeb-48c3-b25f-a250fc681118` |
| D9 | 1D KDE 密度曲線 | 1D KDE 密度曲線疊圖：三條件 logDE 平滑密度，三線重合；最常見值為 1 個下游 DE 基因(n_total_de_genes=1，count=7,316，為單一眾數)， | `2665941c-ad70-4b53-9eac-c8df222c9d82` |

## 矩陣族（10 張）

| id | 標題 | 呈現內容 | artifact |
|---|---|---|---|
| M1 | 相關性熱圖 | Pearson correlation heatmap of 6 numeric features (cells, genes up/down, total DE, on-targ | `83641d05-e1bd-459a-b083-44b64f349424` |
| M10 | Gene×condition DE 熱圖 | Gene x condition n_DE heatmap for the 15 shortlist genes (magma, log scale) with row dendr | `b40d9294-52b5-4710-81c5-6950191913b0` |
| M2 | 階層聚類熱圖 | Same correlation matrix reordered by hierarchical clustering (1-/r/, average linkage) with | `cf645e23-b6db-40bd-b81a-84029f5e7751` |
| M3 | Hexbin 六角密度 | Hexbin density of cells assayed (x, log) vs total DE genes+1 (y, log), LogNorm colourbar;  | `5f540aee-2e7b-4712-8d8b-37cf4d1a8bfb` |
| M4 | 2D density 密度散點 | 2D density scatter (points coloured by local 2D-histogram density, LogNorm) of on-target e | `23035b79-eb5c-4707-9d2b-581428425047` |
| M5 | Scatter matrix 散點矩陣 | 4x4 scatter matrix (hexbin off-diagonal, histograms on diagonal) of cells/effect/DE genes/ | `4712945d-edaa-4e21-9afe-31a2286951f9` |
| M6 | 條件×指標熱圖 | Condition x metric heatmap (7 metrics x Rest/Stim8hr/Stim48hr), row z-score colour with ra | `57843977-5cae-44f3-bd16-125e11194fb9` |
| M7 | Joint scatter 邊際散點 | Joint hexbin (all rows, greys) + gate-passing overlay (2,131 rows, red) of cells vs DE gen | `3761f44a-31ce-4d93-b5bb-bd02fd800ac9` |
| M8 | Dendrogram 聚類樹 | Standalone Ward dendrogram clustering the 15 shortlist genes by their 3-condition effect-s | `f5b11d6d-ebc1-47d7-98fa-a7acbf6e9f49` |
| M9 | Contour 等高線 | Filled 2D-KDE contour of on-target effect size vs total DE genes (log) over the populated  | `854699e6-999d-4ff4-a170-9a1fa06cb57a` |

## 排序族（10 張）

| id | 標題 | 呈現內容 | artifact |
|---|---|---|---|
| R1 | Lollipop 排序 | Dumbbell/lollipop of 15 shortlist genes ranked by max downstream-DE breadth (de_matrix Res | `cb340056-2f57-4399-a6f9-bcda65770065` |
| R10 | Dot-plot matrix (scanpy式) | Scanpy-style dot-plot matrix: 15 genes × 3 conditions, dot size = breadth (de_matrix), dot | `53b27092-085e-49a6-919a-5a147046496a` |
| R2 | Diverging bar 分歧長條 | 0-centered diverging bar: downstream genes down-regulated (left) vs up-regulated (right) p | `642b5eb3-1e64-466c-8f91-a835b9bd8f20` |
| R3 | Stacked bar 組成長條 | 100% stacked bar of response-size composition (n_total_genes_category: no effect/1/2-10/>1 | `0085c032-6c45-4425-81f0-1eaa994db5ed` |
| R4 | Waterfall 瀑布圖 | Waterfall of all 6,290 Stim8hr on-target-significant knockdowns ranked by signed on-target | `5a5120ee-3271-49dd-81df-5742c38aa093` |
| R5 | Bubble 泡泡圖 | Bubble: breadth (log x) vs on-target effect (y), bubble size = n_cells_target, color = con | `1bb4dae4-e464-431d-bbc9-ee1c864279c6` |
| R6 | Grouped bar 分組長條 | Grouped bar: downstream-DE breadth by condition for top-6 targets (de_matrix), 3 bars/gene | `12fcbe86-c89c-43c5-beb7-3a88c21e3381` |
| R7 | Bar with error bars 誤差棒長條 | Bar + 95% CI (t-dist) of mean on-target effect per condition (included KDs; n printed). Si | `b640a7f5-5f88-4b72-a72d-713797a7890f` |
| R8 | Point plot 點趨勢 | Point/slope trend of breadth across 3 conditions for 15 shortlist genes (thin raw lines) + | `1ee05fb9-2c1b-4558-bcf7-42da2ca05864` |
| R9 | MA plot | MA plot: target baseline expression (log x) vs on-target effect, Stim8hr; not-significant  | `fbceab01-445f-461d-af46-ab60179e9dfe` |

## 降維與複合族（9 張）

| id | 標題 | 呈現內容 | artifact |
|---|---|---|---|
| C1 | 3D dot plot 三合一 | Static 3-in-1 dot plot: 15 genes (rows) × 3 conditions (cols); dot color = signed effect ( | `58d1ca82-18a0-4fcf-9695-56ab3ab6f57e` |
| C2 | Volcano 火山圖 | Pseudo-volcano (title states no p-value): effect size vs log10 DE-gene count, colored by c | `b600c45e-fcea-48c9-af1e-dc95cae575e9` |
| C3 | QC funnel 篩選漏斗 | QC funnel centered bars: 33,983 → ≥200 cells 30,515 → significant 19,297 → no off-target 1 | `351c5b08-ea9b-4dbd-a695-bdc94fd3316b` |
| V1 | PCA 主成分 | PCA(PC1 55%, PC2 33%) of 11,086 targets on standardized 3-condition effect + log1p(nDE) fe | `4e4d9665-a50b-442b-ae2b-82af6dad4220` |
| V2 | t-SNE | t-SNE of the same target×condition feature matrix; grey other / viridis gate-passing / rin | `a48cc5c7-7afe-47d0-8236-a50d8172d804` |
| V3 | UMAP | UMAP of the same feature matrix; grey other / viridis gate-passing / ringed shortlist — cu | `c6722321-6266-4302-a80a-0c377d10bd90` |
| V4 | Radar 雷達圖 | Radar over the 15 shortlist genes (spokes) with three condition polygons = on-target /effe | `d7109547-2a88-43b9-9056-ab97b69f5bde` |
| V5 | Circular bar 環形長條 | Circular grouped bar: 15 shortlist genes ranked by 3-condition mean /effect/, three bars/g | `93338205-e03d-4367-bb14-6aca66cba045` |
| V6 | PCA biplot 載荷雙標圖 | PCA biplot: PC1/PC2 scores + loading arrows for 6 features (3 effect condition-colored, 3  | `2e206c36-f172-4feb-bb2a-2309ec7c641c` |

## 網路族（7 張）

| id | 標題 | 呈現內容 | artifact |
|---|---|---|---|
| N1 | STRING 網路 | shortlist 基因的已知蛋白交互網路（STRING/文獻）；三模組圓形叢集佈局。節點色=功能模組(TCR近端訊號/SAGA/Mediator)，節點大小∝/平均在標效應量/( | `b8161148-d035-474c-b474-94e2187858e1` |
| N2 | Chord 環形網路 | 同一 16 節點網路的環形(chord)呈現；節點依模組排在圓環上，弧線=已知PPI，色隨模組。凸顯三模組各自內部緊密、彼此無已知直接交互。節點大小∝/平均在標效應量/。 | `e466dc9c-48ba-4983-b176-e30a724fc5aa` |
| N3 | Venn 文氏圖 | 基因層三集合文氏圖：顯著命中(7,913)、通過門檻(1,235)、有脫靶(1,152)。由 raw 的 ontarget_significant/offtarget_flag 與 | `00efbf9a-0a2a-4c6b-adea-697dcb0ac8f6` |
| N4 | Manhattan 曼哈頓式 | 曼哈頓式散點：x=標的基因(字母序)，y=下游DE基因數(log, n_total_de_genes)，色=三條件。排除脫靶列。標註15個shortlist中DE>1000者，凸顯 | `d39bb657-21ef-47a6-9e3c-a0b0c9762768` |
| N5 | Slope 斜率圖 | 斜率圖：15個shortlist基因在 Rest→Stim8hr→Stim48hr 的在標效應量(effect_matrix)變化。色=刺激後減弱(12/15)/增強(3/15)； | `a366c12e-f940-4e0d-a5f8-2c1602df2f39` |
| N6 | Stacked area 堆疊面積 | 堆疊面積：三條件(時序)下受影響標的依 DE 基因數分層(1–9/10–49/50–199/200–999/≥1000)之組成。由 de_matrix 計算,僅計有≥1個DE基因的 | `74ee2278-807c-46d4-b87c-95bd3759a5db` |
| N7 | UpSet plot 集合交集 | UpSet 集合交集(matplotlib自繪)：4集合 顯著(7,913)/通過門檻(1,235)/脫靶(1,152)/廣效(10)。上方=交集大小長條，左方=集合總量，點矩陣= | `ea70325e-4fa5-4a9d-b614-93e0d682eaba` |

## 階層互動族（7 張）

| id | 標題 | 呈現內容 | artifact |
|---|---|---|---|
| H1 | Treemap 矩形樹圖 | 矩形樹圖。欄=culture_condition，內層=ontarget_effect_category，面積∝DE統計列數(全圖n=33,983)。on-target敲低約62% | `b4785f9d-b770-4dde-bb01-d197200b628e` |
| H2 | Sunburst 放射階層 | 放射階層(sunburst)。內環=培養條件、外環=on-target效應類別，扇角∝列數。三條件效應類別組成幾乎相同。 | `32ae2852-73c9-4da2-83ad-44bb1237ef7c` |
| H3 | Icicle 冰柱階層 | 冰柱階層。三層由左至右：全部→culture_condition→ontarget_effect_category，矩形高∝列數。逐層拆分 33,983 列。 | `897be4fb-c9f6-4d5d-b241-3a5051fd49c9` |
| H4 | Sankey 流向圖 | 流向圖(手繪流帶)。四道門檻篩選級聯：全部→細胞數≥200→顯著on-target→無off-target→DE基因≥50。藍帶保留、灰帶淘汰，33,983→2,131。 | `5de11133-6ebe-4dab-b6be-ed383c7bdd1d` |
| H5 | Funnel 互動漏斗 | 互動漏斗靜態版。同一四關篩選，居中漏斗顯示各關列數、佔全體%與逐關保留率；DE基因≥50為最嚴一關(保留約13%)。 | `1adc47b8-aec4-43fe-a04e-6a6dcd4ef11a` |
| H6 | Parallel coordinates 平行座標 | 平行座標。三個無缺失非冗餘數值特徵(n_cells_target, /ontarget_effect_size/, n_total_de_genes)百分位化；細線抽樣、粗線=三條 | `ed4d5614-96a3-4b5c-86ed-05560a055609` |
| H7 | Parallel categories 類別平行 | 類別平行(alluvial)。四維:culture_condition→ontarget_effect_category→n_total_genes_category→passes | `9f9bc438-bfca-4ba0-b3a6-89fbb64413e2` |