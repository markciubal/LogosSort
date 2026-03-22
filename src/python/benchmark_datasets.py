"""
benchmark_datasets.py — LogosUltraSort per-dataset benchmark

Kaggle dataset categories (one number per line, .txt files):
  uniform          Uniform random floats
  gaussian         Gaussian random floats
  ordered          Pre-sorted ascending
  reverse_ordered  Pre-sorted descending
  repeated_values  Few distinct values (heavy duplicates)
  same_value       All elements identical
  Combinations_*   Mixed ascending/descending integer runs

For each (dataset, size), two algorithms are timed:
  logos_ultra_sort   -- copy-returning variant  (logos_ultra_sort (1).py)
  logos_sort_inplace -- in-place sibling        (logos_sort.py)

"Equivalent" pairing rationale:
  Both are pure Python, zero C calls.  logos_sort_inplace is the canonical
  reference; logos_ultra_sort adds the slice-write counting sort and slightly
  different structure.  The interesting question is whether ultra's extra
  tricks win on each specific data shape.

Each (file, algorithm) pair is run RUNS=2 times; wall-clock results are averaged.

Usage:
  python benchmark_datasets.py --kaggle "C:/path/to/archive"
  python benchmark_datasets.py --kaggle "C:/path/to/archive" --sizes 10000 100000
"""

import argparse
import os
import re
import sys
import time
import importlib.util

# ── Force UTF-8 output on Windows ─────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Import algorithms ──────────────────────────────────────────────────────────
_HERE      = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_ULTRA_FILE = os.path.join(_REPO_ROOT, "logos_ultra_sort (1).py")

_spec = importlib.util.spec_from_file_location("logos_ultra_sort_mod", _ULTRA_FILE)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
logos_ultra_sort = _mod.logos_ultra_sort

sys.path.insert(0, _HERE)
from logos_sort import logos_sort_inplace
from benchmark import tim_sort


# ── Config ─────────────────────────────────────────────────────────────────────
RUNS          = 2
DEFAULT_SIZES = [1_000, 10_000, 100_000, 1_000_000]
TIM_MAX       = 10_000   # tim_sort recursive merge is O(n^2) allocs; skip above this

# Known category directories (inner dir name matches outer)
CATEGORIES = [
    "uniform",
    "gaussian",
    "ordered",
    "reverse_ordered",
    "repeated_values",
    "same_value",
    "Combinations_of_ascending_and_descending_two_sub_arrays",
]

# Human-readable labels and what path each exercises
CATEGORY_META = {
    "uniform":           ("Uniform random",        "dual-pivot introsort path"),
    "gaussian":          ("Gaussian random",        "dual-pivot introsort path"),
    "ordered":           ("Pre-sorted ascending",   "monotone detect -> O(n)"),
    "reverse_ordered":   ("Pre-sorted descending",  "reverse detect -> O(n)"),
    "repeated_values":   ("Repeated values",        "dual-pivot (floats skip counting sort)"),
    "same_value":        ("All same value",         "monotone detect -> O(n)"),
    "Combinations_of_ascending_and_descending_two_sub_arrays":
                         ("Asc/desc runs (int)",    "counting sort or dual-pivot"),
}


# ── File discovery ─────────────────────────────────────────────────────────────

def _extract_size(filename: str) -> int | None:
    """Pull the first large integer from a filename (the array size)."""
    m = re.search(r"-(\d{3,})", filename)
    return int(m.group(1)) if m else None


def find_files(kaggle_root: str, target_sizes: list[int]) -> dict:
    """
    Returns {category: {size: filepath}} for the first matching file
    per (category, size) combination found under kaggle_root.
    """
    result = {}
    for cat in CATEGORIES:
        inner = os.path.join(kaggle_root, cat, cat)
        if not os.path.isdir(inner):
            # some archives drop the double-nesting
            inner = os.path.join(kaggle_root, cat)
        if not os.path.isdir(inner):
            continue

        by_size = {}
        for fname in sorted(os.listdir(inner)):
            if not fname.endswith(".txt"):
                continue
            sz = _extract_size(fname)
            if sz in target_sizes and sz not in by_size:
                by_size[sz] = os.path.join(inner, fname)

        if by_size:
            result[cat] = by_size

    return result


