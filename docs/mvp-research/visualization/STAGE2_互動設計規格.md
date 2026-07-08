# 互動式設計規格 — GWT CD4 Perturb-seq 視覺化模組（階段二）

**用途：** 第二階段（互動）交付物。針對每張圖評估**具體可互動的方式**、**toggle bar 位置**、**可選的資料來源**，並對應到 Streamlit widget 型別，供雲端開發直接實作。

**設計原則：**
1. **hover 是最低成本的互動** — 幾乎每張圖都該有，顯示該資料點的完整證據（基因名、統計值、旗標）。
2. **toggle/篩選要放在不遮擋圖的位置** — 排序類放左側邊欄、多維圖放上方 toggle bar、降維放右側面板。
3. **資料來源選擇** — 每張圖至少允許切換培養條件（Rest/Stim8hr/Stim48hr），這是本資料集最重要的情境維度。
4. **認知負擔控制** — 首頁只放 3 張首選互動圖，其餘收在深入頁，避免一次給太多控制項。

---

## 三張首選互動圖（放 MVP 儀表板首頁）

### [R1] Lollipop 排序
- **互動方式：** hover 顯示基因完整證據；點擊跳轉標的卡
- **toggle bar 位置：** 左側邊欄
- **可選資料來源：** 條件(Rest/Stim8/Stim48)、Top-N 數量、是否隱藏broad-effect
- **Streamlit widget：** `st.selectbox(條件)+st.slider(Top-N)+st.checkbox(隱藏broad)`

### [DOT] 三合一 dot plot
- **互動方式：** hover 顯示三維度數值；點擊選標的
- **toggle bar 位置：** 上方 toggle bar
- **可選資料來源：** 大小編碼欄位、顏色編碼欄位、顯示哪些條件
- **Streamlit widget：** `st.radio(size欄)+st.radio(color欄)+st.multiselect(條件)`

### [V3] UMAP 降維
- **互動方式：** hover 顯示基因名+特徵；框選一群標的匯出
- **toggle bar 位置：** 右側控制面板
- **可選資料來源：** 著色依據(廣度/敲低/broad旗標)、n_neighbors、篩選門檻
- **Streamlit widget：** `st.selectbox(著色)+st.slider(n_neighbors)+st.slider(門檻)`

---

## 次要與補充互動圖（收在深入頁）

| ID | 圖 | 互動方式 | toggle 位置 | 資料來源選擇 | Streamlit widget | 優先級 |
|---|---|---|---|---|---|---|
| M3 | Hexbin 密度 | hover 顯示格內標的數；刷選區域 | 下方 | 條件、gridsize、x/y 軸欄位 | `st.selectbox(條件)+st.slider(gridsize)+st.selectbox×2(軸)` | 🟠 次要 |
| R2 | 上下調分歧bar | hover 顯示上/下調基因清單 | 左側邊欄 | 條件、Top-N | `st.selectbox+st.slider` | 🟠 次要 |
| N1 | STRING 網路 | 拖曳節點；hover 顯示交互作用分數；調整 score 門檻 | 上方 toggle bar | STRING score 門檻、要顯示的標的集合、佈局演算法 | `st.slider(score)+st.multiselect(基因)+st.selectbox(layout)` | 🟠 次要 |
| M1 | 相關性熱圖 | hover 顯示精確相關值 | 無需(靜態即可) | 相關法(Pearson/Spearman)、要納入的特徵 | `st.radio(方法)+st.multiselect(特徵)` | 🟡 補充 |
| N5 | Slope 條件動態 | hover 顯示各條件值；highlight 單一基因 | 左側邊欄 | 要顯示的基因集合、y 軸(廣度/上調/下調) | `st.multiselect(基因)+st.radio(y軸)` | 🟡 補充 |
| D1 | Violin 分佈 | hover 顯示分位數 | 無需 | 條件、y 軸欄位、log/linear | `st.multiselect(條件)+st.selectbox(欄位)+st.radio(尺度)` | 🟡 補充 |
| R4 | Waterfall | hover 顯示基因名+效應 | 無需 | 條件、highlight 特定基因 | `st.selectbox(條件)+st.text_input(highlight)` | 🟡 補充 |

---

## 可執行原型
附帶一份 `STAGE2_interactive_prototype.html` — 用 plotly 產出的**可獨立在瀏覽器開啟**的互動原型，含三張首選圖的互動版本（下拉切換條件、hover 顯示細節、圖例點選過濾）。這是 Streamlit 部署前的概念驗證。
