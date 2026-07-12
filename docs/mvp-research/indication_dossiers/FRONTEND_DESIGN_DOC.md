# Disease Dossier — Front-End Integration Design

**Scope**: wire the 23 compact indication dossiers (one per platform disease label) into the existing React/TypeScript webserver (`frontend/webserver/`), so a user landing on a disease from any target's "External evidence & disease links" panel gets a real disease-level page instead of only the current target-ranking table.

## 1. What exists today (verified against the real repo tree)

| Piece | File | Current behavior |
|---|---|---|
| Per-target disease list | `views/Dossier.tsx` (~L320-345) | Renders `t.diseases: DiseaseAssoc[]` as clickable chips; `onClick={() => navTo("disease", d.id)}` |
| Navigation | `store/store.tsx` `navTo()` | `kind === "disease"` -> `{view: "clinical", clinicalTab: "drug", selectedDisease: id}` |
| Disease-scoped view | `views/Clinical.tsx` (`clinicalTab === "drug"`) | Shows disease-name header + **target-ranking table only** (gene, module, assoc score, trial evidence, readiness, grade) — no disease definition, epidemiology, biology, or standard-of-care content |
| Backend disease endpoint | `api/routers/disease.py` | `GET /api/disease` (list), `GET /api/disease/{disease_name}/targets/{dataset_id}` (target list for a disease) |
| Backend drug-evidence endpoint | `api/routers/disease_drug.py` | `GET /api/disease-drug-evidence?gene=&disease=` — live Open Targets + ClinicalTrials.gov lookup, gene x disease pair |
| Data type | `data/types.ts` | `DiseaseAssoc {name, id, overallScore, geneticAssociationScore}` |

**The gap**: `selectedDisease` in Clinical.tsx currently has nothing to show beyond the target table. This design adds a **Disease Dossier panel** to that same view, sourced from the 23 compact dossiers produced in this pass.

## 2. Disease coverage & source data

23 disease labels come from the Level-4 external-validation crosscheck (`ot_genetic_association_crosscheck.csv`, top_immune_disease per platform target), each carrying an Open Targets genetic-association score. Master cross-reference: **`disease_master_index.csv`** (/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/88118381-77b1-4012-ae43-754697c8c07b/v6e414638_disease_master_index.csv) — 26 disease x gene rows (3 diseases map to 2 genes each: rheumatoid arthritis -> TBC1D10A + TYK2; multiple sclerosis -> EXTL2 + UBAC1; immune system disorder -> PLA2G4A + PDIA6; remaining 20 diseases map to 1 gene each), columns: `disease, slug, gene_symbol, primary_rank, ot_genetic_assoc_score, n_ot_disease, n_ct_trial, n_ncbi_disease, dossier_md_vid, dossier_json_vid`.

Each of the 23 diseases has a compact dossier (`<slug>.md` + `<slug>.json`) with 5 sections: Definition & Population, Epidemiology Highlights, Biology Highlights, Current Treatment, Regulatory & Trials Snapshot — every claim cited (`source_url`, `source_type`, verbatim `quote`); thin-evidence diseases explicitly say "Not established in this pass" rather than guessing. One disease (rheumatoid arthritis) additionally has a full 5-phase deep-dive dossier (`ra_dossier.html`) for reference.

## 3. Data schema for the front end

### 3.1 Static JSON bundle (build-time, no new API dependency)

Ship one consolidated file the front end reads directly — avoids a new backend endpoint for MVP:

```jsonc
// frontend/webserver/public/data/disease_dossiers.json
{
  "generated": "2026-07-12",
  "diseases": [
    {
      "slug": "rheumatoid_arthritis",
      "disease_name": "Rheumatoid arthritis",
      "platform_targets": [
        {"gene": "TBC1D10A", "primary_rank": 6, "ot_genetic_assoc_score": 0.08},
        {"gene": "TYK2", "primary_rank": 11, "ot_genetic_assoc_score": 0.93}
      ],
      "sections": {
        "definition_population": {"content": "...", "coverage": "covered"},
        "epidemiology":          {"content": "...", "coverage": "covered"},
        "biology":                {"content": "...", "coverage": "covered"},
        "treatment":              {"content": "...", "coverage": "covered"},
        "regulatory_trials":      {"content": "...", "coverage": "partial"}
      },
      "sources": [
        {"source_url": "https://doi.org/10.1136/ard-2022-223365", "source_type": "pubmed",
         "quote": "This systematic literature review (SLR) investigated the efficacy of..."}
      ],
      "gaps": ["..."],
      "full_dossier_html": null   // non-null only for rheumatoid_arthritis -> "ra_dossier.html"
    }
  ]
}
```

This mirrors the per-disease JSON schema already produced (`sections.<name>.{content, sources, coverage}`, top-level `gaps`), just concatenated into one array. A build script (`scripts/build_disease_bundle.py`, to be added) pulls the 23 `<slug>.json` artifacts and writes this bundle — same pattern as the existing `real-dataset.json` static data file already in `public/`.

### 3.2 TypeScript types (add to `data/types.ts`)

```typescript
export interface DossierSection {
  content: string;
  coverage: "covered" | "partial" | "not_established";
}

export interface DossierSource {
  source_url: string | null;
  source_type: "pubmed" | "ctgov" | "fda" | "other";
  quote: string;
}

export interface DiseaseDossier {
  slug: string;
  disease_name: string;
  platform_targets: { gene: string; primary_rank: number; ot_genetic_assoc_score: number | null }[];
  sections: {
    definition_population: DossierSection;
    epidemiology: DossierSection;
    biology: DossierSection;
    treatment: DossierSection;
    regulatory_trials: DossierSection;
  };
  sources: DossierSource[];
  gaps: string[];
  full_dossier_html: string | null;
}
```

