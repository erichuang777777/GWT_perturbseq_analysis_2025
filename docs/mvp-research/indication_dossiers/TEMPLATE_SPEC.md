# Compact Indication Dossier — Template Spec (v1, for 23-disease batch)

Each disease gets exactly one markdown file `<slug>.md` + one JSON `<slug>.json`
in `do_not_commit/disease_dossiers/`. Keep total research calls tight:
2-4 PubMed searches, 1-2 ClinicalTrials.gov searches, 1 Drugs@FDA check per
disease is enough. This is NOT a full 5-phase indication-dossier run — it is
a compact single-pass version of the same standards.

## Anti-fabrication rules (non-negotiable, same as indication-dossier skill)
- Every factual claim needs: source_url (real, actually fetched/returned by
  a tool — NEVER construct or guess a URL), source_type
  (pubmed|ctgov|fda|other), and a short verbatim quote from that source.
- If you cannot find a fact after a genuine attempt, write "Not established
  in this pass" — do not guess numbers, dates, drug names, or trial IDs.
- MCP tools available: `pubmed` (search_articles, get_article_metadata),
  `clinical-trials` (search_trials, get_trial_details, analyze_endpoints),
  `drug-regulatory` (search_drug_applications with brand=/generic=/
  active_ingredient= filters, get_drug_statistics).
- All MCP calls happen in the `repl` tool, never python/r.

## Markdown structure (target ~500-900 words per disease)

```markdown
# [Disease Name]

**Platform link**: Target gene **[GENE]** (platform signed-DE rank [N],
Open Targets genetic-association score [S]) [+ second gene if disease has 2].

## 1. Definition & Population
[1-2 sentences: what the disease is, ICD-10 code if commonly known,
who is affected (age/sex pattern if well known).]

## 2. Epidemiology Highlights
[2-3 bullet points: prevalence/incidence numbers with source, or "Not
established in this pass" if a genuine search turns up nothing solid.]

## 3. Biology Highlights
[2-3 bullet points: key pathway/mechanism, and — if relevant — how it
connects to the platform's [GENE] biology (JAK-STAT, cytokine, etc.)
Only draw this connection if genuinely supportable; otherwise state the
disease biology on its own.]

## 4. Current Treatment
[Bulleted list: approved drug classes with mechanism, 1-2 approval
years/FDA anchors if found via drug-regulatory MCP. Or "No FDA-approved
disease-specific therapy identified in this pass" if genuinely none found.]

## 5. Regulatory & Trials Snapshot
[1-2 sentences: total interventional trial count for the disease from
ClinicalTrials.gov (search_trials with count_total=True), any standout
Phase 3 trial found.]

## Sources
[Numbered list: title/short-description, source_type, URL, accessed date.]
```

## JSON structure (`<slug>.json`)
```json
{
  "disease_name": "...",
  "slug": "...",
  "platform_targets": [{"gene": "...", "primary_rank": N, "ot_genetic_assoc_score": 0.0}],
  "sections": {
    "definition_population": {"content": "...", "sources": [{"source_url":"","source_type":"","quote":""}]},
    "epidemiology": {"content": "...", "sources": [...], "coverage": "covered|partial|not_established"},
    "biology": {"content": "...", "sources": [...], "coverage": "..."},
    "treatment": {"content": "...", "sources": [...], "coverage": "..."},
    "regulatory_trials": {"content": "...", "sources": [...], "coverage": "..."}
  },
  "gaps": ["..."]
}
```

## Output
Save both files to `do_not_commit/disease_dossiers/` in your OWN workspace,
then call `save_artifacts` on both. Report back the artifact version_ids
for each file you produced, plus the disease name, plus a one-line note on
data quality per disease (e.g. "TYK2/RA well-sourced; NPHP4/Behcet weak,
only genetic-association score available").
