# Topic 13 - CD4/T-Cell Drug Development Progress And Clinical Trials

Date reviewed: 2026-07-04

Local evidence files:

- `sources/topic13_clinicaltrials_searches.json`: ClinicalTrials.gov API snapshot for 36 CD4/T-cell-related drug/pathway queries.
- `sources/topic13_clinicaltrials_flat.csv`: flattened trial table, 326 returned studies.
- `sources/topic13_pubmed_esummary.json`: PubMed esummary cache for key clinical papers.

## Executive Takeaways

CD4/T-cell drug development is not one route. The clinically useful axes are T-cell modulation, tolerance, costimulation blockade, cytokine signaling, Treg restoration, Th17/IL-23 suppression, and trafficking control.

For GWT primary CD4 Perturb-seq, the practical role is to map CD4 target perturbations to clinical precedent and risk, not to predict clinical success. Active or recruiting trials are evidence of current development interest only. Approved drugs validate a pathway in a specific indication and modality; they do not validate every upstream or downstream target in GWT.

Highest-priority axes for a GWT-aware toolkit:

1. CD40L/costimulation: frexalimab, dapirolizumab pegol, tegoprubart.
2. OX40/OX40L: rocatinlimab, amlitelimab.
3. CD3/TCR tuning: teplizumab, foralumab; otelixizumab as failure anchor.
4. IL-2/Treg restoration: low-dose IL-2, rezpegaldesleukin; daclizumab as warning anchor.
5. PD-1 agonism / checkpoint-tolerance: peresolimab, rosnilimab.
6. Approved benchmark axes: JAK/STAT, IL-17/IL-23/Th17, S1P/integrin trafficking.

## Current Development Map

| Axis | Representative agents | Status as of 2026-07-04 | How GWT can help | Main caveat |
|---|---|---|---|---|
| Direct CD4 | Ibalizumab, UB-421/semzuvolimab | Ibalizumab approved for MDR HIV; UB-421 HIV trials mostly early/mid-stage | Proves CD4 protein can be drugged | Antiviral entry blockade is not autoimmune CD4 modulation |
| CD3/TCR tolerance | Teplizumab, foralumab, otelixizumab | Teplizumab approved; foralumab Phase 2 in SPMS/neuro; otelixizumab failed/terminated | Maps TCR-proximal genes and tolerance signatures | CRS, lymphopenia, viral reactivation, dose/timing |
| CD28/B7 costimulation blockade | Abatacept, belatacept | Approved in RA/transplant/GVHD contexts | Strong positive benchmark for CD28 activation axis | Same pathway failed in IBD; infection/PTLD risks |
| CD40L/CD154 | Frexalimab, dapirolizumab pegol, tegoprubart | Multiple active Phase 2/3 programs; dapirolizumab Phase 3 SLE data published 2026 | High-priority T-cell/APC/B-cell help axis | Old anti-CD40L thromboembolism history; Fc/platelet risk |
| OX40/OX40L | Rocatinlimab, amlitelimab | Phase 2 positive; Phase 3 AD programs active/completed | T helper activation/memory and Th2/AD programs | Skin tissue context and long-term immune safety |
| IL-2/Treg | Rezpegaldesleukin, low-dose IL-2, basiliximab/daclizumab | Rezpegaldesleukin Phase 2 AD/AA/T1D; basiliximab approved transplant; daclizumab withdrawn | FOXP3/IL2RA/STAT5/CTLA4/Treg hypothesis axis | Direction matters: Treg support vs CD25 blockade |
| PD-1 agonism / tolerance | Peresolimab, rosnilimab | Peresolimab Phase 2a signal but later RA study terminated; rosnilimab active Phase 2 RA/UC | Checkpoint/tolerance and activated T-cell suppression | Agonism vs blockade direction must be explicit |
| JAK/STAT | Tofacitinib, upadacitinib, baricitinib, deucravacitinib/TYK2 | Multiple approvals; ongoing extensions and new indications | Strong druggable cytokine-signaling benchmark | Serious infection, MACE, malignancy, thrombosis warnings |
| IL-17/IL-23/Th17 | Secukinumab, ixekizumab, bimekizumab, ustekinumab, risankizumab | Multiple approvals in skin/joint/IBD contexts | Validates Th17/IL-23 modules | IL-17 blockade can worsen/fail in Crohn's disease |
| Trafficking / tissue homing | Vedolizumab, natalizumab, ozanimod, etrasimod | Multiple approvals | Migration/egress/homing modules | PML, lymphopenia, cardiac/liver/infection risks; tissue context often outside GWT |

