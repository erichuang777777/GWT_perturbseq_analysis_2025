import { useMemo } from "react";
import { TARGETS, targetByGene, SOURCE_VERSION } from "../data/dataset";
import { CONSTRAINT_META, DECISION_META, GRADE, READINESS, RED_FLAG_LABELS, REVIEWERS, WKEYS } from "../data/reference";
import type { VoteStatus } from "../data/types";
import { consensus, fmtEffect, fmtFdr, fmtStatus, fmtTs, initials, rankedTargets, similarTargets, subScores } from "../lib/logic";
import { downloadFile } from "../lib/download";
import { useStore } from "../store/store";

const CONDITION_LABEL: Record<string, string> = { Rest: "Rest", Stim8hr: "Stim 8 hr", Stim48hr: "Stim 48 hr" };

export default function Dossier() {
  const { state, setState, navTo, castVote, setVoteNote, clearMyVote, setReviewer, votesFor, myVote } = useStore();
  const S = state;
  const all = TARGETS;
  const R = READINESS;
  const G = GRADE;
  const w = S.weights;

  const t = targetByGene(S.selectedGene) || all[0];
  const call = t.readiness?.call;
  const Rt = call ? R[call] : { label: "Unreviewed", color: "#8a92a0", bg: "#f7f8fa" };
  const Gt = t.grade ? G[t.grade] : { color: "#8a92a0", bg: "#f7f8fa" };

  const wsum = WKEYS.reduce((a, x) => a + (w[x.k] || 0), 0) || 1;
  // Sorting all 7,000+ targets is only a function of the weights, so it's
  // memoized here too -- otherwise every unrelated re-render (a vote click,
  // a note keystroke) would re-rank the whole dataset just to look up one
  // gene's rank.
  const rankedAll = useMemo(() => rankedTargets(w), [w]);
  const tRankInfo = rankedAll.find((x) => x.gene === t.gene)!;
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

  const similar = similarTargets(t, 4).map((st) => {
    const stCall = st.readiness?.call;
    const Rs = stCall ? R[stCall] : { label: "Unreviewed", color: "#8a92a0", bg: "#f7f8fa" };
    return { gene: st.gene, rLabel: Rs.label, rColor: Rs.color, rBg: Rs.bg };
  });

  const DM = DECISION_META;
  const dVotes = votesFor(t.gene);
  const dCons = consensus(dVotes);
  const dMine = myVote(t.gene);
  const decision = {
    reviewers: REVIEWERS.map((r) => ({
      name: r,
      color: r === S.reviewer ? "#fff" : "#4a515e",
      bg: r === S.reviewer ? "#1a5fb4" : "#fff",
      border: r === S.reviewer ? "#1a5fb4" : "#d6dbe3",
    })),
    options: (["advance", "hold", "drop"] as VoteStatus[]).map((st) => {
      const on = !!(dMine && dMine.status === st);
      return { status: st, label: DM[st].label, color: on ? "#fff" : DM[st].color, bg: on ? DM[st].dot : DM[st].bg, border: DM[st].dot };
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
    { label: "|log2 fold-change| (peak condition)", value: fmtEffect(t.effect), color: "#1a1d24" },
    { label: "FDR (BH), peak condition", value: fmtFdr(t.fdr), color: "#1a1d24" },
    { label: "Composite priority", value: String(tRankInfo._comp), color: "#1a5fb4" },
    { label: "Evidence grade", value: t.grade ?? "unknown", color: Gt.color },
    { label: "Cells captured", value: t.nCells != null ? t.nCells.toLocaleString() : "unknown", color: "#1a1d24" },
    { label: "Guides", value: t.nGuides ?? "unknown", color: "#1a1d24" },
    { label: "DE genes (total)", value: t.nTotalDeGenes ?? "unknown", color: "#1a1d24" },
    { label: "Up / down", value: t.nUpGenes != null ? `${t.nUpGenes} / ${t.nDownGenes}` : "unknown", color: "#1a1d24" },
  ];

  const robustnessColor =
    t.crossDonorCorrelationMean == null ? "#9aa1ad" : t.crossDonorCorrelationMean >= 0.6 ? "#0d7d5a" : t.crossDonorCorrelationMean >= 0.35 ? "#b7791f" : "#c0503f";

  const diseases = t.diseases.map((d) => ({
    name: d.name,
    id: d.id,
    score: d.overallScore != null ? d.overallScore.toFixed(2) : "unknown",
    width: d.overallScore != null ? Math.round(d.overallScore * 100) + "%" : "0%",
    source: d.source,
    isLocalExport: d.source.includes("local"),
  }));

  // real tractability flags, grouped by modality — show only modalities/flags that are true
  const modalityLabel: Record<string, string> = { SM: "Small molecule", AB: "Antibody / biologic", PR: "PROTAC / other modality", OC: "Other clinical precedent" };
  const tractRows = Object.entries(t.tractabilityFlags)
    .map(([mod, flags]) => ({ mod, label: modalityLabel[mod] || mod, trueFlags: Object.entries(flags).filter(([, v]) => v).map(([k]) => k) }))
    .filter((r) => r.trueFlags.length > 0);

  const redFlags = t.readiness?.redFlags ?? [];
  const reasonBullets = (t.readiness?.reasons ?? "").split(";").map((s) => s.trim()).filter(Boolean);

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
            {decision.noVotes && <div style={{ fontSize: "12.5px", color: "#a49cbe", padding: "10px 2px" }}>No reviews yet — cast the first call from the panel on the right.</div>}
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
            {decision.hasMine && <div className="navlink" onClick={() => clearMyVote(t.gene)} style={{ fontSize: "11px", color: "#a49cbe", marginTop: "7px" }}>Clear my vote</div>}
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
          Sub-scores are a disclosed formula over real fields (effect size, cross-donor correlation, red flags, gnomAD constraint, disease association) — see the source comment in <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>lib/logic.ts</span>. Change weights in the explorer to re-rank. The <strong>readiness call is computed by the repo's own rule-based engine and does not move with weights</strong>.
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 336px", gap: "26px", alignItems: "start" }}>
        {/* left column */}
        <div style={{ display: "flex", flexDirection: "column", gap: "22px", minWidth: 0 }}>
          {/* statistical evidence */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
              <h3 style={h3}>Statistical evidence</h3>
              <span style={src}>src: target_cards.csv (real screen output)</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "16px" }}>
              {statMetrics.map((m) => (
                <div key={m.label}>
                  <div style={{ fontSize: "20px", fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", letterSpacing: "-.5px", color: m.color }}>{m.value}</div>
                  <div style={{ fontSize: "11px", color: "#6b7280", marginTop: "2px" }}>{m.label}</div>
                </div>
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
          </div>

          {/* downstream footprint: this repo's own signed re-analysis of the same screen */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
              <h3 style={h3}>Downstream footprint</h3>
              <span style={src}>src: signed_ranking_v2 (this repo's signed re-analysis)</span>
            </div>
            {t.downstreamFootprint ? (
              <>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "14px", marginBottom: "12px" }}>
                  <div>
                    <div style={{ fontSize: "18px", fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24" }}>
                      {t.downstreamFootprint.directionalityIndex != null ? t.downstreamFootprint.directionalityIndex.toFixed(2) : "unknown"}
                    </div>
                    <div style={{ fontSize: "11px", color: "#6b7280", marginTop: "2px" }}>Directionality index</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "18px", fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", color: "#0a6e4f" }}>{t.downstreamFootprint.nUp ?? "—"}</div>
                    <div style={{ fontSize: "11px", color: "#6b7280", marginTop: "2px" }}>Up on KO</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "18px", fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", color: "#8a2f2f" }}>{t.downstreamFootprint.nDown ?? "—"}</div>
                    <div style={{ fontSize: "11px", color: "#6b7280", marginTop: "2px" }}>Down on KO</div>
                  </div>
                </div>
                <span
                  style={{
                    display: "inline-block",
                    fontSize: "11.5px",
                    fontWeight: 600,
                    padding: "4px 10px",
                    borderRadius: "20px",
                    color: t.downstreamFootprint.footprintClass === "net_derepressed_on_KO" ? "#0a6e4f" : t.downstreamFootprint.footprintClass === "net_reduced_on_KO" ? "#8a2f2f" : "#5b6270",
                    background: t.downstreamFootprint.footprintClass === "net_derepressed_on_KO" ? "#e4f3ec" : t.downstreamFootprint.footprintClass === "net_reduced_on_KO" ? "#f6e5e5" : "#eef0f3",
                  }}
                >
                  {t.downstreamFootprint.footprintClass.replace(/_/g, " ")}
                </span>
                {t.downstreamFootprint.inGateShortlist && (
                  <span style={{ marginLeft: "8px", fontSize: "10.5px", color: "#9aa1ad" }}>in the 1,235-gene gate shortlist</span>
                )}
                <div style={{ fontSize: "10.5px", color: "#9aa1ad", lineHeight: 1.5, marginTop: "10px" }}>
                  Net transcriptional footprint direction on knockout — NOT a molecular activator/repressor role assignment (a TCR component can be net-derepressed without being a transcriptional repressor).
                </div>
              </>
            ) : (
              <div style={{ fontSize: "12.5px", color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "9px", padding: "11px 14px", fontFamily: "'IBM Plex Mono', monospace" }}>unknown — not in this re-analysis</div>
            )}
          </div>

          {/* concept module membership (real; no fabricated cross-module profile) */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "5px" }}>
              <h3 style={h3}>Immune-concept module</h3>
              <span style={src}>concept modules · M01–M20</span>
            </div>
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
              <div style={{ fontSize: "12.5px", color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "9px", padding: "11px 14px", fontFamily: "'IBM Plex Mono', monospace" }}>
                unknown — not a member of any curated immune-concept module (may be a general chromatin/transcription-machinery gene; see red flags)
              </div>
            )}
            {t.stimulationGated != null && (
              <div style={{ marginTop: "12px", fontSize: "11.5px", color: t.stimulationGated ? "#0a6e4f" : "#6b7280" }}>
                {t.stimulationGated ? "✓ Stimulation-gated — quiet at Rest, active on stimulation (real, from concept_annotation.py)." : "Not flagged stimulation-gated."}
              </div>
            )}
          </div>

          {/* functional-complex clustering: a complement to concept modules, not a replacement */}
          {t.functionalComplexes.length > 0 && (
            <div style={card}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "5px" }}>
                <h3 style={h3}>Functional complex membership</h3>
                <span style={src}>src: CORUM / STRINGdb / KEGG / Reactome clustering</span>
              </div>
              <p style={{ fontSize: "12px", color: "#8a92a0", margin: "0 0 12px", lineHeight: 1.5 }}>
                Real co-regulation cluster overlap with known complex/pathway databases — a complement to the immune-concept modules above, not a replacement.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {t.functionalComplexes.map((c, i) => (
                  <div key={i} style={{ padding: "10px 13px", background: "#f7f8fa", borderRadius: "9px" }}>
                    <div style={{ fontSize: "13px", fontWeight: 600, color: "#1a1d24" }}>{c.clusterAnnotation}</div>
                    <div style={{ fontSize: "11.5px", color: "#8a92a0", marginTop: "2px" }}>{c.bestDescribedBy}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* external evidence: real disease associations */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
              <h3 style={h3}>External evidence &amp; disease links</h3>
              <span style={src}>src: Open Targets (live fetch + local export)</span>
            </div>
            {diseases.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "9px" }}>
                {diseases.map((d) => (
                  <div key={d.id + d.source} className="navlink" onClick={() => navTo("disease", d.id)} style={{ display: "flex", alignItems: "center", gap: "14px", padding: "11px 14px", background: "#f7f8fa", borderRadius: "10px" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ fontSize: "13.5px", fontWeight: 600, color: "#1a1d24" }}>{d.name}</span>
                        {d.isLocalExport && (
                          <span title="From the local 13-indication autoimmune/inflammatory export, not a live per-gene fetch" style={{ fontSize: "9.5px", fontWeight: 600, color: "#6b7280", background: "#eef0f3", padding: "1.5px 6px", borderRadius: "20px" }}>
                            local export
                          </span>
                        )}
                      </div>
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
              <div style={{ fontSize: "12.5px", color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "9px", padding: "11px 14px", fontFamily: "'IBM Plex Mono', monospace" }}>unknown — no disease associations indexed in Open Targets for this gene</div>
            )}
          </div>

          {/* tractability: real flags */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
              <h3 style={h3}>Tractability</h3>
              <span style={src}>src: Open Targets tractability (cached fetch)</span>
            </div>
            {tractRows.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {tractRows.map((r) => (
                  <div key={r.mod} style={{ padding: "11px 14px", background: "#f7f8fa", borderRadius: "10px" }}>
                    <div style={{ fontSize: "13px", fontWeight: 600, color: "#1a1d24", marginBottom: "6px" }}>{r.label}</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                      {r.trueFlags.map((f) => (
                        <span key={f} style={{ fontSize: "11px", fontWeight: 600, color: "#0a6e4f", background: "#e4f3ec", padding: "3px 9px", borderRadius: "20px" }}>✓ {f}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: "12.5px", color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "9px", padding: "11px 14px", fontFamily: "'IBM Plex Mono', monospace" }}>unknown — no positive tractability flags indexed in Open Targets</div>
            )}
            {t.readiness?.tractabilityModality && t.readiness.tractabilityModality !== "unknown" && (
              <div style={{ fontSize: "11px", color: "#9aa1ad", marginTop: "10px" }}>Readiness-engine tractability class: {t.readiness.tractabilityModality}</div>
            )}
          </div>

          {/* membrane / ADC overlay: a different vocabulary than Open Targets
              tractability above, so kept in its own card rather than merged in */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
              <h3 style={h3}>Membrane / ADC overlay</h3>
              <span style={src}>src: project ADC target-discovery DB × GWT overlap</span>
            </div>
            {t.membraneOverlay ? (
              <div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: t.membraneOverlay.druggablePathway ? "10px" : 0 }}>
                  {t.membraneOverlay.isSurfaceProtein && <span style={{ fontSize: "11px", fontWeight: 600, color: "#0a6e4f", background: "#e4f3ec", padding: "3px 9px", borderRadius: "20px" }}>✓ surface protein</span>}
                  {t.membraneOverlay.hasTransmembraneDomain && <span style={{ fontSize: "11px", fontWeight: 600, color: "#0a6e4f", background: "#e4f3ec", padding: "3px 9px", borderRadius: "20px" }}>✓ transmembrane domain</span>}
                  {t.membraneOverlay.hasExtracellularDomain && <span style={{ fontSize: "11px", fontWeight: 600, color: "#0a6e4f", background: "#e4f3ec", padding: "3px 9px", borderRadius: "20px" }}>✓ extracellular domain</span>}
                  {t.membraneOverlay.isDruggable && <span style={{ fontSize: "11px", fontWeight: 600, color: "#0a6e4f", background: "#e4f3ec", padding: "3px 9px", borderRadius: "20px" }}>✓ druggable genome</span>}
                  {!t.membraneOverlay.isSurfaceProtein && !t.membraneOverlay.hasTransmembraneDomain && !t.membraneOverlay.hasExtracellularDomain && !t.membraneOverlay.isDruggable && (
                    <span style={{ fontSize: "12px", color: "#6b7280" }}>Checked — no positive membrane/druggability flags for this gene.</span>
                  )}
                </div>
                {t.membraneOverlay.druggablePathway && (
                  <div style={{ fontSize: "11px", color: "#8a92a0", lineHeight: 1.5 }}>{t.membraneOverlay.druggablePathway.split(";").join(" · ")}</div>
                )}
              </div>
            ) : (
              <div style={{ fontSize: "12.5px", color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "9px", padding: "11px 14px", fontFamily: "'IBM Plex Mono', monospace" }}>unknown — gene not in the ADC × GWT overlap overlay (~50% coverage)</div>
            )}
          </div>

          {/* clinical trial evidence + literature (real) */}
          {(t.clinicalTrials.length > 0 || t.literature.length > 0) && (
            <div style={card}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
                <h3 style={h3}>Clinical trial &amp; literature evidence</h3>
                <span style={src}>src: ClinicalTrials.gov / PubMed (cached fetch)</span>
              </div>
              {t.clinicalTrials.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: "8px", marginBottom: t.literature.length ? "16px" : 0 }}>
                  {t.clinicalTrials.map((c) => (
                    <a key={c.nctId} href={c.url} target="_blank" rel="noreferrer" style={{ display: "block", padding: "11px 14px", background: "#f7f8fa", borderRadius: "10px" }}>
                      <div style={{ fontSize: "13px", fontWeight: 600, color: "#1a1d24" }}>{c.title}</div>
                      <div style={{ fontSize: "11px", color: "#8a92a0", marginTop: "3px" }}>
                        {c.nctId} · {c.phase || "phase unknown"} · {fmtStatus(c.status)} · {c.conditions.join(", ")}
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
            </div>
          )}

          {/* real per-condition DE signal (replaces the old fabricated perturbation-signature + expression panels) */}
          <div style={card}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
              <h3 style={h3}>Signal across culture conditions</h3>
              <span style={src}>src: target_cards.csv · Rest / Stim 8 hr / Stim 48 hr</span>
            </div>
            <p style={{ fontSize: "12px", color: "#8a92a0", margin: "0 0 16px", lineHeight: 1.5 }}>
              Real differential-expression breadth per condition (this repo's DE pipeline, not a raw expression level). {t.stimulationGated ? "This target is stimulation-gated." : ""}
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {t.conditions.map((c) => {
                const maxDe = Math.max(...t.conditions.map((x) => x.nTotalDeGenes ?? 0), 1);
                const width = Math.round(((c.nTotalDeGenes ?? 0) / maxDe) * 100) + "%";
                const color = c.grade != null && c.grade >= 3 ? "#1a5fb4" : c.grade != null && c.grade === 2 ? "#4f83cc" : "#9dbde8";
                return (
                  <div key={c.condition} style={{ display: "grid", gridTemplateColumns: "96px 1fr 150px", gap: "12px", alignItems: "center" }}>
                    <div style={{ fontSize: "12.5px", color: "#4a515e" }}>{CONDITION_LABEL[c.condition] ?? c.condition}</div>
                    <div style={{ height: "10px", background: "#f0f2f5", borderRadius: "5px", overflow: "hidden" }}>
                      <div style={{ height: "100%", width, background: color, borderRadius: "5px" }} />
                    </div>
                    <div style={{ fontSize: "11.5px", textAlign: "right", fontFamily: "'IBM Plex Mono', monospace", color: "#4a515e" }}>
                      {c.nTotalDeGenes ?? "—"} DE ({c.nUpGenes ?? "—"}↑/{c.nDownGenes ?? "—"}↓) grade {c.grade ?? "—"}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* independent screen replication: real hits from other published studies */}
          {t.externalScreens.length > 0 && (
            <div style={card}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                <h3 style={h3}>Independent screen replication</h3>
                <span style={src}>src: 4 published external CRISPR screens</span>
              </div>
              <p style={{ fontSize: "12px", color: "#8a92a0", margin: "0 0 14px", lineHeight: 1.5 }}>
                Real MAGeCK-style enrichment statistics from separately published studies — does an independent screen also see a hit at this gene. neg = depleted for the phenotype, pos = enriched.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {t.externalScreens.map((h, i) => (
                  <div key={i} style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr 1fr", gap: "10px", alignItems: "center", padding: "9px 12px", background: "#f7f8fa", borderRadius: "9px" }}>
                    <div>
                      <div style={{ fontSize: "12.5px", fontWeight: 600, color: "#1a1d24" }}>{h.study}</div>
                      <div style={{ fontSize: "11px", color: "#8a92a0" }}>{h.phenotype}</div>
                    </div>
                    <div style={{ fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", color: h.negFdr != null && h.negFdr < 0.05 ? "#0a6e4f" : "#6b7280" }}>
                      neg fdr {fmtFdr(h.negFdr)}
                    </div>
                    <div style={{ fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", color: h.posFdr != null && h.posFdr < 0.05 ? "#0a6e4f" : "#6b7280" }}>
                      pos fdr {fmtFdr(h.posFdr)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* right rail */}
        <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px", background: "#fafbfc" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 700, margin: "0 0 13px" }}>Readiness rationale</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "9px", marginBottom: redFlags.length ? "14px" : 0 }}>
              {reasonBullets.map((text, i) => (
                <div key={i} style={{ display: "flex", gap: "10px", alignItems: "flex-start" }}>
                  <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: "#2563c9", flexShrink: 0, marginTop: "5px" }} />
                  <div style={{ fontSize: "12px", lineHeight: 1.45, color: "#4a515e" }}>{text}</div>
                </div>
              ))}
            </div>
            {redFlags.length > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginBottom: "12px" }}>
                {redFlags.map((f) => (
                  <div key={f} style={{ fontSize: "11.5px", color: "#8a2f2f", background: "#f6e5e5", borderRadius: "8px", padding: "7px 10px" }}>⚑ {RED_FLAG_LABELS[f] ?? f}</div>
                ))}
              </div>
            )}
            {t.readiness?.nextValidationStep && (
              <div style={{ fontSize: "11.5px", lineHeight: 1.5, color: "#1f56b8", background: "#e8f0fc", borderRadius: "8px", padding: "9px 11px" }}>
                <strong>Next validation step:</strong> {t.readiness.nextValidationStep}
              </div>
            )}
          </div>

          {/* safety window: real red flags + safety liabilities + constraint, no fabricated score */}
          <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
              <h3 style={{ fontSize: "14px", fontWeight: 700, margin: 0 }}>Safety signals</h3>
              <span style={{ fontSize: "10px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace" }}>descriptive</span>
            </div>
            {t.safetyLiabilities.length > 0 ? (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "10px" }}>
                {t.safetyLiabilities.map((s) => (
                  <span key={s.event} style={{ fontSize: "11px", fontWeight: 600, color: "#8a2f2f", background: "#f6e5e5", padding: "3px 9px", borderRadius: "20px" }}>{s.event}</span>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: "11.5px", color: "#6b7280", marginBottom: "10px" }}>No adverse-event liabilities indexed in Open Targets for this gene.</div>
            )}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginBottom: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: "12.5px", color: "#6b7280" }}>Off-context GTEx breadth</span>
                <span style={{ fontSize: "12.5px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24" }}>
                  {t.readiness?.safetyWindowScore != null && t.readiness.safetyWindowScore !== "unknown" ? `${t.readiness.safetyWindowScore} tissues` : "unknown"}
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: "12.5px", color: "#6b7280" }}>Composite safety liability</span>
                <span
                  style={{
                    fontSize: "12.5px",
                    fontWeight: 600,
                    color:
                      t.readiness?.compositeSafetyLiability === "high"
                        ? "#8a2f2f"
                        : t.readiness?.compositeSafetyLiability === "moderate"
                          ? "#8a6a1f"
                          : t.readiness?.compositeSafetyLiability === "low"
                            ? "#0a6e4f"
                            : "#9aa1ad",
                  }}
                >
                  {t.readiness?.compositeSafetyLiability ?? "unknown"}
                </span>
              </div>
              <div style={{ fontSize: "10.5px", color: "#9aa1ad", lineHeight: 1.4 }}>
                gnomAD LoF constraint + GTEx off-context breadth — higher constraint plus broader expression = more concern; a liability flag, not a "this target is safe" signal.
              </div>
            </div>
            {redFlags.length > 0 ? (
              <div style={{ fontSize: "11.5px", color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "8px", padding: "9px 11px" }}>
                {redFlags.length} pipeline red flag{redFlags.length === 1 ? "" : "s"} triggered (see rationale panel).
              </div>
            ) : (
              <div style={{ fontSize: "11.5px", color: "#6b7280" }}>No pipeline red flags triggered for this target.</div>
            )}
          </div>

          {/* prior curated avoid/delivery assessment -- this repo's own editorial
              judgment, deliberately labeled apart from the raw evidence sources above */}
          {t.avoidAssessment && (
            <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
                <h3 style={{ fontSize: "14px", fontWeight: 700, margin: 0 }}>This repo's prior avoid/delivery assessment</h3>
                <span style={{ fontSize: "10px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace" }}>editorial</span>
              </div>
              <div style={{ fontSize: "10.5px", color: "#9aa1ad", lineHeight: 1.4, marginBottom: "12px" }}>
                A prior curated judgment layer from this repo's own research, not a new independent measurement — shown separately from the evidence sources above for that reason.
              </div>
              <span
                style={{
                  display: "inline-block",
                  fontSize: "11.5px",
                  fontWeight: 700,
                  padding: "4px 10px",
                  borderRadius: "20px",
                  marginBottom: "10px",
                  color:
                    t.avoidAssessment.avoidTier === "avoid" ? "#fff" : t.avoidAssessment.avoidTier === "high_risk" ? "#8a2f2f" : t.avoidAssessment.avoidTier === "caution" ? "#8a6a1f" : "#0a6e4f",
                  background:
                    t.avoidAssessment.avoidTier === "avoid" ? "#8a2f2f" : t.avoidAssessment.avoidTier === "high_risk" ? "#f6e5e5" : t.avoidAssessment.avoidTier === "caution" ? "#fbf1de" : "#e4f3ec",
                }}
              >
                {t.avoidAssessment.avoidTier}
              </span>
              {t.avoidAssessment.avoidFlags.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "4px", marginBottom: "12px" }}>
                  {t.avoidAssessment.avoidFlags.map((f) => (
                    <div key={f} style={{ fontSize: "11.5px", color: "#6b7280" }}>· {f}</div>
                  ))}
                </div>
              )}
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontSize: "12.5px", color: "#6b7280" }}>Delivery modality</span>
                  <span style={{ fontSize: "12px", fontWeight: 600, color: "#1a1d24", textAlign: "right", maxWidth: "180px" }}>{t.avoidAssessment.deliveryModality}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontSize: "12.5px", color: "#6b7280" }}>Kinetic archetype</span>
                  <span style={{ fontSize: "12px", fontWeight: 600, color: "#1a1d24" }}>{t.avoidAssessment.kineticArchetype.replace(/_/g, " ")}</span>
                </div>
              </div>
            </div>
          )}

          <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 700, margin: "0 0 13px" }}>Population genetics</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: "12.5px", color: "#6b7280" }}>gnomAD LOEUF</span>
                <span style={{ fontSize: "12.5px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24" }}>{t.gnomad.loeuf != null ? t.gnomad.loeuf.toFixed(3) : "unknown"}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: "12.5px", color: "#6b7280" }}>pLI</span>
                <span style={{ fontSize: "12.5px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24" }}>{t.gnomad.pli != null ? t.gnomad.pli.toFixed(3) : "unknown"}</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: "12.5px", color: "#6b7280" }}>Constraint tier</span>
                <span style={{ fontSize: "12.5px", fontWeight: 600, color: t.gnomad.constraintTier ? CONSTRAINT_META[t.gnomad.constraintTier].color : "#9aa1ad" }}>
                  {t.gnomad.constraintTier ? CONSTRAINT_META[t.gnomad.constraintTier].label : "unknown"}
                </span>
              </div>
            </div>
            <div style={{ fontSize: "10.5px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace", marginTop: "13px", paddingTop: "12px", borderTop: "1px dashed #e2e5ea", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span>src: gnomAD v4</span>
              <span className="navlink" onClick={() => navTo("popgen", t.gene)} style={{ color: "#1a5fb4" }}>Open lookup →</span>
            </div>

            <div style={{ marginTop: "16px", paddingTop: "14px", borderTop: "1px dashed #e2e5ea" }}>
              <div style={{ fontSize: "11px", fontWeight: 700, color: "#8a92a0", textTransform: "uppercase" as const, letterSpacing: ".5px", marginBottom: "8px" }}>
                Lymphocyte-count LoF burden
              </div>
              {t.populationBurden ? (
                <>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
                    <span style={{ fontSize: "12.5px", color: "#6b7280" }}>Effect estimate (95% CI)</span>
                    <span style={{ fontSize: "12.5px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24" }}>
                      {t.populationBurden.effectEstimate != null ? t.populationBurden.effectEstimate.toFixed(3) : "unknown"}
                      {t.populationBurden.ci95Lower != null && t.populationBurden.ci95Upper != null
                        ? ` [${t.populationBurden.ci95Lower.toFixed(3)}, ${t.populationBurden.ci95Upper.toFixed(3)}]`
                        : ""}
                    </span>
                  </div>
                  <div style={{ fontSize: "11.5px", lineHeight: 1.5, color: t.populationBurden.ciExcludesZero ? "#1a1d24" : "#6b7280" }}>
                    {t.populationBurden.hypothesis}
                  </div>
                </>
              ) : (
                <div style={{ fontSize: "11.5px", color: "#9aa1ad" }}>unknown — gene not in the UK Biobank burden estimate table</div>
              )}
              <div style={{ fontSize: "10.5px", color: "#9aa1ad", marginTop: "8px" }}>
                src: UK Biobank exome-wide LoF burden (Backman et al. 2021) — {t.populationBurden?.caveat ?? "population-level statistical association, not a patient-level prediction"}
              </div>
            </div>
          </div>

          <div style={{ border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 700, margin: "0 0 4px" }}>Targets like this</h3>
            <p style={{ fontSize: "11px", color: "#8a92a0", margin: "0 0 13px", lineHeight: 1.45 }}>Other screened targets sharing this gene's assigned concept module (real membership).</p>
            {similar.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                {similar.map((s) => (
                  <div key={s.gene} className="rowhover navlink" onClick={() => navTo("gene", s.gene)} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "8px 9px", borderRadius: "9px" }}>
                    <div style={{ fontSize: "13px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24", width: "70px" }}>{s.gene}</div>
                    <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: "20px", fontSize: "10.5px", fontWeight: 600, color: s.rColor, background: s.rBg }}>{s.rLabel}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ fontSize: "11.5px", color: "#9aa1ad" }}>No other screened targets share this gene's module.</div>
            )}
          </div>

          <button
            onClick={() => {
              const payload = {
                sourceVersion: SOURCE_VERSION,
                exportedFrom: "CD4 Target Discovery Portal (client-side export; no server involved)",
                target: t,
              };
              downloadFile(`cd4-dossier_${t.gene}.json`, JSON.stringify(payload, null, 2), "application/json");
            }}
            style={{ width: "100%", padding: "12px", border: "1.5px solid #1a5fb4", borderRadius: "10px", background: "#fff", color: "#1a5fb4", fontSize: "13.5px", fontWeight: 600, cursor: "pointer" }}
          >
            Export target dossier (JSON)
          </button>
        </div>
      </div>
    </main>
  );
}
