import { useEffect, useMemo, useState } from "react";
import { renderMarkdown } from "../lib/markdown";
import { galleryAsset, loadGallery, type GalleryChart } from "../data/gallery";

// Documentation hub. Surfaces the project's user-facing docs entirely in
// English: an authored getting-started / plain-language / researcher guide
// (from docs/docs.json), links to the full repo docs on GitHub, and two
// embedded English markdown documents (the manuscript appendix and the
// known-limitations register), fetched and rendered on demand.

const ACCENT = "#5b3fb4";

type DocStep = { n: number; h: string; t: string };
type RefDoc = { label: string; path: string; desc: string };
type EmbeddedDoc = { key: string; title: string; file: string; desc: string };

interface DocsData {
  repo_base: string;
  getting_started: { title: string; blurb: string; run_local: string[]; deploy: string; dataset: string };
  for_everyone: { title: string; blurb: string; steps: DocStep[] };
  for_researchers: { title: string; blurb: string; sections: { h: string; t: string }[] };
  embedded_docs: EmbeddedDoc[];
  reference_docs: RefDoc[];
}

type Tab = "start" | "everyone" | "researchers" | "reference" | "supplementary" | "manuscript" | "known_limitations";

interface SuppTable { file: string; title: string; desc: string; columns: string[]; rows: (string | number)[][] }
interface SuppData {
  title: string; intro: string;
  dataset_shape: Record<string, unknown>;
  tables: SuppTable[];
  large_tables: { file: string; title: string; rows: string | number }[];
  plots: { file: string; title: string }[];
}

