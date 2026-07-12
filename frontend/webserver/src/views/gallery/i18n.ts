export type Lang = "en" | "zh";

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
  zh: {
    heading: "圖表與結構圖庫",
    sub: "本專案流程產生的每一張圖表與預測蛋白結構，皆標註其底層資料來源。此為描述性參考資料，不參與 readiness 判定。",
    figures: "圖表",
    structures: "蛋白結構",
    allFamilies: "全部類別",
    source: "資料來源",
    plddt: "平均 pLDDT",
    length: "長度",
    topology: "拓撲",
    tm: "跨膜區段",
    residues: "個胺基酸",
    noStruct: "此蛋白無 AlphaFold 預測模型。",
    openAF: "在 AlphaFold DB 開啟",
    downloadCif: "下載結構檔 (.cif)",
    topologyPlot: "跨膜拓撲圖 (Protter)",
    structNote: "AlphaFold 預測模型。pLDDT 為每殘基信心分數，非實驗量測值。",
  },
} as const;

export function plddtColor(v: number | null): string {
  if (v == null) return "#9aa1ad";
  if (v >= 90) return "#0d7d5a";
  if (v >= 70) return "#3a7bd5";
  if (v >= 50) return "#c68a1a";
  return "#c0603a";
}
