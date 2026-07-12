import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { WPRESETS } from "../data/reference";
import type { Vote, VoteStatus } from "../data/types";
import type { Weights } from "../lib/logic";
import { readHashState, serializeHash } from "../lib/urlState";

export type View =
  | "home"
  | "explorer"
  | "dossier"
  | "clinical"
  | "compare"
  | "figures"
  | "apidocs";

export interface AppState {
  view: View;
  query: string;
  selectedGene: string;
  readinessSel: Record<string, boolean>;
  gradeSel: Record<string, boolean>;
  categorySel: Record<string, boolean>;
  weights: Weights;
  weightPreset: string;
  shortlist: string[];
  decisions: Record<string, Vote[]>;
  reviewer: string;
  decisionFilter: string;
  navStack: Partial<AppState>[];
  clinicalTab: string;
  selectedConcept: string;
  selectedDisease: string;
  popQuery: string;
  sampleText: string;
  drugGene: string;
  drugDisease: string;
  figureId: string;
  figCondition: string;
  figThresh: number;
  figCluster: string;
  figCytokine: string;
  figDisease: string;
  figTrait: string;
}

// ---------- localStorage layer (cd4portal.*) ----------
function lsGet<T>(key: string, def: T): T {
  try {
    const v = localStorage.getItem("cd4portal." + key);
    return v == null ? def : (JSON.parse(v) as T);
  } catch {
    return def;
  }
}
function lsSet(key: string, val: unknown) {
  try {
    localStorage.setItem("cd4portal." + key, JSON.stringify(val));
  } catch {
    /* ignore */
  }
}

function initialState(): AppState {
  const savedPreset = lsGet<string>("weightPreset", "Balanced");
  const savedWeights = lsGet<Weights>("weights", WPRESETS[savedPreset] || WPRESETS.Balanced);
  const base: AppState = {
    view: "home",
    query: "",
    selectedGene: "PLCG1",
    readinessSel: {},
    gradeSel: {},
    categorySel: {},
    weights: savedWeights,
    weightPreset: savedPreset,
    shortlist: lsGet<string[]>("shortlist", []),
    decisions: lsGet<Record<string, Vote[]>>("decisions", {}),
    reviewer: lsGet<string>("reviewer", "A. Okafor"),
    decisionFilter: "all",
    navStack: [],
    clinicalTab: "scope",
    selectedConcept: "M02",
    // "" = Clinical.tsx picks the top real disease from the catalog it builds
    // from actual Open Targets associations (see diseaseCatalog there).
    selectedDisease: "",
    popQuery: "IL2RA",
    sampleText: "",
    drugGene: "IL2RA",
    drugDisease: "",
    figureId: "volcano",
    figCondition: "Stim8hr",
    figThresh: 2,
    figCluster: "all",
    figCytokine: "IFNG",
    figDisease: "RA",
    figTrait: "Lymphocyte count",
  };
  return { ...base, ...readHashState() } as AppState;
}

type Updater = Partial<AppState> | ((s: AppState) => Partial<AppState>);

export interface Store {
  state: AppState;
  setState: (u: Updater) => void;
  // actions
  setWeight: (k: string, v: number) => void;
  applyPreset: (name: string) => void;
  navTo: (kind: "gene" | "concept" | "module" | "popgen" | "disease", id: string) => void;
  navBack: () => void;
  inShortlist: (g: string) => boolean;
  toggleShortlist: (g: string) => void;
  clearShortlist: () => void;
  votesFor: (g: string) => Vote[];
  myVote: (g: string) => Vote | null;
  castVote: (g: string, status: VoteStatus, note?: string) => void;
  setVoteNote: (g: string, note: string) => void;
  clearMyVote: (g: string) => void;
  setReviewer: (r: string) => void;
}

const StoreContext = createContext<Store | null>(null);

