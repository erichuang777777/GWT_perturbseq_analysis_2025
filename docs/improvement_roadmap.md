# 改善方向路線圖(deep-research 支撐 + repo 現況核對)

**狀態:** Phase 1–2 已整合 · Phase 3–5 hook 就位、待資料 · **語言:** 繁體中文 · **日期:** 2026-07-08

**進度標記:** Phase 1(遺傳信心分級 + 複合安全負債 + trait-similarity 誠實 stub)與 Phase 2(LINCS 化合物反轉接線)**已實作並合併**——全部描述性、不進決策層、`unknown≠0` 誠實 fallback。Phase 3(SCEPTRE/GSFA/scPerturb)、Phase 4(Pi/GPS)、Phase 5(multiome)**在此 sandbox 卡資料**(需細胞層 OAK 重跑、外部參考集組裝、或新資料生成),接口/契約就位,對應 `docs/sandbox_blocked_tasks.md`——由有資料/網路的環境接續。

這份路線圖把一輪對抗式查證過的 deep-research(9 個高信心方向、0 refuted、28 來源)落成**可執行、對應本 repo 實際模組**的分階段計畫。每項標:資料來源 / 方法 / 對應我們哪個檔案 / 效果 / 成本 / 誠實 caveat。全部維持本專案紀律:never-fabricate、`unknown ≠ 0`、descriptive-vs-decision 分離。

---

## 0. 已查清的前提(open questions 解答)

**OQ1 — 我們的篩選是 low-MOI 還是 high-MOI?→ 確認 low-MOI(一細胞一擾動)。**
證據(repo 自身 pipeline):
- `src/1_preprocess/sgrna_assignment.py`:`assign_sgrna_crispat` 做**唯一 per-cell 指派**(取最高 UMI 的 guide,>1 guide 的細胞標為 multiplet);`assign_sgrna_naive` 明文「先找**單一 sgRNA** 的細胞;多 sgRNA 則指派**主導** guide」。guide calling 用 `crispat` 的 Poisson-Gauss 混合模型(`fit_PGMM`)。
- QC(`qc_final.ipynb`)追蹤 `'targeting single sgRNA'` 群組。
- DE design formula `~ log10_n_cells + target`(`run_DE_chunk.py`)= 每細胞一個 target contrast;median **539 cells/target**。
→ **結論:low-MOI。SCEPTRE low-MOI 與「excess false positives」benchmark 適用我們**(Phase 3 的 ① 不被卡)。

**OQ2 — L2G/eQTL 都沒贏 nearest-gene,那餵 Pi 的 causal-gene 該怎麼指派?**
→ 用**多重指派 + 信心分級**(nearest-gene / Open Targets L2G / eQTL-coloc 並列,各標 tier),不選單一權威。這正好落實 `unknown ≠ 0`。

**OQ3 — L1000 是癌症細胞系,化合物反轉命中如何對原代 CD4 處理?**
→ 沒有現成的原代-CD4 化合物參考集,所以命中一律**顯性標 cell-context mismatch**、維持 hypothesis-only(沿用我們對 LINCS 敲低參考已在做的揭露)。

**OQ4 — 哪種評分法(GPS 線性 vs ML-GPS 梯度提升 vs MR-graded)最適合我們?**
→ 先用**透明的經驗加權(GPS 式線性)**,保留可解釋 + descriptive-vs-decision 分離;ML-GPS(黑箱梯度提升)列後續選項——黑箱會模糊我們的紀律,不適合當第一步。

---

## 1. 分階段計畫(按 leverage-to-effort 排序)

### Phase 1 — 近零成本、強化既有紀律、打在最強成功預測因子(遺傳+安全)【✅ 已整合】

> 實作:`common/evidence_grading.py`(新)、`common/overlay_lookup.py`、`core/readiness.py` 新增描述性欄位 `genetic_support_confidence`/`genetic_support_max_genetic_score`(僅用 genetic score 分級,避免癌症文獻的 overall score 假冒遺傳支持)、`composite_safety_liability`(gnomAD 約束 × GTEx 特異性,liability flag)、`trait_liability_similarity`(無不良反應詞彙 → 誠實 unknown)。實測:MED12 → strong genetics(0.896)+ high 複合負債;VAV1/PLCG1 → 複合 `unknown`(約束已知但不在 GTEx,誠實傳遞)。regression 確認不動 `readiness_call`/`overall_readiness_stage`。

**P1.1(deep-research ⑧)GWAS-to-gene 連結分級**
- 方法:`human_genetic_support` 呈現時,附上 causal-gene 指派**方法 + 信心 tier**;不把 L2G/eQTL 當權威。
- 對應:`core/readiness.py` 的 `_human_genetic*`、`evidence/external_cache.py`(Open Targets genetics)、卡片欄位 + `data_dictionary.md`。
- 依據:2025 benchmark(445 疾病)——L2G OR 3.14 vs nearest-gene 3.08(無統計差異),eQTL coloc 更差。
- 成本:近零。caveat:未同儕審查 preprint,但與共調控文獻一致;當「校準顯示」而非新科學宣稱。

