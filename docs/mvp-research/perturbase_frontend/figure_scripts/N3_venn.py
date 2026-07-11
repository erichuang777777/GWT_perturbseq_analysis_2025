"""
Standalone figure-generating script.

chart_id            : N3
source image        : N3_venn.png
chart title         : Three-Set Euler Diagram: Significant Genes, Gating Filter, and Off-Target Genes
language            : Python
conda env name      : python
input artifact vids : ['11c6348b-f46d-48a3-8c22-7ae328f40c6c', '506b62e3-4ad0-42a0-ac4d-b779a31f8121']
referenced packages : matplotlib, matplotlib_venn, os, pandas

Extracted verbatim from artifact lineage (host.lineage['fdd1782c-4f48-46da-ac8c-8e4c2b6a8b47']).
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
from matplotlib_venn import venn3, venn3_circles

apply_figure_style(sizes=(8,7,6))
os.makedirs('out', exist_ok=True)

raw = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")
curated = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")

g = raw.groupby('target_contrast_gene_name')
significant = set(g['ontarget_significant'].max()[lambda s: s>0].index)
has_offtarget = set(g['offtarget_flag'].max()[lambda s: s>0].index)
passes_gate = set(curated[curated['passes_gate']==1]['target_contrast_gene_name'].unique())

CCOL = {'Rest':'#4C72B0','Stim8hr':'#DD8452','Stim48hr':'#8172B3'}

def zh(size=None, weight=None):
    fp = FontProperties(family='DejaVu Sans')
    if size: fp.set_size(size)
    if weight: fp.set_weight(weight)
    return fp

S, P, O = significant, passes_gate, has_offtarget
regions = {
    '100': len(S-P-O), '010': len(P-S-O), '001': len(O-S-P),
    '110': len((S&P)-O), '101': len((S&O)-P), '011': len((P&O)-S),
    '111': len(S&P&O)
}

fig, ax = plt.subplots(figsize=(6.2,5.4))
subsets = (regions['100'],regions['010'],regions['110'],regions['001'],regions['101'],regions['011'],regions['111'])
v = venn3(subsets=subsets,
          set_labels=('Significant hits', 'Passes gate', 'Off-target'),
          set_colors=(CCOL['Rest'],'#55A868',CCOL['Stim8hr']), alpha=0.55, ax=ax)
for t in v.set_labels:
    if t: t.set_fontproperties(zh(9))
for sid in regions:
    lbl = v.get_label_by_id(sid)
    if lbl:
        lbl.set_text(f"{regions[sid]:,}" if regions[sid] else "")
        lbl.set_fontsize(8)
venn3_circles(subsets=subsets, ax=ax, lw=0.8, color='#444444')
ax.set_title("Gate-passing targets fall entirely within significant hits; 93 off-target hits lie outside significant",
             fontproperties=zh(11), pad=14)
fig.text(0.5,0.02,"Gene-level sets (n=8,006 unique genes): significant 7,913 \u00b7 passes gate 1,235 \u00b7 off-target 1,152",
         ha='center', fontproperties=zh(7.5), color='#555555')
fig.savefig('out/N3_venn.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close(fig)
