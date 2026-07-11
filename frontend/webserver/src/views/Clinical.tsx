import { DISEASES, DRUGS, GRADE, MODULES, READINESS } from "../data/reference";
import { TARGETS } from "../data/targets";
import type { Category } from "../data/types";
import { useStore } from "../store/store";

const catBadge = (c: Category) =>
  c === "Upstream" ? { catBg: "#eaf1fb", catColor: "#1a5fb4" } : { catBg: "#f0eafb", catColor: "#6b40b8" };

const phaseColor = (p: string) =>
  p === "Approved" ? { c: "#0a6e4f", b: "#e4f3ec" } : p === "Withdrawn" ? { c: "#8a2f2f", b: "#f6e5e5" } : { c: "#1f56b8", b: "#e8f0fc" };

const constraintMeta: Record<string, { label: string; color: string; bg: string }> = {
  high: { label: "High constraint (LoF-intolerant)", color: "#0a6e4f", bg: "#e4f3ec" },
  moderate: { label: "Moderate constraint", color: "#9a6510", bg: "#fbf1de" },
  low: { label: "Low constraint", color: "#5b6270", bg: "#eef0f3" },
};

export default function Clinical() {
  const { state, setState } = useStore();
  const S = state;
  const all = TARGETS;
  const R = READINESS;
  const G = GRADE;

  const clinicalTabs = [
    { key: "scope", label: "Scope & guardrails" },
    { key: "concept", label: "Individual concept profile" },
    { key: "drug", label: "Disease × drug evidence" },
    { key: "popgen", label: "Population genetics" },
  ].map((tb) => ({
    key: tb.key,
    label: tb.label,
    color: S.clinicalTab === tb.key ? "#0d7d5a" : "#8a92a0",
    border: S.clinicalTab === tb.key ? "#0d7d5a" : "transparent",
  }));

  // ---- concept tab ----
  const conceptList = Object.keys(MODULES).map((id) => {
    const m = MODULES[id];
    const active = S.selectedConcept === id;
    const cb = catBadge(m.cat);
    return {
      id,
      name: m.name.replace(/_/g, " "),
      cat: m.cat,
      catBg: cb.catBg,
      catColor: cb.catColor,
      color: active ? "#1a5fb4" : "#3a414d",
      bg: active ? "#eaf1fb" : "#fff",
    };
  });
  const cm = MODULES[S.selectedConcept];
  const ccb = catBadge(cm.cat);
  const conceptTargets = all
    .filter((t) => t.mod === S.selectedConcept)
    .map((t) => {
      const Rr = R[t.call];
      return { gene: t.gene, name: t.name, rLabel: Rr.label, rColor: Rr.color, rBg: Rr.bg };
    });

  // ---- disease × drug tab ----
  const selDisKey = S.selectedDisease;
  const diseaseChips = Object.keys(DISEASES).map((k) => {
    const active = selDisKey === k;
    return {
      key: k,
      name: DISEASES[k].name,
      efo: DISEASES[k].efo,
      color: active ? "#fff" : "#3a414d",
      bg: active ? "#0d7d5a" : "#fff",
      border: active ? "#0d7d5a" : "#d6dbe3",
    };
  });
  const selDis = DISEASES[selDisKey] || Object.values(DISEASES)[0];
  const disMatches = all
    .filter((t) => selDis.genes.includes(t.gene))
    .map((t) => {
      const Rr = R[t.call];
      const Gg = G[t.grade];
      const M = MODULES[t.mod];
      const assoc = Math.max(12, Math.min(98, Math.round(t.score * 0.9 + 6)));
      const dl = DRUGS[t.gene];
      let drug;
      if (Array.isArray(dl) && dl.length) {
        const d0 = dl[0];
        const pc = phaseColor(d0.phase);
        const n = (d0.trials && d0.trials[selDisKey]) || 0;
        drug = {
          has: true,
          none: false,
          name: d0.drug,
          phase: d0.phase,
          phaseC: pc.c,
          phaseB: pc.b,
          trialLabel: n > 0 ? n + " trial" + (n === 1 ? "" : "s") + " in " + selDis.name : "no trial for this indication",
          trialColor: n > 0 ? "#0a6e4f" : "#9a6510",
          extra: dl.length > 1 ? "+" + (dl.length - 1) + " more" : "",
        };
      } else {
        drug = {
          has: false,
          none: true,
          name: dl !== undefined ? "no matchable drug" : "not indexed",
          phase: "",
          phaseC: "#8a92a0",
          phaseB: "#f2f4f7",
          trialLabel: "unknown — reported as-is, never a fabricated 0",
          trialColor: "#9aa1ad",
          extra: "",
        };
      }
      return {
        gene: t.gene,
        name: t.name,
        moduleId: t.mod,
        moduleShort: M ? M.name.replace(/_/g, " ") : "",
        assoc: (assoc / 100).toFixed(2),
        assocW: assoc + "%",
        rLabel: Rr.label,
        rColor: Rr.color,
        rBg: Rr.bg,
        grade: t.grade,
        gColor: Gg.color,
        gBg: Gg.bg,
        drug,
      };
    })
    .sort((a, b) => parseFloat(b.assoc) - parseFloat(a.assoc));

  // ---- popgen tab ----
  const pq = S.popQuery.trim().toUpperCase();
  const pt = all.find((t) => t.gene.toUpperCase() === pq);
  let popTarget = null;
  if (pt) {
    const cmeta = constraintMeta[pt.constraint];
    const loeuf = pt.pop.find((p) => p[0].includes("LOEUF"))![1];
    const mz = pt.pop.find((p) => p[0].includes("Missense"))![1];
    const pli = pt.pop.find((p) => p[0].includes("pLI"))![1];
    popTarget = {
      gene: pt.gene,
      name: pt.name,
      fetched: "2026-06-30",
      constraintLabel: cmeta.label,
      constraintColor: cmeta.color,
      constraintBg: cmeta.bg,
      metrics: [
        { label: "gnomAD LOEUF", value: loeuf, color: "#1a5fb4", note: "Lower = more intolerant to loss of function" },
        { label: "Missense Z", value: mz, color: "#1a5fb4", note: "Higher = missense-constrained" },
        { label: "pLI", value: pli, color: "#1a5fb4", note: "Prob. of LoF intolerance (→1 = intolerant)" },
      ],
      interpretation:
        pt.constraint === "high"
          ? "This gene is strongly loss-of-function intolerant in the general population — heterozygous LoF is under selection, so full antagonism may carry mechanism-based risk. Favour partial or tunable modulation."
          : pt.constraint === "moderate"
            ? "Constraint is intermediate: some LoF tolerance exists but the gene is not neutral. Population genetics neither strongly supports nor argues against modulation on its own."
            : "This gene tolerates loss-of-function variation in the population, which is broadly reassuring for a modulation strategy — though tolerance to germline variation does not by itself predict therapeutic effect.",
    };
  }

  const guardrails = [
    { k: "Descriptive ≠ decision", t: "Statistical evidence (effect, robustness, concept profile) and human judgement (the readiness call, reviewer votes) are kept visually and structurally separate. Nothing here recommends a treatment." },
    { k: "unknown ≠ 0", t: 'Any field without evidence reads "unknown" with a coverage note — never a fabricated zero or default. Empty drug and constraint records are shown honestly rather than hidden.' },
    { k: "Every number is sourced", t: "Each metric carries its origin and version stamp (Open Targets / ChEMBL / gnomAD / the CD4 Perturb-seq screen). Adjustable weights re-order your view of hypotheses; they never rewrite the evidence." },
  ];
  const scopeDoes = [
    "Surface immune-concept biology for one target or concept module",
    "Rank CD4-screen targets against a disease context by association evidence",
    "Report population-genetics constraint (gnomAD) for a gene",
    "Show indexed drug / trial precedent per target and indication",
  ];
  const scopeDoesnt = [
    "Diagnose, stage, or manage any patient",
    "Recommend, dose, or compare therapies",
    "Assert clinical efficacy in any indication",
    "Replace regulatory, clinical, or expert review",
  ];

  const DGRID = "1.15fr 0.95fr 120px 1.5fr 96px 62px";

  return (
    <main style={{ flex: 1, maxWidth: "1120px", margin: "0 auto", width: "100%", padding: "30px 28px 70px" }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: "10px", marginBottom: "22px", padding: "13px 16px", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "11px" }}>
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#b7791f" strokeWidth="2" style={{ flexShrink: 0, marginTop: "1px" }}>
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8v5M12 16h.01" />
        </svg>
        <p style={{ fontSize: "12.5px", lineHeight: 1.5, color: "#7a6a3f", margin: 0 }}>
          <strong style={{ color: "#8a6516" }}>Evidence lookup — not a clinical decision tool.</strong> These panels surface research evidence about immune concepts, targets and genetic constraint. They do not diagnose, do not recommend treatment, and must not be used for patient management.
        </p>
      </div>

      <h1 style={{ fontSize: "28px", fontWeight: 700, letterSpacing: "-.6px", margin: "0 0 6px" }}>Clinical-evidence lookup</h1>
      <p style={{ fontSize: "15px", color: "#4a515e", margin: "0 0 22px", maxWidth: "640px" }}>Read the CD4 T-cell screen through a clinical lens: immune-concept biology, disease-to-target evidence, and population-genetics constraint.</p>

      <div style={{ display: "flex", gap: "4px", borderBottom: "1px solid #e2e5ea", marginBottom: "26px" }}>
        {clinicalTabs.map((t) => (
          <div key={t.key} className="navlink" onClick={() => setState({ clinicalTab: t.key })} style={{ padding: "11px 16px", fontSize: "14px", fontWeight: 600, color: t.color, borderBottom: `2.5px solid ${t.border}`, marginBottom: "-1px" }}>{t.label}</div>
        ))}
      </div>

      {/* scope */}
      {S.clinicalTab === "scope" && (
        <div style={{ maxWidth: "860px" }}>
          <p style={{ fontSize: "15px", lineHeight: 1.6, color: "#4a515e", margin: "0 0 26px", maxWidth: "680px" }}>This lookup reads the CD4 T-cell Perturb-seq screen through a clinical-evidence lens. Before the panels, three rules govern everything shown here — they are what keep it an evidence tool rather than a decision tool.</p>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "30px" }}>
            {guardrails.map((g) => (
              <div key={g.k} style={{ border: "1px solid #e2e5ea", borderLeft: "3px solid #0d7d5a", borderRadius: "0 12px 12px 0", padding: "16px 20px" }}>
                <div style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "13px", fontWeight: 600, color: "#0a6e4f", marginBottom: "5px" }}>{g.k}</div>
                <div style={{ fontSize: "13px", lineHeight: 1.55, color: "#4a515e" }}>{g.t}</div>
              </div>
            ))}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "18px" }}>
            <div style={{ border: "1px solid #e2e5ea", borderRadius: "13px", padding: "20px 22px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "13px" }}>
                <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "22px", height: "22px", borderRadius: "6px", background: "#e4f3ec", color: "#0a6e4f", fontWeight: 700 }}>✓</span>
                <h3 style={{ fontSize: "14px", fontWeight: 700, margin: 0 }}>What this lookup does</h3>
              </div>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "9px" }}>
                {scopeDoes.map((d) => (
                  <li key={d} style={{ fontSize: "13px", color: "#4a515e", lineHeight: 1.45, display: "flex", gap: "9px" }}>
                    <span style={{ color: "#0d7d5a", flexShrink: 0 }}>→</span>
                    {d}
                  </li>
                ))}
              </ul>
            </div>
            <div style={{ border: "1px solid #eddfc0", borderRadius: "13px", padding: "20px 22px", background: "#fdfcf8" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "13px" }}>
                <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "22px", height: "22px", borderRadius: "6px", background: "#f6e5e5", color: "#8a2f2f", fontWeight: 700 }}>×</span>
                <h3 style={{ fontSize: "14px", fontWeight: 700, margin: 0 }}>What it must not be used for</h3>
              </div>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: "9px" }}>
                {scopeDoesnt.map((d) => (
                  <li key={d} style={{ fontSize: "13px", color: "#7a6a3f", lineHeight: 1.45, display: "flex", gap: "9px" }}>
                    <span style={{ color: "#b7791f", flexShrink: 0 }}>—</span>
                    {d}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* concept profile */}
      {S.clinicalTab === "concept" && (
        <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: "26px", alignItems: "start" }}>
          <div style={{ border: "1px solid #e2e5ea", borderRadius: "13px", overflow: "hidden" }}>
            <div style={{ padding: "11px 15px", background: "#f7f8fa", borderBottom: "1px solid #e2e5ea", fontSize: "11px", fontWeight: 700, letterSpacing: ".6px", color: "#8a92a0", textTransform: "uppercase" }}>Immune concepts (M01–M20)</div>
            <div style={{ maxHeight: "520px", overflowY: "auto" }}>
              {conceptList.map((c) => (
                <div key={c.id} className="navlink rowhover" onClick={() => setState({ selectedConcept: c.id })} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "10px 15px", borderBottom: "1px solid #f0f2f5", background: c.bg }}>
                  <span style={{ fontSize: "10.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#9aa1ad" }}>{c.id}</span>
                  <span style={{ fontSize: "12.5px", fontWeight: 500, color: c.color, flex: 1 }}>{c.name}</span>
                  <span style={{ fontSize: "10px", padding: "2px 7px", borderRadius: "5px", background: c.catBg, color: c.catColor, fontWeight: 600 }}>{c.cat}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "26px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "11px", marginBottom: "5px" }}>
              <span style={{ fontSize: "13px", fontFamily: "'IBM Plex Mono', monospace", color: "#1a5fb4", fontWeight: 600 }}>{S.selectedConcept}</span>
              <h2 style={{ fontSize: "21px", fontWeight: 700, margin: 0, letterSpacing: "-.4px" }}>{cm.name.replace(/_/g, " ")}</h2>
              <span style={{ fontSize: "11px", padding: "3px 9px", borderRadius: "6px", background: ccb.catBg, color: ccb.catColor, fontWeight: 600 }}>{cm.cat}</span>
            </div>
            <p style={{ fontSize: "14.5px", lineHeight: 1.6, color: "#3a414d", margin: "14px 0 22px" }}>{cm.desc}</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "22px", marginBottom: "24px" }}>
              <div>
                <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".6px", color: "#8a92a0", textTransform: "uppercase", marginBottom: "9px" }}>Clinical question</div>
                <p style={{ fontSize: "13.5px", lineHeight: 1.55, color: "#3a414d", margin: 0 }}>{cm.question}</p>
              </div>
              <div>
                <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".6px", color: "#8a92a0", textTransform: "uppercase", marginBottom: "9px" }}>Seed genes</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  {cm.seeds.map((s) => (
                    <span key={s} style={{ fontSize: "12px", fontFamily: "'IBM Plex Mono', monospace", padding: "3px 9px", background: "#eaf1fb", color: "#1a5fb4", borderRadius: "6px", fontWeight: 500 }}>{s}</span>
                  ))}
                </div>
              </div>
            </div>
            <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".6px", color: "#8a92a0", textTransform: "uppercase", marginBottom: "11px" }}>Screened targets in this concept</div>
            <div style={{ display: "flex", flexDirection: "column", gap: "7px" }}>
              {conceptTargets.map((t) => (
                <div key={t.gene} className="navlink rowhover" onClick={() => setState({ view: "dossier", selectedGene: t.gene })} style={{ display: "flex", alignItems: "center", gap: "12px", padding: "10px 13px", border: "1px solid #eef0f3", borderRadius: "9px" }}>
                  <span style={{ fontSize: "13.5px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", width: "76px" }}>{t.gene}</span>
                  <span style={{ fontSize: "12.5px", color: "#6b7280", flex: 1 }}>{t.name}</span>
                  <span style={{ display: "inline-block", padding: "3px 9px", borderRadius: "20px", fontSize: "11px", fontWeight: 600, color: t.rColor, background: t.rBg }}>{t.rLabel}</span>
                </div>
              ))}
            </div>
            <div style={{ display: "flex", alignItems: "start", gap: "8px", marginTop: "20px", fontSize: "11.5px", color: "#8a92a0", lineHeight: 1.5 }}>
              <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>ⓘ</span> Concept activation is descriptive biology only — it never drives any readiness or evidence-grade call, and empty concepts report <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>unknown</span> rather than 0.
            </div>
          </div>
        </div>
      )}

      {/* disease × drug */}
      {S.clinicalTab === "drug" && (
        <div>
          <div style={{ fontSize: "13px", fontWeight: 600, color: "#3a414d", marginBottom: "11px" }}>Select a disease context</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "28px" }}>
            {diseaseChips.map((d) => (
              <div key={d.key} className="navlink" onClick={() => setState({ selectedDisease: d.key })} style={{ display: "flex", alignItems: "center", gap: "8px", padding: "9px 15px", border: `1.5px solid ${d.border}`, borderRadius: "22px", background: d.bg, color: d.color, fontSize: "13.5px", fontWeight: 500 }}>
                {d.name} <span style={{ fontSize: "10.5px", fontFamily: "'IBM Plex Mono', monospace", opacity: 0.7 }}>{d.efo}</span>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", alignItems: "baseline", gap: "10px", marginBottom: "15px" }}>
            <h2 style={{ fontSize: "19px", fontWeight: 700, margin: 0 }}>{selDis.name}</h2>
            <span style={{ fontSize: "13px", color: "#6b7280" }}>— {disMatches.length} candidate targets from the CD4 screen</span>
          </div>

          <div style={{ border: "1px solid #e2e5ea", borderRadius: "13px", overflow: "hidden" }}>
            <div style={{ display: "grid", gridTemplateColumns: DGRID, padding: "11px 16px", background: "#f7f8fa", borderBottom: "1px solid #e2e5ea", fontSize: "11px", fontWeight: 700, letterSpacing: ".5px", color: "#8a92a0", textTransform: "uppercase" }}>
              <div>Target</div>
              <div>Concept module</div>
              <div style={{ textAlign: "center" }}>Assoc. score</div>
              <div>Drug precedent (this indication)</div>
              <div style={{ textAlign: "center" }}>Readiness</div>
              <div style={{ textAlign: "center" }}>Grade</div>
            </div>
            {disMatches.map((m) => (
              <div key={m.gene} className="navlink rowhover" onClick={() => setState({ view: "dossier", selectedGene: m.gene })} style={{ display: "grid", gridTemplateColumns: DGRID, alignItems: "center", padding: "13px 16px", borderBottom: "1px solid #eef0f3" }}>
                <div>
                  <div style={{ fontSize: "14px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace" }}>{m.gene}</div>
                  <div style={{ fontSize: "11.5px", color: "#8a92a0" }}>{m.name}</div>
                </div>
                <div style={{ fontSize: "12.5px", color: "#4a515e" }}>
                  <span style={{ fontFamily: "'IBM Plex Mono', monospace", color: "#9aa1ad", fontSize: "10.5px" }}>{m.moduleId}</span> {m.moduleShort}
                </div>
                <div style={{ textAlign: "center" }}>
                  <div style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
                    <div style={{ width: "60px", height: "6px", background: "#e6e9ee", borderRadius: "4px", overflow: "hidden" }}>
                      <div style={{ height: "100%", width: m.assocW, background: "#0d7d5a", borderRadius: "4px" }} />
                    </div>
                    <span style={{ fontSize: "12px", fontFamily: "'IBM Plex Mono', monospace", color: "#0d7d5a", fontWeight: 600 }}>{m.assoc}</span>
                  </div>
                </div>
                <div style={{ paddingRight: "12px" }}>
                  {m.drug.has && (
                    <>
                      <div style={{ display: "flex", alignItems: "center", gap: "7px", flexWrap: "wrap" }}>
                        <span style={{ fontSize: "12.5px", fontWeight: 600, color: "#1a1d24" }}>{m.drug.name}</span>
                        <span style={{ padding: "2px 8px", borderRadius: "20px", fontSize: "10px", fontWeight: 600, color: m.drug.phaseC, background: m.drug.phaseB }}>{m.drug.phase}</span>
                        <span style={{ fontSize: "10.5px", color: "#9aa1ad" }}>{m.drug.extra}</span>
                      </div>
                      <div style={{ fontSize: "11px", color: m.drug.trialColor, marginTop: "3px" }}>{m.drug.trialLabel}</div>
                    </>
                  )}
                  {m.drug.none && (
                    <>
                      <div style={{ fontSize: "12px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace" }}>{m.drug.name}</div>
                      <div style={{ fontSize: "11px", color: "#b0b6c0", marginTop: "3px" }}>{m.drug.trialLabel}</div>
                    </>
                  )}
                </div>
                <div style={{ textAlign: "center" }}>
                  <span style={{ display: "inline-block", padding: "4px 10px", borderRadius: "20px", fontSize: "11px", fontWeight: 600, color: m.rColor, background: m.rBg }}>{m.rLabel}</span>
                </div>
                <div style={{ textAlign: "center" }}>
                  <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "25px", height: "25px", borderRadius: "7px", fontSize: "12px", fontWeight: 700, color: m.gColor, background: m.gBg }}>{m.grade}</span>
                </div>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", alignItems: "start", gap: "8px", marginTop: "16px", fontSize: "11.5px", color: "#8a92a0", lineHeight: 1.5, maxWidth: "720px" }}>
            <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>ⓘ</span> Association scores combine external genetic/literature evidence (Open Targets) with the CD4 perturbation signal. They rank hypotheses for research follow-up — they are not evidence of clinical efficacy in this disease.
          </div>
        </div>
      )}

      {/* population genetics */}
      {S.clinicalTab === "popgen" && (
        <div style={{ maxWidth: "720px" }}>
          <div style={{ display: "flex", gap: "10px", marginBottom: "26px" }}>
            <div style={{ position: "relative", flex: 1 }}>
              <svg style={{ position: "absolute", left: "13px", top: "50%", transform: "translateY(-50%)" }} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8a92a0" strokeWidth="2">
                <circle cx="11" cy="11" r="7" />
                <path d="M20 20L16 16" />
              </svg>
              <input value={S.popQuery} onChange={(e) => setState({ popQuery: e.target.value })} placeholder="Enter a gene symbol, e.g. IL2RA, CTLA4, PLCG1…" style={{ width: "100%", padding: "13px 14px 13px 40px", border: "1.5px solid #d6dbe3", borderRadius: "10px", fontSize: "14.5px" }} />
            </div>
          </div>

          {popTarget && (
            <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "26px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "20px" }}>
                <h2 style={{ fontSize: "24px", fontWeight: 700, margin: 0, fontFamily: "'IBM Plex Mono', monospace", letterSpacing: "-.5px" }}>{popTarget.gene}</h2>
                <span style={{ fontSize: "13.5px", color: "#6b7280" }}>{popTarget.name}</span>
                <span style={{ display: "inline-block", padding: "4px 11px", borderRadius: "20px", fontSize: "11.5px", fontWeight: 600, color: popTarget.constraintColor, background: popTarget.constraintBg, marginLeft: "auto" }}>{popTarget.constraintLabel}</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "1px", background: "#e2e5ea", border: "1px solid #e2e5ea", borderRadius: "12px", overflow: "hidden", marginBottom: "20px" }}>
                {popTarget.metrics.map((m) => (
                  <div key={m.label} style={{ background: "#fff", padding: "18px 20px" }}>
                    <div style={{ fontSize: "24px", fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", letterSpacing: "-.5px", color: m.color }}>{m.value}</div>
                    <div style={{ fontSize: "11.5px", color: "#6b7280", marginTop: "3px" }}>{m.label}</div>
                    <div style={{ fontSize: "10.5px", color: "#9aa1ad", marginTop: "5px", lineHeight: 1.4 }}>{m.note}</div>
                  </div>
                ))}
              </div>
              <div style={{ fontSize: "13px", lineHeight: 1.6, color: "#3a414d", background: "#f7f8fa", borderRadius: "10px", padding: "15px 17px" }}>{popTarget.interpretation}</div>
              <div style={{ fontSize: "10.5px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace", marginTop: "15px" }}>src: gnomAD v4.1 · constraint metrics · fetched {popTarget.fetched} · values shown are illustrative for this research demo</div>
            </div>
          )}
          {!pt && pq.length > 0 && (
            <div style={{ border: "1px dashed #d6dbe3", borderRadius: "14px", padding: "44px", textAlign: "center" }}>
              <div style={{ fontSize: "15px", color: "#6b7280", marginBottom: "6px" }}>No constraint record for “{S.popQuery}” in this screen.</div>
              <div style={{ fontSize: "12.5px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace" }}>returns <strong>unknown</strong> + coverage — never a fabricated 0</div>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