## 4. Page wireframe

### 4.1 Entry points (both already exist, no new nav needed)

1. **Dossier.tsx** (target page) -> disease chip click -> `navTo("disease", d.id)` (existing)
2. **Explorer.tsx** (ranking table) -> could add a disease-tag column later (not in this pass's scope; noted as a follow-up)

### 4.2 Disease Dossier panel (new) — inserted into Clinical.tsx, `clinicalTab === "drug"`, above the existing target-ranking table

```
┌─────────────────────────────────────────────────────────────────────┐
│  ← Back                                    [Disease chip row]        │  (existing)
│                                                                       │
│  Rheumatoid arthritis                          [Full dossier ↗]      │  <- NEW header row;
│  ICD-10 M05/M06 · 621-gene tier1 + Level-4 genetic association       │     "Full dossier" link
│                                                                       │     only shown when
│  ┌───────────┬───────────┬───────────┬───────────┬────────────────┐ │     full_dossier_html
│  │Definition │Epidemio-  │ Biology   │Treatment  │Regulatory &    │ │     is non-null
│  │& Population│logy      │           │           │Trials          │ │  <- NEW 5-tab strip
│  └───────────┴───────────┴───────────┴───────────┴────────────────┘ │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ [Active tab content — 2-4 paragraph content string]            │  │  <- NEW content pane
│  │ Coverage badge: ● covered / ◐ partial / ○ not established      │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Sources (n)                                              [expand ▾]│  <- NEW collapsible
│    1. Efficacy of synthetic and biological DMARDs... (PubMed) ↗     │     source list, each
│       "This systematic literature review (SLR) investigated..."     │     item shows quote
│                                                                       │
│  — existing target-ranking table continues below, unchanged —       │
│  Target │ Concept module │ Assoc. score │ Trial evidence │ ...       │
└─────────────────────────────────────────────────────────────────────┘
```

Design notes:
- **5-tab strip**, not an accordion — matches the existing tab idiom already used elsewhere in Clinical.tsx (`clinicalTab`), so it is visually consistent rather than introducing a new interaction pattern.
- **Coverage badge** is not decorative — it is the same honesty signal the dossiers themselves carry (`covered`/`partial`/`not_established`), so a user immediately sees when a section is thin rather than discovering it by reading prose.
- **Sources list collapsed by default** (matches the existing `ⓘ` disclaimer pattern already at the bottom of the drug tab) — expand reveals the full verbatim-quote citation list, each with an outbound link when `source_url` is non-null.
- When no dossier exists for a `selectedDisease` (e.g. a disease outside the 23), the panel is omitted entirely and the existing target-ranking table renders exactly as it does today — strictly additive, zero regression risk.

## 5. Disease-tag -> target-ranking linkage (the specific ask)

The linkage already exists structurally and this design does not change it — it only adds disease-level content above it:

1. Target's `diseases: DiseaseAssoc[]` (per-target, from Open Targets) carries `{name, id, overallScore, geneticAssociationScore}`.
2. Clicking a disease chip on a target's Dossier page sets `state.selectedDisease = d.id` and switches to Clinical/drug tab.
3. Clinical.tsx filters the full target set to `disMatches` — every target whose own `diseases[]` includes this disease id — and renders them ranked by association score, each row still clickable back to that target's own Dossier page (`onClick={() => setState({view: "dossier", selectedGene: m.gene})}`).
4. **This design's addition**: the disease dossier content (5 sections + sources) is looked up by matching `selectedDisease` (an Open Targets disease id/name) against `disease_dossiers.json[].disease_name` — a case-insensitive name match, since the 23 dossiers were built from the platform's own disease-label vocabulary (`top_immune_disease` column), which is the same vocabulary `DiseaseAssoc.name` uses.

## 6. Known limitations to disclose in the UI (do not silently smooth over)

- Association-score provenance differs across two data pulls used elsewhere in the platform (Level-4 crosscheck vs the 621-gene tier1 expansion) — this design uses the Level-4 pull exclusively for the 23-disease scope to avoid mixing snapshot dates within one page.
- 3 of 23 diseases share a name with a second, unrelated platform target (rheumatoid arthritis: TBC1D10A score 0.08 vs TYK2 score 0.93; multiple sclerosis: EXTL2 0.12 vs UBAC1 0.38; immune system disorder: PLA2G4A score 0.35 vs PDIA6 score 0.36) — the panel must show both targets, not silently pick the higher-scoring one.
- Several dossiers are thin by construction (e.g. "immune system disorder" is a non-specific Open Targets label, not a diagnostic entity) — the `not_established` coverage badge is the mechanism for surfacing this rather than hiding it.
- `regulatory_trials` section is marked `partial` in most dossiers (FDA guidance framework text was not fetched verbatim) — carry this coverage flag through, do not upgrade it silently.

## 7. Implementation order (suggested, not in this pass's scope)

1. Add `build_disease_bundle.py` to generate `public/data/disease_dossiers.json` from the 23 artifact JSONs.
2. Add `DiseaseDossier`/`DossierSection`/`DossierSource` types to `data/types.ts`.
3. Add a `diseaseDossierBySlug()` lookup helper to `lib/logic.ts` (name-matching against `DiseaseAssoc.name`).
4. Add the 5-tab dossier panel component to `views/Clinical.tsx`, gated on `clinicalTab === "drug" && selectedDisease` and a successful lookup.
5. For rheumatoid arthritis specifically, link `full_dossier_html` to the standalone `ra_dossier.html` page (open in new tab) as a worked example of the deeper format.
