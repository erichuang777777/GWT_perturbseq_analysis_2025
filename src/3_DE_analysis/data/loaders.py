"""Shared raw-file loaders: gene lists, druggable-class overlays, benchmark CSV
(architecture refactor Phase 2 -- see ``docs/architecture_refactor_plan.md`` §3).

Before this module existed, ``load_gene_set``/the druggable-class-overlay
loader were independently reimplemented in both ``build_target_cards.py``
(``load_druggable_overlays``) and ``readiness_engine.py`` (``load_overlays``)
-- byte-for-byte identical logic, defined twice. Both modules now import from
here and keep their original names as thin aliases so existing callers are
unaffected.

This is the innermost data-access layer: it depends only on ``pandas``,
stdlib, and (for the druggable-class name -> modality vocabulary)
``core.cards``'s constants -- never on ``evidence``/``api``/``resolve``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Set

import pandas as pd


def load_gene_set(path: Path) -> Set[str]:
    """Load a newline-delimited gene-symbol list (no header) into an upper-cased set."""
    if not Path(path).exists():
        return set()
    genes: Set[str] = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        token = line.strip().split("\t")[0].strip()
        if token and not token.lower().startswith("gene"):
            genes.add(token.upper())
    return genes


def load_druggable_class_overlays(gene_lists_dir: Path, druggable_class_modality: Dict[str, str]) -> Dict[str, Set[str]]:
    """Load druggable-class + genetics gene sets from ``metadata/gene_lists``.

    ``druggable_class_modality`` is ``core.cards.DRUGGABLE_CLASS_MODALITY`` --
    passed in rather than imported, so this data-access module has no
    dependency on ``core``. Returns a dict mapping overlay name -> upper-cased
    gene set; missing files are simply absent from the dict (their domains
    stay ``"unknown"`` downstream).
    """
    gene_lists_dir = Path(gene_lists_dir)
    overlays: Dict[str, Set[str]] = {}
    for name in list(druggable_class_modality) + ["gwascatalog", "clinvar_path_likelypath"]:
        genes = load_gene_set(gene_lists_dir / f"{name}.tsv")
        if genes:
            overlays[name] = genes
    return overlays


def load_benchmark_csv(path: Optional[Path]) -> Optional[pd.DataFrame]:
    if path is None:
        return None
    if not Path(path).exists():
        return None
    return pd.read_csv(path)
