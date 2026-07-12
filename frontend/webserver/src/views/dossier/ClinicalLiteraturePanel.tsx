import type { RealTarget } from "../../data/types";
import SectionCard from "../../components/ui/SectionCard";

export default function ClinicalLiteraturePanel({ t }: { t: RealTarget }) {
  if (t.clinicalTrials.length === 0 && t.literature.length === 0) return null;
  return (
    <SectionCard title="Clinical trial & literature evidence" source="src: ClinicalTrials.gov / PubMed (cached fetch)">
      {t.clinicalTrials.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: t.literature.length ? "16px" : 0 }}>
          {t.clinicalTrials.map((c) => (
            <a key={c.nctId} href={c.url} target="_blank" rel="noreferrer" style={{ display: "block", padding: "11px 14px", background: "#f7f8fa", borderRadius: "10px" }}>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "#1a1d24" }}>{c.title}</div>
              <div style={{ fontSize: "11px", color: "#8a92a0", marginTop: "3px" }}>
                {c.nctId} · {c.phase || "phase unknown"} · {c.status} · {c.conditions.join(", ")}
              </div>
            </a>
          ))}
        </div>
      ) : (
        <div style={{ fontSize: "12.5px", color: "#9aa1ad", marginBottom: t.literature.length ? "16px" : 0 }}>no clinical trial evidence indexed for this target</div>
      )}
      {t.literature.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {t.literature.map((l) => (
            <a key={l.pmid} href={l.url} target="_blank" rel="noreferrer" style={{ fontSize: "12px", color: "#4a515e" }}>
              {l.title} <span style={{ color: "#9aa1ad" }}>— {l.journal}, {l.year}</span>
            </a>
          ))}
        </div>
      )}
    </SectionCard>
  );
}
