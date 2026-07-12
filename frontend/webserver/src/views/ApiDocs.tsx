const API_VERSION = "v1";

const apiEndpoints = [
  { path: "/api/v1/meta.json", desc: "Dataset version, counts, and the endpoint index." },
  { path: "/api/v1/targets.json", desc: "Slim index of all screened targets (gene, name, module, grade, effect, readiness call) — each with an href to its full record." },
  { path: "/api/v1/targets/{gene}.json", desc: "Full real record for one target — statistics, readiness-engine domains, disease links, tractability, gnomAD, external screens, and more." },
  { path: "/api/v1/diseases.json", desc: "Index of every disease association across the screen, each with an href to its target list." },
  { path: "/api/v1/diseases/{id}/targets.json", desc: "Targets referencing one disease, ranked by real Open Targets association score (use the href from diseases.json)." },
  { path: "/api/v1/popgen/{gene}.json", desc: "gnomAD constraint (LOEUF/pLI) and UK Biobank lymphocyte-count LoF burden for one gene." },
];

const apiSample = `{
  "sourceVersion": "GWT_perturbseq_analysis_2025 ...",
  "target": {
    "gene": "PLCG1",
    "name": "Phospholipase C gamma 1",
    "module": { "id": "M02", "name": "TCR_Proximal_Signaling" },
    "grade": "A",
    "gradeNum": 4,
    "effect": 14.10,
    "fdr": 1e-16,
    "primaryCondition": "Stim8hr",
    "readiness": { "call": "advance", "stage": "R3" },
    "...": "plus statistics, tractabilityFlags, diseases, gnomad, and more"
  }
}`;

export default function ApiDocs() {
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const base = `${origin}/api/${API_VERSION}`;

  const preStyle: React.CSSProperties = {
    margin: 0,
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "12.5px",
    lineHeight: 1.6,
    color: "#d6dbe3",
    whiteSpace: "pre",
  };

  return (
    <main style={{ flex: 1, maxWidth: "900px", margin: "0 auto", width: "100%", padding: "40px 28px 80px" }}>
      <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".8px", color: "#1a5fb4", textTransform: "uppercase", marginBottom: "10px" }}>Developer reference</div>
      <h1 style={{ fontSize: "28px", fontWeight: 700, margin: "0 0 10px", letterSpacing: "-.4px" }}>REST API</h1>
      <p style={{ fontSize: "14.5px", lineHeight: 1.6, color: "#4a515e", margin: "0 0 22px", maxWidth: "640px" }}>
        Read-only programmatic access to the same target calls, disease matches and population-genetics data shown in this portal. All endpoints are versioned and stamped with the dataset build — never a silent update.
      </p>

      <div style={{ display: "flex", alignItems: "start", gap: "8px", padding: "14px 16px", background: "#e4f3ec", border: "1px solid #b9e0cd", color: "#0a6e4f", borderRadius: "11px", fontSize: "12.5px", lineHeight: 1.55, marginBottom: "24px" }}>
        <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>ⓘ</span> <strong>Real, static, read-only API.</strong> These endpoints are generated at build time from this repo's own pipeline output and served as same-origin JSON files on the CDN — no server, no auth, no rate limit. They are read-only and by-id (GET), and are regenerated on every deploy so they always match the portal you're browsing.
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "10px", padding: "13px 16px", background: "#f7f8fa", border: "1px solid #e2e5ea", borderRadius: "10px", fontFamily: "'IBM Plex Mono', monospace", fontSize: "13px", marginBottom: "30px" }}>
        <span style={{ fontWeight: 600, color: "#8a92a0" }}>Base URL</span>
        <span style={{ color: "#1a1d24" }}>{base}</span>
      </div>

      <div style={{ fontSize: "15px", fontWeight: 700, marginBottom: "12px" }}>Authentication</div>
      <p style={{ fontSize: "13.5px", lineHeight: 1.6, color: "#4a515e", margin: "0 0 30px" }}>
        None — these are public, read-only static files. Fetch them directly with no key.
      </p>

      <div style={{ fontSize: "15px", fontWeight: 700, marginBottom: "14px" }}>Endpoints</div>
      <div style={{ display: "flex", flexDirection: "column", gap: "1px", background: "#e2e5ea", border: "1px solid #e2e5ea", borderRadius: "12px", overflow: "hidden", marginBottom: "30px" }}>
        {apiEndpoints.map((ep) => (
          <div key={ep.path} style={{ background: "#fff", padding: "16px 18px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
              <span style={{ fontSize: "10.5px", fontWeight: 700, letterSpacing: ".3px", color: "#0a6e4f", background: "#e4f3ec", padding: "3px 8px", borderRadius: "5px" }}>GET</span>
              <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "13.5px", fontWeight: 600 }}>{ep.path}</span>
            </div>
            <div style={{ fontSize: "12.5px", color: "#6b7280", lineHeight: 1.5, marginLeft: "2px" }}>{ep.desc}</div>
          </div>
        ))}
      </div>

      <div style={{ fontSize: "15px", fontWeight: 700, marginBottom: "12px" }}>Example request</div>
      <div style={{ background: "#1a1d24", borderRadius: "12px", padding: "18px 20px", marginBottom: "14px", overflowX: "auto" }}>
        <pre style={preStyle}>{`curl ${base}/targets/PLCG1.json`}</pre>
      </div>
      <div style={{ fontSize: "15px", fontWeight: 700, marginBottom: "12px" }}>Example response</div>
      <div style={{ background: "#1a1d24", borderRadius: "12px", padding: "18px 20px", marginBottom: "30px", overflowX: "auto" }}>
        <pre style={preStyle}>{apiSample}</pre>
      </div>

      <div style={{ display: "flex", alignItems: "start", gap: "8px", padding: "14px 16px", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "11px", fontSize: "12.5px", color: "#7a6420", lineHeight: 1.55 }}>
        <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>ⓘ</span> Fields with no evidence return{" "}
        <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontWeight: 600 }}>"unknown"</span> plus a coverage note — the API never fabricates a zero or default value.
      </div>
    </main>
  );
}