export function StoreProvider({ children }: { children: ReactNode }) {
  const [state, setStateRaw] = useState<AppState>(initialState);
  const ref = useRef(state);
  ref.current = state;

  const setState = useCallback((u: Updater) => {
    setStateRaw((s) => ({ ...s, ...(typeof u === "function" ? u(s) : u) }));
  }, []);

  // persist the cd4portal.* keys whenever they change
  useEffect(() => {
    lsSet("weights", state.weights);
  }, [state.weights]);
  useEffect(() => {
    lsSet("weightPreset", state.weightPreset);
  }, [state.weightPreset]);
  useEffect(() => {
    lsSet("shortlist", state.shortlist);
  }, [state.shortlist]);
  useEffect(() => {
    lsSet("decisions", state.decisions);
  }, [state.decisions]);
  useEffect(() => {
    lsSet("reviewer", state.reviewer);
  }, [state.reviewer]);

  // Sync a minimal slice of navigation state to the URL hash (shareable links).
  useEffect(() => {
    const target = serializeHash(state.view, state.selectedGene, state.clinicalTab);
    if (target !== location.hash && !(target === "" && !location.hash)) {
      if (target === "") {
        // clear hash without adding a history entry cluttered with "#"
        history.replaceState(null, "", location.pathname + location.search);
      } else {
        location.hash = target; // pushes a history entry + fires hashchange
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.view, state.selectedGene, state.clinicalTab]);

  // Back/forward: re-read the hash and apply it (guarded so it can't loop with
  // the write effect above — only setState when a synced field actually differs).
  useEffect(() => {
    const onHash = () => {
      const h = readHashState();
      const nextView = (h.view as AppState["view"]) ?? "home";
      setStateRaw((s) => {
        const nextGene = h.selectedGene ?? s.selectedGene;
        const nextTab = h.clinicalTab ?? s.clinicalTab;
        if (s.view === nextView && s.selectedGene === nextGene && s.clinicalTab === nextTab) return s;
        return { ...s, view: nextView, selectedGene: nextGene, clinicalTab: nextTab };
      });
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const store = useMemo<Store>(() => {
    const votesFor = (g: string): Vote[] => ref.current.decisions[g] || [];
    const myVote = (g: string): Vote | null =>
      votesFor(g).find((v) => v.reviewer === ref.current.reviewer) || null;

    return {
      state,
      setState,
      setWeight: (k, v) =>
        setState((s) => ({ weights: { ...s.weights, [k]: v }, weightPreset: "Custom" })),
      applyPreset: (name) => setState({ weights: { ...WPRESETS[name] }, weightPreset: name }),
      navTo: (kind, id) => {
        setState((s) => {
          const snap: Partial<AppState> = {
            view: s.view,
            selectedGene: s.selectedGene,
            selectedConcept: s.selectedConcept,
            clinicalTab: s.clinicalTab,
            drugDisease: s.drugDisease,
            popQuery: s.popQuery,
          };
          let next: Partial<AppState> | null = null;
          if (kind === "gene") next = { view: "dossier", selectedGene: id };
          else if (kind === "concept" || kind === "module")
            next = { view: "clinical", clinicalTab: "concept", selectedConcept: id };
          else if (kind === "popgen")
            next = { view: "clinical", clinicalTab: "popgen", popQuery: id };
          else if (kind === "disease") {
            // id is a real disease id (e.g. a MONDO id) from a target's own
            // `diseases` array — Clinical.tsx's catalog is built from the
            // same real data, so this always resolves to a real entry.
            next = { view: "clinical", clinicalTab: "drug", selectedDisease: id };
          }
          if (!next) return {};
          return { ...next, navStack: [...s.navStack, snap] };
        });
      },
      navBack: () =>
        setState((s) => {
          if (!s.navStack.length) return { view: "explorer" };
          const prev = s.navStack[s.navStack.length - 1];
          return { ...prev, navStack: s.navStack.slice(0, -1) };
        }),
      inShortlist: (g) => ref.current.shortlist.includes(g),
      toggleShortlist: (g) =>
        setState((s) => ({
          shortlist: s.shortlist.includes(g)
            ? s.shortlist.filter((x) => x !== g)
            : [...s.shortlist, g].slice(0, 5),
        })),
      clearShortlist: () => setState({ shortlist: [] }),
      votesFor,
      myVote,
      castVote: (g, status, note) =>
        setState((s) => {
          const list = (s.decisions[g] || []).filter((v) => v.reviewer !== s.reviewer);
          const existing = (s.decisions[g] || []).find((v) => v.reviewer === s.reviewer);
          list.push({
            reviewer: s.reviewer,
            status,
            note: note != null ? note : existing ? existing.note : "",
            ts: Date.now(),
          });
          return { decisions: { ...s.decisions, [g]: list } };
        }),
      setVoteNote: (g, note) => {
        const mine = myVote(g);
        store.castVote(g, mine ? mine.status : "hold", note);
      },
      clearMyVote: (g) =>
        setState((s) => {
          const list = (s.decisions[g] || []).filter((v) => v.reviewer !== s.reviewer);
          return { decisions: { ...s.decisions, [g]: list } };
        }),
      setReviewer: (r) => setState({ reviewer: r }),
    } as Store;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state, setState]);

  return <StoreContext.Provider value={store}>{children}</StoreContext.Provider>;
}

export function useStore(): Store {
  const s = useContext(StoreContext);
  if (!s) throw new Error("useStore must be used within StoreProvider");
  return s;
}
