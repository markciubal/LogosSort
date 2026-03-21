"""
Benchmark: LogosSort vs Pure-Python Merge Sort
Time + Space complexity at 500 000 · 2 500 000 · 10 000 000 items.

Comparison philosophy
---------------------
logos_sort_inplace  -- pure Python, O(log n) space (recursion stack only).
merge_sort_inplace  -- pure Python, O(n) space (one auxiliary buffer).
  -> These two are the fair algorithmic comparison.

list.sort()         -- C-backed Timsort, shown for scale only.

Memory measurement
------------------
Time runs are performed WITHOUT tracemalloc to avoid 6-8x profiling overhead.
A single separate traced pass measures peak auxiliary heap allocation.
The input array is pre-allocated before the trace starts, so only
*auxiliary* bytes (frames, buffers, temps) appear in the peak figure.
"""

import random
import sys
import time
import tracemalloc
import math
import os

sys.path.insert(0, os.path.dirname(__file__))
from logos_sort import logos_sort_inplace

SIZES   = [500_000, 2_500_000, 10_000_000]
MAX_VAL = 1_000_000_000
RUNS    = 3


# ─────────────────────────────────────────────────────────────────────────────
# Pure Python bottom-up merge sort (one auxiliary buffer = O(n) space)
# ─────────────────────────────────────────────────────────────────────────────

def _isort(a, lo, hi):
    for i in range(lo + 1, hi + 1):
        key = a[i]; j = i - 1
        while j >= lo and a[j] > key: a[j + 1] = a[j]; j -= 1
        a[j + 1] = key


def merge_sort_inplace(arr):
    """Sort arr in place. O(n) auxiliary buffer, zero C sort calls."""
    n = len(arr)
    if n < 2:
        return
    BLOCK = 32
    lo = 0
    while lo < n:
        _isort(arr, lo, min(lo + BLOCK - 1, n - 1))
        lo += BLOCK

    buf = arr[:]          # <-- the single O(n) allocation
    width = BLOCK
    while width < n:
        lo = 0
        while lo < n:
            mid = min(lo + width, n)
            hi  = min(lo + 2 * width, n)
            if mid < hi:
                i, j, k = lo, mid, lo
                while i < mid and j < hi:
                    if arr[i] <= arr[j]: buf[k] = arr[i]; i += 1
                    else:                buf[k] = arr[j]; j += 1
                    k += 1
                while i < mid: buf[k] = arr[i]; i += 1; k += 1
                while j < hi:  buf[k] = arr[j]; j += 1; k += 1
                arr[lo:hi] = buf[lo:hi]
            lo += 2 * width
        width *= 2


# ─────────────────────────────────────────────────────────────────────────────
# Harness — timing and memory measured SEPARATELY to avoid tracer overhead
# ─────────────────────────────────────────────────────────────────────────────

def bench_time(fn, data):
    """Average wall-clock seconds over RUNS; tracemalloc is OFF."""
    total = 0.0
    for _ in range(RUNS):
        arr = data[:]
        t0  = time.perf_counter()
        fn(arr)
        total += time.perf_counter() - t0
    return total / RUNS


def bench_memory(fn, data):
    """Peak auxiliary bytes in ONE traced pass (input pre-allocated, not counted)."""
    arr = data[:]                   # input copy — outside trace window
    tracemalloc.clear_traces()
    tracemalloc.start()
    fn(arr)                         # only auxiliary allocs are counted
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def fmt_bytes(b):
    if b >= 1_048_576: return f"{b / 1_048_576:7.1f} MB"
    if b >= 1_024:     return f"{b / 1_024:7.1f} KB"
    return f"{b:7.0f}  B"


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

tracemalloc.start(); tracemalloc.stop()   # warm-up

SEP  = "-" * 76
DSEP = "=" * 76

print(DSEP)
print("LogosSort vs Pure-Python Merge Sort -- Time + Space Complexity")
print("Both pure Python, insertion-sort base, zero C sort calls.")
print("Timing: avg of 3 runs (no tracer).  Memory: 1 traced pass, aux only.")
print(DSEP)

for n in SIZES:
    print(f"\n  Generating {n:,} items...", end="\r", flush=True)
    data = [random.randint(0, MAX_VAL) for _ in range(n)]

    # --- time (no tracer overhead) ---
    logos_t = bench_time(logos_sort_inplace, data)
    merge_t = bench_time(merge_sort_inplace, data)
    tim_t   = bench_time(lambda a: a.sort(), data)

    # --- memory (one traced pass each) ---
    logos_mem = bench_memory(logos_sort_inplace, data)
    merge_mem = bench_memory(merge_sort_inplace, data)

    log2n = int(math.log2(n))
    theory_stack_kb = (2 * log2n + 4) * 2048 // 1024   # rough frame estimate

    print(f"\n  {n:,} items")
    print(SEP)
    print(f"  {'Algorithm':<20} {'Time':>8}  {'Peak Aux':>9}  {'B/item':>7}  Space")
    print(SEP)

    rows = [
        ("LogosSort (in-place)", logos_t, logos_mem,
         f"O(log n)  ~{theory_stack_kb} KB stack"),
        ("MergeSort (in-place)", merge_t, merge_mem,
         f"O(n)      one {fmt_bytes(merge_mem).strip()} buffer"),
    ]
    for name, t, mem, theory in rows:
        bpi = mem / n
        print(f"  {name:<20} {t:>6.3f}s  {fmt_bytes(mem):>9}  {bpi:>6.2f}B  {theory}")

    print(f"  {'list.sort() *':<20} {tim_t:>6.3f}s  {'n/a':>9}  {'n/a':>7}  "
          f"O(n)  (C-backed)")
    print(SEP)
    ratio_t = logos_t / merge_t
    ratio_m = logos_mem / merge_mem
    winner  = "LogosSort faster" if ratio_t < 1 else "MergeSort faster"
    print(f"  Time: {ratio_t:.2f}x ({winner})   "
          f"Memory: LogosSort uses {merge_mem / logos_mem:.0f}x less auxiliary space")

print("\n" + "-" * 76)
print("* list.sort() = CPython C-Timsort. Not a fair peer; shown for scale.")
print("-" * 76)