## Approved Or Clinically Validated Anchors

| Drug / target / pathway | Indication | Evidence | Outcome | GWT target-card use |
|---|---|---|---|---|
| Ibalizumab / CD4 | Multidrug-resistant HIV-1 | `NCT02475629`, `NCT02707861`; PMID `30110589`; DOI `10.1056/NEJMoa1711460`; DailyMed TROGARZO | FDA-approved CD4-directed antibody | Mark as direct-CD4 druggability anchor, but only for viral entry |
| Teplizumab / anti-CD3 | Stage 2 T1D delay; pediatric/newer T1D settings | `NCT01030861`, `NCT03875729`; PMIDs `31180194`, `37861217`; DailyMed TZIELD | Approved T-cell tolerance/interception anchor | Positive CD3/TCR benchmark; require CRS, lymphopenia, viral-reactivation flags |
| Abatacept / CTLA4-Ig | RA, PsA, pJIA, aGVHD prophylaxis | `NCT00048568`; PMID `16785475`; DailyMed ORENCIA | Approved costimulation blockade | Positive CD28/B7 benchmark for activation suppression |
| Belatacept / CTLA4-Ig variant | Kidney transplant rejection prophylaxis | `NCT00256750`; PMIDs `20415897`, `26816011`; DailyMed NULOJIX | Approved transplant immunosuppression | Costimulation positive control; add infection/PTLD context |
| Secukinumab / IL-17A | Psoriasis, PsA, AS, HS and related diseases | `NCT01365455`, `NCT01358578`; PMID `25007392`; DOI `10.1056/NEJMoa1314258` | Approved Th17-output blockade | Strong Th17 benchmark, but disease context dependent |
| Ustekinumab / IL-12/23 p40 | Psoriasis/IBD and related diseases | `NCT00267969`; PMID `18486739`; DOI `10.1016/S0140-6736(08)60725-4` | Approved IL-12/23 axis drug | Benchmark for IL-23/Th17 upstream biology |
| Risankizumab / IL-23 p19 | Psoriasis/PsA/Crohn/UC | DailyMed SKYRIZI; multiple Phase 3 trials | Approved IL-23 axis | If GWT hits IL23R/STAT3/RORC modules, map to approved class |
| Vedolizumab / alpha4beta7 | UC/Crohn's disease | `NCT00783718`; PMIDs `23964932`, `23964933`; DailyMed ENTYVIO | Approved gut-selective trafficking therapy | Use for gut-homing benchmark; not fully de-risked by CD4 RNA |
| Ozanimod / S1P receptor | UC/MS | `NCT02435992`; PMID `34587385`; DailyMed ZEPOSIA | Approved oral trafficking modulation | Egress/trafficking benchmark; requires lymphopenia/cardiac/liver risk flags |
| Tofacitinib / JAK | RA/PsA/UC/AS and other contexts | `NCT00853385`; PMID `22873531`; ORAL Surveillance `NCT02092467`, PMID `35081280` | Efficacy validated but safety-limited | JAK/STAT benchmark with boxed-warning-like safety cap |
| Deucravacitinib / TYK2 | Plaque psoriasis; PsA indication added in 2026 label materials | DailyMed SOTYKTU; FDA approval letter 2026 | More selective cytokine-signaling benchmark | Useful for TYK2/IL-23/IFN signatures; still monitor infection/liver/TB |

