import { useEffect, useMemo, useState } from "react";

// Provenance & Methods page. Renders the two committed disclosure artifacts
// shipped in public/ (see docs/frontend_disclosure_spec.md):
//   - disclosure.json          — versions, coverage, disclaimer, principles,
//                                 limitations, attribution, concept-layer note
//   - provenance_registry.csv  — data source × algorithm × reference registry
// Nothing here invents a value; it only displays those two files.

interface Attribution {
  source: string;
  cite: string;
  license: string;
  url: string;
}
interface DocLink {
  label: string;
  path: string;
  kind: string;
}
interface Disclosure {
  versions: Record<string, string>;
  coverage: Record<string, unknown> & { note?: string };
  disclaimer: { short: string; long: string };
  principles: { key: string; text: string }[];
  limitations: string[];
  attribution: Attribution[];
  concept_layer: Record<string, string | number>;
  doc_links: DocLink[];
}

type Category = "data_source" | "algorithm" | "reference";

// Minimal quote-aware CSV parser (the registry has no embedded newlines).
function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let field = "";
  let row: string[] = [];
  let inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else inQ = false;
      } else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ",") {
      row.push(field);
      field = "";
    } else if (c === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else if (c !== "\r") field += c;
  }
  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }
  return rows.filter((r) => r.length > 1);
}

// Turn "https://x | PMID 12345 | DOI 10.x/y" into linked fragments.
function LinkedSource({ value }: { value: string }) {
  const parts = value.split("|").map((s) => s.trim()).filter(Boolean);
  return (
    <>
      {parts.map((p, i) => {
        let href: string | null = null;
        if (/^https?:\/\//.test(p)) href = p;
        else {
          const pmid = p.match(/PMID\s*(\d+)/i);
          const doi = p.match(/DOI\s*(10\.\S+)/i);
          if (pmid) href = `https://pubmed.ncbi.nlm.nih.gov/${pmid[1]}/`;
          else if (doi) href = `https://doi.org/${doi[1]}`;
        }
        const sep = i < parts.length - 1 ? " · " : "";
        return href ? (
          <span key={i}>
            <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: "#1a5fb4" }}>
              {p}
            </a>
            {sep}
          </span>
        ) : (
          <span key={i}>
            {p}
            {sep}
          </span>
        );
      })}
    </>
  );
}

const TAB_LABEL: Record<Category, string> = {
  data_source: "Data sources",
  algorithm: "Algorithms",
  reference: "References",
};

