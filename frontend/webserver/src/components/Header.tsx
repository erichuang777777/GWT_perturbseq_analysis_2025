import { TARGETS } from "../data/dataset";
import { DATA_VERSION } from "../data/reference";
import { useStore } from "../store/store";

export default function Header() {
  const { state, setState } = useStore();
  const v = state.view;

  const rActive = v === "explorer" || v === "dossier" || v === "compare";
  const cActive = v === "clinical";
  const fActive = v === "figures";
  const gActive = v === "gallery";
  const tab = (active: boolean, base: string) => ({
    color: active ? "#fff" : "#4a515e",
    background: active ? base : "transparent",
  });
  const rT = tab(rActive, "#1a5fb4");
  const cT = tab(cActive, "#0d7d5a");
  const fT = tab(fActive, "#5b3fb4");
  const gT = tab(gActive, "#5b3fb4");

  const slGenes = state.shortlist.filter((g) => TARGETS.find((x) => x.gene === g));

  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 40,
        display: "flex",
        alignItems: "center",
        gap: "20px",
        padding: "0 28px",
        height: "60px",
        background: "rgba(255,255,255,.92)",
        backdropFilter: "blur(8px)",
        borderBottom: "1px solid #e2e5ea",
      }}
    >
      <div
        className="navlink"
        onClick={() => setState({ view: "home" })}
        style={{ display: "flex", alignItems: "center", gap: "11px" }}
      >
        <div
          style={{
            width: "30px",
            height: "30px",
            borderRadius: "7px",
            background: "linear-gradient(145deg,#1a5fb4,#123f7d)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 2px 8px -2px rgba(26,95,180,.5)",
          }}
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
            <circle cx="6" cy="7" r="2.4" fill="#fff" />
            <circle cx="18" cy="7" r="2.4" fill="#9dc1ee" />
            <circle cx="12" cy="17" r="2.4" fill="#fff" />
            <path d="M6 7L12 17L18 7" stroke="#fff" strokeWidth="1.5" opacity=".7" />
          </svg>
        </div>
        <div style={{ lineHeight: 1.05 }}>
          <div style={{ fontSize: "14.5px", fontWeight: 700, letterSpacing: "-.2px" }}>
            CD4&nbsp;Target&nbsp;Discovery&nbsp;Portal
          </div>
          <div style={{ fontSize: "10.5px", color: "#7a8290", fontWeight: 500, letterSpacing: ".3px" }}>
            Genome-scale Perturb-seq · CD4 T cell
          </div>
        </div>
      </div>

      <nav style={{ display: "flex", gap: "4px", marginLeft: "14px" }}>
        <span
          className="navlink"
          onClick={() => setState({ view: "explorer" })}
          style={{ padding: "7px 13px", borderRadius: "7px", fontSize: "13px", fontWeight: 500, color: rT.color, background: rT.background }}
        >
          Researcher
        </span>
        <span
          className="navlink"
          onClick={() => setState({ view: "clinical" })}
          style={{ padding: "7px 13px", borderRadius: "7px", fontSize: "13px", fontWeight: 500, color: cT.color, background: cT.background }}
        >
          Clinical evidence
        </span>
        <span
          className="navlink"
          onClick={() => setState({ view: "figures" })}
          style={{ padding: "7px 13px", borderRadius: "7px", fontSize: "13px", fontWeight: 500, color: fT.color, background: fT.background }}
        >
          Figure atlas
        </span>
        <span
          className="navlink"
          onClick={() => setState({ view: "gallery" })}
          style={{ padding: "7px 13px", borderRadius: "7px", fontSize: "13px", fontWeight: 500, color: gT.color, background: gT.background }}
        >
          Gallery
        </span>
      </nav>

      <div style={{ flex: 1 }} />
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        {slGenes.length > 0 && (
          <span
            className="navlink"
            onClick={() => setState({ view: "compare" })}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "12.5px",
              fontWeight: 600,
              color: "#1a5fb4",
              background: "#eaf1fb",
              padding: "5px 11px",
              borderRadius: "20px",
            }}
          >
            Compare{" "}
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                minWidth: "17px",
                height: "17px",
                padding: "0 4px",
                borderRadius: "9px",
                background: "#1a5fb4",
                color: "#fff",
                fontSize: "10.5px",
              }}
            >
              {slGenes.length}
            </span>
          </span>
        )}
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "11px",
            fontWeight: 500,
            color: "#5b6270",
            fontFamily: "'IBM Plex Mono', monospace",
          }}
        >
          <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#0d7d5a" }} />
          {DATA_VERSION}
        </span>
        <span style={{ fontSize: "12px", color: "#c8ced7" }}>|</span>
        <span
          className="navlink"
          onClick={() => setState({ view: "docs" })}
          style={{ fontSize: "12.5px", fontWeight: 500, color: "#5b6270" }}
        >
          Docs
        </span>
        <span style={{ fontSize: "12px", color: "#c8ced7" }}>|</span>
        <span
          className="navlink"
          onClick={() => setState({ view: "apidocs" })}
          style={{ fontSize: "12.5px", fontWeight: 500, color: "#5b6270" }}
        >
          API docs
        </span>
        <span style={{ fontSize: "12px", color: "#c8ced7" }}>|</span>
        <span
          className="navlink"
          onClick={() => setState({ view: "deck" })}
          style={{ fontSize: "12.5px", fontWeight: 500, color: "#5b6270" }}
        >
          Overview
        </span>
        <span style={{ fontSize: "12px", color: "#c8ced7" }}>|</span>
        <span
          className="navlink"
          onClick={() => setState({ view: "provenance" })}
          style={{ fontSize: "12.5px", fontWeight: 500, color: "#5b6270" }}
        >
          Provenance
        </span>
      </div>
    </header>
  );
}
