import { SOURCE_VERSION } from "../data/dataset";
import { DATA_VERSION } from "../data/reference";
import { useStore } from "../store/store";

export default function Footer() {
  const { setState } = useStore();
  return (
    <footer style={{ borderTop: "1px solid #e2e5ea", padding: "22px 28px", marginTop: "auto" }}>
      <div
        style={{
          maxWidth: "1400px",
          margin: "0 auto",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "20px",
          flexWrap: "wrap",
        }}
      >
        <div style={{ fontSize: "11.5px", color: "#9aa1ad", lineHeight: 1.5 }}>
          CD4 Target Discovery Portal · genome-scale Perturb-seq ·{" "}
          <span title={SOURCE_VERSION} style={{ fontFamily: "'IBM Plex Mono', monospace", cursor: "help" }}>{DATA_VERSION}</span> ·
          descriptive-vs-decision separation · unknown ≠ 0
        </div>
        <div style={{ display: "flex", gap: "18px", fontSize: "12px", fontWeight: 500 }}>
          {/* Real destinations: the static API's provenance manifest and the full
              dataset download (both served by the CDN). "Data dictionary" was a
              dead href="#" with no served artifact, so it's removed rather than faked. */}
          <a href={`${import.meta.env.BASE_URL}api/v1/meta.json`} target="_blank" rel="noreferrer" style={{ color: "#1a5fb4" }}>
            Provenance
          </a>
          <span className="navlink" onClick={() => setState({ view: "apidocs" })} style={{ color: "#1a5fb4" }}>
            REST API
          </span>
          <a href={`${import.meta.env.BASE_URL}real-dataset.json`} download style={{ color: "#1a5fb4" }}>
            Bulk download
          </a>
        </div>
      </div>
    </footer>
  );
}
