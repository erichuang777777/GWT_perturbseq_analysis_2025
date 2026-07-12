// A label+value metric tile. Covers the Home stats grid, Dossier's
// statistical-evidence grid, and structure/figure metric readouts.
export default function StatTile({
  label,
  value,
  color = "#1a1d24",
  mono = false,
  size = "md",
}: {
  label: React.ReactNode;
  value: React.ReactNode;
  color?: string;
  mono?: boolean;
  size?: "sm" | "md" | "lg";
}) {
  const valueSize = size === "lg" ? "28px" : size === "sm" ? "15px" : "20px";
  return (
    <div>
      <div
        style={{
          fontSize: valueSize,
          fontWeight: 700,
          letterSpacing: "-.5px",
          color,
          fontFamily: mono ? "'IBM Plex Mono', monospace" : undefined,
        }}
      >
        {value}
      </div>
      <div style={{ fontSize: size === "sm" ? "11px" : "12.5px", color: "#6b7280", marginTop: "2px", fontWeight: size === "lg" ? 500 : 400 }}>{label}</div>
    </div>
  );
}
