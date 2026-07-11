"""Dataset build/list/status endpoints (architecture refactor Phase 4, §4.1)."""

from __future__ import annotations

import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api import deps

router = APIRouter(tags=["Build"])

# Release-freeze OF-1 resolution: the canonical reference dataset is the 39-col
# card_schema/v2 build. The legacy 31-col build is retained only as a regression
# fixture (see its DEPRECATED.md) and is flagged so clients exclude it from the
# default selection.
CANONICAL_DATASET_ID = "a6bba17b-f194-4a50-8cf8-96e03eededd6"
DEPRECATED_DATASET_IDS = {"e7ecd8d5-5463-43e3-9bf1-6e8a15d3e137"}


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
    de_stats: str = str(deps.DEFAULT_DE)
    guide_kd: str = str(deps.DEFAULT_GUIDE)
    library_metadata: str = str(deps.DEFAULT_LIB)
    clinical_benchmark: Optional[str] = str(deps.DEFAULT_BENCH)
    min_cells: int = 200
    min_de_genes: int = 50
    skip_benchmark: bool = False
    include_module_scores: bool = True
    max_rows: Optional[int] = None


def _run_script(config: TargetCardRunConfig, out_csv: Path) -> None:
    args = [
        "python",
        str(deps.DEFAULT_BUILD_SCRIPT),
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
    if deps.DEFAULT_SAMPLE_META.exists():
        args.extend(["--sample-metadata", str(deps.DEFAULT_SAMPLE_META)])
    if config.skip_benchmark or config.clinical_benchmark is None:
        args.append("--skip-benchmark")
    else:
        args.extend(["--clinical-benchmark", str(config.clinical_benchmark)])

    # Use explicit shell=False invocation for security and reproducibility.
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "target card generation failed")


@router.get("/api/datasets")
def list_datasets() -> List[Dict[str, Any]]:
    if not deps.CACHE_ROOT.exists():
        return []
    records = []
    for path in deps.CACHE_ROOT.iterdir():
        if not path.is_dir():
            continue
        out_csv = path / "target_cards.csv"
        meta = deps._read_metadata(path.name)
        if not out_csv.exists() and not meta:
            continue
        deprecated = path.name in DEPRECATED_DATASET_IDS or (path / "DEPRECATED.md").exists()
        records.append(
            {
                "dataset_id": path.name,
                "status": meta.get("status", "unknown"),
                "rows": meta.get("rows"),
                "output": meta.get("output", str(out_csv) if out_csv.exists() else ""),
                "canonical": path.name == CANONICAL_DATASET_ID,
                "deprecated": deprecated,
                "updated_at_epoch": max(
                    [p.stat().st_mtime for p in [out_csv, path / "metadata.json"] if p.exists()],
                    default=path.stat().st_mtime,
                ),
            }
        )
    # Canonical first, then non-deprecated (newest first), deprecated datasets last
    # so a default "pick the first" client never lands on the legacy schema.
    records.sort(key=lambda x: (not x["canonical"], x["deprecated"], -x["updated_at_epoch"]))
    return records


@router.post("/api/run/target-card")
def run_target_card(req: RunRequest) -> Dict[str, Any]:
    de_stats = Path(req.de_stats)
    guide_kd = Path(req.guide_kd)
    library_metadata = Path(req.library_metadata)
    deps._assert_allowed_input_path(de_stats)
    deps._assert_allowed_input_path(guide_kd)
    deps._assert_allowed_input_path(library_metadata)

    if not de_stats.exists():
        raise HTTPException(status_code=400, detail=f"de_stats file not found: {de_stats}")
    if not guide_kd.exists():
        raise HTTPException(status_code=400, detail=f"guide_kd file not found: {guide_kd}")
    if not library_metadata.exists():
        raise HTTPException(status_code=400, detail=f"library_metadata file not found: {library_metadata}")

    dataset_id = str(uuid.uuid4())
    job_dir = deps._dataset_path(dataset_id)
    out_csv = job_dir / "target_cards.csv"
    bench = None if req.skip_benchmark or not req.clinical_benchmark else Path(req.clinical_benchmark)
    if bench is not None:
        deps._assert_allowed_input_path(bench)
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
        deps._persist_metadata(
            dataset_id,
            status="failed",
            payload={"error": str(e), "params": req.dict()},
        )
        raise HTTPException(status_code=500, detail=str(e))

    cards = deps._load_cards(out_csv)
    cards = deps._normalize_cell_values(cards)
    preview_limit = int(req.max_rows) if req.max_rows and req.max_rows > 0 else 20
    metadata = {
        "dataset_id": dataset_id,
        "origin": "gwt_reference",
        "params": req.dict(),
        "rows": int(cards.shape[0]),
        "output": str(out_csv),
        "module_scores_enabled": bool(req.include_module_scores),
        "preview_limit": preview_limit,
        "data_version": deps._data_version_fingerprint([de_stats, guide_kd, library_metadata, bench, deps.DEFAULT_SAMPLE_META]),
        "dataset_version": deps.DATASET_VERSION,
    }
    preview = cards.head(preview_limit).to_dict(orient="records")
    deps._persist_metadata(dataset_id, status="completed", payload=metadata)
    return {
        "dataset_id": dataset_id,
        "status": "completed",
        "rows": int(cards.shape[0]),
        "preview": preview,
    }


@router.get("/api/status/{dataset_id}")
def get_status(dataset_id: str) -> Dict[str, Any]:
    meta = deps._read_metadata(dataset_id)
    if not meta:
        raise HTTPException(status_code=404, detail="dataset_id not found")
    return meta
