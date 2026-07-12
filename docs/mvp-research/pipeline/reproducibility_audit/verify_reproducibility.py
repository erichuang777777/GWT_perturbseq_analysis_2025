#!/usr/bin/env python3
"""
verify_reproducibility.py -- CI reproducibility guard for the CD4+ T-cell
Perturb-seq pipeline.

Standalone runner, callable locally AND from CI. It re-derives all five stage
outputs from the ALREADY-COMMITTED raw supplementary table, canonicalises each
output with the bundle's DOCUMENTED canonicalisation method, and compares the
resulting md5 against the FROZEN, committed expected_outputs_checksums.csv.
It returns a NONZERO exit code on any mismatch (or any run/load error) and
NEVER writes or regenerates the expected-checksum file.

Committed bundle (published bioRxiv-preprint supplementary data, already public
in the repo -- this runner does NOT add any new raw data):

    docs/mvp-research/pipeline/reproducibility_audit/reproducibility_bundle/
        raw/DE_stats.suppl_table.csv        # sole raw input
        scripts/                            # 6 stage scripts (py + R)
        expected_outputs_checksums.csv      # FROZEN canonical md5 per output
        REPRODUCE.md
        environment.md

Canonicalisation (verbatim from REPRODUCE.md -- "the authority"):
    1. Columns reordered alphabetically (ascending, case-sensitive).
    2. Rows sorted ascending by the key column first, then by all remaining
       (already alphabetised) columns as tie-breakers, using a STABLE sort.
    3. Cell formatting: NaN/missing -> "" ; bool -> "True"/"False" ;
       int -> plain decimal (no ".0") ; float -> format(x, ".10g") ;
       everything else -> str(x).
    4. Write CSV: "," separator, NO index column, header kept, "\n" terminator,
       UTF-8.
    5. md5 of those bytes = canonical md5.

Usage:
    python verify_reproducibility.py [--bundle DIR] [--lang py|r|both]
                                     [--workdir DIR] [--keep] [-v]

Exit codes:
    0  every stage output (for every selected language) matched the frozen md5
    1  at least one mismatch, or a stage script / output failed to run or load
    2  usage / environment error (bundle not found, tool missing, etc.)
"""
import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------
# Key column per stage output (from REPRODUCE.md, step 2).
# --------------------------------------------------------------------------
KEYS = {
    "curated_targets": "index",
    "gate_passing_targets": "index",
    "effect_matrix": "target_contrast_gene_name",
    "de_matrix": "target_contrast_gene_name",
    "summary_statistics": "metric",
}

# --------------------------------------------------------------------------
# Stage-output -> produced file mapping, per language.
#
# NOTE (decoy guard, from REPRODUCE.md): the curated stage ALSO writes a third
# file 'curated_targets_{py,r}.csv' (gate-passing set deduplicated to ~1,235
# unique targets). That file is a DECOY and has NO expected checksum. The
# 'curated_targets' expected output is the FULL 33,983-row annotated table,
# i.e. curated_{py,r}.csv. We deliberately map by ROLE below, never by the
# 'curated_targets' filename, so the decoy is never checksummed.
# --------------------------------------------------------------------------
OUTPUTS = [
    # stage_output          loader          py filename            r filename
    ("curated_targets",      "csv",     "curated_py.csv",       "curated_r.csv"),
    ("gate_passing_targets", "csv",     "gate_passing_py.csv",  "gate_passing_r.csv"),
    ("effect_matrix",        "csv",     "effect_py.csv",        "effect_r.csv"),
    ("de_matrix",            "csv",     "de_py.csv",            "de_r.csv"),
    ("summary_statistics",   "summary", "summary_py.json",      "summary_r.json"),
]

CHECKSUM_FILE = "expected_outputs_checksums.csv"


# --------------------------------------------------------------------------
# Canonicalisation -- EXACTLY as documented in REPRODUCE.md. This is the whole
# point of the guard: round/sort/normalise BEFORE hashing, so we never do a
# bitwise-md5-on-floats comparison (which false-fails across R/Python/pandas
# float serialization).
# --------------------------------------------------------------------------
def _fmt_cell(v):
    if pd.isna(v):
        return ""
    if isinstance(v, (bool, np.bool_)):
        return "True" if v else "False"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if isinstance(v, (float, np.floating)):
        return format(float(v), ".10g")
    return str(v)


