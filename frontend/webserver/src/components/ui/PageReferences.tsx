import { useStore } from "../../store/store";

// Per-page reference block. Each entry mirrors a row in
// public/provenance_registry.csv (the single source of truth) — component
// label + resolvable identifier (PMID / DOI / URL). Pages pass only the keys
// they actually use, so the block at the foot of each tab lists exactly the
// data sources and papers behind what that page shows, and links through to
// the full provenance table for everything else.

export type RefKey =
  | "gwt_primary"
  | "open_targets"
  | "clinicaltrials"
  | "pubmed"
  | "gnomad"
  | "gtex"
  | "lincs"
  | "reactome"
  | "string"
  | "alphafold"
  | "chembl"
  | "cellxgene"
  | "hpa"
  | "deseq2"
  | "benjamini_hochberg"
  | "ochoa_ot"
  | "karczewski_gnomad"
  | "jumper_alphafold"
  | "szklarczyk_string"
  | "gillespie_reactome"
  | "subramanian_lincs"
  | "zdrazil_chembl"
  | "gtex_consortium"
  | "cz_cellxgene"
  | "jak_oral_surveillance"
  | "teplizumab";

interface RefEntry {
  label: string;
  pmid?: string;
  doi?: string;
  url?: string;
}

// Curated from provenance_registry.csv — identifiers are copied verbatim.
const REF_CATALOG: Record<RefKey, RefEntry> = {
  gwt_primary: { label: "Zhu & Dann et al. 2025 — CD4 Perturb-seq (primary dataset)", doi: "10.64898/2025.12.23.696273" },
  open_targets: { label: "Open Targets Platform", url: "https://platform.opentargets.org", pmid: "39657122" },
  clinicaltrials: { label: "ClinicalTrials.gov (NLM)", url: "https://clinicaltrials.gov" },
  pubmed: { label: "PubMed / PMC", url: "https://pubmed.ncbi.nlm.nih.gov" },
  gnomad: { label: "gnomAD v2.1.1 constraint", url: "https://gnomad.broadinstitute.org", pmid: "32461654" },
  gtex: { label: "GTEx tissue expression", url: "https://gtexportal.org", pmid: "32913098" },
  lincs: { label: "LINCS / CMap L1000", url: "https://clue.io", pmid: "29195078" },
  reactome: { label: "Reactome pathways", url: "https://reactome.org", pmid: "34788843" },
  string: { label: "STRING v12 interactions", url: "https://string-db.org", pmid: "36370105" },
  alphafold: { label: "AlphaFold DB", url: "https://alphafold.ebi.ac.uk", pmid: "34265844" },
  chembl: { label: "ChEMBL", url: "https://www.ebi.ac.uk/chembl", pmid: "37933841" },
  cellxgene: { label: "CELLxGENE Census (CZI)", url: "https://cellxgene.cziscience.com", pmid: "39607691" },
  hpa: { label: "Human Protein Atlas", url: "https://www.proteinatlas.org" },
  deseq2: { label: "Love et al. 2014 — DESeq2", pmid: "25516281", doi: "10.1186/s13059-014-0550-8" },
  benjamini_hochberg: { label: "Benjamini & Hochberg 1995 — FDR control", doi: "10.1111/j.2517-6161.1995.tb02031.x" },
  ochoa_ot: { label: "Ochoa et al. 2024 — Open Targets", pmid: "39657122", doi: "10.1093/nar/gkae1128" },
  karczewski_gnomad: { label: "Karczewski et al. 2020 — gnomAD", pmid: "32461654", doi: "10.1038/s41586-020-2308-7" },
  jumper_alphafold: { label: "Jumper et al. 2021 — AlphaFold", pmid: "34265844", doi: "10.1038/s41586-021-03819-2" },
  szklarczyk_string: { label: "Szklarczyk et al. 2023 — STRING", pmid: "36370105", doi: "10.1093/nar/gkac1000" },
  gillespie_reactome: { label: "Gillespie et al. 2022 — Reactome", pmid: "34788843", doi: "10.1093/nar/gkab1028" },
  subramanian_lincs: { label: "Subramanian et al. 2017 — LINCS L1000", pmid: "29195078", doi: "10.1016/j.cell.2017.10.049" },
  zdrazil_chembl: { label: "Zdrazil et al. 2024 — ChEMBL", pmid: "37933841", doi: "10.1093/nar/gkad1004" },
  gtex_consortium: { label: "GTEx Consortium 2020", pmid: "32913098", doi: "10.1126/science.aaz1776" },
  cz_cellxgene: { label: "CZ CELLxGENE 2024", pmid: "39607691", doi: "10.1093/nar/gkae1142" },
  jak_oral_surveillance: { label: "Ytterberg et al. 2022 — JAK ORAL Surveillance", pmid: "35081280", doi: "10.1056/NEJMoa2109927" },
  teplizumab: { label: "Herold et al. 2019 — Teplizumab", pmid: "31180194", doi: "10.1056/NEJMoa1902226" },
};

export default function PageReferences({ title = "References for this page", keys }: { title?: string; keys: RefKey[] }) {
  const { setState } = useStore();
  const entries = keys.map((k) => REF_CATALOG[k]).filter(Boolean);
  if (entries.length === 0) return null;
  return (
    <section style={{ marginTop: "40px", paddingTop: "22px", borderTop: "1px solid #e2e5ea" }}>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", flexWrap: "wrap", gap: "8px", marginBottom: "12px" }}>
        <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".5px", color: "#8a92a0", textTransform: "uppercase" }}>{title}</div>
        <span className="navlink" onClick={() => setState({ view: "provenance" })} style={{ fontSize: "12px", fontWeight: 600, color: "#1a5fb4" }}>
          Full provenance table →
        </span>
      </div>
      <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 24px" }}>
        {entries.map((e, i) => (
          <li key={i} style={{ fontSize: "12px", color: "#4a515e", lineHeight: 1.5, display: "flex", gap: "8px", alignItems: "baseline" }}>
            <span style={{ color: "#b0b6c0" }}>·</span>
            <span style={{ flex: 1 }}>
              {e.label}
              {(e.pmid || e.doi || e.url) && (
                <span style={{ marginLeft: "7px", display: "inline-flex", gap: "8px" }}>
                  {e.pmid && (
                    <a href={`https://pubmed.ncbi.nlm.nih.gov/${e.pmid}/`} target="_blank" rel="noreferrer" style={{ color: "#1a5fb4", textDecoration: "none", fontSize: "11px" }}>
                      PMID {e.pmid}
                    </a>
                  )}
                  {e.doi && (
                    <a href={`https://doi.org/${e.doi}`} target="_blank" rel="noreferrer" style={{ color: "#1a5fb4", textDecoration: "none", fontSize: "11px" }}>
                      DOI
                    </a>
                  )}
                  {!e.pmid && !e.doi && e.url && (
                    <a href={e.url} target="_blank" rel="noreferrer" style={{ color: "#1a5fb4", textDecoration: "none", fontSize: "11px" }}>
                      link
                    </a>
                  )}
                </span>
              )}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}