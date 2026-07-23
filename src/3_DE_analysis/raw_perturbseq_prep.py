"""Offline prep: raw perturb-seq scRNA (.h5ad) -> the two CSVs the portal ingests.

The portal runtime is deliberately light (no scanpy/anndata) and consumes
SUMMARY tables. This offline tool closes the last gap in "accept any perturb-seq
dataset" (P3): it turns a user's raw single-cell perturb-seq object into

  1. ``target_evidence.csv``  — one row per target x condition (feeds the cards /
     readiness via ``/api/imports`` source type ``target_evidence``), and
  2. ``signed_de.csv``        — one row per target x downstream gene with a signed
     effect (feeds disease-reversal / trans-breadth / ego-network via
     ``/api/imports`` source type ``signed_de_evidence``).

Design:
* The DE **core** (``pseudobulk_de``) is pure numpy/pandas/scipy — no anndata — so
  it is testable without the heavy stack and reusable.
* Only ``prep_h5ad`` touches anndata, lazily, so importing this module never
  requires scanpy/anndata.

Honesty:
* This is a fast, transparent pseudobulk mean-difference DE (log2 fold-change of
  group means + optional Welch t-test + BH-FDR) — NOT the paper's donor-aware
  DESeq2 pipeline. It is a quick-look starting point; for publication-grade calls
  use the full pipeline in ``src/1_preprocess`` … ``src/3_DE_analysis``. This
  caveat is printed by the CLI and recorded in a ``prep_manifest.json``.
* No fabrication: a target/condition group below ``min_cells`` is skipped (not
  imputed); a gene with no expression in either group contributes no edge.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

PSEUDOCOUNT = 1.0


def _bh_fdr(pvals: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values."""
    p = np.asarray(pvals, dtype=float)
    n = p.size
    if n == 0:
        return p
    order = np.argsort(p)
    ranked = p[order] * n / (np.arange(n) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n, dtype=float)
    out[order] = np.clip(ranked, 0, 1)
    return out


