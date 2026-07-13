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
// Every preset carries a "breadth" weight (Task 3's 6th axis): existing
// presets set it to 0, and the dedicated "Breadth-led" preset weights it
// alone so the 15 breadth-selected primary-outcome targets rise to the top.
export const WPRESETS: Record<string, Record<string, number>> = {
  Balanced: { stat: 20, robust: 20, safety: 20, popgen: 20, external: 20, breadth: 0 },
  "Genetics-led": { stat: 15, robust: 10, safety: 15, popgen: 30, external: 30, breadth: 0 },
  "Safety-first": { stat: 15, robust: 25, safety: 35, popgen: 15, external: 10, breadth: 0 },
  "Signal-first": { stat: 40, robust: 25, safety: 15, popgen: 10, external: 10, breadth: 0 },
  // Breadth alone (all other axes 0) — the axis the 15 primary-outcome
  // targets were selected on. With ties broken by raw DE-gene breadth (see
  // lib/logic.ts rankedTargets), all 15 occupy the top of the table.
  "Breadth-led": { stat: 0, robust: 0, safety: 0, popgen: 0, external: 0, breadth: 50 },
};

// Per-preset hover tooltips (Task 2 / 3).
export const WPRESET_TIPS: Record<string, string> = {
  Balanced: "Even weight across all axes (20/20/20/20/20; breadth 0) — no axis is privileged.",
  "Genetics-led": "Weights human genetics: population-genetics constraint (pop-gen) and Open Targets disease-association most heavily.",
  "Safety-first": "Weights the safety axis most heavily — surfaces targets with the fewest red flags, liabilities and constraint concerns first.",
  "Signal-first": "Weights the statistical (on-target effect-size) axis most heavily — surfaces the strongest perturbation effects first.",
  "Breadth-led": "Weights downstream DE-gene breadth alone — the axis the 15 primary-outcome targets were selected on; it floats them to the top of the table.",
};

// The 5 real sub-score axes + the new breadth axis (Task 3). `tip` is the
// exact hover definition shown in the Explorer weight panel (Task 2).
export const WKEYS: { k: string; label: string; short: string; color: string; tip: string }[] = [
  { k: "stat", label: "Statistical", short: "Stat", color: "#1a5fb4", tip: "On-target effect size (score 8–99): |log2FC| from 0–40 maps linearly onto the score; effects above 40 are capped." },
  { k: "robust", label: "Robustness", short: "Robust", color: "#0d7d5a", tip: "Cross-donor reproducibility (score 5–99): mean cross-donor correlation ×100. When correlation is missing, the replicate-pass flag substitutes (pass → 50, fail → 20)." },
  { k: "safety", label: "Safety", short: "Safety", color: "#b7791f", tip: "Descriptive safety (score 5–95): from a base of 60, −15 per pipeline red flag, −10 per Open Targets safety liability, −15 for an off-target flag, −10 for high gnomAD constraint (+10 for low)." },
  { k: "popgen", label: "Pop-gen", short: "Pop-gen", color: "#6b40b8", tip: "gnomAD LoF-constraint tier (discrete): high 88 / moderate 60 / low 32 / unknown 50. LoF-intolerance = depletion of loss-of-function variants in the population." },
  // RENAMED from "External": this axis is the Open Targets disease-ASSOCIATION
  // score, which is DISTINCT from the GWAS/STRING/HIV external revalidation
  // shown in the Dossier's External-corroboration panel. Tooltip makes that
  // distinction explicit.
  { k: "external", label: "Disease association (Open Targets)", short: "Disease assoc.", color: "#c0503f", tip: "Open Targets overall disease-association score (score 0–99): the maximum across this gene's associated diseases, ×100. This is disease-association evidence — distinct from the independent GWAS / STRING / HIV external validation shown in the Dossier's External-corroboration panel." },
  { k: "breadth", label: "Breadth", short: "Breadth", color: "#5b3fb4", tip: "Downstream DE-gene breadth (score 5–99, log-scaled): the axis the 15 primary-outcome targets were selected on. log10(nTotalDeGenes+1) scaled against the p99 breadth (≈2172 genes) and capped, so a few very-broad outliers don't flatten the scale." },
];

// ---------- figure atlas ----------
// The chart itself renders real data fetched from public/figures.json +
// real-dataset.json (see Figures.tsx and lib/drawFigure.ts) -- this is just
// the per-figure caption/title/source. "umap" has no real 2D embedding
// coordinates anywhere in this repo, so Figures.tsx shows an honest
// "unavailable" panel for it rather than fabricating positions.
export const FIGURES: Figure[] = [
  { id: "volcano", num: "S6", title: "Perturbation effect volcano", cat: "Differential expression", src: "3_DE_analysis/DE_results_figure.ipynb", desc: "Genome-scale on-target knockdown effect per gene — effect size against statistical significance, per culture condition. Positive and negative regulators separate by direction; move the FDR threshold to re-call significance." },
  { id: "heatmap", num: "3B", title: "Cluster condition-specificity", cat: "Functional interaction", src: "src/6_functional_interaction/results/clustering_condition_specificity.csv", img: "flagship/fig_condition_specificity.png", desc: "Intra-cluster correlation of each of the 112 co-regulation clusters, per culture condition. The per-condition mean is near-identical across Rest / Stim 8 hr / Stim 48 hr (0.237 / 0.239 / 0.229), so a naïve per-condition view looks flat — but per cluster the conditions diverge (45/112 span >0.15). Clusters are sorted by condition-specificity (68/112 across-condition stable; 44 condition-specific), and the right panel centers each cluster on its own mean to expose which condition each specific cluster tightens in." },
  { id: "cytokine", num: "2A", title: "Cytokine regulators", cat: "Cytokine regulators", src: "5_cytokine_regulators/cytokine_regulators_overview.ipynb", desc: "The strongest positive and negative regulators of a selected cytokine (top/bottom 12 by signed effect, among significant hits), ranked by effect. Pick a cytokine to re-rank." },
  { id: "polar", num: "4C", title: "Th1 / Th2 polarization", cat: "Polarization signatures", src: "4_polarization_signatures/polarization_signature.ipynb", desc: "Each of 3,861 genes modeled in both states, placed on the Th1↔Th2 polarization axis (Th2 − Th1 coefficient) against the magnitude of its effect. Hover for the gene." },
  { id: "gwas", num: "7", title: "Autoimmune GWAS enrichment", cat: "Disease genetics", src: "6_functional_interaction/autoimmune_analysis/opentargets_autoimmune_analysis.ipynb", desc: "Enrichment of autoimmune-disease GWAS genes across the 112 functional regulator clusters (Open Targets). Choose a disease; the dashed line marks nominal significance (-log10 P = 1.3)." },
  { id: "power", num: "1G", title: "Power analysis", cat: "Study design", src: "3_DE_analysis/power_analysis/power_analysis.ipynb", desc: "Held-out-donor replication correlation as a function of cells captured per perturbation, at three subsampled sequencing depths." },
  { id: "burden", num: "6", title: "Regulator–LoF burden", cat: "Population genetics", src: "8_lymphocyte_counts_LoF/lymph_reg_burden_correlation.ipynb", desc: "Perturbation effect against UK Biobank rare loss-of-function burden association with lymphocyte count for the same gene, with a linear fit — the only blood trait this repo has a resolved burden estimate for." },
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
