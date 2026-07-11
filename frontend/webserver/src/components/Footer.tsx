import { DATASET_SOURCE, DATA_VERSION } from "../data/reference";
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
          <span title={DATASET_SOURCE} style={{ fontFamily: "'IBM Plex Mono', monospace", cursor: "help" }}>{DATA_VERSION}</span> ·
          descriptive-vs-decision separation · unknown ≠ 0
        </div>
        <div style={{ display: "flex", gap: "18px", fontSize: "12px", fontWeight: 500 }}>
          <a href="#">Data dictionary</a>
          <a href="#">Provenance</a>
          <span className="navlink" onClick={() => setState({ view: "apidocs" })} style={{ color: "#1a5fb4" }}>
            REST API
          </span>
          <a href="#">Bulk download</a>
        </div>
      </div>
    </footer>
  );
}
