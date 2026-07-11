"""
chart_id:        A14
source image:    context_specific_corrected.png
chart title:     Context-Specific Regulators: Baseline Correction Diagnostic
language:        Python
env name:        python
input-artifact version_ids (2):
  - 11c6348b-f46d-48a3-8c22-7ae328f40c6c  (DE_stats.suppl_table.csv)
  - 39559648-2551-44f3-9d14-80c861dac4af  (target_master_table.csv)
packages referenced: matplotlib, numpy, os, pandas
"""

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

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


de = pd.read_csv('/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/eb4c9b7d-b197-47c5-824c-efbd6bc2b805/v11c6348b_DE_stats.suppl_table.csv')
master = pd.read_csv('/Users/eric777/.claude-science/orgs/da569c35-fbb9-41f8-ad57-1225ad245b87/artifacts/proj_9efc9e969acb/46a1c017-4a49-46dc-8098-512c17286263/v39559648_target_master_table.csv')

ctx = master[master['is_ctx_specific']==True].copy()

rest = de[de['culture_condition']=='Rest'][['target_contrast_gene_name','target_baseMean','n_total_de_genes']].copy()
rest = rest.rename(columns={'target_contrast_gene_name':'gene','target_baseMean':'rest_baseMean'})

floor = de['target_baseMean'].quantile(0.25)

c = ctx.merge(rest[['gene','rest_baseMean']], on='gene', how='left')
c['de_Stim_max'] = c[['de_Stim8hr','de_Stim48hr']].max(axis=1)

flagship = ['CD3E','PLCG1','VAV1','STAT3','BCL10']

def classify2(r):
    bm = r['rest_baseMean']
    if pd.isna(bm): return 'unknown'
    return 'expression_artifact' if bm < floor else 'true_regulator'

c['ctx_class'] = c.apply(classify2, axis=1)
c['is_flagship'] = c['gene'].isin(flagship)

col = {'true_regulator':'#2c7fb8','expression_artifact':'#d95f02','unknown':'#999999'}

apply_figure_style()
fig, ax = plt.subplots(figsize=(7.0,5.0))
plotd = c.copy(); xmin=0.1
for cls in ['true_regulator','expression_artifact']:
    sub = plotd[plotd['ctx_class']==cls]
    ax.scatter(sub['rest_baseMean'], sub['de_Stim_max'], c=col[cls], s=42,
               edgecolor='white', linewidth=0.6, label=cls.replace('_',' '), zorder=3)
ax.set_xscale('log')
ax.axvspan(xmin, floor, color=col['expression_artifact'], alpha=0.08, zorder=0)
ax.axvline(floor, color=col['expression_artifact'], ls='--', lw=1.0, zorder=1)
ax.text(floor*0.9, ax.get_ylim()[1]*0.97, f'baseMean floor = {floor:.1f}\n(all-conditions Q25)',
        ha='right', va='top', fontsize=6, color=col['expression_artifact'])
ax.text(floor**0.5*xmin**0.5, 30, 'artifact zone\n(low Rest expression)', ha='center',
        va='bottom', fontsize=6.5, color=col['expression_artifact'], style='italic')
for _,r in plotd.iterrows():
    if r['is_flagship']:
        ax.annotate(r['gene'], (r['rest_baseMean'], r['de_Stim_max']), fontsize=6.5,
                    fontweight='bold', xytext=(4,3), textcoords='offset points')
    elif r['ctx_class']=='expression_artifact':
        ax.annotate(r['gene'], (r['rest_baseMean'], r['de_Stim_max']), fontsize=5.5,
                    color=col['expression_artifact'], xytext=(3,2), textcoords='offset points')
ax.set_xlabel('Rest baseline expression (target_baseMean, log scale)')
ax.set_ylabel('Context-specific DE effect (max Stim DE genes)')
ax.set_title('Baseline expression separates true context-specific regulators from artifacts')
ax.legend(frameon=False, loc='lower right', fontsize=7); ax.margins(0.04)
fig.tight_layout()
fig.savefig('context_specific_corrected.png', dpi=300, bbox_inches='tight')
