"""
Standalone figure-generating script.

chart_id            : N1
source image        : N1_string.png
chart title         : STRING
language            : Python
conda env name      : python
input artifact vids : ['e168ccb9-6d5d-427c-a5cf-93f388492f2f']
referenced packages : matplotlib, numpy, os, pandas

Extracted verbatim from artifact lineage (host.lineage['dc159141-611d-4867-bab6-676720839471']).
Edit this single file to tweak the figure, then re-run in the 'python' environment.
"""

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


import pandas as pd
import numpy as np
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

apply_figure_style(sizes=(8, 7, 6))
os.makedirs('out', exist_ok=True)

effect = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/34e69736-d190-40d4-853c-90e059c0d7b9/ve168ccb9_effect_matrix.csv", index_col=0)

COND = ['Rest', 'Stim8hr', 'Stim48hr']
CCOL = {'Rest': '#4C72B0', 'Stim8hr': '#DD8452', 'Stim48hr': '#8172B3'}


def zh(size=None, weight=None):
    fp = FontProperties(family='DejaVu Sans')
    if size: fp.set_size(size)
    if weight: fp.set_weight(weight)
    return fp


def ital(s): return f"$\\it{{{s}}}$"


edges = [
    ('CD3E', 'CD3D'), ('CD3E', 'CD3G'), ('CD3E', 'CD247'), ('CD3D', 'CD3G'), ('CD3G', 'CD247'),
    ('CD3E', 'LCK'), ('LCK', 'ZAP70'), ('ZAP70', 'LAT'), ('LAT', 'PLCG1'), ('LAT', 'VAV1'),
    ('LAT', 'LCP2'), ('PLCG1', 'VAV1'), ('VAV1', 'LCP2'), ('CD247', 'ZAP70'), ('LAT', 'ZAP70'),
    ('PLCG1', 'LCP2'), ('LCK', 'CD3E'),
    # SAGA/transcription module
    ('TADA1', 'TADA2B'), ('TADA2B', 'SGF29'), ('TADA1', 'SGF29'), ('SGF29', 'SUPT20H'),
    ('TADA1', 'SUPT20H'), ('TADA2B', 'SUPT20H'),
    # Mediator
    ('MED12', 'CCNC'),
]
nodes = sorted(set([n for e in edges for n in e]))

tcr = {'CD3E', 'CD3D', 'CD3G', 'CD247', 'LCK', 'ZAP70', 'LAT', 'PLCG1', 'VAV1', 'LCP2'}
saga = {'TADA1', 'TADA2B', 'SGF29', 'SUPT20H'}
med = {'MED12', 'CCNC'}


def mod(n): return 'TCR' if n in tcr else ('SAGA' if n in saga else 'MED')


MODCOL = {'TCR': CCOL['Rest'], 'SAGA': CCOL['Stim8hr'], 'MED': CCOL['Stim48hr']}

node_eff = {}
for gn in nodes:
    if gn in effect.index:
        node_eff[gn] = abs(effect.loc[gn, COND].mean())
    else:
        node_eff[gn] = np.nan

centers = {'TCR': np.array([-1.35, 0.0]), 'SAGA': np.array([1.15, 0.75]), 'MED': np.array([1.15, -0.95])}
radii = {'TCR': 0.95, 'SAGA': 0.55, 'MED': 0.30}
pos = {}
for m_ in centers:
    members = sorted([n for n in nodes if mod(n) == m_])
    k = len(members)
    for i, gn in enumerate(members):
        ang = 2 * np.pi * i / k + (0.4 if m_ == 'TCR' else 0)
        pos[gn] = centers[m_] + radii[m_] * np.array([np.cos(ang), np.sin(ang)])

fig, ax = plt.subplots(figsize=(8.4, 6.0))
for u, vv in edges:
    ax.plot([pos[u][0], pos[vv][0]], [pos[u][1], pos[vv][1]], color='#C9C9C9', lw=0.9, zorder=1)
for gn in nodes:
    e = node_eff[gn]
    sz = 110 + (e if not np.isnan(e) else 8) * 15
    ax.scatter(*pos[gn], s=sz, color=MODCOL[mod(gn)], edgecolor='white', lw=1.1, zorder=3, alpha=0.93)
for gn in nodes:
    cen = centers[mod(gn)]
    v = pos[gn] - cen
    v = v / (np.linalg.norm(v) + 1e-9)
    off = v * 13
    ha = 'left' if v[0] > 0.3 else ('right' if v[0] < -0.3 else 'center')
    ax.annotate(ital(gn), pos[gn], xytext=(off[0], off[1]), textcoords='offset points',
                ha=ha, va='center', fontsize=6.6, color='#222', zorder=5)
for m_, lab in [('TCR', 'TCR proximal signaling'), ('SAGA', 'SAGA complex'), ('MED', 'Mediator (CDK)')]:
    c = centers[m_]
    ax.text(c[0], c[1] + radii[m_] + 0.42, lab, ha='center', fontproperties=zh(8.5), color=MODCOL[m_])
ax.set_title("Shortlist targets fall into three known functional modules: TCR proximal signaling, SAGA, Mediator",
             fontproperties=zh(10.5), pad=8)
ax.axis('off')
ax.set_xlim(-2.5, 1.9)
ax.set_ylim(-1.6, 1.7)
ax.text(0.5, -0.02, "Node size \u221d |mean on-target effect| (three conditions); edges are known protein interactions (STRING/literature)",
        transform=ax.transAxes, ha='center', fontproperties=zh(6.8), color='#666')
fig.savefig('N1_string.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
