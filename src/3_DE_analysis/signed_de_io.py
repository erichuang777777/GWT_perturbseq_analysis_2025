"""Read a user-uploaded signed per-downstream-gene DE table into the canonical
shape the reversal / breadth / ego-network engines consume (P1 — accept any
perturb-seq dataset).

The in-repo ``full_signed_DE`` parquet has columns
``target_gene, culture_condition, downstream_gene, log_fc, adj_p_value, zscore``.
A user's own screen may name these differently and ship as CSV or parquet. This
module maps a small set of aliases to that canonical schema so
``disease_reversal.compute_reversal`` / ``trans_network.compute_breadth`` /
``neighborhood_for_target`` (all of which already accept a DataFrame) run
unchanged on the user's data.

Honesty:
* Raises a clear ``ValueError`` when a required column (a target key, a downstream
  gene, or a signed effect) is missing — never silently fabricates one.
* If no condition column is present, a single ``"all"`` condition is synthesized
  (stated, not hidden) so per-condition logic still has a value to group on.
* If no ``adj_p_value`` is present, rows are treated as already-significant
  (``0.0``) — the honest default for a table a user has pre-filtered — and this
  choice is surfaced by ``read_signed_de_table`` via the returned ``notes``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

# canonical column -> accepted source names (case/punct-insensitive)
_ALIASES: Dict[str, List[str]] = {
    "target_gene": ["target_gene", "target", "gene", "gene_symbol", "perturbation", "ko_gene", "knockdown"],
    "downstream_gene": ["downstream_gene", "downstream", "response_gene", "readout_gene", "de_gene", "gene_downstream"],
    "culture_condition": ["culture_condition", "condition", "state", "context", "stimulation"],
    "log_fc": ["log_fc", "logfc", "log2fc", "log2_fold_change", "log_fold_change", "lfc", "coef", "beta"],
    "adj_p_value": ["adj_p_value", "padj", "fdr", "qvalue", "q_value", "adjusted_p_value"],
    "zscore": ["zscore", "z_score", "stat", "z"],
}


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def _resolve(df: pd.DataFrame) -> Dict[str, str]:
    """Map canonical name -> actual column in df (only those present)."""
    by_norm = {_norm(c): c for c in df.columns}
    out: Dict[str, str] = {}
    for canonical, names in _ALIASES.items():
        for n in names:
            if _norm(n) in by_norm:
                out[canonical] = by_norm[_norm(n)]
                break
    return out


def read_signed_de_table(path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Load a signed DE table (csv/tsv/parquet) into the canonical schema.

    Returns ``(df, notes)`` where df has columns
    ``target_gene, culture_condition, downstream_gene, log_fc, adj_p_value``
    (plus ``zscore`` if present), and notes records any defaults applied.
    Raises ``ValueError`` on a missing required column.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".parquet", ".pq"}:
        raw = pd.read_parquet(path)
    elif suffix in {".tsv", ".txt"}:
        raw = pd.read_csv(path, sep="\t")
    else:
        raw = pd.read_csv(path)

    col = _resolve(raw)
    missing = [c for c in ("target_gene", "downstream_gene", "log_fc") if c not in col]
    if missing:
        raise ValueError(
            "signed DE table is missing required column(s) "
            f"{missing}; found columns {list(raw.columns)}. Expected a target key, a "
            "downstream gene, and a signed effect (log_fc/beta/coef)."
        )

    notes: Dict[str, Any] = {"columns_mapped": {k: col[k] for k in col}}
    out = pd.DataFrame({
        "target_gene": raw[col["target_gene"]].astype(str),
        "downstream_gene": raw[col["downstream_gene"]].astype(str),
        "log_fc": pd.to_numeric(raw[col["log_fc"]], errors="coerce"),
    })
    if "culture_condition" in col:
        out["culture_condition"] = raw[col["culture_condition"]].astype(str)
    else:
        out["culture_condition"] = "all"
        notes["condition_synthesized"] = "no condition column found; using a single 'all' condition"
    if "adj_p_value" in col:
        out["adj_p_value"] = pd.to_numeric(raw[col["adj_p_value"]], errors="coerce")
    else:
        out["adj_p_value"] = 0.0
        notes["adj_p_value_defaulted"] = "no adj_p_value column found; treating all rows as significant (0.0)"
    if "zscore" in col:
        out["zscore"] = pd.to_numeric(raw[col["zscore"]], errors="coerce")

    out = out.dropna(subset=["log_fc"])
    notes["n_rows"] = int(out.shape[0])
    notes["n_targets"] = int(out["target_gene"].nunique())
    return out, notes
