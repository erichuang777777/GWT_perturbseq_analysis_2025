export type Call = "advance" | "validate" | "watchlist" | "deprioritize";
export type Grade = "A" | "B" | "C" | "D";
export type ConstraintTier = "high" | "moderate" | "low";

export interface ColorSet {
  label: string;
  color: string;
  bg: string;
  dot: string;
}

export interface GradeStyle {
  color: string;
  bg: string;
  border: string;
}

export type VoteStatus = "advance" | "hold" | "drop";

export interface Vote {
  reviewer: string;
  status: VoteStatus;
  note: string;
  ts: number;
}

// Figure-atlas metadata shape (still illustrative demo data — see Figures.tsx).
export interface Figure {
  id: string;
  num: string;
  title: string;
  cat: string;
  src: string;
  desc: string;
}

// ---------- real dataset shape (src/data/generated/real-dataset.json) ----------
// Produced by scripts/export_real_data.py directly from this repo's own
// target_cards.csv, readiness engine, concept-module loader, and cached
// Open Targets / ClinicalTrials.gov / PubMed / gnomAD evidence. Any field
// the source data didn't have is `null` here — never a fabricated value.

export interface RealModule {
  id: string;
  name: string;
  category: "Upstream" | "Downstream";
  seedGenes: string[];
}

export interface ConditionStat {
  condition: string;
  nTotalDeGenes: number | null;
  nUpGenes: number | null;
  nDownGenes: number | null;
  maxAbsLogFC: number | null;
  fdrMin: number | null;
  ontargetSignificant: boolean | null;
  grade: number | null;
}

export interface DiseaseAssoc {
  name: string;
  id: string;
  overallScore: number | null;
  geneticAssociationScore: number | null;
}

export interface ClinicalTrial {
  nctId: string;
  title: string;
  phase: string | null;
  status: string;
  conditions: string[];
  url: string;
}

export interface LiteratureItem {
  pmid: string;
  title: string;
  year: string;
  journal: string;
  url: string;
}

export interface Readiness {
  call: Call;
  stage: string;
  reasons: string;
  nextValidationStep: string;
  redFlags: string[];
  biologyScore: number | "unknown";
  translationScore: number | "unknown";
  translationCappedBy: string;
  tractabilityScore: number | "unknown";
  tractabilityModality: string;
  humanGeneticSupport: string;
  diseaseRelevanceScore: number | "unknown";
  clinicalFeasibilityScore: number | "unknown";
  compositeSafetyLiability: string;
  geneticSupportConfidence: string;
  hasExternalEvidence: boolean;
  // Count of GTEx tissues (Blood/Spleen excluded) where this gene clears the
  // expression threshold -- higher = more broadly expressed outside CD4
  // context = plausibly a narrower safety window. Real GTEx data for ~47%
  // of targets (sources/target_tool_cache/_overlays/gtex_per_tissue.parquet);
  // "unknown" (not 0) for the rest -- absent from the overlay, not "narrow".
  safetyWindowScore: number | "unknown";
}

// Raw ADC-derived membrane/druggability overlay flags (docs/mvp-research/
// adc_overlay_gwt_overlap_full.csv, ~50% of targets) -- a different
// vocabulary than Open Targets' tractabilityFlags (SM/AB/PR/OC buckets), so
// never merged into that field. null when the gene isn't in this overlay
// (unchecked, not "not druggable").
export interface MembraneOverlay {
  isSurfaceProtein: boolean;
  hasTransmembraneDomain: boolean;
  hasExtracellularDomain: boolean;
  isDruggable: boolean;
  druggablePathway: string | null;
}

export interface RealTarget {
  gene: string;
  name: string;
  ensembl: string | null;
  module: { id: string; name: string; category: string } | null;
  allModules: { id: string; name: string }[];
  primaryCondition: string;
  grade: Grade | null;
  gradeNum: number | null;
  effect: number | null;
  medianLogFC: number | null;
  fdr: number | null;
  nCells: number | null;
  nGuides: number | null;
  nDonors: number | null;
  nTotalDeGenes: number | null;
  nUpGenes: number | null;
  nDownGenes: number | null;
  crossDonorCorrelationMean: number | null;
  crossDonorCorrelationMin: number | null;
  replicatePassFlag: boolean | null;
  offtargetFlag: boolean | null;
  conditions: ConditionStat[];
  stimulationGated: boolean | null;
  readiness: Readiness | null;
  diseases: DiseaseAssoc[];
  tractabilityFlags: Record<string, Record<string, boolean>>;
  membraneOverlay: MembraneOverlay | null;
  safetyLiabilities: { event: string; tissues: string[] }[];
  clinicalTrials: ClinicalTrial[];
  literature: LiteratureItem[];
  gnomad: { loeuf: number | null; pli: number | null; constraintTier: ConstraintTier | null };
}

export interface RealDataset {
  sourceVersion: string;
  modules: RealModule[];
  targets: RealTarget[];
}
