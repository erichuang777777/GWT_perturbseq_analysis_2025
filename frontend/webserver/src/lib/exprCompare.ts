// Client-side comparison of a de-identified patient expression-feature table
// against the GWT CD4 Perturb-seq reference target set. Everything here runs in
// the browser: the uploaded table never leaves the page (no fetch, no backend),
// which is why this works on the static Netlify build and satisfies the
// "uploaded data isolation" principle by construction.
//
// The clinician uploads gene-level expression FEATURES only -- a gene symbol
// plus a numeric value (e.g. log2 fold-change vs their own control, a z-score,
// or +1/-1 direction). No sample identifiers, no per-cell data, no PII. We then
// look up which of those genes are perturbation targets in the reference screen
// and surface the reference readiness call / effect / module / disease links for
// the overlap. This is an overlap lookup, NOT a validated signature classifier
// and NOT a diagnostic.

import type { RealTarget } from "../data/types";

export interface ParsedRow {
  gene: string;
  value: number | null; // null when the value column was absent/non-numeric
}

export interface ParseResult {
  rows: ParsedRow[];
  nRaw: number;
  piiColumns: string[]; // header tokens that look like identifiers -> blocked
  droppedNonGene: number;
  warnings: string[];
  ok: boolean;
}

// Header tokens that indicate the file carries identifiable / clinical fields
// rather than de-identified expression features. If any appear, we refuse to
// parse and tell the user to strip them first.
const PII_TOKENS = [
  "name", "firstname", "lastname", "surname", "patient", "patientid", "mrn",
  "medicalrecord", "ssn", "nhs", "dob", "dateofbirth", "birthdate", "birth",
  "age", "sex", "gender", "address", "postcode", "zip", "phone", "email",
  "accession", "specimen", "sampleid", "subjectid", "record", "encounter",
];

const GENE_RE = /^[A-Za-z][A-Za-z0-9._-]{0,24}$/; // permissive HGNC-ish symbol

