import { galleryAsset, type GalleryStructure } from "../../data/gallery";
import Modal from "../../components/ui/Modal";
import StatTile from "../../components/ui/StatTile";
import { T, plddtColor, type Lang } from "./i18n";

const linkBtn: React.CSSProperties = {
  fontSize: "13px",
  fontWeight: 600,
  color: "#5b3fb4",
  background: "#efe9fb",
  padding: "8px 14px",
  borderRadius: "8px",
  textDecoration: "none",
};

export default function StructureModal({ s, lang, onClose }: { s: GalleryStructure; lang: Lang; onClose: () => void }) {
  const t = T[lang];
  return (
    <Modal onClose={onClose}>
      <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: "10px", flexWrap: "wrap" }}>
          <h2 style={{ fontSize: "20px", fontWeight: 700, letterSpacing: "-.3px", margin: 0 }}>{s.gene}</h2>
          <span style={{ fontSize: "13px", color: "#6b7280" }}>{s.protein_name}</span>
          <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: "11.5px", color: "#8a92a0" }}>{s.uniprot}</span>
        </div>
        <div style={{ display: "flex", gap: "22px", flexWrap: "wrap", fontSize: "13px" }}>
          <StatTile size="sm" label={t.plddt} value={s.plddt != null ? s.plddt.toFixed(1) : "—"} color={plddtColor(s.plddt)} />
          <StatTile size="sm" label={t.length} value={s.length != null ? `${s.length} ${t.residues}` : "—"} />
          <StatTile size="sm" label={t.topology} value={s.topology_class || "—"} />
          <StatTile size="sm" label={t.tm} value={s.n_tm != null ? String(s.n_tm) : "—"} />
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
    </Modal>
  );
}
