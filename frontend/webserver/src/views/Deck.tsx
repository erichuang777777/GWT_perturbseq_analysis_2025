// Project overview "deck" — the 4-slide summary, rendered natively in the
// portal's style (mirrors docs/slides/). All numbers map to real repo files
// (figure_registry.md / de_and_baseline_spec.md / config/versions.py).

const C = {
  ink: "#1a1d24",
  soft: "#4a515e",
  soft2: "#5b6270",
  muted: "#8a92a0",
  line: "#e2e5ea",
  surf: "#f7f8fa",
  blue: "#1a5fb4",
  blueBg: "#eaf1fb",
  green: "#0d7d5a",
  amber: "#b0761a",
  grey: "#8a92a0",
  flag: "#b23b3b",
  mono: "'IBM Plex Mono', monospace",
};

function Slide({ n, eyebrow, title, children }: { n: string; eyebrow: string; title: string; children: React.ReactNode }) {
  return (
    <section style={{ position: "relative", border: `1px solid ${C.line}`, borderRadius: "16px", background: "#fff", padding: "30px 32px", marginBottom: "20px" }}>
      <span style={{ position: "absolute", top: "16px", right: "20px", fontFamily: C.mono, fontSize: "12px", color: C.muted }}>{n}</span>
      <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".8px", color: C.blue, textTransform: "uppercase", marginBottom: "9px" }}>{eyebrow}</div>
      <h2 style={{ fontSize: "23px", fontWeight: 700, letterSpacing: "-.4px", lineHeight: 1.2, margin: "0 0 18px" }}>{title}</h2>
      {children}
    </section>
  );
}

function Tile({ n, l }: { n: string; l: string }) {
  return (
    <div style={{ background: C.surf, borderRadius: "12px", padding: "14px 15px" }}>
      <div style={{ fontSize: "26px", fontWeight: 700, color: C.blue, lineHeight: 1, letterSpacing: "-.5px", fontVariantNumeric: "tabular-nums" }}>{n}</div>
      <div style={{ fontSize: "12px", color: C.soft, marginTop: "6px", lineHeight: 1.4 }}>{l}</div>
    </div>
  );
}

const pill = (bg: string): React.CSSProperties => ({ fontFamily: C.mono, fontSize: "11.5px", color: "#fff", padding: "5px 12px", borderRadius: "20px", background: bg });
const chip: React.CSSProperties = { fontFamily: C.mono, fontSize: "12px", color: C.soft, border: `1px solid ${C.line}`, background: C.surf, padding: "6px 11px", borderRadius: "20px" };
const colh: React.CSSProperties = { fontFamily: C.mono, fontSize: "11px", letterSpacing: ".8px", textTransform: "uppercase", color: C.muted, margin: "0 0 10px" };
const li: React.CSSProperties = { fontSize: "14px", color: C.soft, lineHeight: 1.45, marginBottom: "6px" };

function Funnel() {
  const rows: [string, string, string][] = [
    ["100%", C.blue, "33,983 perturbation × condition"],
    ["64%", "#2d6cb5", "2,131 pass gate (6.3%)"],
    ["42%", C.amber, "1,235 unique targets"],
    ["20%", "#b5316f", "39 deliverable"],
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "9px" }}>
      {rows.map(([w, bg, label]) => (
        <div key={label} style={{ width: w, minWidth: "180px", height: "40px", borderRadius: "9px", background: bg, color: "#fff", display: "flex", alignItems: "center", padding: "0 14px", fontFamily: C.mono, fontSize: "12.5px", fontWeight: 600, whiteSpace: "nowrap", fontVariantNumeric: "tabular-nums" }}>
          {label}
        </div>
      ))}
    </div>
  );
}

