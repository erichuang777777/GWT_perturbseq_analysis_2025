# A convergent regulatory core across CD4⁺ T-cell polarization × aging × autoimmune risk

**狀態:** CANDIDATE 假說 · 內部穩健、**疾病軸未獨立驗證** · **日期:** 2026-07-23
**可重現:** `python3 src/3_DE_analysis/analysis/convergent_core.py`(deterministic)· 測試 `tests/test_convergent_core.py`

> **一句話**:源論文分別報告了 CD4 T 細胞的極化調控子、老化調控子、與自體免疫 GWAS 富集三件事,**卻從未在基因層級整合**。本再分析發現一個橫跨三軸的收斂核心(~16 基因,以耐受/IL-2-Treg 軸為脊柱),它**通過技術 confound 控制、且對真實疾病特異**;但其疾病軸**無法用 repo 內資料獨立驗證**,故為候選假說,非定案發現。

---

## 1. 源論文在這三項各說了什麼(novelty 邊界)

| 軸 | 論文做的 | 表 |
|---|---|---|
| 極化 | 回歸係數提名 Th2/Th1(Ota 2021)+ activation 調控子,每基因 `coef_rank` × Rest/Stim8/Stim48 | `polarization_..._regulator_coefficients.csv` |
| 老化 | 同法提名 CD4 老化 signature 調控子 | `aging_..._regulator_coefficients.csv` |
| 自體免疫 | 擾動 cluster 的下游基因對 autoimmune GWAS 疾病基因的富集(含負對照疾病) | `cluster_autoimmune_enrichment_results.suppl_table.csv` |

**Gap:三軸是三張獨立的圖,論文未在基因層級交叉。** 本分析補這一步。

## 2. 方法(反假象紀律)

這是在**一次失敗嘗試之後**重建的(前一個「反轉 vs 中心性」主張被證實是 sample-size 假象)。所以:

- **只用論文自己的提名 + 標記 + 負對照**,不用任何 toolkit 內部構件。
- 每個富集都對**covariate-matched permutation null**(以 trans-effect breadth 分箱、箱內置換)檢定,而非只控制集合大小 —— 所以「表現廣/測得準的基因到處都高分」無法製造結果。
- **限制性/負面結果一律呈現**,不藏。

## 3. 結果(真實數字,`convergent_core.py` 可重現)

**① 極化 ∩ 老化 重疊(控制 breadth):**
- thr=0.90:obs=166 vs matched-null 143.5,**p=0.013**
- thr=0.95:obs=57 vs matched-null 39.8,**p=0.0037** ← 越嚴格越強(真訊號特徵)

**② 收斂核心(強極化 ∩ 強老化 ∩ autoimmune-driver)@0.90 = 16 基因:**
```
ASXL1 BATF CBLB CCR2 CISD1 DDX6 DNMT3A EGR2
GATA3 HDAC7 ITGAL MAF MAPK1 MBD2 STAT5A STAT5B
```
- pol∩aging 中 autoimmune-driver 富集:obs=16 vs matched-null 8.8,**p=0.014**
- **機制脊柱**:`EGR2`+`CBLB`(T 細胞耐受/anergy,皆已知自體免疫基因)、`STAT5A/B`(IL-2→Treg)、`GATA3/MAF/BATF`(Th 分化)、表觀遺傳(`DNMT3A/MBD2/HDAC7/ASXL1`)。

**③ 負對照特異性(論文自己的負對照疾病):**
- **16/16** 核心基因出現在真實自體免疫疾病富集;**僅 1/16(ASXL1)**出現在負對照疾病 → 強特異性。
- 多疾病:EGR2 橫跨 13 種、GATA3 8、BATF/DDX6 5、CBLB(Hashimoto's/MS/RA)4。

**④ Held-out activation signature(誠實負面結果):**
- ota vs activation 的 `coef_rank` 幾乎不相關(Spearman=0.011)→ activation 是**獨立軸**,此檢定有意義。
- 核心**不**富集於強 activation 調控子(3/16,p=0.87)。
- **雙面解讀**:(a)✅ 若核心只是「普遍強/好測的基因」(confound),它們在 activation 也該強 —— 但沒有,**這反證了 generic-strength 假象**;(b)⚠️ 核心**專屬**極化+老化+自體免疫三軸,**不能**稱為「通用 master regulator」。

## 4. 誠實的狀態與限制

- **效應溫和**(fold ~1.4–1.85)。這是「證據匯聚成的穩健趨勢」,不是戲劇性重疊。
- **疾病軸無法獨立驗證**:repo 內唯一的疾病來源(Open Targets,`src/6_functional_interaction/autoimmune_analysis/`)**就是論文 Fig 7 的來源**,用它驗證會**循環**。真正獨立的驗證需要 repo 外的 GWAS(不同 curation)。
- **novelty 未對照全文**:僅比對 figure_map 與 suppl tables,尚未確認預印本文字沒提過此三軸收斂。
- 定位:適合一個 **focused analysis / research letter / 大論文中的一張整合圖 + 假說**,不足以單獨撐起高影響論文。

## 5. 可證偽的假說 + 使其可投的下一步

> **CD4 T 細胞存在一個橫跨極化、老化、自體免疫遺傳風險的收斂調控核心,以外周耐受/IL-2-Treg 軸(EGR2、CBLB、STAT5A/B)為脊柱。**

要從「候選」變「發現」需要(按重要性):
1. **獨立疾病驗證**:用 repo 外的自體免疫 GWAS(非 Open Targets curation)測 16 基因是否仍富集。**這是關鍵缺口。**
2. **正式通路富集**(Enrichr/Reactome):確認「耐受/IL-2 軸」脊柱在統計上成立,而非知識性 annotation。
3. **對照預印本全文**確認 novelty。
4. (理想)**濕實驗**:核心基因(如 EGR2/CBLB)敲低是否同時影響極化與耐受表型。

---

*本分析全程可重現、deterministic、且**負面結果與循環風險已明列**。它是一個誠實的種子,不是包裝過的結論。*
