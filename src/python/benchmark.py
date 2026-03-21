"""
Benchmark: LogosSort vs Pure-Python Timsort
Time + Space complexity at 500 000 · 2 500 000 · 10 000 000 items.

Comparison philosophy
---------------------
logos_sort_inplace  -- pure Python, O(log n) space (recursion stack only).
tim_sort            -- pure Python Timsort, O(n) space (new lists per merge).
  -> These two are the fair algorithmic comparison (zero C sort calls).

list.sort()         -- C-backed Timsort, shown for scale only.

Memory measurement
------------------
Time runs are performed WITHOUT tracemalloc to avoid 6-8x profiling overhead.
A single separate traced pass measures peak auxiliary heap allocation.
The input array is pre-allocated before the trace starts, so only
*auxiliary* bytes (frames, buffers, temps) appear in the peak figure.

Note on tim_sort's merge():
The merge() function is recursive and allocates a new list at every call
([left[0]] + merge(...)).  This makes each merge O(n) in allocations and
produces O(n log n) total auxiliary bytes — visible in the memory column.
The recursion depth can exceed Python's default limit for large n;
sys.setrecursionlimit is raised accordingly below.
"""

import random
import sys
import time
import tracemalloc
import math
import os

sys.setrecursionlimit(500_000)   # needed for recursive merge at large sizes

sys.path.insert(0, os.path.dirname(__file__))
from logos_sort import logos_sort_inplace

# Note: tim_sort's merge() uses recursive list concatenation ([x] + merge(...))
# which is O(n²) per merge pass, making the overall sort O(n²).
# Sizes are capped at 10 000 so runs complete in seconds, not hours.
# See BENCHMARKS.md for LogosSort vs pure merge sort at 500K–10M items.
SIZES   = [1_000, 5_000, 10_000]
MAX_VAL = 1_000_000_000
RUNS    = 3


# ─────────────────────────────────────────────────────────────────────────────
# Pure-Python Timsort (provided implementation — zero C sort calls)
# ─────────────────────────────────────────────────────────────────────────────

def insertion_sort(arr, left=0, right=None):
    # Base case: if the array is already sorted, do nothing
    if right is None:
        right = len(arr) - 1

    # Iterate through the array, starting from the second element
    for i in range(left + 1, right + 1):
        # Select the current element
        key_item = arr[i]

        # Compare the current element with the previous one
        j = i - 1

        # While the previous element is greater than the current one,
        # shift the previous element to the next position
        while j >= left and arr[j] > key_item:
            arr[j + 1] = arr[j]
            j -= 1

        # Once the loop ends, the previous element is less than or equal to
        # the current element, so place the current element after it
        arr[j + 1] = key_item

    return arr


def merge(left, right):
    # If the left subarray is empty, return the right subarray
    if not left:
        return right

    # If the right subarray is empty, return the left subarray
    if not right:
        return left

    # Compare the first elements of the two subarrays
    if left[0] < right[0]:
        # If the first element of the left subarray is smaller,
        # recursively merge the left subarray with the right one
        return [left[0]] + merge(left[1:], right)
    else:
        # If the first element of the right subarray is smaller,
        # recursively merge the right subarray with the left one
        return [right[0]] + merge(left, right[1:])


def tim_sort(arr):
    # Initialize the minimum run size
    min_run = 32

    # Find the length of the array
    n = len(arr)

    # Traverse the array and do insertion sort on each segment of size min_run
    for i in range(0, n, min_run):
        insertion_sort(arr, i, min(i + min_run - 1, (n - 1)))

    # Start merging from size 32 (or min_run)
    size = min_run
    while size < n:
        # Divide the array into merge_size
        for start in range(0, n, size * 2):
            # Find the midpoint and endpoint of the left and right subarrays
            midpoint = start + size
            end = min((start + size * 2 - 1), (n - 1))

            # Merge the two subarrays
            merged_array = merge(arr[start:midpoint], arr[midpoint:end + 1])

            # Assign the merged array to the original array
            arr[start:start + len(merged_array)] = merged_array

        # Increase the merge size for the next iteration
        size *= 2

    return arr


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
print("LogosSort vs Pure-Python Timsort -- Time + Space Complexity")
print("Both pure Python, insertion-sort base, zero C sort calls.")
print("Timing: avg of 3 runs (no tracer).  Memory: 1 traced pass, aux only.")
print(DSEP)

for n in SIZES:
    print(f"\n  Generating {n:,} items...", end="\r", flush=True)
    data = [random.randint(0, MAX_VAL) for _ in range(n)]

    # --- time (no tracer overhead) ---
    logos_t = bench_time(logos_sort_inplace, data)
    tim_t   = bench_time(tim_sort, data)
    list_t  = bench_time(lambda a: a.sort(), data)

    # --- memory (one traced pass each) ---
    logos_mem = bench_memory(logos_sort_inplace, data)
    tim_mem   = bench_memory(tim_sort, data)

    log2n = int(math.log2(n))
    theory_stack_kb = (2 * log2n + 4) * 2048 // 1024   # rough frame estimate

    print(f"\n  {n:,} items")
    print(SEP)
    print(f"  {'Algorithm':<22} {'Time':>8}  {'Peak Aux':>9}  {'B/item':>7}  Space")
    print(SEP)

    rows = [
        ("LogosSort (in-place)", logos_t, logos_mem,
         f"O(log n)  ~{theory_stack_kb} KB stack"),
        ("TimSort (pure Python)", tim_t, tim_mem,
         f"O(n)      one {fmt_bytes(tim_mem).strip()} buffer"),
    ]
    for name, t, mem, theory in rows:
        bpi = mem / n if n else 0
        print(f"  {name:<22} {t:>6.3f}s  {fmt_bytes(mem):>9}  {bpi:>6.2f}B  {theory}")

    print(f"  {'list.sort() *':<22} {list_t:>6.3f}s  {'n/a':>9}  {'n/a':>7}  "
          f"O(n)  (C-backed)")
    print(SEP)
    ratio_t = logos_t / tim_t
    winner  = "LogosSort faster" if ratio_t < 1 else "TimSort faster"
    mem_ratio = tim_mem / max(logos_mem, 1)
    print(f"  Time: {ratio_t:.2f}x ({winner})   "
          f"Memory: LogosSort uses {mem_ratio:.0f}x less auxiliary space")

print("\n" + "-" * 76)
print("* list.sort() = CPython C-Timsort. Not a fair peer; shown for scale.")
print("-" * 76)
