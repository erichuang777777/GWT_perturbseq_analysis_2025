import { useState } from "react";
import { DECISION_META, REVIEWERS } from "../../data/reference";
import type { VoteStatus } from "../../data/types";
import { consensus, fmtTs, initials } from "../../lib/logic";
import { useStore } from "../../store/store";

// Human reviewer voting layer: sits on top of the evidence, never written
// back into it. Self-contained -- pulls its own store slice by gene.
// Collapsed by default (human judgement is opt-in, layered on the evidence).
export default function ReviewerDecisionPanel({ gene }: { gene: string }) {
  const { state, castVote, setVoteNote, clearMyVote, setReviewer, votesFor, myVote } = useStore();
  const [open, setOpen] = useState(false);
  const DM = DECISION_META;
  const dVotes = votesFor(gene);
  const dCons = consensus(dVotes);
  const dMine = myVote(gene);

  const reviewers = REVIEWERS.map((r) => ({
    name: r,
    color: r === state.reviewer ? "#fff" : "#4a515e",
    bg: r === state.reviewer ? "#1a5fb4" : "#fff",
    border: r === state.reviewer ? "#1a5fb4" : "#d6dbe3",
  }));
  const options = (["advance", "hold", "drop"] as VoteStatus[]).map((st) => {
    const on = !!(dMine && dMine.status === st);
    return { status: st, label: DM[st].label, color: on ? "#fff" : DM[st].color, bg: on ? DM[st].dot : DM[st].bg, border: DM[st].dot };
  });
  const votes = dVotes.map((v) => ({
    reviewer: v.reviewer,
    initials: initials(v.reviewer),
    label: DM[v.status].label,
    color: DM[v.status].color,
    bg: DM[v.status].bg,
    dot: DM[v.status].dot,
    ts: fmtTs(v.ts),
    note: v.note,
    hasNote: !!(v.note && v.note.trim()),
  }));
  const tally = (["advance", "hold", "drop"] as VoteStatus[])
    .filter((st) => dCons.counts && dCons.counts[st])
    .map((st) => dCons.counts[st] + " " + DM[st].label.toLowerCase())
    .join("  ·  ");

  return (
    <div style={{ border: "1.5px dashed #c7bfe0", borderRadius: "14px", padding: "18px 22px", marginBottom: "22px", background: "#faf9fd" }}>
      <div
        className="navlink"
        onClick={() => setOpen((o) => !o)}
        style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "16px", flexWrap: "wrap", marginBottom: open ? "14px" : 0, cursor: "pointer" }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "12px", color: "#8a80a8", transform: open ? "rotate(90deg)" : "none", transition: "transform .12s", display: "inline-block" }}>▸</span>
          <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px", fontWeight: 600, letterSpacing: "1px", textTransform: "uppercase", color: "#6b40b8", background: "#efe9fb", padding: "4px 9px", borderRadius: "5px" }}>Reviewer decision</span>
          <span style={{ fontSize: "11.5px", color: "#8a80a8" }}>Human judgement — layered on the evidence, never written back into it.{!open && " (click to open)"}</span>
        </div>
        <div style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
          <span style={{ display: "inline-flex", alignItems: "center", gap: "7px", padding: "5px 12px", borderRadius: "20px", fontSize: "12.5px", fontWeight: 600, color: DM[dCons.status].color, background: DM[dCons.status].bg }}>
            <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: DM[dCons.status].dot }} />
            {DM[dCons.status].label}
          </span>
          <span style={{ fontSize: "11.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#8a80a8" }}>{tally}</span>
        </div>
      </div>

      {open && <>
      <div style={{ display: "flex", alignItems: "flex-start", gap: "8px", padding: "9px 12px", marginBottom: "14px", background: "#efe9fb", border: "1px solid #d9cef0", borderRadius: "9px" }}>
        <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "12px", color: "#6b40b8", flexShrink: 0, marginTop: "1px" }}>ⓘ</span>
        <span style={{ fontSize: "11.5px", lineHeight: 1.5, color: "#5b4a86" }}>
          <strong>Demonstration reviewers</strong> — A. Okafor, R. Mehta, L. Sørensen and J. Park are fictional demo personas. Votes are stored only in your
          browser (localStorage) and are not real review records; they are never sent anywhere or written back into the evidence.
        </span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: "24px", alignItems: "start" }}>
        <div>
          {votes.length > 0 ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {votes.map((v) => (
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
          ) : (
            <div style={{ fontSize: "12.5px", color: "#a49cbe", padding: "10px 2px" }}>No reviews yet — cast the first call from the panel on the right.</div>
          )}
        </div>

        <div style={{ borderLeft: "1px solid #ece8f5", paddingLeft: "20px" }}>
          <div style={{ fontSize: "10.5px", fontWeight: 700, letterSpacing: ".5px", textTransform: "uppercase", color: "#a49cbe", marginBottom: "7px" }}>Voting as</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "5px", marginBottom: "14px" }}>
            {reviewers.map((rv) => (
              <div key={rv.name} className="navlink" onClick={() => setReviewer(rv.name)} title={rv.name} style={{ fontSize: "11px", fontWeight: 600, padding: "4px 9px", borderRadius: "20px", border: `1.5px solid ${rv.border}`, background: rv.bg, color: rv.color }}>{rv.name}</div>
            ))}
          </div>
          <div style={{ fontSize: "10.5px", fontWeight: 700, letterSpacing: ".5px", textTransform: "uppercase", color: "#a49cbe", marginBottom: "7px" }}>Your call</div>
          <div style={{ display: "flex", gap: "6px", marginBottom: "11px" }}>
            {options.map((op) => (
              <div key={op.status} className="navlink" onClick={() => castVote(gene, op.status)} style={{ flex: 1, textAlign: "center", padding: "8px 0", borderRadius: "8px", border: `1.5px solid ${op.border}`, background: op.bg, color: op.color, fontSize: "12.5px", fontWeight: 600 }}>{op.label}</div>
            ))}
          </div>
          <textarea
            key={gene + "|" + state.reviewer}
            defaultValue={dMine ? dMine.note : ""}
            placeholder="Rationale note (optional)…"
            onBlur={(e) => setVoteNote(gene, e.target.value)}
            style={{ width: "100%", minHeight: "56px", resize: "vertical", padding: "8px 10px", border: "1.5px solid #e0dcec", borderRadius: "8px", fontSize: "12px", color: "#3a414d", lineHeight: 1.45 }}
          />
          {dMine && <div className="navlink" onClick={() => clearMyVote(gene)} style={{ fontSize: "11px", color: "#a49cbe", marginTop: "7px" }}>Clear my vote</div>}
        </div>
      </div>
      </>}
    </div>
  );
}
