import type { Call, ColorSet, Figure, Grade, GradeStyle } from "./types";
import { SOURCE_VERSION } from "./dataset";

// Short badge label (header/footer). Full real provenance lives in SOURCE_VERSION.
export const DATA_VERSION = "GWT-CD4 real-data v1";
export const DATASET_SOURCE = SOURCE_VERSION;

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

// ---------- figure atlas (still illustrative — see Figures.tsx caption) ----------
export const FIGURES: Figure[] = [
  { id: "volcano", num: "S6", title: "Trans-effect volcano", cat: "Differential expression", src: "3_DE_analysis/DE_results_figure.ipynb", desc: "Genome-scale perturbation trans-effects — effect size against statistical significance. Positive and negative regulators separate by direction; move the FDR threshold to re-call significance." },
  { id: "umap", num: "3A", title: "Functional clustering (UMAP)", cat: "Functional interaction", src: "6_functional_interaction/cluster_plot.ipynb", desc: "Regulators embedded by downstream transcriptional similarity and grouped into functional clusters. Hover any point for its gene; highlight one cluster to isolate a program." },
  { id: "heatmap", num: "3B", title: "Regulator × program heatmap", cat: "Functional interaction", src: "6_functional_interaction/condition_specificity.ipynb", desc: "Perturbation effect of each top regulator on downstream transcriptional programs, on a diverging blue–red (vlag) scale. Switch culture condition to see context specificity." },
  { id: "cytokine", num: "2A", title: "Cytokine regulators", cat: "Cytokine regulators", src: "5_cytokine_regulators/cytokine_regulators_overview.ipynb", desc: "The strongest positive and negative regulators of a selected cytokine, ranked by effect. Pick a cytokine to re-rank." },
  { id: "polar", num: "4C", title: "Th1 / Th2 polarization", cat: "Polarization signatures", src: "4_polarization_signatures/polarization_signature.ipynb", desc: "Each perturbation placed on the Th1↔Th2 polarization axis against the magnitude of its effect. Hover for the gene." },
  { id: "gwas", num: "7", title: "Autoimmune GWAS enrichment", cat: "Disease genetics", src: "6_functional_interaction/autoimmune_analysis/opentargets_autoimmune_analysis.ipynb", desc: "Enrichment of autoimmune-disease GWAS genes across functional regulator clusters (Open Targets). Choose a disease; the dashed line marks nominal significance." },
  { id: "power", num: "1G", title: "Power analysis", cat: "Study design", src: "3_DE_analysis/power_analysis/power_analysis.ipynb", desc: "Detection power as a function of cells captured per perturbation, for a range of true effect sizes. Dashed line marks 80% power." },
  { id: "burden", num: "6", title: "Regulator–LoF burden", cat: "Population genetics", src: "8_lymphocyte_counts_LoF/lymph_reg_burden_correlation.ipynb", desc: "Perturbation effect on a blood-trait signature against rare loss-of-function burden association for the same gene, with a linear fit. Switch the trait to re-fit." },
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

// Small illustrative disease list for the figure atlas's GWAS-enrichment demo
// control only (that figure's whole series is synthetic — see Figures.tsx
// caption). Not used anywhere real data is shown; the Clinical tab's disease
// catalog is built from real Open Targets associations in Clinical.tsx.
export const FIGURE_DISEASES: { key: string; name: string }[] = [
  { key: "RA", name: "Rheumatoid arthritis" },
  { key: "IBD", name: "Inflammatory bowel disease" },
  { key: "PSO", name: "Psoriasis" },
  { key: "MS", name: "Multiple sclerosis" },
  { key: "SLE", name: "Systemic lupus erythematosus" },
  { key: "T1D", name: "Type 1 diabetes" },
];
