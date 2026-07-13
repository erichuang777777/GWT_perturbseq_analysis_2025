# Rheumatoid Arthritis

**Platform link**: Target genes **TBC1D10A** (platform signed-DE rank 6, Open Targets genetic-association score 0.08) and **TYK2** (platform signed-DE rank 11, Open Targets genetic-association score 0.93).

> Note: This task's brief stated that a full deep-dive indication dossier for rheumatoid arthritis (covering both TBC1D10A and TYK2) already exists elsewhere in this project, and instructed a brief entry on that basis. However, artifact-store searches run in this session (`host.artifacts(search="rheumatoid arthritis dossier")`, `search="TYK2 rheumatoid"`, `search="TBC1D10A"`, across this project and project_id="all") did not locate that prior dossier — only unrelated QQ/violin-plot scripts and the two files just produced in this pass turned up. This entry is therefore a compact summary only; the referenced fuller dossier could not be independently verified to exist and may need to be located or regenerated.

## 1. Definition & Population
Rheumatoid arthritis (RA) is a chronic, systemic autoimmune disease causing symmetric inflammatory polyarthritis, predominantly affecting small joints of the hands and feet, with a female predominance and typical onset in mid-adulthood.

## 2. Epidemiology Highlights
Not established in this pass — no epidemiology figures were re-sourced, and the task brief's claim of a fuller pre-existing RA dossier holding this detail could not be verified via artifact-store search in this session.

## 3. Biology Highlights
- TYK2 is a well-validated JAK-family kinase in RA-relevant JAK-STAT cytokine signaling; TYK2 inhibition is an active area of RA drug development, as reflected in a recent case report on TYK2 inhibitor use in overlapping psoriatic/rheumatoid arthritis: "Successful Management of Multidrug-Resistant Psoriatic Arthritis Coexisting With Rheumatoid Arthritis Using a TYK2 Inhibitor Deucravacitinib-Based Regimen."
- TBC1D10A is a Rab-GAP family protein with a much lower Open Targets genetic-association score (0.08) than TYK2 (0.93) in this platform's annotations, consistent with it being a novel/lower-confidence nomination rather than an established RA gene — not further re-verified in this compact pass; the brief's claim of a fuller pre-existing dossier with this detail is unverified (see note above).

## 4. Current Treatment
Standard RA therapy includes conventional DMARDs (methotrexate), biologics (TNF inhibitors, IL-6R inhibitors, T-cell costimulation blockade), and JAK inhibitors including tofacitinib, which carries an FDA black-box warning: "The US Food and Drug Administration (FDA) recently placed a black box warning on this class of medications due to safety concerns based on data from studies investigating tofacitinib in patients with rheumatoid arthritis." Full drug-class detail was claimed to exist in a prior dossier per the task brief, but that dossier is unverified via artifact-store search in this session.

## 5. Regulatory & Trials Snapshot
ClinicalTrials.gov lists a large interventional trial base for RA; a search restricted to interventional studies returned a total of 2,538 matching trials, including completed Phase 3 biosimilar comparator studies such as NCT03789292 (CT-P17 vs. Humira in moderate-to-severe active RA).

## Sources
1. "Successful Management of Multidrug-Resistant Psoriatic Arthritis Coexisting With Rheumatoid Arthritis Using a TYK2 Inhibitor Deucravacitinib-Based Regimen" (PMID 40476606), pubmed, https://pubmed.ncbi.nlm.nih.gov/40476606/, accessed 2026-07-12.
2. "A Review on the Safety of Using JAK Inhibitors in Dermatology: Clinical and Laboratory Monitoring" (PMID 36790724), pubmed, https://pubmed.ncbi.nlm.nih.gov/36790724/, accessed 2026-07-12.
3. ClinicalTrials.gov search: condition="rheumatoid arthritis", study_type=INTERVENTIONAL, total=2538, ctgov, https://clinicaltrials.gov/search?cond=rheumatoid%20arthritis, accessed 2026-07-12.
4. NCT03789292, "A Randomized, Active-Controlled, Double-Blind, Phase 3 Study to Compare Efficacy and Safety of CT-P17 With Humira ... in Patients With Moderate to Severe Active Rheumatoid Arthritis", ctgov, https://clinicaltrials.gov/study/NCT03789292, accessed 2026-07-12.
5. Claimed prior full RA/TYK2/TBC1D10A deep-dive dossier (per task brief) — not located via artifact-store search in this session; existence unverified.
