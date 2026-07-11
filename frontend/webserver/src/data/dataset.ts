import type { RealDataset, RealModule, RealTarget } from "./types";

// The one and only data source for this app: real output from this repo's
// own pipeline (target_cards.csv + readiness engine + concept modules +
// cached Open Targets / ClinicalTrials.gov / PubMed / gnomAD evidence).
// Regenerate with `python3 scripts/export_real_data.py` from the repo root.
//
// At ~7,200 genes this is ~940 KB gzipped — too large to bundle as a static
// JS import (V8 parsing a giant object literal is slower than a native
// JSON.parse of fetched text, and it can't be cached by the browser
// independently of the JS bundle). It's fetched once at app startup instead
// (see main.tsx's loadDataset() gate) and exported as live `let` bindings —
// ES module imports of `let` exports are live references, so every
// `import { TARGETS } from "./dataset"` call site elsewhere in the app sees
// the populated arrays without needing to change how they read them, as
// long as nothing reads them before loadDataset() resolves.

export let DATASET: RealDataset = { sourceVersion: "", modules: [], targets: [] };
export let SOURCE_VERSION = "";
export let MODULES: RealModule[] = [];
export let TARGETS: RealTarget[] = [];

let loadPromise: Promise<void> | null = null;

export function loadDataset(): Promise<void> {
  if (TARGETS.length > 0) return Promise.resolve();
  if (!loadPromise) {
    loadPromise = fetch(`${import.meta.env.BASE_URL}real-dataset.json`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load real-dataset.json: ${res.status}`);
        return res.json() as Promise<RealDataset>;
      })
      .then((d) => {
        DATASET = d;
        SOURCE_VERSION = d.sourceVersion;
        MODULES = d.modules;
        TARGETS = d.targets;
      });
  }
  return loadPromise;
}

export const targetByGene = (gene: string): RealTarget | undefined => TARGETS.find((t) => t.gene === gene);

export const targetsInModule = (moduleId: string): RealTarget[] =>
  TARGETS.filter((t) => t.module?.id === moduleId || t.allModules.some((m) => m.id === moduleId));
