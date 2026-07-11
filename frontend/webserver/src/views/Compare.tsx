import { DECISION_META, GRADE, READINESS } from "../data/reference";
import { TARGETS } from "../data/targets";
import type { Target } from "../data/types";
import { composite, consensus } from "../lib/logic";
import { useStore } from "../store/store";

interface Cell {
  plain: boolean;
  badge: boolean;
  display: string;
  color: string;
  bg?: string;
  cellBg: string;
  weight: string | number;
  fam: string;
  dot: string | false;
}

export default function Compare() {
  const { state, setState, navTo, toggleShortlist, clearShortlist, votesFor } = useStore();
  const all = TARGETS;
  const R = READINESS;
  const G = GRADE;

  const slGenes = state.shortlist.filter((g) => all.find((x) => x.gene === g));
  const compareTargets = slGenes.slice(0, 5).map((g) => all.find((x) => x.gene === g)!) as Target[];

  const cmp = compareTargets.map((x) => {
    const Rr = R[x.call];
    const Gg = G[x.grade];
    const cons2 = consensus(votesFor(x.gene));
    const cm2 = DECISION_META[cons2.status];
    const loeuf = parseFloat((x.pop.find((p) => p[0].includes("LOEUF")) || ([] as unknown as [string, string]))[1]);
    const topC = x.concepts.find((c) => c[2] != null) || ([] as unknown as [string, string, number]);
    return {
      x,
      Rr,
      Gg,
      cm2,
      comp: composite(x, state.weights),
      effNum: parseFloat(x.effect),
      fdrNum: parseFloat(x.fdr),
      loeuf,
      robust: x.robustness,
      safe: x.safety,
      topConcept: topC[1] || "—",
      fdr: x.fdr,
    };
  });

  type Spec = {
    label: string;
    kind: "num" | "fdr" | "badge" | "text";
    get: (c: (typeof cmp)[number]) => number | string | { label: string; color: string; bg: string; dot?: string };
    dir?: "hi" | "lo";
    fmt?: (v: number) => string;
  };
  const cSpecs: Spec[] = [
    { label: "Composite priority", kind: "num", get: (c) => c.comp, dir: "hi" },
    { label: "Readiness call", kind: "badge", get: (c) => ({ label: c.Rr.label, color: c.Rr.color, bg: c.Rr.bg }) },
    { label: "Evidence grade", kind: "badge", get: (c) => ({ label: c.x.grade, color: c.Gg.color, bg: c.Gg.bg }) },
    { label: "|log2 fold-change|", kind: "num", get: (c) => c.effNum, dir: "hi", fmt: (v) => v.toFixed(2) },
    { label: "FDR (BH)", kind: "fdr", get: (c) => c.fdr },
    { label: "Robustness", kind: "num", get: (c) => c.robust, dir: "hi", fmt: (v) => v + "%" },
    { label: "Safety window", kind: "num", get: (c) => c.safe, dir: "hi", fmt: (v) => v + " / 100" },
    { label: "gnomAD LOEUF", kind: "num", get: (c) => c.loeuf, dir: "lo", fmt: (v) => (isNaN(v) ? "unknown" : v.toFixed(2)) },
    { label: "Top concept", kind: "text", get: (c) => c.topConcept },
    { label: "Review consensus", kind: "badge", get: (c) => ({ label: c.cm2.label, color: c.cm2.color, bg: c.cm2.bg, dot: c.cm2.dot }) },
  ];
  const cBest = cSpecs.map((s) => {
    if (s.kind === "num") {
      const vs = cmp.map((c) => s.get(c) as number).filter((v) => v != null && !isNaN(v));
      if (!vs.length) return null;
      return s.dir === "hi" ? Math.max.apply(null, vs) : Math.min.apply(null, vs);
    }
    if (s.kind === "fdr") {
      const vs = cmp.map((c) => c.fdrNum).filter((v) => !isNaN(v));
      return vs.length ? Math.min.apply(null, vs) : null;
    }
    return null;
  });
  const compareMetricLabels = cSpecs.map((s) => ({ label: s.label }));
  const compareCols = cmp.map((c) => ({
    gene: c.x.gene,
    name: c.x.name,
    cells: cSpecs.map((s, si): Cell => {
      if (s.kind === "num") {
        const v = s.get(c) as number;
        const disp = v == null || isNaN(v) ? "unknown" : s.fmt ? s.fmt(v) : String(v);
        const hl = cBest[si] != null && v === cBest[si];
        return { plain: true, badge: false, display: disp, color: hl ? "#0a6e4f" : "#1a1d24", cellBg: hl ? "#f1faf5" : "transparent", weight: hl ? 700 : 600, fam: "'IBM Plex Mono', monospace", dot: false };
      }
      if (s.kind === "fdr") {
        const hl = cBest[si] != null && c.fdrNum === cBest[si];
        return { plain: true, badge: false, display: s.get(c) as string, color: hl ? "#0a6e4f" : "#4a515e", cellBg: hl ? "#f1faf5" : "transparent", weight: hl ? 700 : 500, fam: "'IBM Plex Mono', monospace", dot: false };
      }
      if (s.kind === "badge") {
        const b = s.get(c) as { label: string; color: string; bg: string; dot?: string };
        return { plain: false, badge: true, display: b.label, color: b.color, bg: b.bg, dot: b.dot || false, cellBg: "transparent", weight: 600, fam: "inherit" };
      }
      return { plain: true, badge: false, display: s.get(c) as string, color: "#4a515e", cellBg: "transparent", weight: 500, fam: "inherit", dot: false };
    }),
  }));

  const enough = compareTargets.length >= 2;
  const tooFew = compareTargets.length < 2;
  const overflow = slGenes.length > 5;

  return (
    <main style={{ flex: 1, maxWidth: "1400px", margin: "0 auto", width: "100%", padding: "20px 28px 70px" }}>
      <div className="navlink" onClick={() => setState({ view: "explorer" })} style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "13px", color: "#6b7280", marginBottom: "16px", fontWeight: 500 }}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M15 18l-6-6 6-6" />
        </svg>{" "}
        Back to explorer
      </div>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: "20px", marginBottom: "6px", flexWrap: "wrap" }}>
        <h1 style={{ fontSize: "28px", fontWeight: 700, letterSpacing: "-.6px", margin: 0 }}>Compare targets</h1>
        <span className="navlink" onClick={() => clearShortlist()} style={{ fontSize: "12.5px", color: "#1a5fb4", fontWeight: 500 }}>Clear shortlist</span>
      </div>
      <div style={{ fontSize: "13px", color: "#6b7280", marginBottom: "20px" }}>
        {compareTargets.length} targets side by side · best value per row highlighted <span style={{ color: "#0a6e4f", fontWeight: 600 }}>■</span>
      </div>

      {overflow && (
        <div style={{ fontSize: "12.5px", color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "9px", padding: "10px 14px", marginBottom: "18px" }}>
          Comparison is capped at 5 columns — showing the first 5 of your shortlist.
        </div>
      )}

      {enough && (
        <>
          <div style={{ display: "flex", border: "1px solid #e2e5ea", borderRadius: "14px", overflow: "hidden", background: "#fff" }}>
            <div style={{ width: "186px", flexShrink: 0, borderRight: "1px solid #e2e5ea", background: "#fafbfc" }}>
              <div style={{ height: "70px", borderBottom: "1px solid #e2e5ea" }} />
              {compareMetricLabels.map((l) => (
                <div key={l.label} style={{ height: "52px", display: "flex", alignItems: "center", padding: "0 16px", fontSize: "11.5px", fontWeight: 600, color: "#6b7280", borderTop: "1px solid #eef0f3" }}>{l.label}</div>
              ))}
            </div>
            <div style={{ flex: 1, display: "flex", overflowX: "auto" }}>
              {compareCols.map((col) => (
                <div key={col.gene} style={{ flex: 1, minWidth: "168px", borderRight: "1px solid #eef0f3" }}>
                  <div style={{ height: "70px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px", padding: "0 16px", borderBottom: "1px solid #e2e5ea", background: "#f7f8fa" }}>
                    <div className="navlink" onClick={() => navTo("gene", col.gene)} style={{ minWidth: 0 }}>
                      <div style={{ fontSize: "15px", fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", color: "#1a5fb4" }}>{col.gene}</div>
                      <div style={{ fontSize: "10.5px", color: "#8a92a0", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "130px" }}>{col.name}</div>
                    </div>
                    <span className="navlink" onClick={() => toggleShortlist(col.gene)} title="Remove" style={{ flexShrink: 0, display: "inline-flex", alignItems: "center", justifyContent: "center", width: "20px", height: "20px", borderRadius: "50%", background: "#eef0f3", color: "#8a92a0", fontSize: "14px" }}>×</span>
                  </div>
                  {col.cells.map((cell, ci) => (
                    <div key={ci} style={{ height: "52px", display: "flex", alignItems: "center", padding: "0 16px", borderTop: "1px solid #eef0f3", background: cell.cellBg }}>
                      {cell.plain && (
                        <span style={{ fontSize: "12.5px", fontWeight: cell.weight, color: cell.color, fontFamily: cell.fam }}>{cell.display}</span>
                      )}
                      {cell.badge && (
                        <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "3px 10px", borderRadius: "20px", fontSize: "11px", fontWeight: 600, color: cell.color, background: cell.bg }}>
                          {cell.dot && <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: cell.dot }} />}
                          {cell.display}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
          <div style={{ fontSize: "11px", color: "#9aa1ad", marginTop: "14px", lineHeight: 1.5, maxWidth: "760px" }}>
            Highlight marks the best value per row (higher priority / effect / robustness / safety; lower FDR / LOEUF). It is a within-shortlist convenience, not a readiness call — the call stays rule-based and per-target.
          </div>
        </>
      )}

      {tooFew && (
        <div style={{ border: "1px dashed #d6dbe3", borderRadius: "14px", padding: "54px", textAlign: "center" }}>
          <div style={{ fontSize: "15px", color: "#6b7280", marginBottom: "6px" }}>Select at least two targets to compare.</div>
          <div style={{ fontSize: "13px", color: "#9aa1ad" }}>Tick the checkbox on any row in the explorer, then reopen Compare.</div>
        </div>
      )}
    </main>
  );
}
