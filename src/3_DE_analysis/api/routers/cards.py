"""Target-card read/query/export endpoints (architecture refactor Phase 4, §4.1)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from api import deps
from report.generate import build_report_payload, write_report

router = APIRouter(tags=["cards"])


@router.get("/api/targets/{dataset_id}")
def list_targets(
    dataset_id: str,
    grade: Optional[int] = Query(default=None, ge=1, le=4),
    condition: Optional[str] = None,
    pathway_axis: Optional[str] = None,
    clinical_axis: Optional[str] = None,
    cap_reason: Optional[str] = None,
    target_search: Optional[str] = None,
    replicate_pass: Optional[bool] = None,
    off_target: Optional[bool] = None,
    min_de_genes: Optional[int] = Query(default=None, ge=0),
    max_rows: Optional[int] = 500,
) -> List[Dict[str, Any]]:
    out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")

    df = deps._normalize_cell_values(deps._load_cards(out_csv))
    if grade is not None:
        df = df[df["statistical_evidence_grade"] >= grade]
    if condition:
        df = df[df["condition"].str.lower() == condition.lower()]
    if pathway_axis:
        df = df[df["pathway_axis"].str.lower() == pathway_axis.lower()]
    if clinical_axis:
        df = df[df["clinical_axis"].str.lower() == clinical_axis.lower()]
    if cap_reason:
        df = df[df["score_cap_reason"].str.contains(cap_reason, case=False, na=False)]
    if target_search:
        df = df[df["target"].str.contains(target_search, case=False, na=False)]
    if replicate_pass is not None and "replicate_pass_flag" in df.columns:
        df = df[df["replicate_pass_flag"] == replicate_pass]
    if off_target is not None and "offtarget_flag" in df.columns:
        df = df[df["offtarget_flag"] == off_target]
    if min_de_genes is not None:
        df = df[df["n_total_de_genes"] >= min_de_genes]
    df = df.sort_values(
        by=["statistical_evidence_grade", "n_total_de_genes", "n_cells_target"],
        ascending=[False, False, False],
    )
    df = deps._safe_limit(df, max_rows)
    return deps._json_records(df)


@router.get("/api/summary/{dataset_id}")
def summarize_dataset(dataset_id: str, top_n: int = Query(default=50, ge=1, le=500)) -> Dict[str, Any]:
    out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    return build_report_payload(deps._load_cards(out_csv), dataset_id=dataset_id, top_n=top_n, provenance=deps._provenance_block(dataset_id))


@router.get("/api/options/{dataset_id}")
def dataset_options(dataset_id: str) -> Dict[str, Any]:
    out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    df = deps._normalize_cell_values(deps._load_cards(out_csv))

    cap_tokens: set[str] = set()
    if "score_cap_reason" in df.columns:
        for value in df["score_cap_reason"].dropna().astype(str):
            cap_tokens.update(token for token in value.split(";") if token and token != "none")

    def _unique(col: str) -> List[str]:
        if col not in df.columns:
            return []
        return sorted([str(v) for v in df[col].dropna().unique() if str(v)])

    return {
        "conditions": _unique("condition"),
        "pathway_axis": _unique("pathway_axis"),
        "clinical_axis": _unique("clinical_axis"),
        "score_cap_reason": sorted(cap_tokens),
        "grades": sorted([int(v) for v in df["statistical_evidence_grade"].dropna().unique()]) if "statistical_evidence_grade" in df.columns else [],
    }


@router.get("/api/targets/{dataset_id}/{target_id}")
def get_target(dataset_id: str, target_id: str) -> Dict[str, Any]:
    out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    df = deps._normalize_cell_values(deps._load_cards(out_csv))
    target_rows = df[df["target"] == target_id]
    if target_rows.empty:
        raise HTTPException(status_code=404, detail=f"target not found: {target_id}")
    row = target_rows.iloc[0].to_dict()
    return {"target": target_id, "rows": deps._json_records(target_rows), "summary": deps._json_object(row)}


@router.get("/api/modules/{dataset_id}")
def get_module_scores(dataset_id: str) -> List[Dict[str, Any]]:
    out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    meta = deps._read_metadata(dataset_id)
    if meta and meta.get("module_scores_enabled") is False:
        return []
    df = deps._normalize_cell_values(deps._load_cards(out_csv))
    module_df = deps._module_scores(df)
    if module_df.empty:
        return []
    module_df = module_df.sort_values(by=["module_score", "overlap"], ascending=[False, False])
    return deps._safe_limit(module_df, 1000).to_dict(orient="records")


@router.get("/api/exports/{dataset_id}")
def export_dataset(dataset_id: str, fmt: str = Query(default="csv")) -> Any:
    out_csv = deps._dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    if fmt == "csv":
        return FileResponse(str(out_csv), filename="target_cards.csv")
    if fmt != "json":
        raise HTTPException(status_code=400, detail="fmt must be csv or json")
    df = deps._load_cards(out_csv)
    payload = df.to_dict(orient="records")
    return JSONResponse(content={"dataset_id": dataset_id, "targets": payload})


@router.get("/api/reports/{dataset_id}")
def report_dataset(
    dataset_id: str,
    fmt: str = Query(default="html"),
    top_n: int = Query(default=50, ge=1, le=500),
) -> Any:
    job_dir = deps._dataset_path(dataset_id)
    out_csv = job_dir / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    provenance = deps._provenance_block(dataset_id)
    if fmt == "json":
        payload = build_report_payload(deps._load_cards(out_csv), dataset_id=dataset_id, top_n=top_n, provenance=provenance)
        return JSONResponse(content=payload)
    if fmt not in {"html", "md"}:
        raise HTTPException(status_code=400, detail="fmt must be html, md, or json")

    report_path = job_dir / f"target_report.{fmt}"
    write_report(out_csv, report_path, dataset_id=dataset_id, fmt=fmt, top_n=top_n, provenance=provenance)
    media_type = "text/html" if fmt == "html" else "text/markdown"
    return FileResponse(str(report_path), filename=f"target_report.{fmt}", media_type=media_type)