**P1.2(⑤)causal-gene 指派信心當一級卡片欄位**
- 方法:新增描述性欄位記錄「此標的的遺傳支持信心層級」(OMIM/Mendelian > 高信心 L2G > 低信心)。
- 依據:Minikel 2024——遺傳支持機制成功率 **2.6x**,隨 causal-gene 信心提升(OMIM RS=3.7),與效應量/頻率無關。驗證我們現有 UK Biobank rare-LoF 層。
- 成本:低。descriptive-only,不進 `_stage()`。

**P1.3(⑥)複合安全負債訊號 + trait-similarity 匹配**
- 方法:把現有 **gnomAD LOEUF/pLI(=遺傳約束)** + **GTEx breadth(=組織特異性)** 明確合成一個 disclosed safety-liability 視圖,**新增**「標的關聯到與不良反應相似性狀」的匹配特徵。
- 對應:`evidence/safety_overlay.py`、`common/overlay_lookup.py`、disease-drug evidence matching。
- 依據:Duffy 2020(五個聯合遺傳特徵 → 2.6x 副作用風險);Nat Rev Genet 2025(安全性停試標的低組織特異性 + 高約束;關聯相似性狀時不良反應 2x)。
- 成本:低-中(約束/組織特異性已有;trait-similarity 是新增)。⚠️ **反直覺**:遺傳支持預測 **on-target 負債**——是 liability flag,不是 de-risking,措辭必須清楚。

### Phase 2 — 重用既有 machinery、公開資料【✅ 接線已整合(化合物資料未到前誠實 unavailable)】

> 實作:`evidence/lincs_reference_cache.py` 新增 `COMPOUND_SIGNATURES_PATH`/`load_compound_signatures`/`compound_reversal_matches`(重用 `lincs_connectivity_score`,依反轉連結性排序);`signature_explorer.py::match_reference_compounds` 現在 route 到化合物反轉路徑,化合物矩陣未 committed 時維持 `source_status: unavailable`。cell-context mismatch caveat 強制帶。真化合物資料(GSE92742/70138)一落地即亮。

**P2.1(⑦)LINCS L1000 化合物反轉 — 補明說的 compound-reversal 缺口**
- 方法:把 L1000 **化合物** perturbation profile 接進 connectivity explorer,找 signature 反轉命中;**重用 `signature_explorer.connectivity_score` 的加權 cosine**(已支援任意 `{gene:score}` 參考)。
- 資料:LINCS L1000(GSE92742/GSE70138)——注意這是我 blocked-tasks 清單裡 §F 的 compound 半(目前只接了 genetic-perturbation 敲低半)。
- 對應:`signature_explorer.py::match_reference_compounds`(目前誠實 unavailable)、`evidence/lincs_reference_cache.py`。
- caveat:L1000 多在癌症/永生化細胞系(非原代 CD4),命中顯性標 cell-context mismatch。

### Phase 3 — 統計核心升級(最高單項槓桿,較大工程;建議綁 Task A 全量重跑環境一起做)

**P3.1(①)SCEPTRE low-MOI 校準關聯檢定**
- 方法:用 SCEPTRE(R 套件)的 resampling 校準關聯檢定,重算/校準 `statistical_evidence_grade` 的地基;修正標準 DE 的偽陽性/檢定力不足。
- 依據:SCEPTRE Genome Biol 2024(low-MOI「resolves excess false positives, improved calibration and power」)。OQ1 已確認 low-MOI 適用。
- 成本:中-高;需 cell-level / pseudobulk 資料 → 綁 `docs/sandbox_blocked_tasks.md` §A 的 OAK 重跑環境。caveat:method-superiority 多作者自評。

**P3.2(①)GSFA 潛在基因模組因子模型**
- 方法:GSFA 推斷共調控潛在因子、跨模組借力提升 per-gene 檢定力——**其 latent-module 結構直接對應我們的 20 個 concept modules**。
- 依據:GSFA Nat Methods 2023。成本:中。

**P3.3(②)scPerturb E-distance / E-test**
- 方法:每個 knockdown×condition 一個**多變量分布層級效應量** + 校準顯著性(energy distance + permutation E-test),餵 connectivity + benchmark harness。
- 依據:scPerturb Nat Methods 2024(PMID 38279009);另附 44-dataset 標準化語料當 benchmark。
- 成本:中。⚠️ 11,526×3 排列檢定**計算量重**,需批次/近似。

### Phase 4 — 遺傳學網路優先排序(高槓桿,需組裝參考集)

