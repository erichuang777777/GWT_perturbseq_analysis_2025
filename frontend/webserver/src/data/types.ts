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
  // When set, this figure is a static, pipeline-rendered PNG (public/) shown
  // in place of the interactive chart — used for 3B, whose informative view
  // (a sorted 112-cluster heatmap + Δ-from-mean panel) is a real computed
  // figure rather than an interactive trace.
  img?: string;
}

// ---------- real dataset shape (public/real-dataset.json) ----------
// Fetched at runtime by dataset.ts's loadDataset() from the app's BASE_URL
// (Vite serves public/ at the site root) -- not statically imported, so it
// never gets bundled into the JS payload. Produced by
// scripts/export_real_data.py directly from this repo's own
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

// PubMed novelty descriptor (plan P0-E). null when no literature count was
// measured for this gene (unknown != 0). `tier`: no_record | understudied |
// moderate | well_studied. `noveltyScore` in (0,1], HIGHER = more novel
// (fewer papers). Descriptive only — never feeds the readiness call.
export interface Novelty {
  tier: "no_record" | "understudied" | "moderate" | "well_studied";
  literatureCount: number;
  noveltyScore: number;
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
}

// Real UK Biobank exome-wide rare-LoF-variant lymphocyte-count burden
// (Backman et al. 2021) -- a population-level statistical association, zero
// network calls, ~98.5% of targets. Independent of gnomAD's constraint
// signal: gnomAD says how tolerant the population is to losing the gene;
// this says what actually happens to lymphocyte count when it's lost.
export interface PopulationBurden {
  trait: string;
  effectEstimate: number | null;
  ci95Lower: number | null;
  ci95Upper: number | null;
  ciExcludesZero: boolean;
  direction: "higher" | "lower";
  hypothesis: string;
  caveat: string;
}

// ---------- per-target external corroboration (Level-4 revalidation) ----------
// Three orthogonal, independent external sources, joined per target by the
// export script from docs/mvp-research/level4_external_validation/. Any track
// with no row for a gene is `null` (honest "no external hit", never a
// fabricated 0); a gene absent from all three has externalEvidence: null.
//   gwas   — Open Targets GWAS genetic-association re-check (55 targets)
//   string — STRING known-partner recovery in the CD4 downstream set (15)
//   hiv    — GEO GSE318876 independent CRISPRa/n HIV screen concordance (1,235)
export interface GwasEvidence {
  topImmuneDisease: string | null;
  topImmuneGAScore: number | null;
  topAnyDisease: string | null;
  topAnyGAScore: number | null;
  nImmuneGeneticAssoc: number | null;
  classicAutoimmuneHit: string | null;
  hasClassicAutoimmune: boolean | null;
  footprintClass: string | null;
}
export interface StringEvidence {
  group: string | null;
  nKnownPartners: number | null;
  nInDownstream: number | null;
  nDownstreamTotal: number | null;
  recoveryFrac: number | null;
}
export interface HivEvidence {
  hivHitClass: string | null;
  bestLfc: number | null;
  screen: string | null;
  bestDir: string | null;
  inLibrary: boolean | null;
  inVal55: boolean | null;
  movesInUninfected: boolean | null;
}
export interface ExternalEvidence {
  gwas: GwasEvidence | null;
  string: StringEvidence | null;
  hiv: HivEvidence | null;
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
  safetyLiabilities: { event: string; tissues: string[] }[];
  clinicalTrials: ClinicalTrial[];
  literature: LiteratureItem[];
  novelty: Novelty | null;
  gnomad: { loeuf: number | null; pli: number | null; constraintTier: ConstraintTier | null };
  populationBurden: PopulationBurden | null;
  // Per-target external corroboration; null when the gene is in none of the
  // three Level-4 tracks. See ExternalEvidence above.
  externalEvidence: ExternalEvidence | null;
  // The 15 breadth-selected primary-outcome targets (server headline result).
  primaryOutcome: boolean;
  primaryOutcomeRank: number | null;
}

export interface RealDataset {
  sourceVersion: string;
  modules: RealModule[];
  targets: RealTarget[];
}
