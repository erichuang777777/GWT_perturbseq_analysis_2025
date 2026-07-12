# Cell-state embedding
CD4 T 細胞狀態的嵌入表示,供下游狀態/程式分析參考。

- **輸入**:cellranger/前處理輸出(見 `src/1_preprocess/`)
- **notebook**:`ntc_embedding.ipynb`(以非標靶對照 NTC 細胞建立嵌入)
- **下游**:極化訊號(`src/4`)、細胞激素調控子(`src/5`)
