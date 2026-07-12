#!/usr/bin/env python3
"""Freeze-integrity verifier — the machine check behind "結果可以重現".

Reads ``docs/mvp-research/pipeline/FREEZE_MANIFEST.csv`` (the sole authoritative
pin manifest) and, for every pinned asset, recomputes its live md5 and compares
it to the frozen md5. Any drift, or any missing asset, is a non-zero exit — so
``make freeze`` fails loudly if a frozen stage output was silently edited,
regenerated, or lost.

This does NOT re-run the heavy analysis pipeline (the raw single-cell layer is
S3-only and ~1.7 TB; see docs/REPRODUCIBILITY.md §8). It verifies that the
frozen, in-repo stage artifacts still match their pins — the reproducibility
guarantee that is actually checkable in a normal checkout/CI.

Exit codes: 0 = all pins verified; 1 = drift/missing; 2 = manifest problem.

Usage::

    python scripts/freeze_pipeline.py            # verify all pins
    python scripts/freeze_pipeline.py --eda       # also run the EDA generator --check
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

REPO = Path(__file__).resolve().parent.parent
PIPE = REPO / "docs" / "mvp-research" / "pipeline"
MANIFEST = PIPE / "FREEZE_MANIFEST.csv"

# Assets that do NOT live under the pipeline dir need an explicit path (basename
# alone is ambiguous -- e.g. target_cards.csv exists in every cache UUID dir).
EXPLICIT_PATHS: Dict[str, Path] = {
    "target_cards.csv": REPO
    / "sources" / "target_tool_cache" / "a6bba17b-f194-4a50-8cf8-96e03eededd6" / "target_cards.csv",
    "real-dataset.json": REPO / "frontend" / "webserver" / "public" / "real-dataset.json",
    "signed_module_effect.parquet": REPO / "sources" / "target_tool_cache" / "_overlays" / "signed_module_effect.parquet",
}


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _basename(stage_asset: str) -> str:
    """`"05_visualization / REFINED_CATALOG_53.csv (note)"` -> `"REFINED_CATALOG_53.csv"`."""
    tail = stage_asset.split(" / ", 1)[-1]
    return tail.split(" (", 1)[0].strip()


def _resolve(stage_asset: str) -> Optional[Path]:
    name = _basename(stage_asset)
    if name in EXPLICIT_PATHS:
        p = EXPLICIT_PATHS[name]
        return p if p.exists() else None
    # basename search under the pipeline dir (deterministic: shortest path wins)
    matches = sorted(PIPE.rglob(name), key=lambda p: (len(str(p)), str(p)))
    return matches[0] if matches else None


def verify() -> int:
    if not MANIFEST.exists():
        print(f"FATAL: manifest not found: {MANIFEST}", file=sys.stderr)
        return 2
    rows = list(csv.DictReader(MANIFEST.read_text(encoding="utf-8").splitlines()))
    if not rows:
        print("FATAL: manifest empty", file=sys.stderr)
        return 2

    ok, drift, missing = 0, [], []
    for row in rows:
        asset = row["stage_asset"]
        pinned = row["md5"].strip()
        path = _resolve(asset)
        if path is None:
            missing.append(asset)
            print(f"  MISSING  {asset}")
            continue
        live = _md5(path)
        if live == pinned:
            ok += 1
            print(f"  OK       {asset}  ({live[:8]}…)")
        else:
            drift.append((asset, pinned, live, path))
            print(f"  DRIFT    {asset}\n           pinned={pinned}\n           live  ={live}\n           at    ={path.relative_to(REPO)}")

    print(f"\nfreeze verify: {ok} OK, {len(drift)} drifted, {len(missing)} missing "
          f"(of {len(rows)} pins)")
    return 0 if (not drift and not missing) else 1


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--eda", action="store_true", help="also run generate_stage_eda.py --check")
    args = ap.parse_args(argv)

    rc = verify()
    if args.eda:
        print("\n--- EDA report freshness ---")
        eda_rc = subprocess.call([sys.executable, str(REPO / "scripts" / "generate_stage_eda.py"), "--check"])
        rc = rc or eda_rc
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
