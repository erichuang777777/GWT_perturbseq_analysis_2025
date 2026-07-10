"""Cell-level perturbation-response analysis for the GWT ``*.assigned_guide.h5ad`` files.

Implements the "Next Extensions" named in this directory's README:
    - guide assignment QC report
    - Mixscape-style perturbation-response detection (responder vs escaper cells)
    - SCEPTRE integration hook (honest external hook, not a reimplementation)
    - UCell/AUCell-style CD4 module scoring
    - bridge integrated cell-state evidence back into target cards

See ``RUN_ON_REAL_DATA.md`` in this directory for the exact commands to run
once the real files are downloaded (they are NOT present in this repo/session
-- see that file for why and what to do instead).

Real per-cell schema (from ``metadata/data_sharing_readme.md``, "Cell-level
data" section) -- one file per donor x condition, e.g. ``D1_Rest.assigned_guide.h5ad``:

    .obs: lane_id, n_genes_by_counts, total_counts, pct_counts_mt,
          top_guide_UMI_counts, guide_id, perturbed_gene_name,
          perturbed_gene_id, guide_type ("targeting"/"non-targeting"),
          PuroR, guide_group, low_quality
    .var: gene_ids, feature_types, genome, gene_name, mt
    .X:   sparse UMI counts

Donor and culture_condition are NOT columns in the file -- they are encoded
in the filename. ``load_donor_condition_h5ad`` injects them as obs columns so
every downstream function can group by donor/condition uniformly.

Scale note: the smallest real file is ~131 GiB. Every function that touches
``.X`` here is written to work against a **backed** AnnData
(``anndata.read_h5ad(path, backed="r")``) and only materializes small,
explicitly-bounded slices into memory (per-target cell subsets, or an
explicit ``max_cells`` subsample) -- never the whole file at once.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

try:
    import anndata as ad
except ImportError:  # pragma: no cover
    ad = None

try:
    import scanpy as sc
except ImportError:  # pragma: no cover
    sc = None

REQUIRED_OBS_COLUMNS = [
    "lane_id",
    "guide_id",
    "perturbed_gene_name",
    "guide_type",
]
CONTROL_GUIDE_TYPE = "non-targeting"
TARGETING_GUIDE_TYPE = "targeting"


def _require_deps() -> None:
    if ad is None or sc is None:
        raise ImportError(
            "perturbation_response_analysis requires anndata and scanpy "
            "(pip install anndata scanpy) -- not needed for the CSV-first "
            "target-card toolkit, only for this cell-level extension."
        )


# --------------------------------------------------------------------------
# Loading + schema validation (donor/condition are filename-encoded, not obs columns)
# --------------------------------------------------------------------------


def load_donor_condition_h5ad(
    path: Path,
    donor_id: Optional[str] = None,
    culture_condition: Optional[str] = None,
    backed: Optional[str] = "r",
) -> "ad.AnnData":
    """Load one ``D{n}_{condition}.assigned_guide.h5ad`` file in backed mode.

    If ``donor_id``/``culture_condition`` are not given, they are parsed from
    the filename (``D1_Rest.assigned_guide.h5ad`` -> donor_id="D1",
    culture_condition="Rest"), matching the real GWT filename convention
    documented in metadata/data_sharing_readme.md.
    """
    _require_deps()
    path = Path(path)
    if donor_id is None or culture_condition is None:
        stem = path.name.split(".")[0]  # "D1_Rest"
        parts = stem.split("_", 1)
        donor_id = donor_id or (parts[0] if parts else "unknown")
        culture_condition = culture_condition or (parts[1] if len(parts) > 1 else "unknown")

    adata = ad.read_h5ad(path, backed=backed)
    adata.obs["donor_id"] = donor_id
    adata.obs["culture_condition"] = culture_condition
    return adata


def validate_schema(adata: "ad.AnnData") -> List[str]:
    """Return schema problems (empty list = valid). Never raises."""
    problems = []
    missing = [c for c in REQUIRED_OBS_COLUMNS if c not in adata.obs.columns]
    if missing:
        problems.append(f"obs missing required columns: {missing}")
    if adata.n_obs == 0:
        problems.append("zero cells")
    guide_types = set(adata.obs.get("guide_type", pd.Series(dtype=str)).astype(str).unique())
    if CONTROL_GUIDE_TYPE not in guide_types:
        problems.append(f"no '{CONTROL_GUIDE_TYPE}' control cells found (guide_type values seen: {sorted(guide_types)[:10]})")
    return problems


def build_synthetic_adata(
    n_cells_per_target: int = 150,
    targets: Optional[List[str]] = None,
    n_background_genes: int = 50,
    responder_fraction: float = 0.6,
    effect_size: float = 3.0,
    donor_id: str = "D1",
    culture_condition: str = "Rest",
    seed: int = 0,
) -> "ad.AnnData":
    """Build a small synthetic AnnData matching the REAL per-file schema, for testing.

    Simulates non-targeting-control cells plus a handful of targets, each with
    a KNOWN ground-truth responder fraction, so the classifier can be checked
    against a known answer instead of only checked for "runs without crashing."
    Column names match metadata/data_sharing_readme.md exactly.
    """
    _require_deps()
    rng = np.random.default_rng(seed)
    targets = targets or ["ZAP70", "PLCG1", "MED12"]
    genes = [f"GENE{i}" for i in range(n_background_genes)] + targets + ["CD3E", "IL2RA"]
    n_genes = len(genes)

    guide_names = ["NTC"] * (n_cells_per_target * 2) + [t for t in targets for _ in range(n_cells_per_target)]
    guide_types = [CONTROL_GUIDE_TYPE if g == "NTC" else TARGETING_GUIDE_TYPE for g in guide_names]

    X = rng.negative_binomial(5, 0.5, size=(len(guide_names), n_genes)).astype(float)
    ground_truth_responder = np.zeros(len(guide_names), dtype=bool)
    for i, target in enumerate(guide_names):
        if target == "NTC":
            continue
        is_responder = rng.random() < responder_fraction
        ground_truth_responder[i] = is_responder
        if is_responder:
            X[i, :5] += effect_size * rng.normal(1.0, 0.2)

    obs = pd.DataFrame(
        {
            "lane_id": rng.choice(["L1", "L2"], size=len(guide_names)),
            "n_genes_by_counts": np.nan,
            "total_counts": np.nan,
            "pct_counts_mt": rng.uniform(0, 5, size=len(guide_names)),
            "top_guide_UMI_counts": rng.integers(5, 100, size=len(guide_names)),
            "guide_id": [f"{t}_g1" if t != "NTC" else "NTC_g1" for t in guide_names],
            "perturbed_gene_name": guide_names,
            "perturbed_gene_id": [f"ENSG_{t}" if t != "NTC" else "" for t in guide_names],
            "guide_type": guide_types,
            "PuroR": rng.uniform(0, 1, size=len(guide_names)),
            "guide_group": "g1",
            "low_quality": False,
            "_ground_truth_responder": ground_truth_responder,  # test-only column
        }
    )
    var = pd.DataFrame({"gene_name": genes, "gene_ids": [f"ENSG{i:08d}" for i in range(n_genes)]}, index=genes)
    adata = ad.AnnData(X=X, obs=obs, var=var)
    adata.obs["donor_id"] = donor_id
    adata.obs["culture_condition"] = culture_condition
    return adata


# --------------------------------------------------------------------------
# Guide-assignment QC report
# --------------------------------------------------------------------------


def guide_assignment_qc(adata: "ad.AnnData") -> Dict[str, Any]:
    """Guide-assignment diagnostics, matching the categories in
    QC_summaries_per_sample_lane.csv (NTC single sgRNA / multi sgRNA /
    no sgRNA / targeting single sgRNA), computed from obs only -- cheap even
    on a backed 130+ GiB file.
    """
    obs = adata.obs
    guide_id = obs["guide_id"].astype(str)
    guide_type = obs.get("guide_type", pd.Series(dtype=str)).astype(str)
    low_quality = obs.get("low_quality", pd.Series(False, index=obs.index)).astype(bool)

    n_cells = int(adata.n_obs)
    n_low_quality = int(low_quality.sum())
    n_multi = int((guide_id.str.lower() == "multi-guide").sum())
    n_ntc = int((guide_type == CONTROL_GUIDE_TYPE).sum())
    n_targeting = int((guide_type == TARGETING_GUIDE_TYPE).sum())
    n_other = n_cells - n_multi - n_ntc - n_targeting

    return {
        "n_cells": n_cells,
        "n_low_quality_cells": n_low_quality,
        "n_ntc_single_sgrna": n_ntc,
        "n_multi_sgrna": n_multi,
        "n_targeting_single_sgrna": n_targeting,
        "n_other_or_unassigned": n_other,
        "n_unique_guides": int(guide_id[guide_type != ""].nunique()),
        "n_unique_perturbed_genes": int(obs.loc[guide_type == TARGETING_GUIDE_TYPE, "perturbed_gene_name"].nunique()),
        "recommended_filter": "guide_type in {'targeting','non-targeting'} & low_quality == False & guide_id != 'multi-guide'",
    }


# --------------------------------------------------------------------------
# Mixscape-style responder/escaper classification (backed-safe, per target)
# --------------------------------------------------------------------------


def _materialize(adata: "ad.AnnData", idx: np.ndarray) -> np.ndarray:
    """Load a small, explicit cell subset into memory as a dense log1p matrix."""
    X = adata.X[idx]
    if hasattr(X, "todense"):
        X = np.asarray(X.todense())
    else:
        X = np.asarray(X)
    return np.log1p(X)


def classify_perturbation_response(
    adata: "ad.AnnData",
    target_col: str = "perturbed_gene_name",
    guide_type_col: str = "guide_type",
    n_pcs: int = 10,
    min_cells: int = 20,
    max_ntc_pool: int = 2000,
    seed: int = 0,
) -> pd.DataFrame:
    """Classify each targeting cell as a likely responder or non-perturbed escaper.

    Reimplements Mixscape's core statistical idea directly (pertpy failed to
    install in the development environment due to an unrelated transitive
    dependency -- see RUN_ON_REAL_DATA.md): for each target, project targeting
    + non-targeting-control cells onto the difference-of-means axis between
    the two groups in PCA space (the "perturbation signature" concept
    Mixscape uses), then fit a 2-component Gaussian mixture on that 1-D
    projection. The component further from the NTC mean is "responder"; the
    NTC-like component is "escaper" (no detectable perturbation effect).

    Backed-safe by construction: for each target, only that target's cells
    plus a capped random sample of up to ``max_ntc_pool`` control cells are
    materialized into memory (``_materialize``) -- never the whole file.
    """
    _require_deps()
    from sklearn.decomposition import PCA
    from sklearn.mixture import GaussianMixture

    rng = np.random.default_rng(seed)
    obs = adata.obs
    guide_type = obs[guide_type_col].astype(str)
    ntc_positions = np.where(guide_type.values == CONTROL_GUIDE_TYPE)[0]
    targets = sorted(obs.loc[guide_type.values == TARGETING_GUIDE_TYPE, target_col].dropna().unique())

    donor = str(obs["donor_id"].iloc[0]) if "donor_id" in obs.columns and adata.n_obs else "unknown"
    condition = str(obs["culture_condition"].iloc[0]) if "culture_condition" in obs.columns and adata.n_obs else "unknown"

    records = []
    for target in targets:
        pert_positions = np.where((guide_type.values == TARGETING_GUIDE_TYPE) & (obs[target_col].values == target))[0]
        if len(pert_positions) < min_cells or len(ntc_positions) < min_cells:
            for pos in pert_positions:
                records.append(
                    {
                        "target": target,
                        "donor_id": donor,
                        "condition": condition,
                        "guide_id": str(obs.iloc[pos]["guide_id"]),
                        "response_call": "unclassified",
                        "signature_score": np.nan,
                        "reason": f"insufficient cells (perturbed={len(pert_positions)}, ntc={len(ntc_positions)}, min={min_cells})",
                    }
                )
            continue

        ntc_sample = ntc_positions if len(ntc_positions) <= max_ntc_pool else rng.choice(ntc_positions, size=max_ntc_pool, replace=False)
        combined = np.concatenate([pert_positions, ntc_sample])
        X = _materialize(adata, np.sort(combined))
        # np.sort is required by some backed h5py slicing backends; recover original order.
        order = np.argsort(np.argsort(combined))
        X = X[order]

        n_components = min(n_pcs, X.shape[0] - 1, X.shape[1])
        pcs = PCA(n_components=n_components, random_state=0).fit_transform(X)

        n_pert = len(pert_positions)
        pert_mean = pcs[:n_pert].mean(axis=0)
        ntc_mean = pcs[n_pert:].mean(axis=0)
        axis = pert_mean - ntc_mean
        axis_norm = axis / (np.linalg.norm(axis) + 1e-12)
        projection = pcs @ axis_norm
        ntc_center = projection[n_pert:].mean()

        gmm = GaussianMixture(n_components=2, random_state=0).fit(projection.reshape(-1, 1))
        labels = gmm.predict(projection.reshape(-1, 1))
        ntc_component = gmm.predict(np.array([[ntc_center]]))[0]

        for local_i, global_pos in enumerate(pert_positions):
            call = "escaper" if labels[local_i] == ntc_component else "responder"
            records.append(
                {
                    "target": target,
                    "donor_id": donor,
                    "condition": condition,
                    "guide_id": str(obs.iloc[global_pos]["guide_id"]),
                    "response_call": call,
                    "signature_score": float(projection[local_i]),
                    "reason": None,
                }
            )
    return pd.DataFrame.from_records(records)


# --------------------------------------------------------------------------
# SCEPTRE: honest external hook, not a reimplementation
# --------------------------------------------------------------------------


def run_sceptre_external(h5ad_path: Path, r_script_path: Optional[Path] = None, timeout: int = 3600) -> Dict[str, Any]:
    """Attempt to run SCEPTRE via an external R script; degrade honestly if unavailable.

    SCEPTRE (Katsevich lab) is a calibrated conditional-resampling test whose
    correctness depends on a specific, carefully-validated permutation/CRT
    procedure implemented in R (PMID 34930414, low-MOI update PMID 38760839).
    A from-scratch Python reimplementation risks reproducing exactly the
    p-value miscalibration SCEPTRE exists to fix. This function is therefore
    an integration POINT, not a statistical engine -- see RUN_ON_REAL_DATA.md
    for how to supply a driver script once R + the sceptre package are
    installed on the processing machine.
    """
    import shutil
    import subprocess

    rscript_bin = shutil.which("Rscript")
    if rscript_bin is None:
        return {"status": "unavailable", "reason": "Rscript not found on PATH; SCEPTRE requires R"}
    if r_script_path is None or not Path(r_script_path).exists():
        return {"status": "unavailable", "reason": "no SCEPTRE driver R script supplied (r_script_path)"}
    try:
        proc = subprocess.run(
            [rscript_bin, str(r_script_path), str(h5ad_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            return {"status": "failed", "reason": proc.stderr[-2000:]}
        return {"status": "ok", "stdout": proc.stdout[-2000:]}
    except Exception as exc:
        return {"status": "unavailable", "reason": f"{type(exc).__name__}: {exc}"}


# --------------------------------------------------------------------------
# CD4 program scoring (UCell/AUCell-style, per cell)
# --------------------------------------------------------------------------


def load_seed_modules(path: Path) -> Dict[str, List[str]]:
    df = pd.read_csv(path)
    modules = {}
    for _, row in df.iterrows():
        genes = [g.strip().upper() for g in str(row["seed_genes"]).split(",") if g.strip()]
        modules[row["module_name"]] = genes
    return modules


def score_cd4_programs(adata: "ad.AnnData", modules: Dict[str, List[str]], max_cells: Optional[int] = None, seed: int = 0) -> Dict[str, str]:
    """Score cells for each CD4 program module, in-memory (loads adata.X fully).

    This is the most memory-heavy step (score_genes needs the full expression
    matrix it is scoring), so pass ``max_cells`` to subsample first on a
    memory-constrained machine -- consistent with the ``max_cells`` convention
    already used by cell_integration_pipeline.py's manifest.

    Uses scanpy's score_genes (a standard, widely-used alternative to
    UCell/AUCell's rank-based method -- not a reimplementation of UCell's
    specific Mann-Whitney-U algorithm). Modules with fewer than 2 genes
    present in this file's ``gene_name`` column are skipped, never silently
    scored from a partial/absent gene set.
    """
    _require_deps()
    working = adata
    if max_cells is not None and adata.n_obs > max_cells:
        rng = np.random.default_rng(seed)
        idx = np.sort(rng.choice(adata.n_obs, size=max_cells, replace=False))
        working = adata[idx].to_memory() if adata.isbacked else adata[idx].copy()
    elif adata.isbacked:
        working = adata.to_memory()

    gene_name_col = "gene_name" if "gene_name" in working.var.columns else None
    symbol_lookup = {
        str(working.var[gene_name_col].iloc[i]).upper(): working.var_names[i] for i in range(working.n_vars)
    } if gene_name_col else {str(g).upper(): g for g in working.var_names}

    scored = {}
    for module_name, genes in modules.items():
        present = [symbol_lookup[g] for g in genes if g in symbol_lookup]
        if len(present) < 2:
            scored[module_name] = "skipped (fewer than 2 module genes present in this file)"
            continue
        sc.tl.score_genes(working, gene_list=present, score_name=f"program_{module_name}")
        scored[module_name] = f"scored using {len(present)}/{len(genes)} module genes"
    return scored, working


# --------------------------------------------------------------------------
# Bridge cell-level findings back to the target_cards.csv schema
# --------------------------------------------------------------------------


def summarize_state_specific_effects(response_calls: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-cell response calls into target x condition summary rows,
    for ONE donor/condition file. Combine multiple files' output with
    ``merge_donor_condition_summaries`` before bridging into target_cards.csv.
    """
    if response_calls.empty:
        return pd.DataFrame(columns=["target", "condition", "donor_id", "n_cells_classified", "responder_fraction"])

    def _agg(group: pd.DataFrame) -> pd.Series:
        classified = group[group["response_call"].isin(["responder", "escaper"])]
        n_classified = len(classified)
        responder_fraction = float((classified["response_call"] == "responder").mean()) if n_classified else np.nan
        return pd.Series({"n_cells_classified": n_classified, "responder_fraction": responder_fraction})

    return (
        response_calls.groupby(["target", "condition", "donor_id"], observed=True)
        .apply(_agg, include_groups=False)
        .reset_index()
    )


