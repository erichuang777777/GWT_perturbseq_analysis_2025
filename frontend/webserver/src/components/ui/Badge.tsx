// A small colored pill used everywhere a status/category/score needs a label
// (readiness call, grade, vote status, constraint tier, pLDDT confidence).
// Replaces ~15 hand-rolled copies of the same inline style object.
export interface BadgeProps {
  label: React.ReactNode;
  color: string;
  bg: string;
  dot?: string;
  size?: "sm" | "md";
  onClick?: () => void;
  title?: string;
}

export default function Badge({ label, color, bg, dot, size = "md", onClick, title }: BadgeProps) {
  const pad = size === "sm" ? "2px 8px" : "5px 12px";
  const fontSize = size === "sm" ? "10.5px" : "12.5px";
  return (
    <span
      onClick={onClick}
      title={title}
      className={onClick ? "navlink" : undefined}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: dot ? "6px" : 0,
        padding: pad,
        borderRadius: "20px",
        fontSize,
        fontWeight: 600,
        color,
        background: bg,
        cursor: onClick ? "pointer" : undefined,
      }}
    >
      {dot && <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: dot }} />}
      {label}
    </span>
  );
}