export default function Docs() {
  const [data, setData] = useState<DocsData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("start");
  const [md, setMd] = useState<Record<string, string>>({});
  const [mdErr, setMdErr] = useState<string | null>(null);
  const [supp, setSupp] = useState<SuppData | null>(null);
  const [suppErr, setSuppErr] = useState<string | null>(null);
  const [suppFigs, setSuppFigs] = useState<GalleryChart[] | null>(null);

  const base = import.meta.env.BASE_URL;

  useEffect(() => {
    fetch(`${base}docs/docs.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`docs.json ${r.status}`);
        return r.json() as Promise<DocsData>;
      })
      .then(setData)
      .catch((e) => setErr(String(e)));
  }, [base]);

  // Lazily fetch an embedded markdown doc the first time its tab is opened.
  useEffect(() => {
    if (!data) return;
    const doc = data.embedded_docs.find((d) => d.key === tab);
    if (!doc || md[doc.key] != null) return;
    fetch(`${base}${doc.file}`)
      .then((r) => {
        if (!r.ok) throw new Error(`${doc.file} ${r.status}`);
        return r.text();
      })
      .then((text) => setMd((m) => ({ ...m, [doc.key]: text })))
      .catch((e) => setMdErr(String(e)));
  }, [tab, data, md, base]);

  // Lazily fetch the supplementary EDA payload the first time that tab opens.
  useEffect(() => {
    if (tab !== "supplementary" || supp) return;
    fetch(`${base}docs/supplementary_eda.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`supplementary_eda.json ${r.status}`);
        return r.json() as Promise<SuppData>;
      })
      .then(setSupp)
      .catch((e) => setSuppErr(String(e)));
  }, [tab, supp, base]);

  // Supplement-placement gallery charts also surface under this tab.
  useEffect(() => {
    if (tab !== "supplementary" || suppFigs) return;
    loadGallery()
      .then((g) => setSuppFigs(g.charts.filter((c) => c.placement === "supplement")))
      .catch(() => setSuppFigs([]));
  }, [tab, suppFigs]);

  const tabs: { k: Tab; label: string }[] = useMemo(
    () => [
      { k: "start", label: "Getting started" },
      { k: "everyone", label: "For everyone" },
      { k: "researchers", label: "For researchers" },
      { k: "reference", label: "Reference docs" },
      { k: "supplementary", label: "Supplementary (EDA)" },
      { k: "manuscript", label: "Manuscript (appendix)" },
      { k: "known_limitations", label: "Known limitations" },
    ],
    [],
  );

  if (err)
    return (
      <main style={{ flex: 1, maxWidth: "980px", margin: "0 auto", width: "100%", padding: "40px 28px" }}>
        <p style={{ color: "#b23b3b", fontSize: "14px" }}>Could not load documentation: {err}</p>
      </main>
    );
  if (!data)
    return (
      <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#9aa1ad", fontSize: "14px" }}>
        Loading documentation…
      </main>
    );

  const card: React.CSSProperties = { border: "1px solid #e2e5ea", borderRadius: "14px", padding: "20px 22px", background: "#fff" };
  const sec: React.CSSProperties = { fontSize: "16px", fontWeight: 700, margin: "0 0 12px" };

  return (
    <main style={{ flex: 1, maxWidth: "980px", margin: "0 auto", width: "100%", padding: "40px 28px 80px" }}>
      <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: ".8px", color: ACCENT, textTransform: "uppercase", marginBottom: "10px" }}>
        Documentation
      </div>
      <h1 style={{ fontSize: "28px", fontWeight: 700, margin: "0 0 10px", letterSpacing: "-.4px" }}>Docs &amp; references</h1>
      <p style={{ fontSize: "14.5px", lineHeight: 1.6, color: "#4a515e", margin: "0 0 22px", maxWidth: "700px" }}>
        Everything you need to run, understand, and cite this platform — a plain-language tour, a researcher's
        guide, links to the full repository documentation, the literature reference set, and the full manuscript draft.
      </p>

      {/* tab bar */}
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "26px" }}>
        {tabs.map((t) => {
          const active = tab === t.k;
          return (
            <button
              key={t.k}
              onClick={() => setTab(t.k)}
              style={{
                padding: "8px 15px", border: `1.5px solid ${active ? ACCENT : "#d6dbe3"}`, borderRadius: "9px",
                cursor: "pointer", fontSize: "13px", fontWeight: 600,
                background: active ? ACCENT : "#fff", color: active ? "#fff" : "#4a515e",
              }}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {tab === "start" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
          <div style={{ padding: "13px 16px", background: "#fdf6e3", border: "1px solid #eddfc0", borderRadius: "11px", fontSize: "13px", color: "#7a6420", lineHeight: 1.55 }}>
            <strong style={{ color: "#8a6516" }}>Research / hypothesis-generating use only — not clinical software.</strong>
          </div>
          <p style={{ fontSize: "14px", lineHeight: 1.65, color: "#3a414d", margin: 0 }}>{data.getting_started.blurb}</p>
          <div style={card}>
            <div style={sec}>Run it locally</div>
            <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "13.5px", lineHeight: 1.7, color: "#3a414d" }}>
              {data.getting_started.run_local.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          </div>
          <div style={card}>
            <div style={sec}>Deploy</div>
            <p style={{ margin: 0, fontSize: "13.5px", lineHeight: 1.65, color: "#3a414d" }}>{data.getting_started.deploy}</p>
          </div>
          <div style={card}>
            <div style={sec}>Data version</div>
            <p style={{ margin: 0, fontSize: "13.5px", lineHeight: 1.65, color: "#3a414d" }}>{data.getting_started.dataset}</p>
          </div>
        </div>
      )}

      {tab === "everyone" && (
        <div>
          <p style={{ fontSize: "14px", lineHeight: 1.65, color: "#3a414d", margin: "0 0 18px" }}>{data.for_everyone.blurb}</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "14px" }}>
            {data.for_everyone.steps.map((s) => (
              <div key={s.n} style={card}>
                <div style={{ display: "flex", alignItems: "center", gap: "9px", marginBottom: "7px" }}>
                  <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "24px", height: "24px", borderRadius: "50%", background: "#efe9fb", color: ACCENT, fontSize: "12px", fontWeight: 700 }}>{s.n}</span>
                  <span style={{ fontSize: "14px", fontWeight: 700, color: "#1a1d24" }}>{s.h}</span>
                </div>
                <p style={{ margin: 0, fontSize: "13px", lineHeight: 1.6, color: "#4a515e" }}>{s.t}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "researchers" && (
        <div>
          <p style={{ fontSize: "14px", lineHeight: 1.65, color: "#3a414d", margin: "0 0 18px" }}>{data.for_researchers.blurb}</p>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {data.for_researchers.sections.map((s, i) => (
              <div key={i} style={card}>
                <div style={{ fontSize: "14px", fontWeight: 700, color: "#1a1d24", marginBottom: "5px" }}>{s.h}</div>
                <p style={{ margin: 0, fontSize: "13px", lineHeight: 1.6, color: "#4a515e" }}>{s.t}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "reference" && (
        <div>
          <p style={{ fontSize: "14px", lineHeight: 1.65, color: "#3a414d", margin: "0 0 18px" }}>
            The full repository documentation. These open on GitHub (the authoritative source of each file).
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {data.reference_docs.map((d) => (
              <a key={d.path} href={`${data.repo_base}${d.path}`} target="_blank" rel="noopener noreferrer"
                 style={{ ...card, textDecoration: "none", display: "block" }}>
                <div style={{ fontSize: "13.5px", fontWeight: 700, color: "#1a5fb4", marginBottom: "3px" }}>{d.label} ↗</div>
                <div style={{ fontSize: "12.5px", color: "#6b7280", lineHeight: 1.55 }}>{d.desc}</div>
              </a>
            ))}
          </div>
        </div>
      )}

      {tab === "supplementary" && (
        <div>
          {suppErr && !supp ? (
            <p style={{ color: "#b23b3b", fontSize: "13px" }}>Could not load supplementary_eda.json: {suppErr}</p>
          ) : !supp ? (
            <p style={{ color: "#9aa1ad", fontSize: "13px" }}>Loading supplementary EDA…</p>
          ) : (
            <div>
              <p style={{ fontSize: "14px", lineHeight: 1.65, color: "#3a414d", margin: "0 0 8px" }}>{supp.intro}</p>
              {/* dataset shape */}
              <div style={{ ...card, marginBottom: "20px" }}>
                <div style={{ fontSize: "13px", fontWeight: 700, marginBottom: "8px" }}>Dataset shape</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                  {Object.entries(supp.dataset_shape).map(([k, v]) => (
                    <span key={k} style={{ fontSize: "12px", background: "#f2f5f9", borderRadius: "7px", padding: "5px 10px", color: "#3a414d" }}>
                      <strong>{Array.isArray(v) ? v.join(" · ") : String(v)}</strong> {k}
                    </span>
                  ))}
                </div>
              </div>

              {/* supplement-placement gallery figures */}
              {suppFigs && suppFigs.length > 0 && (
                <div style={{ marginBottom: "24px" }}>
                  <div style={{ fontSize: "13px", fontWeight: 700, margin: "0 0 4px" }}>Supplementary figures</div>
                  <div style={{ fontSize: "12px", color: "#6b7280", marginBottom: "12px", lineHeight: 1.5 }}>
                    Alternate views of the primary-gallery distributions, retained here as supporting evidence.
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: "16px" }}>
                    {suppFigs.map((c) => (
                      <div key={c.id} style={card}>
                        <div style={{ aspectRatio: "4 / 3", background: "#fafafb", border: "1px solid #eef0f3", borderRadius: "8px", overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", marginBottom: "8px" }}>
                          <img src={galleryAsset(c.img)} alt={c.en.title} loading="lazy" style={{ width: "100%", height: "100%", objectFit: "contain" }} />
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "7px", marginBottom: "3px" }}>
                          <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "10.5px", fontWeight: 600, color: ACCENT }}>{c.id}</span>
                          <span style={{ fontSize: "10.5px", color: "#9aa1ad" }}>{c.en.family}</span>
                        </div>
                        <div style={{ fontSize: "12.5px", fontWeight: 600, color: "#1a1d24", lineHeight: 1.35 }}>{c.en.title}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* embedded tables */}
              {supp.tables.map((t) => (
                <div key={t.file} style={{ ...card, marginBottom: "16px" }}>
                  <div style={{ fontSize: "13.5px", fontWeight: 700, marginBottom: "3px" }}>{t.title}</div>
                  <div style={{ fontSize: "12px", color: "#6b7280", marginBottom: "10px", lineHeight: 1.5 }}>{t.desc}</div>
                  <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                      <thead>
                        <tr style={{ textAlign: "left", color: "#8a92a0", fontSize: "10.5px", textTransform: "uppercase", letterSpacing: ".3px" }}>
                          {t.columns.map((c) => <th key={c} style={{ padding: "5px 8px", whiteSpace: "nowrap" }}>{c}</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {t.rows.map((row, ri) => (
                          <tr key={ri} style={{ borderTop: "1px solid #eef0f3" }}>
                            {row.map((cell, ci) => (
                              <td key={ci} style={{ padding: "5px 8px", fontFamily: typeof cell === "number" ? "'IBM Plex Mono', monospace" : undefined, color: "#3a414d", whiteSpace: "nowrap" }}>
                                {typeof cell === "number" ? (Number.isInteger(cell) ? cell : cell.toFixed(2)) : String(cell)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <a href={`${base}docs/supplementary/${t.file}`} download
                     style={{ fontSize: "11.5px", color: "#1a5fb4", textDecoration: "none", display: "inline-block", marginTop: "8px" }}>
                    Download {t.file} ↓
                  </a>
                </div>
              ))}

              {/* plots */}
              <div style={{ fontSize: "13px", fontWeight: 700, margin: "22px 0 10px" }}>Diagnostic plots</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                {supp.plots.map((p) => (
                  <div key={p.file} style={card}>
                    <div style={{ fontSize: "12.5px", fontWeight: 600, marginBottom: "8px", color: "#3a414d" }}>{p.title}</div>
                    <img src={`${base}docs/${p.file}`} alt={p.title} style={{ width: "100%", borderRadius: "8px", border: "1px solid #eef0f3" }} />
                  </div>
                ))}
              </div>

              {/* large tables -> download only */}
              <div style={{ fontSize: "13px", fontWeight: 700, margin: "22px 0 10px" }}>Full tables (download)</div>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {supp.large_tables.map((t) => (
                  <a key={t.file} href={`${base}docs/supplementary/${t.file}`} download
                     style={{ ...card, textDecoration: "none", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: "12.5px", fontWeight: 600, color: "#1a5fb4" }}>{t.title} ↓</span>
                    <span style={{ fontSize: "11.5px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace" }}>{t.rows} rows · {t.file}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {(tab === "manuscript" || tab === "known_limitations") && (() => {
        const doc = data.embedded_docs.find((d) => d.key === tab)!;
        const text = md[doc.key];
        return (
          <div>
            <p style={{ fontSize: "13.5px", lineHeight: 1.6, color: "#6b7280", margin: "0 0 18px" }}>{doc.desc}</p>
            {mdErr && !text ? (
              <p style={{ color: "#b23b3b", fontSize: "13px" }}>Could not load {doc.file}: {mdErr}</p>
            ) : !text ? (
              <p style={{ color: "#9aa1ad", fontSize: "13px" }}>Loading {doc.title}…</p>
            ) : (
              <div
                style={{ fontSize: "14px", lineHeight: 1.7, color: "#2b313b" }}
                dangerouslySetInnerHTML={{ __html: renderMarkdown(text) }}
              />
            )}
          </div>
        );
      })()}
    </main>
  );
}
