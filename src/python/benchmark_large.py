"""
Benchmark: LogosSort (copy) vs logos_sort_inplace vs pure-Python TimSort
Sizes: 500 000 · 2 500 000 · 10 000 000 (comparison sort path)
        1 000 000 000 (counting sort fast path, tight integer range)

All three algorithms are pure Python — zero C sort calls.

NOTE — TimSort size cap
  The pure-Python tim_sort (from benchmark.py) uses a recursive merge() that
  allocates [x] + merge(...) at every call, giving O(n^2) total allocations.
  It is only run for n <= TIM_MAX (10 000); above that its column is skipped.

NOTE — 1B items
  The 1B run uses integers in [0, 3] so logos_sort takes its counting
  sort fast path (O(n) time, O(range) aux space — 4 counters).
  Even so, the Python list backing store is ~8 GB of object pointers.
  Ensure >=16 GB free RAM before running that section.

Both timing passes run WITHOUT tracemalloc to avoid profiler overhead.
Memory is measured in a separate traced pass (input pre-allocated, not counted).
"""

import random
import sys
import time
import tracemalloc
import math
import os

# Force UTF-8 output on Windows terminals that default to cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Import logos_sort (copy-returning variant, source of truth) ────────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _REPO_ROOT)
from logos_sort import logos_sort as logos_sort_copy

# Also import the canonical in-place variant and pure-Python TimSort
sys.path.insert(0, os.path.dirname(__file__))
from logos_sort import logos_sort_inplace
from benchmark import insertion_sort, merge, tim_sort


# ── Config ────────────────────────────────────────────────────────────────────
SIZES   = [500_000, 2_500_000, 10_000_000]
MAX_VAL = 1_000_000_000
RUNS    = 3          # timing runs per (algorithm, size) pair
TIM_MAX = 10_000     # tim_sort's recursive merge is O(n^2) allocs; cap here


# ── Harness ───────────────────────────────────────────────────────────────────

def bench_time(fn, data, *, inplace=False):
    """Average wall-clock seconds over RUNS; tracemalloc OFF."""
    total = 0.0
    for _ in range(RUNS):
        arr = data[:]
        t0  = time.perf_counter()
        fn(arr) if inplace else fn(arr)
        total += time.perf_counter() - t0
    return total / RUNS


def bench_memory(fn, data, *, inplace=False):
    """Peak auxiliary bytes in ONE traced pass (input copy pre-allocated)."""
    arr = data[:]
    tracemalloc.clear_traces()
    tracemalloc.start()
    fn(arr) if inplace else fn(arr)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def fmt_bytes(b):
    if b >= 1_073_741_824: return f"{b / 1_073_741_824:7.2f} GB"
    if b >= 1_048_576:     return f"{b / 1_048_576:7.1f} MB"
    if b >= 1_024:         return f"{b / 1_024:7.1f} KB"
    return f"{b:7.0f}  B"


# ── Main ──────────────────────────────────────────────────────────────────────
tracemalloc.start(); tracemalloc.stop()   # warm-up

SEP  = "-" * 80
DSEP = "=" * 80

print(DSEP)
print("  LogosSort (copy) vs logos_sort_inplace vs pure-Python TimSort  —  Time + Space")
print("  All pure Python, zero C sort calls.")
print("  Timing: avg of 3 runs (no tracer).  Memory: 1 traced pass, aux only.")
print(f"  TimSort column shown only for n <= {TIM_MAX:,} (recursive merge is O(n^2) allocs).")
print(DSEP)

