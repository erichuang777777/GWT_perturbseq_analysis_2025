// Real figure-atlas data extracted from this repo's own pipeline outputs.
// Regenerate with the Part-1 export script; see public/figures.json's
// sourceVersion for full provenance. Fetched once at app startup (see
// main.tsx's loadFigures() gate) and exported as live `let` bindings — ES
// module imports of `let` exports are live references, so every
// `import { FIGURES_DATA } from "./figuresData"` call site sees the
// populated object without needing to change how it reads it, as long as
// nothing reads it before loadFigures() resolves.

export interface FiguresData {
  sourceVersion: string;
  conditions: string[];
  cytokines: string[];
  diseases: string[];
  depths: number[];
  volcano: Record<string, { g: string; x: number; y: number }[]>;
  cytokine: Record<string, { g: string; x: number }[]>;
  polar: { g: string; x: number; y: number }[];
  heatmap: { rows: { cluster: number | string; label: string }[]; cols: string[]; z: number[][] };
  gwas: Record<string, { cluster: string; y: number }[]>;
  power: Record<string, { n_cells: number; corr: number }[]>;
}

export let FIGURES_DATA: FiguresData = {
  sourceVersion: "",
  conditions: [],
  cytokines: [],
  diseases: [],
  depths: [],
  volcano: {},
  cytokine: {},
  polar: [],
  heatmap: { rows: [], cols: [], z: [] },
  gwas: {},
  power: {},
};

let loadPromise: Promise<void> | null = null;

export function loadFigures(): Promise<void> {
  if (FIGURES_DATA.sourceVersion) return Promise.resolve();
  if (!loadPromise) {
    loadPromise = fetch(`${import.meta.env.BASE_URL}figures.json`)
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load figures.json: ${res.status}`);
        return res.json() as Promise<FiguresData>;
      })
      .then((d) => {
        FIGURES_DATA = d;
      });
  }
  return loadPromise;
}
