import { useEffect, useMemo, useState } from "react";
import { galleryAsset, loadGallery, type GalleryChart, type GalleryData, type GalleryStructure } from "../data/gallery";
import Chip from "../components/ui/Chip";
import { InlineScreen } from "../components/ui/ScreenState";
import FigureModal from "./gallery/FigureModal";
import StructureModal from "./gallery/StructureModal";
import PageReferences from "../components/ui/PageReferences";
import { T, plddtColor, type Lang } from "./gallery/i18n";
import { useStore } from "../store/store";

const ACCENT = "#5b3fb4";
const CORE5_ORDER = ["CD3E", "CD247", "LAT", "PLCG1", "VAV1"];
const CORE5_INDEX = new Map(CORE5_ORDER.map((gene, index) => [gene, index]));
const PUBLICATION_HIGHLIGHT_IDS = ["A16", "A15", "A3"];
const FAMILY_ORDER = [
  "Dimensionality reduction & composite",
  "Distributions",
  "Matrices",
  "Networks",
  "Ranking",
  "Hierarchical & interactive",
];
type Tab = "figures" | "structures";

export default function Gallery() {
  const { setState } = useStore();
  const [data, setData] = useState<GalleryData | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  // Portal is English-only (delivery requirement) — no language switcher.
  const lang: Lang = "en";
  const [tab, setTab] = useState<Tab>("figures");
  const [family, setFamily] = useState<string>("__all__");
  const [openChart, setOpenChart] = useState<GalleryChart | null>(null);
  const [openStruct, setOpenStruct] = useState<GalleryStructure | null>(null);

  useEffect(() => {
    loadGallery().then((d) => { setData(d); setStatus("ready"); }).catch(() => setStatus("error"));
  }, []);

  const t = T[lang];

  // Only primary-placement charts appear in the main gallery. Supplement
  // charts live in the Docs → Supplementary tab; archived charts are retired.
  const primaryCharts = useMemo(
    () => (data ? data.charts.filter((c) => c.placement === "primary") : []),
    [data],
  );

  // Group by the canonical English family label.
  const families = useMemo(() => {
    const keys = Array.from(new Set(primaryCharts.map((c) => c.en.family))).sort();
    return keys.map((k) => ({ key: k, label: k }));
  }, [primaryCharts]);

  const shownCharts = useMemo(() => {
    return family === "__all__" ? primaryCharts : primaryCharts.filter((c) => c.en.family === family);
  }, [primaryCharts, family]);

  const publicationCharts = useMemo(
    () => shownCharts.filter((c) => c.group === "Analysis & publication"),
    [shownCharts],
  );
  const publicationHighlights = useMemo(
    () => PUBLICATION_HIGHLIGHT_IDS.map((id) => publicationCharts.find((c) => c.id === id)).filter((c): c is GalleryChart => Boolean(c)),
    [publicationCharts],
  );
  const publicationRemainder = useMemo(
    () => publicationCharts.filter((c) => !PUBLICATION_HIGHLIGHT_IDS.includes(c.id)),
    [publicationCharts],
  );
  const secondaryCharts = useMemo(
    () => [...publicationRemainder, ...shownCharts.filter((c) => c.group !== "Analysis & publication")],
    [publicationRemainder, shownCharts],
  );
  const secondaryGroups = useMemo(() => {
    const groups = new Map<string, GalleryChart[]>();
    for (const chart of secondaryCharts) {
      const family = chart.en.family;
      groups.set(family, [...(groups.get(family) ?? []), chart]);
    }
    return [...groups.entries()].sort(([a], [b]) => {
      const ai = FAMILY_ORDER.indexOf(a);
      const bi = FAMILY_ORDER.indexOf(b);
      return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi) || a.localeCompare(b);
    });
  }, [secondaryCharts]);
  const orderedStructures = useMemo(
    () => [...data?.structures ?? []].sort((a, b) => (CORE5_INDEX.get(a.gene) ?? 999) - (CORE5_INDEX.get(b.gene) ?? 999)),
    [data],
  );

  const chartCard = (c: GalleryChart, large: boolean, showDescription = false) => {
    const cl = c[lang];
    return (
      <button
        key={c.id}
        onClick={() => setOpenChart(c)}
        className="lift"
        style={{ textAlign: "left", border: "1px solid #e6e2f2", borderRadius: "13px", overflow: "hidden", background: "#fff", cursor: "pointer", padding: 0, display: "flex", flexDirection: "column" }}
      >
        <div style={{ aspectRatio: large ? "16 / 10" : "4 / 3", background: "#fafafb", borderBottom: "1px solid #eceef2", display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
          <img src={galleryAsset(c.img)} alt={cl.title} loading="lazy" style={{ width: "100%", height: "100%", objectFit: "contain" }} />
        </div>
        <div style={{ padding: large ? "14px 16px 16px" : "11px 13px 13px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "7px", marginBottom: "5px" }}>
            <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: large ? "11px" : "10.5px", fontWeight: 600, color: ACCENT }}>{c.id}</span>
            <span style={{ fontSize: large ? "11px" : "10.5px", color: "#9aa1ad" }}>{cl.family}</span>
          </div>
          <div style={{ fontSize: large ? "14px" : "13px", fontWeight: 600, color: "#1a1d24", lineHeight: 1.35 }}>{cl.title}</div>
          {showDescription && <div style={{ fontSize: "12px", lineHeight: 1.5, color: "#5f6672", marginTop: "8px" }}>{cl.description}</div>}
        </div>
      </button>
    );
  };

  if (status === "loading") return <InlineScreen>Loading gallery…</InlineScreen>;
  if (status === "error" || !data) return <InlineScreen>Couldn't load the gallery catalog.</InlineScreen>;

  return (
    <main style={{ flex: 1, maxWidth: "1440px", width: "100%", margin: "0 auto", padding: "34px 28px 70px" }}>
      <div style={{ display: "flex", gap: "4px", marginBottom: "18px", background: "#f2f0f9", borderRadius: "9px", padding: "3px", width: "fit-content" }}>
        <span className="navlink" onClick={() => setState({ view: "figures" })} style={{ padding: "6px 16px", borderRadius: "7px", fontSize: "12px", fontWeight: 600, color: "#5b4a86", background: "transparent" }}>Interactive figures</span>
        <span className="navlink" style={{ padding: "6px 16px", borderRadius: "7px", fontSize: "12px", fontWeight: 600, color: "#fff", background: ACCENT }}>Gallery (EDA)</span>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap" }}>
        <div style={{ maxWidth: "760px" }}>
          <h1 style={{ fontSize: "30px", fontWeight: 700, letterSpacing: "-.8px", margin: "0 0 10px" }}>{t.heading}</h1>
          <p style={{ fontSize: "14.5px", lineHeight: 1.55, color: "#4a515e", margin: 0 }}>{t.sub}</p>
        </div>
      </div>

      <div style={{ display: "flex", gap: "8px", margin: "24px 0 18px" }}>
        {(["figures", "structures"] as Tab[]).map((tk) => {
          const active = tab === tk;
          const n = tk === "figures" ? primaryCharts.length : data.structures.length;
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
            <Chip label={t.allFamilies} active={family === "__all__"} onClick={() => setFamily("__all__")} accent={ACCENT} />
            {families.map((f) => (
              <Chip key={f.key} label={f.label} active={family === f.key} onClick={() => setFamily(f.key)} accent={ACCENT} />
            ))}
          </div>
          {publicationHighlights.length > 0 && (
            <section style={{ marginBottom: "30px" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: "10px", margin: "0 0 12px" }}>
                <h2 style={{ fontSize: "20px", margin: 0, color: "#1a1d24" }}>Publication highlights</h2>
                <span style={{ fontSize: "12px", color: "#7a6a3f" }}>3 key figures</span>
              </div>
              <div style={{ fontSize: "13px", lineHeight: 1.5, color: "#5f6672", marginBottom: "14px", maxWidth: "850px" }}>
                The three figures that best summarize the platform's contribution: reproducible curation, validation, and translation into a delivery decision. Click any figure for the full publication view and provenance.
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "18px" }}>
                {publicationHighlights.map((c) => chartCard(c, true, true))}
              </div>
            </section>
          )}
          {secondaryGroups.map(([family, charts]) => (
            <section key={family} style={{ marginBottom: "30px" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: "10px", margin: "0 0 12px" }}>
                <h2 style={{ fontSize: "20px", margin: 0, color: "#1a1d24" }}>{family}</h2>
                <span style={{ fontSize: "12px", color: "#7a8491" }}>{charts.length} figures</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))", gap: "16px" }}>
                {charts.map((c) => chartCard(c, false))}
              </div>
            </section>
          ))}
        </>
      )}

      {tab === "structures" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "16px" }}>
          {orderedStructures.map((s) => (
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
                  {CORE5_INDEX.has(s.gene) && <span style={{ fontSize: "9.5px", fontWeight: 700, color: "#fff", background: ACCENT, padding: "2px 6px", borderRadius: "5px" }}>CORE-5</span>}
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

      <PageReferences
        keys={["gwt_primary", "alphafold", "string", "reactome", "open_targets", "gnomad", "hpa"]}
      />

      {openChart && <FigureModal chart={openChart} lang={lang} onClose={() => setOpenChart(null)} />}
      {openStruct && <StructureModal s={openStruct} lang={lang} onClose={() => setOpenStruct(null)} />}
    </main>
  );
}