for n in SIZES:
    print(f"\n  Generating {n:,} random integers…", end="\r", flush=True)
    data = [random.randint(0, MAX_VAL) for _ in range(n)]

    run_tim = n <= TIM_MAX

    # timing
    copy_t    = bench_time(logos_sort_copy,    data)
    inplace_t = bench_time(logos_sort_inplace, data, inplace=True)
    tim_t     = bench_time(tim_sort, data, inplace=True) if run_tim else None

    # memory
    copy_mem    = bench_memory(logos_sort_copy,    data)
    inplace_mem = bench_memory(logos_sort_inplace, data, inplace=True)
    tim_mem     = bench_memory(tim_sort, data, inplace=True) if run_tim else None

    log2n = int(math.log2(n))
    stack_kb = (2 * log2n + 4) * 2048 // 1024

    print(f"\n  {n:,} items  (random ints 0..{MAX_VAL:,})")
    print(SEP)
    print(f"  {'Algorithm':<26} {'Time':>8}   {'Peak Aux':>10}   {'B/item':>7}   Space theory")
    print(SEP)

    rows = [
        ("logos_sort (copy)",   copy_t,    copy_mem,
         f"O(log n)  ~{stack_kb} KB stack"),
        ("logos_sort_inplace",  inplace_t, inplace_mem,
         f"O(log n)  ~{stack_kb} KB stack"),
    ]
    for name, t, mem, theory in rows:
        bpi = mem / n if n else 0
        print(f"  {name:<26} {t:>6.3f}s   {fmt_bytes(mem):>10}   {bpi:>6.2f}B   {theory}")

    if run_tim:
        bpi = tim_mem / n if n else 0
        print(f"  {'TimSort (pure Python)':<26} {tim_t:>6.3f}s   {fmt_bytes(tim_mem):>10}   {bpi:>6.2f}B   O(n log n) allocs")
    else:
        print(f"  {'TimSort (pure Python)':<26} {'--':>8}   {'n/a':>10}   {'n/a':>7}   skipped (n > {TIM_MAX:,})")
    print(SEP)

    if copy_t > 0 and inplace_t > 0:
        ratio = copy_t / inplace_t
        faster = "copy faster" if ratio < 1 else "inplace faster"
        print(f"  copy vs inplace: {ratio:.2f}x ({faster})")
    if run_tim and tim_t and copy_t > 0:
        ratio2 = copy_t / tim_t
        faster2 = "logos_sort faster" if ratio2 < 1 else "TimSort faster"
        print(f"  logos_sort vs TimSort: {ratio2:.2f}x ({faster2})")


# ── 1 billion item counting-sort trial ───────────────────────────────────────
print("\n" + DSEP)
print("  1 000 000 000-item trial  (counting sort fast path)")
print("  Integer values in [0, 3] -- span < 4xn triggers O(n) counting sort.")
print(f"  List pointer store alone ~{1_000_000_000 * 8 / 1_073_741_824:.1f} GB; ensure >=16 GB free RAM.")
print(DSEP)

N1B = 1_000_000_000

try:
    print(f"  Allocating {N1B:,} integers…", end="\r", flush=True)
    t_alloc = time.perf_counter()
    data1b  = [random.randint(0, 3) for _ in range(N1B)]
    alloc_s = time.perf_counter() - t_alloc
    print(f"  Allocation done in {alloc_s:.1f}s                                ")

    arr = data1b[:]
    t0  = time.perf_counter()
    logos_sort_copy(arr)
    copy_1b = time.perf_counter() - t0

    arr2 = data1b[:]
    t0   = time.perf_counter()
    logos_sort_inplace(arr2)
    inplace_1b = time.perf_counter() - t0

    del arr, arr2   # free before memory pass

    print(f"\n  1,000,000,000 items  (range 0-3, counting sort path)")
    print(SEP)
    print(f"  {'Algorithm':<26} {'Time':>8}   Notes")
    print(SEP)
    print(f"  {'logos_sort (copy)':<26} {copy_1b:>6.2f}s   O(n), 4-entry count array")
    print(f"  {'logos_sort_inplace':<26} {inplace_1b:>6.2f}s   O(n), 4-entry count array")
    print(f"  {'TimSort (pure Python)':<26} {'--':>8}   skipped — O(n^2) allocs, infeasible at 1B")
    print(SEP)
    ratio_1b = copy_1b / inplace_1b if inplace_1b > 0 else float('inf')
    faster_1b = "copy faster" if ratio_1b < 1 else "inplace faster"
    print(f"  copy vs inplace at 1B: {ratio_1b:.2f}x ({faster_1b})")

except MemoryError:
    print("\n  MemoryError: not enough RAM for 1B-item Python list on this machine.")
    print("  Estimated requirement: ~16 GB free (8 GB pointers + OS/interpreter overhead).")

print("\n" + SEP)
print("  TimSort skipped above TIM_MAX: its recursive merge() is O(n^2) in allocations.")
print(SEP)
