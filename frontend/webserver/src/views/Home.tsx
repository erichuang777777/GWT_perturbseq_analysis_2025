import { MODULES, TARGETS } from "../data/dataset";
import { useStore } from "../store/store";
import StatTile from "../components/ui/StatTile";

export default function Home() {
  const { state, setState } = useStore();
  const all = TARGETS;

  const stats = [
    { value: all.length, label: "CD4 perturbations profiled" },
    { value: MODULES.length, label: "Immune concept modules" },
    { value: all.filter((x) => x.readiness?.call === "advance").length, label: "Targets called Advance" },
    { value: 6, label: "REST API endpoints" },
  ];

  const onSearchKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      const m = all.find((x) => x.gene.toUpperCase() === state.query.trim().toUpperCase());
      setState(m ? { view: "dossier", selectedGene: m.gene } : { view: "explorer" });
    }
  };

  return (
    <main style={{ flex: 1 }}>
      <section style={{ maxWidth: "1120px", margin: "0 auto", padding: "60px 28px 8px" }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "5px 12px",
            borderRadius: "20px",
            background: "#eaf1fb",
            color: "#1a5fb4",
            fontSize: "12px",
            fontWeight: 600,
            marginBottom: "20px",
          }}
        >
          <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#1a5fb4" }} />
          Research-use portal · {all.length} perturbations · {MODULES.length} immune concepts
        </div>
        <h1 style={{ fontSize: "42px", lineHeight: 1.07, letterSpacing: "-1.2px", fontWeight: 700, margin: "0 0 16px", maxWidth: "820px" }}>
          Drug-target discovery from CD4 T-cell Perturb-seq, made legible.
        </h1>
        <p style={{ fontSize: "17.5px", lineHeight: 1.55, color: "#4a515e", maxWidth: "660px", margin: "0 0 12px" }}>
          The same evidence, read two ways. Choose how you want to start — the portal orders what you see first
          around your question.
        </p>

        {/* Role splitter — the two entry points */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginTop: "28px" }}>
          {/* Researcher */}
          <div
            className="lift"
            onClick={() => setState({ view: "explorer" })}
            style={{ border: "1.5px solid #cfe0f5", borderRadius: "16px", padding: "26px 26px 22px", cursor: "pointer", background: "linear-gradient(180deg,#f7fafe,#ffffff)" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" }}>
              <div style={{ width: "44px", height: "44px", borderRadius: "12px", background: "#eaf1fb", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width="23" height="23" viewBox="0 0 24 24" fill="none" stroke="#1a5fb4" strokeWidth="1.8">
                  <path d="M3 3v18h18" />
                  <rect x="7" y="11" width="3" height="7" />
                  <rect x="12.5" y="7" width="3" height="11" />
                  <rect x="18" y="13" width="3" height="5" />
                </svg>
              </div>
              <div>
                <div style={{ fontSize: "12px", fontWeight: 700, color: "#1a5fb4", letterSpacing: ".3px", textTransform: "uppercase" }}>I'm a researcher</div>
                <div style={{ fontSize: "19px", fontWeight: 700, letterSpacing: "-.3px" }}>Find a novel target</div>
              </div>
            </div>
            <p style={{ fontSize: "14px", lineHeight: 1.55, color: "#1a1d24", margin: "0 0 14px" }}>
              Rank targets by readiness, then review each target's evidence in development order.
            </p>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "#1a1d24", letterSpacing: ".4px", textTransform: "uppercase", marginBottom: "8px" }}>What you see first</div>
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 16px", display: "flex", flexDirection: "column", gap: "7px" }}>
              {[
                "15 primary-outcome genes — our breadth-ranked shortlist",
                "Readiness call — advance / validate / watchlist",
                "Perturbation score — reweightable 0–100 priority",
              ].map((li) => (
                <li key={li} style={{ fontSize: "13px", color: "#1a1d24", display: "flex", gap: "9px" }}>
                  <span style={{ color: "#1a5fb4" }}>→</span> {li}
                </li>
              ))}
            </ul>
            <div style={{ fontSize: "13.5px", fontWeight: 600, color: "#1a5fb4" }}>Open target explorer →</div>
          </div>

          {/* Clinician */}
          <div
            className="lift"
            onClick={() => setState({ view: "clinical" })}
            style={{ border: "1.5px solid #c7e6d9", borderRadius: "16px", padding: "26px 26px 22px", cursor: "pointer", background: "linear-gradient(180deg,#f5fbf8,#ffffff)" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "12px" }}>
              <div style={{ width: "44px", height: "44px", borderRadius: "12px", background: "#e6f4ee", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width="23" height="23" viewBox="0 0 24 24" fill="none" stroke="#0d7d5a" strokeWidth="1.8">
                  <path d="M12 3v6M9 6h6" />
                  <rect x="4" y="9" width="16" height="11" rx="2" />
                  <path d="M8 14h8" />
                </svg>
              </div>
              <div>
                <div style={{ fontSize: "12px", fontWeight: 700, color: "#0d7d5a", letterSpacing: ".3px", textTransform: "uppercase" }}>I'm a clinician</div>
                <div style={{ fontSize: "19px", fontWeight: 700, letterSpacing: "-.3px" }}>Check a disease's targets</div>
              </div>
            </div>
            <p style={{ fontSize: "14px", lineHeight: 1.55, color: "#1a1d24", margin: "0 0 14px" }}>
              Start with a disease, review targets by safety risk, and compare a de-identified expression profile.
            </p>
            <div style={{ fontSize: "11px", fontWeight: 700, color: "#1a1d24", letterSpacing: ".4px", textTransform: "uppercase", marginBottom: "8px" }}>What you see first</div>
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 16px", display: "flex", flexDirection: "column", gap: "7px" }}>
              {[
                "Disease → associated targets",
                "Risk tier — clear / caution / high / avoid",
                "Known-drug benchmark for the target",
              ].map((li) => (
                <li key={li} style={{ fontSize: "13px", color: "#1a1d24", display: "flex", gap: "9px" }}>
                  <span style={{ color: "#0d7d5a" }}>→</span> {li}
                </li>
              ))}
            </ul>
            <div style={{ fontSize: "13.5px", fontWeight: 600, color: "#0d7d5a" }}>Open clinical lookup →</div>
          </div>
        </div>

        {/* Search — quick jump for anyone who already knows the gene */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", maxWidth: "620px", margin: "22px 0 6px" }}>
          <div style={{ position: "relative", flex: 1 }}>
            <svg
              style={{ position: "absolute", left: "15px", top: "50%", transform: "translateY(-50%)" }}
              width="17"
              height="17"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#8a92a0"
              strokeWidth="2"
            >
              <circle cx="11" cy="11" r="7" />
              <path d="M20 20L16 16" />
            </svg>
            <input
              value={state.query}
              onChange={(e) => setState({ query: e.target.value })}
              onKeyDown={onSearchKey}
              placeholder="Already know the gene? Jump straight to it — e.g. PLCG1, IL2RA, CTLA4…"
              style={{ width: "100%", padding: "13px 16px 13px 42px", border: "1.5px solid #d6dbe3", borderRadius: "11px", fontSize: "14px", color: "#1a1d24" }}
            />
          </div>
          <button
            onClick={() => setState({ view: "explorer" })}
            style={{ padding: "13px 20px", border: "none", borderRadius: "11px", background: "#1a5fb4", color: "#fff", fontSize: "14px", fontWeight: 600, cursor: "pointer" }}
          >
            Explore all
          </button>
        </div>
      </section>

      {/* The tension figure — image-only link to the figure atlas */}
      <section style={{ maxWidth: "1120px", margin: "0 auto", padding: "22px 28px 8px" }}>
        <button
          className="lift"
          aria-label="Open the researcher value versus clinical risk figure in the figure atlas"
          onClick={() => setState({ view: "figures" })}
          style={{ width: "100%", display: "block", border: 0, borderRadius: "16px", padding: 0, overflow: "hidden", cursor: "pointer", background: "transparent" }}
        >
          <img
            src={`${import.meta.env.BASE_URL}flagship/fig_tension.svg`}
            alt="Researcher value vs. clinical risk across all 7,249 targets — downstream DE breadth against perturbation effect size, coloured by clinical risk tier, with conflict-zone flagships CD3E, VAV1, STAT3, PLCG1 and BCL10 called out"
            loading="lazy"
            style={{ width: "100%", height: "auto", display: "block" }}
          />
        </button>
      </section>

      <section style={{ maxWidth: "1120px", margin: "0 auto", padding: "40px 28px 70px" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4,1fr)",
            gap: "1px",
            background: "#e2e5ea",
            border: "1px solid #e2e5ea",
            borderRadius: "14px",
            overflow: "hidden",
          }}
        >
          {stats.map((s) => (
            <div key={s.label} style={{ background: "#fff", padding: "22px 24px" }}>
              <StatTile size="lg" label={s.label} value={s.value} />
            </div>
          ))}
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "10px",
            marginTop: "20px",
            padding: "14px 16px",
            background: "#fbf9f2",
            border: "1px solid #eddfc0",
            borderRadius: "11px",
          }}
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#b7791f" strokeWidth="2" style={{ flexShrink: 0, marginTop: "1px" }}>
            <path d="M12 9v4M12 17h.01" />
            <path d="M10.3 3.9L2.4 18a2 2 0 001.7 3h15.8a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z" />
          </svg>
          <p style={{ fontSize: "12.5px", lineHeight: 1.5, color: "#7a6a3f", margin: 0 }}>
            <strong style={{ color: "#8a6516" }}>Research use only — not clinical software.</strong> Outputs are
            exploratory drug-target hypotheses from a CD4 T-cell Perturb-seq screen. They are not diagnostic, not
            treatment recommendations, and not efficacy predictions. Concept profiles are descriptive and never feed
            the readiness call.
          </p>
        </div>
      </section>
    </main>
  );
}
