"""
chart_id:        A15
source image:    methodological_validation.png
chart title:     Perturb-seq Platform Validation: AUROC, Survivorship Bias Filtering, and Context-Specific Regulation
language:        Python
env name:        python
input-artifact version_ids (3):
  - b5899e1f-e6ae-4de8-8438-7be8def535dd  (benchmark_results.csv)
  - a76505a5-a3d7-4d2b-b6c7-0d6d2689b88f  (dropout_diagnosis.csv)
  - 26f49368-549f-4923-bf86-f02ca670180f  (context_specific_corrected.csv)
packages referenced: PIL, host, json, matplotlib, numpy, pandas, sklearn
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve, auc

# skill:figure-composer kernel.py (auto-injected on skill load)
import json


def fc_sdk():
    """Rebind-proof SDK handle — see pdf-explore/kernel.py:pdf_sdk."""
    import host
    return host


def figure_outline_schema():
    return {"type":"object","properties":{
        "claim":{"type":"string"}, "width_mm":{"type":"number"},
        "ncol":{"type":"integer"},
        "row_heights_mm":{"type":"array","items":{"type":"number"}},
        "panels":{"type":"array","items":{"type":"object","properties":{
            "letter":{"type":"string"},
            "role":{"type":"string","enum":["schematic","hero","primary","supporting"]},
            "message":{"type":"string"}, "chart_family":{"type":"string"},
            "data_vid":{"type":["string","null"]}, "data_desc":{"type":"string"},
            "row":{"type":"integer"}, "col":{"type":"integer"},
            "colspan":{"type":"integer"}, "rowspan":{"type":"integer"},
            "label_budget":{"type":"integer"}, "ask":{"type":"string"}},
            "required":["letter","role","message","chart_family","row","col","colspan","ask"]}}},
        "required":["claim","width_mm","ncol","row_heights_mm","panels"]}


def grid_geom(outline, dpi=300, gutter_mm=4):
    mm = dpi/25.4
    W = int(outline["width_mm"]*mm); ncol = outline["ncol"]; g = int(gutter_mm*mm)
    colw = (W - g*(ncol-1)) // ncol
    rowh = [int(h*mm) for h in outline["row_heights_mm"]]
    row_y = [sum(rowh[:i]) + g*i for i in range(len(rowh))]
    return W, ncol, colw, rowh, row_y, g

def panel_px(outline, letter, dpi=300, gutter_mm=4):
    W, ncol, colw, rowh, row_y, g = grid_geom(outline, dpi, gutter_mm)
    p = next(q for q in outline["panels"] if q["letter"]==letter)
    cs, rs, r = p["colspan"], p.get("rowspan",1), p["row"]
    return colw*cs + g*(cs-1), sum(rowh[r:r+rs]) + g*(rs-1)

def panel_xy(outline, letter, dpi=300, gutter_mm=4):
    W, ncol, colw, rowh, row_y, g = grid_geom(outline, dpi, gutter_mm)
    p = next(q for q in outline["panels"] if q["letter"]==letter)
    return p["col"]*(colw+g), row_y[p["row"]]

def panel_task(outline, letter, fig_label="Figure", rules_ref="(load `figure-style`)"):
    p = next(q for q in outline["panels"] if q["letter"]==letter)
    w,h = panel_px(outline, letter)
    neighbours = ", ".join(f"{q['letter']}={q['role']}:{q['chart_family']}"
                           for q in outline["panels"] if q["letter"]!=letter)
    data_line = (f"**Data:** `{{{{artifact:{p['data_vid']}}}}}` — {p.get('data_desc','')}"
                 if p.get("data_vid") else "**Data:** none (schematic).")
    rowmates = [q["letter"] for q in outline["panels"]
                if q["row"]==p["row"] and q["letter"]!=letter and q.get("rowspan",1)==p.get("rowspan",1)]
    share_line = (f"- **Row-mates: {','.join(rowmates)}** — match y-limits if same metric; series identity "
                  f"labelled ONCE on the row (rightmost panel).") if rowmates else ""
    bud = p.get("label_budget", 4)
    return f"""Produce panel **{letter}** of {fig_label}."""

def compose_crops(outline, dpi=300, gutter_mm=4, pad_px=4):
    W, ncol, colw, rowh, row_y, g = grid_geom(outline, dpi, gutter_mm)
    H = row_y[-1] + rowh[-1]
    out = {}
    for p in outline["panels"]:
        L = p["letter"]
        w, h = panel_px(outline, L, dpi, gutter_mm)
        x, y = panel_xy(outline, L, dpi, gutter_mm)
        out[L] = (max(x - pad_px, 0), max(y - pad_px, 0),
                  min(x + w + pad_px, W), min(y + h + pad_px, H))
    return out


def compose_figure(outline, panel_paths, out_path, dpi=300, gutter_mm=4,
                   letter_font="DejaVuSans-Bold.ttf", letter_pt=9, letter_case="lower"):
    from PIL import Image, ImageDraw, ImageFont
    W, ncol, colw, rowh, row_y, g = grid_geom(outline, dpi, gutter_mm)
    H = row_y[-1] + rowh[-1]
    canvas = Image.new("RGB",(W,H),"white"); draw = ImageDraw.Draw(canvas)
    try: ft = ImageFont.truetype(letter_font, int(letter_pt/72*dpi))
    except Exception: ft = ImageFont.load_default()
    for p in outline["panels"]:
        L = p["letter"]; w,h = panel_px(outline,L,dpi,gutter_mm); x,y = panel_xy(outline,L,dpi,gutter_mm)
        im = Image.open(panel_paths[L]).convert("RGBA")
        if im.size != (w,h): im = im.resize((w,h))
        canvas.paste(im,(x,y),im)
        stamp = L.lower() if letter_case == "lower" else L.upper()
        draw.text((x+int(1.5/25.4*dpi), y+int(1/25.4*dpi)), stamp, fill="black", font=ft)
    canvas.save(out_path); return out_path,(W,H)

def group_fixes_by_panel(review):
    out = {}
    for v in review.get("violations",[]):
        if v.get("severity") not in ("BLOCKER","MAJOR"): continue
        L = v.get("panel_letter") or (v.get("location"," ")+" ")[0]
        out.setdefault(L,[]).append(
            f"- **[{v['severity']}]** ({v.get('rule_ref','')}, {v.get('location','')}) "
            f"{v.get('finding','')} **Fix:** {v.get('fix','')}")
    return {k:"\n".join(v) for k,v in out.items()}

def review_schema(per_panel=True):
    v_props = {"severity":{"type":"string","enum":["BLOCKER","MAJOR","MINOR"]},
               "rule_ref":{"type":"string"},"location":{"type":"string"},
               "finding":{"type":"string"},"fix":{"type":"string"}}
    if per_panel: v_props["panel_letter"]={"type":"string"}
    return {"type":"object","properties":{
        "editor_verdict":{"type":"string",
            "enum":["accept","minor_revision","major_revision","reject"]},
        "outline_revisions":{"type":"array","description":
            "Figure-level changes that no single panel can fix in isolation.",
            "items":{"type":"object","properties":{
                "kind":{"type":"string","enum":["geometry","titles","panel_set","label_budget","other"]},
                "affected_panels":{"type":"array","items":{"type":"string"}},
                "finding":{"type":"string"},"revision":{"type":"string"}},
                "required":["kind","affected_panels","finding","revision"]}},
        "violations":{"type":"array","items":{"type":"object","properties":v_props,
            "required":list(v_props)}},
        "regression_vs_prev":{"type":"array","items":{"type":"string"}},
        "strongest_aspect":{"type":"string"}},
        "required":["editor_verdict","outline_revisions","violations","strongest_aspect"]}

def composite_review_task(composite_vid, outline, rules_vid, prev_vid=None, round_no=1, min_floor=5):
    panel_tbl = "\n".join(
        f"  {p['letter']}: {p['role']:<10} row{p['row']}+{p.get('rowspan',1)} col{p['col']}+{p['colspan']} "
        f"— {p['chart_family']} — \"{p['message']}\""
        for p in outline["panels"])
    return f"""Review figure."""

def apply_outline_revisions(outline, revisions):
    affected = set()
    for r in revisions:
        affected |= set(r.get("affected_panels", []))
    return affected

def derive_outline(figure_png_path, claim=None, data_hints=None, model=None):
    out = {}
    for p in out.get("panels") or []:
        p["data_vid"] = None
    return out


import host

def apply_figure_style(sizes=(9, 8, 7)):
    pass

def set_frame(ax):
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)


mpl.rcParams['savefig.bbox'] = None

bm = pd.read_csv(host.artifact_path("b5899e1f-e6ae-4de8-8438-7be8def535dd"))
dr = pd.read_csv(host.artifact_path("a76505a5-a3d7-4d2b-b6c7-0d6d2689b88f"))
bc = pd.read_csv(host.artifact_path("26f49368-549f-4923-bf86-f02ca670180f"))

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
axA = axes[0]
y = (bm.truth_class == "positive").astype(int).values
score = bm.ctx_specific_de.fillna(0).values
fpr, tpr, _ = roc_curve(y, score)
rocauc = auc(fpr, tpr)
axA.plot(fpr, tpr, color="#d97757", lw=2.2, label=f"ranking (AUROC={rocauc:.2f})")
axA.plot([0, 1], [0, 1], color="#bbb", lw=1, ls="--", label="random")
axA.set_xlabel("False positive rate")
axA.set_ylabel("True positive rate")
axA.set_title("A · Benchmark: known regulators\nenrich at the top (independent truth)", loc="left", fontsize=10)
axA.legend(frameon=False, fontsize=8, loc="lower right")
axA.text(0.03, 0.03,
         "13 of 27 canonical positives survived the gate,\nscored vs 1,211 'rest' (only 1 curated negative survived)",
         transform=axA.transAxes, fontsize=6.4, color="#777", va="bottom", style="italic")
for s in ["top", "right"]:
    axA.spines[s].set_visible(False)

axB = axes[1]
tier_col = {"well_measured": "#c9c9c9", "low_cells_other": "#e8a33d", "likely_essential_dropout": "#c0504d"}
drp = dr.dropna(subset=["loeuf"])
ndrop = int((dr.essentiality_tier == "likely_essential_dropout").sum())
for t in ["well_measured", "low_cells_other", "likely_essential_dropout"]:
    s = drp[drp.essentiality_tier == t]
    axB.scatter(s.max_n_cells.clip(upper=3000), s.loeuf, s=10, c=tier_col[t], alpha=0.45, edgecolor="none",
                label={"well_measured": "well measured", "low_cells_other": "low cells, other",
                       "likely_essential_dropout": f"likely essential dropout (n={ndrop})"}[t])
axB.axvline(200, color="#555", lw=1, ls="--")
axB.text(210, axB.get_ylim()[1] * 0.96, "gate: n≥200", fontsize=7, color="#555", va="top")
axB.set_xlabel("Max cell count across conditions")
axB.set_ylabel("LOEUF (lower = more constrained)")
axB.set_title("B · Survivorship bias: essential genes\ndeplete cells → filtered out", loc="left", fontsize=10)
axB.legend(frameon=False, fontsize=7, loc="upper right")
for s in ["top", "right"]:
    axB.spines[s].set_visible(False)

axC = axes[2]
cls_col = {"true_regulator": "#788c5d", "expression_artifact": "#c0504d"}
floor = 8.33
bcp = bc.copy()
bcp.rest_baseMean = pd.to_numeric(bcp.rest_baseMean, errors="coerce")
for c in ["true_regulator", "expression_artifact"]:
    s = bcp[bcp.ctx_class == c].dropna(subset=["rest_baseMean"])
    axC.scatter(s.rest_baseMean.clip(lower=0.5), s.de_Stim_max, s=32, c=cls_col[c], alpha=0.7,
                edgecolor="white", lw=0.4,
                label={"true_regulator": f"true regulator (n={int((bc.ctx_class == 'true_regulator').sum())})",
                       "expression_artifact": f"expression artifact (n={int((bc.ctx_class == 'expression_artifact').sum())})"}[c])
axC.axvline(floor, color="#555", lw=1, ls="--")
axC.text(floor * 1.1, axC.get_ylim()[1] * 0.5, "Rest expression\nfloor (Q25)", fontsize=7, color="#555")
axC.set_xscale("log")
axC.set_xlabel("Rest baseline expression (log)")
axC.set_ylabel("Context-specific DE (max Stim)")
axC.set_title("C · Expression control: 11/96 candidates\nare artifacts, not true regulators", loc="left", fontsize=10)
axC.legend(frameon=False, fontsize=7.5, loc="lower right")
for s in ["top", "right"]:
    axC.spines[s].set_visible(False)

fig.suptitle("Methodological validation of the target ranking (all GB10-free)", x=0.5, y=1.01, ha="center",
             fontsize=14, fontweight="bold")
fig.tight_layout()
fig.savefig("methodological_validation.png", dpi=300, bbox_inches="tight")
print("done")
plt.close(fig)
