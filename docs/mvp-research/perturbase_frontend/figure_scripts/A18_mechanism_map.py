"""
chart_id:        A18
source image:    mechanism_map.png
chart title:     Downstream Reactome pathway enrichment for 5 flagship perturbations
language:        Python
env name:        python
input-artifact version_ids (2):
  - ca1ccabf-a849-4eac-9225-be930d12a3a8  (part-000.parquet)
  - 3df56bd0-dcae-437c-8137-68c8e0308a40  (part-001.parquet)
packages referenced: matplotlib, numpy, os, pandas, requests, time
"""

import pandas as pd
import numpy as np
import requests
import time
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# skill:figure-style kernel.py (auto-injected on skill load)
META_GREY = "#888888"


def apply_figure_style(*, frame="open", font=None, sizes=(8, 7, 6), grid=False):
    import matplotlib as mpl
    if frame not in ("open", "boxed", "none"):
        raise ValueError(f"frame must be 'open'|'boxed'|'none', got {frame!r}")
    try:
        import os, sys, glob, matplotlib.font_manager as fm
        fdir = os.path.join(os.environ.get("CONDA_PREFIX") or sys.prefix, "fonts")
        if os.path.isdir(fdir):
            known = {f.fname for f in fm.fontManager.ttflist}
            for f in glob.glob(os.path.join(fdir, "*.ttf")):
                if f not in known:
                    fm.fontManager.addfont(f)
    except Exception:
        pass
    base, secondary, tick = sizes
    boxed = (frame == "boxed")
    rc = {
        "font.family": "sans-serif",
        "font.size": base,
        "axes.labelsize": base,
        "axes.titlesize": base,
        "legend.fontsize": secondary,
        "xtick.labelsize": tick,
        "ytick.labelsize": tick,
        "axes.linewidth": 0.6,
        "xtick.direction": "out", "ytick.direction": "out",
        "xtick.major.size": 3, "ytick.major.size": 3,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "axes.spines.top": boxed, "axes.spines.right": boxed,
        "axes.spines.left": frame != "none", "axes.spines.bottom": frame != "none",
        "axes.grid": bool(grid),
        "legend.frameon": False,
        "figure.dpi": 200,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.titleweight": "normal",
        "axes.titlelocation": "left",
        "axes.labelweight": "normal",
        "lines.linewidth": 1.2,
        "patch.linewidth": 0.6,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    }
    if font:
        rc["font.sans-serif"] = [font, "DejaVu Sans"]
    mpl.rcParams.update(rc)


# Load data
full = pd.concat([
    pd.read_parquet("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/ed0fef52-6322-4297-9044-fd821bd683f9/vca1ccabf_part-000.parquet"),
    pd.read_parquet("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/d3754585-a77d-4289-b4dd-7fc62ca84277/v3df56bd0_part-001.parquet")
], ignore_index=True)

flag = ["CD3E", "PLCG1", "VAV1", "STAT3", "BCL10"]
sub = full[full.target_gene.isin(flag)].copy()

agg = sub.groupby(["target_gene", "downstream_gene"])["log_fc"].mean().reset_index()
sets = {}
for g in flag:
    d = agg[agg.target_gene == g]
    up = sorted(d[d.log_fc > 0].downstream_gene.unique().tolist())
    dn = sorted(d[d.log_fc < 0].downstream_gene.unique().tolist())
    sets[g] = {"up": up, "down": dn}

URL = "https://reactome.org/AnalysisService/identifiers/projection"
params = {"interactors": "false", "pageSize": "15", "page": "1", "sortBy": "ENTITIES_FDR",
          "order": "ASC", "resource": "TOTAL", "pValue": "1"}
hdr = {"Content-Type": "text/plain"}
rows = []
for g in flag:
    for direction in ["up", "down"]:
        genes = sets[g][direction]
        body = "\n".join(genes)
        r = requests.post(URL, params=params, headers=hdr, data=body.encode())
        r.raise_for_status()
        js = r.json()
        paths = js.get("pathways", [])
        for p in paths:
            ent = p["entities"]
            rows.append({"flagship": g, "direction": direction, "pathway": p["name"],
                         "stId": p["stId"], "n_genes": ent["found"],
                         "p_value": ent["pValue"], "FDR": ent["fdr"], "source": "Reactome"})
        time.sleep(0.5)
enr = pd.DataFrame(rows)

apply_figure_style()

fig, axes = plt.subplots(1, 5, figsize=(24, 6.8), constrained_layout=True)
flags = ["CD3E", "PLCG1", "VAV1", "STAT3", "BCL10"]


def shorten(s, n=40):
    return s if len(s) <= n else s[:n - 1] + "\u2026"


for ax, g in zip(axes, flags):
    up = enr[(enr.flagship == g) & (enr.direction == "up")].nsmallest(5, "FDR")
    dn = enr[(enr.flagship == g) & (enr.direction == "down")].nsmallest(5, "FDR")
    d = pd.concat([up.assign(dir="up"), dn.assign(dir="down")])
    d["nlp"] = -np.log10(d["FDR"].clip(lower=1e-300))
    d = d.iloc[::-1]
    colors = ["#c0392b" if x == "up" else "#2471a3" for x in d["dir"]]
    y = np.arange(len(d))
    ax.barh(y, d["nlp"], color=colors)
    ax.set_yticks(y)
    ax.set_yticklabels([shorten(p) for p in d["pathway"]])
    ax.set_title(g, fontweight="bold")
    ax.set_xlabel("-log10 FDR")
    ax.axvline(-np.log10(0.05), ls="--", color="0.5", lw=1)
    ax.margins(y=0.02)

fig.legend(handles=[Patch(color="#c0392b", label="Downstream UP (log2FC > 0)"),
                    Patch(color="#2471a3", label="Downstream DOWN (log2FC < 0)")],
           loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.04))
fig.suptitle("Downstream Reactome pathway enrichment for 5 flagship perturbations (CD4+ T-cell Perturb-seq)",
             fontsize=14, fontweight="bold")
fig.savefig("mechanism_map.png", dpi=200, bbox_inches="tight")
