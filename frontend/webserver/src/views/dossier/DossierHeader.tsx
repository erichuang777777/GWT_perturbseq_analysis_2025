import { GRADE, READINESS } from "../../data/reference";
import type { RealTarget } from "../../data/types";
import { useStore } from "../../store/store";
import Badge from "../../components/ui/Badge";

export default function DossierHeader({ t, comp }: { t: RealTarget; comp: number }) {
  const { setState, navTo } = useStore();
  const call = t.readiness?.call;
  const Rt = call ? READINESS[call] : { label: "Unreviewed", color: "#8a92a0", bg: "#f7f8fa" };
  const Gt = t.grade ? GRADE[t.grade] : { color: "#8a92a0", bg: "#f7f8fa" };

  return (
    <>
      <div
        className="navlink"
        onClick={() => setState({ view: "explorer" })}
        style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "13px", color: "#6b7280", marginBottom: "18px", fontWeight: 500 }}
      >
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M15 18l-6-6 6-6" />
        </svg>{" "}
        Back to explorer
      </div>

      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "24px", paddingBottom: "22px", borderBottom: "1px solid #e2e5ea", marginBottom: "26px" }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "13px", marginBottom: "7px" }}>
            <h1 style={{ fontSize: "34px", fontWeight: 700, letterSpacing: "-.8px", margin: 0, fontFamily: "'IBM Plex Mono', monospace" }}>{t.gene}</h1>
            {t.primaryOutcome && (
              <span
                title={`Primary-outcome target #${t.primaryOutcomeRank} of 15 — the server's headline result, selected by trans-effect (downstream DE) breadth ranking`}
                style={{ display: "inline-flex", alignItems: "center", gap: "5px", padding: "5px 11px", borderRadius: "20px", fontSize: "11.5px", fontWeight: 700, color: "#fff", background: "#5b3fb4", letterSpacing: ".2px" }}
              >
                ★ Primary outcome{t.primaryOutcomeRank ? ` · #${t.primaryOutcomeRank}` : ""}
              </span>
            )}
            <Badge label={Rt.label} color={Rt.color} bg={Rt.bg} />
            <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "30px", height: "30px", borderRadius: "8px", fontSize: "14px", fontWeight: 700, color: Gt.color, background: Gt.bg }}>{t.grade ?? "—"}</span>
          </div>
          <div style={{ fontSize: "16px", color: "#4a515e" }}>{t.name}</div>
          <div style={{ display: "flex", gap: "8px", marginTop: "13px", flexWrap: "wrap" }}>
            {t.module ? (
              <span className="navlink" onClick={() => navTo("concept", t.module!.id)} style={{ fontSize: "11.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#1a5fb4", background: "#eaf1fb", padding: "4px 9px", borderRadius: "6px" }}>
                {t.module.id} · {t.module.name.replace(/_/g, " ")} →
              </span>
            ) : (
              <span style={{ fontSize: "11.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#9aa1ad", background: "#f2f4f7", padding: "4px 9px", borderRadius: "6px" }}>no assigned immune-concept module</span>
            )}
            <span style={{ fontSize: "11.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#6b7280", background: "#f2f4f7", padding: "4px 9px", borderRadius: "6px" }}>{t.primaryCondition}</span>
            <span style={{ fontSize: "11.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#6b7280", background: "#f2f4f7", padding: "4px 9px", borderRadius: "6px" }}>Ensembl {t.ensembl ?? "unknown"}</span>
          </div>
        </div>
        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <div title="A 0–100 weighted blend of the evidence sub-scores that moves with your weight sliders. It reorders your view of the hypotheses; it never changes the evidence or the rule-based readiness call. This is the second of the portal's two rankings — the first is the fixed 15-gene primary-outcome shortlist (our rule, by trans-effect breadth)." style={{ fontSize: "11px", color: "#9aa1ad", fontWeight: 600, letterSpacing: ".5px", textTransform: "uppercase", marginBottom: "4px", cursor: "help" }}>Perturbation score <span style={{ fontSize: "10px", color: "#b0b6c0", fontFamily: "'IBM Plex Mono', monospace" }} aria-hidden>ⓘ</span></div>
          <div style={{ fontSize: "42px", fontWeight: 700, letterSpacing: "-1.5px", color: "#1a5fb4", lineHeight: 1 }}>{comp}</div>
          <div style={{ fontSize: "11px", color: "#9aa1ad", marginTop: "3px" }}>0–100 · moves with your weights</div>
        </div>
      </div>
    </>
  );
}
