# Indication Dossier: Rheumatoid Arthritis

**Definition**: A chronic, systemic autoimmune disease characterized by symmetric inflammatory polyarthritis of the small joints, driven by synovial pannus that erodes cartilage and bone and frequently accompanied by RF/ACPA autoantibodies and extra-articular manifestations.
**ICD-10**: M05 (RA with rheumatoid factor), M06 (other RA, incl. M06.9 unspecified), M08 (juvenile)
**Parent Indication**: Inflammatory arthritis / systemic autoimmune rheumatic disease

> **Platform link.** Among the perturb-seq platform's top signed-DE targets, RA is the strongest *druggable* immune connection: RA maps to **TYK2** (Open Targets genetic-association 0.93), a JAK-family kinase in the same JAK–STAT axis that JAK inhibitors already drug in RA. This dossier characterizes the RA patient population and the regulatory precedent a TYK2/JAK-axis asset would enter.

---

## 1. Population Definition & Epidemiology

### 1.1 Diagnostic Criteria
RA patients are identified by the **2010 ACR/EULAR classification criteria**, which score four domains — joint involvement, serology (RF/ACPA), acute-phase reactants (CRP/ESR), and symptom duration ≥6 weeks — with a score ≥6/10 in a patient with at least one clinically swollen joint (not better explained by another disease) classifying as definite RA. These criteria replaced the 1987 ACR criteria to catch patients earlier, when the joints are still savable. Serology splits the population: seropositive RA (RF and/or ACPA, ICD-10 M05) versus seronegative RA (M06), the latter being harder to diagnose but still erosive.

### 1.2 Prevalence & Incidence
Classic population studies put RA at **0.5–1.0% of adults in developed countries**, with incidence of **5–50 per 100,000 adults per year**, rising with age [8]. Contemporary Global Burden of Disease analyses refine this for the working-age population: the global age-standardized prevalence rate among 15–49-year-olds reached **153.73 per 100,000 in 2021**, up 29% from 1990, with prevalent cases in this age band rising **87.7% (3.23M → 6.07M)** over three decades [1]. A separate GBD illness-death model projects the global ASPR will climb a further **6.3% to ~222 per 100,000 by 2040** [2]. In the United States, the most recent NHANES-based subtype analysis (2017–March 2020) found RA accounts for **15.8% of all diagnosed arthritis = 10.6 million adults** — the second most common arthritis type after osteoarthritis [4]. (A narrower case definition circulates as ~1.3 million; the discrepancy is a case-ascertainment artifact, noted as a gap.)

### 1.3 Demographics & Risk Factors
RA is strongly **female-predominant**: women carry ~**2.8-fold** the age-standardized prevalence of men (228.3 vs 81.0 per 100,000 in the 15–49y GBD analysis), and roughly three-quarters of US RA patients are women [1]. Prevalence rises with age (peak onset in the 50s–60s). There are steep socioeconomic and geographic gradients — high-SDI countries show **triple** the prevalence of low-SDI countries (209 vs 65 per 100,000), and Andean Latin America records the highest regional rate (420.7 per 100,000) [1]. **Smoking** is the leading modifiable risk factor, accounting for **6.5% of RA DALYs in 2021** (down from 8.8%), and is most strongly linked to ACPA-positive disease [1].

### 1.4 Natural History
Untreated RA is chronic and progressive: persistent synovitis erodes cartilage and bone, producing deformity and disability. An early **"window of opportunity"** in the first months is when DMARD therapy most alters the trajectory. Treatment advances have bent the mortality curve — age-standardized RA mortality in the Asia-Pacific GBD analysis fell **43% (0.75 → 0.43 per 100,000, 1990–2023)** [3]. Excess mortality is now driven largely by extra-articular disease: **RA-associated interstitial lung disease (RA-ILD)** has a **20-year cumulative incidence of 15.3%**, with ever-smoking (HR 1.92), older onset age (HR 1.89/decade), and severe extra-articular manifestations (HR 2.29) as the dominant risk factors [5].

---

## 2. Disease Biology

### 2.1 Pathophysiology
RA begins with a breach of immune tolerance to citrullinated self-proteins, generating ACPA and RF immune complexes that seed synovial inflammation. The inflamed synovium becomes an invasive **pannus** of activated fibroblast-like synoviocytes, macrophages, T cells (including Th17), B cells, and osteoclasts. A small set of effector cytokines — **TNF-α, IL-6, IL-1, GM-CSF** — sustains the process, while RANKL-driven osteoclastogenesis and matrix metalloproteinases drive the bone and cartilage erosion that defines the disease [6]. Critically, the receptors for many of these cytokines converge intracellularly on the **JAK–STAT** pathway — which is why broad JAK inhibition works across the disease, and why the platform's top signed target **TYK2** (a JAK-family kinase) sits squarely on the validated mechanistic axis.

