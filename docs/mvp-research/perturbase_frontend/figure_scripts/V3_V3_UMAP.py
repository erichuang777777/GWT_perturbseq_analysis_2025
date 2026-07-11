"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        V3
source image:    V3_UMAP.png
chart title:     UMAP
language:        Python
env name:        python
packages:        adjustText, matplotlib, numpy, os, pandas, sklearn
input-artifact version_ids:
  - 506b62e3-4ad0-42a0-ac4d-b779a31f8121
  - e168ccb9-6d5d-427c-a5cf-93f388492f2f
  - a58b4ba0-da04-46b9-9ad2-21a3e632615c
  - 024cefa5-3a8f-4e4e-b82a-51f356a03960
  - 02213819-0c89-4011-b488-e7780f3edd0a
"""

import os
os.environ['NUMBA_CACHE_DIR'] = os.path.abspath('./numba_cache')
os.makedirs('./numba_cache', exist_ok=True)

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import Normalize
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from adjustText import adjust_text

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

apply_figure_style()

curated = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/71b03570-3c70-4117-bd81-90917d27ab6b/v506b62e3_curated_targets.csv")
eff = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/34e69736-d190-40d4-853c-90e059c0d7b9/ve168ccb9_effect_matrix.csv", index_col=0)
dem = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/b6f9b507-3552-4d58-84f3-07354e0f53cb/va58b4ba0_de_matrix.csv", index_col=0)
gate = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/e3866132-df1b-4e32-a9d9-db3c9ca7eb4e/v024cefa5_gate_passing_targets.csv")

COND = ['Rest', 'Stim8hr', 'Stim48hr']
CCOL = {'Rest': '#4C6FB1', 'Stim8hr': '#E8A33D', 'Stim48hr': '#B5462E'}
CLAB = {'Rest': 'Rest', 'Stim8hr': 'Stim 8 hr', 'Stim48hr': 'Stim 48 hr'}
shortlist = ['CD3E', 'LAT', 'TADA2B', 'SENP5', 'PLCG1', 'VAV1', 'SGF29', 'UBXN1', 'CD247', 'MED12', 'CCNC', 'SUPT20H', 'TADA1', 'DENR', 'PMVK']

feat = eff.dropna(how='any').copy()
feat_genes = feat.index.tolist()
demf = dem.reindex(feat.index)
sl_present = [g for g in shortlist if g in feat.index]
gate_targets = set(gate['target_contrast_gene_name'].unique())
is_gate = np.array([g in gate_targets for g in feat_genes])
resp_mag = np.abs(feat.values).mean(axis=1)

X = np.column_stack([feat.values, np.log1p(demf.values)])
Xs = StandardScaler().fit_transform(X)

Y_umap = np.load("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/2a0bd42f-1c35-4988-a923-e7b7feeeeee3/v02213819_Yumap.npy")

def corner_arrows(ax, xlabel, ylabel, frac=0.16):
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    lx = (x1-x0)*frac; ly = (y1-y0)*frac
    ox = x0+(x1-x0)*0.03; oy = y0+(y1-y0)*0.03
    ap = dict(arrowstyle='-|>', lw=1.3, color='0.25', mutation_scale=11)
    ax.annotate('', xy=(ox+lx, oy), xytext=(ox, oy), arrowprops=ap)
    ax.annotate('', xy=(ox, oy+ly), xytext=(ox, oy), arrowprops=ap)
    ax.text(ox+lx*0.55, oy-(y1-y0)*0.03, xlabel, ha='center', va='top', fontsize=6, color='0.25')
    ax.text(ox-(x1-x0)*0.03, oy+ly*0.55, ylabel, ha='right', va='center', rotation=90, fontsize=6, color='0.25')

def leader_labels(ax, xs, ys, labels, italic=True, fs=6, force=(0.6, 0.9)):
    texts = [ax.text(x, y, l, fontsize=fs, fontstyle='italic' if italic else 'normal', ha='center', va='center',
             zorder=7, bbox=dict(boxstyle='round,pad=0.12', fc='white', ec='none', alpha=0.9)) for x, y, l in zip(xs, ys, labels)]
    adjust_text(texts, x=list(xs), y=list(ys), ax=ax, expand=(1.5, 1.9),
        arrowprops=dict(arrowstyle='-', color='0.45', lw=0.5), force_text=force, force_static=(0.3, 0.4))
    return texts

n_nongate = int((~is_gate).sum())
n_gate = int(is_gate.sum())

def embed_plot(coords, title, xname, yname, fname):
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    norm = Normalize(vmin=0, vmax=np.percentile(resp_mag, 98))
    ax.scatter(coords[~is_gate, 0], coords[~is_gate, 1], s=5, c='0.82', alpha=0.55, linewidths=0, zorder=1, rasterized=True)
    sc = ax.scatter(coords[is_gate, 0], coords[is_gate, 1], s=11, c=resp_mag[is_gate], cmap='viridis', norm=norm, alpha=0.9, linewidths=0, zorder=3, rasterized=True)
    sl_idx = [feat_genes.index(g) for g in sl_present]
    ax.scatter(coords[sl_idx, 0], coords[sl_idx, 1], s=34, facecolors='none', edgecolors='#B5462E', linewidths=1.1, zorder=5)
    ax.margins(0.06); corner_arrows(ax, xname, yname)
    leader_labels(ax, coords[sl_idx, 0], coords[sl_idx, 1], sl_present, fs=6)
    ax.set_title(title, loc='left')
    cb = fig.colorbar(sc, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("Gate-passing: mean |effect|", fontsize=6); cb.ax.tick_params(labelsize=6)
    handles = [Line2D([0], [0], marker='o', ls='', mfc='0.82', mec='none', ms=4, label=f'Other targets ({n_nongate:,})'),
               Line2D([0], [0], marker='o', ls='', mfc=plt.get_cmap('viridis')(0.6), mec='none', ms=4, label=f'Gate-passing ({n_gate:,})'),
               Line2D([0], [0], marker='o', ls='', mfc='none', mec='#B5462E', mew=1.1, ms=6, label='Curated shortlist (15)')]
    ax.legend(handles=handles, loc='upper right', frameon=False, fontsize=6, handletextpad=0.4)
    fig.tight_layout(); fig.savefig(fname, dpi=300, bbox_inches='tight')
    return fig

plt.close('all')
f3 = embed_plot(Y_umap, "UMAP places curated targets in shared response neighbourhoods", "UMAP 1", "UMAP 2", "V3_UMAP.png")