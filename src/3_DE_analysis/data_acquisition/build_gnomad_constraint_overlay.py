#!/usr/bin/env python3
"""Build the full-genome gnomAD LoF-constraint overlay (LOEUF + pLI).

Replaces the earlier 15-gene shortlist seed (which carried demo values
derived from ``docs/mvp-research/connector_enrichment_demo.csv`` and was
mislabelled "real gnomAD v4") with an authentic, complete, single-version
snapshot straight from gnomAD's public release bucket.

Source (canonical, versioned, one row per gene, includes chrX):
  gnomAD v2.1.1 gene-level LoF constraint metrics
  https://storage.googleapis.com/gcp-public-data--gnomad/release/2.1.1/constraint/gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz

Why v2.1.1 rather than v4.1: v2.1.1 ``lof_metrics.by_gene`` is the canonical,
most-cited constraint table (Karczewski et al. 2020), one row per gene across
the whole genome -- crucially including chromosome X. For a CD4 T-cell tool,
chrX genes are not optional: FOXP3 (the master Treg regulator), CD40LG, and
others live there. The v4.1 ``constraint_metrics`` distribution we could reach
in this environment was autosomes-only, so it would have silently dropped
FOXP3/MED12/CD40LG -- an unacceptable, invisible completeness gap. A single
complete version beats a newer-but-partial one here.

Columns taken (gnomAD name -> overlay name):
  gene         -> gene_symbol
  gene_id      -> ensembl_id   (ENSG...)
  oe_lof_upper -> loeuf        (upper bound of the observed/expected LoF CI = LOEUF)
  pLI          -> pli

Honesty / reproducibility contract:
  * Rows missing any of {ensembl_id, gene_symbol, loeuf, pli} are dropped --
    an absent gene is genuinely unmeasured downstream (``unknown != 0``), never
    a fabricated 0. The loader's fallback contract handles absence.
  * A handful of gene symbols carry two rows (alternate canonical transcripts);
    we keep the row with the smaller LOEUF (the more conservative / more
    constrained estimate) deterministically, so the output is stable.
  * Output is sorted by gene_symbol and written with fixed float formatting so
    re-running yields a byte-identical file (git-diffable).

Usage:
  # from a locally-downloaded release file (offline-friendly, default if present):
  python build_gnomad_constraint_overlay.py --source /path/to/gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz

  # or let it fetch the public release over the network:
  python build_gnomad_constraint_overlay.py --download
"""

from __future__ import annotations

import argparse
import gzip
import io
import sys
from pathlib import Path

import pandas as pd

GNOMAD_V211_BY_GENE_URL = (
    "https://storage.googleapis.com/gcp-public-data--gnomad/"
    "release/2.1.1/constraint/gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz"
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = (
    _REPO_ROOT / "sources" / "target_tool_cache" / "_overlays" / "gnomad_constraint_seed.csv"
)

# gnomAD v2.1.1 by-gene column names we read.
_COL_GENE = "gene"
_COL_GENE_ID = "gene_id"
_COL_LOEUF = "oe_lof_upper"
_COL_PLI = "pLI"


def _read_gnomad_table(source: Path) -> pd.DataFrame:
    """Read the bgzip'd (or plain) gnomAD by-gene TSV into a DataFrame."""
    raw = source.read_bytes()
    # bgzip is gzip-compatible; gzip.decompress reads the whole (multi-block) file.
    try:
        text = gzip.decompress(raw).decode("utf-8")
    except OSError:
        text = raw.decode("utf-8")
    return pd.read_csv(io.StringIO(text), sep="\t", low_memory=False)


def _download(url: str, dest: Path) -> Path:
    import requests  # local import: only needed for the networked path

    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
    return dest


def build_overlay(df: pd.DataFrame) -> pd.DataFrame:
    """Project + clean the gnomAD by-gene table into the overlay schema."""
    missing = [c for c in (_COL_GENE, _COL_GENE_ID, _COL_LOEUF, _COL_PLI) if c not in df.columns]
    if missing:
        raise ValueError(f"gnomAD source is missing expected columns: {missing}")

    out = df[[_COL_GENE_ID, _COL_GENE, _COL_LOEUF, _COL_PLI]].copy()
    out.columns = ["ensembl_id", "gene_symbol", "loeuf", "pli"]

    # keep only Ensembl gene IDs; coerce constraint values to numeric
    out = out[out["ensembl_id"].astype(str).str.startswith("ENSG")]
    out["loeuf"] = pd.to_numeric(out["loeuf"], errors="coerce")
    out["pli"] = pd.to_numeric(out["pli"], errors="coerce")

    # unknown != 0: drop rows with any missing required field rather than impute
    out = out.dropna(subset=["ensembl_id", "gene_symbol", "loeuf", "pli"])

    # deterministic dedupe: a few symbols carry two transcript rows -> keep the
    # smaller (more conservative / more constrained) LOEUF
    out = out.sort_values(["gene_symbol", "loeuf"]).drop_duplicates(
        subset=["gene_symbol"], keep="first"
    )

    out = out.sort_values("gene_symbol").reset_index(drop=True)
    # fixed formatting for byte-stable output
    out["loeuf"] = out["loeuf"].map(lambda v: f"{float(v):.4f}")
    out["pli"] = out["pli"].map(lambda v: f"{float(v):.4g}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--source",
        type=Path,
        default=None,
        help="local gnomAD v2.1.1 by-gene .txt.bgz (or .tsv). If omitted and --download not set, "
        "looks for a cached copy next to this script.",
    )
    ap.add_argument("--download", action="store_true", help=f"fetch {GNOMAD_V211_BY_GENE_URL}")
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args(argv)

    cached = Path(__file__).resolve().parent / "gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz"
    if args.download:
        source = _download(GNOMAD_V211_BY_GENE_URL, cached)
    elif args.source is not None:
        source = args.source
    elif cached.exists():
        source = cached
    else:
        print(
            "no source file: pass --source <file> or --download to fetch\n"
            f"  {GNOMAD_V211_BY_GENE_URL}",
            file=sys.stderr,
        )
        return 2

    df = _read_gnomad_table(source)
    overlay = build_overlay(df)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    overlay.to_csv(args.output, index=False)
    print(f"wrote {len(overlay)} genes -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
