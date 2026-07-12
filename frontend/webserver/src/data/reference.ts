import type { Call, ColorSet, Figure, Grade, GradeStyle } from "./types";

// Short badge label (header/footer). Full real provenance lives in
// data/dataset.ts's SOURCE_VERSION (a live `let` export populated after
// loadDataset() resolves) -- import that directly rather than re-exporting
// it here as a `const`, which would freeze it at its pre-load empty value.
export const DATA_VERSION = "GWT-CD4 real-data v1";

export const READINESS: Record<Call, ColorSet> = {
  advance: { label: "Advance", color: "#0a6e4f", bg: "#e4f3ec", dot: "#0d7d5a" },
  validate: { label: "Validate", color: "#1f56b8", bg: "#e8f0fc", dot: "#2563c9" },
  watchlist: { label: "Watchlist", color: "#9a6510", bg: "#fbf1de", dot: "#b7791f" },
  deprioritize: { label: "Deprioritize", color: "#5b6270", bg: "#eef0f3", dot: "#8a92a0" },
};

export const GRADE: Record<Grade, GradeStyle> = {
  A: { color: "#0a6e4f", bg: "#e4f3ec", border: "#bfe4d3" },
  B: { color: "#1f56b8", bg: "#e8f0fc", border: "#c6dbf7" },
  C: { color: "#9a6510", bg: "#fbf1de", border: "#ebd7a8" },
  D: { color: "#5b6270", bg: "#eef0f3", border: "#d6dbe3" },
};

export const DECISION_META: Record<string, ColorSet> = {
  advance: { label: "Advance", color: "#0a6e4f", bg: "#e4f3ec", dot: "#0d7d5a" },
  hold: { label: "Hold", color: "#9a6510", bg: "#fbf1de", dot: "#b7791f" },
  drop: { label: "Drop", color: "#8a2f2f", bg: "#f6e5e5", dot: "#c0503f" },
  split: { label: "No consensus", color: "#5b6270", bg: "#eef0f3", dot: "#8a92a0" },
  none: { label: "Unreviewed", color: "#8a92a0", bg: "#f7f8fa", dot: "#c8ced7" },
};

export const REVIEWERS = ["A. Okafor", "R. Mehta", "L. Sørensen", "J. Park"];

export const CONSTRAINT_META: Record<string, { label: string; color: string; bg: string }> = {
  high: { label: "High constraint (LoF-intolerant)", color: "#0a6e4f", bg: "#e4f3ec" },
  moderate: { label: "Moderate constraint", color: "#9a6510", bg: "#fbf1de" },
  low: { label: "Low constraint", color: "#5b6270", bg: "#eef0f3" },
};

export const RED_FLAG_LABELS: Record<string, string> = {
  essential_gene: "Essential gene (Hart core-essentials screen)",
  broad_effect: "Broad/pleiotropic effect (chromatin-transcription machinery)",
  high_offtarget: "High off-target signal flagged",
  uncertain_direction: "Effect direction not confidently called",
  batch_confounded: "Batch-sensitive across runs",
  kd_not_measurable: "Knockdown not measurable in NTC cells",
  kd_weak: "Knockdown confirmed but weak",
};

// Weight presets re-order the researcher's VIEW of the real evidence; they
// never change the evidence itself or the (rule-based, real) readiness call.
export const WPRESETS: Record<string, Record<string, number>> = {
  Balanced: { stat: 20, robust: 20, safety: 20, popgen: 20, external: 20 },
  "Genetics-led": { stat: 15, robust: 10, safety: 15, popgen: 30, external: 30 },
  "Safety-first": { stat: 15, robust: 25, safety: 35, popgen: 15, external: 10 },
  "Signal-first": { stat: 40, robust: 25, safety: 15, popgen: 10, external: 10 },
};

export const WKEYS: { k: string; label: string; short: string; color: string }[] = [
  { k: "stat", label: "Statistical", short: "Stat", color: "#1a5fb4" },
  { k: "robust", label: "Robustness", short: "Robust", color: "#0d7d5a" },
  { k: "safety", label: "Safety", short: "Safety", color: "#b7791f" },
  { k: "popgen", label: "Pop-gen", short: "Pop-gen", color: "#6b40b8" },
  { k: "external", label: "External", short: "Extern", color: "#c0503f" },
];

