import { MODULES, TARGETS } from "../data/dataset";
import { WKEYS, clusterNames } from "../data/reference";
import type { RealTarget, Vote } from "../data/types";

export type Weights = Record<string, number>;

// ---------- deterministic RNG helpers (figure atlas only — still illustrative) ----------
export function hash(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  }
  return h >>> 0;
}
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export function gauss(rand: () => number): number {
  let u = 0;
  let v = 0;
  while (u === 0) u = rand();
  while (v === 0) v = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

export const pct = (v: number): string => Math.round(v * 100) + "%";

// ---------- ① scoring: sub-scores derived from real fields + weighted composite ----------
// Every input here is a real, sourced field on RealTarget (see data/types.ts).
// The combining formula (clamps, multipliers) is a disclosed heuristic — it
// reorders the researcher's VIEW of the real evidence, exactly like the
// adjustable weights above it; it never fabricates a new fact about a gene.
export function subScores(t: RealTarget): Record<string, number> {
  const eff = t.effect ?? 0;
  const stat = Math.round(Math.max(8, Math.min(99, (Math.min(eff, 40) / 40) * 100)));

  let robust: number;
  if (t.crossDonorCorrelationMean != null) {
    robust = Math.round(Math.max(5, Math.min(99, t.crossDonorCorrelationMean * 100)));
  } else {
    robust = t.replicatePassFlag ? 50 : 20;
  }

  let safety = 60;
  safety -= (t.readiness?.redFlags.length ?? 0) * 15;
  safety -= t.safetyLiabilities.length * 10;
  if (t.offtargetFlag) safety -= 15;
  if (t.gnomad.constraintTier === "high") safety -= 10;
  if (t.gnomad.constraintTier === "low") safety += 10;
  safety = Math.round(Math.max(5, Math.min(95, safety)));

  const popgen =
    t.gnomad.constraintTier === "high" ? 88 : t.gnomad.constraintTier === "moderate" ? 60 : t.gnomad.constraintTier === "low" ? 32 : 50;

  const external = t.diseases.length ? Math.round(Math.max(...t.diseases.map((d) => d.overallScore ?? 0)) * 100) : 0;

  // Breadth (Task 3): downstream DE-gene breadth, log-scaled. 3.34 ≈ log10 of
  // the p99 breadth value (2172 genes); the clip cap keeps a handful of
  // 5,000-gene outliers from flattening the scale, and makes the 15
  // primary-outcome targets (all near the ceiling) rankable against the rest.
  const nde = t.nTotalDeGenes ?? 0;
  const breadth = Math.round(Math.max(5, Math.min(99, (Math.log10(nde + 1) / 3.34) * 94 + 5)));

  return { stat, robust, safety, popgen, external, breadth };
}

export function composite(t: RealTarget, w: Weights): number {
  const s = subScores(t);
  let numr = 0;
  let den = 0;
  WKEYS.forEach(({ k }) => {
    const wi = w[k] || 0;
    numr += wi * s[k];
    den += wi;
  });
  return den ? Math.round(numr / den) : 0;
}

export interface RankedTarget extends RealTarget {
  _rank: number;
  _comp: number;
}

export function rankedTargets(w: Weights): RankedTarget[] {
  // Primary sort by composite; ties broken by raw downstream DE-gene breadth
  // (nTotalDeGenes). The breadth sub-score is log-scaled and capped at 99, so
  // many broad targets share the ceiling — this tiebreak only reorders exact
  // composite ties, and under the Breadth-led preset it lifts the highest-DE
  // targets (the 15 primary-outcome shortlist) to the very top of the table.
  return TARGETS.map((t) => ({ t, comp: composite(t, w) }))
    .sort((a, b) => b.comp - a.comp || (b.t.nTotalDeGenes ?? 0) - (a.t.nTotalDeGenes ?? 0))
    .map((x, i) => ({ ...x.t, _rank: i + 1, _comp: x.comp }));
}

// ---------- ③ similar targets — real shared concept-module membership ----------
// No continuous cross-module profile exists in the real data (see Dossier's
// concept-profile panel), so "similar" here means "screened targets that
// share this gene's assigned module" — real membership, not a fabricated
// similarity score. Empty when the gene has no module or no module-mates.
export function similarTargets(t: RealTarget, n = 4): RealTarget[] {
  if (!t.module) return [];
  return TARGETS.filter((x) => x.gene !== t.gene && x.module?.id === t.module!.id).slice(0, n);
}

// ---------- ④ multi-reviewer decisions (unrelated to the dataset — pure vote logic) ----------
export interface Consensus {
  status: string;
  label: string;
  counts: Record<string, number>;
  split?: boolean;
  n?: number;
}
export function consensus(votes: Vote[]): Consensus {
  if (!votes.length) return { status: "none", label: "No reviews", counts: {} };
  const counts: Record<string, number> = { advance: 0, hold: 0, drop: 0 };
  votes.forEach((v) => (counts[v.status] = (counts[v.status] || 0) + 1));
  const order = ["advance", "hold", "drop"];
  const sorted = order.filter((k) => counts[k]).sort((a, b) => counts[b] - counts[a]);
  const top = sorted[0];
  const tie = sorted.length > 1 && counts[sorted[1]] === counts[top];
  return { status: tie ? "split" : top, label: tie ? "No consensus" : top, counts, split: tie, n: votes.length };
}

// ---------- figure atlas helpers (still illustrative demo data) ----------
export function geneUniverse(): { gene: string; module: string }[] {
  const seen = new Set<string>();
  const out: { gene: string; module: string }[] = [];
  MODULES.forEach((m) =>
    m.seedGenes.forEach((g) => {
      if (!seen.has(g)) {
        seen.add(g);
        out.push({ gene: g, module: m.id });
      }
    }),
  );
  return out;
}
export function clusterCenter(c: string): [number, number] {
  const names = clusterNames();
  const i = Math.max(0, names.indexOf(c));
  const n = names.length;
  const a = (2 * Math.PI * i) / n;
  return [Math.cos(a) * 5.2, Math.sin(a) * 5.2];
}

// ---------- misc formatting ----------
export const initials = (nm: string): string =>
  nm
    .split(/[\s.]+/)
    .filter(Boolean)
    .map((x) => x[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

export const fmtTs = (ts: number): string => {
  const d = new Date(ts);
  return (
    d.toLocaleDateString("en-US", { month: "short", day: "numeric" }) +
    " · " +
    d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
  );
};

export const fmtFdr = (v: number | null): string => (v == null ? "unknown" : v.toExponential(1));
export const fmtEffect = (v: number | null): string => (v == null ? "unknown" : v.toFixed(2));
