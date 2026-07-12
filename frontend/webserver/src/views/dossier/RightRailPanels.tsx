import { CONSTRAINT_META, RED_FLAG_LABELS } from "../../data/reference";
import type { RealTarget } from "../../data/types";
import { similarTargets } from "../../lib/logic";
import { downloadJson } from "../../lib/download";
import { useStore } from "../../store/store";
import { READINESS as R } from "../../data/reference";

export function ReadinessRationalePanel({ t }: { t: RealTarget }) {
  const redFlags = t.readiness?.redFlags ?? [];
  const reasonBullets = (t.readiness?.reasons ?? "").split(";").map((s) => s.trim()).filter(Boolean);
  return (
    <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px", background: "#fafbfc" }}>
      <h3 style={{ fontSize: "14px", fontWeight: 700, margin: "0 0 13px" }}>Readiness rationale</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "9px", marginBottom: redFlags.length ? "14px" : 0 }}>
        {reasonBullets.map((text, i) => (
          <div key={i} style={{ display: "flex", gap: "10px", alignItems: "flex-start" }}>
            <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: "#2563c9", flexShrink: 0, marginTop: "5px" }} />
            <div style={{ fontSize: "12px", lineHeight: 1.45, color: "#4a515e" }}>{text}</div>
          </div>
        ))}
      </div>
      {redFlags.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginBottom: "12px" }}>
          {redFlags.map((f) => (
            <div key={f} style={{ fontSize: "11.5px", color: "#8a2f2f", background: "#f6e5e5", borderRadius: "8px", padding: "7px 10px" }}>⚑ {RED_FLAG_LABELS[f] ?? f}</div>
          ))}
        </div>
      )}
      {t.readiness?.nextValidationStep && (
        <div style={{ fontSize: "11.5px", lineHeight: 1.5, color: "#1f56b8", background: "#e8f0fc", borderRadius: "8px", padding: "9px 11px" }}>
          <strong>Next validation step:</strong> {t.readiness.nextValidationStep}
        </div>
      )}
    </div>
  );
}

export function SafetySignalsPanel({ t }: { t: RealTarget }) {
  const redFlags = t.readiness?.redFlags ?? [];
  return (
    <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
        <h3 style={{ fontSize: "14px", fontWeight: 700, margin: 0 }}>Safety signals</h3>
        <span style={{ fontSize: "10px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace" }}>descriptive</span>
      </div>
      {t.safetyLiabilities.length > 0 ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "10px" }}>
          {t.safetyLiabilities.map((s) => (
            <span key={s.event} style={{ fontSize: "11px", fontWeight: 600, color: "#8a2f2f", background: "#f6e5e5", padding: "3px 9px", borderRadius: "20px" }}>{s.event}</span>
          ))}
        </div>
      ) : (
        <div style={{ fontSize: "11.5px", color: "#6b7280", marginBottom: "10px" }}>No adverse-event liabilities indexed in Open Targets for this gene.</div>
      )}
      {redFlags.length > 0 ? (
        <div style={{ fontSize: "11.5px", color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "8px", padding: "9px 11px" }}>
          {redFlags.length} pipeline red flag{redFlags.length === 1 ? "" : "s"} triggered (see rationale panel).
        </div>
      ) : (
        <div style={{ fontSize: "11.5px", color: "#6b7280" }}>No pipeline red flags triggered for this target.</div>
      )}
    </div>
  );
}

export function PopulationGeneticsPanel({ t }: { t: RealTarget }) {
  const { navTo } = useStore();
  return (
    <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px" }}>
      <h3 style={{ fontSize: "14px", fontWeight: 700, margin: "0 0 13px" }}>Population genetics</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontSize: "12.5px", color: "#6b7280" }}>gnomAD LOEUF</span>
          <span style={{ fontSize: "12.5px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24" }}>{t.gnomad.loeuf != null ? t.gnomad.loeuf.toFixed(3) : "unknown"}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontSize: "12.5px", color: "#6b7280" }}>pLI</span>
          <span style={{ fontSize: "12.5px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24" }}>{t.gnomad.pli != null ? t.gnomad.pli.toFixed(3) : "unknown"}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span style={{ fontSize: "12.5px", color: "#6b7280" }}>Constraint tier</span>
          <span style={{ fontSize: "12.5px", fontWeight: 600, color: t.gnomad.constraintTier ? CONSTRAINT_META[t.gnomad.constraintTier].color : "#9aa1ad" }}>
            {t.gnomad.constraintTier ? CONSTRAINT_META[t.gnomad.constraintTier].label : "unknown"}
          </span>
        </div>
      </div>
      <div style={{ fontSize: "10.5px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace", marginTop: "13px", paddingTop: "12px", borderTop: "1px dashed #e2e5ea", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span>src: gnomAD v4</span>
        <span className="navlink" onClick={() => navTo("popgen", t.gene)} style={{ color: "#1a5fb4" }}>Open lookup →</span>
      </div>
    </div>
  );
}

export function SimilarTargetsPanel({ t }: { t: RealTarget }) {
  const { navTo } = useStore();
  const similar = similarTargets(t, 4).map((st) => {
    const stCall = st.readiness?.call;
    const Rs = stCall ? R[stCall] : { label: "Unreviewed", color: "#8a92a0", bg: "#f7f8fa" };
    return { gene: st.gene, rLabel: Rs.label, rColor: Rs.color, rBg: Rs.bg };
  });
  return (
    <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px" }}>
      <h3 style={{ fontSize: "14px", fontWeight: 700, margin: "0 0 4px" }}>Targets like this</h3>
      <p style={{ fontSize: "11px", color: "#8a92a0", margin: "0 0 13px", lineHeight: 1.45 }}>Other screened targets sharing this gene's assigned concept module (real membership).</p>
      {similar.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {similar.map((s) => (
            <div key={s.gene} className="rowhover navlink" onClick={() => navTo("gene", s.gene)} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "8px 9px", borderRadius: "9px" }}>
              <div style={{ fontSize: "13px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24", width: "70px" }}>{s.gene}</div>
              <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: "20px", fontSize: "10.5px", fontWeight: 600, color: s.rColor, background: s.rBg }}>{s.rLabel}</span>
            </div>
          ))}
        </div>
      ) : (
        <div style={{ fontSize: "11.5px", color: "#9aa1ad" }}>No other screened targets share this gene's module.</div>
      )}
    </div>
  );
}

// Real client-side export: serializes the exact RealTarget object rendered
// on this page (sourced from real-dataset.json) to a downloaded JSON file.
// No backend call, no fake alert() -- what you see is what you get.
export function ExportDossierButton({ t }: { t: RealTarget }) {
  return (
    <button
      onClick={() => downloadJson(`${t.gene}_dossier.json`, t)}
      style={{ width: "100%", padding: "12px", border: "1.5px solid #1a5fb4", borderRadius: "10px", background: "#fff", color: "#1a5fb4", fontSize: "13.5px", fontWeight: 600, cursor: "pointer" }}
    >
      Export target dossier (JSON)
    </button>
  );
}
