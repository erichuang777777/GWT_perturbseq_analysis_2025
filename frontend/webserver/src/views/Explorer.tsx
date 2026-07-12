import { useVirtualizer } from "@tanstack/react-virtual";
import { useCallback, useMemo, useRef } from "react";
import { TARGETS } from "../data/dataset";
import { GRADE, READINESS, DECISION_META, WKEYS, WPRESETS } from "../data/reference";
import type { Call, Grade } from "../data/types";
import { consensus, fmtEffect, rankedTargets } from "../lib/logic";
import { useStore } from "../store/store";

const ROW_HEIGHT = 54;
const TABLE_HEIGHT = 700;

export default function Explorer() {
  const { state, setState, applyPreset, inShortlist, toggleShortlist, clearShortlist, votesFor } = useStore();
  const S = state;

  // 660+ real targets means a full re-rank/re-render per slider tick is
  // expensive — coalesce rapid drag events to one update per animation
  // frame instead of committing every native "input" event.
  const pendingWeights = useRef<Record<string, number>>({});
  const rafId = useRef<number | null>(null);
  const flushWeights = useCallback(() => {
    rafId.current = null;
    const pending = pendingWeights.current;
    pendingWeights.current = {};
    setState((s) => ({ weights: { ...s.weights, ...pending }, weightPreset: "Custom" }));
  }, [setState]);
  const setWeight = useCallback(
    (k: string, v: number) => {
      pendingWeights.current[k] = v;
      if (rafId.current == null) rafId.current = requestAnimationFrame(flushWeights);
    },
    [flushWeights],
  );
  const all = TARGETS;
  const R = READINESS;
  const G = GRADE;

  // ---- facets ----
  const readinessFacets = (["advance", "validate", "watchlist", "deprioritize"] as Call[]).map((k) => {
    const sel = !!S.readinessSel[k];
    return {
      k,
      label: R[k].label,
      dot: R[k].dot,
      count: all.filter((t) => t.readiness?.call === k).length,
      color: sel ? R[k].color : "#4a515e",
      bg: sel ? R[k].bg : "transparent",
    };
  });
  const gradeFacets = (["A", "B", "C", "D"] as Grade[]).map((k) => {
    const sel = !!S.gradeSel[k];
    return {
      k,
      label: k,
      count: all.filter((t) => t.grade === k).length,
      color: sel ? G[k].color : "#8a92a0",
      bg: sel ? G[k].bg : "#fff",
      border: sel ? G[k].border : "#e2e5ea",
    };
  });
  const categoryFacets = (["Upstream", "Downstream"] as const).map((k) => {
    const sel = !!S.categorySel[k];
    return {
      k,
      label: k,
      count: all.filter((t) => t.module?.category === k).length,
      color: sel ? "#1a5fb4" : "#4a515e",
      bg: sel ? "#eaf1fb" : "transparent",
    };
  });

  // ---- weights ----
  const w = S.weights;
  const wsum = WKEYS.reduce((a, x) => a + (w[x.k] || 0), 0) || 1;
  const weightControls = WKEYS.map((x) => ({
    k: x.k,
    label: x.label,
    color: x.color,
    value: w[x.k] || 0,
    pct: Math.round(((w[x.k] || 0) / wsum) * 100) + "%",
  }));
  const weightPresets = Object.keys(WPRESETS).map((name) => ({
    name,
    color: S.weightPreset === name ? "#fff" : "#4a515e",
    bg: S.weightPreset === name ? "#1a5fb4" : "#fff",
    border: S.weightPreset === name ? "#1a5fb4" : "#d6dbe3",
  }));

  // ---- filtering + ranking ----
  const q = S.query.trim().toUpperCase();
  const rs = S.readinessSel;
  const gs = S.gradeSel;
  const cs = S.categorySel;
  const anyR = Object.keys(rs).some((k) => rs[k]);
  const anyG = Object.keys(gs).some((k) => gs[k]);
  const anyC = Object.keys(cs).some((k) => cs[k]);
  const filtered = all.filter((t) => {
    if (q && !(t.gene.toUpperCase().includes(q) || t.name.toUpperCase().includes(q))) return false;
    if (anyR && !(t.readiness && rs[t.readiness.call])) return false;
    if (anyG && !(t.grade && gs[t.grade])) return false;
    if (anyC && !(t.module && cs[t.module.category])) return false;
    return true;
  });
  const filtGenes = new Set(filtered.map((t) => t.gene));
  const dfilter = S.decisionFilter;
  // Sorting + composite-scoring all targets is only a function of the
  // weights, so it's memoized separately from filtering/search — otherwise
  // every keystroke in the search box would re-rank all 7,000+ targets.
  const rankedAll = useMemo(() => rankedTargets(w), [w]);
  const rankedFiltered = rankedAll.filter((t) => {
    if (!filtGenes.has(t.gene)) return false;
    if (dfilter !== "all") {
      const c = consensus(votesFor(t.gene));
      if (dfilter === "reviewed") {
        if (c.status === "none") return false;
      } else if (c.status !== dfilter) return false;
    }
    return true;
  });

  // Row view-models are built only for the rows the virtualizer actually
  // mounts, not the whole (possibly 7,000+ row) filtered list.
  const buildRow = useCallback(
    (t: (typeof rankedFiltered)[number]) => {
      const call = t.readiness?.call;
      const R2 = call ? R[call] : { label: "Unreviewed", color: "#8a92a0", bg: "#f7f8fa" };
      const G2 = t.grade ? G[t.grade] : { color: "#8a92a0", bg: "#f7f8fa" };
      const c = consensus(votesFor(t.gene));
      const cm2 = DECISION_META[c.status];
      const listed = inShortlist(t.gene);
      return {
        rank: t._rank,
        comp: t._comp,
        gene: t.gene,
        name: t.name,
        moduleId: t.module?.id ?? "—",
        moduleShort: t.module ? t.module.name.replace(/_/g, " ") : "no assigned concept module",
        effect: fmtEffect(t.effect),
        rLabel: R2.label,
        rColor: R2.color,
        rBg: R2.bg,
        grade: t.grade ?? "—",
        gColor: G2.color,
        gBg: G2.bg,
        checkBg: listed ? "#1a5fb4" : "#fff",
        checkBorder: listed ? "#1a5fb4" : "#c8ced7",
        checkOpacity: listed ? "1" : "0.35",
        decLabel: c.n ? (c.split ? "split" : cm2.label) : "—",
        decColor: cm2.color,
        decBg: cm2.bg,
        decDot: cm2.dot,
      };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [votesFor, inShortlist],
  );

  const decisionFacets = [
    { k: "all", label: "All" },
    { k: "advance", label: "Advance" },
    { k: "hold", label: "Hold" },
    { k: "drop", label: "Drop" },
    { k: "split", label: "No consensus" },
  ].map((d) => ({
    k: d.k,
    label: d.label,
    color: dfilter === d.k ? "#fff" : "#4a515e",
    bg: dfilter === d.k ? "#0d7d5a" : "transparent",
  }));

  // 7,000+ real targets can't all be mounted as DOM rows at once -- only
  // render the rows currently scrolled into view.
  const scrollRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: rankedFiltered.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 12,
  });

  const slGenes = S.shortlist.filter((g) => all.find((x) => x.gene === g));
  const shortlistChips = slGenes.map((g) => ({ gene: g }));

  const GRID = "30px 34px 1.4fr 1fr 62px 66px 104px 44px 78px";

  const label = (t: string) => (
    <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".8px", color: "#8a92a0", textTransform: "uppercase" as const }}>{t}</div>
  );

  return (
    <main style={{ flex: 1, display: "flex", maxWidth: "1400px", margin: "0 auto", width: "100%" }}>
      {/* filter rail */}
      <aside
        style={{
          width: "258px",
          flexShrink: 0,
          borderRight: "1px solid #e2e5ea",
          padding: "24px 20px",
          display: "flex",
          flexDirection: "column",
          gap: "24px",
        }}
      >
        {/* ① scoring weights */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
            {label("Scoring weights")}
            <span className="navlink" onClick={() => applyPreset("Balanced")} style={{ fontSize: "11px", color: "#1a5fb4", fontWeight: 500 }}>
              Reset
            </span>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "5px", marginBottom: "13px" }}>
            {weightPresets.map((p) => (
              <div
                key={p.name}
                className="navlink"
                onClick={() => applyPreset(p.name)}
                style={{ fontSize: "11px", fontWeight: 600, padding: "4px 9px", borderRadius: "20px", border: `1.5px solid ${p.border}`, background: p.bg, color: p.color }}
              >
                {p.name}
              </div>
            ))}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "11px" }}>
            {weightControls.map((wc) => (
              <div key={wc.k}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                  <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "12px", color: "#3a414d", fontWeight: 500 }}>
                    <span style={{ width: "8px", height: "8px", borderRadius: "2px", background: wc.color }} />
                    {wc.label}
                  </span>
                  <span style={{ fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace", color: "#6b7280", fontWeight: 600 }}>{wc.pct}</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={50}
                  step={1}
                  value={wc.value}
                  onInput={(e) => setWeight(wc.k, +(e.target as HTMLInputElement).value)}
                  onChange={(e) => setWeight(wc.k, +e.target.value)}
                  style={{ width: "100%", accentColor: wc.color, height: "4px", cursor: "pointer" }}
                />
              </div>
            ))}
          </div>
          <div style={{ fontSize: "10.5px", lineHeight: 1.45, color: "#9aa1ad", marginTop: "10px" }}>
            Weights reorder your <em>view</em> of the hypotheses. They never change the evidence or the readiness call.
          </div>
        </div>

        <div style={{ borderTop: "1px solid #eef0f3" }} />

        <div>
          <div style={{ marginBottom: "11px" }}>{label("Readiness call")}</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
            {readinessFacets.map((f) => (
              <div
                key={f.k}
                className={f.count === 0 ? "" : "navlink"}
                onClick={f.count === 0 ? undefined : () => setState((s) => ({ readinessSel: { ...s.readinessSel, [f.k]: !s.readinessSel[f.k] } }))}
                title={f.count === 0 ? "No targets currently carry this call — the target-selection threshold excludes deprioritize-graded genes below grade 2" : undefined}
                style={{ display: "flex", alignItems: "center", gap: "9px", padding: "7px 9px", borderRadius: "8px", background: f.bg, opacity: f.count === 0 ? 0.45 : 1, cursor: f.count === 0 ? "default" : "pointer" }}
              >
                <span style={{ width: "9px", height: "9px", borderRadius: "3px", background: f.dot }} />
                <span style={{ fontSize: "13px", fontWeight: 500, color: f.color, flex: 1 }}>{f.label}</span>
                <span style={{ fontSize: "11px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace" }}>{f.count}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div style={{ marginBottom: "11px" }}>{label("Evidence grade")}</div>
          <div style={{ display: "flex", gap: "6px" }}>
            {gradeFacets.map((g) => (
              <div
                key={g.k}
                className="navlink"
                onClick={() => setState((s) => ({ gradeSel: { ...s.gradeSel, [g.k]: !s.gradeSel[g.k] } }))}
                style={{ flex: 1, textAlign: "center", padding: "8px 0", borderRadius: "8px", border: `1.5px solid ${g.border}`, background: g.bg, color: g.color, fontSize: "13px", fontWeight: 600 }}
              >
                {g.label}
              </div>
            ))}
          </div>
        </div>

        <div>
          <div style={{ marginBottom: "11px" }}>{label("Node category")}</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
            {categoryFacets.map((c) => (
              <div
                key={c.k}
                className="navlink"
                onClick={() => setState((s) => ({ categorySel: { ...s.categorySel, [c.k]: !s.categorySel[c.k] } }))}
                style={{ display: "flex", alignItems: "center", gap: "9px", padding: "7px 9px", borderRadius: "8px", background: c.bg }}
              >
                <span style={{ fontSize: "13px", fontWeight: 500, color: c.color, flex: 1 }}>{c.label}</span>
                <span style={{ fontSize: "11px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace" }}>{c.count}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div style={{ marginBottom: "11px" }}>{label("Review consensus")}</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
            {decisionFacets.map((d) => (
              <div
                key={d.k}
                className="navlink"
                onClick={() => setState({ decisionFilter: d.k })}
                style={{ display: "flex", alignItems: "center", padding: "7px 9px", borderRadius: "8px", background: d.bg }}
              >
                <span style={{ fontSize: "13px", fontWeight: 500, color: d.color }}>{d.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div
          className="navlink"
          onClick={() => setState({ readinessSel: {}, gradeSel: {}, categorySel: {}, query: "", decisionFilter: "all" })}
          style={{ fontSize: "12.5px", color: "#1a5fb4", fontWeight: 500 }}
        >
          Clear all filters
        </div>
      </aside>

      {/* table */}
      <section style={{ flex: 1, minWidth: 0, padding: "24px 28px" }}>
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: "4px" }}>
          <h2 style={{ fontSize: "22px", fontWeight: 700, letterSpacing: "-.4px", margin: 0 }}>Target explorer</h2>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ position: "relative" }}>
              <svg style={{ position: "absolute", left: "11px", top: "50%", transform: "translateY(-50%)" }} width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#8a92a0" strokeWidth="2">
                <circle cx="11" cy="11" r="7" />
                <path d="M20 20L16 16" />
              </svg>
              <input
                value={S.query}
                onChange={(e) => setState({ query: e.target.value })}
                placeholder="Filter genes…"
                style={{ width: "210px", padding: "9px 12px 9px 33px", border: "1.5px solid #d6dbe3", borderRadius: "9px", fontSize: "13px" }}
              />
            </div>
            <button
              onClick={() =>
                alert(
                  "Exporting " +
                    rankedFiltered.length +
                    " targets as CSV (with provenance + current composite columns)…\n\nIn the live portal this streams from /api/exports/{id}.csv",
                )
              }
              style={{ display: "inline-flex", alignItems: "center", gap: "7px", padding: "9px 14px", border: "1.5px solid #d6dbe3", borderRadius: "9px", background: "#fff", fontSize: "13px", fontWeight: 500, color: "#3a414d", cursor: "pointer" }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M12 3v12M7 10l5 5 5-5" />
                <path d="M4 20h16" />
              </svg>{" "}
              Export
            </button>
          </div>
        </div>
        <div style={{ fontSize: "13px", color: "#6b7280", marginBottom: "16px" }}>
          Showing <strong style={{ color: "#1a1d24" }}>{rankedFiltered.length}</strong> of {all.length} targets · ranked by composite priority
        </div>

        <div style={{ border: "1px solid #e2e5ea", borderRadius: "13px", overflow: "hidden" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: GRID,
              gap: "12px",
              padding: "11px 16px",
              background: "#f7f8fa",
              borderBottom: "1px solid #e2e5ea",
              fontSize: "11px",
              fontWeight: 700,
              letterSpacing: ".5px",
              color: "#8a92a0",
              textTransform: "uppercase",
            }}
          >
            <div />
            <div>#</div>
            <div>Target</div>
            <div>Concept module</div>
            <div style={{ textAlign: "right" }}>|log2FC|</div>
            <div style={{ textAlign: "right" }}>Priority</div>
            <div style={{ textAlign: "center" }}>Readiness</div>
            <div style={{ textAlign: "center" }}>Grade</div>
            <div style={{ textAlign: "center" }}>Review</div>
          </div>
          {rankedFiltered.length > 0 && (
            <div ref={scrollRef} style={{ height: TABLE_HEIGHT + "px", overflowY: "auto" }}>
              <div style={{ height: rowVirtualizer.getTotalSize() + "px", position: "relative", width: "100%" }}>
                {rowVirtualizer.getVirtualItems().map((vi) => {
                  const r = buildRow(rankedFiltered[vi.index]);
                  return (
                    <div
                      key={r.gene}
                      className="rowhover navlink"
                      onClick={() => setState({ view: "dossier", selectedGene: r.gene })}
                      style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        width: "100%",
                        height: ROW_HEIGHT + "px",
                        transform: `translateY(${vi.start}px)`,
                        display: "grid",
                        gridTemplateColumns: GRID,
                        gap: "12px",
                        alignItems: "center",
                        padding: "0 16px",
                        borderBottom: "1px solid #eef0f3",
                        background: "#fff",
                      }}
                    >
                      <div
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleShortlist(r.gene);
                        }}
                        style={{ width: "18px", height: "18px", borderRadius: "5px", border: `1.5px solid ${r.checkBorder}`, background: r.checkBg, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", opacity: r.checkOpacity }}
                      >
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3.5">
                          <path d="M20 6L9 17l-5-5" />
                        </svg>
                      </div>
                      <div style={{ fontSize: "13px", fontWeight: 600, color: "#b0b6c0", fontFamily: "'IBM Plex Mono', monospace" }}>{r.rank}</div>
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontSize: "14.5px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24" }}>{r.gene}</div>
                        <div style={{ fontSize: "12px", color: "#8a92a0", marginTop: "1px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.name}</div>
                      </div>
                      <div style={{ minWidth: 0 }}>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "12.5px", color: "#4a515e", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          <span style={{ fontSize: "10.5px", fontFamily: "'IBM Plex Mono', monospace", color: "#9aa1ad" }}>{r.moduleId}</span> {r.moduleShort}
                        </span>
                      </div>
                      <div style={{ textAlign: "right", fontSize: "13px", fontFamily: "'IBM Plex Mono', monospace", color: "#1a1d24" }}>{r.effect}</div>
                      <div style={{ textAlign: "right", fontSize: "14px", fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace", color: "#1a5fb4" }}>{r.comp}</div>
                      <div style={{ textAlign: "center" }}>
                        <span style={{ display: "inline-block", padding: "4px 10px", borderRadius: "20px", fontSize: "11.5px", fontWeight: 600, color: r.rColor, background: r.rBg }}>{r.rLabel}</span>
                      </div>
                      <div style={{ textAlign: "center" }}>
                        <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "26px", height: "26px", borderRadius: "7px", fontSize: "12.5px", fontWeight: 700, color: r.gColor, background: r.gBg }}>{r.grade}</span>
                      </div>
                      <div style={{ textAlign: "center" }}>
                        <span title="reviewer consensus" style={{ display: "inline-flex", alignItems: "center", gap: "5px", padding: "3px 8px", borderRadius: "20px", fontSize: "10.5px", fontWeight: 600, color: r.decColor, background: r.decBg }}>
                          <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: r.decDot }} />
                          {r.decLabel}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          {rankedFiltered.length === 0 && (
            <div style={{ padding: "44px", textAlign: "center", color: "#9aa1ad", fontSize: "14px" }}>No targets match the current filters.</div>
          )}
        </div>
      </section>

      {/* shortlist tray */}
      {slGenes.length > 0 && (
        <div
          style={{
            position: "fixed",
            left: "50%",
            transform: "translateX(-50%)",
            bottom: "20px",
            zIndex: 50,
            display: "flex",
            alignItems: "center",
            gap: "14px",
            width: "min(920px, calc(100% - 48px))",
            padding: "12px 16px",
            background: "#12151b",
            borderRadius: "14px",
            boxShadow: "0 14px 44px -12px rgba(10,20,40,.55)",
          }}
        >
          <span style={{ fontSize: "12px", fontWeight: 600, color: "#fff", whiteSpace: "nowrap" }}>{slGenes.length} selected</span>
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", flex: 1, minWidth: 0, overflow: "hidden", maxHeight: "28px" }}>
            {shortlistChips.map((c) => (
              <span key={c.gene} style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "4px 6px 4px 10px", borderRadius: "20px", background: "rgba(255,255,255,.1)", fontSize: "12px", fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", color: "#fff" }}>
                {c.gene}
                <span
                  className="navlink"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleShortlist(c.gene);
                  }}
                  style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "16px", height: "16px", borderRadius: "50%", background: "rgba(255,255,255,.16)", color: "#fff", fontSize: "12px" }}
                >
                  ×
                </span>
              </span>
            ))}
          </div>
          <span className="navlink" onClick={() => clearShortlist()} style={{ fontSize: "12px", color: "#b0b6c0", fontWeight: 500, whiteSpace: "nowrap" }}>
            Clear
          </span>
          <button onClick={() => setState({ view: "compare" })} style={{ padding: "9px 18px", border: "none", borderRadius: "9px", background: "#1a5fb4", color: "#fff", fontSize: "13px", fontWeight: 600, cursor: "pointer", whiteSpace: "nowrap" }}>
            Compare →
          </button>
        </div>
      )}
    </main>
  );
}
