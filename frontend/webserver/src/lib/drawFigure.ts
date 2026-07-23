import Plotly from "plotly.js-dist-min";
import { TARGETS } from "../data/dataset";
import { FIGURES_DATA } from "../data/figuresData";
import type { AppState } from "../store/store";

// Renders each figure-atlas panel from real pipeline output (figures.json)
// and the real dataset (real-dataset.json, via TARGETS) — see Figures.tsx's
// caption for provenance per figure. No synthetic/deterministic-random data.
export function drawFigure(el: HTMLElement, S: AppState) {
  if (S.figureId === "umap") {
    // No 2D embedding coordinates ship with this repo's pipeline outputs —
    // rendering a scatter here would mean fabricating positions. Figures.tsx
    // shows an honest "unavailable" panel instead of this chart div.
    Plotly.purge(el);
    return;
  }

  const base = (extra?: Record<string, unknown>) =>
    Object.assign(
      {
        font: { family: "IBM Plex Mono, ui-monospace, monospace", size: 12, color: "#3a414d" },
        paper_bgcolor: "#fff",
        plot_bgcolor: "#fff",
        margin: { l: 62, r: 20, t: 12, b: 54 },
        hovermode: "closest",
        legend: { font: { size: 11 } },
      },
      extra || {},
    );
  const cfg = {
    responsive: true,
    displaylogo: false,
    modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines", "zoomIn2d", "zoomOut2d"],
  };
  let data: unknown[] = [];
  let layout: Record<string, unknown> = {};

  if (S.figureId === "volcano") {
    const cond = S.figCondition;
    const th = S.figThresh;
    const pts = FIGURES_DATA.volcano[cond] || [];
    const gpos: typeof pts = [];
    const gneg: typeof pts = [];
    const gns: typeof pts = [];
    pts.forEach((p) => {
      if (p.y < th) gns.push(p);
      else if (p.x > 0) gpos.push(p);
      else gneg.push(p);
    });
    const tr = (g: typeof pts, name: string, color: string) => ({
      x: g.map((p) => p.x),
      y: g.map((p) => p.y),
      text: g.map((p) => p.g),
      mode: "markers",
      type: "scatter",
      name,
      marker: { size: 7, color, opacity: 0.85, line: { width: 0.5, color: "#fff" } },
      hovertemplate: "<b>%{text}</b><br>log2FC %{x:.2f}<br>-log10 FDR %{y:.2f}<extra></extra>",
    });
    data = [tr(gns, "n.s.", "#c3c9d2"), tr(gneg, "Negative regulator", "#A8373A"), tr(gpos, "Positive regulator", "#2D6CBC")];
    layout = base({
      xaxis: { title: "On-target knockdown effect (log2 fold-change)", zeroline: false, gridcolor: "#eef0f3" },
      yaxis: { title: "-log10 FDR", gridcolor: "#eef0f3" },
      shapes: [
        { type: "line", x0: 0, x1: 0, yref: "paper", y0: 0, y1: 1, line: { color: "#e2e5ea", width: 1, dash: "dot" } },
        { type: "line", xref: "paper", x0: 0, x1: 1, y0: th, y1: th, line: { color: "#b7791f", width: 1, dash: "dash" } },
      ],
    });
  } else if (S.figureId === "heatmap") {
    const h = FIGURES_DATA.heatmap;
    const zmax = h.z.length ? Math.max(...h.z.map((row) => Math.max(...row))) : 0.9;
    data = [
      {
        z: h.z,
        x: h.cols,
        y: h.rows.map((r) => r.label),
        type: "heatmap",
        colorscale: [
          [0, "#f7f7fb"],
          [0.5, "#b6a8e0"],
          [1, "#5b3fb4"],
        ],
        zmin: 0,
        zmax,
        colorbar: { title: { text: "intra-cluster corr", side: "right" }, thickness: 12, len: 0.7 },
        hovertemplate: "%{y} · %{x}<br>corr %{z:.2f}<extra></extra>",
      },
    ];
    layout = base({
      margin: { l: 200, r: 20, t: 12, b: 74 },
      xaxis: { tickangle: -35, side: "bottom" },
      yaxis: { automargin: true, tickfont: { size: 8 } },
      height: Math.max(462, h.rows.length * 9),
    });
  } else if (S.figureId === "cytokine") {
    const ck = S.figCytokine;
    const arr = FIGURES_DATA.cytokine[ck] || [];
    data = [
      {
        x: arr.map((d) => d.x),
        y: arr.map((d) => d.g),
        type: "bar",
        orientation: "h",
        marker: { color: arr.map((d) => (d.x > 0 ? "#2D6CBC" : "#A8373A")) },
        hovertemplate: "<b>%{y}</b><br>effect on " + ck + ": %{x:.2f}<extra></extra>",
      },
    ];
    layout = base({ margin: { l: 84, r: 20, t: 12, b: 46 }, xaxis: { title: "Effect on " + ck + " (log2 fold-change)", zeroline: true, zerolinecolor: "#d6dbe3", gridcolor: "#eef0f3" }, yaxis: { automargin: true } });
  } else if (S.figureId === "polar") {
    const pts = FIGURES_DATA.polar;
    data = [
      {
        x: pts.map((p) => p.x),
        y: pts.map((p) => p.y),
        text: pts.map((p) => p.g),
        mode: "markers",
        type: "scatter",
        marker: { size: 8, color: pts.map((p) => (p.x > 0 ? "#ff7f00" : "#1f78b4")), opacity: 0.85, line: { width: 0.5, color: "#fff" } },
        hovertemplate: "<b>%{text}</b><br>polarization %{x:.4f}<br>magnitude %{y:.4f}<extra></extra>",
      },
    ];
    layout = base({ xaxis: { title: "← Th1    polarization coefficient (Th2 − Th1)    Th2 →", zeroline: true, zerolinecolor: "#d6dbe3", gridcolor: "#eef0f3" }, yaxis: { title: "Effect magnitude", gridcolor: "#eef0f3" } });
  } else if (S.figureId === "gwas") {
    const dis = S.figDisease;
    const arr = FIGURES_DATA.gwas[dis] || [];
    data = [
      {
        x: arr.map((d) => d.cluster),
        y: arr.map((d) => d.y),
        type: "bar",
        marker: { color: arr.map((d) => (d.y > 1.3 ? "#A8373A" : "#2D6CBC")) },
        hovertemplate: "cluster %{x}<br>-log10 P %{y:.2f}<extra></extra>",
      },
    ];
    layout = base({
      margin: { l: 58, r: 20, t: 12, b: 90 },
      xaxis: { title: "Regulator cluster", tickangle: -35 },
      yaxis: { title: "GWAS enrichment (-log10 P)", gridcolor: "#eef0f3" },
      shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: 1.3, y1: 1.3, line: { color: "#b7791f", width: 1, dash: "dash" } }],
    });
  } else if (S.figureId === "power") {
    const depths = [...FIGURES_DATA.depths].sort((a, b) => a - b);
    const colors = ["#b6de2b", "#1f9d8a", "#31678e"];
    data = depths.map((d, i) => {
      const points = FIGURES_DATA.power[String(d)] || [];
      return {
        x: points.map((p) => p.n_cells),
        y: points.map((p) => p.corr),
        mode: "lines",
        name: `depth ${d}%`,
        line: { color: colors[i % colors.length], width: 2.6 },
        hovertemplate: "%{x} cells<br>corr %{y:.3f}<extra></extra>",
      };
    });
    layout = base({ xaxis: { title: "Cells per perturbation", gridcolor: "#eef0f3" }, yaxis: { title: "Held-out replication correlation", range: [-0.1, 1], gridcolor: "#eef0f3" } });
  } else if (S.figureId === "burden") {
    // Only "lymphocyte_count" has a resolved UK Biobank LoF-burden trait in
    // this repo (evidence/population.py) -- so there is nothing to switch
    // between; the panel always renders that one real trait.
    const pts = TARGETS.filter((t) => t.populationBurden && t.populationBurden.effectEstimate != null && t.effect != null).map((t) => ({
      g: t.gene,
      x: t.effect as number,
      y: t.populationBurden!.effectEstimate as number,
    }));
    const xs = pts.map((p) => p.x);
    const ys = pts.map((p) => p.y);
    const mx = xs.reduce((a, b) => a + b, 0) / (xs.length || 1);
    const my = ys.reduce((a, b) => a + b, 0) / (ys.length || 1);
    let numr = 0;
    let den = 0;
    xs.forEach((x, i) => {
      numr += (x - mx) * (ys[i] - my);
      den += (x - mx) * (x - mx);
    });
    const slope = den ? numr / den : 0;
    const intc = my - slope * mx;
    const xr = xs.length ? [Math.min.apply(null, xs), Math.max.apply(null, xs)] : [0, 0];
    data = [
      {
        x: xs,
        y: ys,
        text: pts.map((p) => p.g),
        mode: "markers",
        type: "scatter",
        name: "gene",
        marker: { size: 7, color: "#6baed6", opacity: 0.85, line: { width: 0.5, color: "#fff" } },
        hovertemplate: "<b>%{text}</b><br>perturb effect %{x:.2f}<br>LoF burden β %{y:.3f}<extra></extra>",
      },
      { x: xr, y: xr.map((x) => slope * x + intc), mode: "lines", name: "linear fit", line: { color: "#A8373A", width: 2 }, hoverinfo: "skip" },
    ];
    layout = base({ xaxis: { title: "Perturbation effect (|log2FC|)", zeroline: true, zerolinecolor: "#d6dbe3", gridcolor: "#eef0f3" }, yaxis: { title: "Lymphocyte-count LoF-burden β (UK Biobank)", zeroline: true, zerolinecolor: "#d6dbe3", gridcolor: "#eef0f3" } });
  } else if (S.figureId === "noveltyEffect") {
    // Novelty × effect quadrant (plan P1-F). Real TARGETS only; a point exists
    // only where BOTH a perturbation effect and a measured PubMed novelty are
    // present — genes without a literature count are honestly absent, never
    // plotted at zero (unknown != 0). Upper-right = strong effect + understudied.
    const pts = TARGETS.filter((t) => t.novelty && t.novelty.noveltyScore != null && t.effect != null).map((t) => ({
      g: t.gene,
      x: t.effect as number,
      y: t.novelty!.noveltyScore as number,
      tier: t.novelty!.tier,
      call: t.readiness?.call || "unreviewed",
    }));
    const CALL_COLOR: Record<string, string> = { advance: "#1a7f5a", validate: "#2563a8", watchlist: "#b8860b", deprioritize: "#9aa1ad", unreviewed: "#c0c6cf" };
    const xs = pts.map((p) => p.x);
    const medX = xs.length ? [...xs].sort((a, b) => a - b)[Math.floor(xs.length / 2)] : 0;
    const maxX = xs.length ? Math.max.apply(null, xs) : 1;
    data = [
      {
        x: xs,
        y: pts.map((p) => p.y),
        text: pts.map((p) => `${p.g} · ${p.tier} · ${p.call}`),
        mode: "markers",
        type: "scatter",
        name: "gene",
        marker: { size: 9, color: pts.map((p) => CALL_COLOR[p.call] || "#c0c6cf"), opacity: 0.85, line: { width: 0.5, color: "#fff" } },
        hovertemplate: "<b>%{text}</b><br>effect %{x:.2f}<br>novelty %{y:.2f} (higher = fewer papers)<extra></extra>",
      },
    ];
    layout = base({
      xaxis: { title: "Perturbation effect (|log2FC|)", zeroline: false, gridcolor: "#eef0f3" },
      yaxis: { title: "PubMed novelty (higher = fewer papers)", range: [0, 1.02], gridcolor: "#eef0f3" },
      shapes: [
        { type: "line", x0: medX, x1: medX, y0: 0, y1: 1.02, line: { color: "#d6dbe3", width: 1, dash: "dot" } },
        { type: "line", x0: 0, x1: maxX, y0: 0.5, y1: 0.5, line: { color: "#d6dbe3", width: 1, dash: "dot" } },
      ],
      annotations: [
        { x: maxX, y: 1.0, xanchor: "right", yanchor: "top", showarrow: false, text: "strong effect · understudied", font: { size: 10, color: "#7c3aed" } },
      ],
    });
  }
  Plotly.react(el, data, layout, cfg);
}
