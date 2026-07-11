export type Call = "advance" | "validate" | "watchlist" | "deprioritize";
export type Grade = "A" | "B" | "C" | "D";
export type Category = "Upstream" | "Downstream";
export type Constraint = "high" | "moderate" | "low";
export type VoteStatus = "advance" | "hold" | "drop";

export interface Target {
  gene: string;
  name: string;
  mod: string;
  cat: Category;
  rank: number;
  score: number;
  call: Call;
  grade: Grade;
  effect: string;
  fdr: string;
  robustness: number;
  safety: number;
  ensembl: string;
  /** [name, efo, score] */
  diseases: [string, string, number][];
  /** [moduleId, label, activation | null] */
  concepts: [string, string, number | null][];
  safetyNote: string;
  /** [label, value] */
  pop: [string, string][];
  constraint: Constraint;
  /** [dotColor, text] */
  rationale: [string, string][];
}

export interface Module {
  name: string;
  cat: Category;
  desc: string;
  question: string;
  seeds: string[];
}

export interface Disease {
  name: string;
  efo: string;
  genes: string[];
}

export interface Drug {
  drug: string;
  phase: string;
  moa: string;
  approved: string;
  trials: Record<string, number>;
}

export interface Figure {
  id: string;
  num: string;
  title: string;
  cat: string;
  src: string;
  desc: string;
}

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

export interface Vote {
  reviewer: string;
  status: VoteStatus;
  note: string;
  ts: number;
}
