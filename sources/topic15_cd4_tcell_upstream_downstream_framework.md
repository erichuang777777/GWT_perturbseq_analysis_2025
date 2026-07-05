# Topic 15 - CD4 T Cell 上游/下游共表達框架（研究提案版）

## 1) 這題目標

你要做的是把 `perturbation -> target signal -> downstream co-expression program -> 可驗證假設` 串起來，形成可進入藥物開發的 evidence pipeline。

## 2) CD4 上游可控節點（可當 target seed）

- TCR 複合體：`CD3D, CD3E, CD3G, CD247, TRBC1, TRBC2`
- TCR proximal signal：`LCK, FYN, ZAP70, LAT, LCP2, PLCG1, ITK, VAV1, CARD11, BCL10, MALT1`
- 共刺激/共抑制：`CD28, ICOS, CTLA4, PDCD1, TIGIT, LAG3, CD40, CD40LG`
- cytokine receptor：`IL2RA, IL2RB, IL7R, IFNAR1, IFNGR1, JAK1, JAK3, STAT1, STAT3, STAT4, STAT5A, STAT5B`
- 轉錄因子軸：`NFATC1, NFATC2, FOS, JUN, NR4A1, IRF4, BATF, BCL6, PRDM1, TBX21, GATA3, RORC`
- 代謝/命運軸：`MYC, MTOR, HIF1A, TCF7, BACH2, ARID1A, SMARCC1, KDM1A`

## 3) 下游共表達/程式化模組（可直接對應 signature）

- 立即早期活化：`FOS, JUN, FOSB, NR4A1, NR4A2`
- TCR/活化模組：`CD69, CD25(IL2RA), CD40LG, TRAT1, GRAP2`
- Th1：`TBX21, IFNG, CXCR3, STAT4, EOMES`
- Th2：`GATA3, IL4, IL13, IL4R, STAT6`
- Th17：`RORC, IL17A, IL17F, IL23R, CCR6`
- Treg：`FOXP3, IKZF2, CTLA4, IL2RA, TIGIT, LAG3`
- 記憶歸巢：`CCR7, SELL, LTB, S1PR1, IL7R`
- 穿梭/趨化：`CXCR3, CXCR4, CCR5, CCR6, XCL1`
- 細胞毒傾向：`GZMB, PRF1, NKG7, FAS, FASLG, IFNG`
- 耗竭：`PDCD1, HAVCR2, TOX, ENTPD1`

## 4) 可直接用的資源

- GRN/TF：DoRothEA、SCENIC、TRRUST v2、JASPAR、OmniPath、`metadata/Lambert_2018_HumanTF.csv`
- 共表達：MSigDB、GO、Reactome、KEGG、STRING、CORUM、WGCNA、NMF、ICA、COXPRESdb
- 細胞間訊號：CellChat、NicheNet、CellPhoneDB
- 平台：Cellxgene / Census、GEO
- Perturb-seq 工具：scMAGeCK、SCEPTRE、Mixscape、pertpy

## 5) 可直接落地到 GWT 的欄位對應

1. 以 `target` 對 `metadata/sgrna_library_metadata.suppl_table.csv`
2. 篩掉 off-target、低 kd（來自 `guide_kd_efficiency`）
3. 對每個 `target_condition` 取 signature（DE）
4. 對接上游 target seed 與下游 module 做方向一致性檢驗
5. 用 `crossguide_correlation`、`crossdonor_correlation_mean` 校正穩健性

## 6) MVP 假設（可直接跑）

1. `ZAP70`：Rest 與 Stim8 會顯著改變 TCR 模組（CD247/LCP2/LAT/PLCG1）
2. `CD28`：Stim8 可能重塑共刺激與增殖相關基因（IL2RA/CD69/ICOS/MYC）
3. `PTPN2`：刺激條件下影響 cytokine hypersensitivity（JAK-STAT/ISG）
4. `CCR7`：Rest 條件下改變 naive/memory trafficking 模組（CCR7/S1PR1/SELL/IL7R）
5. `IL2RA`：Stim8 下影響 IL-2/FOXP3 相關共表達方向

## 7) 限制與空窗

- in vitro 的 context 與疾病組織有落差（需外部資料對照）
- RNA 不等於蛋白與功能，不能直接下藥物結論
- KD 弱的 target 常假陰性，需要 guide 一致性與效果門檻
- donor 異質性高，必須 donor/guide 覆蓋

## 8) 下一步建議

- 先用 `topic15_cd4_tcell_upstream_downstream_seed_modules.csv` 當 seed，做共表達 module score 的第一輪排序
- 再接 `topic15_limitation_future_work_audit_table.md` 做限制作為 score_cap_reason 對應
- 之後再決定要不要補 `target-to-drug prototype` 的欄位化模板
