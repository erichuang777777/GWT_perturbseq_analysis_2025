import { DECISION_META, GRADE, MODULES, READINESS, REVIEWERS, WKEYS } from "../data/reference";
import { TARGETS } from "../data/targets";
import type { VoteStatus } from "../data/types";
import {
  EXPRESSION,
  PERTURB,
  consensus,
  fmtTs,
  initials,
  pct,
  rankedTargets,
  similarTargets,
  subScores,
  targetByGene,
  tractability,
} from "../lib/logic";
import { useStore } from "../store/store";

const conceptColor = (v: number) => (v >= 0.7 ? "#1a5fb4" : v >= 0.45 ? "#4f83cc" : "#9dbde8");

export default function Dossier() {
  const { state, setState, navTo, castVote, setVoteNote, clearMyVote, setReviewer, votesFor, myVote } =
    useStore();
  const S = state;
  const all = TARGETS;
  const R = READINESS;
  const G = GRADE;
  const w = S.weights;

  const t = targetByGene(S.selectedGene) || all[0];
  const Rt = R[t.call];
  const Gt = G[t.grade];
  const Mt = MODULES[t.mod];

  const wsum = WKEYS.reduce((a, x) => a + (w[x.k] || 0), 0) || 1;
  const rankedAll = rankedTargets(w);
  const tRankInfo = rankedAll.find((x) => x.gene === t.gene) || { _rank: t.rank, _comp: t.score };
  const subs = subScores(t);

  let contribTotal = 0;
  WKEYS.forEach((x) => (contribTotal += (w[x.k] || 0) * subs[x.k]));
  contribTotal = contribTotal || 1;
  const breakdown = WKEYS.map((x) => {
    const contrib = (w[x.k] || 0) * subs[x.k];
    return {
      k: x.k,
      label: x.label,
      color: x.color,
      sub: subs[x.k],
      weightPct: Math.round(((w[x.k] || 0) / wsum) * 100),
      width: ((contrib / contribTotal) * 100).toFixed(1) + "%",
      contribPct: Math.round((contrib / contribTotal) * 100),
    };
  });

  const similar = similarTargets(t, 4).map(({ t: st, sim }) => {
    const Rs = R[st.call];
    return { gene: st.gene, sim: Math.round(sim * 100) + "%", rLabel: Rs.label, rColor: Rs.color, rBg: Rs.bg };
  });

  const geneSet: Record<string, boolean> = {};
  all.forEach((x) => (geneSet[x.gene] = true));

  const tr = tractability(t);
  const tract = {
    known: tr.known,
    unknown: !tr.known,
    modality: [
      { label: "Small molecule", ok: tr.modality.sm },
      { label: "Antibody / biologic", ok: tr.modality.ab },
      { label: "Other clinical", ok: tr.known && !tr.modality.sm && !tr.modality.ab },
    ].map((m) => ({
      label: m.label,
      mark: m.ok ? "✓" : "—",
      color: m.ok ? "#0a6e4f" : "#b0b6c0",
      bg: m.ok ? "#e4f3ec" : "#f4f6f8",
      border: m.ok ? "#bfe4d3" : "#e6e9ee",
    })),
    drugs: tr.drugs.map((d) => ({
      drug: d.drug,
      phase: d.phase,
      moa: d.moa,
      approved: d.approved,
      phaseC: d.phase === "Approved" ? "#0a6e4f" : d.phase === "Withdrawn" ? "#8a2f2f" : "#1f56b8",
      phaseB: d.phase === "Approved" ? "#e4f3ec" : d.phase === "Withdrawn" ? "#f6e5e5" : "#e8f0fc",
    })),
  };

  const pb = PERTURB(t);
  const mkPg = (x: { gene: string; fc: number }) => ({
    gene: x.gene,
    fc: (x.fc > 0 ? "+" : "") + x.fc.toFixed(2),
    isTarget: !!geneSet[x.gene],
    geneColor: geneSet[x.gene] ? "#1a5fb4" : "#3a414d",
    width: Math.min(100, (Math.abs(x.fc) / 2.4) * 100) + "%",
  });
  const perturbation = { up: pb.up.map(mkPg), down: pb.down.map(mkPg) };

  const expression = EXPRESSION(t).map((e) => ({
    condition: e.condition,
    level: e.level.toFixed(2),
    width: Math.round(e.level * 100) + "%",
    color: e.level >= 0.66 ? "#1a5fb4" : e.level >= 0.4 ? "#4f83cc" : "#9dbde8",
  }));

  const DM = DECISION_META;
  const dVotes = votesFor(t.gene);
  const dCons = consensus(dVotes);
  const dMine = myVote(t.gene);
  const decision = {
    reviewers: REVIEWERS.map((r) => ({
      name: r,
      active: r === S.reviewer,
      color: r === S.reviewer ? "#fff" : "#4a515e",
      bg: r === S.reviewer ? "#1a5fb4" : "#fff",
      border: r === S.reviewer ? "#1a5fb4" : "#d6dbe3",
    })),
    options: (["advance", "hold", "drop"] as VoteStatus[]).map((st) => {
      const on = !!(dMine && dMine.status === st);
      return {
        status: st,
        label: DM[st].label,
        color: on ? "#fff" : DM[st].color,
        bg: on ? DM[st].dot : DM[st].bg,
        border: DM[st].dot,
      };
    }),
    hasMine: !!dMine,
    noteKey: t.gene + "|" + S.reviewer,
    myNote: dMine ? dMine.note : "",
    votes: dVotes.map((v) => ({
      reviewer: v.reviewer,
      initials: initials(v.reviewer),
      label: DM[v.status].label,
      color: DM[v.status].color,
      bg: DM[v.status].bg,
      dot: DM[v.status].dot,
      ts: fmtTs(v.ts),
      note: v.note,
      hasNote: !!(v.note && v.note.trim()),
    })),
    hasVotes: dVotes.length > 0,
    noVotes: dVotes.length === 0,
    consensusLabel: DM[dCons.status].label,
    consensusColor: DM[dCons.status].color,
    consensusBg: DM[dCons.status].bg,
    consensusDot: DM[dCons.status].dot,
    tally: (["advance", "hold", "drop"] as VoteStatus[])
      .filter((st) => dCons.counts && dCons.counts[st])
      .map((st) => dCons.counts[st] + " " + DM[st].label.toLowerCase())
      .join("  ·  "),
  };

  const statMetrics = [
    { label: "|log2 fold-change|", value: t.effect, color: "#1a1d24" },
    { label: "FDR (BH)", value: t.fdr, color: "#1a1d24" },
    { label: "Composite priority", value: String(tRankInfo._comp), color: "#1a5fb4" },
    { label: "Evidence grade", value: t.grade, color: Gt.color },
  ];
  const concepts = t.concepts.map(([id, name, v]) => ({
    id,
    name,
    width: v == null ? "0%" : pct(v),
    color: v == null ? "#e6e9ee" : conceptColor(v),
    display: v == null ? "unknown" : v.toFixed(2),
    valColor: v == null ? "#b7791f" : "#4a515e",
  }));
  const diseases = t.diseases.map(([name, efo, sc]) => ({ name, efo, score: sc.toFixed(2), width: pct(sc) }));
  const rationale = t.rationale.map(([dot, text]) => ({ dot, text }));
  const popgen = t.pop.map(([label, value]) => ({ label, value }));
  const safetyColor = t.safety >= 75 ? "#0d7d5a" : t.safety >= 55 ? "#b7791f" : "#c0503f";
  const robustnessColor = t.robustness >= 85 ? "#0d7d5a" : t.robustness >= 65 ? "#b7791f" : "#c0503f";

  const card: React.CSSProperties = { border: "1px solid #e2e5ea", borderRadius: "14px", padding: "22px" };
  const h3: React.CSSProperties = { fontSize: "15px", fontWeight: 700, margin: 0 };
  const src: React.CSSProperties = { fontSize: "10.5px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace" };

  return (
    <main style={{ flex: 1, maxWidth: "1120px", margin: "0 auto", width: "100%", padding: "20px 28px 70px" }}>
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

      {/* header */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "24px", paddingBottom: "22px", borderBottom: "1px solid #e2e5ea", marginBottom: "26px" }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "13px", marginBottom: "7px" }}>
            <h1 style={{ fontSize: "34px", fontWeight: 700, letterSpacing: "-.8px", margin: 0, fontFamily: "'IBM Plex Mono', monospace" }}>{t.gene}</h1>
            <span style={{ display: "inline-block", padding: "5px 13px", borderRadius: "20px", fontSize: "13px", fontWeight: 600, color: Rt.color, background: Rt.bg }}>{Rt.label}</span>
            <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "30px", height: "30px", borderRadius: "8px", fontSize: "14px", fontWeight: 700, color: Gt.color, background: Gt.bg }}>{t.grade}</span>
          </div>
          <div style={{ fontSize: "16px", color: "#4a515e" }}>{t.name}</div>
          <div style={{ display: "flex", gap: "8px", marginTop: "13px", flexWrap: "wrap" }}>
            <span className="navlink" onClick={() => navTo("concept", t.mod)} style={{ fontSize: "11.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#1a5fb4", background: "#eaf1fb", padding: "4px 9px", borderRadius: "6px" }}>{t.mod} · {Mt.name.replace(/_/g, " ")} →</span>
            <span style={{ fontSize: "11.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#6b7280", background: "#f2f4f7", padding: "4px 9px", borderRadius: "6px" }}>{t.cat}</span>
            <span style={{ fontSize: "11.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#6b7280", background: "#f2f4f7", padding: "4px 9px", borderRadius: "6px" }}>Ensembl {t.ensembl}</span>
          </div>
        </div>
        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <div style={{ fontSize: "11px", color: "#9aa1ad", fontWeight: 600, letterSpacing: ".5px", textTransform: "uppercase", marginBottom: "4px" }}>Composite priority</div>
          <div style={{ fontSize: "42px", fontWeight: 700, letterSpacing: "-1.5px", color: "#1a5fb4", lineHeight: 1 }}>{tRankInfo._comp}</div>
          <div style={{ fontSize: "12px", color: "#9aa1ad", marginTop: "3px" }}>rank #{tRankInfo._rank} of {all.length}</div>
        </div>
      </div>

      {/* ④ reviewer decision layer */}
      <div style={{ border: "1.5px dashed #c7bfe0", borderRadius: "14px", padding: "18px 22px", marginBottom: "22px", background: "#faf9fd" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "16px", flexWrap: "wrap", marginBottom: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px", fontWeight: 600, letterSpacing: "1px", textTransform: "uppercase", color: "#6b40b8", background: "#efe9fb", padding: "4px 9px", borderRadius: "5px" }}>Reviewer decision</span>
            <span style={{ fontSize: "11.5px", color: "#8a80a8" }}>Human judgement — layered on the evidence, never written back into it.</span>
          </div>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
            <span style={{ display: "inline-flex", alignItems: "center", gap: "7px", padding: "5px 12px", borderRadius: "20px", fontSize: "12.5px", fontWeight: 600, color: decision.consensusColor, background: decision.consensusBg }}>
              <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: decision.consensusDot }} />
              {decision.consensusLabel}
            </span>
            <span style={{ fontSize: "11.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#8a80a8" }}>{decision.tally}</span>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "24px", alignItems: "start" }}>
          <div>
            {decision.hasVotes && (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {decision.votes.map((v) => (
                  <div key={v.reviewer} style={{ display: "flex", alignItems: "flex-start", gap: "11px", padding: "10px 12px", background: "#fff", border: "1px solid #ece8f5", borderRadius: "10px" }}>
                    <div style={{ flexShrink: 0, width: "30px", height: "30px", borderRadius: "50%", background: "#efe9fb", color: "#6b40b8", fontSize: "11px", fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'IBM Plex Mono', monospace" }}>{v.initials}</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
                        <span style={{ fontSize: "13px", fontWeight: 600, color: "#1a1d24" }}>{v.reviewer}</span>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: "5px", padding: "2px 8px", borderRadius: "20px", fontSize: "10.5px", fontWeight: 600, color: v.color, background: v.bg }}>
                          <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: v.dot }} />
                          {v.label}
                        </span>
                        <span style={{ fontSize: "10.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#b0a8c8" }}>{v.ts}</span>
                      </div>
                      {v.hasNote && <div style={{ fontSize: "12px", color: "#5b6270", lineHeight: 1.45, marginTop: "4px" }}>{v.note}</div>}
                    </div>
                  </div>
                ))}
              </div>
            )}
            {decision.noVotes && (
              <div style={{ fontSize: "12.5px", color: "#a49cbe", padding: "10px 2px" }}>No reviews yet — cast the first call from the panel on the right.</div>
            )}
          </div>

          <div style={{ borderLeft: "1px solid #ece8f5", paddingLeft: "20px" }}>
            <div style={{ fontSize: "10.5px", fontWeight: 700, letterSpacing: ".5px", textTransform: "uppercase", color: "#a49cbe", marginBottom: "7px" }}>Voting as</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "5px", marginBottom: "14px" }}>
              {decision.reviewers.map((rv) => (
                <div key={rv.name} className="navlink" onClick={() => setReviewer(rv.name)} title={rv.name} style={{ fontSize: "11px", fontWeight: 600, padding: "4px 9px", borderRadius: "20px", border: `1.5px solid ${rv.border}`, background: rv.bg, color: rv.color }}>{rv.name}</div>
              ))}
            </div>
            <div style={{ fontSize: "10.5px", fontWeight: 700, letterSpacing: ".5px", textTransform: "uppercase", color: "#a49cbe", marginBottom: "7px" }}>Your call</div>
            <div style={{ display: "flex", gap: "6px", marginBottom: "11px" }}>
              {decision.options.map((op) => (
                <div key={op.status} className="navlink" onClick={() => castVote(t.gene, op.status)} style={{ flex: 1, textAlign: "center", padding: "8px 0", borderRadius: "8px", border: `1.5px solid ${op.border}`, background: op.bg, color: op.color, fontSize: "12.5px", fontWeight: 600 }}>{op.label}</div>
              ))}
            </div>
            <textarea
              key={decision.noteKey}
              defaultValue={decision.myNote}
              placeholder="Rationale note (optional)…"
              onBlur={(e) => setVoteNote(t.gene, e.target.value)}
              style={{ width: "100%", minHeight: "56px", resize: "vertical", padding: "8px 10px", border: "1.5px solid #e0dcec", borderRadius: "8px", fontSize: "12px", color: "#3a414d", lineHeight: 1.45 }}
            />
            {decision.hasMine && (
              <div className="navlink" onClick={() => clearMyVote(t.gene)} style={{ fontSize: "11px", color: "#a49cbe", marginTop: "7px" }}>Clear my vote</div>
            )}
          </div>
        </div>
      </div>

      {/* ① composite breakdown */}
      <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "18px 22px", marginBottom: "26px", background: "#fbfcfd" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
          <h3 style={{ fontSize: "14px", fontWeight: 700, margin: 0 }}>How this priority is composed</h3>
          <span style={{ fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", color: "#6b7280" }}>weights: {S.weightPreset}</span>
        </div>
        <div style={{ display: "flex", height: "30px", borderRadius: "8px", overflow: "hidden", marginBottom: "12px" }}>
          {breakdown.map((b) => (
            <div key={b.k} title={b.label} style={{ width: b.width, background: b.color, display: "flex", alignItems: "center", justifyContent: "center", minWidth: 0 }}>
              <span style={{ fontSize: "10.5px", fontWeight: 700, color: "#fff", whiteSpace: "nowrap", overflow: "hidden" }}>{b.contribPct}</span>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "14px" }}>
          {breakdown.map((b) => (
            <div key={b.k} style={{ display: "flex", alignItems: "center", gap: "7px" }}>
              <span style={{ width: "9px", height: "9px", borderRadius: "2px", background: b.color }} />
              <span style={{ fontSize: "11.5px", color: "#4a515e" }}>{b.label}</span>
              <span style={{ fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", color: "#9aa1ad" }}>sub {b.sub} · w {b.weightPct}%</span>
            </div>
          ))}
        </div>
        <div style={{ fontSize: "10.5px", color: "#9aa1ad", marginTop: "11px", lineHeight: 1.45 }}>
          Each segment = weight × sub-score. Change weights in the explorer to re-rank. Sub-scores are fixed evidence; the <strong>readiness call is rule-based and does not move with weights</strong>.
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 336px", gap: "26px", alignItems: "start" }}>
        {/* left column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "22px", minWidth: 0 }}>
          {/* statistical evidence */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
              <h3 style={h3}>Statistical evidence</h3>
              <span style={src}>src: DE_analysis · GWT-CD4 v2026.1</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "16px" }}>
              {statMetrics.map((m) => (
                <div key={m.label}>
                  <div style={{ fontSize: "22px", fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", letterSpacing: "-.5px", color: m.color }}>{m.value}</div>
                  <div style={{ fontSize: "11.5px", color: "#6b7280", marginTop: "2px" }}>{m.label}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: "18px", paddingTop: "16px", borderTop: "1px dashed #e2e5ea" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#6b7280", marginBottom: "6px" }}>
                <span>Robustness across pseudo-replicates</span>
                <span style={{ fontWeight: 600, color: "#1a1d24", fontFamily: "'IBM Plex Mono', monospace" }}>{t.robustness}%</span>
              </div>
              <div style={{ height: "8px", background: "#eef0f3", borderRadius: "5px", overflow: "hidden" }}>
                <div style={{ height: "100%", width: t.robustness + "%", background: robustnessColor, borderRadius: "5px" }} />
              </div>
            </div>
          </div>

          {/* concept profile */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "5px" }}>
              <h3 style={h3}>Immune-concept profile</h3>
              <span style={src}>concept-bottleneck · M01–M20</span>
            </div>
            <p style={{ fontSize: "12px", color: "#8a92a0", margin: "0 0 16px", lineHeight: 1.5 }}>
              Descriptive projection onto CD4 immune concepts. <strong style={{ color: "#7a6a3f" }}>Never feeds the readiness call.</strong> Empty concepts report <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>unknown</span>, never 0.
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: "11px" }}>
              {concepts.map((c) => (
                <div key={c.id} className="navlink" onClick={() => navTo("concept", c.id)} style={{ display: "grid", gridTemplateColumns: "190px 1fr 54px", gap: "12px", alignItems: "center" }}>
                  <div style={{ fontSize: "12.5px", color: "#3a414d", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    <span style={{ fontFamily: "'IBM Plex Mono', monospace", color: "#9aa1ad", fontSize: "10.5px" }}>{c.id}</span> {c.name}
                  </div>
                  <div style={{ height: "9px", background: "#f0f2f5", borderRadius: "5px", overflow: "hidden", position: "relative" }}>
                    <div style={{ height: "100%", width: c.width, background: c.color, borderRadius: "5px" }} />
                  </div>
                  <div style={{ fontSize: "12px", textAlign: "right", fontFamily: "'IBM Plex Mono', monospace", color: c.valColor }}>{c.display}</div>
                </div>
              ))}
            </div>
          </div>

          {/* external evidence */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
              <h3 style={h3}>External evidence &amp; disease links</h3>
              <span style={src}>src: Open Targets · fetched 2026-06-30</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "9px" }}>
              {diseases.map((d) => (
                <div key={d.efo} className="navlink" onClick={() => navTo("disease", d.efo)} style={{ display: "flex", alignItems: "center", gap: "14px", padding: "11px 14px", background: "#f7f8fa", borderRadius: "10px" }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: "13.5px", fontWeight: 600, color: "#1a1d24" }}>{d.name}</div>
                    <div style={{ fontSize: "11.5px", color: "#8a92a0", fontFamily: "'IBM Plex Mono', monospace" }}>{d.efo}</div>
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
          </div>

          {/* ⑤ tractability */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
              <h3 style={h3}>Tractability</h3>
              <span style={src}>src: Open Targets / ChEMBL</span>
            </div>
            <div style={{ display: "flex", gap: "8px", marginBottom: "16px", flexWrap: "wrap" }}>
              {tract.modality.map((m) => (
                <div key={m.label} style={{ display: "inline-flex", alignItems: "center", gap: "7px", padding: "6px 12px", borderRadius: "8px", border: `1px solid ${m.border}`, background: m.bg, color: m.color, fontSize: "12px", fontWeight: 600 }}>
                  <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>{m.mark}</span>
                  {m.label}
                </div>
              ))}
            </div>
            {tract.known && (
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {tract.drugs.map((d) => (
                  <div key={d.drug} style={{ display: "flex", alignItems: "center", gap: "12px", padding: "11px 14px", background: "#f7f8fa", borderRadius: "10px" }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: "13.5px", fontWeight: 600, color: "#1a1d24" }}>{d.drug}</div>
                      <div style={{ fontSize: "11.5px", color: "#8a92a0" }}>{d.moa} · {d.approved}</div>
                    </div>
                    <span style={{ flexShrink: 0, padding: "3px 10px", borderRadius: "20px", fontSize: "11px", fontWeight: 600, color: d.phaseC, background: d.phaseB }}>{d.phase}</span>
                  </div>
                ))}
              </div>
            )}
            {tract.unknown && (
              <div style={{ fontSize: "12.5px", color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "9px", padding: "11px 14px", fontFamily: "'IBM Plex Mono', monospace" }}>unknown — no tractability record indexed</div>
            )}
          </div>

          {/* ⑤ KO perturbation signature */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
              <h3 style={h3}>Perturbation signature</h3>
              <span style={src}>illustrative · Zhu 2025 DE drops in here</span>
            </div>
            <p style={{ fontSize: "12px", color: "#8a92a0", margin: "0 0 16px", lineHeight: 1.5 }}>Top trans-effects when this target is knocked out — what the cell does downstream. Click a target-gene to jump to its dossier.</p>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
              <div>
                <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".4px", textTransform: "uppercase", color: "#2D6CBC", marginBottom: "9px" }}>Up-regulated</div>
                <div style={{ display: "flex", flexDirection: "column", gap: "7px" }}>
                  {perturbation.up.map((g) => (
                    <div key={g.gene} className="navlink" onClick={() => g.isTarget && navTo("gene", g.gene)} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontSize: "12.5px", fontFamily: "'IBM Plex Mono', monospace", fontWeight: 600, color: g.geneColor, width: "66px" }}>{g.gene}</span>
                      <div style={{ flex: 1, height: "7px", background: "#eef2f8", borderRadius: "4px", overflow: "hidden" }}>
                        <div style={{ height: "100%", width: g.width, background: "#2D6CBC", borderRadius: "4px" }} />
                      </div>
                      <span style={{ fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", color: "#2D6CBC", width: "42px", textAlign: "right" }}>{g.fc}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".4px", textTransform: "uppercase", color: "#A8373A", marginBottom: "9px" }}>Down-regulated</div>
                <div style={{ display: "flex", flexDirection: "column", gap: "7px" }}>
                  {perturbation.down.map((g) => (
                    <div key={g.gene} className="navlink" onClick={() => g.isTarget && navTo("gene", g.gene)} style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontSize: "12.5px", fontFamily: "'IBM Plex Mono', monospace", fontWeight: 600, color: g.geneColor, width: "66px" }}>{g.gene}</span>
                      <div style={{ flex: 1, height: "7px", background: "#f7ecec", borderRadius: "4px", overflow: "hidden" }}>
                        <div style={{ height: "100%", width: g.width, background: "#A8373A", borderRadius: "4px" }} />
                      </div>
                      <span style={{ fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", color: "#A8373A", width: "42px", textAlign: "right" }}>{g.fc}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* ⑤ expression across conditions */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
              <h3 style={h3}>Activity across culture conditions</h3>
              <span style={src}>illustrative · rest / stimulated</span>
            </div>
            <p style={{ fontSize: "12px", color: "#8a92a0", margin: "0 0 16px", lineHeight: 1.5 }}>Active regulators shift sharply with stimulation — the study's central finding.</p>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {expression.map((e) => (
                <div key={e.condition} style={{ display: "grid", gridTemplateColumns: "96px 1fr 46px", gap: "12px", alignItems: "center" }}>
                  <div style={{ fontSize: "12.5px", color: "#4a515e" }}>{e.condition}</div>
                  <div style={{ height: "10px", background: "#f0f2f5", borderRadius: "5px", overflow: "hidden" }}>
                    <div style={{ height: "100%", width: e.width, background: e.color, borderRadius: "5px" }} />
                  </div>
                  <div style={{ fontSize: "12px", textAlign: "right", fontFamily: "'IBM Plex Mono', monospace", color: "#4a515e" }}>{e.level}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* right rail */}
        <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px", background: "#fafbfc" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 700, margin: "0 0 13px" }}>Readiness rationale</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "11px" }}>
              {rationale.map((x, i) => (
                <div key={i} style={{ display: "flex", gap: "10px", alignItems: "flex-start" }}>
                  <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: x.dot, flexShrink: 0, marginTop: "5px" }} />
                  <div style={{ fontSize: "12.5px", lineHeight: 1.45, color: "#4a515e" }}>{x.text}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
              <h3 style={{ fontSize: "14px", fontWeight: 700, margin: 0 }}>Safety window</h3>
              <span style={{ fontSize: "10px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace" }}>descriptive</span>
            </div>
            <div style={{ display: "flex", alignItems: "baseline", gap: "8px", margin: "8px 0 4px" }}>
              <div style={{ fontSize: "30px", fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", letterSpacing: "-1px", color: safetyColor }}>{t.safety}</div>
              <div style={{ fontSize: "12px", color: "#9aa1ad" }}>/ 100</div>
            </div>
            <div style={{ height: "7px", background: "#eef0f3", borderRadius: "5px", overflow: "hidden", marginBottom: "12px" }}>
              <div style={{ height: "100%", width: t.safety + "%", background: safetyColor, borderRadius: "5px" }} />
            </div>
            <div style={{ fontSize: "11.5px", lineHeight: 1.5, color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "8px", padding: "9px 11px" }}>{t.safetyNote}</div>
          </div>

          <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 700, margin: "0 0 13px" }}>Population genetics</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {popgen.map((p) => (
                <div key={p.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontSize: "12.5px", color: "#6b7280" }}>{p.label}</span>
                  <span style={{ fontSize: "12.5px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24" }}>{p.value}</span>
                </div>
              ))}
            </div>
            <div style={{ fontSize: "10.5px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace", marginTop: "13px", paddingTop: "12px", borderTop: "1px dashed #e2e5ea", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span>src: gnomAD v4 · fetched 2026-06-30</span>
              <span className="navlink" onClick={() => navTo("popgen", t.gene)} style={{ color: "#1a5fb4" }}>Open lookup →</span>
            </div>
          </div>

          <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 700, margin: "0 0 4px" }}>Targets like this</h3>
            <p style={{ fontSize: "11px", color: "#8a92a0", margin: "0 0 13px", lineHeight: 1.45 }}>Nearest neighbours by immune-concept profile (cosine similarity).</p>
            <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
              {similar.map((s) => (
                <div key={s.gene} className="rowhover navlink" onClick={() => navTo("gene", s.gene)} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "8px 9px", borderRadius: "9px" }}>
                  <div style={{ fontSize: "13px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24", width: "62px" }}>{s.gene}</div>
                  <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: "20px", fontSize: "10.5px", fontWeight: 600, color: s.rColor, background: s.rBg }}>{s.rLabel}</span>
                  <div style={{ flex: 1 }} />
                  <div style={{ fontSize: "12px", fontFamily: "'IBM Plex Mono', monospace", color: "#6b7280" }}>{s.sim}</div>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={() => alert("Exporting " + t.gene + " dossier as JSON with full provenance…\n\nGET /api/targets/" + t.gene + "?format=json")}
            style={{ width: "100%", padding: "12px", border: "1.5px solid #1a5fb4", borderRadius: "10px", background: "#fff", color: "#1a5fb4", fontSize: "13.5px", fontWeight: 600, cursor: "pointer" }}
          >
            Export target dossier (JSON)
          </button>
        </div>
      </div>
    </main>
  );
}