export default function Provenance() {
  const [disc, setDisc] = useState<Disclosure | null>(null);
  const [rows, setRows] = useState<string[][]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<Category>("data_source");

  useEffect(() => {
    const base = import.meta.env.BASE_URL;
    Promise.all([
      fetch(`${base}disclosure.json`).then((r) => {
        if (!r.ok) throw new Error(`disclosure.json ${r.status}`);
        return r.json() as Promise<Disclosure>;
      }),
      fetch(`${base}provenance_registry.csv`).then((r) => {
        if (!r.ok) throw new Error(`provenance_registry.csv ${r.status}`);
        return r.text();
      }),
    ])
      .then(([d, csv]) => {
        setDisc(d);
        setRows(parseCsv(csv));
      })
      .catch((e) => setErr(String(e)));
  }, []);

  const header = rows[0] ?? [];
  const dataRows = useMemo(() => rows.slice(1).filter((r) => r[0] === tab), [rows, tab]);
  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    rows.slice(1).forEach((r) => (c[r[0]] = (c[r[0]] ?? 0) + 1));
    return c;
  }, [rows]);

  const sec: React.CSSProperties = { fontSize: "15px", fontWeight: 700, margin: "34px 0 12px" };
  const chip: React.CSSProperties = {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "11.5px",
    color: "#4a515e",
    background: "#f7f8fa",
    border: "1px solid #e2e5ea",
    borderRadius: "7px",
    padding: "6px 10px",
  };

  if (err)
    return (
      <main style={{ flex: 1, maxWidth: "980px", margin: "0 auto", width: "100%", padding: "40px 28px" }}>
        <p style={{ color: "#b23b3b", fontSize: "14px" }}>Could not load disclosure files: {err}</p>
      </main>
    );
  if (!disc)
    return (
      <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#9aa1ad", fontSize: "14px" }}>
        Loading provenance…
      </main>
    );

  return (
    <main style={{ flex: 1, maxWidth: "980px", margin: "0 auto", width: "100%", padding: "40px 28px 80px" }}>
      <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".8px", color: "#1a5fb4", textTransform: "uppercase", marginBottom: "10px" }}>
        Provenance &amp; methods
      </div>
      <h1 style={{ fontSize: "28px", fontWeight: 700, margin: "0 0 10px", letterSpacing: "-.4px" }}>Provenance</h1>
      <p style={{ fontSize: "14.5px", lineHeight: 1.6, color: "#4a515e", margin: "0 0 22px", maxWidth: "680px" }}>
        Every data source, computation and reference behind this portal, aligned to one fixed schema. This page renders two
        committed files — <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>disclosure.json</span> and{" "}
        <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>provenance_registry.csv</span> — nothing here is invented.
      </p>

      {/* research-use disclaimer */}
      <div style={{ padding: "13px 16px", background: "#fdf6e3", border: "1px solid #eddfc0", borderRadius: "11px", fontSize: "13px", color: "#7a6420", lineHeight: 1.55, marginBottom: "26px" }}>
        <strong style={{ color: "#8a6516" }}>{disc.disclaimer.short}</strong> {disc.disclaimer.long}
      </div>

      {/* versions */}
      <div style={sec}>Versions</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
        {Object.entries(disc.versions).map(([k, v]) => (
          <span key={k} style={chip}>
            <span style={{ color: "#8a92a0" }}>{k}</span> {v}
          </span>
        ))}
      </div>

      {/* coverage */}
      <div style={sec}>Coverage</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "8px" }}>
        {Object.entries(disc.coverage)
          .filter(([k]) => k !== "note")
          .map(([k, v]) => (
            <span key={k} style={chip}>
              <span style={{ color: "#8a92a0" }}>{k}</span> {Array.isArray(v) ? v.join(" / ") : String(v)}
            </span>
          ))}
      </div>
      {disc.coverage.note && <p style={{ fontSize: "12.5px", color: "#6b7280", lineHeight: 1.55, margin: 0 }}>{disc.coverage.note}</p>}

      {/* registry tabs */}
      <div style={sec}>Registry</div>
      <div style={{ display: "flex", gap: "8px", marginBottom: "14px" }}>
        {(Object.keys(TAB_LABEL) as Category[]).map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => setTab(c)}
            style={{
              cursor: "pointer",
              fontSize: "12.5px",
              fontWeight: 600,
              padding: "7px 13px",
              borderRadius: "8px",
              border: "1px solid " + (tab === c ? "#1a5fb4" : "#e2e5ea"),
              background: tab === c ? "#eaf1fb" : "#fff",
              color: tab === c ? "#1a5fb4" : "#4a515e",
            }}
          >
            {TAB_LABEL[c]} <span style={{ color: "#9aa1ad" }}>{counts[c] ?? 0}</span>
          </button>
        ))}
      </div>
      <div style={{ overflowX: "auto", border: "1px solid #e2e5ea", borderRadius: "12px" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12.5px", minWidth: "760px" }}>
          <thead>
            <tr>
              {["component", "type", "identifier", "version", "source", "produced_by", "notes"].map((h) => (
                <th key={h} style={{ textAlign: "left", padding: "9px 12px", background: "#f7f8fa", borderBottom: "1px solid #e2e5ea", fontFamily: "'IBM Plex Mono', monospace", fontSize: "10.5px", letterSpacing: ".4px", textTransform: "uppercase", color: "#8a92a0", whiteSpace: "nowrap" }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dataRows.map((r, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #eef0f3" }}>
                <td style={{ padding: "10px 12px", fontWeight: 600, color: "#1a1d24" }}>{r[1]}</td>
                <td style={{ padding: "10px 12px", color: "#6b7280", fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px" }}>{r[2]}</td>
                <td style={{ padding: "10px 12px", color: "#4a515e" }}>{r[3]}</td>
                <td style={{ padding: "10px 12px", color: "#4a515e", fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px" }}>{r[4]}</td>
                <td style={{ padding: "10px 12px", color: "#4a515e" }}>{r[5] && r[5] !== "-" ? <LinkedSource value={r[5]} /> : <span style={{ color: "#b9bfc9" }}>—</span>}</td>
                <td style={{ padding: "10px 12px", color: "#6b7280", fontFamily: "'IBM Plex Mono', monospace", fontSize: "11px" }}>{r[6] && r[6] !== "-" ? r[6] : "—"}</td>
                <td style={{ padding: "10px 12px", color: "#6b7280", maxWidth: "260px" }}>{r[7]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ fontSize: "11px", color: "#9aa1ad", marginTop: "8px", fontFamily: "'IBM Plex Mono', monospace" }}>
        src: docs/provenance_registry.csv ({header.length ? header.length : 8} cols · {rows.length ? rows.length - 1 : 0} rows)
      </div>

      {/* principles */}
      <div style={sec}>Design principles</div>
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {disc.principles.map((p) => (
          <div key={p.key} style={{ display: "flex", gap: "12px", alignItems: "baseline", borderLeft: "3px solid #1a5fb4", background: "#f7f9fc", borderRadius: "0 9px 9px 0", padding: "11px 14px" }}>
            <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "12px", fontWeight: 600, color: "#1a5fb4", minWidth: "140px" }}>{p.key}</span>
            <span style={{ fontSize: "13px", color: "#4a515e", lineHeight: 1.5 }}>{p.text}</span>
          </div>
        ))}
      </div>

      {/* limitations */}
      <div style={sec}>Limitations</div>
      <ul style={{ margin: 0, paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "6px" }}>
        {disc.limitations.map((l, i) => (
          <li key={i} style={{ fontSize: "13px", color: "#4a515e", lineHeight: 1.55 }}>{l}</li>
        ))}
      </ul>

      {/* concept layer */}
      <div style={sec}>Concept layer (M01–M20)</div>
      <div style={{ padding: "13px 16px", background: "#f4f0fb", border: "1px solid #e2d9f3", borderRadius: "11px", fontSize: "13px", color: "#5a4a7a", lineHeight: 1.55 }}>
        {String(disc.concept_layer.count)} immune concept modules · {String(disc.concept_layer.scoring)}.{" "}
        <strong>{String(disc.concept_layer.invariant)}</strong>
      </div>

      {/* attribution */}
      <div style={sec}>External data attribution</div>
      <div style={{ display: "flex", flexDirection: "column", gap: "1px", background: "#e2e5ea", border: "1px solid #e2e5ea", borderRadius: "12px", overflow: "hidden" }}>
        {disc.attribution.map((a) => (
          <div key={a.source} style={{ background: "#fff", padding: "12px 16px", display: "flex", flexWrap: "wrap", gap: "6px 14px", alignItems: "baseline" }}>
            <a href={a.url} target="_blank" rel="noopener noreferrer" style={{ fontWeight: 600, fontSize: "13px", color: "#1a5fb4", minWidth: "170px" }}>
              {a.source}
            </a>
            <span style={{ fontSize: "12px", color: "#6b7280" }}>{a.cite}</span>
            <span style={{ fontSize: "11px", color: "#8a92a0", fontFamily: "'IBM Plex Mono', monospace" }}>{a.license}</span>
          </div>
        ))}
      </div>
      <p style={{ fontSize: "11.5px", color: "#9aa1ad", marginTop: "8px", lineHeight: 1.5 }}>
        ⚠️ Licence terms shown for convenience — verify each source's current terms before public launch. See docs/data_use_terms.md.
      </p>

      {/* doc links */}
      <div style={sec}>Full documentation</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
        {disc.doc_links.map((d) => {
          const href = d.kind === "external" ? d.path : `${import.meta.env.BASE_URL}${d.path}`;
          return (
            <a key={d.label} href={href} target="_blank" rel="noopener noreferrer" style={{ ...chip, color: "#1a5fb4", textDecoration: "none" }}>
              {d.label} ↗
            </a>
          );
        })}
      </div>
    </main>
  );
}