### 2.2 Biomarkers
The serological cornerstones are **RF and ACPA (anti-CCP)**, which define seropositive disease and remain the diagnostic anchors; **CRP and ESR** grade inflammatory activity [6]. Prognostically, RF-positivity (more than ACPA) marks patients "particularly prone to high disease activity and joint destruction," and there are early **predictive** signals: high CRP "may predict a particularly good response to IL-6 blockade, but not to other therapies," and high RF may track with better response to Fc-free monoclonals [7]. Newer multi-analyte panels (cytokines, microRNAs, MMPs, proteomic/glycosylation markers) "can significantly outperform traditional serological tests" for early and seronegative RA but are not yet FDA-qualified [9]. Disease activity in trials and treat-to-target practice is measured with composite indices — **DAS28, CDAI, SDAI**.

---

## 3. Standard of Care

### 3.1 Approved Therapies
RA therapy is tiered across three DMARD classes (mechanism and FDA anchor verified via Drugs@FDA):

| Class | Drug (example) | Mechanism (EPC) | FDA anchor |
|---|---|---|---|
| csDMARD | Methotrexate | Folate Analog Metabolic Inhibitor | app. 1959 |
| bDMARD (TNF) | Etanercept / Infliximab / Adalimumab | TNF Blocker | 1998 / 1998 / 2002 |
| bDMARD (IL-6R) | Tocilizumab | Interleukin-6 Receptor Antagonist | 2010 |
| bDMARD (costim) | Abatacept | Selective T-Cell Costimulation Modulator | 2005 |
| bDMARD (B-cell) | Rituximab | CD20-directed Cytolytic Antibody | RA ind. 2006 |
| tsDMARD (JAK) | Tofacitinib / Baricitinib / Upadacitinib | Janus Kinase Inhibitor | 2012 / 2018 / 2019 |

No drug cures RA; a substantial fraction of patients never reach remission on any single agent, and the entire JAK class carries a boxed warning (see §5.2) [10, 11].

### 3.2 Treatment Guidelines
EULAR (2022/2023 update) and ACR guidelines converge on a **treat-to-target** algorithm: begin methotrexate plus short-term glucocorticoids at diagnosis; target sustained remission or low disease activity by a composite index; if the target is missed and poor-prognosis factors are present (high activity, RF/ACPA positivity, early erosions), escalate to a bDMARD or JAK inhibitor, usually on background methotrexate; taper (biologic first) on sustained remission. The systematic review informing the 2022 EULAR update screened 8,969 records to establish comparative DMARD efficacy [10].

### 3.3 Unmet Need
Despite a deep armamentarium, five gaps persist: (1) **difficult-to-treat RA** — patients who cycle through multiple bDMARD/tsDMARD mechanisms without remission; (2) **no predictive biomarker** reliably matches drug to patient, so therapy is largely trial-and-error — "newer studies … have either not shown better results than those seen with the long-established ones or have not been sufficiently validated" [7]; (3) **seronegative and early RA** are under-served by RF/ACPA-based diagnosis, delaying window-of-opportunity treatment; (4) **JAK safety signals** constrain use in older/cardiovascular-risk patients; (5) **disease modification / drug-free cure** remains unachieved. The predictive-mechanism-selection gap is exactly where a directionality-aware target-discovery platform (signed-DE ranking over the JAK–STAT/TYK2 axis) is positioned to contribute.

---

## 4. Clinical Endpoints & Regulatory Path

### 4.1 Accepted Endpoints
RA registration endpoints are well-standardized (confirmed from active CT.gov trial records):

| Endpoint | What it measures | Role |
|---|---|---|
| **ACR20 / 50 / 70** | ≥20/50/70% improvement in tender+swollen joint counts plus 3/5 ACR core measures | Primary signs-and-symptoms efficacy |
| **modified Total Sharp Score (mTSS)** | Radiographic joint-damage progression | Structural-damage (disease-modification) claim |
| **DAS28 / CDAI / SDAI** | Composite disease activity | Remission / low-disease-activity targets |
| **HAQ-DI** | Physical function | Function claim |

Regulators expect a symptomatic endpoint (ACR/DAS28) and, for a structural claim, radiographic progression (mTSS) [confirmed via NCT02706951 outcomes].

### 4.2 Regulatory Precedents
FDA maintains a longstanding RA development framework (signs/symptoms + optional structural-damage + physical-function claims). The approval history is mature and layered: csDMARDs, then TNF blockers (1998–2002), then IL-6R/costimulation/CD20 biologics (2005–2010), then JAK inhibitors (2012–2019) [FDA/Drugs@FDA]. The JAK class now carries a **class-wide boxed warning** triggered by the ORAL Surveillance post-marketing trial (§5.2).

### 4.3 Trial Design Parameters
Typical Phase 3 RA registration trials enroll **~500–1,600 patients**, are randomized double-blind, and are framed by prior-therapy failure — MTX-inadequate-responders (MTX-IR) or biologic-inadequate-responders (bDMARD-IR). Comparators are placebo (on background MTX) and/or an active comparator (MTX monotherapy or adalimumab). Signs/symptoms read out at week 12–24; radiographic and long-term safety extensions run to week 52 and beyond. The landscape is large and mature: **2,291 interventional trials — 477 Phase 3, 332 Phase 4** [CT.gov].

---

## 5. Key Trials

