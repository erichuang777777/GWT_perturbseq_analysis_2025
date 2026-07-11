import type {
  Call,
  ColorSet,
  Disease,
  Drug,
  Figure,
  Grade,
  GradeStyle,
  Module,
} from "./types";

export const DATA_VERSION = "GWT-CD4 v2026.1";

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

export const MODULES: Record<string, Module> = {
  M01: { name: "TCR_Core_Receptor", cat: "Upstream", desc: "The TCR core receptor complex (CD3 chains + TRBC) — the most upstream initiation point of the CD4 activation signal. Governs whether the activation threshold can be reshaped.", question: "Can CD4 TCR initiation signalling reshape the activation threshold?", seeds: ["CD3D", "CD3E", "CD3G", "CD247", "TRBC1", "TRBC2"] },
  M02: { name: "TCR_Proximal_Signaling", cat: "Upstream", desc: "The proximal TCR signalling chain — a node-dense stretch of kinases and adaptors immediately downstream of receptor engagement, rich in druggable checkpoints.", question: "Which early TCR-downstream nodes behave as druggable regulatory points?", seeds: ["LCK", "FYN", "ZAP70", "LAT", "LCP2", "PLCG1", "ITK", "VAV1", "CARD11", "BCL10", "MALT1"] },
  M03: { name: "Costimulation", cat: "Upstream", desc: "The costimulatory axis (CD28/ICOS and ligands) that sets how activation and proliferation programs are re-wired after receptor engagement.", question: "Does costimulation drive reconfiguration of the proliferation/activation program?", seeds: ["CD28", "ICOS", "GRB2", "PIK3R1", "TRAT1", "CD80", "CD86"] },
  M04: { name: "Checkpoint_Module", cat: "Upstream", desc: "Inhibitory checkpoint receptors balancing immune suppression against activation — assessed for reversible or enhanceable signalling.", question: "Does the inhibitory axis show reversible / enhanceable signal?", seeds: ["CTLA4", "PDCD1", "TIGIT", "LAG3", "ICOS", "CD40", "CD40LG"] },
  M05: { name: "IL2R_JAKSTAT", cat: "Upstream", desc: "The IL-2 receptor / JAK-STAT survival and proliferation loop — a key branch point between Treg and effector fates.", question: "Is the IL-2 survival & proliferation loop reset by perturbation?", seeds: ["IL2RA", "IL2RB", "JAK1", "JAK3", "STAT5A", "STAT5B"] },
  M06: { name: "IFN_Response", cat: "Upstream", desc: "Interferon response axis (type I/II receptors + STAT1/IRF) capturing inflammatory-stimulus sensitivity.", question: "Is inflammatory-stimulus sensitivity amplified or dampened?", seeds: ["IFNAR1", "IFNAR2", "IFNGR1", "IFNGR2", "STAT1", "IRF1", "IRF9"] },
  M07: { name: "Th1_Polarization", cat: "Downstream", desc: "The master transcriptional program for Th1 differentiation.", question: "Does perturbation drive a Th1-like transcriptomic shift?", seeds: ["TBX21", "IFNG", "IRF1", "EOMES", "STAT4", "CXCR3"] },
  M08: { name: "Th2_Polarization", cat: "Downstream", desc: "The Th2 differentiation program (GATA3/STAT6 axis + IL4/IL13 effectors).", question: "Does perturbation drive a Th2-like skew?", seeds: ["GATA3", "IL4", "IL13", "IL4R", "STAT6", "IRF4"] },
  M09: { name: "Th17_Polarization", cat: "Downstream", desc: "The Th17 inflammatory differentiation program (RORC/STAT3 axis + IL17 effectors) — common in chronic autoimmune inflammation.", question: "Does perturbation drive a Th17-like inflammatory program?", seeds: ["RORC", "IL17A", "IL17F", "IL23R", "STAT3", "CCR6"] },
  M10: { name: "Treg_Modulation", cat: "Downstream", desc: "The regulatory-T tolerance / suppression program.", question: "Is the tolerance/suppression axis altered?", seeds: ["FOXP3", "IKZF2", "CTLA4", "IL2RA", "TGFB1", "TGFB2"] },
  M11: { name: "NFkB_Axis", cat: "Downstream", desc: "The NF-κB inflammatory signal-amplification axis.", question: "Is innate/inflammatory signal amplification altered?", seeds: ["NFKB1", "RELA", "IKBKB", "TRAF2", "TNFRSF1A", "REL"] },
  M12: { name: "AP1_NFAT_Activation", cat: "Downstream", desc: "AP-1 / NFAT immediate-early activation response — a directionality sanity check for perturbations.", question: "Do immediate-early activation responses shift in concert?", seeds: ["FOS", "JUN", "FOSB", "FOSL2", "NR4A1", "NR4A2", "NFATC1", "NFATC2"] },
  M13: { name: "PI3K_AKT_mTOR", cat: "Upstream", desc: "The PI3K-AKT-mTOR metabolic / proliferation signalling axis.", question: "Are metabolic and proliferation signals rewritten?", seeds: ["PIK3CD", "PIK3R1", "MTOR", "RPTOR", "AKT1"] },
  M14: { name: "Metabolic_Switch", cat: "Downstream", desc: "The activation-coupled metabolic reprogramming (MYC/HIF1A/glycolysis).", question: "Does metabolic reprogramming track with activation?", seeds: ["MYC", "SLC2A1", "HIF1A", "CCND3", "RPS6KB1"] },
  M15: { name: "Maturation_Memory_Trafficking", cat: "Downstream", desc: "Naive/memory homing and lymphoid-tissue positioning program.", question: "Is the naive/memory homing profile preserved?", seeds: ["CCR7", "SELL", "LTB", "S1PR1", "IL7R"] },
  M16: { name: "Chemotaxis_Tissue_Infiltration", cat: "Downstream", desc: "Chemotaxis and tissue-infiltration program.", question: "Are migration / tissue-positioning programs altered?", seeds: ["CXCR3", "CXCR4", "CCR5", "CCR6", "XCL1", "XCL2"] },
  M17: { name: "Cytotoxic_Like_Differentiation", cat: "Downstream", desc: "Atypical CD4 cytotoxic / effector-like program.", question: "Does perturbation bias toward effector-like cytotoxic programs?", seeds: ["GZMB", "PRF1", "NKG7", "FAS", "FASLG", "IFNG"] },
  M18: { name: "Exhaustion_Escape", cat: "Downstream", desc: "T-cell exhaustion / escape program (TOX-driven + inhibitory receptors) — used in safety and therapeutic-window assessment.", question: "Does prolonged stimulation induce exhaustion or reversible suppression?", seeds: ["PDCD1", "HAVCR2", "LAG3", "TOX", "ENTPD1"] },
  M19: { name: "Memory_Fate_Program", cat: "Downstream", desc: "Memory-fate / plasticity transcriptional and chromatin program.", question: "Are fate plasticity and stability changed?", seeds: ["TCF7", "BCL11B", "RUNX3", "BACH2", "SMARCA4", "ARID1A"] },
  M20: { name: "Cell_Cycle_Proliferation", cat: "Downstream", desc: "Cell-cycle / proliferation marker program — a non-specific-proliferation sanity check.", question: "Does perturbation mainly drive proliferation rather than a specific immune pathway?", seeds: ["MKI67", "TOP2A", "MCM7", "PCNA", "TYMS"] },
};

