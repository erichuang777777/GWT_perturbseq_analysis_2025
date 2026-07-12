import { useEffect, useMemo, useState } from "react";
import {
  galleryAsset,
  loadGallery,
  type GalleryChart,
  type GalleryData,
  type GalleryStructure,
} from "../data/gallery";

const ACCENT = "#5b3fb4";
type Lang = "en" | "zh";
type Tab = "figures" | "structures";

const T = {
  en: {
    heading: "Figure & structure gallery",
    sub: "Every rendered figure and predicted protein structure from this repo's pipeline, each stamped with the underlying data source. Descriptive reference material — it never feeds the readiness call.",
    figures: "Figures",
    structures: "Protein structures",
    allFamilies: "All families",
    source: "Data source",
    close: "Close",
    plddt: "Mean pLDDT",
    length: "Length",
    topology: "Topology",
    tm: "TM segments",
    residues: "aa",
    noStruct: "No AlphaFold model available for this protein.",
    openAF: "Open in AlphaFold DB",
    downloadCif: "Download structure (.cif)",
    topologyPlot: "Transmembrane topology (Protter)",
    structNote: "Predicted model (AlphaFold). pLDDT is a per-residue confidence score, not an experimental measurement.",
    count: (n: number, kind: string) => `${n} ${kind}`,
  },
  zh: {
    heading: "圖表與結構圖庫",
    sub: "本專案流程產生的每一張圖表與預測蛋白結構，皆標註其底層資料來源。此為描述性參考資料，不參與 readiness 判定。",
    figures: "圖表",
    structures: "蛋白結構",
    allFamilies: "全部類別",
    source: "資料來源",
    close: "關閉",
    plddt: "平均 pLDDT",
    length: "長度",
    topology: "拓撲",
    tm: "跨膜區段",
    residues: "個胺基酸",
    noStruct: "此蛋白無 AlphaFold 預測模型。",
    openAF: "在 AlphaFold DB 開啟",
    downloadCif: "下載結構檔 (.cif)",
    topologyPlot: "跨膜拓撲圖 (Protter)",
    structNote: "AlphaFold 預測模型。pLDDT 為每殘基信心分數，非實驗量測值。",
    count: (n: number, kind: string) => `${n} ${kind}`,
  },
};

function plddtColor(v: number | null): string {
  if (v == null) return "#9aa1ad";
  if (v >= 90) return "#0d7d5a";
  if (v >= 70) return "#3a7bd5";
  if (v >= 50) return "#c68a1a";
  return "#c0603a";
}

function FigureModal({ chart, lang, onClose }: { chart: GalleryChart; lang: Lang; onClose: () => void }) {
  const t = T[lang];
  const c = chart[lang];
  return (
    <Overlay onClose={onClose}>
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: "10px", flexWrap: "wrap" }}>
          <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "12px", fontWeight: 600, color: ACCENT, background: "#efe9fb", padding: "2px 8px", borderRadius: "6px" }}>{chart.id}</span>
          <h2 style={{ fontSize: "19px", fontWeight: 700, letterSpacing: "-.3px", margin: 0 }}>{c.title}</h2>
        </div>
        <div style={{ fontSize: "12px", color: "#8a92a0", marginTop: "-6px" }}>{chart.group} · {c.family}</div>
        <img
          src={galleryAsset(chart.img)}
          alt={c.title}
          style={{ width: "100%", maxHeight: "56vh", objectFit: "contain", background: "#fafafb", border: "1px solid #eceef2", borderRadius: "10px" }}
        />
        <p style={{ fontSize: "14px", lineHeight: 1.6, color: "#3a414d", margin: 0 }}>{c.description}</p>
        <p style={{ fontSize: "13.5px", lineHeight: 1.6, color: "#4a515e", margin: 0 }}>{c.data_explanation}</p>
        <div style={{ fontSize: "12px", lineHeight: 1.55, color: "#7a818d", background: "#f7f8fa", border: "1px solid #eceef2", borderRadius: "8px", padding: "10px 12px" }}>
          <strong style={{ color: "#5b6270" }}>{t.source}:</strong> {chart.raw_source}
        </div>
      </div>
    </Overlay>
  );
}

