# Topic 15 - Limitations / Future Work（CD4 T cell 上游-下游共表達主題稽核表）

目的：讓你在每一篇關鍵文獻後，能直接對到你的 GWT 流程中要補的部位。

| paper | PMID / DOI | 限制 (Limitation) | Future Work | 可落地到 GWT 的對策 |
|---|---|---|---|---|
| Zhu & Dann，GWT primary CD4 Perturb-seq | 10.64898/2025.12.23.696273 | 以 in vitro primary CD4 為主；藥物效應與 in vivo 組織 microenvironment 仍有落差；部分 perturbation signal 弱 | 加入更多 donor, longer/earlier time-course, 結合蛋白與功能驗證 | 在 target card 增加 donor/condition/guide 穩定性欄位與批次敏感度 |
| Shifrut et al., pooled CRISPR in primary human T cells | 30449619 | 早期 T-cell perturb-seq 在導向與擴增上仍有技術變異，單 guide 效果受 transduction 影響 | 多 guide + 更細胞層級 assignment QC；建立 guide 效果權重 | 導入 guide_kd_efficiency、off-target flag、multi-guide 過濾 |
| Replogle et al., genome-scale Perturb-seq | 35688146 | 大規模設計下，低效 guide 仍可能造成假陰性 | 加入 guide 效率建模與 target-level 最小有效 cell 限制 | 對接 `n_cells_target` 與 `knockdown_effect` 做雙門檻 |
| Schmidt et al., perturb-seq in T-cell context | 35113687 | 受細胞狀態與活化條件強烈影響，單一條件外推不足 | 在多條件（Rest/Stim8hr/Stim48hr）重複同一 target | 用 `crossdonor`、`cross-guide` 與條件一致性三軸篩掉 context-only signal |
| Arce et al., CD4 perturbation framework | 39663454 | 模型以特定樣本與條件為主，尚未完整對接臨床 endpoint | 以疾病特異資料重訓、加入 longitudinal validation | 對接 success/failure 藥物軸作第二層分層，而非只靠 transcript rank |
| Weinstock et al., scRNA GRN for CD4 context | 39395408 | GRN inferred 結果偏向調控關聯，因果方向仍不保證 | 引入 perturbation evidence 作 triangulation | 將 TF 模組與上游 module 用 perturb signature 同步比對 |
| Ho et al., CRISPR in autoimmune trait context | 40968290 | 遺傳關聯與 perturb signal 對齊仍有限，可能受 linkage / locus granularity 影響 | 以多型位點與 expression causal model 串接 | 在 pipeline 增加「pathway axis」而非單基因一對一判斷 |
| Freimer et al., large perturbation benchmark | 36356142 | high-throughput 策略可能將轉錄訊號過度簡化，缺少功能 readout 平衡 | 需配套 cytokine、功能 assay、蛋白層讀出 | 將 target card 加一層 `technical / biological / translational` 驗證欄位 |
| Zhou et al., in vivo-like CD4 program transfer | 37968405 | in vitro 與疾病組織背景轉移時存在 context shift | 做組織背景轉換測試（例如 external single-cell atlas 對照） | 導入外部 cell atlas 對位（Cellxgene/Census）做穩定性檢核 |
| Ota et al., trait-linked single-cell perturbation | 41372418 | trait mapping 仍是預測層，臨床可行性需再證 | 逐步加入藥物靶向資料與安全性層指標 | 在 target card 加 `clinical_axis` 與 `nearest_failure_or_warning` |
| SCEPTRE 討論（統計校準） | 34930414 / 38760839 | 低 MOI/guide 分佈偏差仍可影響 p-value 校正行為 | 在多方法交叉（SCEPTRE + scMAGeCK）下做敏感度分析 | 將統計結果與跨方法一致性作為可選 score 欄位 |
| MIXscape/Perturb-CITE-seq | 33649593 / 33649592 | RNA-only 模式仍受蛋白轉錄延遲與非對應機制干擾 | 結合 protein / surface marker / cytokine | 將 co-expression 假設輸出為機制假說，保留功能實驗欄位 |

## 可直接行動化的檢核（對應到前面的 target-card）

- 若 `offtarget_flag=True`，不進入 high-confidence tier，即使 DE 強也不列入臨床類比。
- 若 `crossdonor_correlation_mean < 0.2` 或 `crossguide_correlation < 0.2`，降為 warning 牌，不做藥物排序第一層。
- 若 `condition_specificity_score` 高但 `technical_score` 低，標記為「context-dependent, low-confidence」。
- 每個 target 在 `score_cap_reason` 至少掛一個可解釋原因，避免只報高 DE 無法複製。
