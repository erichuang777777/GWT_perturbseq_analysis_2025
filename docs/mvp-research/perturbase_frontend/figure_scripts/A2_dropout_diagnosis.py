"""
chart_id:        A2
source image:    dropout_diagnosis.png
chart title:     Loss-intolerant genes drop out below the cell-count gate
language:        Python
env name:        python
input-artifact version_ids (2):
  - 11c6348b-f46d-48a3-8c22-7ae328f40c6c  (DE_stats.suppl_table.csv)
  - 39559648-2551-44f3-9d14-80c861dac4af  (target_master_table.csv)
packages referenced: gzip, matplotlib, numpy, os, pandas
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import gzip

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


de = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv")
mt = pd.read_csv("/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/46a1c017-4a49-46dc-8098-512c17286263/v39559648_target_master_table.csv")

# Aggregate per target across conditions
g = de.groupby('target_contrast_gene_name')
agg = pd.DataFrame({
    'max_n_cells': g['n_cells_target'].max(),
    'min_n_cells': g['n_cells_target'].min(),
    'n_conditions': g.size(),
    'any_significant': g['ontarget_significant'].any(),
}).reset_index().rename(columns={'target_contrast_gene_name':'target'})

agg['n_cells_percentile'] = agg['max_n_cells'].rank(pct=True)*100

GATE=200
agg['gate_failed_on_cells'] = agg['max_n_cells'] < GATE

# Merge constraint from master table
cons = mt[['gene','loeuf','pli']].rename(columns={'gene':'target'})
diag = agg.merge(cons, on='target', how='left')

diag['high_constraint'] = ((diag['loeuf'] < 0.35) | (diag['pli'] >= 0.9))
diag.loc[diag['loeuf'].isna() & diag['pli'].isna(), 'high_constraint'] = np.nan

diag['low_cells'] = diag['max_n_cells'] < 539.0
diag['essential_suspect'] = diag['gate_failed_on_cells'] & (diag['high_constraint'] == True)

def tier(r):
    if not r['gate_failed_on_cells']:
        return 'well_measured'
    if r['high_constraint'] == True:
        return 'likely_essential_dropout'
    return 'low_cells_other'
diag['essentiality_tier'] = diag.apply(tier, axis=1)
diag['n_cells_percentile'] = diag['n_cells_percentile'].round(2)

# Load gnomAD constraint
gn = pd.read_csv("/tmp/gnomad_constraint.txt.bgz", sep="\t", compression="gzip")
gsub = gn[['gene','oe_lof_upper','pLI']].rename(columns={'oe_lof_upper':'loeuf_gnomad','pLI':'pli_gnomad'})
gsub = gsub.sort_values('loeuf_gnomad').drop_duplicates('gene', keep='first')

gsub2 = gsub.rename(columns={'gene':'target'})
diag2 = diag.drop(columns=['high_constraint','low_cells','essential_suspect','essentiality_tier'], errors='ignore').merge(gsub2, on='target', how='left')
diag2['loeuf'] = diag2['loeuf_gnomad'].combine_first(diag2['loeuf'])
diag2['pli']   = diag2['pli_gnomad'].combine_first(diag2['pli'])

hc = ((diag2['loeuf'] < 0.35) | (diag2['pli'] >= 0.9))
diag2['high_constraint'] = hc.where(diag2['loeuf'].notna() | diag2['pli'].notna())

GATE=200
diag2['gate_failed_on_cells'] = diag2['max_n_cells'] < GATE
diag2['essential_suspect'] = diag2['gate_failed_on_cells'] & (diag2['high_constraint'] == True)
def tier(r):
    if not r['gate_failed_on_cells']: return 'well_measured'
    if r['high_constraint'] == True: return 'likely_essential_dropout'
    return 'low_cells_other'
diag2['essentiality_tier'] = diag2.apply(tier, axis=1)

led = diag2[diag2['essentiality_tier']=='likely_essential_dropout']
led_sorted = led.sort_values(['loeuf','max_n_cells']).copy()

d = diag2.copy()
p = d[d['loeuf'].notna()].copy()
bg = p[p['essentiality_tier']!='likely_essential_dropout']
es = p[p['essentiality_tier']=='likely_essential_dropout']

apply_figure_style()
fig, ax = plt.subplots(figsize=(9,6.5))
ax.scatter(bg['max_n_cells'], bg['loeuf'], s=8, c=META_GREY, alpha=0.40, linewidths=0,
           label='Other targets', rasterized=True)
ax.scatter(es['max_n_cells'], es['loeuf'], s=28, c='#c0392b', alpha=0.85, linewidths=0,
           label=f'Likely essential dropout (n={len(es)})')
ax.axvline(200, color='#2c3e50', ls='--', lw=1.3)
ax.axhline(0.35, color='#2c3e50', ls=':', lw=1.2)
ax.set_xscale('log'); ax.set_xlim(15,12000); ax.set_ylim(-0.02,2.0)
ax.set_xticks([100,1000,10000]); ax.set_xticklabels(['100','1k','10k'])
ax.set_xlabel('Max cells recovered across conditions')
ax.set_ylabel('LOEUF (gnomAD) — lower = more loss-intolerant')
ax.set_title('Loss-intolerant genes drop out below the cell-count gate')
ymax_frac=(0.35-(-0.02))/(2.0-(-0.02))
ax.axvspan(15,200, ymin=0, ymax=ymax_frac, color='#c0392b', alpha=0.06)
ax.text(215,1.90,'gate = 200 cells', color='#2c3e50', fontsize=7)
ax.text(9500,0.37,'LOEUF 0.35', color='#2c3e50', fontsize=7, ha='right', va='bottom')
ax.text(55,0.45,'essential-suspect dropout zone\n(<200 cells, LOEUF<0.35)',
        color='#7b241c', fontsize=6.5, ha='center', va='bottom', style='italic')
labs=led_sorted.head(6).reset_index(drop=True); ys=[1.35,1.15,0.95,0.75,0.60,0.48]
for i,rw in labs.iterrows():
    ax.annotate(rw['target'], xy=(rw['max_n_cells'],rw['loeuf']),
                xytext=(rw['max_n_cells']*(0.6 if i%2==0 else 1.15), ys[i]),
                fontsize=6.5, color='#7b241c', ha='center',
                arrowprops=dict(arrowstyle='-', color='#7b241c', lw=0.5, alpha=0.7))
ax.legend(loc='upper right', frameon=False, fontsize=7)
fig.tight_layout()
fig.savefig('dropout_diagnosis.png', dpi=150, bbox_inches='tight')
print("saved")
