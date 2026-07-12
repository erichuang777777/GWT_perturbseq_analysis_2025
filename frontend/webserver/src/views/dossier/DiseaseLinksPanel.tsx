import type { RealTarget } from "../../data/types";
import { useStore } from "../../store/store";
import SectionCard, { UnknownNotice } from "../../components/ui/SectionCard";

export default function DiseaseLinksPanel({ t }: { t: RealTarget }) {
  const { navTo } = useStore();
  const diseases = t.diseases.map((d) => ({
    name: d.name,
    id: d.id,
    score: d.overallScore != null ? d.overallScore.toFixed(2) : "unknown",
    width: d.overallScore != null ? Math.round(d.overallScore * 100) + "%" : "0%",
  }));

  return (
    <SectionCard title="External evidence & disease links" source="src: Open Targets (cached fetch)">
      {diseases.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "9px" }}>
          {diseases.map((d) => (
            <div key={d.id} className="navlink" onClick={() => navTo("disease", d.id)} style={{ display: "flex", alignItems: "center", gap: "14px", padding: "11px 14px", background: "#f7f8fa", borderRadius: "10px" }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: "13.5px", fontWeight: 600, color: "#1a1d24" }}>{d.name}</div>
                <div style={{ fontSize: "11.5px", color: "#8a92a0", fontFamily: "'IBM Plex Mono', monospace" }}>{d.id}</div>
              </div>
              <div style={{ width: "130px" }}>
                <div style={{ height: "6px", background: "#e6e9ee", borderRadius: "4px", overflow: "hidden" }}>
                  <div style={{ height: "100%", width: d.width, background: "#1a5fb4", borderRadius: "4px" }} />
                </div>
              </div>
              <div style={{ width: "42px", textAlign: "right", fontSize: "12.5px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a5fb4" }}>{d.score}</div>
            </div>
          ))}
        </div>
      ) : (
        <UnknownNotice>unknown — no disease associations indexed in Open Targets for this gene</UnknownNotice>
      )}
    </SectionCard>
  );
}
