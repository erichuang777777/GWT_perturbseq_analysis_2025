"""Staging import utilities for target evidence and raw-cell inputs."""

from __future__ import annotations

import base64
import binascii
import json
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from common import timeutil


TABLE_EXTENSIONS = {".csv", ".tsv", ".txt", ".json", ".jsonl"}
RAW_CELL_EXTENSIONS = {".h5ad", ".h5", ".hdf5", ".mtx", ".loom", ".zarr"}
VALID_SOURCE_TYPES = {"auto", "target_evidence", "guide_evidence", "external_evidence", "metadata_manifest", "raw_cell_data"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

REQUIRED_COLUMNS: Dict[str, List[str]] = {
    "target_evidence": ["target", "condition"],
    "guide_evidence": ["guide", "target"],
    "external_evidence": ["target", "source"],
    "metadata_manifest": ["dataset_id", "file_path", "format"],
}

RECOMMENDED_COLUMNS: Dict[str, List[str]] = {
    "target_evidence": ["effect_size", "logfc", "p_value", "fdr", "n_cells", "n_guides", "n_total_de_genes"],
    "guide_evidence": ["kd_score", "guide_id", "sgrna", "fdr", "effect_size"],
    "external_evidence": ["evidence_type", "pmid", "url", "disease", "drug", "clinical_phase"],
    "metadata_manifest": ["species", "cell_type", "condition", "donor", "batch", "source"],
}

ROUTES = {
    "target_evidence": "csv_evidence_layer",
    "guide_evidence": "csv_evidence_layer",
    "external_evidence": "external_evidence_layer",
    "metadata_manifest": "metadata_harmonization_layer",
    "raw_cell_data": "raw_cell_staging",
    "unknown_table": "staging_only",
    "unknown_file": "staging_only",
}


@dataclass
class ImportPayload:
    source_name: str
    filename: Optional[str] = None
    content_base64: Optional[str] = None
    file_path: Optional[str] = None
    declared_source_type: Optional[str] = None
    mode: str = "strict"
    notes: Optional[str] = None


# Re-export for backward compatibility -- canonical implementation now lives
# in common/timeutil.py (architecture refactor Phase 1; see that module's
# docstring for the three-copy duplication this consolidates).
utc_now = timeutil.utc_now


def safe_name(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return name or "uploaded_source"


def normalize_columns(columns: List[str]) -> Dict[str, str]:
    mapping = {}
    for col in columns:
        norm = str(col).strip().lower()
        norm = re.sub(r"[^a-z0-9]+", "_", norm).strip("_")
        mapping[norm] = col
    aliases = {
        "gene": "target",
        "gene_symbol": "target",
        "target_gene": "target",
        "culture_condition": "condition",
        "padj": "fdr",
        "adj_p_value": "fdr",
        "pvalue": "p_value",
        "p_val": "p_value",
        "log_fold_change": "logfc",
        "log2fc": "logfc",
        "n_de_genes": "n_total_de_genes",
        "num_de_genes": "n_total_de_genes",
        "total_de_genes": "n_total_de_genes",
        "n_significant_genes": "n_total_de_genes",
        "guide_id": "guide",
        "sgrna": "guide",
        "donor_id": "donor",
        "batch_id": "batch",
        "lane_id": "batch",
        "pubmed_id": "pmid",
        "publication": "pmid",
    }
    for src, dst in aliases.items():
        if src in mapping and dst not in mapping:
            mapping[dst] = mapping[src]
    return mapping


def duplicate_normalized_columns(columns: List[str]) -> Dict[str, List[str]]:
    groups: Dict[str, List[str]] = {}
    for col in columns:
        norm = str(col).strip().lower()
        norm = re.sub(r"[^a-z0-9]+", "_", norm).strip("_")
        groups.setdefault(norm, []).append(str(col))
    return {key: vals for key, vals in groups.items() if key and len(vals) > 1}


def ensure_valid_declared_type(declared: Optional[str], suffix: str) -> Optional[str]:
    if not declared:
        return None
    declared_clean = declared.strip().lower()
    if not declared_clean or declared_clean == "auto":
        return None
    if declared_clean not in VALID_SOURCE_TYPES:
        raise ValueError(f"Unsupported declared_source_type: {declared}")
    if declared_clean == "raw_cell_data" and suffix not in RAW_CELL_EXTENSIONS:
        raise ValueError("raw_cell_data imports must use a raw-cell extension such as .h5ad, .h5, .mtx, .loom, or .zarr")
    if declared_clean in {"target_evidence", "guide_evidence", "external_evidence", "metadata_manifest"} and suffix not in TABLE_EXTENSIONS:
        raise ValueError(f"{declared_clean} imports must use a table extension: {', '.join(sorted(TABLE_EXTENSIONS))}")
    return declared_clean


def read_table_preview(path: Path, max_rows: int = 100) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, nrows=max_rows)
    if suffix in {".tsv", ".txt"}:
        return pd.read_csv(path, sep="\t", nrows=max_rows)
    if suffix == ".jsonl":
        return pd.read_json(path, lines=True, nrows=max_rows)
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return pd.DataFrame(data[:max_rows])
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, list):
                    return pd.DataFrame(value[:max_rows])
            return pd.DataFrame([data])
    raise ValueError(f"Unsupported preview format: {suffix}")


