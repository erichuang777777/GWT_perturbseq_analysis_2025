"""Upload/import staging endpoints (architecture refactor Phase 4, §4.1)."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api import deps
from core.cards import adapt_generic_de, build_cards_frame
from upload.import_manager import (
    ImportPayload,
    apply_and_validate_mapping,
    approve_import,
    build_mapped_view,
    canonical_fields,
    duplicate_normalized_columns,
    list_imports,
    mark_merged,
    read_import,
    read_preview,
    read_table_preview,
    register_import,
    suggested_mapping,
)

router = APIRouter(tags=["imports"])


class ImportRequest(BaseModel):
    source_name: str
    filename: Optional[str] = None
    content_base64: Optional[str] = None
    file_path: Optional[str] = None
    declared_source_type: Optional[str] = "auto"
    mode: str = "strict"
    notes: Optional[str] = None


class ImportApprovalRequest(BaseModel):
    approved_by: str = "local_user"


class MappingRequest(BaseModel):
    map: Dict[str, Optional[str]]
    source_type: Optional[str] = None


class MergeRequest(BaseModel):
    min_cells: int = 200
    min_de_genes: int = 50
    force: bool = False


@router.post("/api/imports")
def create_import(req: ImportRequest) -> Dict[str, Any]:
    if req.mode not in {"strict", "exploratory"}:
        raise HTTPException(status_code=400, detail="mode must be strict or exploratory")
    if not req.content_base64 and not req.file_path:
        raise HTTPException(status_code=400, detail="Either content_base64 or file_path is required")
    if req.content_base64 and req.file_path:
        raise HTTPException(status_code=400, detail="Use either content_base64 or file_path, not both")

    payload = ImportPayload(
        source_name=req.source_name,
        filename=req.filename,
        content_base64=req.content_base64,
        file_path=req.file_path,
        declared_source_type=req.declared_source_type,
        mode=req.mode,
        notes=req.notes,
    )
    try:
        return register_import(deps.CACHE_ROOT, payload, allowed_roots=deps._import_allowed_roots())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/imports")
def get_imports() -> List[Dict[str, Any]]:
    return list_imports(deps.CACHE_ROOT)


@router.get("/api/imports/{import_id}")
def get_import(import_id: str) -> Dict[str, Any]:
    try:
        return read_import(deps.CACHE_ROOT, import_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/imports/{import_id}/preview")
def get_import_preview(import_id: str) -> List[Dict[str, Any]]:
    try:
        read_import(deps.CACHE_ROOT, import_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return read_preview(deps.CACHE_ROOT, import_id)


@router.post("/api/imports/{import_id}/approve")
def approve_staged_import(import_id: str, req: ImportApprovalRequest) -> Dict[str, Any]:
    try:
        return approve_import(deps.CACHE_ROOT, import_id, approved_by=req.approved_by)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/imports/{import_id}/mapping/suggestion")
def get_mapping_suggestion(import_id: str) -> Dict[str, Any]:
    meta = read_import(deps.CACHE_ROOT, import_id)
    source_type = meta.get("source_type", "unknown_table")
    if source_type in {"unknown_table", "unknown_file"}:
        source_type = "target_evidence"
    columns = meta.get("columns", [])
    return {
        "import_id": import_id,
        "source_type": source_type,
        "canonical_fields": canonical_fields(source_type),
        "uploaded_columns": columns,
        "suggested": suggested_mapping(source_type, columns),
        "duplicates": duplicate_normalized_columns(columns),
    }


@router.post("/api/imports/{import_id}/mapping")
def apply_mapping(import_id: str, req: MappingRequest) -> Dict[str, Any]:
    try:
        return apply_and_validate_mapping(deps.CACHE_ROOT, import_id, req.map, source_type=req.source_type)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/imports/{import_id}/merge")
def merge_import(import_id: str, req: MergeRequest) -> Dict[str, Any]:
    meta = read_import(deps.CACHE_ROOT, import_id)
    status = str(meta.get("merge_status", ""))
    if status == "merged_into_cards" and meta.get("merged_dataset_id") and not req.force:
        return {"dataset_id": meta["merged_dataset_id"], "status": "already_merged", "rows": meta.get("rows", 0)}
    if not status.startswith("approved"):
        raise HTTPException(status_code=400, detail=f"import must be approved before merge (status={status})")
    source_type = meta.get("source_type")
    if source_type not in {"target_evidence", "guide_evidence"}:
        raise HTTPException(status_code=400, detail=f"only target/guide evidence can be merged into cards (got {source_type})")

    source_path = Path(meta["source_path"])
    if not source_path.exists():
        raise HTTPException(status_code=400, detail=f"source file missing: {source_path}")
    deps._assert_allowed_input_path(source_path)
    try:
        full_df = read_table_preview(source_path, max_rows=1_000_000)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"could not read uploaded table: {exc}")

    mapping = (meta.get("column_mapping_override") or {}).get("map")
    if mapping:
        full_df = build_mapped_view(full_df, mapping)
    adapted = adapt_generic_de(full_df)
    try:
        cards = build_cards_frame(
            adapted,
            guide_df=None,
            lib_map=None,
            benchmark=None,
            min_cells=int(req.min_cells),
            min_de_genes=int(req.min_de_genes),
            schema="generic",
            sample_meta=None,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"card build failed: {exc}")

    dataset_id = f"usr_{import_id[:8]}_{uuid.uuid4().hex[:8]}"
    job_dir = deps._dataset_path(dataset_id)
    out_csv = job_dir / "target_cards.csv"
    cards.to_csv(out_csv, index=False)
    deps._persist_metadata(
        dataset_id,
        status="completed",
        payload={
            "dataset_id": dataset_id,
            "origin": "user_upload",
            "rows": int(cards.shape[0]),
            "output": str(out_csv),
            "data_version": deps._data_version_fingerprint([source_path]),
            "lineage": {
                "kind": "user_merge",
                "import_id": import_id,
                "source_name": meta.get("source_name"),
                "source_type": source_type,
                "context_tier": (meta.get("context_match") or {}).get("tier"),
                "column_mapping_override": meta.get("column_mapping_override"),
                "builder_schema": "generic",
                "min_cells": int(req.min_cells),
                "min_de_genes": int(req.min_de_genes),
            },
        },
    )
    mark_merged(deps.CACHE_ROOT, import_id, dataset_id)
    preview = cards.head(20).to_dict(orient="records")
    return {"dataset_id": dataset_id, "status": "completed", "rows": int(cards.shape[0]), "preview": preview}