def canonical_md5(df: pd.DataFrame, key: str) -> str:
    """Return the canonical md5 of a stage-output table (documented method)."""
    if key not in df.columns:
        raise KeyError(
            f"key column {key!r} not present in output columns {list(df.columns)}"
        )
    # 1. columns alphabetised (ascending, case-sensitive)
    df = df[sorted(df.columns)]
    # 2. rows sorted by key, then remaining alphabetised columns; STABLE sort
    sort_cols = [key] + [c for c in df.columns if c != key]
    df = df.sort_values(sort_cols, kind="mergesort").reset_index(drop=True)
    # 3. + 4. normalise cells and write CSV with no index, "\n" terminator, UTF-8
    buf = io.StringIO()
    df.map(_fmt_cell).to_csv(buf, index=False, lineterminator="\n")
    # 5. md5
    return hashlib.md5(buf.getvalue().encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# Loaders. summary_statistics is emitted by the stage scripts as a JSON dict of
# {metric: value}; REPRODUCE.md says to flatten it into a two-column
# metric/value table before checksumming.
# --------------------------------------------------------------------------
def load_output(path: Path, loader: str) -> pd.DataFrame:
    if loader == "csv":
        return pd.read_csv(path)
    if loader == "summary":
        with open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        return pd.DataFrame({"metric": list(d.keys()), "value": list(d.values())})
    raise ValueError(f"unknown loader {loader!r}")


# --------------------------------------------------------------------------
# Bundle discovery. The bundle is committed; we locate it rather than fetch it.
# --------------------------------------------------------------------------
DEFAULT_SUBPATH = Path(
    "docs/mvp-research/pipeline/reproducibility_audit/reproducibility_bundle"
)


def _is_bundle(p: Path) -> bool:
    return (p / CHECKSUM_FILE).is_file() and (p / "scripts").is_dir() and (
        p / "raw"
    ).is_dir()


def find_bundle(explicit):
    """Resolve the committed bundle directory. Search order:
    explicit --bundle, $REPRO_BUNDLE, then the default committed subpath under
    each plausible repo root ($GITHUB_WORKSPACE, cwd, this file's ancestors).
    Auto-descend one level into 'reproducibility_bundle' if pointed at the
    parent 'reproducibility_audit' dir.
    """
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("REPRO_BUNDLE"):
        candidates.append(Path(os.environ["REPRO_BUNDLE"]))

    roots = []
    if os.environ.get("GITHUB_WORKSPACE"):
        roots.append(Path(os.environ["GITHUB_WORKSPACE"]))
    roots.append(Path.cwd())
    here = Path(__file__).resolve()
    roots.extend(here.parents)  # walk up from .github/scripts/... to repo root

    for root in roots:
        candidates.append(root / DEFAULT_SUBPATH)

    seen = set()
    for c in candidates:
        c = c.resolve()
        if c in seen:
            continue
        seen.add(c)
        if _is_bundle(c):
            return c
        # tolerate being pointed one level up (the audit dir)
        descended = c / "reproducibility_bundle"
        if _is_bundle(descended):
            return descended
    raise FileNotFoundError(
        "could not locate the committed reproducibility bundle "
        f"(looked for {CHECKSUM_FILE} + scripts/ + raw/ under: "
        + ", ".join(str(x) for x in candidates)
        + "). Pass --bundle or set $REPRO_BUNDLE."
    )


# --------------------------------------------------------------------------
# Stage execution. Each stage reads the raw table directly and writes its
# output files into the per-language work directory.
# --------------------------------------------------------------------------
def _run(cmd, cwd, verbose):
    if verbose:
        print("    $ " + " ".join(str(x) for x in cmd), flush=True)
    proc = subprocess.run(
        [str(x) for x in cmd],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"stage command failed ({proc.returncode}): {' '.join(map(str, cmd))}\n"
            f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
        )
    if verbose and proc.stdout.strip():
        for line in proc.stdout.strip().splitlines():
            print(f"      {line}", flush=True)


def run_stages(lang, bundle, raw, workdir, verbose):
    scripts = bundle / "scripts"
    workdir.mkdir(parents=True, exist_ok=True)
    if lang == "py":
        py = sys.executable
        _run([py, scripts / "curated_py.py", "--raw", raw, "--outdir", workdir],
             cwd=workdir, verbose=verbose)
        _run([py, scripts / "processed_py.py", raw], cwd=workdir, verbose=verbose)
        _run([py, scripts / "statistical_py.py", raw, workdir / "summary_py.json"],
             cwd=workdir, verbose=verbose)
    elif lang == "r":
        rscript = os.environ.get("RSCRIPT", "Rscript")
        _run([rscript, scripts / "curated_r.R", "--raw", raw, "--outdir", workdir],
             cwd=workdir, verbose=verbose)
        _run([rscript, scripts / "processed_r.R", raw], cwd=workdir, verbose=verbose)
        _run([rscript, scripts / "statistical_r.R", raw, workdir / "summary_r.json"],
             cwd=workdir, verbose=verbose)
    else:
        raise ValueError(f"unknown lang {lang!r}")


# --------------------------------------------------------------------------
# Verification driver.
# --------------------------------------------------------------------------
def verify_lang(lang, bundle, raw, workroot, expected, verbose):
    workdir = workroot / lang
    print(f"[{lang}] running stage scripts from committed raw ...", flush=True)
    run_stages(lang, bundle, raw, workdir, verbose)

    results = []
    fname_idx = 2 if lang == "py" else 3
    for row in OUTPUTS:
        stage_output, loader = row[0], row[1]
        fname = row[fname_idx]
        key = KEYS[stage_output]
        exp_md5 = expected.get(stage_output)
        try:
            df = load_output(workdir / fname, loader)
            got_md5 = canonical_md5(df, key)
            ok = (exp_md5 is not None) and (got_md5 == exp_md5)
            err = "" if exp_md5 is not None else "no expected checksum row"
        except Exception as exc:  # load/canonicalise failure -> treat as failure
            got_md5, ok, err = "ERROR", False, str(exc)
        results.append((lang, stage_output, fname, exp_md5, got_md5, ok, err))
    return results


def main():
    ap = argparse.ArgumentParser(
        description="CI reproducibility guard: re-derive Perturb-seq stage "
                    "outputs from committed raw, canonicalise, and compare to "
                    "the FROZEN expected_outputs_checksums.csv."
    )
    ap.add_argument("--bundle", default=None,
                    help="path to the committed reproducibility_bundle dir "
                         "(default: auto-detect the committed location).")
    ap.add_argument("--lang", choices=["py", "r", "both"], default="both",
                    help="which implementation(s) to verify (default: both).")
    ap.add_argument("--workdir", default=None,
                    help="scratch dir for regenerated outputs "
                         "(default: a temp dir, removed on exit).")
    ap.add_argument("--keep", action="store_true",
                    help="keep the scratch work dir instead of deleting it.")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="echo each stage command and its stdout.")
    args = ap.parse_args()

    try:
        bundle = find_bundle(args.bundle)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    raw = bundle / "raw" / "DE_stats.suppl_table.csv"
    if not raw.is_file():
        print(f"ERROR: raw input not found at {raw}", file=sys.stderr)
        return 2

    # FROZEN expected checksums -- read only, NEVER written by this runner.
    expected_df = pd.read_csv(bundle / CHECKSUM_FILE)
    expected = expected_df.set_index("stage_output")["canonical_md5"]

    print(f"bundle : {bundle}")
    print(f"raw    : {raw}")
    print(f"frozen : {bundle / CHECKSUM_FILE} ({len(expected)} expected checksums)")
    print(f"lang   : {args.lang}\n")

    langs = ["py", "r"] if args.lang == "both" else [args.lang]

    if args.workdir:
        workroot = Path(args.workdir)
        workroot.mkdir(parents=True, exist_ok=True)
        tmp_ctx = None
    else:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="repro_guard_")
        workroot = Path(tmp_ctx.name)

    all_results = []
    run_error = False
    try:
        for lang in langs:
            try:
                all_results.extend(
                    verify_lang(lang, bundle, raw, workroot, expected, args.verbose)
                )
            except Exception as exc:
                run_error = True
                print(f"[{lang}] STAGE EXECUTION FAILED: {exc}", file=sys.stderr)
    finally:
        if tmp_ctx is not None and not args.keep:
            tmp_ctx.cleanup()
        elif args.keep:
            print(f"\n(work dir kept at {workroot})")

    # Report
    print("\n" + "=" * 78)
    print(f"{'lang':4} {'stage_output':22} {'file':22} {'result':8} md5")
    print("-" * 78)
    n_fail = 0
    for lang, stage, fname, exp_md5, got_md5, ok, err in all_results:
        status = "OK" if ok else "MISMATCH"
        if not ok:
            n_fail += 1
        print(f"{lang:4} {stage:22} {fname:22} {status:8} {got_md5}")
        if not ok:
            print(f"{'':4} {'':22} {'':22} {'expected':8} {exp_md5}")
            if err:
                print(f"{'':4} -> {err}")
    print("=" * 78)

    total = len(all_results)
    if run_error or n_fail or total == 0:
        print(f"RESULT: FAIL  ({n_fail}/{total} outputs mismatched"
              f"{'; stage execution error' if run_error else ''}"
              f"{'; nothing verified' if total == 0 else ''})")
        print("\nFROZEN-CHECKSUM DISCIPLINE: this is a hard failure. If (and only "
              "if) a change to the pipeline scripts LEGITIMATELY alters an output, "
              "a human must deliberately update expected_outputs_checksums.csv in "
              "the same PR (see CI_REPRODUCIBILITY_README.md). CI never "
              "auto-regenerates the expected file.")
        return 1

    print(f"RESULT: PASS  (all {total} stage outputs match the frozen canonical md5)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
