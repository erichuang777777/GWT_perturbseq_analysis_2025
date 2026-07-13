import { useEffect, useMemo, useState } from "react";
import { FlagshipFigure } from "../components/ui";

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
interface ValidationLadderRung {
  level: string;
  label: string;
  status: "met" | "partial" | "gap" | string;
  evidence: string;
}
interface TrackDResult {
  status?: string;
  summary?: string;
  auroc?: { screen: string; auroc: number; perm_p: number }[];
  interpretation?: string;
  secondary_magnitude_axis?: {
    summary?: string;
    auroc_no_essential?: { screen: string; auroc: number; perm_p: number }[];
    caveat?: string;
  };
  report?: string;
  shifrut_note?: string;
}
interface ValidationBlock {
  plan_doc: string;
  summary: string;
  ladder: ValidationLadderRung[];
  calibration?: Record<string, unknown>;
  track_d_phenotype_matched?: TrackDResult;
  l4_limitations?: string[];
}
interface Disclosure {
  versions: Record<string, string>;
  coverage: Record<string, unknown> & { note?: string };
  paper_reference?: {
    cite?: string;
    library_size_genes?: number;
    perturbed_with_trans_effects?: number;
    perturbed_with_trans_effects_pct?: number;
    trans_effect_significance?: string;
    mean_downstream_de_genes?: number;
    summary?: string;
  };
  disclaimer: { short: string; long: string };
  principles: { key: string; text: string }[];
  limitations: string[];
  validation?: ValidationBlock;
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
      {"measured_downstream_genes" in disc.coverage && (
        <p style={{ fontSize: "11.5px", color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "8px", padding: "9px 12px", lineHeight: 1.5, margin: "10px 0 0" }}>
          <strong>Note on <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>measured_downstream_genes</span> ({String(disc.coverage.measured_downstream_genes)}):</strong>{" "}
          this figure is the variable (measured-gene) axis of the source <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>DE_stats.h5ad</span> object, which lives only in <span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>S3</span> and is <strong>not present in this local repository</strong>. The signed-DE tables that <em>are</em> shipped here give 10,271–10,273 <strong>significant</strong> downstream genes. The gap is therefore a data-availability limitation plus the distinction between the h5ad's full measured-gene axis and the per-condition significant-gene tables — <strong>not</strong> a paper-vs-platform definition difference; it is disclosed here rather than silently reconciled.
        </p>
      )}
      {disc.paper_reference && (
        <p style={{ fontSize: "11.5px", color: "#3f5a7a", background: "#f2f6fb", border: "1px solid #cfe0f0", borderRadius: "8px", padding: "9px 12px", lineHeight: 1.5, margin: "10px 0 0" }}>
          <strong>Paper reference numbers</strong>{disc.paper_reference.cite ? <> (<span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>{disc.paper_reference.cite}</span>)</> : null}:{" "}
          the source paper reports <strong>{disc.paper_reference.perturbed_with_trans_effects?.toLocaleString()} ({disc.paper_reference.perturbed_with_trans_effects_pct}%)</strong> of perturbed genes with significant trans-effects ({disc.paper_reference.trans_effect_significance}), and a mean of <strong>{disc.paper_reference.mean_downstream_de_genes}</strong> downstream DE genes per perturbation, drawn from a <strong>{disc.paper_reference.library_size_genes?.toLocaleString()}</strong>-gene library. These authoritative figures are shown alongside — not merged into — this portal's own coverage numbers above.
        </p>
      )}

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

      {/* external-validation reproduction figure */}
      <div style={sec}>External-validation reproduction</div>
      <FlagshipFigure
        src={`${import.meta.env.BASE_URL}flagship/fig_validation.png`}
        alt="External-validation reproduction figure: three cross-checks against Open Targets, STRING and the independent GEO GSE318876 CRISPRa HIV screen, with a right panel showing STRING known-partner recovery for the five flagship genes; per-check tallies are printed on the figure panels"
        title="External evidence reproduction"
        caption="Three corroborative cross-checks the pipeline ran against public sources — Open Targets association re-checks, STRING known-partner recovery for the flagship genes, and overlap with the independent GEO GSE318876 CRISPRa HIV screen. The exact per-check tallies are printed on the figure's own panels. This is a corroborative overlap figure, not a live re-query; the phenotype-matched external screen (Track D) is documented separately as null — see the validation ladder below."
        footnote={<>GSE318876 measures HIV infection, not T-cell activation, so this is a corroborative overlap check (association ≠ causation), not a phenotype-matched confirmation.</>}
        source="Open Targets · STRING v12 · GEO GSE318876 · public/flagship/fig_validation.png"
      />

