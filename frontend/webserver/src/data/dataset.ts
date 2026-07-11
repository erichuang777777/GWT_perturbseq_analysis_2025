import raw from "./generated/real-dataset.json";
import type { RealDataset, RealModule, RealTarget } from "./types";

// The one and only data source for this app: real output from this repo's
// own pipeline (target_cards.csv + readiness engine + concept modules +
// cached Open Targets / ClinicalTrials.gov / PubMed / gnomAD evidence).
// Regenerate with `python3 scripts/export_real_data.py` from the repo root.
export const DATASET = raw as RealDataset;

export const SOURCE_VERSION = DATASET.sourceVersion;
export const MODULES: RealModule[] = DATASET.modules;
export const TARGETS: RealTarget[] = DATASET.targets;

export const MODULES_BY_ID: Record<string, RealModule> = Object.fromEntries(MODULES.map((m) => [m.id, m]));

export const targetByGene = (gene: string): RealTarget | undefined => TARGETS.find((t) => t.gene === gene);

export const targetsInModule = (moduleId: string): RealTarget[] =>
  TARGETS.filter((t) => t.module?.id === moduleId || t.allModules.some((m) => m.id === moduleId));
