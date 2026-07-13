import { useEffect, useRef, useState } from "react";
import { DATA_VERSION, FIGURES } from "../data/reference";
import { FIGURES_DATA, loadFigures } from "../data/figuresData";
import { drawFigure } from "../lib/drawFigure";
import { useStore } from "../store/store";
import PageReferences from "../components/ui/PageReferences";

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

function titleCase(s: string): string {
  return s.replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function Figures() {
  const { state, setState } = useStore();
  const S = state;
  const panelRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    loadFigures()
      .then(() => setStatus("ready"))
      .catch(() => setStatus("error"));
  }, []);

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
  } else if (S.figureId === "cytokine" && status === "ready") {
    // Only cytokines with >=20 significant regulators make it into
    // figures.json (see build_figures_data.py) -- offer exactly that real
    // list, never a fixed guess that might include one with too few hits.
    segControls = [
      mkSeg(
        "Cytokine",
        FIGURES_DATA.cytokines.map((c) => ({ k: c, l: c })),
        S.figCytokine,
        (k) => ({ figCytokine: k }),
      ),
    ];
  } else if (S.figureId === "gwas" && status === "ready") {
    segControls = [
      mkSeg(
        "Disease",
        FIGURES_DATA.diseases.map((d) => ({ k: d, l: titleCase(d) })),
        S.figDisease,
        (k) => ({ figDisease: k }),
      ),
    ];
  }
  // No control for "umap" (nothing to filter -- the panel has no chart) or
  // "burden" (only one real blood trait, lymphocyte count, exists in this
  // repo's UK Biobank burden data -- offering a picker with fake alternative
  // traits would be exactly the fabricated-control-list bug this rewiring
  // fixes elsewhere).

  useEffect(() => {
    if (status === "ready" && panelRef.current) drawFigure(panelRef.current, S);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, S.figureId, S.figCondition, S.figThresh, S.figCytokine, S.figDisease]);

  if (status === "loading")
    return <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#9aa1ad", fontSize: "14px" }}>Loading figure data…</main>;
  if (status === "error")
    return <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#9aa1ad", fontSize: "14px" }}>Couldn't load figures.json.</main>;

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
        {(segControls.length > 0 || fdrSlider) && (
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
        )}

        {/* chart — keyed per-branch so React unmounts rather than reuses the DOM
            node between the Plotly-managed div and the plain message div (Plotly
            mutates its element imperatively, e.g. adding the "js-plotly-plot"
            class, which React would otherwise silently carry over on reuse) */}
        {S.figureId === "umap" ? (
          <div key="umap-message" style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "28px 24px", minHeight: "462px", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div style={{ maxWidth: "560px", textAlign: "center", color: "#4a515e", fontSize: "13.5px", lineHeight: 1.6 }}>
              <div style={{ fontSize: "22px", marginBottom: "10px" }}>—</div>
              <div style={{ fontWeight: 700, marginBottom: "8px", color: "#3a414d" }}>UMAP not available</div>
              <div>
                A faithful functional-clustering UMAP needs 2D embedding coordinates computed from the pipeline&apos;s AnnData objects, which are <strong>not included in this repository</strong>. Real gene→cluster assignments exist (112 clusters — see the heatmap figure) but not 2D positions, so this figure is <strong>intentionally not drawn rather than fabricated</strong>.
              </div>
            </div>
          </div>
        ) : (
          <div key="chart-panel" style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "14px 12px 8px" }}>
            <div ref={panelRef} style={{ width: "100%", height: "462px" }} />
          </div>
        )}

        <div style={{ display: "flex", alignItems: "flex-start", gap: "8px", marginTop: "14px", fontSize: "11.5px", color: "#8a92a0", lineHeight: 1.5, maxWidth: "820px" }}>
          <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>ⓘ</span>{" "}
          <span>
            Values are real data extracted from this repo&apos;s pipeline outputs (see each figure&apos;s source). Drag to zoom, double-click to reset, hover for the gene. Descriptive figures never feed any readiness or evidence-grade call.
          </span>
        </div>

        <PageReferences
          keys={["gwt_primary", "open_targets", "gnomad", "reactome", "deseq2", "benjamini_hochberg"]}
        />
      </section>
    </main>
  );
}
