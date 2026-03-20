"""
Benchmark: LogosSort vs Pure-Python Merge Sort vs C-backed list.sort()
Sizes: 500 000 · 2 500 000 · 10 000 000
Data:  random integers in [0, 1 000 000 000]

Comparison philosophy
─────────────────────
• LogosSort (this file)  — 100% pure Python, insertion sort at base cases.
• merge_sort (this file) — 100% pure Python bottom-up merge sort (simplified
                           Timsort): same interpreter, same overheads.
  → These two are the apples-to-apples algorithmic comparison.

• list.sort() (C-backed)  — shown for reference/scale only.
  Timsort compiled into CPython; not a fair algorithmic peer.
"""

import random
import sys
import time
import os

sys.path.insert(0, os.path.dirname(__file__))
from logos_sort import logos_sort

SIZES   = [500_000, 2_500_000, 10_000_000]
MAX_VAL = 1_000_000_000
RUNS    = 3


# ─────────────────────────────────────────────────────────────────────────────
# Pure Python bottom-up merge sort (no C sort calls)
# Uses insertion sort for initial runs of size 32 — same base-case size class
# as LogosSort — to keep the comparison on equal footing.
# ─────────────────────────────────────────────────────────────────────────────

def _insertion_sort_block(a, lo, hi):
    for i in range(lo + 1, hi + 1):
        key = a[i]; j = i - 1
        while j >= lo and a[j] > key:
            a[j + 1] = a[j]; j -= 1
        a[j + 1] = key


def merge_sort(arr: list) -> list:
    """Pure Python bottom-up merge sort — O(n log n), zero C sort calls."""
    n = len(arr)
    if n < 2:
        return arr[:]

    src = arr[:]
    dst = src[:]

    # Phase 1: sort initial blocks of 32 with insertion sort
    BLOCK = 32
    lo = 0
    while lo < n:
        hi = min(lo + BLOCK - 1, n - 1)
        _insertion_sort_block(src, lo, hi)
        lo += BLOCK

    # Phase 2: bottom-up merge passes
    width = BLOCK
    while width < n:
        lo = 0
        while lo < n:
            mid = min(lo + width,         n)
            hi  = min(lo + 2 * width,     n)
            if mid >= hi:
                dst[lo:hi] = src[lo:hi]   # odd run — just copy
            else:
                i, j, k = lo, mid, lo
                while i < mid and j < hi:
                    if src[i] <= src[j]:
                        dst[k] = src[i]; i += 1
                    else:
                        dst[k] = src[j]; j += 1
                    k += 1
                while i < mid:
                    dst[k] = src[i]; i += 1; k += 1
                while j < hi:
                    dst[k] = src[j]; j += 1; k += 1
            lo += 2 * width
        src, dst = dst, src
        width *= 2

    return src


# ─────────────────────────────────────────────────────────────────────────────
# Benchmark harness
# ─────────────────────────────────────────────────────────────────────────────

def bench(fn, data: list) -> float:
    arr = data[:]
    t0  = time.perf_counter()
    fn(arr)
    return time.perf_counter() - t0


def logos_wrapper(arr):
    result = logos_sort(arr)
    arr[:] = result


def merge_wrapper(arr):
    result = merge_sort(arr)
    arr[:] = result


def timsort_c(arr):
    arr.sort()   # C-backed — shown for scale only


print("=" * 70)
print("LogosSort vs Pure-Python Merge Sort  (apples-to-apples)")
print("C-backed list.sort() shown for reference scale only")
print("=" * 70)
print(f"{'Size':>12}  {'LogosSort':>11}  {'MergeSort':>11}  {'list.sort()':>11}  {'L/M ratio':>9}")
print("-" * 70)

for n in SIZES:
    print(f"  Generating {n:,} items...", end="\r", flush=True)
    data = [random.randint(0, MAX_VAL) for _ in range(n)]

    logos_times = [bench(logos_wrapper, data) for _ in range(RUNS)]
    merge_times = [bench(merge_wrapper, data) for _ in range(RUNS)]
    tim_times   = [bench(timsort_c,     data) for _ in range(RUNS)]

    la = sum(logos_times) / RUNS
    ma = sum(merge_times) / RUNS
    ta = sum(tim_times)   / RUNS

    print(
        f"{n:>12,}  {la:>9.3f}s  {ma:>9.3f}s  {ta:>9.3f}s  {la/ma:>8.2f}x"
    )

print()
print("L/M ratio: LogosSort time / MergeSort time (<1.0 = LogosSort wins)")
print()
print("Note: list.sort() is CPython's C-implemented Timsort — not a fair")
print("      peer but shown to illustrate the Python interpreter overhead.")
print("      See compiled language benchmarks for the true algorithmic story.")
