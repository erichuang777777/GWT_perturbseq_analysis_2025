import { TARGETS, targetByGene } from "../data/dataset";
import { GRADE } from "../data/reference";
import { rankedTargets } from "../lib/logic";
import { useStore } from "../store/store";
import DossierHeader from "./dossier/DossierHeader";
import ReviewerDecisionPanel from "./dossier/ReviewerDecisionPanel";
import CompositeBreakdownPanel from "./dossier/CompositeBreakdownPanel";
import StatisticalEvidencePanel from "./dossier/StatisticalEvidencePanel";
import ConceptModulePanel from "./dossier/ConceptModulePanel";
import DiseaseLinksPanel from "./dossier/DiseaseLinksPanel";
import TractabilityPanel from "./dossier/TractabilityPanel";
import ClinicalLiteraturePanel from "./dossier/ClinicalLiteraturePanel";
import ConditionSignalPanel from "./dossier/ConditionSignalPanel";
import { ReadinessRationalePanel, SafetySignalsPanel, PopulationGeneticsPanel, SimilarTargetsPanel, ExportDossierButton } from "./dossier/RightRailPanels";

// This view is intentionally a thin composition of independent panels
// (views/dossier/*) rather than one monolithic component -- each panel
// takes just the RealTarget slice it needs and reads store actions (navTo,
// vote actions) directly, so any of them can be reused standalone (e.g. by
// a future narrative/story view that highlights one panel for one gene).
export default function Dossier() {
  const { state } = useStore();
  const t = targetByGene(state.selectedGene) || TARGETS[0];

  const rankedAll = rankedTargets(state.weights);
  const tRankInfo = rankedAll.find((x) => x.gene === t.gene)!;
  const gradeColor = t.grade ? GRADE[t.grade].color : "#8a92a0";

  return (
    <main style={{ flex: 1, maxWidth: "1120px", margin: "0 auto", width: "100%", padding: "20px 28px 70px" }}>
      <DossierHeader t={t} comp={tRankInfo._comp} rank={tRankInfo._rank} total={TARGETS.length} />
      <ReviewerDecisionPanel gene={t.gene} />
      <CompositeBreakdownPanel t={t} />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 336px", gap: "26px", alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "22px", minWidth: 0 }}>
          <StatisticalEvidencePanel t={t} comp={tRankInfo._comp} gradeColor={gradeColor} />
          <ConceptModulePanel t={t} />
          <DiseaseLinksPanel t={t} />
          <TractabilityPanel t={t} />
          <ClinicalLiteraturePanel t={t} />
          <ConditionSignalPanel t={t} />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          <ReadinessRationalePanel t={t} />
          <SafetySignalsPanel t={t} />
          <PopulationGeneticsPanel t={t} />
          <SimilarTargetsPanel t={t} />
          <ExportDossierButton t={t} />
        </div>
      </div>
    </main>
  );
}