export default function Deck() {
  const decisions = (
    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
      <span style={pill(C.green)}>ADVANCE</span>
      <span style={pill(C.blue)}>VALIDATE</span>
      <span style={pill(C.amber)}>WATCHLIST</span>
      <span style={pill(C.grey)}>DEPRIORITIZE</span>
    </div>
  );
  return (
    <main style={{ flex: 1, maxWidth: "980px", margin: "0 auto", width: "100%", padding: "40px 28px 80px" }}>
      <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".8px", color: C.blue, textTransform: "uppercase", marginBottom: "10px" }}>Project overview</div>
      <h1 style={{ fontSize: "30px", fontWeight: 700, letterSpacing: "-.6px", margin: "0 0 10px" }}>What we built — in four slides</h1>
      <p style={{ fontSize: "14.5px", lineHeight: 1.6, color: C.soft, maxWidth: "680px", margin: "0 0 26px" }}>
        A shareable summary of the platform. Every number maps to a real repo file (funnel / AUROC / modules from{" "}
        <span style={{ fontFamily: C.mono }}>figure_registry.md</span> &amp; <span style={{ fontFamily: C.mono }}>de_and_baseline_spec.md</span>).
      </p>

      <Slide n="1 / 4" eyebrow="What we built" title="Genome-scale CD4⁺ T-cell Perturb-seq → a defensible drug-target prioritization platform">
        <p style={{ fontSize: "14.5px", color: C.soft, lineHeight: 1.55, margin: "0 0 16px", maxWidth: "680px" }}>
          Turns <strong style={{ color: C.ink }}>33,983 rows</strong> of perturbation differential-expression into decisions a researcher can read directly — not fooled by strong-but-bad signals, and fully traceable.
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "12px" }}>
          <Tile n="33,983" l="perturbation × condition DE rows" />
          <Tile n="11,526" l="unique target genes" />
          <Tile n="4 × 3" l="donors × culture conditions" />
          <Tile n="M01–20" l="immune concept modules" />
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "14px" }}>
          {["Target cards", "Readiness engine", "Calibration", "External evidence", "Disease translation", "Concept layer M01–M20"].map((c) => (
            <span key={c} style={chip}><b style={{ color: C.blue }}>{c}</b></span>
          ))}
        </div>
      </Slide>

      <Slide n="2 / 4" eyebrow="How it works · Why it's trustworthy" title="From statistics to decisions — a guardrail at every step">
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", alignItems: "stretch", marginBottom: "16px" }}>
          {[
            ["Data", "Upstream DESeq2 DE (consumed, not recomputed)"],
            ["Target card", "1–4 evidence grade + knockdown causal gate"],
            ["Readiness engine", "12 domains → R0–R5 → red-flag override"],
            ["Decision", "+ cap reason + provenance"],
          ].map(([b, t], i, a) => (
            <div key={b} style={{ display: "contents" }}>
              <div style={{ flex: 1, minWidth: "135px", background: C.surf, borderRadius: "11px", padding: "12px 13px", fontSize: "12.5px", color: C.soft, lineHeight: 1.4 }}>
                <b style={{ display: "block", color: C.ink, marginBottom: "2px" }}>{b}</b>
                {t}
              </div>
              {i < a.length - 1 && <span style={{ alignSelf: "center", color: C.blue, fontWeight: 700 }}>→</span>}
            </div>
          ))}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "22px" }}>
          <div>
            <div style={colh}>Four-way decision</div>
            {decisions}
            <p style={{ fontSize: "13px", color: C.soft, marginTop: "11px", lineHeight: 1.45 }}>
              Red-flag override — <span style={{ color: C.flag, fontFamily: C.mono, fontSize: "12px" }}>essential / broad-effect / off-target / kd not confirmed</span> — however strong the stats, a hit caps the call.
            </p>
          </div>
          <div>
            <div style={colh}>Guardrails + calibration</div>
            <ul style={{ margin: 0, paddingLeft: "18px" }}>
              <li style={li}><b style={{ color: C.ink }}>unknown ≠ 0</b> · <b style={{ color: C.ink }}>CRISPRi ≠ pharmacology</b> · four-layer versioning</li>
              <li style={li}>Negative controls <b style={{ color: C.ink }}>99.96%</b> at grade 1, <b style={{ color: C.ink }}>0%</b> reach advance</li>
              <li style={li}>Ranking benchmark <b style={{ color: C.ink }}>AUROC 0.85</b> (canonical CD4 positives)</li>
            </ul>
          </div>
        </div>
      </Slide>

      <Slide n="3 / 4" eyebrow="Preliminary results · Deliverables" title="From 34k of noise to an actionable shortlist — all productized">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "22px" }}>
          <div>
            <div style={colh}>Preliminary results (exploratory)</div>
            <ul style={{ margin: 0, paddingLeft: "18px" }}>
              <li style={li}>Curation funnel <b style={{ color: C.ink }}>33,983 → 2,131 (6.3%) = 1,235 targets</b></li>
              <li style={li}>Top hits recapitulate <b style={{ color: C.ink }}>TCR-proximal / SAGA / Mediator</b> modules</li>
              <li style={li}>96 context-specific → <b style={{ color: C.ink }}>39</b> with an actionable modality today</li>
              <li style={li}><b style={{ color: C.ink }}>237</b> essential-gene dropout · <b style={{ color: C.ink }}>387</b> genes with ≥2 risk flags</li>
            </ul>
          </div>
          <div>
            <div style={colh}>Delivered (build)</div>
            <ul style={{ margin: 0, paddingLeft: "18px" }}>
              <li style={li}>FastAPI <b style={{ color: C.ink }}>13 routers</b> + React portal (Provenance disclosure page)</li>
              <li style={li}><b style={{ color: C.ink }}>34</b> test files · frozen <b style={{ color: C.ink }}>7-stage</b> pipeline + per-stage EDA</li>
              <li style={li}>Full docs + <b style={{ color: C.ink }}>2 guide sites</b> + 9-page wiki</li>
              <li style={li}>Public data: SRA <b style={{ color: C.ink }}>SRP643211</b> / GEO <b style={{ color: C.ink }}>GSE314342</b></li>
            </ul>
          </div>
        </div>
        <div style={{ marginTop: "16px", padding: "11px 14px", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "9px", fontSize: "12.5px", lineHeight: 1.5, color: "#7a6a3f" }}>
          <b style={{ color: "#8a6516" }}>Validation, honestly:</b> internal calibration passes (ranking AUROC 0.85, neg-control 99.96%, rank-stability r=0.943). Phenotype-matched external screens (Track D) were <b>actually run</b>: the directionality ranking is a <b>null</b> (AUROC &lt;0.5); a magnitude-axis fair version passes (0.74–0.79) but is exploratory with a detectability confound. <b>Corroborative, not confirmatory — L5 wet-lab is the gap.</b>
        </div>
      </Slide>

      <Slide n="4 / 4" eyebrow="At a glance · Infographic" title="Data → decision: the story in one figure">
        <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: "26px", alignItems: "start" }}>
          <div>
            <div style={colh}>Curation funnel (genome-wide → deliverable)</div>
            <Funnel />
            <div style={{ ...colh, marginTop: "20px" }}>Decision system</div>
            {decisions}
            <p style={{ fontSize: "12.5px", color: C.soft, marginTop: "10px" }}>🚩 Red-flag override: essential / broad-effect / off-target / kd not confirmed → capped</p>
          </div>
          <div>
            <div style={colh}>Key numbers</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
              <Tile n="0.85" l="ranking AUROC (positives)" />
              <Tile n="99.96%" l="neg. controls at grade 1" />
              <Tile n="3" l="regulatory modules recovered" />
              <Tile n="M01–20" l="concept layer (never feeds decisions)" />
            </div>
            <div style={{ ...colh, marginTop: "18px" }}>Provenance &amp; honesty</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {["unknown ≠ 0", "four-layer versioning", "79-row provenance", "CRISPRi ≠ pharmacology"].map((c) => (
                <span key={c} style={chip}>{c}</span>
              ))}
            </div>
          </div>
        </div>
        <div style={{ fontSize: "11px", color: C.muted, borderTop: `1px solid ${C.line}`, marginTop: "18px", paddingTop: "12px", lineHeight: 1.5 }}>
          Research-use target prioritization — not clinical or prescribing advice. Funnel / AUROC / modules are the tool's exploratory analysis of public data; all numbers map to real repo files.
        </div>
      </Slide>
    </main>
  );
}