function norm(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function splitLine(line: string): string[] {
  // comma or tab delimited; trims quotes/space
  const delim = line.includes("\t") && !line.includes(",") ? "\t" : line.includes(",") ? "," : "\t";
  return line.split(delim).map((c) => c.trim().replace(/^"(.*)"$/, "$1"));
}

export function parseExpression(text: string): ParseResult {
  const warnings: string[] = [];
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  if (lines.length === 0) {
    return { rows: [], nRaw: 0, piiColumns: [], droppedNonGene: 0, warnings: ["No data found."], ok: false };
  }

  // Detect a header row: first row whose first cell is not a gene-shaped token,
  // or which contains known column words.
  const firstCells = splitLine(lines[0]);
  const headerLooksLabelled = firstCells.some((c) => ["gene", "symbol", "value", "logfc", "log2fc", "score", "zscore", "direction", "feature"].includes(norm(c)));
  const hasHeader = headerLooksLabelled || !GENE_RE.test(firstCells[0]);

  // PII guard on the header. Match by substring so composite columns like
  // "patient_name", "date_of_birth", or "subject_age" are caught too, not just
  // exact single-word headers. The two legitimate columns (gene, value) are
  // whitelisted so a token like "age" can't false-positive on them.
  const GENE_VALUE_WORDS = new Set([
    "gene", "symbol", "genesymbol", "feature", "hgnc",
    "value", "logfc", "log2fc", "log2foldchange", "foldchange", "score", "zscore", "z", "stat", "direction",
  ]);
  const GENE_VALUE_SUBWORDS = ["gene", "symbol", "hgnc", "logfc", "foldchange", "log2"];
  const piiColumns: string[] = [];
  if (hasHeader) {
    firstCells.forEach((c) => {
      const n = norm(c);
      if (!n || GENE_VALUE_WORDS.has(n)) return;
      // a data column like "gene_name" / "gene_symbol" is legitimate even though
      // it contains the PII token "name" — skip when it names the gene/value col
      if (GENE_VALUE_SUBWORDS.some((w) => n.includes(w))) return;
      if (PII_TOKENS.some((tok) => n.includes(tok))) piiColumns.push(c);
    });
  }
  if (piiColumns.length > 0) {
    return {
      rows: [], nRaw: lines.length - 1, piiColumns, droppedNonGene: 0,
      warnings: [`Refused: the file contains columns that look like identifiers (${piiColumns.join(", ")}). Upload de-identified expression features only — a gene column and a numeric value column, nothing else.`],
      ok: false,
    };
  }

  // Locate gene + value columns
  let geneIdx = 0;
  let valIdx = 1;
  if (hasHeader) {
    const h = firstCells.map(norm);
    const gi = h.findIndex((c) => ["gene", "symbol", "genesymbol", "feature", "hgnc"].includes(c));
    const vi = h.findIndex((c) => ["value", "logfc", "log2fc", "log2foldchange", "foldchange", "score", "zscore", "z", "stat", "direction"].includes(c));
    if (gi >= 0) geneIdx = gi;
    if (vi >= 0) valIdx = vi;
    else if (firstCells.length < 2) valIdx = -1;
  }

  const body = hasHeader ? lines.slice(1) : lines;
  const rows: ParsedRow[] = [];
  const seen = new Set<string>();
  let droppedNonGene = 0;

  for (const line of body) {
    const cells = splitLine(line);
    const rawGene = cells[geneIdx] ?? "";
    const gene = rawGene.trim().toUpperCase();
    if (!gene || !GENE_RE.test(rawGene)) { droppedNonGene++; continue; }
    if (seen.has(gene)) continue; // dedupe, keep first
    seen.add(gene);
    let value: number | null = null;
    if (valIdx >= 0 && cells[valIdx] != null && cells[valIdx] !== "") {
      const v = Number(cells[valIdx]);
      value = Number.isFinite(v) ? v : null;
    }
    rows.push({ gene, value });
  }

  if (droppedNonGene > 0) warnings.push(`${droppedNonGene} row(s) did not have a valid gene symbol in the gene column and were skipped.`);
  if (rows.every((r) => r.value === null)) warnings.push("No numeric value column detected — matching on gene identity only (no directional concordance).");
  if (rows.length === 0) warnings.push("No valid gene rows parsed.");

  return { rows, nRaw: body.length, piiColumns: [], droppedNonGene, warnings, ok: rows.length > 0 };
}

export interface MatchedGene {
  gene: string;
  patientValue: number | null;
  target: RealTarget;
  call: string;         // readiness call, or "unreviewed"
  effect: number | null;
  medianLogFC: number | null;
  module: string | null;
  topDisease: string | null;
  // directional concordance between the patient's value and the perturbation's
  // downstream effect direction, only when both signs are available
  concordance: "concordant" | "opposing" | "n/a";
}

export interface CompareResult {
  matched: MatchedGene[];
  nUploaded: number;
  nMatched: number;
  byCall: Record<string, number>;   // advance/validate/watchlist/deprioritize/unreviewed
  moduleCounts: { module: string; count: number }[];
  diseaseCounts: { id: string; name: string; count: number }[];
}

const CALL_ORDER = ["advance", "validate", "watchlist", "deprioritize", "unreviewed"];

export function compareToReference(rows: ParsedRow[], targets: RealTarget[]): CompareResult {
  const byGene = new Map<string, RealTarget>();
  targets.forEach((t) => byGene.set(t.gene.toUpperCase(), t));

  const matched: MatchedGene[] = [];
  const byCall: Record<string, number> = { advance: 0, validate: 0, watchlist: 0, deprioritize: 0, unreviewed: 0 };
  const moduleMap = new Map<string, number>();
  const diseaseMap = new Map<string, { name: string; count: number }>();

  for (const r of rows) {
    const t = byGene.get(r.gene);
    if (!t) continue;
    const call = t.readiness?.call ?? "unreviewed";
    byCall[call] = (byCall[call] ?? 0) + 1;

    const mod = t.module ? t.module.id : null;
    if (mod) moduleMap.set(mod, (moduleMap.get(mod) ?? 0) + 1);

    const topDis = (t.diseases && t.diseases.length)
      ? [...t.diseases].sort((a, b) => (b.overallScore ?? 0) - (a.overallScore ?? 0))[0]
      : null;
    if (topDis) {
      const e = diseaseMap.get(topDis.id) ?? { name: topDis.name, count: 0 };
      e.count++; diseaseMap.set(topDis.id, e);
    }

    // Directional concordance: patient value sign vs perturbation median logFC
    // sign. Interpreted only as a coarse same/opposite direction flag.
    let concordance: MatchedGene["concordance"] = "n/a";
    if (r.value != null && r.value !== 0 && t.medianLogFC != null && t.medianLogFC !== 0) {
      concordance = Math.sign(r.value) === Math.sign(t.medianLogFC) ? "concordant" : "opposing";
    }

    matched.push({
      gene: t.gene,
      patientValue: r.value,
      target: t,
      call,
      effect: t.effect ?? null,
      medianLogFC: t.medianLogFC ?? null,
      module: mod,
      topDisease: topDis ? topDis.name : null,
      concordance,
    });
  }

  // sort matched: by call priority, then by |effect| desc
  matched.sort((a, b) => {
    const ca = CALL_ORDER.indexOf(a.call), cb = CALL_ORDER.indexOf(b.call);
    if (ca !== cb) return ca - cb;
    return (Math.abs(b.effect ?? 0)) - (Math.abs(a.effect ?? 0));
  });

  const moduleCounts = [...moduleMap.entries()].map(([module, count]) => ({ module, count })).sort((a, b) => b.count - a.count);
  const diseaseCounts = [...diseaseMap.entries()].map(([id, v]) => ({ id, name: v.name, count: v.count })).sort((a, b) => b.count - a.count).slice(0, 12);

  return {
    matched,
    nUploaded: rows.length,
    nMatched: matched.length,
    byCall,
    moduleCounts,
    diseaseCounts,
  };
}
