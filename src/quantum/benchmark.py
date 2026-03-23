"""
LogosSort -- Quantum vs. Classical Benchmark
=============================================
Compares two pivot-entropy sources head-to-head:

  CLASSICAL  random.uniform()   -- one PRNG draw per partition, per sort
  QUANTUM    Hadamard oracle    -- all chaos values drawn in ONE batched
                                   quantum job before sorting begins;
                                   each sort call pops from an in-memory pool

The sort logic is otherwise identical (same dual-pivot, ninther, counting-sort
fast path, depth budget, tail-call loop).  Only the chaos source differs.

Batched quantum approach
------------------------
Total chaos values needed = sum(trials for each size).  A QuantumChaosPool is
built once with that many shots in a single Qiskit job.  Subsequent pool.draw()
calls are O(1) deque pops -- no network, no simulator overhead.

This means the "quantum overhead" column shows the amortised per-sort cost of
the single upfront batch, not a per-sort API round-trip.

Usage
-----
  # from the repo root:
  python src/quantum/benchmark.py

  # custom sizes:
  python src/quantum/benchmark.py --sizes 500 5000 50000

  # more trials:
  python src/quantum/benchmark.py --trials 10

  # use real IBM Quantum hardware for the batch QRNG job:
  python src/quantum/benchmark.py --hardware
"""

import argparse
import os
import random
import sys
import time

# ── Path setup ────────────────────────────────────────────────────────────────
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from logos_sort import logos_sort as logos_sort_classical
from src.quantum.logos_sort_quantum import (
    logos_sort_quantum,
    QuantumChaosPool,
    _resolve_backend,
)

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_SIZES  = [1_000, 10_000, 100_000, 10_000_000]
MAX_TRIALS = {
    1_000:       20,
    10_000:      10,
    100_000:      5,
    10_000_000:   3,
}
DEFAULT_TRIALS = 5


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_array(n: int, seed: int = 0) -> list[int]:
    rng = random.Random(seed)
    return [rng.randint(0, n * 10) for _ in range(n)]


def _fmt(seconds: float) -> str:
    if seconds >= 1.0:
        return f"{seconds:8.3f} s "
    if seconds >= 1e-3:
        return f"{seconds * 1e3:8.2f} ms"
    return f"{seconds * 1e6:8.1f} us"


def _fmt_n(n: int) -> str:
    if n >= 1_000_000:
        return f"{n // 1_000_000}M"
    if n >= 1_000:
        return f"{n // 1_000}K"
    return str(n)


# ── Timed runners ─────────────────────────────────────────────────────────────

def bench_classical(arr: list, trials: int) -> dict:
    total = 0.0
    result = None
    for _ in range(trials):
        a = arr[:]
        t0 = time.perf_counter()
        result = logos_sort_classical(a)
        total += time.perf_counter() - t0
    return {"mean": total / trials, "result": result}


def bench_quantum(arr: list, trials: int, pool: QuantumChaosPool) -> dict:
    """Sort *trials* times, drawing chaos values from the pre-built pool."""
    sort_total = 0.0
    result = None
    for _ in range(trials):
        a         = arr[:]
        chaos_int = pool.draw()          # O(1) deque pop -- no API call
        t0        = time.perf_counter()
        result    = logos_sort_quantum(a, chaos_int=chaos_int)
        sort_total += time.perf_counter() - t0
    return {"sort_mean": sort_total / trials, "result": result}


# ── Verification ──────────────────────────────────────────────────────────────

def _verify(a: list, b: list, n: int) -> str:
    if a == b:
        return "OK identical"
    a_ok = all(a[i] <= a[i+1] for i in range(n-1))
    b_ok = all(b[i] <= b[i+1] for i in range(n-1))
    return "OK both sorted" if (a_ok and b_ok) else "FAIL sort error"


# ── Report ────────────────────────────────────────────────────────────────────

W = 80

