// Portal ships English-only (delivery requirement). The gallery previously
// carried a zh translation table and a language switcher; both were removed so
// the rendered UI is guaranteed single-language English. `Lang` is retained as
// a one-member union so the chart/structure accessors stay type-safe.
export type Lang = "en";

export const T = {
  en: {
    heading: "Figure & structure gallery",
    sub: "Every rendered figure and predicted protein structure from this repo's pipeline, each stamped with the underlying data source. Descriptive reference material — it never feeds the readiness call.",
    figures: "Figures",
    structures: "Protein structures",
    allFamilies: "All families",
    source: "Data source",
    plddt: "Mean pLDDT",
    length: "Length",
    topology: "Topology",
    tm: "TM segments",
    residues: "aa",
    noStruct: "No AlphaFold model available for this protein.",
    openAF: "Open in AlphaFold DB",
    downloadCif: "Download structure (.cif)",
    topologyPlot: "Transmembrane topology (Protter)",
    structNote: "Predicted model (AlphaFold). pLDDT is a per-residue confidence score, not an experimental measurement.",
  },
} as const;

export function plddtColor(v: number | null): string {
  if (v == null) return "#9aa1ad";
  if (v >= 90) return "#0d7d5a";
  if (v >= 70) return "#3a7bd5";
  if (v >= 50) return "#c68a1a";
  return "#c0603a";
}
