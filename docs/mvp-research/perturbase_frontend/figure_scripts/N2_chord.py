"""
Standalone figure-generating script.

chart_id            : N2
source image        : N2_chord.png
chart title         : Chord
language            : Python
conda env name      : python
input artifact vids : ['e168ccb9-6d5d-427c-a5cf-93f388492f2f']
referenced packages : matplotlib, os, pandas

Extracted verbatim from artifact lineage (host.lineage['96b6076d-dc97-49bc-99d7-3a2e78c528dd']).
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


import pandas as pd, numpy as np, os
import matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.path import Path
import matplotlib.patches as patches

apply_figure_style(sizes=(8,7,6))
os.makedirs('out', exist_ok=True)

effect = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/34e69736-d190-40d4-853c-90e059c0d7b9/ve168ccb9_effect_matrix.csv", index_col=0)

COND = ['Rest','Stim8hr','Stim48hr']
CCOL = {'Rest':'#4C72B0','Stim8hr':'#DD8452','Stim48hr':'#8172B3'}

edges = [
    ('CD3E','CD3D'),('CD3E','CD3G'),('CD3E','CD247'),('CD3D','CD3G'),('CD3G','CD247'),
    ('CD3E','LCK'),('LCK','ZAP70'),('ZAP70','LAT'),('LAT','PLCG1'),('LAT','VAV1'),
    ('LAT','LCP2'),('PLCG1','VAV1'),('VAV1','LCP2'),('CD247','ZAP70'),('LAT','ZAP70'),
    ('PLCG1','LCP2'),('LCK','CD3E'),
    # SAGA/transcription module
    ('TADA1','TADA2B'),('TADA2B','SGF29'),('TADA1','SGF29'),('SGF29','SUPT20H'),
    ('TADA1','SUPT20H'),('TADA2B','SUPT20H'),
    # Mediator
    ('MED12','CCNC'),
]
nodes = sorted(set([n for e in edges for n in e]))
tcr = {'CD3E','CD3D','CD3G','CD247','LCK','ZAP70','LAT','PLCG1','VAV1','LCP2'}
saga = {'TADA1','TADA2B','SGF29','SUPT20H'}
med = {'MED12','CCNC'}
def mod(n): return 'TCR' if n in tcr else ('SAGA' if n in saga else 'MED')
MODCOL={'TCR':CCOL['Rest'],'SAGA':CCOL['Stim8hr'],'MED':CCOL['Stim48hr']}
node_eff = {}
for gn in nodes:
    if gn in effect.index:
        node_eff[gn] = abs(effect.loc[gn,COND].mean())
    else:
        node_eff[gn]=np.nan

order = [n for m_ in ['TCR','SAGA','MED'] for n in sorted([x for x in nodes if mod(x)==m_])]
N=len(order); ang={gn: 2*np.pi*i/N + np.pi/2 for i,gn in enumerate(order)}
R=1.0
cpos={gn: R*np.array([np.cos(ang[gn]), np.sin(ang[gn])]) for gn in order}

def zh(size=None, weight=None):
    fp = FontProperties(family='DejaVu Sans')
    if size: fp.set_size(size)
    if weight: fp.set_weight(weight)
    return fp

fig, ax = plt.subplots(figsize=(6.8,6.8))
for u,vv in edges:
    p0=cpos[u]; p2=cpos[vv]; ctrl=0.15*(p0+p2)
    ax.add_patch(patches.PathPatch(Path([p0,ctrl,p2],[Path.MOVETO,Path.CURVE3,Path.CURVE3]),
                 fc='none', ec=MODCOL[mod(u)], lw=1.0, alpha=0.55, zorder=1))
for gn in order:
    e=node_eff[gn]; sz=90+(e if not np.isnan(e) else 8)*13
    ax.scatter(*cpos[gn], s=sz, color=MODCOL[mod(gn)], edgecolor='white', lw=1.0, zorder=3)
    a=ang[gn]; lx,ly=1.16*np.cos(a),1.16*np.sin(a); rot=np.degrees(a)
    ha='left' if np.cos(a)>=0 else 'right'
    if np.cos(a)<0: rot+=180
    ax.text(lx,ly, gn, rotation=rot, rotation_mode='anchor', ha=ha, va='center',
            fontsize=6.6, fontstyle='italic', color='#222')
ax.set_xlim(-1.5,1.5); ax.set_ylim(-1.5,1.5); ax.set_aspect('equal'); ax.axis('off')
ax.set_title("Each functional module is tightly interconnected internally, with no known direct interaction between them", fontproperties=zh(10.5), pad=6, y=1.02)
from matplotlib.lines import Line2D
mh=[Line2D([0],[0],marker='o',color='w',markerfacecolor=MODCOL['TCR'],markersize=8,label='TCR proximal signaling'),
    Line2D([0],[0],marker='o',color='w',markerfacecolor=MODCOL['SAGA'],markersize=8,label='SAGA complex'),
    Line2D([0],[0],marker='o',color='w',markerfacecolor=MODCOL['MED'],markersize=8,label='Mediator (CDK)')]
ax.legend(handles=mh, loc='center', frameon=False, prop=zh(7), handletextpad=0.3)
fig.text(0.5,0.02,"16 nodes arranged on a ring by module; arcs are known protein interactions; node size \u221d |mean on-target effect|",
         ha='center', fontproperties=zh(6.8), color='#666')
fig.savefig('N2_chord.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
