const API_VERSION = "v1";

const apiEndpoints = [
  { path: "/targets", desc: "List all screened targets with rank, call, grade and effect size." },
  { path: "/targets/{gene}", desc: "Full dossier for one target — statistical evidence, robustness, safety window and module membership." },
  { path: "/diseases", desc: "List disease contexts (EFO id, name, associated genes)." },
  { path: "/diseases/{efo}/targets", desc: "Targets matched to a disease context, ranked by association score." },
  { path: "/popgen/{gene}", desc: "Population-genetics constraint metrics (gnomAD-derived) for one gene." },
  { path: "/figures/{id}", desc: "Metadata and underlying data series for one figure in the atlas." },
];

const apiSample = `{
  "gene": "PLCG1",
  "name": "Phospholipase C gamma 1",
  "module": "M02",
  "call": "advance",
  "grade": "A",
  "effect_size": 2.14,
  "fdr": "3.1e-14",
  "robustness": 96,
  "safety_window": 82,
  "dataset_version": "GWT-CD4 v2026.1"
}`;

export default function ApiDocs() {
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

      <div style={{ display: "flex", alignItems: "center", gap: "10px", padding: "13px 16px", background: "#f7f8fa", border: "1px solid #e2e5ea", borderRadius: "10px", fontFamily: "'IBM Plex Mono', monospace", fontSize: "13px", marginBottom: "30px" }}>
        <span style={{ fontWeight: 600, color: "#8a92a0" }}>Base URL</span>
        <span style={{ color: "#1a1d24" }}>https://api.cd4-target-portal.org/{API_VERSION}</span>
      </div>

      <div style={{ fontSize: "15px", fontWeight: 700, marginBottom: "12px" }}>Authentication</div>
      <p style={{ fontSize: "13.5px", lineHeight: 1.6, color: "#4a515e", margin: "0 0 30px" }}>
        Send an API key issued from your account as a bearer token:{" "}
        <span style={{ fontFamily: "'IBM Plex Mono', monospace", background: "#f7f8fa", padding: "2px 6px", borderRadius: "5px", fontSize: "12.5px" }}>Authorization: Bearer &lt;key&gt;</span>. Requests without a key are rate-limited to 60/hour.
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
        <pre style={preStyle}>{`curl https://api.cd4-target-portal.org/${API_VERSION}/targets/PLCG1 \\
  -H "Authorization: Bearer <key>"`}</pre>
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