### 5.1 Landmark Trials
- **SELECT-MONOTHERAPY** (NCT02706951; upadacitinib, AbbVie; n=648). Upadacitinib monotherapy vs continuing MTX in MTX-IR patients — pivotal to the 2019 JAK-inhibitor approval; primary endpoints ACR20 and mTSS at week 52 [confirmed via MCP].
- **SELECT-COMPARE** (NCT02629159; upadacitinib, AbbVie; n=1,629). Upadacitinib vs placebo vs adalimumab on background MTX — the head-to-head-against-a-TNF design that positioned upadacitinib against the biologic standard.
- **ORAL program** (e.g., NCT00853385; tofacitinib, Pfizer; n=717). Supported the first-in-class 2012 JAK approval.
- **Foundational biologic trials** established the TNF (etanercept/infliximab/adalimumab), IL-6R (tocilizumab), costimulation (abatacept), and B-cell (rituximab) mechanisms and made ACR20/50/70 + mTSS the accepted endpoint pairing.

### 5.2 Notable Failures & Lessons
- **ORAL Surveillance** (NCT02092467; tofacitinib vs TNF inhibitor; n=4,372; Phase 3B/4, mandated post-marketing). Designed "to compare the safety of tofacitinib versus TNF inhibitor with respect to major cardiovascular adverse events and malignancies"; tofacitinib failed non-inferiority for MACE and malignancy in RA patients ≥50 with ≥1 cardiovascular risk factor, triggering a **class-wide boxed warning** for all JAK inhibitors (serious CV events, malignancy, thrombosis, mortality) [verified via MCP].
- **Mechanism lesson.** Narrow single-cytokine approaches (e.g., anti-IL-1 anakinra) proved less effective in RA than TNF/IL-6/JAK blockade, reinforcing that RA is a **multi-cytokine convergent disease** — which is precisely why targeting a convergent signaling node (JAK–STAT / TYK2) is mechanistically attractive and why the platform's TYK2 signal is decision-relevant.

---

## Appendix: Sources

**PubMed (literature)**
1. [Global burden and inequalities of rheumatoid arthritis in adults aged 15–49 years, 1990–2021 (GBD)](https://doi.org/10.1007/s10067-026-08158-z) — accessed 2026-07-12
2. [Assessing rheumatoid arthritis prevalence from 1990 to 2040: global inequities through the lens of sociodemographic development](https://doi.org/10.1007/s10067-026-08150-7) — accessed 2026-07-12
3. [Epidemiology of Rheumatoid Arthritis in the Asia-Pacific Region (GBD systematic analysis)](https://doi.org/10.1111/1756-185x.70674) — accessed 2026-07-12
5. [Incidence, Risk Factors, and Mortality of Rheumatoid Arthritis-Associated Interstitial Lung Disease](https://doi.org/10.1002/acr.24856) — accessed 2026-07-12
6. [Proteomic and glycosylation biomarkers in rheumatoid arthritis: advancing early diagnosis](https://doi.org/10.1016/j.cca.2025.120801) — accessed 2026-07-12
7. [Poor prognostic factors and unmet needs in rheumatoid arthritis](https://doi.org/10.1093/rheumatology/keae701) — accessed 2026-07-12
9. [Proteomic and glycosylation biomarkers in RA (multi-analyte panels)](https://doi.org/10.1016/j.cca.2025.120801) — accessed 2026-07-12
10. [Efficacy of synthetic and biological DMARDs: SLR informing the 2022 EULAR recommendations](https://doi.org/10.1136/ard-2022-223365) — accessed 2026-07-12

**FDA (Drugs@FDA, via MCP)**
11. [Drugs@FDA — RA drug applications & pharmacologic classes (methotrexate, TNF blockers, tocilizumab, abatacept, rituximab, JAK inhibitors)](https://www.accessdata.fda.gov/scripts/cder/daf/) — accessed 2026-07-12

**ClinicalTrials.gov (via MCP)**
12. [NCT02706951 — SELECT-MONOTHERAPY (upadacitinib vs MTX)](https://clinicaltrials.gov/study/NCT02706951) — accessed 2026-07-12
13. [NCT02629159 — SELECT-COMPARE (upadacitinib vs placebo vs adalimumab)](https://clinicaltrials.gov/study/NCT02629159) — accessed 2026-07-12
14. [NCT00853385 — ORAL program (tofacitinib Phase 3)](https://clinicaltrials.gov/study/NCT00853385) — accessed 2026-07-12
15. [NCT02092467 — ORAL Surveillance (tofacitinib vs TNF inhibitor safety)](https://clinicaltrials.gov/study/NCT02092467) — accessed 2026-07-12

**CDC / NHANES**
4. [Distribution of Arthritis Subtypes Among US Adults, 2017–March 2020 (NHANES)](https://www.cdc.gov/pcd/issues/2025/24_0393.htm) — accessed 2026-07-12

**ClinicalTrials.gov protocol (epidemiology reference)**
8. [Population-based RA frequency/incidence (protocol epidemiology section, NCT04033809)](https://cdn.clinicaltrials.gov/large-docs/09/NCT04033809/Prot_SAP_000.pdf) — accessed 2026-07-12
