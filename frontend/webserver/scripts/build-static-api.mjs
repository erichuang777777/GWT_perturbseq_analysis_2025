// Pre-generate a real, static, read-only JSON API from the built real dataset.
// Runs after `vite build` (see package.json "build"). Writes dist/api/v1/*.json
// — pure build artifacts (dist/ is gitignored), served directly by Netlify's CDN
// as a same-origin, zero-compute, read-only, GET-by-id JSON API (no auth).
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");                       // frontend/webserver
const SRC = join(ROOT, "public", "real-dataset.json");
const OUT = join(ROOT, "dist", "api", "v1");

const raw = JSON.parse(readFileSync(SRC, "utf8"));
const targets = raw.targets;

if (existsSync(OUT)) rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });

const write = (relPath, obj) => {
  const full = join(OUT, relPath);
  mkdirSync(dirname(full), { recursive: true });
  writeFileSync(full, JSON.stringify(obj));
};
const safe = (s) => String(s).replace(/[^A-Za-z0-9_.-]/g, "_");

// meta
write("meta.json", {
  sourceVersion: raw.sourceVersion,
  generatedAt: raw.generatedAt,
  counts: { targets: targets.length, modules: raw.modules.length },
  endpoints: [
    "/api/v1/meta.json",
    "/api/v1/targets.json",
    "/api/v1/targets/{gene}.json",
    "/api/v1/diseases.json",
    "/api/v1/diseases/{sanitizedId}/targets.json",
    "/api/v1/popgen/{gene}.json",
  ],
  note: "Real, static, read-only API generated at build time from this repo's own pipeline output. Same origin, no auth, by-id GET. Regenerated on each deploy.",
});

// targets index (slim)
write("targets.json", {
  sourceVersion: raw.sourceVersion,
  count: targets.length,
  targets: targets.map((t) => ({
    gene: t.gene,
    name: t.name,
    module: t.module ? { id: t.module.id, name: t.module.name } : null,
    grade: t.grade,
    gradeNum: t.gradeNum,
    effect: t.effect,
    fdr: t.fdr,
    readinessCall: t.readiness ? t.readiness.call : null,
    readinessStage: t.readiness ? t.readiness.stage : null,
    primaryCondition: t.primaryCondition,
    href: `/api/v1/targets/${t.gene}.json`,
  })),
});

// per-target full record + per-gene popgen
for (const t of targets) {
  write(`targets/${safe(t.gene)}.json`, { sourceVersion: raw.sourceVersion, target: t });
  write(`popgen/${safe(t.gene)}.json`, {
    sourceVersion: raw.sourceVersion,
    gene: t.gene,
    gnomad: t.gnomad,
    populationBurden: t.populationBurden,
  });
}

// diseases aggregate + per-disease target lists
const byDisease = new Map();
for (const t of targets) {
  for (const d of t.diseases || []) {
    if (!d.id) continue;
    if (!byDisease.has(d.id)) byDisease.set(d.id, { id: d.id, name: d.name, targets: [] });
    byDisease.get(d.id).targets.push({ gene: t.gene, name: t.name, overallScore: d.overallScore, source: d.source });
  }
}
const diseaseIndex = [];
for (const { id, name, targets: dts } of byDisease.values()) {
  const sid = safe(id);
  dts.sort((a, b) => (b.overallScore ?? 0) - (a.overallScore ?? 0));
  write(`diseases/${sid}/targets.json`, { sourceVersion: raw.sourceVersion, disease: { id, name }, count: dts.length, targets: dts });
  diseaseIndex.push({ id, name, nTargets: dts.length, href: `/api/v1/diseases/${sid}/targets.json` });
}
diseaseIndex.sort((a, b) => b.nTargets - a.nTargets);
write("diseases.json", { sourceVersion: raw.sourceVersion, count: diseaseIndex.length, diseases: diseaseIndex });

console.log(`Static API -> dist/api/v1: ${targets.length} targets, ${diseaseIndex.length} diseases, ~${3 + targets.length * 2 + diseaseIndex.length} files`);
