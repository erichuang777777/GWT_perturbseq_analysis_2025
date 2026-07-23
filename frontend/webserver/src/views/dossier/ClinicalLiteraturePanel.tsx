import type { RealTarget } from "../../data/types";
import SectionCard from "../../components/ui/SectionCard";

const NOVELTY_META: Record<string, { label: string; color: string; bg: string }> = {
  no_record: { label: "No PubMed record", color: "#7c3aed", bg: "#f3edff" },
  understudied: { label: "Understudied", color: "#2563a8", bg: "#e8f1fb" },
  moderate: { label: "Moderately studied", color: "#8a6d1f", bg: "#fbf3dc" },
  well_studied: { label: "Well-studied", color: "#6b7280", bg: "#f1f2f4" },
};

export default function ClinicalLiteraturePanel({ t }: { t: RealTarget }) {
  const nov = t.novelty;
  if (t.clinicalTrials.length === 0 && t.literature.length === 0 && !nov) return null;
  return (
    <SectionCard title="Clinical trial & literature evidence" source="src: ClinicalTrials.gov / PubMed (cached fetch)">
      {nov && (
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px", flexWrap: "wrap" }}>
          <span
            style={{
              fontSize: "11px", fontWeight: 600, padding: "3px 9px", borderRadius: "8px",
              color: (NOVELTY_META[nov.tier] || NOVELTY_META.well_studied).color,
              background: (NOVELTY_META[nov.tier] || NOVELTY_META.well_studied).bg,
            }}
          >
            {(NOVELTY_META[nov.tier] || NOVELTY_META.well_studied).label}
          </span>
          <span style={{ fontSize: "11.5px", color: "#8a92a0" }}>
            {nov.literatureCount} PubMed hit{nov.literatureCount === 1 ? "" : "s"} for “{t.gene} + CD4 T cell” · novelty {nov.noveltyScore.toFixed(2)} (higher = fewer papers)
          </span>
        </div>
      )}
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
