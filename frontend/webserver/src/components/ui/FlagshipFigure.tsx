// A framed, captioned real-data flagship figure (a static PNG rendered by the
// pipeline into public/flagship/). Every embed carries a caption and an
// explicit source line so a reader always knows the figure is real, computed
// output — not decoration. Optional onClick makes the whole card a click-through
// (e.g. to the interactive figure atlas).

export default function FlagshipFigure({
  src,
  alt,
  title,
  caption,
  source,
  onClick,
  cta,
  footnote,
  maxHeight = 520,
}: {
  src: string;
  alt: string;
  title?: string;
  caption: string;
  source: string;
  onClick?: () => void;
  cta?: string;
  footnote?: React.ReactNode;
  maxHeight?: number;
}) {
  const clickable = typeof onClick === "function";
  return (
    <figure
      className={clickable ? "lift" : undefined}
      onClick={onClick}
      style={{
        margin: 0,
        border: "1px solid #e2e5ea",
        borderRadius: "14px",
        overflow: "hidden",
        background: "#fff",
        cursor: clickable ? "pointer" : "default",
      }}
    >
      {title && (
        <div style={{ padding: "16px 20px 0", fontSize: "15px", fontWeight: 700, letterSpacing: "-.2px", color: "#1a1d24" }}>{title}</div>
      )}
      <div style={{ padding: "14px 20px" }}>
        <img
          src={src}
          alt={alt}
          loading="lazy"
          style={{ display: "block", width: "100%", height: "auto", maxHeight: `${maxHeight}px`, objectFit: "contain", borderRadius: "8px" }}
        />
      </div>
      <figcaption style={{ padding: "0 20px 16px", minWidth: 0 }}>
        <div style={{ fontSize: "13px", lineHeight: 1.55, color: "#4a515e" }}>{caption}</div>
        {footnote && (
          <div style={{ fontSize: "11.5px", lineHeight: 1.5, color: "#7a6a3f", background: "#fbf9f2", border: "1px solid #eddfc0", borderRadius: "8px", padding: "8px 11px", marginTop: "10px" }}>{footnote}</div>
        )}
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: "12px", flexWrap: "wrap", marginTop: "10px" }}>
          <div style={{ fontSize: "11px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace", wordBreak: "break-word", minWidth: 0 }}>Source: {source}</div>
          {clickable && cta && <div style={{ fontSize: "12.5px", fontWeight: 600, color: "#5b3fb4", whiteSpace: "nowrap" }}>{cta} →</div>}
        </div>
      </figcaption>
    </figure>
  );
}
