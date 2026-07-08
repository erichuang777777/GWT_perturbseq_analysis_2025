# 視覺化模組設計文件 — GWT CD4 Perturb-seq MVP

**用途：** 這是視覺化模組的整合設計文件，串起三個階段的工具。目標是讓使用者一眼看出資料重點、認知負擔最小化。所有設計都建立在文獻慣例（perturb-seq 用 UMAP/火山圖/dotplot；標的優先序用 Open Targets 紅綠燈色系）之上。

**資料來源（統一）：** `DE_stats.suppl_table.csv`（公開 S3：`s3://genome-scale-tcell-perturb-seq/marson2025_data/suppl_tables/`；33,983 列 = 11,526 標的 × 3 條件）。降維與 3D 用 5 個數值特徵聚合到標的層（3,098 個有足夠訊號的標的）。蛋白結構來自 AlphaFold DB（透過 structures-interactions 連結器）。

---

## 三階段架構總覽

| 階段 | 工具型態 | 交付物 | 使用者能做什麼 |
|---|---|---|---|
| **一** | 靜態圖 | `STAGE1_靜態圖表目錄.md` + 5 張圖表庫 PNG | 看 31 張已文件化的圖，每張含資料來源/標題/說明/數據意義/認知負擔評分 |
| **二** | 互動圖 | `STAGE2_互動設計規格.md` + `interactivity_spec.csv` + `STAGE2_interactive_prototype.html` | 調整參數（條件切換、Top-N、門檻）、hover 看細節、圖例過濾 |
| **三** | 3D 模擬 | `STAGE3_3d_rotatable.html` + 5 個 AlphaFold `.cif` | 旋轉 3D 資料散點、旋轉蛋白結構（Mol* 檢視器） |

---

## 階段一：靜態圖（現在的圖）

31 張圖分 6 組，全部文件化。**認知負擔評分（⚪1→🔴5）決定放儀表板哪一層。**

- **首頁（低負擔 ⚪🟢）**：Lollipop 排序（R1）、Box（D2）、Condition heatmap（M6）、Stacked area（N6）
- **深入頁（高負擔 🟠）**：UMAP（V3）、STRING network（N1）、Clustered heatmap（M2）、PCA biplot（V6）

詳見 `STAGE1_靜態圖表目錄.md`。

---

## 階段二：互動圖

**三張首選互動圖（放首頁）：**
1. **三合一 Dot Plot** — 上方 toggle bar 切換 size/color 編碼欄位與條件；hover 顯示三維度數值。
2. **UMAP 降維** — 右側面板選著色依據、n_neighbors、門檻；框選匯出一群標的。
3. **Lollipop 排序** — 左側邊欄選條件、Top-N、隱藏 broad-effect。

**設計原則：** hover 是最低成本互動（每張都該有）；toggle 放不遮圖處；每張至少能切換培養條件；首頁只放 3 張避免控制項過載。

可執行原型 `STAGE2_interactive_prototype.html` 可直接在瀏覽器開，是 Streamlit 部署前的概念驗證。完整 widget 對應見 `interactivity_spec.csv`。

---

## 階段三：3D 模擬

2D 平面圖資訊不足時的補充，兩類：

**1. 3D 資料旋轉**（`STAGE3_3d_rotatable.html`）
- 3D UMAP + 3D PCA，滑鼠可旋轉/縮放/hover。
- broad-effect 基因（紅）與免疫候選（藍）在 3D 空間的分離比 2D 投影更清楚。

**2. 蛋白質 AlphaFold 結構**（Mol* 檢視器可旋轉的 `.cif`）

| 標的 | UniProt | pLDDT | 長度 | 說明 |
|---|---|---|---|---|
| PLCG1 | P19174 | 82.8 | 1290 | 1-phosphatidylinositol 4,5-bisphosphate  |
| VAV1 | P15498 | 86.4 | 845 | Proto-oncogene vav |
| CD3E | P07766 | 73.1 | 207 | T-cell surface glycoprotein CD3 epsilon  |
| CD247 | P20963 | 62.4 | 164 | T-cell surface glycoprotein CD3 zeta cha |
| LAT | O43561 | 59.3 | 262 | Linker for activation of T-cells family  |

pLDDT 是 AlphaFold 的預測信心分數（0–100）：PLCG1/VAV1 高信心（>80，結構可信）；CD3E 中等（73）；LAT/CD247 較低（含大量膜相關無序區，符合預期）。**這些是預測結構，非實驗解析結構**，用於視覺化與可成藥位點探索，不作為原子級精確結論。

---

## 如何接回 MVP 儀表板

1. **靜態圖**：直接嵌入報告或儀表板總覽頁，用認知負擔評分決定放哪一層。
2. **互動圖**：Streamlit 依 `interactivity_spec.csv` 的 widget 規格實作；資料來源選擇統一走培養條件切換。
3. **3D**：資料 3D 用 plotly 內嵌 iframe；蛋白結構用平台的 Mol* 檢視器（`.cif` artifact 直接可旋轉）。

## 誠實護欄

- 降維軸（尤其 t-SNE/UMAP）無絕對意義，簇間距離不可量化解讀——只用於「有沒有分群」。
- AlphaFold 是預測結構，pLDDT 低的區域（LAT/CD247 的無序區）不可作為結構結論。
- 所有圖的 broad-effect 紅色標記對應 C7 隔離旗標，提醒使用者這些高效應標的可能是泛效應污染而非免疫特異訊號。