      {/* validation ladder */}
      {disc.validation?.ladder?.length ? (
        <>
          <div style={sec}>Validation ladder</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {disc.validation.ladder.map((rung) => {
              const statusColor =
                rung.status === "met" ? "#0d7d5a" : rung.status === "partial" ? "#b7791f" : rung.status === "gap" ? "#c0392b" : "#6b7280";
              return (
                <div
                  key={rung.level}
                  style={{ display: "flex", gap: "12px", alignItems: "baseline", flexWrap: "wrap", border: "1px solid #e2e5ea", borderRadius: "9px", padding: "11px 14px" }}
                >
                  <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "12px", fontWeight: 700, color: "#1a5fb4", minWidth: "28px" }}>
                    {rung.level}
                  </span>
                  <span style={{ fontSize: "13px", fontWeight: 600, color: "#1a1d24", minWidth: "140px" }}>{rung.label}</span>
                  <span
                    style={{
                      fontFamily: "'IBM Plex Mono', monospace",
                      fontSize: "10.5px",
                      fontWeight: 700,
                      letterSpacing: ".4px",
                      textTransform: "uppercase",
                      color: "#fff",
                      background: statusColor,
                      borderRadius: "5px",
                      padding: "2px 7px",
                    }}
                  >
                    {rung.status}
                  </span>
                  <span style={{ fontSize: "12.5px", color: "#4a515e", lineHeight: 1.5, flex: "1 1 320px" }}>{rung.evidence}</span>
                </div>
              );
            })}
          </div>
          <p style={{ fontSize: "13px", color: "#4a515e", lineHeight: 1.6, margin: "12px 0 0" }}>{disc.validation.summary}</p>
          {disc.validation.track_d_phenotype_matched ? (
            <div style={{ marginTop: "12px", border: "1px solid #eddfc0", background: "#fbf9f2", borderRadius: "10px", padding: "12px 15px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "9px", marginBottom: "6px" }}>
                <span style={{ fontSize: "12.5px", fontWeight: 700, color: "#1a1d24" }}>Track D — phenotype-matched external screens (actual run)</span>
                <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "10.5px", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".4px", color: "#fff", background: "#b7791f", borderRadius: "5px", padding: "2px 7px" }}>
                  null result
                </span>
              </div>
              {disc.validation.track_d_phenotype_matched.auroc?.length ? (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px 14px", fontFamily: "'IBM Plex Mono', monospace", fontSize: "11.5px", color: "#7a6a3f", marginBottom: "6px" }}>
                  {disc.validation.track_d_phenotype_matched.auroc.map((a) => (
                    <span key={a.screen}>{a.screen}: AUROC {a.auroc.toFixed(3)} (p {a.perm_p})</span>
                  ))}
                </div>
              ) : null}
              <p style={{ fontSize: "12px", color: "#7a6a3f", lineHeight: 1.55, margin: 0 }}>
                {disc.validation.track_d_phenotype_matched.interpretation}
              </p>
              {disc.validation.track_d_phenotype_matched.secondary_magnitude_axis ? (
                <div style={{ marginTop: "8px", paddingTop: "8px", borderTop: "1px dashed #e0d3a8" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                    <span style={{ fontSize: "11.5px", fontWeight: 700, color: "#1a1d24" }}>Fair-axis secondary (magnitude, exploratory)</span>
                    <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "10px", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".4px", color: "#fff", background: "#0d7d5a", borderRadius: "5px", padding: "1px 6px" }}>
                      passes (w/ confound)
                    </span>
                  </div>
                  {disc.validation.track_d_phenotype_matched.secondary_magnitude_axis.auroc_no_essential?.length ? (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "6px 14px", fontFamily: "'IBM Plex Mono', monospace", fontSize: "11.5px", color: "#7a6a3f", marginBottom: "4px" }}>
                      {disc.validation.track_d_phenotype_matched.secondary_magnitude_axis.auroc_no_essential.map((a) => (
                        <span key={a.screen}>{a.screen}: AUROC {a.auroc.toFixed(3)} (p {a.perm_p})</span>
                      ))}
                    </div>
                  ) : null}
                  <p style={{ fontSize: "11.5px", color: "#7a6a3f", lineHeight: 1.5, margin: 0 }}>
                    {disc.validation.track_d_phenotype_matched.secondary_magnitude_axis.summary}{" "}
                    {disc.validation.track_d_phenotype_matched.secondary_magnitude_axis.caveat}
                  </p>
                </div>
              ) : null}
              {disc.validation.track_d_phenotype_matched.shifrut_note ? (
                <p style={{ fontSize: "11px", color: "#9aa1ad", lineHeight: 1.5, margin: "6px 0 0" }}>
                  {disc.validation.track_d_phenotype_matched.shifrut_note}
                </p>
              ) : null}
            </div>
          ) : null}
          <p style={{ fontSize: "11.5px", color: "#9aa1ad", marginTop: "6px" }}>
            src:{" "}
            <a
              href="https://github.com/erichuang777777/GWT_perturbseq_analysis_2025/blob/main/docs/perturbation_validation_plan.md"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "#1a5fb4" }}
            >
              {disc.validation.plan_doc}
            </a>
          </p>
        </>
      ) : null}

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
