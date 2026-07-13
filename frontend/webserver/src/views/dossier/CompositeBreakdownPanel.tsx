import { WKEYS } from "../../data/reference";
import type { RealTarget } from "../../data/types";
import { subScores } from "../../lib/logic";
import { useStore } from "../../store/store";

export default function CompositeBreakdownPanel({ t }: { t: RealTarget }) {
  const { state } = useStore();
  const w = state.weights;
  const subs = subScores(t);
  const wsum = WKEYS.reduce((a, x) => a + (w[x.k] || 0), 0) || 1;

  let contribTotal = 0;
  WKEYS.forEach((x) => (contribTotal += (w[x.k] || 0) * subs[x.k]));
  contribTotal = contribTotal || 1;
  const breakdown = WKEYS.map((x) => {
    const contrib = (w[x.k] || 0) * subs[x.k];
    return {
      k: x.k,
      label: x.label,
      color: x.color,
      sub: subs[x.k],
      weightPct: Math.round(((w[x.k] || 0) / wsum) * 100),
      width: ((contrib / contribTotal) * 100).toFixed(1) + "%",
      contribPct: Math.round((contrib / contribTotal) * 100),
    };
  });

  return (
    <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "18px 22px", marginBottom: "26px", background: "#fbfcfd" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
        <h3 style={{ fontSize: "14px", fontWeight: 700, margin: 0 }}>How this perturbation score is composed</h3>
        <span style={{ fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", color: "#6b7280" }}>weights: {state.weightPreset}</span>
      </div>
      <div style={{ display: "flex", height: "30px", borderRadius: "8px", overflow: "hidden", marginBottom: "12px" }}>
        {breakdown.map((b) => (
          <div key={b.k} title={b.label} style={{ width: b.width, background: b.color, display: "flex", alignItems: "center", justifyContent: "center", minWidth: 0 }}>
            <span style={{ fontSize: "10.5px", fontWeight: 700, color: "#fff", whiteSpace: "nowrap", overflow: "hidden" }}>{b.contribPct}</span>
          </div>
        ))}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "14px" }}>
        {breakdown.map((b) => (
          <div key={b.k} style={{ display: "flex", alignItems: "center", gap: "7px" }}>
            <span style={{ width: "9px", height: "9px", borderRadius: "2px", background: b.color }} />
            <span style={{ fontSize: "11.5px", color: "#4a515e" }}>{b.label}</span>
            <span style={{ fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", color: "#9aa1ad" }}>sub {b.sub} · w {b.weightPct}%</span>
          </div>
        ))}
      </div>
      <div style={{ fontSize: "10.5px", color: "#9aa1ad", marginTop: "11px", lineHeight: 1.45 }}>
        Sub-scores are a disclosed formula over real fields (effect size, cross-donor correlation, red flags, gnomAD constraint, disease association) — see the source comment in <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>lib/logic.ts</span>. Change weights in the explorer to re-rank. The <strong>readiness call is computed by the repo's own rule-based engine and does not move with weights</strong>.
      </div>
    </div>
  );
}
