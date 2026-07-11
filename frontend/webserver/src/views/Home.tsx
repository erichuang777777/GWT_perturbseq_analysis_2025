import { TARGETS } from "../data/targets";
import { useStore } from "../store/store";

export default function Home() {
  const { state, setState } = useStore();
  const all = TARGETS;

  const stats = [
    { value: all.length, label: "CD4 perturbations profiled" },
    { value: "20", label: "Immune concept modules" },
    { value: all.filter((x) => x.call === "advance").length, label: "Targets called Advance" },
    { value: "~30", label: "REST API endpoints" },
  ];

  const onSearchKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      const m = all.find((x) => x.gene.toUpperCase() === state.query.trim().toUpperCase());
      setState(m ? { view: "dossier", selectedGene: m.gene } : { view: "explorer" });
    }
  };

  return (
    <main style={{ flex: 1 }}>
      <section style={{ maxWidth: "1120px", margin: "0 auto", padding: "66px 28px 20px" }}>
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
            marginBottom: "22px",
          }}
        >
          <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#1a5fb4" }} />
          Research-use portal · {all.length} perturbations · 20 immune concepts
        </div>
        <h1 style={{ fontSize: "46px", lineHeight: 1.06, letterSpacing: "-1.3px", fontWeight: 700, margin: "0 0 18px", maxWidth: "780px" }}>
          Drug-target discovery from CD4 T-cell Perturb-seq, made legible.
        </h1>
        <p style={{ fontSize: "18px", lineHeight: 1.55, color: "#4a515e", maxWidth: "640px", margin: "0 0 30px" }}>
          Every target sits on one evidence-backed page — statistical strength, robustness, immune-concept
          profile, safety window and population genetics — each number stamped with its source and version.
        </p>

        <div style={{ display: "flex", alignItems: "center", gap: "12px", maxWidth: "620px", marginBottom: "46px" }}>
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
              placeholder="Search a gene, e.g. PLCG1, IL2RA, JAK3…"
              style={{ width: "100%", padding: "15px 16px 15px 42px", border: "1.5px solid #d6dbe3", borderRadius: "11px", fontSize: "15px", color: "#1a1d24" }}
            />
          </div>
          <button
            onClick={() => setState({ view: "explorer" })}
            style={{ padding: "15px 22px", border: "none", borderRadius: "11px", background: "#1a5fb4", color: "#fff", fontSize: "14.5px", fontWeight: 600, cursor: "pointer" }}
          >
            Explore targets
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
          <div
            className="lift"
            onClick={() => setState({ view: "explorer" })}
            style={{ border: "1px solid #e2e5ea", borderRadius: "16px", padding: "28px", cursor: "pointer", background: "#fff" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "15px" }}>
              <div style={{ width: "42px", height: "42px", borderRadius: "11px", background: "#eaf1fb", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1a5fb4" strokeWidth="1.8">
                  <path d="M3 3v18h18" />
                  <rect x="7" y="11" width="3" height="7" />
                  <rect x="12.5" y="7" width="3" height="11" />
                  <rect x="18" y="13" width="3" height="5" />
                </svg>
              </div>
              <div style={{ fontSize: "19px", fontWeight: 700, letterSpacing: "-.3px" }}>Researcher workspace</div>
            </div>
            <p style={{ fontSize: "14.5px", lineHeight: 1.55, color: "#4a515e", margin: "0 0 16px" }}>
              Rank and filter the full perturbation screen by readiness call and evidence grade. Drill into any
              target's full dossier, audit its concept profile, and export.
            </p>
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 18px", display: "flex", flexDirection: "column", gap: "8px" }}>
              {[
                "Faceted target explorer with live filters",
                "Entity-centric dossier per target",
                "Concept-bottleneck profile (M01–M20)",
              ].map((li) => (
                <li key={li} style={{ fontSize: "13px", color: "#5b6270", display: "flex", gap: "9px" }}>
                  <span style={{ color: "#1a5fb4" }}>→</span> {li}
                </li>
              ))}
            </ul>
            <div style={{ fontSize: "13.5px", fontWeight: 600, color: "#1a5fb4" }}>Open workspace →</div>
          </div>

          <div
            className="lift"
            onClick={() => setState({ view: "clinical" })}
            style={{ border: "1px solid #e2e5ea", borderRadius: "16px", padding: "28px", cursor: "pointer", background: "#fff" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "15px" }}>
              <div style={{ width: "42px", height: "42px", borderRadius: "11px", background: "#e6f4ee", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0d7d5a" strokeWidth="1.8">
                  <path d="M12 3v6M9 6h6" />
                  <rect x="4" y="9" width="16" height="11" rx="2" />
                  <path d="M8 14h8" />
                </svg>
              </div>
              <div style={{ fontSize: "19px", fontWeight: 700, letterSpacing: "-.3px" }}>Clinical-evidence lookup</div>
            </div>
            <p style={{ fontSize: "14.5px", lineHeight: 1.55, color: "#4a515e", margin: "0 0 16px" }}>
              Look up a single immune concept or gene, match a disease context to candidate targets, and read
              population-genetics constraint — framed strictly as evidence, never as clinical guidance.
            </p>
            <ul style={{ listStyle: "none", padding: 0, margin: "0 0 18px", display: "flex", flexDirection: "column", gap: "8px" }}>
              {[
                "Immune-concept profile viewer",
                "Disease × target evidence match",
                "Population-genetics constraint lookup",
              ].map((li) => (
                <li key={li} style={{ fontSize: "13px", color: "#5b6270", display: "flex", gap: "9px" }}>
                  <span style={{ color: "#0d7d5a" }}>→</span> {li}
                </li>
              ))}
            </ul>
            <div style={{ fontSize: "13.5px", fontWeight: 600, color: "#0d7d5a" }}>Open lookup →</div>
          </div>
        </div>

        <div
          className="lift navlink"
          onClick={() => setState({ view: "figures" })}
          style={{
            marginTop: "20px",
            display: "flex",
            alignItems: "center",
            gap: "18px",
            border: "1px solid #e6e2f2",
            borderRadius: "16px",
            padding: "22px 26px",
            background: "linear-gradient(100deg,#faf8ff,#ffffff)",
            cursor: "pointer",
          }}
        >
          <div style={{ width: "46px", height: "46px", borderRadius: "12px", background: "#efe9fb", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#5b3fb4" strokeWidth="1.8">
              <path d="M3 3v18h18" />
              <circle cx="9" cy="14" r="1.6" />
              <circle cx="14" cy="9" r="1.6" />
              <circle cx="19" cy="12" r="1.6" />
              <path d="M9 14l5-5 5 3" opacity=".6" />
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: "16px", fontWeight: 700, letterSpacing: "-.2px" }}>Interactive figure atlas</div>
            <div style={{ fontSize: "13.5px", color: "#5b6270", marginTop: "2px", lineHeight: 1.5 }}>
              Explore the study's figures live — trans-effect volcano, UMAP functional clustering, effect heatmaps,
              Th1/Th2 polarization, GWAS enrichment, power &amp; LoF-burden — with hover, zoom and filtering.
            </div>
          </div>
          <div style={{ fontSize: "13.5px", fontWeight: 600, color: "#5b3fb4", whiteSpace: "nowrap" }}>Open atlas →</div>
        </div>
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
              <div style={{ fontSize: "28px", fontWeight: 700, letterSpacing: "-.6px", color: "#1a1d24" }}>{s.value}</div>
              <div style={{ fontSize: "12.5px", color: "#6b7280", marginTop: "3px", fontWeight: 500 }}>{s.label}</div>
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