export const DISEASES: Record<string, Disease> = {
  RA: { name: "Rheumatoid arthritis", efo: "EFO_0000685", genes: ["IL2RA", "CTLA4", "STAT3", "PLCG1"] },
  IBD: { name: "Inflammatory bowel disease", efo: "EFO_0003767", genes: ["RORC", "STAT3", "JAK3", "TIGIT"] },
  PSO: { name: "Psoriasis", efo: "EFO_0000676", genes: ["RORC", "STAT3", "TIGIT", "ITK"] },
  MS: { name: "Multiple sclerosis", efo: "EFO_0003885", genes: ["IL2RA", "CTLA4", "LAG3", "TBX21IRF"] },
  SLE: { name: "Systemic lupus erythematosus", efo: "EFO_0002690", genes: ["PLCG1", "ITK", "STAT3", "PDCD1"] },
  T1D: { name: "Type 1 diabetes", efo: "EFO_0001359", genes: ["CTLA4", "IL2RA", "PTPN22FOX", "FOXP3"] },
};

// Illustrative disease-agnostic drug lists per gene; trials keyed by disease code.
// A nonzero count only means trials exist for THAT disease. Empty [] = gene resolves but no matchable drugs.
export const DRUGS: Record<string, Drug[]> = {
  IL2RA: [
    { drug: "Basiliximab", phase: "Approved", moa: "Anti-CD25 (IL2RA) mAb", approved: "Kidney-transplant rejection", trials: {} },
    { drug: "Daclizumab", phase: "Withdrawn", moa: "Anti-CD25 (IL2RA) mAb", approved: "Multiple sclerosis (withdrawn 2018)", trials: { MS: 11 } },
  ],
  CTLA4: [
    { drug: "Abatacept", phase: "Approved", moa: "CTLA4-Ig fusion (co-stimulation blocker)", approved: "Rheumatoid arthritis, PsA, JIA", trials: { RA: 63, PSO: 5, T1D: 6 } },
    { drug: "Belatacept", phase: "Approved", moa: "CTLA4-Ig fusion", approved: "Kidney-transplant rejection", trials: {} },
  ],
  JAK3: [
    { drug: "Tofacitinib", phase: "Approved", moa: "JAK1/JAK3 inhibitor", approved: "RA, ulcerative colitis, PsA, AS", trials: { RA: 44, IBD: 23, PSO: 8 } },
    { drug: "Decernotinib", phase: "Phase 2", moa: "JAK3-selective inhibitor", approved: "Investigational", trials: { RA: 5 } },
  ],
  PDCD1: [
    { drug: "Nivolumab", phase: "Approved", moa: "Anti-PD-1 mAb (checkpoint inhibitor)", approved: "Oncology (melanoma, NSCLC, …)", trials: {} },
    { drug: "Pembrolizumab", phase: "Approved", moa: "Anti-PD-1 mAb (checkpoint inhibitor)", approved: "Oncology (multiple)", trials: {} },
  ],
  TIGIT: [{ drug: "Tiragolumab", phase: "Phase 3", moa: "Anti-TIGIT mAb", approved: "Investigational (oncology)", trials: {} }],
  LAG3: [{ drug: "Relatlimab", phase: "Approved", moa: "Anti-LAG-3 mAb", approved: "Melanoma (with nivolumab)", trials: {} }],
  RORC: [{ drug: "RORγt inverse agonists (e.g. JTE-451)", phase: "Phase 2", moa: "RORγt inverse agonist", approved: "Investigational", trials: { PSO: 4 } }],
  ITK: [{ drug: "Ibrutinib (off-target ITK)", phase: "Approved", moa: "BTK / ITK inhibitor", approved: "B-cell malignancies", trials: {} }],
  STAT3: [],
  FOXP3: [],
  PLCG1: [],
  ZAP70: [],
};

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
