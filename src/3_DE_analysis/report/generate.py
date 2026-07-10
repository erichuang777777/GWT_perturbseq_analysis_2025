"""Generate compact reports from target-card CSV outputs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


LIMITATIONS_PARAGRAPH = (
    "Limitations: This platform is based on primary human CD4⁺ T cell CRISPRi "
    "Perturb-seq across Rest/Stim8hr/Stim48hr conditions, with limited donors, "
    "transcriptomic readouts, and hypothesis-generating interpretation only. "
    "Results require orthogonal validation such as independent guides, donor "
    "replication, protein/functional assays, and disease-context models before "
    "therapeutic interpretation."
)

EVIDENCE_TYPE_GUIDE = [
    {
        "label": "Perturb-seq screen evidence",
        "caveat": (
            "Experimental CD4 CRISPRi transcriptomic evidence; supports a "
            "target-condition perturbation hypothesis, not therapeutic efficacy."
        ),
    },
    {
        "label": "Human genetic association",
        "caveat": (
            "External association support for disease relevance; not direct "
            "perturbation validation and not proof of causal drug response."
        ),
    },
    {
        "label": "Population LoF evidence",
        "caveat": (
            "Population-level loss-of-function burden evidence; not patient-level "
            "prediction and not a substitute for disease-context validation."
        ),
    },
    {
        "label": "Drug / tractability precedent",
        "caveat": (
            "Evidence that a target class or nearby mechanism may be druggable; "
            "not evidence that modulating this target is safe or efficacious here."
        ),
    },
    {
        "label": "Heuristic readiness triage",
        "caveat": (
            "Internal prioritization heuristic for follow-up planning; not a "
            "clinical recommendation or validation endpoint."
        ),
    },
]

CORE_COLUMNS = [
    "target",
    "condition",
    "target_id",
    "statistical_evidence_grade",
    "n_cells_target",
    "n_guides",
    "n_total_de_genes",
    "crossdonor_correlation_mean",
    "crossguide_correlation",
    "replicate_pass_flag",
    "pathway_axis",
    "clinical_axis",
    "nearest_success_drug",
    "score_cap_reason",
]


def _bool_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.lower().isin({"true", "1", "yes", "y"})


def normalize_cards(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["ontarget_significant", "offtarget_flag", "replicate_pass_flag"]:
        if col in out.columns:
            out[col] = _bool_series(out[col])
    numeric_cols = [
        "statistical_evidence_grade",
        "n_cells_target",
        "n_guides",
        "n_total_de_genes",
        "n_up_genes",
        "n_down_genes",
        "crossdonor_correlation_mean",
        "crossguide_correlation",
        "condition_specificity_score",
        "positive_control_similarity",
    ]
    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def _top_candidates(df: pd.DataFrame, top_n: int) -> pd.DataFrame:
    sort_cols = [
        "statistical_evidence_grade",
        "replicate_pass_flag",
        "n_total_de_genes",
        "n_cells_target",
        "condition_specificity_score",
    ]
    sort_cols = [c for c in sort_cols if c in df.columns]
    top = df.sort_values(sort_cols, ascending=[False] * len(sort_cols)) if sort_cols else df
    return top.head(top_n).copy()


def _watchlist(df: pd.DataFrame, top_n: int) -> pd.DataFrame:
    if "score_cap_reason" not in df.columns:
        return df.head(0).copy()
    mask = ~df["score_cap_reason"].fillna("").str.lower().isin({"", "none"})
    if "statistical_evidence_grade" in df.columns:
        mask &= df["statistical_evidence_grade"].fillna(0) >= 2
    watch = df.loc[mask].copy()
    sort_cols = [c for c in ["statistical_evidence_grade", "n_total_de_genes", "n_cells_target"] if c in watch.columns]
    if sort_cols:
        watch = watch.sort_values(sort_cols, ascending=[False] * len(sort_cols))
    return watch.head(top_n)


def _counts(df: pd.DataFrame, column: str) -> List[Dict[str, Any]]:
    if column not in df.columns:
        return []
    counts = df[column].fillna("unknown").astype(str).value_counts().reset_index()
    counts.columns = [column, "n"]
    return json.loads(counts.to_json(orient="records"))


def _safe_records(df: pd.DataFrame, columns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    if columns is not None:
        df = df[[c for c in columns if c in df.columns]].copy()
    return json.loads(df.where(pd.notna(df), None).to_json(orient="records"))


def build_report_payload(
    cards: pd.DataFrame,
    dataset_id: str = "local",
    top_n: int = 50,
    provenance: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    df = normalize_cards(cards)
    top = _top_candidates(df, top_n)
    watch = _watchlist(df, top_n)
    grade_counts = _counts(df, "statistical_evidence_grade")
    condition_counts = _counts(df, "condition")
    pathway_counts = _counts(df, "pathway_axis")
    clinical_counts = _counts(df, "clinical_axis")

    high_confidence = 0
    if "statistical_evidence_grade" in df.columns:
        high_confidence = int((df["statistical_evidence_grade"].fillna(0) >= 3).sum())

    replicate_pass = 0
    if "replicate_pass_flag" in df.columns:
        replicate_pass = int(df["replicate_pass_flag"].sum())

    summary = {
        "dataset_id": dataset_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "n_rows": int(df.shape[0]),
        "n_targets": int(df["target"].nunique()) if "target" in df.columns else 0,
        "n_conditions": int(df["condition"].nunique()) if "condition" in df.columns else 0,
        "n_grade_3_or_4": high_confidence,
        "n_replicate_pass": replicate_pass,
        "n_watchlist": int(watch.shape[0]),
    }

    return {
        "summary": summary,
        "grade_counts": grade_counts,
        "condition_counts": condition_counts,
        "pathway_counts": pathway_counts,
        "clinical_counts": clinical_counts,
        "top_candidates": _safe_records(top, CORE_COLUMNS),
        "top_candidates_note": (
            "Top Candidates are ranked by the primary DE signal with replicate_pass_flag used as a "
            "sort key, not as a hard filter. Distinguish this from the guide-robust "
            "high-confidence signal; use the high-confidence / replicate-pass subset for "
            "biological claims whenever possible."
        ),
        "watchlist": _safe_records(watch, CORE_COLUMNS),
        "limitations": LIMITATIONS_PARAGRAPH,
        "evidence_type_guide": EVIDENCE_TYPE_GUIDE,
        "next_steps": [
            "Treat Top Candidates as primary DE signal; prioritize grade 3-4 target-condition pairs with replicate_pass_flag=True as guide-robust high-confidence signal for biological claims.",
            "Treat high score_cap_reason burden as an experiment-design issue before biology interpretation.",
            "Use h5ad-level validation for selected targets: donor-aware pseudobulk, module scoring, and batch sensitivity checks.",
            "Map short-listed targets to clinical mechanism, safety liability, and assay feasibility before drug discovery handoff.",
        ],
        # Four-layer provenance (dataset_version/engine_version/schema_version/
        # signature_set_version) per docs/IMPLEMENTATION_PLAN.md's B4 response --
        # every export should carry them, not just the live API. Empty dict when
        # the caller has no dataset metadata (e.g. a bare CSV with no build record).
        "provenance": provenance or {},
    }


def _markdown_table(records: List[Dict[str, Any]], columns: List[str]) -> str:
    if not records:
        return "_No records._"
    df = pd.DataFrame(records)
    df = df[[c for c in columns if c in df.columns]]
    headers = list(df.columns)
    rows = []
    rows.append("| " + " | ".join(headers) + " |")
    rows.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        values = [str(row.get(col, "")).replace("|", "/") for col in headers]
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def render_markdown(payload: Dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# GWT Target Card Report",
        "",
        f"- dataset_id: `{summary['dataset_id']}`",
        f"- created_at: `{summary['created_at']}`",
        f"- rows: {summary['n_rows']}",
        f"- targets: {summary['n_targets']}",
        f"- conditions: {summary['n_conditions']}",
        f"- grade 3-4 rows: {summary['n_grade_3_or_4']}",
        f"- replicate-pass rows: {summary['n_replicate_pass']}",
        f"- watchlist rows: {summary['n_watchlist']}",
        "",
        "## Limitations",
        "",
        payload.get("limitations", LIMITATIONS_PARAGRAPH),
        "",
        "## Evidence Type Guide",
        "",
    ]
    for item in payload.get("evidence_type_guide", EVIDENCE_TYPE_GUIDE):
        lines.append(f"- **{item['label']}** — {item['caveat']}")
    lines.extend([
        "",
        "## Top Candidates",
        "",
        payload.get("top_candidates_note", ""),
        "",
        _markdown_table(payload["top_candidates"], CORE_COLUMNS),
        "",
        "## Watchlist",
        "",
        _markdown_table(payload["watchlist"], CORE_COLUMNS),
        "",
        "## Next Steps",
        "",
    ])
    lines.extend(f"- {item}" for item in payload["next_steps"])
    lines.append("")
    provenance = payload.get("provenance") or {}
    if provenance:
        lines.append("## Provenance")
        lines.append("")
        lines.extend(f"- {k}: `{v}`" for k, v in provenance.items())
        lines.append("")
    return "\n".join(lines)


def render_html(payload: Dict[str, Any]) -> str:
    summary = payload["summary"]
    top_df = pd.DataFrame(payload["top_candidates"])
    watch_df = pd.DataFrame(payload["watchlist"])
    top_html = top_df.to_html(index=False, escape=True) if not top_df.empty else "<p>No records.</p>"
    watch_html = watch_df.to_html(index=False, escape=True) if not watch_df.empty else "<p>No records.</p>"
    next_steps = "".join(f"<li>{step}</li>" for step in payload["next_steps"])
    metrics = "".join(
        f"<div class='metric'><span>{k}</span><strong>{v}</strong></div>"
        for k, v in summary.items()
    )
    provenance = payload.get("provenance") or {}
    provenance_section = ""
    if provenance:
        provenance_items = "".join(f"<li><code>{k}</code>: {v}</li>" for k, v in provenance.items())
        provenance_section = f"<h2>Provenance</h2>\n  <ul>{provenance_items}</ul>"
    evidence_items = "".join(
        f"<li><strong>{item['label']}:</strong> {item['caveat']}</li>"
        for item in payload.get("evidence_type_guide", EVIDENCE_TYPE_GUIDE)
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>GWT Target Card Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }}
    h1, h2 {{ margin-bottom: 10px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; margin: 20px 0; }}
    .metric {{ border: 1px solid #d8dee8; border-radius: 6px; padding: 10px 12px; }}
    .metric span {{ display: block; color: #52606d; font-size: 12px; }}
    .metric strong {{ display: block; margin-top: 4px; font-size: 18px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 12px; margin-bottom: 28px; }}
    th, td {{ border: 1px solid #d8dee8; padding: 6px 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f5f7fa; }}
  </style>
</head>
<body>
  <h1>GWT Target Card Report</h1>
  <div class="metrics">{metrics}</div>
  <h2>Limitations</h2>
  <p>{payload.get("limitations", LIMITATIONS_PARAGRAPH)}</p>
  <h2>Evidence Type Guide</h2>
  <ul>{evidence_items}</ul>
  <h2>Top Candidates</h2>
  <p>{payload.get("top_candidates_note", "")}</p>
  {top_html}
  <h2>Watchlist</h2>
  {watch_html}
  <h2>Next Steps</h2>
  <ul>{next_steps}</ul>
  {provenance_section}
</body>
</html>
"""


def write_report(
    cards_path: Path,
    out_path: Path,
    dataset_id: str = "local",
    fmt: str = "html",
    top_n: int = 50,
    provenance: Optional[Dict[str, Any]] = None,
) -> Path:
    cards = pd.read_csv(cards_path)
    payload = build_report_payload(cards, dataset_id=dataset_id, top_n=top_n, provenance=provenance)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    elif fmt == "md":
        out_path.write_text(render_markdown(payload), encoding="utf-8")
    elif fmt == "html":
        out_path.write_text(render_html(payload), encoding="utf-8")
    else:
        raise ValueError("fmt must be html, md, or json")
    return out_path


def build_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate target-card summary report.")
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dataset-id", default="local")
    parser.add_argument("--fmt", choices=["html", "md", "json"], default="html")
    parser.add_argument("--top-n", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    args = build_parser()
    out = write_report(args.cards, args.output, dataset_id=args.dataset_id, fmt=args.fmt, top_n=args.top_n)
    print(f"Wrote target report -> {out.resolve()}")


if __name__ == "__main__":
    main()
