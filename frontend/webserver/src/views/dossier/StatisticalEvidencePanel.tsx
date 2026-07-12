import type { RealTarget } from "../../data/types";
import { fmtEffect, fmtFdr } from "../../lib/logic";
import SectionCard from "../../components/ui/SectionCard";
import StatTile from "../../components/ui/StatTile";

export default function StatisticalEvidencePanel({ t, comp, gradeColor }: { t: RealTarget; comp: number; gradeColor: string }) {
  const metrics = [
    { label: "|log2 fold-change| (peak condition)", value: fmtEffect(t.effect), color: "#1a1d24" },
    { label: "FDR (BH), peak condition", value: fmtFdr(t.fdr), color: "#1a1d24" },
    { label: "Composite priority", value: String(comp), color: "#1a5fb4" },
    { label: "Evidence grade", value: t.grade ?? "unknown", color: gradeColor },
    { label: "Cells captured", value: t.nCells != null ? t.nCells.toLocaleString() : "unknown", color: "#1a1d24" },
    { label: "Guides", value: t.nGuides ?? "unknown", color: "#1a1d24" },
    { label: "DE genes (total)", value: t.nTotalDeGenes ?? "unknown", color: "#1a1d24" },
    { label: "Up / down", value: t.nUpGenes != null ? `${t.nUpGenes} / ${t.nDownGenes}` : "unknown", color: "#1a1d24" },
  ];
  const robustnessColor =
    t.crossDonorCorrelationMean == null ? "#9aa1ad" : t.crossDonorCorrelationMean >= 0.6 ? "#0d7d5a" : t.crossDonorCorrelationMean >= 0.35 ? "#b7791f" : "#c0503f";

  return (
    <SectionCard title="Statistical evidence" source="src: target_cards.csv (real screen output)">
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "16px" }}>
        {metrics.map((m) => (
          <StatTile key={m.label} label={m.label} value={m.value} color={m.color} mono />
        ))}
      </div>
      <div style={{ marginTop: "18px", paddingTop: "16px", borderTop: "1px dashed #e2e5ea" }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#6b7280", marginBottom: "6px" }}>
          <span>Cross-donor correlation (peak condition)</span>
          <span style={{ fontWeight: 600, color: "#1a1d24", fontFamily: "'IBM Plex Mono', monospace" }}>
            {t.crossDonorCorrelationMean != null ? t.crossDonorCorrelationMean.toFixed(2) : "not measured"}
          </span>
        </div>
        <div style={{ height: "8px", background: "#eef0f3", borderRadius: "5px", overflow: "hidden" }}>
          <div style={{ height: "100%", width: t.crossDonorCorrelationMean != null ? Math.round(t.crossDonorCorrelationMean * 100) + "%" : "0%", background: robustnessColor, borderRadius: "5px" }} />
        </div>
        <div style={{ fontSize: "11px", color: "#9aa1ad", marginTop: "6px" }}>
          Replicate pass: {t.replicatePassFlag == null ? "unknown" : t.replicatePassFlag ? "yes" : "no"}
          {t.readiness?.translationCappedBy && t.readiness.translationCappedBy !== "not_capped" ? ` · translation capped: ${t.readiness.translationCappedBy.replace(/_/g, " ")}` : ""}
        </div>
      </div>
    </SectionCard>
  );
}
