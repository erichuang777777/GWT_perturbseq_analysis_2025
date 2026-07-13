# 23-Disease Dossier Batch — Summary

Generated 2026-07-12 for the GWT Perturb-seq / Perturbase target-discovery platform.

## Scope
23 immune-related disease labels drawn from the platform's Level-4 external-validation
crosscheck (`top_immune_disease` per target, Open Targets genetic-association score).
26 disease x gene rows total (3 diseases map to 2 targets each: rheumatoid arthritis, multiple sclerosis, immune system disorder; remaining 20 map to 1 target each).

## Deliverables

1. **23 compact indication dossiers** (/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/88118381-77b1-4012-ae43-754697c8c07b/v6e414638_disease_master_index.csv indexes all of them) —
   each with Definition & Population / Epidemiology / Biology / Treatment / Regulatory & Trials
   sections, every claim cited with source_url + source_type + verbatim quote.
   One disease (rheumatoid arthritis) additionally has a full 5-phase deep-dive dossier
   (`ra_dossier.html`, produced in an earlier pass).

2. **Cross-disease master index** — `disease_master_index.csv`
   (disease x platform target x rank x genetic-association score x dossier links).

3. **Front-end design document** — `FRONTEND_DESIGN_DOC.md` — data schema, wireframe, and
   exact wiring instructions grounded in the real `frontend/webserver/` React/TS codebase
   (verified against `views/Clinical.tsx`, `views/Dossier.tsx`, `store/store.tsx`,
   `api/routers/disease.py`).

## Data quality notes

- All 23 dossiers passed a citation-completeness check (every source has source_url +
  source_type + quote) and a URL-fabrication check (2 constructed FDA URLs found and
  fixed — drug-regulatory MCP tool does not return a URL field, so none should have
  been invented).
- 17 of 23 files had leaked internal `<cite>` tags from citation formatting; all stripped.
- 5 of 23 files run slightly under the ~500-900 word target (433-481 words) — this
  reflects genuinely thin published evidence for those diseases, not under-reporting;
  content was not padded with uncited filler to hit a word count.
- Three diseases share a name across two distinct platform targets with very different
  genetic-association scores (rheumatoid arthritis: TBC1D10A 0.08 vs TYK2 0.93;
  multiple sclerosis: EXTL2 0.12 vs UBAC1 0.38; immune system disorder: PLA2G4A 0.35
  vs PDIA6 0.36) — all three pairs are preserved in the master index rather than
  collapsed to one.

## Disease list (ranked by best platform signed-DE rank)

                                                            disease gene_symbol  primary_rank  ot_genetic_assoc_score
                                                lupus erythematosus       FOXN2           1.0                    0.09
                                                             asthma        SIK2           3.0                    0.72
                                                           vitiligo    TMEM131L           5.0                    0.43
                                               rheumatoid arthritis    TBC1D10A           6.0                    0.08
                                                       polycythemia       THAP5           7.0                    0.34
                                               rheumatoid arthritis        TYK2          11.0                    0.93
               Spondyloenchondrodysplasia with immune dysregulation      ZNF627          15.0                    0.94
                                              primary myelofibrosis        CALR          17.0                    0.72
                                                     Graves disease       ITM2A          18.0                    0.52
                                                 ulcerative colitis        ERN1          21.0                    0.45
                                             immune system disorder     PLA2G4A          23.0                    0.35
                                                  acute tonsillitis      MAN2A1          25.0                    0.31
                                           type 1 diabetes mellitus      DIPK1A          31.0                    0.50
                                             immune system disorder       PDIA6          32.0                    0.36
                                                immunodeficiency 28      IFNGR2          33.0                    0.90
                                           primary thrombocytopenia     TMEM131          34.0                    0.39
                                                      Crohn disease        CYLD          36.0                    0.59
                                                          psoriasis     KLHDC10          37.0                    0.40
                                                     Behcet disease       NPHP4          39.0                    0.45
                                                 multiple sclerosis       EXTL2          43.0                    0.12
                                                 multiple sclerosis       UBAC1          44.0                    0.38
                                                psoriatic arthritis      KIF16B          46.0                    0.47
                                                immunodeficiency 18        CD3E         401.0                    0.92
           immune dysregulation, autoimmunity, and autoinflammation       PLCG1         520.0                    0.55
                                                immunodeficiency 37       BCL10         889.0                    0.86
hyper-IgE syndrome 6, autosomal dominant, with recurrent infections       STAT3         925.0                    0.95