## Active Or Emerging Development Axes

| Drug / target / pathway | Current trials/status | Primary evidence | Interpretation for GWT |
|---|---|---|---|
| Frexalimab / CD40L | Phase 2 positive in relapsing MS; Phase 3 active/not recruiting in RMS/SPMS; recruiting additional MS/transplant studies | `NCT04879628`, `NCT06141473`, `NCT06141486`, `NCT07325292`; PMID `38354138`; DOI `10.1056/NEJMoa2309439` | High-priority CD40L/APC-crosstalk axis; score cap remains Phase 3/investigational |
| Dapirolizumab pegol / CD40L | Phase 3 SLE completed/published; long-term extension and additional Phase 3 studies | `NCT04294667`, `NCT04976322`, `NCT06617325`; PMID `42214397`; DOI `10.1016/S0140-6736(26)00691-4` | Strong 2026 signal for CD40L in SLE; still investigational until regulatory approval |
| Tegoprubart / CD40L | Phase 1/2 and Phase 2 transplant development | `NCT06305286`; company/clinical-trial updates | Transplant costimulation axis; use as development-interest evidence, not efficacy proof unless peer-reviewed |
| Rocatinlimab / OX40 | Multiple Phase 3 AD studies completed/active; Phase 2b published | `NCT05398445`, `NCT05633355`, `NCT05724199`, `NCT05882877`; PMID `36509097` | Good T-cell activation/memory/AD benchmark; requires skin context |
| Amlitelimab / OX40L | Phase 2b published; Phase 3 AD recruiting/active | `NCT05131477`, `NCT06241118`, `NCT06407934`; PMIDs `37463508`, `39522654` | Non-depleting OX40L blockade; useful for Th2/T helper program matching |
| Foralumab / anti-CD3 | Intranasal/oral anti-CD3 programs in SPMS, Alzheimer, MSA; some withdrawn COVID/NASH studies | `NCT06292923`, `NCT06489548`, `NCT06868628`, `NCT06802328` | Emerging CD3 tolerance axis; development-interest only until larger efficacy data mature |
| Rezpegaldesleukin / IL-2 pathway | Phase 2b AD and alopecia areata active; recruiting new-onset T1D | `NCT06136741`, `NCT06340360`, `NCT07142252`; prior SLE `NCT04433585` | Treg-biased restoration axis; GWT should require Treg function validation |
| Rosnilimab / PD-1 agonist-like pathogenic T-cell depletion/modulation | Active Phase 2 RA and UC programs | `NCT06041269`, `NCT06127043` | Checkpoint/tolerance axis; use as investigational benchmark |
| Peresolimab / PD-1 agonist | Phase 2a RA positive publication; later RA Phase 2 terminated | `NCT04634253`, `NCT05516758`; PMID `37195941`; DOI `10.1056/NEJMoa2209856` | Interesting mechanism but program risk; mark as mixed/terminated, not validated |

## Failure And Safety-Limited Anchors

