"""Cell-level ingestion and integration pipeline for h5ad/10x datasets.

This is a first-pass, reproducible scaffold for integrating GWT cell-level data
with external single-cell datasets. It intentionally keeps the workflow explicit:
load -> harmonize metadata -> QC -> concatenate -> normalize/HVG/PCA -> integrate.

For very large datasets, run with dataset-level subsetting first, then move the
same manifest/config contract to a backed/Zarr workflow.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import anndata as ad
import numpy as np
import pandas as pd
import scanpy as sc
import yaml
from scipy import sparse


REQUIRED_MANIFEST_COLUMNS = {
    "dataset_id",
    "path",
    "format",
}

SUPPORTED_FORMATS = {"h5ad", "10x_h5", "10x_mtx"}


def _read_yaml(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _read_manifest(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = REQUIRED_MANIFEST_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Manifest missing required columns: {sorted(missing)}")
    unsupported = sorted(set(df["format"].dropna()) - SUPPORTED_FORMATS)
    if unsupported:
        raise ValueError(f"Unsupported manifest format values: {unsupported}")
    return df


def _load_one(row: pd.Series) -> ad.AnnData:
    path = Path(str(row["path"]))
    fmt = str(row["format"])
    if fmt == "h5ad":
        a = ad.read_h5ad(path)
    elif fmt == "10x_h5":
        a = sc.read_10x_h5(path)
    elif fmt == "10x_mtx":
        a = sc.read_10x_mtx(path, var_names="gene_symbols", cache=False)
    else:
        raise ValueError(f"Unsupported input format: {fmt}")
    a.var_names_make_unique()
    a.obs_names_make_unique()
    return a


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def _first_existing(columns: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    column_set = set(columns)
    for candidate in candidates:
        if candidate in column_set:
            return candidate
    return None


def _standardize_var(adata: ad.AnnData, config: Dict[str, Any]) -> None:
    gene_symbol_candidates = config.get("gene_symbol_columns", ["gene_symbol", "gene_name", "features", "symbol"])
    gene_id_candidates = config.get("gene_id_columns", ["gene_id", "gene_ids", "ensembl_id", "id"])

    symbol_col = _first_existing(adata.var.columns, gene_symbol_candidates)
    id_col = _first_existing(adata.var.columns, gene_id_candidates)

    if symbol_col is None:
        adata.var["gene_symbol"] = adata.var_names.astype(str)
    else:
        adata.var["gene_symbol"] = adata.var[symbol_col].astype(str)

    if id_col is None:
        adata.var["gene_id"] = adata.var_names.astype(str)
    else:
        adata.var["gene_id"] = adata.var[id_col].astype(str)

    adata.var["gene_symbol"] = adata.var["gene_symbol"].replace({"nan": ""})
    adata.var["gene_id"] = adata.var["gene_id"].replace({"nan": ""})


def _standardize_obs(adata: ad.AnnData, row: pd.Series, config: Dict[str, Any]) -> None:
    dataset_id = str(row["dataset_id"])
    adata.obs_names = [f"{dataset_id}:{idx}" for idx in adata.obs_names.astype(str)]
    adata.obs["dataset_id"] = dataset_id

    manifest_metadata = config.get("manifest_metadata_columns", [])
    for col in manifest_metadata:
        if col in row.index and pd.notna(row[col]):
            adata.obs[col] = row[col]

    constants = config.get("obs_constants", {})
    for col, value in constants.items():
        if col not in adata.obs.columns:
            adata.obs[col] = value

    rename_map = config.get("obs_rename", {})
    present_rename = {src: dst for src, dst in rename_map.items() if src in adata.obs.columns}
    if present_rename:
        adata.obs.rename(columns=present_rename, inplace=True)

    required_obs = config.get("required_obs_columns", [])
    for col in required_obs:
        if col not in adata.obs.columns:
            adata.obs[col] = "unknown"


def _subset_obs(adata: ad.AnnData, row: pd.Series) -> ad.AnnData:
    query = row.get("obs_query", "")
    if isinstance(query, str) and query.strip():
        mask = adata.obs.eval(query)
        adata = adata[mask].copy()
    max_cells = row.get("max_cells", np.nan)
    if pd.notna(max_cells) and int(max_cells) > 0 and adata.n_obs > int(max_cells):
        rng = np.random.default_rng(0)
        idx = rng.choice(adata.n_obs, size=int(max_cells), replace=False)
        adata = adata[idx, :].copy()
    return adata


def _qc_one(adata: ad.AnnData, config: Dict[str, Any]) -> ad.AnnData:
    qc = config.get("qc", {})
    mt_prefixes = tuple(qc.get("mitochondrial_prefixes", ["MT-"]))
    adata.var["mt"] = adata.var["gene_symbol"].astype(str).str.upper().str.startswith(mt_prefixes)
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], inplace=True, percent_top=None)

    min_genes = int(qc.get("min_genes", 200))
    min_counts = int(qc.get("min_counts", 0))
    max_genes = qc.get("max_genes")
    max_counts = qc.get("max_counts")
    max_pct_mt = float(qc.get("max_pct_mt", 20))

    mask = (adata.obs["n_genes_by_counts"] >= min_genes) & (adata.obs["total_counts"] >= min_counts)
    if max_genes is not None:
        mask &= adata.obs["n_genes_by_counts"] <= int(max_genes)
    if max_counts is not None:
        mask &= adata.obs["total_counts"] <= float(max_counts)
    if "pct_counts_mt" in adata.obs.columns:
        mask &= adata.obs["pct_counts_mt"] <= max_pct_mt
    return adata[mask].copy()


def load_and_harmonize(manifest: pd.DataFrame, config: Dict[str, Any]) -> List[ad.AnnData]:
    adatas = []
    for _, row in manifest.iterrows():
        a = _load_one(row)
        _standardize_var(a, config)
        _standardize_obs(a, row, config)
        a = _subset_obs(a, row)
        if _as_bool(row.get("apply_qc", True)):
            a = _qc_one(a, config)
        if a.n_obs == 0:
            continue
        a.strings_to_categoricals()
        adatas.append(a)
    if not adatas:
        raise ValueError("No cells remained after loading and QC.")
    return adatas


def concatenate(adatas: List[ad.AnnData], config: Dict[str, Any]) -> ad.AnnData:
    concat_cfg = config.get("concat", {})
    join = concat_cfg.get("join", "inner")
    adata = ad.concat(
        adatas,
        axis=0,
        join=join,
        merge="same",
        label=None,
        index_unique=None,
    )
    adata.var_names_make_unique()
    if sparse.issparse(adata.X):
        adata.X = adata.X.tocsr()
    else:
        adata.X = sparse.csr_matrix(adata.X)
    adata.layers["counts"] = adata.X.copy()
    adata.strings_to_categoricals()
    return adata


def _preprocess_for_embedding(adata: ad.AnnData, config: Dict[str, Any]) -> None:
    pp = config.get("preprocess", {})
    batch_key = config.get("batch_key", "dataset_id")
    sc.pp.normalize_total(adata, target_sum=float(pp.get("target_sum", 1e4)))
    sc.pp.log1p(adata)
    hvg_flavor = pp.get("hvg_flavor", "seurat")
    n_hvg = int(pp.get("n_top_genes", 3000))
    if batch_key in adata.obs.columns:
        sc.pp.highly_variable_genes(adata, n_top_genes=n_hvg, flavor=hvg_flavor, batch_key=batch_key)
    else:
        sc.pp.highly_variable_genes(adata, n_top_genes=n_hvg, flavor=hvg_flavor)
    adata.raw = adata
    if bool(pp.get("subset_hvg", True)):
        adata._inplace_subset_var(adata.var["highly_variable"].to_numpy())
    sc.pp.scale(adata, max_value=float(pp.get("scale_max_value", 10)))
    sc.tl.pca(adata, n_comps=int(pp.get("n_pcs", 50)), svd_solver="arpack")


def _run_scvi(adata: ad.AnnData, config: Dict[str, Any]) -> str:
    try:
        import scvi  # type: ignore
    except ImportError as exc:
        raise ImportError("scvi-tools is required for integration.method=scvi") from exc

    batch_key = config.get("batch_key", "dataset_id")
    scvi_cfg = config.get("scvi", {})
    categorical_covariates = [c for c in scvi_cfg.get("categorical_covariates", []) if c in adata.obs.columns]
    continuous_covariates = [c for c in scvi_cfg.get("continuous_covariates", []) if c in adata.obs.columns]

    scvi.model.SCVI.setup_anndata(
        adata,
        layer="counts",
        batch_key=batch_key if batch_key in adata.obs.columns else None,
        categorical_covariate_keys=categorical_covariates or None,
        continuous_covariate_keys=continuous_covariates or None,
    )
    model = scvi.model.SCVI(adata, n_latent=int(scvi_cfg.get("n_latent", 30)))
    model.train(max_epochs=int(scvi_cfg.get("max_epochs", 100)))
    adata.obsm["X_scVI"] = model.get_latent_representation()

    model_dir = scvi_cfg.get("model_dir")
    if model_dir:
        model.save(model_dir, overwrite=True)
    return "X_scVI"


def integrate(adata: ad.AnnData, config: Dict[str, Any]) -> str:
    method = config.get("integration", {}).get("method", "none")
    batch_key = config.get("batch_key", "dataset_id")

    if method == "none":
        return "X_pca"
    if method == "combat":
        if batch_key not in adata.obs.columns:
            raise ValueError(f"batch_key not found for ComBat: {batch_key}")
        sc.pp.combat(adata, key=batch_key)
        sc.tl.pca(adata, n_comps=int(config.get("preprocess", {}).get("n_pcs", 50)), svd_solver="arpack")
        return "X_pca"
    if method == "harmony":
        if batch_key not in adata.obs.columns:
            raise ValueError(f"batch_key not found for Harmony: {batch_key}")
        try:
            import scanpy.external as sce
        except ImportError as exc:
            raise ImportError("scanpy.external/harmonypy is required for integration.method=harmony") from exc
        sce.pp.harmony_integrate(adata, key=batch_key, basis="X_pca", adjusted_basis="X_harmony")
        return "X_harmony"
    if method == "scvi":
        return _run_scvi(adata, config)
    raise ValueError(f"Unsupported integration method: {method}")


def run_embedding(adata: ad.AnnData, use_rep: str, config: Dict[str, Any]) -> None:
    emb = config.get("embedding", {})
    sc.pp.neighbors(
        adata,
        use_rep=use_rep,
        n_neighbors=int(emb.get("n_neighbors", 15)),
        n_pcs=None if use_rep != "X_pca" else int(config.get("preprocess", {}).get("n_pcs", 50)),
    )
    sc.tl.umap(adata, min_dist=float(emb.get("umap_min_dist", 0.4)))
    if bool(emb.get("run_leiden", True)):
        try:
            sc.tl.leiden(adata, resolution=float(emb.get("leiden_resolution", 0.8)), key_added="leiden")
        except ImportError as exc:
            adata.uns["leiden_warning"] = str(exc)


def summarize(adata: ad.AnnData, config: Dict[str, Any], use_rep: str) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "integration_method": config.get("integration", {}).get("method", "none"),
        "use_rep": use_rep,
        "obs_columns": list(map(str, adata.obs.columns)),
        "var_columns": list(map(str, adata.var.columns)),
        "obsm_keys": list(map(str, adata.obsm.keys())),
    }
    for col in ["dataset_id", "condition", "cell_type", "donor_id", config.get("batch_key", "dataset_id")]:
        if col in adata.obs.columns:
            counts = adata.obs[col].astype(str).value_counts().reset_index()
            counts.columns = [col, "n"]
            summary[f"{col}_counts"] = json.loads(counts.to_json(orient="records"))
    return summary


def run_pipeline(config_path: Path, manifest_path: Path, output_h5ad: Path, summary_json: Path) -> None:
    config = _read_yaml(config_path)
    manifest = _read_manifest(manifest_path)
    adatas = load_and_harmonize(manifest, config)
    adata = concatenate(adatas, config)
    _preprocess_for_embedding(adata, config)
    use_rep = integrate(adata, config)
    run_embedding(adata, use_rep, config)

    output_h5ad.parent.mkdir(parents=True, exist_ok=True)
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(output_h5ad, compression="gzip")
    summary_json.write_text(json.dumps(summarize(adata, config, use_rep), indent=2), encoding="utf-8")
    adata.obs.to_csv(output_h5ad.with_suffix(".obs.csv"))
    adata.var.to_csv(output_h5ad.with_suffix(".var.csv"))


def validate_manifest(config_path: Path, manifest_path: Path) -> Dict[str, Any]:
    config = _read_yaml(config_path)
    manifest = _read_manifest(manifest_path)
    records = []
    for _, row in manifest.iterrows():
        path = Path(str(row["path"]))
        records.append(
            {
                "dataset_id": row["dataset_id"],
                "format": row["format"],
                "path": str(path),
                "path_exists": path.exists(),
                "apply_qc": _as_bool(row.get("apply_qc", True)),
            }
        )
    return {
        "n_datasets": int(manifest.shape[0]),
        "batch_key": config.get("batch_key", "dataset_id"),
        "integration_method": config.get("integration", {}).get("method", "none"),
        "datasets": records,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cell-level ingestion and integration pipeline.")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate-manifest", help="Validate manifest/config before running.")
    validate.add_argument("--config", type=Path, required=True)
    validate.add_argument("--manifest", type=Path, required=True)

    run = sub.add_parser("run", help="Run ingestion, QC, integration, and embedding.")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--output-h5ad", type=Path, required=True)
    run.add_argument("--summary-json", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "validate-manifest":
        payload = validate_manifest(args.config, args.manifest)
        print(json.dumps(payload, indent=2))
        return
    if args.command == "run":
        run_pipeline(args.config, args.manifest, args.output_h5ad, args.summary_json)
        print(f"Wrote integrated h5ad -> {args.output_h5ad.resolve()}")
        print(f"Wrote summary -> {args.summary_json.resolve()}")
        return
    raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