function StructureModal({ s, lang, onClose }: { s: GalleryStructure; lang: Lang; onClose: () => void }) {
  const t = T[lang];
  return (
    <Overlay onClose={onClose}>
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: "10px", flexWrap: "wrap" }}>
          <h2 style={{ fontSize: "20px", fontWeight: 700, letterSpacing: "-.3px", margin: 0 }}>{s.gene}</h2>
          <span style={{ fontSize: "13px", color: "#6b7280" }}>{s.protein_name}</span>
          <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "11.5px", color: "#8a92a0" }}>{s.uniprot}</span>
        </div>
        <div style={{ display: "flex", gap: "22px", flexWrap: "wrap", fontSize: "13px" }}>
          <Metric label={t.plddt} value={s.plddt != null ? s.plddt.toFixed(1) : "—"} color={plddtColor(s.plddt)} />
          <Metric label={t.length} value={s.length != null ? `${s.length} ${t.residues}` : "—"} />
          <Metric label={t.topology} value={s.topology_class || "—"} />
          <Metric label={t.tm} value={s.n_tm != null ? String(s.n_tm) : "—"} />
        </div>
        {s.protter ? (
          <div>
            <div style={{ fontSize: "12px", color: "#8a92a0", marginBottom: "6px" }}>{t.topologyPlot}</div>
            <img src={galleryAsset(s.protter)} alt={`${s.gene} topology`} style={{ width: "100%", maxHeight: "50vh", objectFit: "contain", background: "#fafafb", border: "1px solid #eceef2", borderRadius: "10px" }} />
          </div>
        ) : (
          <div style={{ fontSize: "13px", color: "#8a92a0" }}>{t.noStruct}</div>
        )}
        <div style={{ fontSize: "12px", lineHeight: 1.55, color: "#7a818d" }}>{t.structNote}</div>
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          {s.has_alphafold && (
            <a href={`https://alphafold.ebi.ac.uk/entry/${s.uniprot}`} target="_blank" rel="noreferrer" style={linkBtn}>{t.openAF} →</a>
          )}
          {s.cif && (
            <a href={galleryAsset(s.cif)} download style={{ ...linkBtn, color: "#4a515e", background: "#f2f3f6" }}>{t.downloadCif}</a>
          )}
        </div>
      </div>
    </Overlay>
  );
}

const linkBtn: React.CSSProperties = {
  fontSize: "13px",
  fontWeight: 600,
  color: ACCENT,
  background: "#efe9fb",
  padding: "8px 14px",
  borderRadius: "8px",
  textDecoration: "none",
};

function Metric({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div style={{ fontSize: "11px", color: "#9aa1ad", marginBottom: "2px" }}>{label}</div>
      <div style={{ fontSize: "15px", fontWeight: 700, color: color || "#1a1d24" }}>{value}</div>
    </div>
  );
}

function Overlay({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);
  return (
    <div
      onClick={onClose}
      style={{ position: "fixed", inset: 0, zIndex: 100, background: "rgba(20,22,28,.55)", backdropFilter: "blur(3px)", display: "flex", alignItems: "flex-start", justifyContent: "center", padding: "40px 20px", overflowY: "auto" }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{ position: "relative", width: "100%", maxWidth: "760px", background: "#fff", borderRadius: "16px", padding: "26px 28px 30px", boxShadow: "0 24px 60px -12px rgba(20,22,28,.4)" }}
      >
        <button
          onClick={onClose}
          aria-label="Close"
          style={{ position: "absolute", top: "16px", right: "16px", width: "30px", height: "30px", border: "none", borderRadius: "8px", background: "#f2f3f6", color: "#5b6270", fontSize: "17px", cursor: "pointer", lineHeight: 1 }}
        >
          ×
        </button>
        {children}
      </div>
    </div>
  );
}