| Axis / drug | Evidence | Outcome | Toolkit lesson |
|---|---|---|---|
| CD28 agonism / TGN1412 | PMID `16908486`; DOI `10.1056/NEJMoa063842` | Severe Phase 1 cytokine storm | Any T-cell agonism target needs CRS hard stop and human whole-blood/PBMC cytokine assay |
| Old anti-CD40L / BG9588 | `NCT00001789`; PMID `12632425`; DOI `10.1002/art.10856` | Serologic signal but lupus nephritis trial stopped for thromboembolic events | CD40L score needs thrombosis/platelet/Fc-format safety flag |
| Daclizumab / CD25-IL2RA | `NCT01064401`; PMID `26444729`; DOI `10.1056/NEJMoa1501481`; withdrawn after serious immune-mediated safety issues | Efficacy did not prevent withdrawal | IL-2R/Treg axis needs directionality and immune-mediated toxicity flags |
| JAK inhibitors / tofacitinib ORAL Surveillance | `NCT02092467`; PMID `35081280`; DOI `10.1056/NEJMoa2109927` | Higher MACE/malignancy risk vs TNF inhibitors in risk-enriched RA population | JAK-like signatures need infection, malignancy, MACE, VTE caps |
| IL-17 blockade / secukinumab in Crohn's | `NCT01009281`; PMID `22595313`; DOI `10.1136/gutjnl-2011-301668` | Negative/worsening Crohn signal | Th17 biology must be tissue- and disease-specific |
| Abatacept in IBD | `NCT00406653`, `NCT00410410`; PMID `22504093`; DOI `10.1053/j.gastro.2012.04.010` | Not efficacious in Crohn's/UC | Same costimulation axis can work in RA but not IBD |
| Natalizumab / alpha4 integrin | PMIDs `16510744`, `16510745`; DailyMed TYSABRI | Effective but PML risk | Trafficking targets need PML/opportunistic infection warning |
| Otelixizumab / anti-CD3 | `NCT00678886`, `NCT01123083`; PMID `25011949` | Phase 3 T1D program failed/terminated | Anti-CD3 success depends on dose, timing, endpoint, and patient selection |
| Itolizumab / CD6 | `NCT05263999` terminated Phase 3 aGVHD; `NCT04605926` withdrawn COVID-19 | Program-level mixed/terminated development | Activated T-cell modulation is not automatically translatable |

## Clinical Layer For Target Cards

Recommended fields:

```text
clinical_axis
representative_agents
clinical_stage_bucket
nearest_success_anchor
nearest_failure_anchor
matched_indication
same_direction_as_success
disease_context_match
therapeutic_direction
modality
known_safety_liability
required_PD_biomarker
required_external_validation
score_cap_reason
evidence_date
source_url
```

Recommended stage buckets:

```text
approved
completed_positive
active_recruiting
completed_negative
terminated_or_withdrawn
safety_limited
postmarket_warning
```

## Priority Matching Rules For GWT Top Hits

| GWT signature/hit pattern | Clinical mapping | Required extra validation |
|---|---|---|
| TCR-proximal genes: `CD3E`, `CD247`, `ZAP70`, `LAT`, `LCK`, `ITK`, `PLCG1` | CD3/TCR tuning, teplizumab/foralumab benchmark | Cytokine release, lymphopenia, viral reactivation, activation vs tolerance direction |
| Costimulation genes: `CD28`, `CTLA4`, `ICOS`, `CD40LG`, APC-help modules | Abatacept/belatacept, CD40L programs | Disease-specific context and thrombosis/Fc risk for CD40L |
| Treg/tolerance genes: `FOXP3`, `IL2RA`, `STAT5A/B`, `CTLA4`, `IKZF` | IL-2/Treg restoration or CD25 warning | Treg suppression assay, protein markers, stability |
| JAK/STAT/cytokine modules | JAK/TYK2 drugs | Dose-window, infection, MACE, malignancy, thrombosis flags |
| Th17 genes/modules: `IL17A/F`, `IL23R`, `RORC`, `STAT3`, `CCR6` | IL-17/IL-23 axis | Tissue flag: psoriasis/skin positive, Crohn/IBD caution |
| Homing/egress genes: `ITGA4`, `ITGB7`, `CCR7`, `CCR9`, `S1PR1` | Vedolizumab/natalizumab/S1P drugs | Tissue trafficking, PML/opportunistic infection, lymphocyte count |
| Checkpoint genes: `PDCD1`, `LAG3`, `TIGIT`, `CTLA4` | PD-1 agonism/tolerance or oncology checkpoint blockade | Direction must be explicit: agonize tolerance vs block checkpoint |

## Guardrails

Use these claims:

- GWT CD4 Perturb-seq nominates mechanistic target-condition hypotheses and maps them to clinical precedent.
- Active or recruiting trials indicate current development interest, not therapeutic success.
- Approved drugs validate a pathway in a specific indication and modality.
- Failure anchors are risk priors and design warnings, not proof that every related target will fail.

