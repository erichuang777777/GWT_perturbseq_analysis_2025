# 資料使用與條款 Data Use & Terms(對外 portal)

> 對外 CD4 Target Discovery Portal 的資料使用聲明與條款草稿。前端可渲染本頁(或連結),與 `disclosure.json` / `provenance_registry.csv` 搭配。**上線前請由專案負責人/法務確認各外部來源當前條款。**

## 1. 用途限定 Intended use

本平台輸出為**研究用標靶優先排序**。它**不診斷、不建議治療、不預測療效**,**不得用於病人管理或臨床決策**。體外 CD4 T 細胞情境下的強訊號是研究線索,並非療效或安全性的保證(**CRISPRi ≠ 藥理學**)。

## 2. 授權 Licensing

- **程式碼**:MIT License(Copyright © 2025 Emma Dann;見 repo `LICENSE`)。
- **主資料(GWT CD4 Perturb-seq)**:依原論文與 CZI Virtual Cells Platform 條款(Zhu R., Dann E. et al. 2025,bioRxiv `10.64898/2025.12.23.696273`)。
- **外部聚合資料**:各依其來源授權(見 §4)。本平台呈現的是這些來源的**快照/衍生**,不改變其原始授權。

## 3. 引用 How to cite

使用本平台或其資料於研究時,請引用主資料集:
> Zhu R., Dann E. et al. (2025) Genome-scale perturb-seq in primary human CD4⁺ T cells maps context-specific regulators of T cell programs and human immune traits. *bioRxiv* `10.64898/2025.12.23.696273`.

並視使用到的外部證據,一併引用 §4 對應來源。

## 4. 外部資料 Attribution

本平台整合下列公開資料;呈現時附引用與(適用時)授權。完整清單見 `disclosure.json`(`attribution`)與 `provenance_registry.csv`(`category=data_source`)。

Open Targets(Ochoa 2024, PMID 39657122)· ChEMBL(PMID 37933841, CC BY-SA 3.0)· gnomAD v4(Karczewski 2020, PMID 32461654)· GTEx(PMID 32913098)· Reactome(PMID 34788843, CC BY 4.0)· STRING v12(PMID 36370105, CC BY 4.0)· AlphaFold DB(Jumper 2021, PMID 34265844, CC BY 4.0)· ClinicalTrials.gov(NLM, 公眾領域)· PubMed/PMC(NLM)· CELLxGENE Census(CZI, PMID 39607691)· LINCS/CMap(PMID 29195078)。

> ⚠️ 授權版本以各來源官方當前條款為準;本表為便利對照,非法律意見。

## 5. 隱私 / 無個資 No PII

主資料為公開發表資料集;平台**不處理可識別個資**——捐贈者僅以去識別化人口學欄位存在於 supplementary table(見 `technical_methods.md` §2.4)。

## 6. 無擔保 No warranty

本平台與資料以「現況」(as-is)提供,**不含任何明示或默示擔保**(包括適售性、特定用途適用性)。已知限制(heuristic、descope、覆蓋率、上傳路徑技術債等)見 `disclosure.json`(`limitations`)與 `technical_methods.md` §5。

## 7. 聯絡 Contact

科學/資料問題見主 repo `README.md` 的 Contact 段落,或於 [GitHub Issues](https://github.com/erichuang777777/GWT_perturbseq_analysis_2025/issues) 提出。

---

> 本頁為草稿,供前端揭露與對外溝通使用;正式對外條款請經負責人/法務確認。