export default function Gallery() {
  const [data, setData] = useState<GalleryData | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [lang, setLang] = useState<Lang>("en");
  const [tab, setTab] = useState<Tab>("figures");
  const [family, setFamily] = useState<string>("__all__");
  const [openChart, setOpenChart] = useState<GalleryChart | null>(null);
  const [openStruct, setOpenStruct] = useState<GalleryStructure | null>(null);

  useEffect(() => {
    loadGallery().then((d) => { setData(d); setStatus("ready"); }).catch(() => setStatus("error"));
  }, []);

  const t = T[lang];

  // Group by the canonical ENGLISH family (the zh.family labels in the source
  // catalog are free-form and inconsistent -- the same English family can carry
  // several zh spellings -- so keying off en.family keeps exactly one clean
  // facet per group in both languages; we localize only the display label.
  const families = useMemo(() => {
    if (!data) return [] as { key: string; label: string }[];
    const zhLabel = new Map<string, string>();
    for (const c of data.charts) if (!zhLabel.has(c.en.family)) zhLabel.set(c.en.family, c.zh.family);
    const keys = Array.from(new Set(data.charts.map((c) => c.en.family))).sort();
    return keys.map((k) => ({ key: k, label: lang === "en" ? k : zhLabel.get(k) || k }));
  }, [data, lang]);

  const shownCharts = useMemo(() => {
    if (!data) return [];
    return family === "__all__" ? data.charts : data.charts.filter((c) => c.en.family === family);
  }, [data, family]);

  if (status === "loading")
    return <Centered>Loading gallery…</Centered>;
  if (status === "error" || !data)
    return <Centered>Couldn't load the gallery catalog.</Centered>;

  return (
    <main style={{ flex: 1, maxWidth: "1280px", width: "100%", margin: "0 auto", padding: "34px 28px 70px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap" }}>
        <div style={{ maxWidth: "760px" }}>
          <h1 style={{ fontSize: "30px", fontWeight: 700, letterSpacing: "-.8px", margin: "0 0 10px" }}>{t.heading}</h1>
          <p style={{ fontSize: "14.5px", lineHeight: 1.55, color: "#4a515e", margin: 0 }}>{t.sub}</p>
        </div>
        <div style={{ display: "flex", gap: "4px", background: "#f2f3f6", borderRadius: "9px", padding: "3px" }}>
          {(["en", "zh"] as Lang[]).map((l) => (
            <button
              key={l}
              onClick={() => setLang(l)}
              style={{ padding: "6px 14px", border: "none", borderRadius: "7px", cursor: "pointer", fontSize: "13px", fontWeight: 600, background: lang === l ? "#fff" : "transparent", color: lang === l ? ACCENT : "#6b7280", boxShadow: lang === l ? "0 1px 3px rgba(0,0,0,.08)" : "none" }}
            >
              {l === "en" ? "EN" : "中文"}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", gap: "8px", margin: "24px 0 18px" }}>
        {(["figures", "structures"] as Tab[]).map((tk) => {
          const active = tab === tk;
          const n = tk === "figures" ? data.charts.length : data.structures.length;
          return (
            <button
              key={tk}
              onClick={() => setTab(tk)}
              style={{ padding: "9px 18px", border: `1.5px solid ${active ? ACCENT : "#d6dbe3"}`, borderRadius: "9px", cursor: "pointer", fontSize: "14px", fontWeight: 600, background: active ? ACCENT : "#fff", color: active ? "#fff" : "#4a515e" }}
            >
              {tk === "figures" ? t.figures : t.structures} · {n}
            </button>
          );
        })}
      </div>

      {tab === "figures" && (
        <>
          <div style={{ display: "flex", gap: "7px", flexWrap: "wrap", marginBottom: "20px" }}>
            <Chip label={t.allFamilies} active={family === "__all__"} onClick={() => setFamily("__all__")} />
            {families.map((f) => (
              <Chip key={f.key} label={f.label} active={family === f.key} onClick={() => setFamily(f.key)} />
            ))}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))", gap: "16px" }}>
            {shownCharts.map((c) => {
              const cl = c[lang];
              return (
                <button
                  key={c.id}
                  onClick={() => setOpenChart(c)}
                  className="lift"
                  style={{ textAlign: "left", border: "1px solid #e6e2f2", borderRadius: "13px", overflow: "hidden", background: "#fff", cursor: "pointer", padding: 0, display: "flex", flexDirection: "column" }}
                >
                  <div style={{ aspectRatio: "4 / 3", background: "#fafafb", borderBottom: "1px solid #eceef2", display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
                    <img src={galleryAsset(c.img)} alt={cl.title} loading="lazy" style={{ width: "100%", height: "100%", objectFit: "contain" }} />
                  </div>
                  <div style={{ padding: "11px 13px 13px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "7px", marginBottom: "5px" }}>
                      <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "10.5px", fontWeight: 600, color: ACCENT }}>{c.id}</span>
                      <span style={{ fontSize: "10.5px", color: "#9aa1ad" }}>{cl.family}</span>
                    </div>
                    <div style={{ fontSize: "13px", fontWeight: 600, color: "#1a1d24", lineHeight: 1.35 }}>{cl.title}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </>
      )}

      {tab === "structures" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "16px" }}>
          {data.structures.map((s) => (
            <button
              key={s.uniprot}
              onClick={() => setOpenStruct(s)}
              className="lift"
              style={{ textAlign: "left", border: "1px solid #e6e2f2", borderRadius: "13px", overflow: "hidden", background: "#fff", cursor: "pointer", padding: 0, display: "flex", flexDirection: "column" }}
            >
              <div style={{ aspectRatio: "1 / 1", background: "#fafafb", borderBottom: "1px solid #eceef2", display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
                {s.protter ? (
                  <img src={galleryAsset(s.protter)} alt={`${s.gene} topology`} loading="lazy" style={{ width: "100%", height: "100%", objectFit: "contain" }} />
                ) : (
                  <span style={{ fontSize: "11px", color: "#b0b6c0" }}>no model</span>
                )}
              </div>
              <div style={{ padding: "11px 13px 13px" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "6px", marginBottom: "3px" }}>
                  <span style={{ fontSize: "14px", fontWeight: 700, color: "#1a1d24" }}>{s.gene}</span>
                  {s.plddt != null && (
                    <span style={{ fontSize: "10.5px", fontWeight: 600, color: "#fff", background: plddtColor(s.plddt), padding: "1px 6px", borderRadius: "5px" }}>{s.plddt.toFixed(0)}</span>
                  )}
                </div>
                <div style={{ fontSize: "11px", color: "#8a92a0", lineHeight: 1.35, marginBottom: "6px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.protein_name}</div>
                <div style={{ fontSize: "10.5px", color: "#9aa1ad" }}>{s.topology_class}{s.n_tm ? ` · ${s.n_tm} TM` : ""}</div>
              </div>
            </button>
          ))}
        </div>
      )}

      {openChart && <FigureModal chart={openChart} lang={lang} onClose={() => setOpenChart(null)} />}
      {openStruct && <StructureModal s={openStruct} lang={lang} onClose={() => setOpenStruct(null)} />}
    </main>
  );
}

function Chip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{ padding: "6px 13px", border: `1px solid ${active ? ACCENT : "#d6dbe3"}`, borderRadius: "20px", cursor: "pointer", fontSize: "12.5px", fontWeight: 500, background: active ? "#efe9fb" : "#fff", color: active ? ACCENT : "#5b6270" }}
    >
      {label}
    </button>
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return (
    <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "#9aa1ad", fontSize: "14px", minHeight: "50vh" }}>
      {children}
    </main>
  );
}