def pseudobulk_de(
    X: np.ndarray,
    gene_names: Sequence[str],
    target_labels: Sequence[str],
    *,
    condition_labels: Optional[Sequence[str]] = None,
    control_label: str = "NTC",
    min_cells: int = 10,
    lfc_threshold: float = 1.0,
    sig_padj: float = 0.1,
    use_ttest: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Pure pseudobulk mean-difference DE. Returns ``(signed_de, target_evidence)``.

    ``X`` is a (cells x genes) matrix (raw or normalized counts). For each
    ``target x condition`` group (>= ``min_cells``) it compares against the
    control group in the SAME condition, computing per-gene
    ``log2((mean_target+1)/(mean_control+1))`` and (if scipy is available and
    ``use_ttest``) a Welch t-test -> BH-FDR. ``signed_de`` keeps genes with
    ``adj_p_value <= sig_padj`` (or ``|log_fc| >= lfc_threshold`` when no p-value).
    """
    X = np.asarray(X, dtype=float)
    genes = np.asarray(list(gene_names))
    targets = np.asarray([str(t) for t in target_labels])
    conds = np.asarray([str(c) for c in condition_labels]) if condition_labels is not None else np.array(["all"] * X.shape[0])

    try:
        from scipy import stats as _stats  # noqa: F401
        have_scipy = use_ttest
    except Exception:  # noqa: BLE001
        have_scipy = False

    signed_rows: List[Dict[str, Any]] = []
    evid_rows: List[Dict[str, Any]] = []

    for cond in pd.unique(conds):
        cmask = conds == cond
        ctrl_mask = cmask & (targets == control_label)
        if ctrl_mask.sum() < min_cells:
            continue  # no usable control in this condition -> skip (never fabricate)
        ctrl_X = X[ctrl_mask]
        ctrl_mean = ctrl_X.mean(axis=0)
        for tgt in pd.unique(targets[cmask]):
            if tgt == control_label:
                continue
            tmask = cmask & (targets == tgt)
            n_cells = int(tmask.sum())
            if n_cells < min_cells:
                continue
            tgt_X = X[tmask]
            tgt_mean = tgt_X.mean(axis=0)
            lfc = np.log2((tgt_mean + PSEUDOCOUNT) / (ctrl_mean + PSEUDOCOUNT))
            if have_scipy:
                from scipy import stats

                tstat, pval = stats.ttest_ind(tgt_X, ctrl_X, axis=0, equal_var=False)
                pval = np.nan_to_num(pval, nan=1.0)
                padj = _bh_fdr(pval)
                keep = padj <= sig_padj
            else:
                tstat = np.zeros_like(lfc)
                padj = np.full_like(lfc, np.nan)
                keep = np.abs(lfc) >= lfc_threshold
            idx = np.where(keep & np.isfinite(lfc))[0]
            for j in idx:
                signed_rows.append({
                    "target_gene": tgt,
                    "culture_condition": cond,
                    "downstream_gene": str(genes[j]),
                    "log_fc": round(float(lfc[j]), 5),
                    "adj_p_value": (None if np.isnan(padj[j]) else round(float(padj[j]), 6)),
                    "zscore": round(float(tstat[j]), 5),
                })
            sig_lfc = lfc[idx]
            evid_rows.append({
                "target": tgt,
                "condition": cond,
                "n_cells": n_cells,
                "n_total_de_genes": int(idx.size),
                "n_up_genes": int((sig_lfc > 0).sum()),
                "n_down_genes": int((sig_lfc < 0).sum()),
                "effect_size": (round(float(np.abs(sig_lfc).max()), 5) if idx.size else 0.0),
                "logfc": (round(float(sig_lfc[np.argmax(np.abs(sig_lfc))]), 5) if idx.size else 0.0),
                "fdr": (round(float(np.nanmin(padj[idx])), 6) if (idx.size and have_scipy) else None),
            })

    signed_de = pd.DataFrame(signed_rows, columns=["target_gene", "culture_condition", "downstream_gene", "log_fc", "adj_p_value", "zscore"])
    target_evidence = pd.DataFrame(evid_rows, columns=["target", "condition", "n_cells", "n_total_de_genes", "n_up_genes", "n_down_genes", "effect_size", "logfc", "fdr"])
    return signed_de, target_evidence


def prep_h5ad(
    h5ad_path: Path,
    out_dir: Path,
    *,
    target_col: str = "target",
    condition_col: Optional[str] = None,
    control_label: str = "NTC",
    layer: Optional[str] = None,
    **de_kwargs: Any,
) -> Dict[str, Any]:
    """Read an h5ad and write ``signed_de.csv`` + ``target_evidence.csv`` + a manifest.

    ``anndata`` is imported lazily here so the rest of this module needs no heavy
    stack. ``target_col`` / ``condition_col`` name the per-cell obs columns.
    """
    import anndata  # lazy — only this path needs it

    adata = anndata.read_h5ad(str(h5ad_path))
    if target_col not in adata.obs.columns:
        raise ValueError(f"target_col {target_col!r} not in obs columns {list(adata.obs.columns)}")
    X = adata.layers[layer] if layer else adata.X
    X = X.toarray() if hasattr(X, "toarray") else np.asarray(X)
    gene_names = list(adata.var_names)
    target_labels = adata.obs[target_col].astype(str).tolist()
    condition_labels = adata.obs[condition_col].astype(str).tolist() if condition_col and condition_col in adata.obs.columns else None

    signed_de, target_evidence = pseudobulk_de(
        X, gene_names, target_labels, condition_labels=condition_labels, control_label=control_label, **de_kwargs,
    )
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    signed_path = out_dir / "signed_de.csv"
    evid_path = out_dir / "target_evidence.csv"
    signed_de.to_csv(signed_path, index=False)
    target_evidence.to_csv(evid_path, index=False)
    manifest = {
        "source_h5ad": str(h5ad_path),
        "n_cells": int(X.shape[0]),
        "n_genes": int(X.shape[1]),
        "n_targets": int(target_evidence["target"].nunique()) if not target_evidence.empty else 0,
        "signed_de_csv": str(signed_path),
        "target_evidence_csv": str(evid_path),
        "caveat": "Fast pseudobulk mean-difference DE (log2FC of group means + Welch t-test + BH-FDR), "
                  "NOT the paper's donor-aware DESeq2 pipeline. Quick-look only; use the full "
                  "src/1_preprocess..3_DE_analysis pipeline for publication-grade calls.",
    }
    (out_dir / "prep_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Prep a raw perturb-seq .h5ad into portal-ingestible CSVs.")
    ap.add_argument("h5ad", type=Path)
    ap.add_argument("--out", type=Path, default=Path("./prep_out"))
    ap.add_argument("--target-col", default="target")
    ap.add_argument("--condition-col", default=None)
    ap.add_argument("--control-label", default="NTC")
    ap.add_argument("--layer", default=None)
    ap.add_argument("--min-cells", type=int, default=10)
    args = ap.parse_args(argv)
    manifest = prep_h5ad(
        args.h5ad, args.out, target_col=args.target_col, condition_col=args.condition_col,
        control_label=args.control_label, layer=args.layer, min_cells=args.min_cells,
    )
    print(json.dumps(manifest, indent=2))
    print("\nNext: upload target_evidence.csv (target_evidence) and signed_de.csv (signed_de_evidence) "
          "via /api/imports, or point export_real_data.py --cards at the built cards.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
