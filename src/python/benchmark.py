"""
Benchmark: LogosSort vs Timsort
Sizes: 500 000 · 2 500 000 · 10 000 000
Data:  random integers in [0, 1 000 000 000]
"""

import random
import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from logos_sort import logos_sort

SIZES   = [500_000, 2_500_000, 10_000_000]
MAX_VAL = 1_000_000_000
RUNS    = 3   # average over N runs per size


def bench(fn, data: list) -> float:
    arr = data[:]
    t0  = time.perf_counter()
    fn(arr)
    return time.perf_counter() - t0


def timsort_inplace(arr: list) -> list:
    arr.sort()
    return arr


def logos_wrapper(arr: list) -> list:
    result = logos_sort(arr)
    arr[:] = result
    return arr


print("LogosSort vs Timsort — Python reference benchmark")
print("=" * 60)
print(f"{'Size':>12}  {'LogosSort':>11}  {'Timsort':>11}  {'Ratio':>7}")
print("-" * 60)

for n in SIZES:
    print(f"  Generating {n:,} random ints...", end="\r", flush=True)
    data = [random.randint(0, MAX_VAL) for _ in range(n)]

    logos_times = []
    tim_times   = []

    for _ in range(RUNS):
        logos_times.append(bench(logos_wrapper, data))
        tim_times.append(bench(timsort_inplace, data))

    logos_avg = sum(logos_times) / RUNS
    tim_avg   = sum(tim_times)   / RUNS
    ratio     = logos_avg / tim_avg

    print(f"{n:>12,}  {logos_avg:>9.3f}s  {tim_avg:>9.3f}s  {ratio:>6.2f}x")

print()
print("Note: Python LogosSort adds orchestration overhead on top of Timsort")
print("      (which is invoked for base cases). See C++/Rust for native performance.")