// ---------- figure atlas (real data — see public/figures.json + real-dataset.json) ----------
export const FIGURES: Figure[] = [
  { id: "volcano", num: "S6", title: "Perturbation effect volcano", cat: "Differential expression", src: "3_DE_analysis/DE_results_figure.ipynb", desc: "Signed on-target knockdown effect (log2 fold-change) vs statistical significance for every perturbed gene, by culture condition — real differential-expression output. Move the FDR threshold to re-call significance." },
  { id: "umap", num: "3A", title: "Functional clustering (UMAP)", cat: "Functional interaction", src: "6_functional_interaction/cluster_plot.ipynb", desc: "A faithful functional-clustering UMAP needs 2D embedding coordinates computed from the pipeline's AnnData objects, which are not included in this repository. Real gene→cluster assignments exist (112 clusters) but not 2D positions, so this figure is intentionally not drawn rather than fabricated." },
  { id: "heatmap", num: "3B", title: "Cluster condition-specificity", cat: "Functional interaction", src: "6_functional_interaction/condition_specificity.ipynb", desc: "Real per-condition intra-cluster transcriptional correlation for each of 112 functional regulator clusters (Rest / Stim 8 hr / Stim 48 hr). Darker = more coherent co-regulation in that condition." },
  { id: "cytokine", num: "2A", title: "Cytokine regulators", cat: "Cytokine regulators", src: "5_cytokine_regulators/cytokine_regulators_overview.ipynb", desc: "The strongest positive and negative real regulators of a selected cytokine, ranked by signed knockdown effect (genome-scale signed DE table). Pick a cytokine to re-rank." },
  { id: "polar", num: "4C", title: "Th1 / Th2 polarization", cat: "Polarization signatures", src: "4_polarization_signatures/polarization_signature.ipynb", desc: "Each gene placed on the Th1↔Th2 axis by its real polarization-model coefficients (Th2 − Th1) against effect magnitude. Coefficient magnitudes are small — hover for the gene." },
  { id: "gwas", num: "7", title: "Autoimmune GWAS enrichment", cat: "Disease genetics", src: "6_functional_interaction/autoimmune_analysis/opentargets_autoimmune_analysis.ipynb", desc: "Real enrichment of autoimmune-disease GWAS genes across functional regulator clusters (Open Targets). Choose a disease; the dashed line marks nominal significance (p = 0.05)." },
  { id: "power", num: "1G", title: "Replication power", cat: "Study design", src: "3_DE_analysis/power_analysis/power_analysis.ipynb", desc: "Real held-out replication correlation of perturbation effects vs cells captured, at three sequencing depths — a reproducibility/power proxy (not a theoretical power curve). More cells → higher replication." },
  { id: "burden", num: "6", title: "Regulator–LoF burden", cat: "Population genetics", src: "8_lymphocyte_counts_LoF/lymph_reg_burden_correlation.ipynb", desc: "Real perturbation effect vs UK Biobank rare loss-of-function burden association (β) on lymphocyte count for the same gene, with a linear fit (~7,140 genes)." },
];

export const CLUSTER_MAP: Record<string, string> = {
  M01: "TCR signaling", M02: "TCR signaling", M03: "Costimulation",
  M04: "Checkpoint / Exhaustion", M18: "Checkpoint / Exhaustion",
  M05: "Cytokine–JAK/STAT", M06: "Cytokine–JAK/STAT",
  M07: "Th polarization", M08: "Th polarization", M09: "Th polarization", M10: "Th polarization",
  M11: "NF-κB / AP-1", M12: "NF-κB / AP-1",
  M13: "Metabolic", M14: "Metabolic",
  M15: "Memory / Trafficking", M16: "Memory / Trafficking", M19: "Memory / Trafficking",
  M17: "Cytotoxic-like", M20: "Cell cycle",
};

export const CLUSTER_COLORS: Record<string, string> = {
  "TCR signaling": "#2D6CBC", Costimulation: "#1f9d8a", "Checkpoint / Exhaustion": "#A8373A",
  "Cytokine–JAK/STAT": "#ff7f00", "Th polarization": "#9971AD", "NF-κB / AP-1": "#6a9a1f",
  Metabolic: "#31678e", "Memory / Trafficking": "#d98c2b", "Cytotoxic-like": "#c0503f", "Cell cycle": "#8a8f98",
};

export const clusterNames = () => Object.keys(CLUSTER_COLORS);

// No longer used by the figure atlas: the GWAS-enrichment figure's disease
// control now lists the real diseases in figures.json (FIGURES_DATA.diseases,
// via Figures.tsx). Kept only in case another view wants this short curated
// list; the Clinical tab's own disease catalog is built from real Open
// Targets associations in Clinical.tsx.
export const FIGURE_DISEASES: { key: string; name: string }[] = [
  { key: "RA", name: "Rheumatoid arthritis" },
  { key: "IBD", name: "Inflammatory bowel disease" },
  { key: "PSO", name: "Psoriasis" },
  { key: "MS", name: "Multiple sclerosis" },
  { key: "SLE", name: "Systemic lupus erythematosus" },
  { key: "T1D", name: "Type 1 diabetes" },
];
