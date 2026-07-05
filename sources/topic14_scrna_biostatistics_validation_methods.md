# Topic 14 - scRNA 生物統計與生物資訊統計：CD4 GWT 角度（已含統計與 validation）

## 1) 結論先行

GWT Perturb-seq 的統計核心不是「先找很多 DE 基因」，而是把每個 `target × condition` 當作一個可重複驗證的實驗單位，先做 replicate-aware 證據排位，再回到細胞層做模型化。  

因此資料流建議是：

- 有 `DE_stats` CSV 時先做 evidence dashboard。
- 有 `h5ad` 時再做更高階的 cell-level model + batch + 驗證層。

## 2) scRNA 典型分析模組（對應 GWT 場景）

- 2.1 前置品質控制
  - Cell QC：UMI、基因數、線粒體比例、雙細胞 (doublet)。
  - Perturbation QC：guide assignment、non-targeting 控制、guide 稀有度、multi-guide 過濾。
  - KD QC：guide\_kd\_efficiency、`ontarget_flag`、`offtarget_flag`。
- 2.2 Normalization 與 feature selection
  - size factor / scran pooling、sctransform，搭配高變異基因挑選。
  - 建議先在原始計數空間做建模，再用正規化值視覺化；避免在已回歸掉的空間直接做 DEG。
- 2.3 降維與群聚/註解
  - PCA/UMAP/Leiden，做條件對齊與 donor 影響檢查。
  - 以已知 marker（CD3D/E, IL7R, CCR7, LTB 等）標註 major state。
- 2.4 Differential expression（DE）
  - CSV-first：`n_total_de_genes`, `n_up_de_genes`, `n_down_de_genes`, `adj_pval`, `logFC` 做一致性排序。
  - h5ad-first：建議 pseudobulk + donor/guide 層級模型（GLM/混合效應）作主證據，避免 pseudoreplication。
- 2.5 批次效應與整合
  - 先做無整合比較（未回歸）做 QC，後用 Harmony/scVI/Scanorama/Seurat integration 作敏感度分析。
  - 重點不是求「最漂亮」UMAP，而是看結果對 batch 敏感程度是否改變。
- 2.6 differential abundance / composition
  - 用 scCODA / Milo 等測試條件間細胞狀態比例改變。
- 2.7 Perturbation 特化統計
  - 同 target 多 guide 的一致性（cross-guide correlation）
  - donor 間一致性（cross-donor correlation）
  - guide 效果方向是否與生物邏輯一致（knockdown 是 down/up 的預期方向）
- 2.8 共表達與路徑推斷
  - 規則：SCENIC、DoRothEA/PROGENy、pathway module（MSigDB/Reactome/GO）
  - 驗證訊號軸：TCR/NFAT/NF-κB/JAK-STAT、Th1/Th2/Th17/Treg、trafficking
- 2.9 時間軸與動態
  - trajectory / pseudotime / RNA velocity（Monocle、Slingshot、scVelo）作為補充，不建議作為核心目標排位主證據。
- 2.10 power / sample size / 可偵測性
  - 用 powsimR/scPower 做最少 donor、guide、細胞數下界估計，防止「細胞數多但 replicate 少」造成誤判。

## 3) CSV-first 與 h5ad 升級版的實作差別

- CSV-first（可立即啟動）
  - `target-condition card`：每個 target 的 effect 大小、FDR、重現度、off-target、條件敏感度。
  - 全域 dashboard：QC gate、交叉 donor/guide、條件特異性、已知藥物軸對照。
- h5ad 升級（建議下一步）
  - pseudobulk + 負二項/GLM 混合模型
  - donor/sample/guide 分層
  - perturbation embedding
  - pathway validation on cell-level
  - 以 technical/生物/轉譯三層驗證。

## 4) Validation 展示建議（建模到報表）

