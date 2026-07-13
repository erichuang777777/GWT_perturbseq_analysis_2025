const API_VERSION = "v1";

// These are exactly the files emitted by scripts/build-static-api.mjs into
// dist/api/v1 at build time — nothing here is documented that the build does
// not actually produce.
const apiEndpoints = [
  { path: "/meta.json", desc: "Dataset build stamp, target/module counts, and this endpoint list." },
  { path: "/targets.json", desc: "Slim index of all screened targets with rank, readiness call, grade and effect size." },
  { path: "/targets/{gene}.json", desc: "Full record for one target — statistical evidence, readiness-engine domains, tractability and module membership." },
  { path: "/diseases.json", desc: "Real disease associations (MONDO id, name, target count) aggregated from Open Targets, most-referenced first." },
  { path: "/diseases/{sanitizedId}/targets.json", desc: "Targets matched to a disease context, ranked by real Open Targets association score." },
  { path: "/popgen/{gene}.json", desc: "Population-genetics constraint metrics (gnomAD-derived) for one gene." },
];

// Shape mirrors dist/api/v1/targets/{gene}.json as emitted by
// scripts/build-static-api.mjs: a build stamp plus the full nested target
// record (abridged here).
const apiSample = `{
  "sourceVersion": "GWT-CD4 real-data v1",
  "target": {
    "gene": "PLCG1",
    "name": "Phospholipase C gamma 1",
    "module": { "id": "M02", "name": "TCR_Proximal_Signaling" },
    "grade": "A",
    "gradeNum": 4,
    "effect": 14.10,
    "fdr": 1e-16,
    "primaryCondition": "Stim8hr",
    "readiness": { "call": "advance", "stage": "R4" }
  }
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
      <p style={{ fontSize: "14.5px", lineHeight: 1.6, color: "#4a515e", margin: "0 0 22px", maxWidth: "660px" }}>
        Read-only programmatic access to the same target calls, disease matches and population-genetics data shown in this portal. The API is a set of <strong>static JSON files</strong> generated at build time from this repo's own pipeline output and served from the same origin as the site — no server, no compute, no silent updates. Each file is stamped with the dataset build.
      </p>

      <div style={{ display: "flex", alignItems: "center", gap: "10px", padding: "13px 16px", background: "#f7f8fa", border: "1px solid #e2e5ea", borderRadius: "10px", fontFamily: "'IBM Plex Mono', monospace", fontSize: "13px", marginBottom: "30px", flexWrap: "wrap" }}>
        <span style={{ fontWeight: 600, color: "#8a92a0" }}>Base path</span>
        <span style={{ color: "#1a1d24", wordBreak: "break-all" }}>{`<this-site-origin>/api/${API_VERSION}`}</span>
      </div>

      <div style={{ fontSize: "15px", fontWeight: 700, marginBottom: "12px" }}>Access</div>
      <p style={{ fontSize: "13.5px", lineHeight: 1.6, color: "#4a515e", margin: "0 0 30px" }}>
        Public, read-only, no authentication — every endpoint is a plain <span style={{ fontFamily: "'IBM Plex Mono', monospace", background: "#f7f8fa", padding: "2px 6px", borderRadius: "5px", fontSize: "12.5px" }}>GET</span> for a static <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>.json</span> file served by the CDN. There is no API key, no rate limit and no write access.
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
        <pre style={preStyle}>{`# same-origin static file — no key, no auth
curl https://<this-site-origin>/api/${API_VERSION}/targets/PLCG1.json`}</pre>
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
