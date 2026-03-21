"""
Benchmark: LogosUltraSort vs list.sort()
Sizes: 500 000 · 2 500 000 · 10 000 000 (comparison sort path)
        1 000 000 000 (counting sort fast path, tight integer range)

NOTE — 1B items
  The 1B run uses integers in [0, 3] so logos_ultra_sort takes its counting
  sort fast path (O(n) time, O(range) aux space — 4 counters).
  Even so, the Python list backing store is ~8 GB of object pointers.
  Ensure ≥16 GB free RAM before running that section.

Both timing passes run WITHOUT tracemalloc to avoid profiler overhead.
Memory is measured in a separate traced pass (input pre-allocated, not counted).
"""

import random
import sys
import time
import tracemalloc
import math
import os

# ── Import logos_ultra_sort ────────────────────────────────────────────────────
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_ULTRA_FILE = os.path.join(_REPO_ROOT, "logos_ultra_sort (1).py")

import importlib.util
_spec = importlib.util.spec_from_file_location("logos_ultra_sort_mod", _ULTRA_FILE)
_mod  = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
logos_ultra_sort = _mod.logos_ultra_sort

# Also import the canonical in-place variant for comparison
sys.path.insert(0, os.path.dirname(__file__))
from logos_sort import logos_sort_inplace


# ── Config ────────────────────────────────────────────────────────────────────
SIZES   = [500_000, 2_500_000, 10_000_000]
MAX_VAL = 1_000_000_000
RUNS    = 3          # timing runs per (algorithm, size) pair


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
print("  LogosUltraSort vs logos_sort_inplace vs list.sort()  —  Time + Space")
print("  Timing: avg of 3 runs (no tracer).  Memory: 1 traced pass, aux only.")
print(DSEP)

for n in SIZES:
    print(f"\n  Generating {n:,} random integers…", end="\r", flush=True)
    data = [random.randint(0, MAX_VAL) for _ in range(n)]

    # timing
    ultra_t   = bench_time(logos_ultra_sort,  data)
    inplace_t = bench_time(logos_sort_inplace, data, inplace=True)
    list_t    = bench_time(lambda a: a.sort(), data, inplace=True)

    # memory
    ultra_mem   = bench_memory(logos_ultra_sort,  data)
    inplace_mem = bench_memory(logos_sort_inplace, data, inplace=True)

    log2n = int(math.log2(n))
    stack_kb = (2 * log2n + 4) * 2048 // 1024

    print(f"\n  {n:,} items  (random ints 0..{MAX_VAL:,})")
    print(SEP)
    print(f"  {'Algorithm':<26} {'Time':>8}   {'Peak Aux':>10}   {'B/item':>7}   Space theory")
    print(SEP)

    rows = [
        ("LogosUltraSort",        ultra_t,   ultra_mem,
         f"O(log n)  ~{stack_kb} KB stack"),
        ("logos_sort_inplace",    inplace_t, inplace_mem,
         f"O(log n)  ~{stack_kb} KB stack"),
    ]
    for name, t, mem, theory in rows:
        bpi = mem / n if n else 0
        print(f"  {name:<26} {t:>6.3f}s   {fmt_bytes(mem):>10}   {bpi:>6.2f}B   {theory}")

    print(f"  {'list.sort() *':<26} {list_t:>6.3f}s   {'n/a':>10}   {'n/a':>7}   O(n) C-backed")
    print(SEP)

    if ultra_t > 0 and inplace_t > 0:
        ratio = ultra_t / inplace_t
        faster = "UltraSort faster" if ratio < 1 else "inplace faster"
        print(f"  Ultra vs inplace: {ratio:.2f}x ({faster})")
    if ultra_t > 0 and list_t > 0:
        print(f"  list.sort() is {ultra_t / list_t:.1f}x faster than UltraSort (C vs pure Python)")


# ── 1 billion item counting-sort trial ───────────────────────────────────────
print("\n" + DSEP)
print("  1 000 000 000-item trial  (counting sort fast path)")
print("  Integer values in [0, 3] — span < 4×n triggers O(n) counting sort.")
print(f"  List pointer store alone ≈ {1_000_000_000 * 8 / 1_073_741_824:.1f} GB; ensure ≥16 GB free RAM.")
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
    logos_ultra_sort(arr)
    ultra_1b = time.perf_counter() - t0

    arr2 = data1b[:]
    t0   = time.perf_counter()
    arr2.sort()
    list_1b = time.perf_counter() - t0

    del arr, arr2   # free before memory pass

    print(f"\n  1,000,000,000 items  (range 0–3, counting sort path)")
    print(SEP)
    print(f"  {'Algorithm':<26} {'Time':>8}   Notes")
    print(SEP)
    print(f"  {'LogosUltraSort':<26} {ultra_1b:>6.2f}s   O(n), 4-entry count array")
    print(f"  {'list.sort() *':<26} {list_1b:>6.2f}s   C-backed Timsort")
    print(SEP)
    print(f"  list.sort() is {ultra_1b / list_1b:.1f}x faster than UltraSort at 1B items")

except MemoryError:
    print("\n  MemoryError: not enough RAM for 1B-item Python list on this machine.")
    print("  Estimated requirement: ~16 GB free (8 GB pointers + OS/interpreter overhead).")

print("\n" + SEP)
print("  * list.sort() = CPython C-Timsort — not a fair peer; shown for scale.")
print(SEP)
