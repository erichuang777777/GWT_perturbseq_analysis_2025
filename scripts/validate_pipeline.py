#!/usr/bin/env python3
"""Pipeline validation COLLECTOR — read-only. Feeds docs/human_validation_protocol.md.

This is a *collector, not a validator*: it does not decide pass/fail and it
re-implements no pinned value. The authority for correctness is the test suite
(``tests/``) and the schema contract (``src/3_DE_analysis/contracts/card_schema.py``).
This script only fetches the live numbers a human needs to eyeball while walking
the human-validation protocol -- so a domain scientist reads a number off this
terminal instead of hand-writing pandas across five files.

Every block printed here maps to a checkbox / open-finding in
``docs/human_validation_protocol.md``. It is strictly read-only: it opens files,
counts rows, reports dtypes, and calls the existing ``validate_cards`` -- it
never writes, mutates, or rebuilds anything.

Run: ``make validate-pipeline``  (or ``python scripts/validate_pipeline.py``).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src" / "3_DE_analysis"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pandas as pd  # noqa: E402

# Stage-0 raw inputs (paths mirror config/settings.py; kept here as literals so
# the collector has no import-time dependency on the backend beyond card_schema).
RAW_INPUTS = {
    "DE_stats": REPO_ROOT / "metadata" / "suppl_tables" / "DE_stats.suppl_table.csv",
    "guide_kd_efficiency": REPO_ROOT / "metadata" / "suppl_tables" / "guide_kd_efficiency.suppl_table.csv",
    "sgrna_library_metadata": REPO_ROOT / "metadata" / "suppl_tables" / "sgrna_library_metadata.suppl_table.csv",
    "sample_metadata": REPO_ROOT / "metadata" / "suppl_tables" / "sample_metadata.suppl_table.csv",
    "disease_gene_associations": REPO_ROOT / "src" / "6_functional_interaction" / "results" / "disease_gene_associations_detailed.csv",
    "gnomad_constraint_seed": REPO_ROOT / "sources" / "target_tool_cache" / "_overlays" / "gnomad_constraint_seed.csv",
}
CACHE_ROOT = REPO_ROOT / "sources" / "target_tool_cache"


def _hr(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def _find_card_datasets() -> List[Path]:
    """Every cache subdir that actually holds a target_cards.csv (skips the
    _evidence/_overlays/_pathway/_lincs/imports helper dirs)."""
    if not CACHE_ROOT.exists():
        return []
    return sorted(p.parent for p in CACHE_ROOT.glob("*/target_cards.csv"))


def _thresholds_block() -> None:
    _hr("LIVE THRESHOLDS (config/thresholds.py) — check docs/data_dictionary.md §2 against these")
    try:
        from config import thresholds as t  # noqa: WPS433
    except Exception as exc:  # noqa: BLE001
        print(f"  could not import config.thresholds: {exc}")
        return
    for name in sorted(dir(t)):
        if name.isupper():
            print(f"  {name} = {getattr(t, name)}")


def _card_schema_block(dataset_dir: Path) -> None:
    csv = dataset_dir / "target_cards.csv"
    _hr(f"CARDS SCHEMA + DTYPES — {dataset_dir.name}")
    df = pd.read_csv(csv, low_memory=False)
    n_cols = len(df.columns)
    print(f"  rows: {len(df):,}   columns: {n_cols}")

    try:
        from contracts.card_schema import CARD_COLUMNS, validate_cards  # noqa: WPS433

        declared = len(CARD_COLUMNS)
        # --- OF-1: schema drift (auto-detect) ---
        if n_cols == declared:
            print(f"  OF-1 schema drift ...... OK   ({n_cols} cols == CARD_COLUMNS {declared})")
        else:
            missing = [c for c in CARD_COLUMNS if c not in df.columns]
            print(f"  OF-1 schema drift ...... FAIL ({n_cols} cols != CARD_COLUMNS {declared})")
            print(f"       columns declared-but-absent: {missing}")

        strict_errors = validate_cards(df, strict=True)
        core_errors = validate_cards(df, strict=False)
        print(f"  validate_cards(strict=True)  -> {len(strict_errors)} error(s)"
              + ("" if not strict_errors else ":"))
        for e in strict_errors:
            print(f"       - {e}")
        print(f"  validate_cards(strict=False) -> {len(core_errors)} error(s) (core 9-column contract)")
    except Exception as exc:  # noqa: BLE001
        print(f"  could not run validate_cards: {exc}")

    print("  dtypes:")
    for col, dt in df.dtypes.items():
        print(f"       {col:<32} {dt}")


def _metadata_block(dataset_dir: Path) -> None:
    meta = dataset_dir / "metadata.json"
    _hr(f"METADATA + OF-2 (leak/conflict auto-detect) — {dataset_dir.name}")
    if not meta.exists():
        print("  metadata.json: ABSENT")
        return
    raw = meta.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        print(f"  metadata.json unparseable: {exc}")
        return
    # OF-2a: Windows absolute-path leak.
    win_paths = [ln.strip() for ln in raw.splitlines() if "\\" in ln and ":" in ln]
    if win_paths:
        print("  OF-2 windows-path leak .. FAIL (absolute Windows path(s) present):")
        for ln in win_paths:
            print(f"       {ln}")
    else:
        print("  OF-2 windows-path leak .. OK")
    # OF-2b: max_rows / preview_limit vs real row count conflict.
    params = data.get("params", {}) or {}
    max_rows = params.get("max_rows")
    preview_limit = data.get("preview_limit")
    real_rows = data.get("rows")
    if max_rows is not None or preview_limit is not None:
        print(f"  OF-2 max_rows/preview .... REVIEW (params.max_rows={max_rows}, "
              f"preview_limit={preview_limit}, metadata rows={real_rows}) "
              "— confirm the cap never truncated the shipped data")
    else:
        print("  OF-2 max_rows/preview .... OK (no truncation params present)")


def _raw_inputs_block() -> None:
    _hr("STAGE 0 RAW INPUT ROW COUNTS — check docs/data_dictionary.md §1")
    for name, path in RAW_INPUTS.items():
        if not path.exists():
            print(f"  {name:<28} MISSING at {path}")
            continue
        # Count data rows without loading the whole frame into memory.
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            n = sum(1 for _ in fh) - 1  # minus header
        print(f"  {name:<28} {n:,} data rows   ({path.relative_to(REPO_ROOT)})")


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    _hr("PIPELINE VALIDATION COLLECTOR (read-only) — feeds docs/human_validation_protocol.md")
    print("  This prints numbers for a human to sign off on. It is NOT the authority;")
    print("  tests/ and contracts/ are. See the protocol doc for what each block gates.")

    datasets = _find_card_datasets()
    _hr("ACTIVE DATASETS (cache subdirs holding target_cards.csv)")
    if not datasets:
        print("  none found under sources/target_tool_cache/ — build one first "
              "(make api, then POST /api/run/target-card) or check the repo checkout.")
    for d in datasets:
        try:
            ncols = len(pd.read_csv(d / "target_cards.csv", nrows=0).columns)
        except Exception:  # noqa: BLE001
            ncols = "?"
        print(f"  {d.name}   ({ncols} cols)")

    _raw_inputs_block()
    _thresholds_block()

    # Per-dataset schema + metadata blocks. The human records which UUID is the
    # "active/canonical" one in the protocol's §0 banner.
    target = argv[0] if argv else None
    for d in datasets:
        if target and d.name != target:
            continue
        _card_schema_block(d)
        _metadata_block(d)

    _hr("DONE — carry these numbers into docs/human_validation_protocol.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