def infer_source_type(path: Path, columns: List[str], declared: Optional[str]) -> str:
    suffix = path.suffix.lower()
    declared_clean = ensure_valid_declared_type(declared, suffix)
    if declared_clean:
        return declared_clean

    if suffix in RAW_CELL_EXTENSIONS:
        return "raw_cell_data"

    norm = normalize_columns(columns)
    keys = set(norm)
    if {"dataset_id", "file_path", "format"}.issubset(keys):
        return "metadata_manifest"
    if {"guide", "target"}.issubset(keys):
        return "guide_evidence"
    if "target" in keys and ("condition" in keys or any(k in keys for k in ["effect_size", "logfc", "fdr", "p_value"])):
        return "target_evidence"
    if "target" in keys and any(k in keys for k in ["evidence_type", "source", "pmid", "drug", "clinical_phase", "disease"]):
        return "external_evidence"
    if suffix in TABLE_EXTENSIONS:
        return "unknown_table"
    return "unknown_file"


def value_text(df: Optional[pd.DataFrame], payload: ImportPayload) -> str:
    parts = [payload.source_name or "", payload.notes or "", payload.filename or "", payload.file_path or ""]
    if df is not None and not df.empty:
        cols = {str(c).lower(): c for c in df.columns}
        for key in ["species", "cell_type", "tissue", "condition", "assay", "platform", "perturbation_type", "source"]:
            if key in cols:
                parts.extend(df[cols[key]].dropna().astype(str).head(20).tolist())
    return " ".join(parts).lower()


def context_match_score(df: Optional[pd.DataFrame], payload: ImportPayload, source_type: str) -> Dict[str, Any]:
    text = value_text(df, payload)
    score = 0.0
    reasons = []

    if "human" in text or "homo sapiens" in text:
        score += 0.20
        reasons.append("human species")
    if "cd4" in text:
        score += 0.25
        reasons.append("CD4 context")
    elif "t cell" in text or "t-cell" in text or "lymphocyte" in text:
        score += 0.15
        reasons.append("T-cell context")
    if "primary" in text or "donor" in text or "pbmc" in text or "blood" in text:
        score += 0.10
        reasons.append("primary/donor-like context")
    if any(token in text for token in ["perturb", "crispr", "guide", "sgrna", "grna", "knockdown", "knockout"]):
        score += 0.15
        reasons.append("perturbation context")
    if any(token in text for token in ["scrna", "single cell", "single-cell", "10x", "h5ad"]):
        score += 0.10
        reasons.append("single-cell assay")
    if any(token in text for token in ["stim", "activation", "tcr", "cd3", "cd28"]):
        score += 0.10
        reasons.append("activation/stimulation context")
    if any(token in text for token in ["autoimmune", "immune", "inflammation", "cytokine"]):
        score += 0.05
        reasons.append("immune disease/function context")

    if source_type == "raw_cell_data" and not reasons:
        score += 0.05
        reasons.append("raw-cell file with unknown context")

    score = min(score, 1.0)
    if score >= 0.75:
        tier = "high_direct_context"
    elif score >= 0.50:
        tier = "compatible_context"
    elif score >= 0.25:
        tier = "indirect_context"
    else:
        tier = "low_or_unknown_context"
    return {"score": round(score, 3), "tier": tier, "reasons": reasons}


