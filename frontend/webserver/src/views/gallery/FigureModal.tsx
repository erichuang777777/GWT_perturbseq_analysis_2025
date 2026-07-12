import { galleryAsset, type GalleryChart } from "../../data/gallery";
import Modal from "../../components/ui/Modal";
import { T, type Lang } from "./i18n";

const ACCENT = "#5b3fb4";

export default function FigureModal({ chart, lang, onClose }: { chart: GalleryChart; lang: Lang; onClose: () => void }) {
  const t = T[lang];
  const c = chart[lang];
  return (
    <Modal onClose={onClose}>
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
    </Modal>
  );
}
