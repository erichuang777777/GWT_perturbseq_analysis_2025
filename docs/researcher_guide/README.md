# 研究人員導覽 Researcher's Guide site

`index.html` 是一份**給科研人員**的導覽單頁網站(繁體中文),與科普網站(`docs/explainer/`)成一對:科普站帶一般讀者理解概念,本站帶研究者**判讀與使用**平台。

## 涵蓋
1. 30 秒定位(決策支援層,consume ≠ recompute)· 2. 資料集與出處 · 3. 怎麼讀一張標靶卡片(evidence grade / kd_status / 穩健性 / 決策+封頂原因)· 4. 就緒度引擎與紅旗覆蓋 · 5. 校準(正/負對照、AUROC、排序穩定度)· 6. 概念層 M01–M20 · 7. API 入口與主要端點 · 8. 圖表判讀路徑 · 9. 限制與如何引用 · 10. **建議閱讀順序**(連向 `server_modules` / `technical_methods` / `figure_guide` / `concept_dictionary` / `data_dictionary`)。

## 特性
- 單一檔案、零相依;深/淺主題;尊重 `prefers-reduced-motion`;可直接開或自行部署。
- 務實/參考取向(表格、端點、判讀卡),與科普站共用同一套視覺語言。
- 所有數字對應 repo 內真實檔案;外部/文件連結供進一步查證。

## 本機預覽
```bash
python -m http.server -d docs/researcher_guide 8080   # 然後開 http://localhost:8080
```

> 這是研究者的**入口/導覽層**;逐字權威內容以連結的 `docs/` 文件與程式為準。