def _header(pool_time: float, total_sorts: int):
    amortised = pool_time / total_sorts if total_sorts else 0
    print()
    print("LogosSort -- Quantum Hadamard Oracle (batched) vs. Classical random.uniform")
    print(f"  Quantum pool: {_fmt(pool_time).strip()} for {total_sorts} chaos values "
          f"({_fmt(amortised).strip()} amortised per sort)")
    print("-" * W)
    print(f"{'Size':>6}  {'Trials':>6}  "
          f"{'Classical':>12}  "
          f"{'Q sort':>10}  {'Q+amort':>10}  "
          f"{'Speedup':>9}  {'Verify':>14}")
    print("-" * W)


def _row(n, trials, c, q, pool_time, total_sorts):
    amortised  = pool_time / total_sorts if total_sorts else 0
    q_total    = q["sort_mean"] + amortised
    speedup    = c["mean"] / q_total if q_total > 0 else float("inf")
    verify     = _verify(c["result"], q["result"], n)
    print(
        f"{_fmt_n(n):>6}  {trials:>6}  "
        f"{_fmt(c['mean']):>12}  "
        f"{_fmt(q['sort_mean']):>10}  "
        f"{_fmt(q_total):>10}  "
        f"{speedup:>8.2f}x  "
        f"{verify:>14}"
    )


def _footer(backend_label: str):
    print("-" * W)
    print()
    print("Columns")
    print("  Classical  : logos_sort() -- random.uniform() called once per partition")
    print("  Q sort     : sort kernel  -- quantum chaos_int from pool, same algorithm")
    print("  Q+amort    : Q sort + (pool build time / total sorts)")
    print("  Speedup    : Classical / Q+amort")
    print()
    print(f"Quantum backend : {backend_label}")
    print("Array type      : random integers, uniform distribution")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="LogosSort quantum benchmark")
    parser.add_argument(
        "--sizes", nargs="+", type=int, default=DEFAULT_SIZES, metavar="N",
    )
    parser.add_argument("--trials", type=int, default=None)
    parser.add_argument(
        "--hardware", action="store_true",
        help="Use real IBM Quantum hardware for the QRNG batch job",
    )
    args = parser.parse_args()

    # ── Resolve trial counts ──────────────────────────────────────────────────
    trial_map   = {n: (args.trials or MAX_TRIALS.get(n, DEFAULT_TRIALS))
                   for n in args.sizes}
    total_sorts = sum(trial_map.values())

    # ── Backend ───────────────────────────────────────────────────────────────
    if args.hardware:
        backend, is_hw = _resolve_backend()
    else:
        from qiskit_aer import AerSimulator
        backend = AerSimulator()
        is_hw   = False

    backend_label = (
        f"IBM Quantum ({getattr(backend, 'name', os.getenv('IBM_QUANTUM_BACKEND', 'hardware'))})"
        if is_hw else "Qiskit Aer (local noiseless simulator)"
    )
    print(f"\nBackend : {backend_label}")

    # ── Build the pool (ONE quantum job for all sorts) ────────────────────────
    print(f"Building quantum chaos pool ({total_sorts} shots)...", end=" ", flush=True)
    t0         = time.perf_counter()
    pool       = QuantumChaosPool(backend=backend, size=total_sorts, n_qubits=53)
    pool_time  = time.perf_counter() - t0
    print(f"done in {_fmt(pool_time).strip()}.")

    # ── Benchmark loop ────────────────────────────────────────────────────────
    _header(pool_time, total_sorts)

    rows = []
    for n in args.sizes:
        trials = trial_map[n]
        arr    = _make_array(n, seed=42)
        print(f"  [{_fmt_n(n):>5}] {trials} trial(s)...", end="\r", flush=True)
        c = bench_classical(arr, trials)
        q = bench_quantum(arr, trials, pool)
        rows.append((n, trials, c, q))
        _row(n, trials, c, q, pool_time, total_sorts)

    _footer(backend_label)


if __name__ == "__main__":
    main()