# ── Data loading ───────────────────────────────────────────────────────────────

def load_file(path: str) -> list:
    """Read one number per line; return as Python list (float or int)."""
    data = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                v = int(line) if "." not in line else float(line)
                data.append(v)
            except ValueError:
                pass
    return data


# ── Timing harness ─────────────────────────────────────────────────────────────

def bench(fn, data: list, *, inplace: bool = False) -> float:
    """Run fn RUNS times, return average wall-clock seconds."""
    total = 0.0
    for _ in range(RUNS):
        arr = data[:]
        t0  = time.perf_counter()
        fn(arr)
        total += time.perf_counter() - t0
    return total / RUNS


# ── Formatting ─────────────────────────────────────────────────────────────────

def fmt_t(s: float) -> str:
    if s >= 10:   return f"{s:7.2f}s"
    if s >= 1:    return f"{s:7.3f}s"
    if s >= 0.01: return f"{s*1000:7.1f}ms"
    return f"{s*1000:7.2f}ms"


SEP  = "-" * 78
DSEP = "=" * 78


# ── Main ───────────────────────────────────────────────────────────────────────

def run(kaggle_root: str, target_sizes: list[int]) -> None:
    print(DSEP)
    print("  LogosUltraSort vs logos_sort_inplace  --  Kaggle Dataset Benchmark")
    print(f"  Runs per measurement: {RUNS}  (averaged)")
    print(f"  Target sizes: {[f'{s:,}' for s in sorted(target_sizes)]}")
    print(f"  Dataset root: {kaggle_root}")
    print(DSEP)

    file_map = find_files(kaggle_root, set(target_sizes))

    if not file_map:
        print("  No matching files found. Check --kaggle path.")
        return

    for cat in CATEGORIES:
        if cat not in file_map:
            continue

        label, path_note = CATEGORY_META.get(cat, (cat, ""))
        print(f"\n  [{label}]  ({path_note})")
        print(SEP)
        print(f"  {'Size':>10}   {'UltraSort':>10}   {'inplace':>10}   {'TimSort':>10}   {'ratio':>7}   Winner")
        print(SEP)

        for sz in sorted(file_map[cat]):
            fpath = file_map[cat][sz]
            data  = load_file(fpath)
            actual_n = len(data)
            if actual_n == 0:
                print(f"  {sz:>10,}   (empty file, skipped)")
                continue

            ultra_t   = bench(logos_ultra_sort,  data)
            inplace_t = bench(logos_sort_inplace, data, inplace=True)
            run_tim   = actual_n <= TIM_MAX
            tim_t     = bench(tim_sort, data, inplace=True) if run_tim else None

            ratio   = ultra_t / inplace_t if inplace_t > 0 else float("inf")
            winner  = "ultra" if ratio < 0.99 else ("inplace" if ratio > 1.01 else "tied")

            tim_col = fmt_t(tim_t) if run_tim else "     n/a"
            print(f"  {actual_n:>10,}   {fmt_t(ultra_t):>10}   {fmt_t(inplace_t):>10}"
                  f"   {tim_col:>10}   {ratio:>6.2f}x   {winner}")

        print(SEP)

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LogosUltraSort per-dataset benchmark (Kaggle archive)")
    parser.add_argument(
        "--kaggle", metavar="PATH", required=True,
        help="Root directory of the Kaggle sort-benchmark archive")
    parser.add_argument(
        "--sizes", metavar="N", nargs="+", type=int, default=DEFAULT_SIZES,
        help=f"Array sizes to benchmark (default: {DEFAULT_SIZES})")
    args = parser.parse_args()

    if not os.path.isdir(args.kaggle):
        print(f"Error: --kaggle path not found: {args.kaggle}", file=sys.stderr)
        sys.exit(1)

    run(args.kaggle, args.sizes)


if __name__ == "__main__":
    main()
