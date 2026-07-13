import type { RealTarget } from "../../data/types";
import SectionCard from "../../components/ui/SectionCard";

const CONDITION_LABEL: Record<string, string> = { Rest: "Rest", Stim8hr: "Stim 8 hr", Stim48hr: "Stim 48 hr" };

export default function ConditionSignalPanel({ t }: { t: RealTarget }) {
  const maxDe = Math.max(...t.conditions.map((x) => x.nTotalDeGenes ?? 0), 1);
  return (
    <SectionCard title="Signal across culture conditions" source="src: target_cards.csv · Rest / Stim 8 hr / Stim 48 hr">
      <p style={{ fontSize: "12px", color: "#8a92a0", margin: "0 0 16px", lineHeight: 1.5 }}>
        Real differential-expression breadth per condition (this repo's DE pipeline, not a raw expression level). {t.stimulationGated ? "This target is stimulation-gated." : ""}
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {t.conditions.map((c) => {
          const width = Math.round(((c.nTotalDeGenes ?? 0) / maxDe) * 100) + "%";
          const color = c.grade != null && c.grade >= 3 ? "#1a5fb4" : c.grade != null && c.grade === 2 ? "#4f83cc" : "#9dbde8";
          return (
            <div key={c.condition} style={{ display: "grid", gridTemplateColumns: "96px 1fr 150px", gap: "12px", alignItems: "center" }}>
              <div style={{ fontSize: "12.5px", color: "#4a515e" }}>{CONDITION_LABEL[c.condition] ?? c.condition}</div>
              <div style={{ height: "10px", background: "#f0f2f5", borderRadius: "5px", overflow: "hidden" }}>
                <div style={{ height: "100%", width, background: color, borderRadius: "5px" }} />
              </div>
              <div style={{ fontSize: "11.5px", textAlign: "right", fontFamily: "'IBM Plex Mono', monospace", color: "#4a515e" }}>
                {c.nTotalDeGenes ?? "—"} DE ({c.nUpGenes ?? "—"}↑/{c.nDownGenes ?? "—"}↓) grade {c.grade ?? "—"}
              </div>
            </div>
          );
        })}
      </div>
    </SectionCard>
  );
}