def merge_donor_condition_summaries(per_file_summaries: List[pd.DataFrame]) -> pd.DataFrame:
    """Combine per-donor-condition-file summaries into one target x condition table."""
    if not per_file_summaries:
        return pd.DataFrame(columns=["target", "condition", "n_cells_classified", "responder_fraction", "n_donors_classified"])
    combined = pd.concat(per_file_summaries, ignore_index=True)

    def _agg(group: pd.DataFrame) -> pd.Series:
        total_cells = group["n_cells_classified"].sum()
        weighted_fraction = (
            (group["responder_fraction"] * group["n_cells_classified"]).sum() / total_cells if total_cells else np.nan
        )
        return pd.Series(
            {
                "n_cells_classified": int(total_cells),
                "responder_fraction": weighted_fraction,
                "n_donors_classified": group["donor_id"].nunique(),
            }
        )

    return combined.groupby(["target", "condition"], observed=True).apply(_agg, include_groups=False).reset_index()


def bridge_to_card_columns(cell_summary: pd.DataFrame, cards: pd.DataFrame) -> pd.DataFrame:
    """Left-join cell-level summary columns onto an existing target_cards.csv frame.

    Rows with no cell-level data keep NaN in the new columns -- this is an
    additive enrichment, never a replacement of the CSV-first card. The added
    fields (`n_cells_classified`, `responder_fraction`, and
    `n_donors_classified`) are exploratory/descriptive integrated-state
    summaries for visualization, state matching, and hypothesis generation;
    they must not supersede pseudobulk or raw-count DE evidence.
    """
    if cell_summary.empty:
        out = cards.copy()
        for col in ["n_cells_classified", "responder_fraction", "n_donors_classified"]:
            out[col] = np.nan
        return out
    return cards.merge(cell_summary, on=["target", "condition"], how="left")
