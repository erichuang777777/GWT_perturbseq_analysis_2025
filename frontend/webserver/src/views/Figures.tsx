import { useEffect, useRef } from "react";
import { DATA_VERSION, DISEASES, FIGURES, clusterNames } from "../data/reference";
import { drawFigure } from "../lib/drawFigure";
import { useStore } from "../store/store";

interface SegOption {
  k: string;
  label: string;
  color: string;
  bg: string;
  border: string;
  onSelect: () => void;
}
interface Seg {
  label: string;
  options: SegOption[];
}

export default function Figures() {
  const { state, setState } = useStore();
  const S = state;
  const panelRef = useRef<HTMLDivElement>(null);

  const figMeta = FIGURES.find((f) => f.id === S.figureId) || FIGURES[0];

  const figureRail = FIGURES.map((f) => {
    const active = f.id === S.figureId;
    return {
      id: f.id,
      num: f.num,
      title: f.title,
      cat: f.cat,
      color: active ? "#fff" : "#3a414d",
      bg: active ? "#5b3fb4" : "#fff",
      numColor: active ? "rgba(255,255,255,.85)" : "#b0b6c0",
      catColor: active ? "rgba(255,255,255,.75)" : "#9aa1ad",
    };
  });

  const mkSeg = (
    label: string,
    opts: { k: string; l: string }[],
    cur: string,
    apply: (k: string) => Partial<typeof S>,
  ): Seg => ({
    label,
    options: opts.map((o) => ({
      k: o.k,
      label: o.l,
      color: cur === o.k ? "#fff" : "#4a515e",
      bg: cur === o.k ? "#5b3fb4" : "#fff",
      border: cur === o.k ? "#5b3fb4" : "#d6dbe3",
      onSelect: () => setState(apply(o.k)),
    })),
  });

  let segControls: Seg[] = [];
  let fdrSlider = false;
  const conds = [
    { k: "Rest", l: "Rest" },
    { k: "Stim8hr", l: "Stim 8 hr" },
    { k: "Stim48hr", l: "Stim 48 hr" },
  ];
  if (S.figureId === "volcano") {
    segControls = [mkSeg("Culture condition", conds, S.figCondition, (k) => ({ figCondition: k }))];
    fdrSlider = true;
  } else if (S.figureId === "heatmap") {
    segControls = [mkSeg("Culture condition", conds, S.figCondition, (k) => ({ figCondition: k }))];
  } else if (S.figureId === "umap") {
    segControls = [
      mkSeg(
        "Highlight cluster",
        [{ k: "all", l: "All" }].concat(clusterNames().map((n) => ({ k: n, l: n }))),
        S.figCluster,
        (k) => ({ figCluster: k }),
      ),
    ];
  } else if (S.figureId === "cytokine") {
    segControls = [
      mkSeg(
        "Cytokine",
        ["IFNG", "IL2", "IL4", "IL13", "IL17A", "IL10", "IL21", "TNF"].map((c) => ({ k: c, l: c })),
        S.figCytokine,
        (k) => ({ figCytokine: k }),
      ),
    ];
  } else if (S.figureId === "gwas") {
    segControls = [
      mkSeg(
        "Disease",
        Object.keys(DISEASES).map((k) => ({ k, l: DISEASES[k].name })),
        S.figDisease,
        (k) => ({ figDisease: k }),
      ),
    ];
  } else if (S.figureId === "burden") {
    segControls = [
      mkSeg(
        "Blood trait",
        ["Lymphocyte count", "Lymphocyte %", "Neutrophil count", "Eosinophil count"].map((t) => ({ k: t, l: t })),
        S.figTrait,
        (k) => ({ figTrait: k }),
      ),
    ];
  }

  useEffect(() => {
    if (panelRef.current) drawFigure(panelRef.current, S);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [S.figureId, S.figCondition, S.figThresh, S.figCluster, S.figCytokine, S.figDisease, S.figTrait]);

  return (
    <main style={{ flex: 1, display: "flex", maxWidth: "1400px", margin: "0 auto", width: "100%" }}>
      {/* figure rail */}
      <aside style={{ width: "262px", flexShrink: 0, borderRight: "1px solid #e2e5ea", padding: "22px 16px" }}>
        <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".8px", color: "#8a92a0", textTransform: "uppercase", margin: "4px 6px 12px" }}>Figures</div>
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {figureRail.map((f) => (
            <div key={f.id} className="navlink" onClick={() => setState({ figureId: f.id })} style={{ display: "flex", alignItems: "center", gap: "11px", padding: "10px 12px", borderRadius: "10px", background: f.bg }}>
              <span style={{ fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", fontWeight: 600, color: f.numColor, width: "26px", flexShrink: 0 }}>{f.num}</span>
              <span style={{ flex: 1, minWidth: 0 }}>
                <span style={{ display: "block", fontSize: "13px", fontWeight: 600, color: f.color, lineHeight: 1.25 }}>{f.title}</span>
                <span style={{ display: "block", fontSize: "11px", color: f.catColor, marginTop: "1px" }}>{f.cat}</span>
              </span>
            </div>
          ))}
        </div>
      </aside>

      {/* figure panel */}
      <section style={{ flex: 1, minWidth: 0, padding: "24px 28px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "11px", marginBottom: "8px" }}>
          <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", padding: "4px 10px", borderRadius: "7px", background: "#efe9fb", color: "#5b3fb4", fontSize: "12px", fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace" }}>Fig {figMeta.num}</span>
          <h2 style={{ fontSize: "22px", fontWeight: 700, letterSpacing: "-.4px", margin: 0 }}>{figMeta.title}</h2>
          <span style={{ fontSize: "11.5px", padding: "3px 9px", borderRadius: "6px", background: "#f2f4f7", color: "#6b7280", fontWeight: 500 }}>{figMeta.cat}</span>
        </div>
        <p style={{ fontSize: "14px", lineHeight: 1.55, color: "#4a515e", margin: "0 0 6px", maxWidth: "780px" }}>{figMeta.desc}</p>
        <div style={{ fontSize: "10.5px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace", marginBottom: "20px" }}>source: {figMeta.src} · {DATA_VERSION}</div>

        {/* controls */}
        <div style={{ display: "flex", flexDirection: "column", gap: "13px", marginBottom: "18px" }}>
          {segControls.map((grp) => (
            <div key={grp.label} style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
              <span style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".6px", color: "#8a92a0", textTransform: "uppercase", minWidth: "118px" }}>{grp.label}</span>
              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                {grp.options.map((o) => (
                  <div key={o.k} className="navlink" onClick={o.onSelect} style={{ padding: "6px 12px", borderRadius: "8px", border: `1.5px solid ${o.border}`, background: o.bg, color: o.color, fontSize: "12.5px", fontWeight: 500 }}>{o.label}</div>
                ))}
              </div>
            </div>
          ))}
          {fdrSlider && (
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".6px", color: "#8a92a0", textTransform: "uppercase", minWidth: "118px" }}>FDR threshold</span>
              <input type="range" min={0} max={5} step={0.5} value={S.figThresh} onChange={(e) => setState({ figThresh: +e.target.value })} style={{ width: "220px", accentColor: "#5b3fb4" }} />
              <span style={{ fontSize: "12.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#5b3fb4", fontWeight: 600 }}>-log10 FDR ≥ {S.figThresh}</span>
            </div>
          )}
        </div>

        {/* chart */}
        <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "14px 12px 8px" }}>
          <div ref={panelRef} style={{ width: "100%", height: "462px" }} />
        </div>

        <div style={{ display: "flex", alignItems: "flex-start", gap: "8px", marginTop: "14px", fontSize: "11.5px", color: "#8a92a0", lineHeight: 1.5, maxWidth: "820px" }}>
          <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>ⓘ</span>{" "}
          <span>
            Drag to zoom, double-click to reset, hover a point for its gene. Values shown are <strong>illustrative for this research demo</strong> — in the live portal each figure is rendered from the notebook outputs in <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>{figMeta.src}</span> with full provenance. Descriptive figures never feed any readiness or evidence-grade call.
          </span>
        </div>
      </section>
    </main>
  );
}
