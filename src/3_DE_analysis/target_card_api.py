"""Minimal FastAPI service for CD4 Perturb-seq target-card generation."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from generate_target_report import build_report_payload, write_report
from build_target_cards import adapt_generic_de, build_cards_frame
from readiness_engine import compute_readiness, load_overlays, readiness_summary
from build_target_cards import load_gene_set
from calibration import run_calibration
from external_evidence_cache import build_evidence_for_genes, load_snapshot as load_evidence_snapshot
from disease_translator import list_diseases, load_disease_associations, translate_disease
from import_manager import (
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
    utc_now,
)


ROOT = Path(__file__).resolve().parents[2]
SRC = Path(__file__).resolve().parent
DEFAULT_DE = ROOT / "metadata" / "suppl_tables" / "DE_stats.suppl_table.csv"
DEFAULT_GUIDE = ROOT / "metadata" / "suppl_tables" / "guide_kd_efficiency.suppl_table.csv"
DEFAULT_LIB = ROOT / "metadata" / "suppl_tables" / "sgrna_library_metadata.suppl_table.csv"
DEFAULT_BENCH = ROOT / "sources" / "topic05_successful_drug_benchmarks.csv"
SEED_MODULES = ROOT / "sources" / "topic15_cd4_tcell_upstream_downstream_seed_modules.csv"
CACHE_ROOT = ROOT / "sources" / "target_tool_cache"
DEFAULT_BUILD_SCRIPT = SRC / "build_target_cards.py"
DEFAULT_SAMPLE_META = ROOT / "metadata" / "suppl_tables" / "sample_metadata.suppl_table.csv"
GENE_LISTS_DIR = ROOT / "metadata" / "gene_lists"
DEFAULT_ESSENTIALS = GENE_LISTS_DIR / "core_essentials_hart.tsv"
DEFAULT_BROAD_EFFECT = ROOT / "sources" / "broad_effect_genes.txt"
EVIDENCE_CACHE_DIR = CACHE_ROOT / "_evidence"
DISEASE_ASSOCIATIONS_PATH = ROOT / "src" / "6_functional_interaction" / "results" / "disease_gene_associations_detailed.csv"


def _disease_associations():
    return load_disease_associations(DISEASE_ASSOCIATIONS_PATH)

# Bump whenever build_target_cards.py, readiness_engine.py, calibration.py, or
# external_evidence_cache.py change scoring/engine behavior, so every dataset's
# provenance footer can say exactly which engine produced it.
ENGINE_VERSION = "1.3.0"  # wave 3: readiness engine + real batch flag + upload merge loop (1.0-1.2) + external evidence (1.3)


def _data_version_fingerprint(paths: List[Path]) -> str:
    """Deterministic fingerprint of input file identity: name + mtime + size, joined."""
    parts = []
    for path in paths:
        if path and Path(path).exists():
            stat = Path(path).stat()
            parts.append(f"{Path(path).name}@{int(stat.st_mtime)}:{stat.st_size}")
    return ";".join(parts) if parts else "unknown"


def _overlays():
    return load_overlays(GENE_LISTS_DIR)


def _essentials():
    return load_gene_set(DEFAULT_ESSENTIALS)


def _broad_effect_genes():
    return load_gene_set(DEFAULT_BROAD_EFFECT)


def _import_allowed_roots() -> List[Path]:
    raw = os.getenv("GWT_IMPORT_ALLOW_ROOTS", "")
    roots = [ROOT]
    for token in raw.split(";"):
        token = token.strip()
        if token:
            roots.append(Path(token))
    return roots


def _assert_allowed_input_path(path: Path) -> None:
    resolved = path.resolve()
    for root in _import_allowed_roots():
        try:
            resolved.relative_to(root.resolve())
            return
        except ValueError:
            continue
    allowed = ", ".join(str(root.resolve()) for root in _import_allowed_roots())
    raise HTTPException(status_code=403, detail=f"input path must be under an allowed root: {allowed}")


@dataclass
class TargetCardRunConfig:
    de_stats: Path
    guide_kd: Path
    library_metadata: Path
    clinical_benchmark: Optional[Path]
    min_cells: int = 200
    min_de: int = 50
    skip_benchmark: bool = False


class RunRequest(BaseModel):
    de_stats: str = str(DEFAULT_DE)
    guide_kd: str = str(DEFAULT_GUIDE)
    library_metadata: str = str(DEFAULT_LIB)
    clinical_benchmark: Optional[str] = str(DEFAULT_BENCH)
    min_cells: int = 200
    min_de_genes: int = 50
    skip_benchmark: bool = False
    include_module_scores: bool = True
    max_rows: Optional[int] = None


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


class EvidenceBuildRequest(BaseModel):
    dataset_id: Optional[str] = None
    genes: Optional[List[str]] = None
    top_n: int = 20
    force: bool = False


app = FastAPI(title="GWT Target Card API", version="0.1.0")


def _dataset_path(dataset_id: str) -> Path:
    path = CACHE_ROOT / dataset_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _run_script(config: TargetCardRunConfig, out_csv: Path) -> None:
    args = [
        "python",
        str(DEFAULT_BUILD_SCRIPT),
        "--de-stats",
        str(config.de_stats),
        "--guide-kd",
        str(config.guide_kd),
        "--library-metadata",
        str(config.library_metadata),
        "--output",
        str(out_csv),
        "--min-cells",
        str(config.min_cells),
        "--min-de",
        str(config.min_de),
    ]
    if DEFAULT_SAMPLE_META.exists():
        args.extend(["--sample-metadata", str(DEFAULT_SAMPLE_META)])
    if config.skip_benchmark or config.clinical_benchmark is None:
        args.append("--skip-benchmark")
    else:
        args.extend(["--clinical-benchmark", str(config.clinical_benchmark)])

    # Use explicit shell=False invocation for security and reproducibility.
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "target card generation failed")


def _load_cards(out_csv: Path) -> pd.DataFrame:
    if not out_csv.exists():
        raise FileNotFoundError(f"Target cards file not found: {out_csv}")
    return pd.read_csv(out_csv)


def _normalize_cell_values(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["ontarget_significant", "offtarget_flag", "replicate_pass_flag"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().isin({"true", "1", "yes", "y"})
    for col in [
        "n_cells_target",
        "n_guides",
        "n_total_de_genes",
        "n_up_genes",
        "n_down_genes",
        "crossdonor_correlation_mean",
        "crossdonor_correlation_min",
        "crossguide_correlation",
        "condition_specificity_score",
        "statistical_evidence_grade",
        "positive_control_similarity",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _load_modules() -> Dict[str, List[str]]:
    modules: Dict[str, List[str]] = {}
    if not SEED_MODULES.exists():
        return modules
    with open(SEED_MODULES, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            genes = row.get("seed_genes", "")
            gene_list = [g.strip() for g in genes.split(",") if g.strip()]
            modules[row.get("module_id", f"module_{row.get('module_name', '')}")] = gene_list
    return modules


def _module_scores(df: pd.DataFrame) -> pd.DataFrame:
    modules = _load_modules()
    if not modules:
        return pd.DataFrame(columns=["target", "condition", "module_id", "module_name", "overlap", "module_score"])

    module_records = []
    module_names = {}
    with open(SEED_MODULES, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            module_names[row["module_id"]] = row["module_name"]

    for _, row in df.iterrows():
        target = row["target"]
        target_gene = str(target).strip().upper()
        condition = row["condition"] if "condition" in df.columns else row.get("culture_condition", "")
        score_basis = float(row.get("condition_specificity_score", 0) or 0)
        for module_id, genes in modules.items():
            module_genes = {g.strip().upper() for g in genes if g.strip()}
            overlap = 1 if target_gene in module_genes else 0
            if overlap == 0:
                continue
            module_score = overlap * (1.0 + score_basis)
            module_records.append(
                {
                    "target": target,
                    "condition": condition,
                    "module_id": module_id,
                    "module_name": module_names.get(module_id, module_id),
                    "overlap": overlap,
                    "module_score": module_score,
                }
            )
    return pd.DataFrame(module_records)


def _persist_metadata(dataset_id: str, status: str, payload: Dict[str, Any]) -> None:
    path = _dataset_path(dataset_id) / "metadata.json"
    data = {
        "dataset_id": dataset_id,
        "status": status,
        "engine_version": ENGINE_VERSION,
        "built_at": utc_now(),
    }
    data.update(payload)  # payload may override engine_version/built_at/data_version if the caller sets them explicitly
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _read_metadata(dataset_id: str) -> Dict[str, Any]:
    path = _dataset_path(dataset_id) / "metadata.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_limit(df: pd.DataFrame, max_rows: Optional[int]) -> pd.DataFrame:
    if max_rows is None or max_rows <= 0:
        return df
    return df.head(max_rows).copy()


def _json_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    return json.loads(df.where(pd.notna(df), None).to_json(orient="records"))


def _json_object(payload: Dict[str, Any]) -> Dict[str, Any]:
    return json.loads(pd.Series(payload).to_json())


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/datasets")
def list_datasets() -> List[Dict[str, Any]]:
    if not CACHE_ROOT.exists():
        return []
    records = []
    for path in CACHE_ROOT.iterdir():
        if not path.is_dir():
            continue
        out_csv = path / "target_cards.csv"
        meta = _read_metadata(path.name)
        if not out_csv.exists() and not meta:
            continue
        records.append(
            {
                "dataset_id": path.name,
                "status": meta.get("status", "unknown"),
                "rows": meta.get("rows"),
                "output": meta.get("output", str(out_csv) if out_csv.exists() else ""),
                "updated_at_epoch": max(
                    [p.stat().st_mtime for p in [out_csv, path / "metadata.json"] if p.exists()],
                    default=path.stat().st_mtime,
                ),
            }
        )
    return sorted(records, key=lambda x: x["updated_at_epoch"], reverse=True)


@app.post("/api/imports")
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
        return register_import(CACHE_ROOT, payload, allowed_roots=_import_allowed_roots())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/imports")
def get_imports() -> List[Dict[str, Any]]:
    return list_imports(CACHE_ROOT)


@app.get("/api/imports/{import_id}")
def get_import(import_id: str) -> Dict[str, Any]:
    try:
        return read_import(CACHE_ROOT, import_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/api/imports/{import_id}/preview")
def get_import_preview(import_id: str) -> List[Dict[str, Any]]:
    try:
        read_import(CACHE_ROOT, import_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return read_preview(CACHE_ROOT, import_id)


@app.post("/api/imports/{import_id}/approve")
def approve_staged_import(import_id: str, req: ImportApprovalRequest) -> Dict[str, Any]:
    try:
        return approve_import(CACHE_ROOT, import_id, approved_by=req.approved_by)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/imports/{import_id}/mapping/suggestion")
def get_mapping_suggestion(import_id: str) -> Dict[str, Any]:
    meta = read_import(CACHE_ROOT, import_id)
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


@app.post("/api/imports/{import_id}/mapping")
def apply_mapping(import_id: str, req: MappingRequest) -> Dict[str, Any]:
    try:
        return apply_and_validate_mapping(CACHE_ROOT, import_id, req.map, source_type=req.source_type)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/imports/{import_id}/merge")
def merge_import(import_id: str, req: MergeRequest) -> Dict[str, Any]:
    meta = read_import(CACHE_ROOT, import_id)
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
    _assert_allowed_input_path(source_path)
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
    job_dir = _dataset_path(dataset_id)
    out_csv = job_dir / "target_cards.csv"
    cards.to_csv(out_csv, index=False)
    _persist_metadata(
        dataset_id,
        status="completed",
        payload={
            "dataset_id": dataset_id,
            "origin": "user_upload",
            "rows": int(cards.shape[0]),
            "output": str(out_csv),
            "data_version": _data_version_fingerprint([source_path]),
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
    mark_merged(CACHE_ROOT, import_id, dataset_id)
    preview = cards.head(20).to_dict(orient="records")
    return {"dataset_id": dataset_id, "status": "completed", "rows": int(cards.shape[0]), "preview": preview}


def _evidence_dir_mtime() -> float:
    if not EVIDENCE_CACHE_DIR.exists():
        return 0.0
    mtimes = [p.stat().st_mtime for p in EVIDENCE_CACHE_DIR.glob("*.json")]
    return max(mtimes, default=0.0)


@app.get("/api/readiness/{dataset_id}")
def get_readiness(dataset_id: str, refresh: bool = Query(default=False)) -> Dict[str, Any]:
    out_csv = _dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    readiness_csv = _dataset_path(dataset_id) / "readiness.csv"
    overlays = _overlays()
    stale = (
        refresh
        or not readiness_csv.exists()
        or readiness_csv.stat().st_mtime < out_csv.stat().st_mtime
        or readiness_csv.stat().st_mtime < _evidence_dir_mtime()
    )
    if stale:
        cards = _normalize_cell_values(_load_cards(out_csv))
        readiness = compute_readiness(
            cards,
            overlays=overlays,
            essentials=_essentials(),
            broad_effect_genes=_broad_effect_genes(),
            evidence_dir=EVIDENCE_CACHE_DIR,
        )
        readiness.to_csv(readiness_csv, index=False)
    else:
        readiness = pd.read_csv(readiness_csv)
    return {
        "dataset_id": dataset_id,
        **readiness_summary(readiness, overlays=overlays),
        "readiness": _json_records(readiness),
    }


@app.get("/api/evidence/{gene}")
def get_evidence(gene: str) -> Dict[str, Any]:
    snapshot = load_evidence_snapshot(EVIDENCE_CACHE_DIR, gene)
    if snapshot is None:
        raise HTTPException(status_code=404, detail=f"no evidence snapshot fetched yet for {gene}")
    return snapshot


# Hard cap on how many genes one build request may schedule, so a single call
# can never fan out into an unbounded number of external HTTP fetches.
MAX_EVIDENCE_GENES = 50


@app.post("/api/evidence/build")
def build_evidence(req: EvidenceBuildRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    genes = list(req.genes or [])
    if req.dataset_id:
        out_csv = _dataset_path(req.dataset_id) / "target_cards.csv"
        if not out_csv.exists():
            raise HTTPException(status_code=404, detail="dataset_id not found")
        df = _load_cards(out_csv)
        df = df.sort_values(
            by=[c for c in ["statistical_evidence_grade", "n_total_de_genes"] if c in df.columns],
            ascending=False,
        )
        genes.extend(df["target"].dropna().astype(str).str.upper().unique().tolist()[: req.top_n])
    genes = list(dict.fromkeys(g.upper() for g in genes if g))[:MAX_EVIDENCE_GENES]
    if not genes:
        raise HTTPException(status_code=400, detail="no genes to build evidence for (pass dataset_id or genes)")

    # Report what is already cached synchronously (no network); schedule only the
    # missing/forced genes as a BACKGROUND task so the request returns promptly
    # and external fetches never block the HTTP response (external_evidence_cache
    # is designed as an offline batch job, not a request-path call).
    cached: Dict[str, Any] = {}
    to_fetch = []
    for gene in genes:
        snap = load_evidence_snapshot(EVIDENCE_CACHE_DIR, gene)
        if snap is not None and not req.force:
            cached[gene] = {name: src.get("source_status") for name, src in snap.get("sources", {}).items()}
        else:
            to_fetch.append(gene)

    if to_fetch:
        background_tasks.add_task(build_evidence_for_genes, to_fetch, EVIDENCE_CACHE_DIR, force=req.force)

    return {
        "genes": genes,
        "cache_dir": str(EVIDENCE_CACHE_DIR),
        "cached": cached,
        "scheduled": to_fetch,
        "note": "scheduled genes are fetched in the background; poll GET /api/evidence/{gene} for results",
    }


@app.get("/api/calibration/{dataset_id}")
def get_calibration(dataset_id: str, refresh: bool = Query(default=False)) -> Dict[str, Any]:
    out_csv = _dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    calib_json = _dataset_path(dataset_id) / "calibration.json"
    if refresh or not calib_json.exists() or calib_json.stat().st_mtime < out_csv.stat().st_mtime:
        cards = _normalize_cell_values(_load_cards(out_csv))
        report = run_calibration(cards)
        calib_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    else:
        report = json.loads(calib_json.read_text(encoding="utf-8"))
    return {"dataset_id": dataset_id, **report}


@app.get("/api/disease")
def get_diseases() -> Dict[str, Any]:
    associations = _disease_associations()
    return {
        "source": str(DISEASE_ASSOCIATIONS_PATH.relative_to(ROOT)) if DISEASE_ASSOCIATIONS_PATH.exists() else None,
        "diseases": list_diseases(associations),
    }


@app.get("/api/disease/{disease_name}/targets/{dataset_id}")
def get_disease_targets(
    disease_name: str,
    dataset_id: str,
    min_grade: int = Query(default=2, ge=1, le=4),
    top_n: int = Query(default=50, ge=1, le=500),
) -> Dict[str, Any]:
    out_csv = _dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    cards = _normalize_cell_values(_load_cards(out_csv))
    associations = _disease_associations()

    readiness_csv = _dataset_path(dataset_id) / "readiness.csv"
    readiness_df = pd.read_csv(readiness_csv) if readiness_csv.exists() else None

    result = translate_disease(cards, disease_name, associations, readiness=readiness_df, min_grade=min_grade, top_n=top_n)
    return {"dataset_id": dataset_id, "disease_name": disease_name, **result}


@app.post("/api/run/target-card")
def run_target_card(req: RunRequest) -> Dict[str, Any]:
    de_stats = Path(req.de_stats)
    guide_kd = Path(req.guide_kd)
    library_metadata = Path(req.library_metadata)
    _assert_allowed_input_path(de_stats)
    _assert_allowed_input_path(guide_kd)
    _assert_allowed_input_path(library_metadata)

    if not de_stats.exists():
        raise HTTPException(status_code=400, detail=f"de_stats file not found: {de_stats}")
    if not guide_kd.exists():
        raise HTTPException(status_code=400, detail=f"guide_kd file not found: {guide_kd}")
    if not library_metadata.exists():
        raise HTTPException(status_code=400, detail=f"library_metadata file not found: {library_metadata}")

    dataset_id = str(uuid.uuid4())
    job_dir = _dataset_path(dataset_id)
    out_csv = job_dir / "target_cards.csv"
    bench = None if req.skip_benchmark or not req.clinical_benchmark else Path(req.clinical_benchmark)
    if bench is not None:
        _assert_allowed_input_path(bench)
    if bench is not None and not bench.exists():
        raise HTTPException(status_code=400, detail=f"clinical benchmark file not found: {bench}")

    config = TargetCardRunConfig(
        de_stats=de_stats,
        guide_kd=guide_kd,
        library_metadata=library_metadata,
        clinical_benchmark=bench,
        min_cells=int(req.min_cells),
        min_de=int(req.min_de_genes),
        skip_benchmark=req.skip_benchmark,
    )

    try:
        _run_script(config, out_csv)
    except RuntimeError as e:
        _persist_metadata(
            dataset_id,
            status="failed",
            payload={"error": str(e), "params": req.dict()},
        )
        raise HTTPException(status_code=500, detail=str(e))

    cards = _load_cards(out_csv)
    cards = _normalize_cell_values(cards)
    preview_limit = int(req.max_rows) if req.max_rows and req.max_rows > 0 else 20
    metadata = {
        "dataset_id": dataset_id,
        "origin": "gwt_reference",
        "params": req.dict(),
        "rows": int(cards.shape[0]),
        "output": str(out_csv),
        "module_scores_enabled": bool(req.include_module_scores),
        "preview_limit": preview_limit,
        "data_version": _data_version_fingerprint([de_stats, guide_kd, library_metadata, bench, DEFAULT_SAMPLE_META]),
    }
    preview = cards.head(preview_limit).to_dict(orient="records")
    _persist_metadata(dataset_id, status="completed", payload=metadata)
    return {
        "dataset_id": dataset_id,
        "status": "completed",
        "rows": int(cards.shape[0]),
        "preview": preview,
    }


@app.get("/api/targets/{dataset_id}")
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
    out_csv = _dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")

    df = _normalize_cell_values(_load_cards(out_csv))
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
    df = _safe_limit(df, max_rows)
    return _json_records(df)


@app.get("/api/summary/{dataset_id}")
def summarize_dataset(dataset_id: str, top_n: int = Query(default=50, ge=1, le=500)) -> Dict[str, Any]:
    out_csv = _dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    return build_report_payload(_load_cards(out_csv), dataset_id=dataset_id, top_n=top_n)


@app.get("/api/options/{dataset_id}")
def dataset_options(dataset_id: str) -> Dict[str, Any]:
    out_csv = _dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    df = _normalize_cell_values(_load_cards(out_csv))

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


@app.get("/api/targets/{dataset_id}/{target_id}")
def get_target(dataset_id: str, target_id: str) -> Dict[str, Any]:
    out_csv = _dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    df = _normalize_cell_values(_load_cards(out_csv))
    target_rows = df[df["target"] == target_id]
    if target_rows.empty:
        raise HTTPException(status_code=404, detail=f"target not found: {target_id}")
    row = target_rows.iloc[0].to_dict()
    return {"target": target_id, "rows": _json_records(target_rows), "summary": _json_object(row)}


@app.get("/api/modules/{dataset_id}")
def get_module_scores(dataset_id: str) -> List[Dict[str, Any]]:
    out_csv = _dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    meta = _read_metadata(dataset_id)
    if meta and meta.get("module_scores_enabled") is False:
        return []
    df = _normalize_cell_values(_load_cards(out_csv))
    module_df = _module_scores(df)
    if module_df.empty:
        return []
    module_df = module_df.sort_values(by=["module_score", "overlap"], ascending=[False, False])
    return _safe_limit(module_df, 1000).to_dict(orient="records")


@app.get("/api/exports/{dataset_id}")
def export_dataset(dataset_id: str, fmt: str = Query(default="csv")) -> Any:
    out_csv = _dataset_path(dataset_id) / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    if fmt == "csv":
        return FileResponse(str(out_csv), filename="target_cards.csv")
    if fmt != "json":
        raise HTTPException(status_code=400, detail="fmt must be csv or json")
    df = _load_cards(out_csv)
    payload = df.to_dict(orient="records")
    return JSONResponse(content={"dataset_id": dataset_id, "targets": payload})


@app.get("/api/reports/{dataset_id}")
def report_dataset(
    dataset_id: str,
    fmt: str = Query(default="html"),
    top_n: int = Query(default=50, ge=1, le=500),
) -> Any:
    job_dir = _dataset_path(dataset_id)
    out_csv = job_dir / "target_cards.csv"
    if not out_csv.exists():
        raise HTTPException(status_code=404, detail="dataset_id not found")
    if fmt == "json":
        payload = build_report_payload(_load_cards(out_csv), dataset_id=dataset_id, top_n=top_n)
        return JSONResponse(content=payload)
    if fmt not in {"html", "md"}:
        raise HTTPException(status_code=400, detail="fmt must be html, md, or json")

    report_path = job_dir / f"target_report.{fmt}"
    write_report(out_csv, report_path, dataset_id=dataset_id, fmt=fmt, top_n=top_n)
    media_type = "text/html" if fmt == "html" else "text/markdown"
    return FileResponse(str(report_path), filename=f"target_report.{fmt}", media_type=media_type)


@app.get("/api/status/{dataset_id}")
def get_status(dataset_id: str) -> Dict[str, Any]:
    meta = _read_metadata(dataset_id)
    if not meta:
        raise HTTPException(status_code=404, detail="dataset_id not found")
    return meta
