// Minimal URL-hash sync so dossiers / clinical tabs are shareable & bookmarkable.
// Only `view`, `selectedGene` (as `gene`), and `clinicalTab` (as `ctab`) are
// synced — not weights/shortlist/filters (those live in localStorage). Format:
//   #view=dossier&gene=CD3E
//   #view=clinical&ctab=popgen
// Home view produces an empty hash to keep the URL clean.

type HashState = { view?: string; selectedGene?: string; clinicalTab?: string };

export function readHashState(): HashState {
  const h = typeof location !== "undefined" ? location.hash.replace(/^#/, "") : "";
  if (!h) return {};
  const p = new URLSearchParams(h);
  const out: HashState = {};
  const view = p.get("view");
  const gene = p.get("gene");
  const ctab = p.get("ctab");
  if (view) out.view = view;
  if (gene) out.selectedGene = gene;
  if (ctab) out.clinicalTab = ctab;
  return out;
}

export function serializeHash(view: string, selectedGene: string, clinicalTab: string): string {
  if (view === "home") return "";
  const p = new URLSearchParams();
  p.set("view", view);
  if (view === "dossier") p.set("gene", selectedGene);
  if (view === "clinical") p.set("ctab", clinicalTab);
  return "#" + p.toString();
}
