import type { RealTarget } from "../../data/types";
import { useStore } from "../../store/store";
import SectionCard, { UnknownNotice } from "../../components/ui/SectionCard";

export default function ConceptModulePanel({ t }: { t: RealTarget }) {
  const { navTo } = useStore();
  return (
    <SectionCard title="Immune-concept module" source="concept modules · M01–M20">
      <p style={{ fontSize: "12px", color: "#8a92a0", margin: "0 0 14px", lineHeight: 1.5 }}>
        Real seed-gene membership (concept_annotation.py). <strong style={{ color: "#7a6a3f" }}>Descriptive only — never feeds the readiness call.</strong> This pipeline does not compute a continuous activation score across every module for every gene, so only actual membership is shown — never a fabricated cross-module profile.
      </p>
      {t.allModules.length > 0 ? (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
          {t.allModules.map((m) => (
            <span key={m.id} className="navlink" onClick={() => navTo("concept", m.id)} style={{ fontSize: "12.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#1a5fb4", background: "#eaf1fb", padding: "6px 12px", borderRadius: "8px" }}>
              {m.id} · {m.name.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      ) : (
        <UnknownNotice>unknown — not a member of any curated immune-concept module (may be a general chromatin/transcription-machinery gene; see red flags)</UnknownNotice>
      )}
      {t.stimulationGated != null && (
        <div style={{ marginTop: "12px", fontSize: "11.5px", color: t.stimulationGated ? "#0a6e4f" : "#6b7280" }}>
          {t.stimulationGated ? "✓ Stimulation-gated — quiet at Rest, active on stimulation (real, from concept_annotation.py)." : "Not flagged stimulation-gated."}
        </div>
      )}
    </SectionCard>
  );
}