**P4.1(③)Priority index (Pi) 式網路傳播評分**
- 方法:GWAS + 功能基因組(Hi-C/eQTL,依 OQ2 多重指派)+ STRING,random-walk-with-restart → Fisher 合併成 0-5 星 → 縮到 ~30-50 通路交會節點。對應我們 `readiness_call` + mechanism graph;能撈網路中心但無直接 GWAS 訊號的高價值標的(如 TNF)。
- 依據:Fang Nat Genet 2019 / Pi NAR 2022(RA 前 1% 對已核准藥標的 OR=24.4;贏 Open Targets genetics)。
- 成本:高(組裝 GWAS+功能基因組+藥物適應症參考集)。⚠️ benchmark 作者自評。

**P4.2(④)GPS 式經驗加權評分**
- 方法:用「已知藥物適應症」學各證據源最佳權重,取代 ad hoc 加權(先線性 GPS,見 OQ4)。
- 依據:GPS Nat Genet 2023(前 0.19% 標的有藥指徵機率 11x);綜述 Nat Rev Genet 2025。成本:中。

### Phase 5 — Roadmap(需新資料,非純 dashboard)

**P5.1(⑨)Multiome Perturb-seq epigenome 層** — 同時測表現 + 染色質可及性,補「轉錄體以外」缺口;需新資料生成或外部 multiome 資料。依據:Cell Systems 2024。

---

## 2. 建議起手順序

1. **Phase 1 全做(P1.1–P1.3)**：近零-低成本、用已碰資料、強化 `unknown≠0` 紀律、且打在**最強臨床成功預測因子(遺傳支持 + 安全)**。
2. **P2.1**：補我們明說的 compound-reversal 缺口,重用現有 machinery。
3. **Phase 3(統計核心)**：綁 Task A 全量重跑環境一起做(需 cell-level 資料)。
4. **Phase 4(Pi/GPS)**：中期投資,價值高但要組裝外部參考集。
5. **Phase 5**：等有 multiome 資料再說。

---

## 3. 誠實護欄(全域,每階段遵守)

- 多數方法「可採用」但有**非平凡工程量**(E-distance 在我們規模計算重;Pi/GPS 要組裝 GWAS+功能基因組+藥物適應症參考集)。
- 兩個量化宣稱(MR-XGBoost 55% approval、eQTL/L2G-vs-nearest-gene benchmark)來自**單一未同儕審查 preprint**——引用為 modeling/benchmark 結果,非定論。
- method-superiority(GSFA/SCEPTRE/Pi)多為**作者自我 benchmark**,尚未獨立複現。
- 遺傳支持的安全訊號**反直覺**(預測 on-target 負債,非 de-risking)——一律當 liability flag。
- 全部維持 descriptive-vs-decision 分離、`unknown≠0`、never-fabricate;新描述性層不進 `_stage()`/`readiness_call`(除非有明確可辯護的因果理由)。

---

## 4. 引用

| # | 方向 | 來源 |
|---|---|---|
| ① | GSFA 潛在模組 | Nat Methods 2023 — https://www.nature.com/articles/s41592-023-02017-4 |
| ① | SCEPTRE low-MOI | Genome Biol 2024 — https://doi.org/10.1186/s13059-024-03254-2 |
| ② | scPerturb E-distance | Nat Methods 2024, PMID 38279009 — https://pubmed.ncbi.nlm.nih.gov/38279009/ |
| ③ | Priority index (Pi) | Nat Genet 2019 — https://www.nature.com/articles/s41588-019-0456-1 ; NAR 2022 — https://academic.oup.com/nar/article/50/D1/D1358/6423928 |
| ④ | GPS / ML-GPS | Nat Genet 2023 — https://www.nature.com/articles/s41588-023-01609-2 ; Nat Rev Genet 2025 — https://www.nature.com/articles/s41576-025-00904-4 |
| ⑤ | 遺傳支持 2.6x | Minikel Nature 2024 — https://www.nature.com/articles/s41586-024-07316-0 |
| ⑥ | 複合安全負債 | Duffy Sci Adv 2020 — https://www.science.org/doi/10.1126/sciadv.abb6242 ; Nat Rev Genet 2025 — https://www.nature.com/articles/s41576-025-00904-4 |
| ⑦ | LINCS 化合物反轉 | Nat Rev Genet 2025 — https://www.nature.com/articles/s41576-025-00904-4 |
| ⑧ | L2G/eQTL 不贏 nearest-gene | medRxiv 2025 — https://www.medrxiv.org/content/10.1101/2025.09.23.25336370v1.full |
| ⑨ | Multiome Perturb-seq | Cell Systems 2024 — https://www.cell.com/cell-systems/fulltext/S2405-4712(24)00366-1 |
