"""
Standalone generating script for a Perturbase CD4+ T-cell Perturb-seq platform chart.

chart_id:        V6
source image:    V6_pca_biplot.png
chart title:     Effect size and DE-gene count load on separate principal axes
language:        Python
env name:        python
packages:        matplotlib, os, pandas, sklearn
input-artifact version_ids:
  - e168ccb9-6d5d-427c-a5cf-93f388492f2f
  - a58b4ba0-da04-46b9-9ad2-21a3e632615c
  - 024cefa5-3a8f-4e4e-b82a-51f356a03960
"""

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


import os
os.environ['NUMBA_CACHE_DIR'] = os.path.abspath('./numba_cache')
import pandas as pd, numpy as np, matplotlib as mpl, matplotlib.pyplot as plt

figs = apply_figure_style()

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

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

X = np.column_stack([feat.values, np.log1p(demf.values)])
Xs = StandardScaler().fit_transform(X)
pca = PCA(n_components=6, random_state=0)
P = pca.fit_transform(Xs)
evr = pca.explained_variance_ratio_

feat_names = ['Rest effect', 'Stim8hr effect', 'Stim48hr effect', 'Rest nDE', 'Stim8hr nDE', 'Stim48hr nDE']
load = pca.components_[:2].T  # (6 features, 2 PCs)

x_lo, x_hi = P[:, 0].min(), P[:, 0].max()
y_lo, y_hi = P[:, 1].min(), P[:, 1].max()
half = 0.62 * min(x_hi - x_lo, y_hi - y_lo) / 2
load_scale = half / np.abs(load).max()

fig_v6, ax = plt.subplots(figsize=(5.8, 4.8))
ax.scatter(P[~is_gate, 0], P[~is_gate, 1], s=5, c='0.85', alpha=0.5, linewidths=0, zorder=1, rasterized=True)
ax.scatter(P[is_gate, 0], P[is_gate, 1], s=9, c='#7FA8D0', alpha=0.7, linewidths=0, zorder=2, rasterized=True, label='Gate-passing (1,225)')
sl_idx = [feat_genes.index(g) for g in sl_present]
ax.scatter(P[sl_idx, 0], P[sl_idx, 1], s=30, facecolors='none', edgecolors='#B5462E', linewidths=1.1, zorder=5, label='Curated shortlist (15)')

arr_col = [CCOL['Rest'], CCOL['Stim8hr'], CCOL['Stim48hr'], '0.4', '0.4', '0.4']
for k, c in enumerate(arr_col):
    dx, dy = load[k, 0] * load_scale, load[k, 1] * load_scale
    ax.annotate('', xy=(dx, dy), xytext=(0, 0), arrowprops=dict(arrowstyle='-|>', color=c, lw=1.3, mutation_scale=10, alpha=0.9), zorder=6)
# effect triple points to positive-PC1/positive-PC2 region; label stacked beyond tips
etip = load[:3].mean(0) * load_scale
for i, cond in enumerate(COND):
    ax.text(etip[0] + 1.1, etip[1] - 1.0 + (1 - i) * 1.2, f"{CLAB[cond]} effect", color=CCOL[cond],
            fontsize=6, ha='left', va='center', zorder=7)
ntip = load[3:].mean(0) * load_scale
ax.text(ntip[0] - 0.4, ntip[1] + 0.9, "DE-gene count\n(all conditions)", color='0.3', fontsize=6,
        ha='center', va='bottom', zorder=7)
ax.axhline(0, color='0.8', lw=0.5, zorder=0)
ax.axvline(0, color='0.8', lw=0.5, zorder=0)
ax.set_xlabel("PC1 (55% of variance)")
ax.set_ylabel("PC2 (33% of variance)")
ax.set_xlim(x_lo - 0.6, x_hi + 3.2)
ax.set_ylim(y_lo - 0.6, y_hi + 1.0)
ax.set_title("Effect size and DE-gene count load on separate principal axes", loc='left')
ax.legend(loc='lower right', frameon=False, fontsize=6, handletextpad=0.4)
fig_v6.tight_layout()
fig_v6.savefig("V6_pca_biplot.png", dpi=300, bbox_inches='tight')