Avoid these claims:

- GWT predicts clinical efficacy or safety.
- A high DE score means a druggable target.
- Gene knockdown is equivalent to pharmacologic inhibition, agonism, biologic blockade, protein occupancy, or tissue exposure.
- An approved drug in one disease validates the same pathway for all immune diseases.

## Source Links

ClinicalTrials.gov and labels:

- ClinicalTrials.gov API snapshot: `sources/topic13_clinicaltrials_searches.json`
- Ibalizumab Phase 3: https://clinicaltrials.gov/study/NCT02475629
- TZIELD label: https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=e8a39a5f-139c-4510-9777-71cbb00138fa
- FDA 2026 Tzield indication update: https://www.fda.gov/news-events/press-announcements/fda-approves-new-indication-tzield-teplizumab-certain-pediatric-patients-recently-diagnosed-stage-3
- Abatacept: https://clinicaltrials.gov/study/NCT00048568
- Frexalimab Phase 2: https://clinicaltrials.gov/study/NCT04879628
- Frexalimab Phase 3 RMS: https://clinicaltrials.gov/study/NCT06141473
- Dapirolizumab pegol Phase 3 SLE: https://clinicaltrials.gov/study/NCT04294667
- Amlitelimab Phase 3 AD: https://clinicaltrials.gov/study/NCT06241118
- Rocatinlimab Phase 3 AD: https://clinicaltrials.gov/study/NCT05398445
- Foralumab SPMS: https://clinicaltrials.gov/study/NCT06292923
- Rezpegaldesleukin AD: https://clinicaltrials.gov/study/NCT06136741
- Rosnilimab RA: https://clinicaltrials.gov/study/NCT06041269
- Tofacitinib ORAL Surveillance: https://clinicaltrials.gov/study/NCT02092467

Key PubMed sources:

- Ibalizumab: https://pubmed.ncbi.nlm.nih.gov/30110589/
- Teplizumab T1D delay: https://pubmed.ncbi.nlm.nih.gov/31180194/
- Teplizumab stage 3 T1D: https://pubmed.ncbi.nlm.nih.gov/37861217/
- Abatacept RA: https://pubmed.ncbi.nlm.nih.gov/16785475/
- Belatacept BENEFIT: https://pubmed.ncbi.nlm.nih.gov/20415897/
- Secukinumab psoriasis: https://pubmed.ncbi.nlm.nih.gov/25007392/
- Vedolizumab UC/CD: https://pubmed.ncbi.nlm.nih.gov/23964932/ and https://pubmed.ncbi.nlm.nih.gov/23964933/
- Ozanimod UC: https://pubmed.ncbi.nlm.nih.gov/34587385/
- Frexalimab MS: https://pubmed.ncbi.nlm.nih.gov/38354138/
- Peresolimab RA: https://pubmed.ncbi.nlm.nih.gov/37195941/
- Rocatinlimab AD: https://pubmed.ncbi.nlm.nih.gov/36509097/
- Amlitelimab AD Phase 2b: https://pubmed.ncbi.nlm.nih.gov/39522654/
- Dapirolizumab pegol SLE Phase 3: https://pubmed.ncbi.nlm.nih.gov/42214397/
- TGN1412: https://pubmed.ncbi.nlm.nih.gov/16908486/
- Anti-CD40L BG9588: https://pubmed.ncbi.nlm.nih.gov/12632425/
- Daclizumab MS: https://pubmed.ncbi.nlm.nih.gov/26444729/
- Tofacitinib ORAL Surveillance: https://pubmed.ncbi.nlm.nih.gov/35081280/
- Secukinumab Crohn's disease failure: https://pubmed.ncbi.nlm.nih.gov/22595313/
- Abatacept IBD failure: https://pubmed.ncbi.nlm.nih.gov/22504093/
