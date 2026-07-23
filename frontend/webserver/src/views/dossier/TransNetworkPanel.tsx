import type { RealTarget } from "../../data/types";
import SectionCard from "../../components/ui/SectionCard";

// Interactive causal ego-network (plan P3-I). Dependency-free inline SVG (the
// static portal has no CDN access) — the target at the center, its strongest
// downstream genes on a ring, edges colored by direction (red = rises on
// knockdown, blue = falls). Descriptive: the KD -> DEG edges are from the
// in-repo signed DE table, not a learned causal-network inference.
export default function TransNetworkPanel({ t }: { t: RealTarget }) {
  const edges = t.transNeighborhood;
  if (!edges || edges.length === 0) return null;

  const W = 460;
  const H = 300;
  const cx = W / 2;
  const cy = H / 2;
  const R = 108;
  const n = edges.length;
  const maxAbs = Math.max(...edges.map((e) => Math.abs(e.log_fc)), 0.001);

  return (
    <SectionCard title="Trans-effect neighborhood" source="src: full_signed_DE (KD → DEG edges, descriptive)">
      <div style={{ fontSize: "12px", color: "#6b7280", marginBottom: "8px" }}>
        The {n} strongest downstream genes knocking <b>{t.gene}</b> down moves — red rises on knockdown, blue falls.
        Not a learned causal network; the edges are this repo's own signed DE.
      </div>
      <div style={{ overflowX: "auto" }}>
        <svg width={W} height={H} role="img" aria-label={`${t.gene} trans-effect neighborhood`} style={{ maxWidth: "100%" }}>
          {edges.map((e, i) => {
            const ang = (2 * Math.PI * i) / n - Math.PI / 2;
            const x = cx + R * Math.cos(ang);
            const y = cy + R * Math.sin(ang);
            const color = e.direction === "up" ? "#c0504d" : "#3f6fb0";
            const width = 1 + 3 * (Math.abs(e.log_fc) / maxAbs);
            return (
              <g key={e.downstream_gene}>
                <line x1={cx} y1={cy} x2={x} y2={y} stroke={color} strokeWidth={width} strokeOpacity={0.55} />
                <circle cx={x} cy={y} r={4.5} fill={color} />
                <text x={x} y={y} dy={y < cy ? -8 : 15} textAnchor="middle" fontSize={10} fill="#4a515e" fontFamily="'IBM Plex Mono', monospace">
                  {e.downstream_gene}
                </text>
              </g>
            );
          })}
          <circle cx={cx} cy={cy} r={26} fill="#1a1d24" />
          <text x={cx} y={cy} dy={4} textAnchor="middle" fontSize={11} fontWeight={700} fill="#fff" fontFamily="'IBM Plex Mono', monospace">
            {t.gene}
          </text>
        </svg>
      </div>
      <div style={{ fontSize: "11px", color: "#9aa1ad", marginTop: "6px" }}>
        Broad neighborhood = broader downstream footprint = higher potential for pleiotropic effects.
      </div>
    </SectionCard>
  );
}
