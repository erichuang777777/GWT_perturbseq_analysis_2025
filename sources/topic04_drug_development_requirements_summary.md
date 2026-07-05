# Topic 4 - 開發藥物需要的條件

## Executive takeaways

GWT CD4 Perturb-seq 可以支援「drug target hypothesis」與「target card prioritization」，但不能單獨證明一個 target 已經能進入 drug program。最合理的開發定位是：把每個 perturbation target 轉成一張 target card，清楚標記哪些證據來自 GWT，哪些需要外部資料，哪些必須靠 wet-lab 或 clinical validation。

最重要的結論是：不要只輸出 top genes。工具應輸出 target-to-program rationale：疾病關聯、CD4 cell-state effect、可成藥 modality、安全風險、biomarker、下一步 validation。

## Drug-development readiness domains

| Domain | 必要條件 | GWT 可直接支持 | 需要外部資料/實驗 |
|---|---|---|---|
| Biology causality | target perturbation 造成明確、可重現、方向可解釋的 CD4 state/pathway effect | perturbation signature, effect size, pathway/module shift | orthogonal perturbation, rescue, dose-response |
| Disease relevance | effect 對應 disease-relevant CD4 program，而非一般 stress/viability | disease signature reversal/mimicry if signatures exist | patient scRNA, GWAS/eQTL, Open Targets, disease cohorts |
| Directionality | inhibit/activate/degrade/block ligand/reprogramming 要與 biology 和 genetics 對齊 | partial | human genetics direction, tool compound/antibody experiment |
| Tractability | target 有可行 modality | target class hint only | Open Targets tractability, ChEMBL, UniProt, PDB, DrugBank |
| Safety window | 不造成 broad immunosuppression、cytokine release、Treg collapse、autoimmunity | stress/apoptosis/proliferation/cytokine RNA flags | cytokine assay, essentiality, tissue expression, immunotoxicity |
| Biomarker | 有 target engagement 或 PD marker | 3-10 gene RNA PD panel candidates | qPCR, flow, ELISA, protein-level assay |
| Translation | 跨 donor/condition/context 穩定 | if metadata available | primary human validation, patient ex vivo model, in vivo/humanized model |
| Clinical feasibility | 有 indication、patient subgroup、endpoint、trial path | no | clinical landscape, endpoints, competitor/label/trial data |

## Recommended scoring rubric

Use 0-5 scores for seven domains:

| Score | Meaning |
|---|---|
| 0 | no evidence, contradictory evidence, or killer risk |
| 1 | weak computational signal |
| 2 | GWT Perturb-seq signal but little external support |
| 3 | GWT signal plus at least one external evidence class |
| 4 | multiple evidence classes agree and tractability/safety look plausible |
| 5 | human disease evidence plus functional validation plus target engagement/PD biomarker |

Recommended domains:

- `biology_causality_score`
- `disease_relevance_score`
- `tractability_score`
- `safety_window_score`
- `biomarker_score`
- `translation_score`
- `clinical_feasibility_score`

Stage-gated readiness:

| Stage | Meaning | Rule of thumb |
|---|---|---|
| R0 deprioritize | weak or unsafe | biology/disease <2 or killer safety red flag |
| R1 exploratory | interesting GWT signal | GWT signal exists, external evidence incomplete |
| R2 hypothesis-ready | usable therapeutic hypothesis | biology, disease, tractability mostly >=3 |
| R3 validation-ready | ready for focused experiments | R2 plus biomarker or translation score >=3 |
| R4 program-candidate | strong preclinical candidate | most domains >=4 and no killer red flag |
| R5 nomination-ready | near program nomination | functional validation, target engagement, PD marker, initial safety package |

## Decision labels

`advance`: strong GWT effect, clear direction, disease-relevant CD4 state correction, at least one external evidence class, plausible modality, measurable biomarker, and no major CD4 immune red flag.

`validate`: strong GWT signal but missing genetics, tractability, biomarker, or safety evidence. This is the most likely status for many promising targets from the current repo.

`watchlist`: context-specific or moderate signal, unclear indication, unclear modality, or manageable but unresolved immune risk.

`deprioritize`: weak/inconsistent GWT effect, pan-CD4 viability collapse, pan-activation, broad immunosuppression, cytokine-release risk, Treg destabilization, no plausible modality, or human genetics points in the opposite therapeutic direction.

Red-flag overrides:

- `cytokine_release_high = true`: maximum call is `validate`.
- `global_cd4_suppression = true`: maximum call is `watchlist`.
- `autoimmunity_risk_high = true`: maximum call is `validate`.
- `effect_direction_uncertain = true`: maximum call is `validate`.
- `no_modality = true` without RNA/gene/cell-therapy path: `watchlist` or `deprioritize`.

## Minimal validation plan

1. Computational triage: effect size, FDR, CD4 state specificity, stress confounding, disease signature matching, Open Targets/genetics/GTEx/ChEMBL overlay.
2. Orthogonal perturbation: independent sgRNA, CRISPRi/a, siRNA, or tool compound/antibody in 3-5 primary human CD4 donors and 2-3 activation contexts.
3. Functional CD4 assay: Th17/Th1/Tfh cytokines for inflammatory hypotheses; FOXP3/IL2RA/CTLA4 and suppression for Treg hypotheses; viability/proliferation/apoptosis/cytokine release for safety.
4. Biomarker confirmation: compress Perturb-seq signature to a 3-10 gene PD panel and validate by qPCR, flow, ELISA, or intracellular cytokine staining.
5. Translational anchor: confirm target/pathway in patient scRNA or disease ex vivo CD4 cells.

Minimum pass standard: reproduced biology in primary CD4 cells, disease-relevant direction, no strong pan-toxicity/cytokine red flag, one measurable PD biomarker, and plausible modality.

## Key references

- GOT-IT target assessment: PMID 33199880, DOI `10.1038/s41573-020-0087-3`.
- Human genetics for target validation: PMID 23868113, DOI `10.1038/nrd4051`.
- Genetic support and drug success: PMID 26121088, DOI `10.1038/ng.3314`.
- Druggable genome: PMID 28356508, DOI `10.1126/scitranslmed.aag1166`.
- What makes a good drug target: PMID 22155646, DOI `10.1016/j.drudis.2011.09.006`.
- Open Targets Platform: PMID 33196847, https://platform.opentargets.org.
- Open Targets tractability documentation: https://platform-docs.opentargets.org/target/tractability.
- ChEMBL 2023: PMID 37933841, DOI `10.1093/nar/gkad1004`.
- Three pillars of survival in translational pharmacology: PMID 22227532, DOI `10.1016/j.drudis.2011.12.020`.
- In vitro pharmacological profiling for safety: PMID 23197038, DOI `10.1038/nrd3845`.
- Safer immunomodulatory biologics: PMID 23535934, DOI `10.1038/nrd3974`.
- FDA enrichment strategy guidance: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/enrichment-strategies-clinical-trials-support-approval-human-drugs-and-biological-products.
- FDA immunotoxicity guidance: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/nonclinical-evaluation-immunotoxic-potential-pharmaceuticals.
- ICH M3(R2) nonclinical safety studies: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/m3r2-nonclinical-safety-studies-conduct-human-clinical-trials-and-marketing-authorization.
- ICH E8(R1) clinical studies: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/e8r1-general-considerations-clinical-studies.
