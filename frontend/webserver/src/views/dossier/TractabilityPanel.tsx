import type { RealTarget } from "../../data/types";
import SectionCard, { UnknownNotice } from "../../components/ui/SectionCard";

const MODALITY_LABEL: Record<string, string> = { SM: "Small molecule", AB: "Antibody / biologic", PR: "PROTAC / other modality", OC: "Other clinical precedent" };

export default function TractabilityPanel({ t }: { t: RealTarget }) {
  const rows = Object.entries(t.tractabilityFlags)
    .map(([mod, flags]) => ({ mod, label: MODALITY_LABEL[mod] || mod, trueFlags: Object.entries(flags).filter(([, v]) => v).map(([k]) => k) }))
    .filter((r) => r.trueFlags.length > 0);

  return (
    <SectionCard title="Tractability" source="src: Open Targets tractability (cached fetch)">
      {rows.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {rows.map((r) => (
            <div key={r.mod} style={{ padding: "11px 14px", background: "#f7f8fa", borderRadius: "10px" }}>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "#1a1d24", marginBottom: "6px" }}>{r.label}</div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {r.trueFlags.map((f) => (
                  <span key={f} style={{ fontSize: "11px", fontWeight: 600, color: "#0a6e4f", background: "#e4f3ec", padding: "3px 9px", borderRadius: "20px" }}>✓ {f}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <UnknownNotice>unknown — no positive tractability flags indexed in Open Targets</UnknownNotice>
      )}
      {t.readiness?.tractabilityModality && t.readiness.tractabilityModality !== "unknown" && (
        <div style={{ fontSize: "11px", color: "#9aa1ad", marginTop: "10px" }}>Readiness-engine tractability class: {t.readiness.tractabilityModality}</div>
      )}
    </SectionCard>
  );
}
