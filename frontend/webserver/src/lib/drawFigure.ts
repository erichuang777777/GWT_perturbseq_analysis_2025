import Plotly from "plotly.js-dist-min";
import { TARGETS } from "../data/dataset";
import { CLUSTER_COLORS, CLUSTER_MAP, clusterNames } from "../data/reference";
import type { AppState } from "../store/store";
import { clusterCenter, gauss, geneUniverse, hash, rng } from "./logic";

// Ported verbatim from the DC drawFigure() — deterministic, illustrative series.
export function drawFigure(el: HTMLElement, S: AppState) {
  const base = (extra?: Record<string, unknown>) =>
    Object.assign(
      {
        font: { family: "IBM Plex Sans, sans-serif", size: 12, color: "#3a414d" },
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
    const scale = ({ Rest: 1, Stim8hr: 1.5, Stim48hr: 1.9 } as Record<string, number>)[cond] || 1;
    const U = geneUniverse();
    const pts = U.map(({ gene }) => {
      const r = rng(hash(gene + cond));
      const x = gauss(r) * 0.72 * scale;
      const y = Math.max(0.02, Math.abs(x) * 1.55 + gauss(r) * 0.75 + 0.35);
      return { gene, x, y };
    });
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
      text: g.map((p) => p.gene),
      mode: "markers",
      type: "scatter",
      name,
      marker: { size: 7, color, opacity: 0.85, line: { width: 0.5, color: "#fff" } },
      hovertemplate: "<b>%{text}</b><br>log2FC %{x:.2f}<br>-log10 FDR %{y:.2f}<extra></extra>",
    });
    data = [tr(gns, "n.s.", "#c3c9d2"), tr(gneg, "Negative regulator", "#A8373A"), tr(gpos, "Positive regulator", "#2D6CBC")];
    layout = base({
      xaxis: { title: "Perturbation effect (log2 fold-change)", zeroline: false, gridcolor: "#eef0f3" },
      yaxis: { title: "-log10 FDR", gridcolor: "#eef0f3" },
      shapes: [
        { type: "line", x0: 0, x1: 0, yref: "paper", y0: 0, y1: 1, line: { color: "#e2e5ea", width: 1, dash: "dot" } },
        { type: "line", xref: "paper", x0: 0, x1: 1, y0: th, y1: th, line: { color: "#b7791f", width: 1, dash: "dash" } },
      ],
    });
  } else if (S.figureId === "umap") {
    const U = geneUniverse();
    const cmap = CLUSTER_COLORS;
    const mmap = CLUSTER_MAP;
    const hi = S.figCluster;
    const byC: Record<string, { gene: string; x: number; y: number }[]> = {};
    U.forEach(({ gene, module }) => {
      const c = mmap[module] || "Cell cycle";
      const r = rng(hash(gene + "umap"));
      const ctr = clusterCenter(c);
      const x = ctr[0] + gauss(r) * 0.95;
      const y = ctr[1] + gauss(r) * 0.95;
      (byC[c] = byC[c] || []).push({ gene, x, y });
    });
    data = Object.keys(byC).map((c) => ({
      x: byC[c].map((p) => p.x),
      y: byC[c].map((p) => p.y),
      text: byC[c].map((p) => p.gene),
      name: c,
      mode: "markers",
      type: "scatter",
      marker: { size: 8, color: cmap[c] || "#8a8f98", opacity: hi === "all" || hi === c ? 0.92 : 0.1, line: { width: 0.5, color: "#fff" } },
      hovertemplate: "<b>%{text}</b><br>" + c + "<extra></extra>",
    }));
    layout = base({ xaxis: { visible: false }, yaxis: { visible: false, scaleanchor: "x" }, legend: { font: { size: 10 }, orientation: "v" }, margin: { l: 12, r: 12, t: 12, b: 12 } });
  } else if (S.figureId === "heatmap") {
    const cond = S.figCondition;
    const rows = TARGETS.map((t) => t.gene);
    const cols = ["Th1", "Th2", "Th17", "Treg", "IL-2/STAT5", "IFN", "NF-κB", "Metabolic", "Cytotoxic", "Cell cycle"];
    const s = ({ Rest: 0.8, Stim8hr: 1.2, Stim48hr: 1.5 } as Record<string, number>)[cond] || 1;
    const z = rows.map((g) =>
      cols.map((c) => {
        const r = rng(hash(g + c + cond));
        return +(gauss(r) * 0.95 * s).toFixed(2);
      }),
    );
    data = [
      {
        z,
        x: cols,
        y: rows,
        type: "heatmap",
        colorscale: [
          [0, "#2369b0"],
          [0.5, "#f7f7f7"],
          [1, "#b0373a"],
        ],
        zmid: 0,
        zmin: -2.6,
        zmax: 2.6,
        colorbar: { title: { text: "effect", side: "right" }, thickness: 12, len: 0.7 },
        hovertemplate: "%{y} → %{x}<br>effect %{z:.2f}<extra></extra>",
      },
    ];
    layout = base({ margin: { l: 72, r: 20, t: 12, b: 74 }, xaxis: { tickangle: -35, side: "bottom" }, yaxis: { autorange: "reversed" } });
  } else if (S.figureId === "cytokine") {
    const ck = S.figCytokine;
    const U = geneUniverse();
    const arr = U.map(({ gene }) => {
      const r = rng(hash(gene + ck + "ck"));
      return { gene, v: +(gauss(r) * 1.25).toFixed(2) };
    });
    arr.sort((a, b) => b.v - a.v);
    const top = arr.slice(0, 9).concat(arr.slice(-9));
    top.sort((a, b) => a.v - b.v);
    data = [
      {
        x: top.map((d) => d.v),
        y: top.map((d) => d.gene),
        type: "bar",
        orientation: "h",
        marker: { color: top.map((d) => (d.v > 0 ? "#2D6CBC" : "#A8373A")) },
        hovertemplate: "<b>%{y}</b><br>effect on " + ck + ": %{x:.2f}<extra></extra>",
      },
    ];
    layout = base({ margin: { l: 84, r: 20, t: 12, b: 46 }, xaxis: { title: "Effect on " + ck + " (log2 fold-change)", zeroline: true, zerolinecolor: "#d6dbe3", gridcolor: "#eef0f3" }, yaxis: { automargin: true } });
  } else if (S.figureId === "polar") {
    const U = geneUniverse();
    const pts = U.map(({ gene }) => {
      const r = rng(hash(gene + "th"));
      const pol = gauss(r) * 0.5;
      const mag = Math.abs(pol) * 1.25 + Math.abs(gauss(r)) * 0.45;
      return { gene, x: pol, y: mag };
    });
    data = [
      {
        x: pts.map((p) => p.x),
        y: pts.map((p) => p.y),
        text: pts.map((p) => p.gene),
        mode: "markers",
        type: "scatter",
        marker: { size: 8, color: pts.map((p) => (p.x > 0 ? "#ff7f00" : "#1f78b4")), opacity: 0.85, line: { width: 0.5, color: "#fff" } },
        hovertemplate: "<b>%{text}</b><br>polarization %{x:.2f}<br>magnitude %{y:.2f}<extra></extra>",
      },
    ];
    layout = base({ xaxis: { title: "← Th1        polarization score        Th2 →", zeroline: true, zerolinecolor: "#d6dbe3", gridcolor: "#eef0f3" }, yaxis: { title: "Effect magnitude", gridcolor: "#eef0f3" } });
  } else if (S.figureId === "gwas") {
    const dis = S.figDisease;
    const clusters = clusterNames();
    const vals = clusters.map((c) => {
      const r = rng(hash(c + dis + "gwas"));
      return +(Math.abs(gauss(r)) * 2 + r() * 1.6).toFixed(2);
    });
    data = [
      {
        x: clusters,
        y: vals,
        type: "bar",
        marker: { color: vals.map((v) => (v > 2 ? "#A8373A" : "#2D6CBC")) },
        hovertemplate: "<b>%{x}</b><br>-log10 P %{y:.2f}<extra></extra>",
      },
    ];
    layout = base({ margin: { l: 58, r: 20, t: 12, b: 120 }, xaxis: { tickangle: -35 }, yaxis: { title: "GWAS enrichment (-log10 P)", gridcolor: "#eef0f3" }, shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: 2, y1: 2, line: { color: "#b7791f", width: 1, dash: "dash" } }] });
  } else if (S.figureId === "power") {
    const cells: number[] = [];
    for (let c = 20; c <= 520; c += 20) cells.push(c);
    const effects = [0.25, 0.5, 1.0];
    const colors = ["#b6de2b", "#1f9d8a", "#31678e"];
    data = effects.map((e, i) => ({
      x: cells,
      y: cells.map((n) => {
        const p = 1 / (1 + Math.exp(-((n * e * e) / 55 - 2)));
        return +p.toFixed(3);
      }),
      mode: "lines",
      name: "|log2FC| = " + e.toFixed(2),
      line: { color: colors[i], width: 2.6 },
      hovertemplate: "%{x} cells<br>power %{y:.2f}<extra></extra>",
    }));
    layout = base({ xaxis: { title: "Cells per perturbation", gridcolor: "#eef0f3" }, yaxis: { title: "Detection power", range: [0, 1.03], gridcolor: "#eef0f3" }, shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: 0.8, y1: 0.8, line: { color: "#b7791f", width: 1, dash: "dash" } }] });
  } else if (S.figureId === "burden") {
    const trait = S.figTrait;
    const U = geneUniverse().slice(0, 64);
    const pts = U.map(({ gene }) => {
      const r = rng(hash(gene + trait + "burden"));
      const x = gauss(r);
      const y = x * 0.6 + gauss(r) * 0.6;
      return { gene, x, y };
    });
    const xs = pts.map((p) => p.x);
    const ys = pts.map((p) => p.y);
    const mx = xs.reduce((a, b) => a + b, 0) / xs.length;
    const my = ys.reduce((a, b) => a + b, 0) / ys.length;
    let numr = 0;
    let den = 0;
    xs.forEach((x, i) => {
      numr += (x - mx) * (ys[i] - my);
      den += (x - mx) * (x - mx);
    });
    const slope = numr / den;
    const intc = my - slope * mx;
    const xr = [Math.min.apply(null, xs), Math.max.apply(null, xs)];
    data = [
      {
        x: xs,
        y: ys,
        text: pts.map((p) => p.gene),
        mode: "markers",
        type: "scatter",
        name: "gene",
        marker: { size: 7, color: "#6baed6", opacity: 0.85, line: { width: 0.5, color: "#fff" } },
        hovertemplate: "<b>%{text}</b><br>perturb effect %{x:.2f}<br>LoF burden β %{y:.2f}<extra></extra>",
      },
      { x: xr, y: xr.map((x) => slope * x + intc), mode: "lines", name: "linear fit", line: { color: "#A8373A", width: 2 }, hoverinfo: "skip" },
    ];
    layout = base({ xaxis: { title: "Perturbation effect on " + trait + " signature", zeroline: true, zerolinecolor: "#d6dbe3", gridcolor: "#eef0f3" }, yaxis: { title: "LoF burden association (β)", zeroline: true, zerolinecolor: "#d6dbe3", gridcolor: "#eef0f3" } });
  }
  Plotly.react(el, data, layout, cfg);
}