def validate_schema(source_type: str, columns: List[str], mode: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    norm = normalize_columns(columns)
    duplicates = duplicate_normalized_columns(columns)
    keys = set(norm)
    required = REQUIRED_COLUMNS.get(source_type, [])
    recommended = RECOMMENDED_COLUMNS.get(source_type, [])
    missing_required = [col for col in required if col not in keys]
    missing_recommended = [col for col in recommended if col not in keys]

    warnings = []
    blocking_issues = []
    if duplicates:
        blocking_issues.append(
            "duplicate normalized columns: "
            + "; ".join(f"{key} -> {', '.join(vals)}" for key, vals in sorted(duplicates.items()))
        )
    if missing_required:
        blocking_issues.append(f"missing required columns: {', '.join(missing_required)}")
    if missing_recommended:
        warnings.append(f"missing recommended columns: {', '.join(missing_recommended)}")
    if source_type == "unknown_table":
        warnings.append("source type could not be inferred; column mapping is required before merge")
    if source_type == "raw_cell_data":
        warnings.append("raw-cell source requires a manifest with donor, condition, batch, guide/target, and control fields before integration")
    if df is not None and not df.empty:
        for canonical in ["target", "condition", "source"]:
            if canonical in norm:
                col = norm[canonical]
                if df[col].isna().any() or (df[col].astype(str).str.strip() == "").any():
                    blocking_issues.append(f"{canonical} contains blank values in preview")
        for canonical in ["fdr", "p_value", "effect_size", "logfc", "n_cells", "n_guides"]:
            if canonical in norm:
                col = norm[canonical]
                values = pd.to_numeric(df[col], errors="coerce")
                if values.isna().any() and df[col].notna().any():
                    blocking_issues.append(f"{canonical} contains non-numeric values in preview")
    manifest_missing = []
    if source_type == "metadata_manifest":
        manifest_required_for_integration = ["species", "cell_type", "condition", "donor", "batch", "source"]
        manifest_missing = [col for col in manifest_required_for_integration if col not in keys]
        if manifest_missing:
            blocking_issues.append(
                "metadata manifest is not integration-ready; missing: " + ", ".join(manifest_missing)
            )
    if blocking_issues:
        status = "blocked"
    elif warnings:
        status = "warning"
    else:
        status = "passed"
    return {
        "status": status,
        "normalized_columns": sorted(keys),
        "column_mapping": {k: str(v) for k, v in norm.items()},
        "duplicate_normalized_columns": duplicates,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "blocking_issues": blocking_issues,
        "manifest_integration_missing": manifest_missing,
        "warnings": warnings,
    }


def canonical_fields(source_type: str) -> Dict[str, List[str]]:
    """Return required + recommended canonical fields for a source type."""
    return {
        "required": list(REQUIRED_COLUMNS.get(source_type, [])),
        "recommended": list(RECOMMENDED_COLUMNS.get(source_type, [])),
    }


def suggested_mapping(source_type: str, columns: List[str]) -> Dict[str, Optional[str]]:
    """Auto-suggest canonical<-uploaded mapping using normalize_columns aliases.

    Returns {canonical: uploaded_column_or_None} for every canonical field of the type.
    """
    norm = normalize_columns(columns)  # {normalized_or_alias: original_column}
    fields = canonical_fields(source_type)
    out: Dict[str, Optional[str]] = {}
    for canonical in fields["required"] + fields["recommended"]:
        out[canonical] = norm.get(canonical)
    return out


def build_mapped_view(df: pd.DataFrame, mapping: Dict[str, Optional[str]]) -> pd.DataFrame:
    """Rename uploaded columns to canonical names, keeping only mapped columns.

    ``mapping`` is {canonical: uploaded_column|None}. Canonical fields mapped to
    None are simply absent (they become NaN downstream, never fabricated).
    """
    rename = {up: canon for canon, up in mapping.items() if up}
    present = [up for up in rename if up in df.columns]
    view = df[present].rename(columns={c: rename[c] for c in present}).copy()
    return view


def apply_and_validate_mapping(
    cache_root: Path,
    import_id: str,
    mapping: Dict[str, Optional[str]],
    source_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist a column mapping, re-validate the mapped view, recompute merge_status."""
    metadata = read_import(cache_root, import_id)
    import_dir = cache_root / "imports" / import_id
    resolved_type = source_type or metadata.get("source_type", "unknown_table")
    if resolved_type in {"unknown_table", "unknown_file"}:
        resolved_type = "target_evidence"

    # Validate that every mapped uploaded column actually exists.
    uploaded_cols = set(metadata.get("columns", []))
    for canonical, up in mapping.items():
        if up and up not in uploaded_cols:
            raise ValueError(f"mapping references unknown uploaded column: {up}")

    source_path = Path(metadata["source_path"])
    if source_path.exists() and source_path.suffix.lower() in TABLE_EXTENSIONS:
        full_df = read_table_preview(source_path, max_rows=200)
    else:
        full_df = pd.DataFrame(read_preview(cache_root, import_id))
    mapped_df = build_mapped_view(full_df, mapping)

    schema = validate_schema(resolved_type, list(mapped_df.columns), metadata.get("mode", "strict"), df=mapped_df)
    context = metadata.get("context_match", {})

    merge_status = "staged"
    if schema["status"] == "blocked":
        merge_status = "blocked_needs_column_mapping"
    elif metadata.get("mode") == "exploratory":
        merge_status = "staged_exploratory_review_required"
    elif context.get("tier") == "low_or_unknown_context" and metadata.get("mode") == "strict":
        merge_status = "staged_low_context_review_required"

    metadata["source_type"] = resolved_type
    metadata["route"] = ROUTES.get(resolved_type, "staging_only")
    metadata["column_mapping_override"] = {
        "version": 1,
        "created_at": utc_now(),
        "source_type": resolved_type,
        "map": {k: v for k, v in mapping.items()},
    }
    metadata["schema_validation"] = schema
    metadata["merge_status"] = merge_status
    (import_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def is_within_allowed_roots(path: Path, allowed_roots: List[Path]) -> bool:
    resolved = path.resolve()
    for root in allowed_roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def write_payload_file(import_dir: Path, payload: ImportPayload, allowed_roots: Optional[List[Path]] = None) -> Path:
    if payload.content_base64:
        filename = safe_name(payload.filename or "uploaded_source")
        path = import_dir / filename
        suffix = path.suffix.lower()
        if suffix not in TABLE_EXTENSIONS:
            raise ValueError(f"Uploaded content must be a supported table file: {', '.join(sorted(TABLE_EXTENSIONS))}")
        if len(payload.content_base64) > int(MAX_UPLOAD_BYTES * 1.4):
            raise ValueError(f"Uploaded content exceeds {MAX_UPLOAD_BYTES} bytes")
        try:
            content = base64.b64decode(payload.content_base64, validate=True)
        except binascii.Error as exc:
            raise ValueError(f"Invalid base64 content: {exc}") from exc
        if len(content) > MAX_UPLOAD_BYTES:
            raise ValueError(f"Uploaded content exceeds {MAX_UPLOAD_BYTES} bytes")
        path.write_bytes(content)
        return path

    if payload.file_path:
        path = Path(payload.file_path)
        if not path.exists():
            raise FileNotFoundError(f"file_path not found: {payload.file_path}")
        if allowed_roots and not is_within_allowed_roots(path, allowed_roots):
            allowed = ", ".join(str(root.resolve()) for root in allowed_roots)
            raise PermissionError(f"file_path must be under an allowed import root: {allowed}")
        return path

    raise ValueError("Either content_base64 or file_path is required")


def register_import(cache_root: Path, payload: ImportPayload, allowed_roots: Optional[List[Path]] = None) -> Dict[str, Any]:
    import_id = str(uuid.uuid4())
    imports_root = cache_root / "imports"
    import_dir = imports_root / import_id
    import_dir.mkdir(parents=True, exist_ok=True)

    try:
        source_path = write_payload_file(import_dir, payload, allowed_roots=allowed_roots)
    except Exception:
        if import_dir.exists():
            for child in import_dir.iterdir():
                if child.is_file():
                    child.unlink()
            import_dir.rmdir()
        raise
    suffix = source_path.suffix.lower()
    file_size = source_path.stat().st_size if source_path.exists() and source_path.is_file() else None
    columns: List[str] = []
    preview_records: List[Dict[str, Any]] = []
    table_shape: Optional[List[int]] = None
    preview_error: Optional[str] = None
    preview_df: Optional[pd.DataFrame] = None

    if suffix in TABLE_EXTENSIONS:
        try:
            preview_df = read_table_preview(source_path, max_rows=100)
            columns = [str(c) for c in preview_df.columns]
            table_shape = [int(preview_df.shape[0]), int(preview_df.shape[1])]
            preview_records = json.loads(preview_df.head(25).where(pd.notna(preview_df), None).to_json(orient="records"))
            (import_dir / "preview.json").write_text(json.dumps(preview_records, indent=2), encoding="utf-8")
        except Exception as exc:
            preview_error = str(exc)

    try:
        source_type = infer_source_type(source_path, columns, payload.declared_source_type)
    except Exception:
        if import_dir.exists() and not (import_dir / "metadata.json").exists():
            shutil.rmtree(import_dir)
        raise
    schema = validate_schema(source_type, columns, payload.mode, df=preview_df)
    context = context_match_score(preview_df, payload, source_type)
    route = ROUTES.get(source_type, "staging_only")

    merge_status = "staged"
    if schema["status"] == "blocked":
        merge_status = "blocked_needs_column_mapping"
    elif source_type in {"unknown_table", "unknown_file"}:
        merge_status = "staged_needs_classification"
    elif payload.mode == "exploratory":
        merge_status = "staged_exploratory_review_required"
    elif context["tier"] == "low_or_unknown_context" and payload.mode == "strict":
        merge_status = "staged_low_context_review_required"
    elif source_type == "raw_cell_data":
        merge_status = "staged_manifest_required"

    metadata = {
        "import_id": import_id,
        "created_at": utc_now(),
        "source_name": payload.source_name,
        "source_type": source_type,
        "declared_source_type": payload.declared_source_type or "auto",
        "mode": payload.mode,
        "notes": payload.notes,
        "route": route,
        "merge_status": merge_status,
        "filename": source_path.name,
        "source_path": str(source_path),
        "stored_copy": bool(payload.content_base64),
        "file_size_bytes": file_size,
        "columns": columns,
        "table_preview_shape": table_shape,
        "preview_error": preview_error,
        "schema_validation": schema,
        "context_match": context,
    }
    (import_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def list_imports(cache_root: Path) -> List[Dict[str, Any]]:
    imports_root = cache_root / "imports"
    if not imports_root.exists():
        return []
    records = []
    for path in imports_root.iterdir():
        meta_path = path / "metadata.json"
        if not meta_path.exists():
            continue
        records.append(json.loads(meta_path.read_text(encoding="utf-8")))
    return sorted(records, key=lambda row: row.get("created_at", ""), reverse=True)


def read_import(cache_root: Path, import_id: str) -> Dict[str, Any]:
    meta_path = cache_root / "imports" / import_id / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"import_id not found: {import_id}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def read_preview(cache_root: Path, import_id: str) -> List[Dict[str, Any]]:
    preview_path = cache_root / "imports" / import_id / "preview.json"
    if not preview_path.exists():
        return []
    return json.loads(preview_path.read_text(encoding="utf-8"))


def approve_import(cache_root: Path, import_id: str, approved_by: str = "local_user") -> Dict[str, Any]:
    metadata = read_import(cache_root, import_id)
    if metadata["merge_status"] != "staged":
        raise ValueError(
            "only clean staged imports can be approved; resolve classification, context, manifest, or schema issues first"
        )
    schema = metadata.get("schema_validation", {})
    if schema.get("status") == "blocked" or schema.get("blocking_issues"):
        raise ValueError("schema blocking issues must be resolved before approval")
    metadata["merge_status"] = "approved_for_downstream_use"
    metadata["approved_at"] = utc_now()
    metadata["approved_by"] = approved_by
    meta_path = cache_root / "imports" / import_id / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def mark_merged(cache_root: Path, import_id: str, dataset_id: str) -> Dict[str, Any]:
    """Stamp the merged dataset id back onto the import so the loop is closed/traceable."""
    metadata = read_import(cache_root, import_id)
    metadata["merge_status"] = "merged_into_cards"
    metadata["merged_dataset_id"] = dataset_id
    metadata["merged_at"] = utc_now()
    meta_path = cache_root / "imports" / import_id / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
