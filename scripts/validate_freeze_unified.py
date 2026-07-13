#!/usr/bin/env python3
"""Unified whole-repo freeze + isolation verifier.

The machine behind "每個相位凍結且隔離,改一個模組不會污染別的相位".

Reads ``docs/structure/FREEZE_MANIFEST_UNIFIED.csv`` (97 modules across the 9
phases + a shared-infra layer). For every module it recomputes a single deterministic freeze value
from the live checkout and compares to the pinned value. Because THIS script is
also the generator (``--freeze`` rewrites the pins with the same recipe), the
shipped manifest reproduces 100% by construction.

Freeze recipe (one per module, deterministic):
  - gather every file under the module's dir(s) (compound "a + b" and glob
    "topic*" dirs supported), excluding VCS/cache noise;
  - for each file compute its git blob sha1 ("blob <size>\\0<bytes>");
  - sort the shas, join, sha256 -> the module freeze value.
This is content-addressed and path-stable: editing ANY file in a module changes
only that module's value; touching another module cannot move it.

ISOLATION / CONTAMINATION CHECK (--isolation <moduleA>):
  asserts that, relative to the pinned manifest, ONLY <moduleA>'s freeze value
  may differ. Any OTHER module whose live value drifted = cross-phase
  contamination -> non-zero exit naming the leaked module(s).

Exit codes: 0 = all pins verified (or only the allowed module drifted);
            1 = drift / contamination; 2 = manifest or path problem.

Usage::
    python scripts/validate_freeze_unified.py                 # verify all
    python scripts/validate_freeze_unified.py --freeze        # (re)generate pins
    python scripts/validate_freeze_unified.py --isolation P3_statistics::de_engine_and_backend
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "docs" / "structure" / "FREEZE_MANIFEST_UNIFIED.csv"

_SKIP_PARTS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".ipynb_checkpoints", "dist"}


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(data))
    h.update(data)
    return h.hexdigest()


def _parse_dirs(dir_field: str) -> List[str]:
    """`"metadata/ + docs/"` -> ["metadata/", "docs/"]; strips "(annotation)"."""
    raw = dir_field.replace(";", "+").split("+")
    out = []
    for tok in raw:
        tok = tok.split("(", 1)[0].strip()
        if tok:
            out.append(tok)
    return out


def _iter_files(dir_token: str) -> List[Path]:
    """Resolve a dir token (plain dir, single file, or glob) to concrete files."""
    # glob token (e.g. "sources/topic*")
    if any(ch in dir_token for ch in "*?[]"):
        hits = [Path(p) for p in glob.glob(str(REPO / dir_token), recursive=True)]
        files: List[Path] = []
        for h in hits:
            if h.is_file():
                files.append(h)
            elif h.is_dir():
                files += [Path(p) for p in glob.glob(str(h / "**" / "*"), recursive=True) if Path(p).is_file()]
        return files
    base = REPO / dir_token.rstrip("/")
    if base.is_file():
        return [base]
    if base.is_dir():
        return [Path(p) for p in glob.glob(str(base / "**" / "*"), recursive=True) if Path(p).is_file()]
    return []


def _match_len(tok: str, rel: str) -> int:
    """Length of the dir-prefix match between token `tok` and repo-relative path
    `rel`; -1 if no match. Longer = more specific owner."""
    t = tok.rstrip("/")
    if any(ch in t for ch in "*?[]"):
        import fnmatch
        if fnmatch.fnmatch(rel, t + "/*") or fnmatch.fnmatch(rel, t):
            return len(t.split("*")[0])
        return -1
    if rel == t or rel.startswith(t + "/"):
        return len(t)
    return -1


_REPO_R = REPO.resolve()


def _all_repo_files() -> List[Path]:
    out = []
    for p in glob.glob(str(_REPO_R / "**" / "*"), recursive=True):
        pp = Path(p)
        if pp.is_file() and _SKIP_PARTS.isdisjoint(pp.parts):
            out.append(pp)
    return out


def partition(rows: List[dict]) -> Dict[str, List[Path]]:
    """Assign EVERY repo file to exactly one module — the one whose dir token is
    the longest matching prefix. This makes ownership disjoint by construction,
    so editing files in one module cannot change another module's freeze value."""
    mod_toks = {_key(r): _parse_dirs(r["dir"]) for r in rows}
    owned: Dict[str, List[Path]] = {k: [] for k in mod_toks}
    for f in _all_repo_files():
        rel = str(f.relative_to(_REPO_R))
        best, best_len = None, -1
        for key, toks in mod_toks.items():
            for tok in toks:
                ml = _match_len(tok, rel)
                if ml > best_len:
                    best_len, best = ml, key
        if best is not None:
            owned[best].append(f)
    return owned


def _freeze_files(files: List[Path]) -> Tuple[Optional[str], int]:
    if not files:
        return None, 0
    shas = sorted(_git_blob_sha(f) for f in files)
    return hashlib.sha256("".join(shas).encode()).hexdigest(), len(shas)


def _load() -> List[dict]:
    if not MANIFEST.exists():
        print(f"[freeze] manifest not found: {MANIFEST}", file=sys.stderr)
        sys.exit(2)
    with open(MANIFEST, newline="") as fh:
        return list(csv.DictReader(fh))


def _key(row: dict) -> str:
    return f"{row['phase']}::{row['module']}"


def verify(allow: Optional[str] = None) -> int:
    rows = _load()
    owned = partition(rows)
    drift, missing, leaked = [], [], []
    for row in rows:
        live, n = _freeze_files(owned.get(_key(row), []))
        if live is None:
            missing.append(_key(row))
            continue
        if live != row["freeze_value"]:
            if allow and _key(row) == allow:
                drift.append(_key(row))  # expected, allowed
            else:
                leaked.append(_key(row))
    ok = not missing and not leaked
    print(f"[freeze] {len(rows)} modules · {len(leaked)} unexpected drift · "
          f"{len(missing)} missing · {len(drift)} allowed-drift")
    if allow:
        print(f"[isolation] editing scope = {allow}")
        if leaked:
            print("[isolation] CROSS-PHASE CONTAMINATION — these modules moved but were NOT the edit scope:")
            for k in leaked:
                print(f"    ✗ {k}")
    else:
        for k in leaked:
            print(f"    ✗ drift: {k}")
    for k in missing:
        print(f"    ? missing files: {k}")
    return 0 if ok else 1


def freeze() -> int:
    rows = _load()
    owned = partition(rows)
    for row in rows:
        live, n = _freeze_files(owned.get(_key(row), []))
        if live is None:
            print(f"[freeze] WARN no files for {_key(row)} (dir={row['dir']})", file=sys.stderr)
            continue
        row["freeze_value"] = live
        row["shape_or_filecount"] = f"{n} files"
    with open(MANIFEST, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[freeze] re-pinned {len(rows)} modules -> {MANIFEST.relative_to(REPO)}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--freeze", action="store_true", help="(re)generate pins from live tree")
    ap.add_argument("--isolation", metavar="PHASE::MODULE",
                    help="verify that ONLY this module may have drifted (contamination guard)")
    args = ap.parse_args(argv)
    if args.freeze:
        return freeze()
    return verify(allow=args.isolation)


if __name__ == "__main__":
    raise SystemExit(main())
