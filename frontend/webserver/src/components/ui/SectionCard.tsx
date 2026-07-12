// The bordered, rounded "panel" shell repeated ~10x per dossier-style view
// (Dossier, Clinical, Provenance): a heading, an optional right-aligned
// source stamp, and content. Doesn't own the content's internal layout.
export default function SectionCard({
  title,
  source,
  variant = "default",
  children,
}: {
  title?: React.ReactNode;
  source?: React.ReactNode;
  variant?: "default" | "muted";
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        border: "1px solid #e2e5ea",
        borderRadius: "14px",
        padding: "22px",
        background: variant === "muted" ? "#fafbfc" : undefined,
      }}
    >
      {(title || source) && (
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", gap: "12px" }}>
          {title && <h3 style={{ fontSize: "15px", fontWeight: 700, margin: 0 }}>{title}</h3>}
          {source && <span style={{ fontSize: "10.5px", color: "#9aa1ad", fontFamily: "'IBM Plex Mono', monospace" }}>{source}</span>}
        </div>
      )}
      {children}
    </div>
  );
}

// The "unknown / no data indexed" empty-state box used across every
// evidence panel -- honest missing-data messaging, never a fabricated zero.
export function UnknownNotice({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        fontSize: "12.5px",
        color: "#7a6a3f",
        background: "#fbf9f2",
        border: "1px solid #eddfc0",
        borderRadius: "9px",
        padding: "11px 14px",
        fontFamily: "'IBM Plex Mono', monospace",
      }}
    >
      {children}
    </div>
  );
}