- Technical: control guide null 分布、guide 一致性、off-target flag、n cells threshold、batch sensitivity flag。
- Biological: 正向對照基因是否回收（CD3E, ZAP70, LCK, IL7R, CTLA4, FOXP3 等）。
- Translational: 對照已知失敗/成功藥物軸（例如 teplizumab、abatacept、secukinumab、tofacitinib、TGN1412、daclizumab）。
- 圖表示例：
  - cross-guide vs cross-donor scatter
  - condition specificity heatmap
  - success axis / warning axis 雷達
  - target card 的 top evidence 路徑追蹤圖（from raw DE → reproducible signal → pathway → clinical analog）。

## 5) 常見陷阱（避免過度推論）

- 把每個 cell 當獨立 replicate，未做 donor/guide 分層。
- 只靠 DE 基因數量，不看效應方向與穩定度。
- 忽略 batch/condition confounding，尤其刺激條件與 donor 交互。
- 以單篇文獻/單一條件類比臨床成功。
- 將 RNA 層結果直接視為蛋白與功能層結果。
- 把低 kd 的「無訊號」誤判為真陰性；未檢查 escape / non-responder。

## 6) 可直接落地的 target-card 欄位建議

- `target`, `condition`, `n_cells_target`, `n_guides`, `n_donors`
- `ontarget_significant`, `offtarget_flag`, `n_total_de_genes`, `n_up_de_genes`, `n_down_de_genes`
- `median_logFC`, `max_abs_logFC`, `fdr_min`
- `crossguide_correlation`, `crossdonor_correlation_mean`
- `replicate_pass_flag`, `batch_sensitivity_flag`
- `pathway_axis`, `condition_specificity_score`, `clinical_axis`
- `statistical_evidence_grade`, `score_cap_reason`

## 7) 參考方法文獻（PMID/DOI）

- 31217225 Current best practices in scRNA-seq: 10.15252/msb.20188746
- 27122128 Pooling normalization: 10.1186/s13059-016-0947-7
- 31870423 sctransform: 10.1186/s13059-019-1874-1
- 30504886 scVI: 10.1038/s41592-018-0229-2
- 31740819 Harmony: 10.1038/s41592-019-0619-0
- 31178118 Seurat integration: 10.1016/j.cell.2019.05.031
- 34949812 Integration benchmarking: 10.1038/s41592-021-01336-8
- 29481549 DE bias: 10.1038/nmeth.4612
- 34584091 scRNA DE false discoveries: 10.1038/s41467-021-25960-2
- 33257685 muscat: 10.1038/s41467-020-19894-4
- 31980032 scMAGeCK: 10.1186/s13059-020-1928-4
- 34930414 SCEPTRE: 10.1186/s13059-021-02545-2
- 38760839 low-MOI SCEPTRE: 10.1186/s13059-024-03254-2
- 33649593 Mixscape/perturb checkpoints: 10.1038/s41588-021-00778-2
- 33649592 Perturb-CITE-seq: 10.1038/s41588-021-00779-1
- 41476114 pertpy: 10.1038/s41592-025-02909-7
- 34824236 scCODA: 10.1038/s41467-021-27150-6
- 34594043 Milo: 10.1038/s41587-021-01033-z
- 28991892 SCENIC: 10.1038/nmeth.4463
- 34285779 UCell: 10.1016/j.csbj.2021.06.043
- 29295995 PROGENy: 10.1038/s41467-017-02391-6
- 32747759 scVelo: 10.1038/s41587-020-0591-3
- 24658644 Monocle: 10.1038/nbt.2859
- 29914354 Slingshot: 10.1186/s12864-018-4772-0
- 33597522 CellChat: 10.1038/s41467-021-21246-9
- 31819264 NicheNet: 10.1038/s41592-019-0667-5
- 34785648 scPower: 10.1038/s41467-021-26779-7
- 29036287 powsimR: 10.1093/bioinformatics/btx435

備註：`36156203` 在先前結果為題目誤配，非 decoupleR 核心參考文獻，不建議使用。

## 8) 本次 15 主題協作紀錄

- 先前 search 代理曾因使用額度限制超時；我改採本地已蒐集文獻與資料池補齊。
- Topic14 已有 synthesis 代理輸出，現已整理成可落地文件。
