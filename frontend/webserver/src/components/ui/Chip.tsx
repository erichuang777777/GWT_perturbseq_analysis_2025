// A filter/facet toggle pill (family filters in Gallery, tag filters
// elsewhere). Distinct from Badge: Chip is always interactive and has an
// explicit active/inactive visual state; Badge is a passive label.
const ACCENT = "#5b3fb4";

export default function Chip({ label, active, onClick, accent = ACCENT }: { label: React.ReactNode; active: boolean; onClick: () => void; accent?: string }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: "6px 13px",
        border: `1px solid ${active ? accent : "#d6dbe3"}`,
        borderRadius: "20px",
        cursor: "pointer",
        fontSize: "12.5px",
        fontWeight: 500,
        background: active ? `${accent}18` : "#fff",
        color: active ? accent : "#5b6270",
      }}
    >
      {label}
    </button>
  );
}
