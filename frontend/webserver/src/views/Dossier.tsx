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
import ExternalCorroborationPanel from "./dossier/ExternalCorroborationPanel";
import TractabilityPanel from "./dossier/TractabilityPanel";
import ClinicalLiteraturePanel from "./dossier/ClinicalLiteraturePanel";
import ConditionSignalPanel from "./dossier/ConditionSignalPanel";
import { ReadinessRationalePanel, SafetySignalsPanel, PopulationGeneticsPanel, SimilarTargetsPanel, ExportDossierButton } from "./dossier/RightRailPanels";
import PageReferences from "../components/ui/PageReferences";

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
      <DossierHeader t={t} comp={tRankInfo._comp} />
      <ReviewerDecisionPanel gene={t.gene} />
      <CompositeBreakdownPanel t={t} />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 336px", gap: "26px", alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "22px", minWidth: 0 }}>
          <StageLabel n={1} title="Discovery evidence" sub="Does the perturbation do something, and does it hold up?" />
          <StatisticalEvidencePanel t={t} comp={tRankInfo._comp} gradeColor={gradeColor} />
          <ConditionSignalPanel t={t} />
          <StageLabel n={2} title="Mechanism" sub="Which immune concept does the target act through?" />
          <ConceptModulePanel t={t} />
          <StageLabel n={3} title="Disease relevance" sub="Where is the target genetically linked to disease, and does independent external evidence corroborate it?" />
          <DiseaseLinksPanel t={t} />
          <ExternalCorroborationPanel t={t} />
          <StageLabel n={4} title="Tractability & translation" sub="Can it be drugged, and what clinical precedent exists?" />
          <TractabilityPanel t={t} />
          <ClinicalLiteraturePanel t={t} />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          <ReadinessRationalePanel t={t} />
          <SafetySignalsPanel t={t} />
          <PopulationGeneticsPanel t={t} />
          <SimilarTargetsPanel t={t} />
          <ExportDossierButton t={t} />
        </div>
      </div>

      <PageReferences
        keys={["gwt_primary", "open_targets", "gnomad", "chembl", "reactome", "string", "alphafold", "clinicaltrials", "pubmed", "deseq2"]}
      />
    </main>
  );
}

function StageLabel({ n, title, sub }: { n: number; title: string; sub: string }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: "10px", margin: "6px 0 -8px", paddingBottom: "6px", borderBottom: "1px solid #e8ebf0" }}>
      <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "20px", height: "20px", borderRadius: "6px", background: "#12233a", color: "#fff", fontSize: "11px", fontWeight: 700, flexShrink: 0 }}>{n}</span>
      <span style={{ fontSize: "13.5px", fontWeight: 700, color: "#12233a", letterSpacing: "-.2px" }}>{title}</span>
      <span style={{ fontSize: "12px", color: "#8a92a0" }}>{sub}</span>
    </div>
  );
}
