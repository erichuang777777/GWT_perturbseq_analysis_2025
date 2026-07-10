# 科普導覽網站 Explainer site

`index.html` 是一份**給完全不懂本專案的人**的科普導覽單頁網站(繁體中文),從最基本的問題開始,用 12 個步驟帶讀者走完「從一管血到一張藥物標靶優先順序表」的完整流程,每一步都解釋「在做什麼」與「為什麼這樣做」,並在過程中引用外部論文與公開資料庫(PubMed、Open Targets、gnomAD、GTEx、LINCS、CELLxGENE、DepMap 等)幫助理解。

## 特性
- **單一檔案、零相依**:所有 CSS/JS 內嵌,可直接用瀏覽器打開,或放到任何靜態主機。
- **深/淺色主題**:跟隨系統設定,右上角可手動切換。
- **無障礙**:尊重 `prefers-reduced-motion`、鍵盤 focus 樣式、語意標記。
- **內容對應真實檔案**:所有專案內數字(33,983 筆結果、239 個廣泛影響基因、4 位捐贈者/3 種情境等)皆對應 repo 內既有資料;外部連結指向公開來源。

## 本機預覽
```bash
# 直接開檔
xdg-open docs/explainer/index.html   # macOS 用 open,Windows 用 start
# 或起一個簡單伺服器
python -m http.server -d docs/explainer 8080   # 然後開 http://localhost:8080
```

## 內容大綱(12 步)
1. 為什麼從 T 細胞開始 · 2. 核心問題(基因開關 / 藥物標靶) · 3. CRISPRi 把基因調暗 · 4. Perturb-seq 逐細胞讀取 · 5. 真人細胞、全基因體規模 · 6. 差異表現分析 · 7. 兩道可信度把關 · 8. 標靶卡片與就緒度引擎 · 9. 紅旗:強訊號 ≠ 好標靶 · 10. 外部證據資料庫 · 11. 藥物安全的教訓 · 12. 原則與現況 · 附錄:白話詞彙表 + 延伸閱讀。

> 這是導覽/科普層。逐字權威內容見 repo 的 [Wiki](https://github.com/erichuang777777/GWT_perturbseq_analysis_2025/wiki) 與 `docs/`。
