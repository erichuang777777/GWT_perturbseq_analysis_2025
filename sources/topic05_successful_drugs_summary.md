# Topic 5 - 已知成功藥物有哪些

## Executive takeaways

成功案例要分三層看：

1. **Direct-CD4 drugs**: 直接綁 CD4 的成功案例很少。Ibalizumab/Trogarzo 是清楚的 approved CD4-directed antibody，但它的成功機制是 HIV entry blockade，不是調節 CD4 T cell inflammation。
2. **CD4-pathway drugs**: 這是 GWT CD4 Perturb-seq 最適合對照的成功類別，包括 CD3/TCR tolerance、CD28 costimulation、calcineurin/NFAT、JAK/STAT、IL-2/IL-2R、S1P trafficking。
3. **Cytokine-output / tissue-context drugs**: TNF、IL-17、IL-23、integrin blockers 和 checkpoint inhibitors 是重要 clinical success benchmarks，但通常不是 CD4-exclusive，不能直接把藥物成功解讀成「CD4 perturbation target 已驗證」。

因此 target-card 工具需要判斷：這個 GWT signature 比較像 direct T-cell modulation、CD4 pathway modulation、downstream cytokine output、trafficking/homing、還是 oncology T-cell activation。

## Benchmark axes for GWT target cards

| Axis | Representative drugs | Why it matters for GWT | Interpretation |
|---|---|---|---|
| Direct CD4 | ibalizumab | proves CD4 receptor can be drugged | disease-context benchmark, not autoimmune CD4 validation |
| CD3/TCR tolerance | teplizumab | approved T-cell tolerance/disease-interception anchor | positive control plus CRS/lymphopenia warning |
| CD28 costimulation | abatacept, belatacept | clean CD4 activation checkpoint success | positive control for costimulation modules |
| Calcineurin/NFAT | tacrolimus, cyclosporine | strongest TCR-NFAT suppression benchmark | positive control, but narrow therapeutic window |
| IL-2/IL-2R | basiliximab, aldesleukin, denileukin diftitox | same axis can block, agonize, expand, or deplete | directionality warning |
| JAK/STAT | tofacitinib, upadacitinib, baricitinib, ritlecitinib | actionable cytokine-response modules | positive control plus boxed-warning safety gate |
| S1P trafficking | fingolimod, ozanimod, etrasimod | lymphocyte trafficking/egress is druggable | disease-context benchmark; in-vitro CD4 data is incomplete |
| Th17/IL-17 | secukinumab, ixekizumab, brodalumab, bimekizumab | Th17 output is clinically validated | cytokine-output positive control |
| IL-12/23 / IL-23 | ustekinumab, risankizumab, guselkumab | strong psoriasis/PsA/IBD disease anchor | disease-context benchmark |
| TNF | adalimumab, infliximab, etanercept, golimumab, certolizumab | canonical inflammatory comparator | not CD4-specific; requires myeloid/tissue validation |
| Integrin/homing | vedolizumab, natalizumab | tissue-selective trafficking can work | gut-selective success vs broad trafficking PML risk |
| Checkpoint oncology | ipilimumab, pembrolizumab, nivolumab, atezolizumab | T-cell activation can be therapeutic in cancer | directionality differs from autoimmunity |

## What can directly validate GWT signatures

Best positive-control signatures:

- `abatacept/belatacept`: CD28-CD80/86 costimulation, IL2/NFAT/AP-1 downstream activation threshold.
- `teplizumab`: anti-CD3 partial agonism, tolerance/reset, effector/Treg balance.
- `calcineurin inhibitors`: TCR-NFAT/IL2 suppression. If GWT signatures cannot recover this axis, the platform sensitivity is questionable.
- `JAK inhibitors`: IFN, IL-2, IL-6, IL-7/15, IL-23 downstream JAK/STAT response modules.
- `IL-2 axis`: dose- and context-dependent Treg versus effector expansion; STAT5/CD25 feedback.
- `basiliximab`: CD25/IL2RA blockade in activated T cell and Treg contexts.

Benchmarks that need extra caution:

- `ibalizumab`: direct CD4 druggability but HIV-specific.
- `S1P modulators`: clinical effect is trafficking/egress, only partly visible in isolated CD4 transcriptomics.
- `integrin blockers`: require tissue-homing and compartment biology; broad alpha4 blockade can carry PML risk.
- `TNF/IL-17/IL-23 blockers`: strong disease success, but sources can be myeloid, stromal, ILC, keratinocyte, and tissue loops.
- `checkpoint inhibitors`: require tumor antigen, TCR clonality, tumor microenvironment, CD8/myeloid/Treg context.

## Red flags from successful drugs

Target cards should explicitly flag:

- Pan-T-cell suppression: infection, viral reactivation, impaired vaccine response.
- Treg collateral damage: loss of tolerance or autoimmunity when targeting IL2RA, IL2, CTLA4, TNFRSF axes.
- CRS/immune activation: anti-CD3, IL-2, T-cell engager, checkpoint-like signatures.
- Opportunistic viral risk: PML with broad integrin blockade, EBV/PTLD with belatacept, herpes/zoster with JAK/S1P, viral reactivation with anti-CD3.
- Malignancy/lymphoproliferation risk under broad or chronic immunosuppression.
- Cardiovascular/thrombotic risks: JAK inhibitor MACE/VTE warnings; S1P first-dose cardiac effects.
- Organ toxicity: calcineurin nephrotoxicity; JAK CBC/liver/lipid abnormalities; S1P macular edema/liver effects; high-dose IL-2 capillary leak.
- Assay-context gap: isolated in-vitro CD4 Perturb-seq lacks antigen specificity, tissue trafficking, tumor microenvironment, and myeloid/stromal feedback.

## Implication for the toolkit

The benchmark table in `topic05_successful_drug_benchmarks.csv` should become a reference layer for target cards. Each target should ask:

- Which successful drug axis is most similar?
- Is the intended therapeutic direction inhibit, activate, agonize, block, deplete, or reprogram?
- Is the observed GWT effect a precision immune reset or broad immunosuppression?
- Which known drug can be used as a positive-control perturbation?
- Which clinical safety lesson should cap the readiness call?

## Key references

- Ibalizumab phase 3: PMID 30110589; FDA Trogarzo label.
- Teplizumab: PMID 31180194; ClinicalTrials.gov NCT01030861; FDA Tzield label/announcements.
- Abatacept RA: PMID 16785475; Orencia FDA label.
- Belatacept BENEFIT: PMID 20415897; long-term outcomes PMID 26816011; Nulojix label.
- Fingolimod MS: PMID 20089952; ozanimod UC: PMID 34587385.
- Anti-TNF benchmark: infliximab RA PMID 10622295; anti-TNF review PMID 22137924.
- Secukinumab/IL-17 psoriasis: PMID 25007392.
- Ustekinumab/IL-12/23 psoriasis: PMID 18486739.
- Checkpoint blockade: ipilimumab PMID 20525992; pembrolizumab PMID 25891173; nivolumab/ipilimumab PMID 26027431.
- Blinatumomab/T-cell engager benchmark: PMID 28249141.
- JAK inhibitor safety signal: ORAL Surveillance tofacitinib PMID 35081280; FDA boxed warnings/labels.
