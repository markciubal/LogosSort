# LogosSort

> "In the beginning was the Logos, and the Logos was with God, and the Logos was God." — John 1:1

A golden-ratio dual-pivot introsort with oracle-seeded randomisation. Pure Python — zero calls to C sort functions anywhere.

---

## How it works — and why

Sorting is the problem of taking a collection of items in arbitrary order and producing them in the one arrangement that is most knowable: smallest to largest, or by any other criterion. It is one of the oldest problems in computing, and its theoretical limit is well-established: no comparison-based sort can do better than O(n log n) comparisons on average. LogosSort meets that bound — and guarantees it in the worst case as well.

**Divide and conquer**

The algorithm works by repeatedly dividing an unsorted region into smaller pieces, sorting each piece, and combining them. This is the idea behind quicksort, invented by Tony Hoare in 1959. The key insight: pick a "pivot" value, split the array into elements smaller than it and elements larger, and both halves become independent subproblems — smaller problems converge faster.

LogosSort uses *two* pivots at once, producing *three* regions (less than, between, and greater than). This dual-pivot approach was introduced by Vladimir Yaroslavskiy and adopted as Java's standard sort in 2009. It reduces the average number of comparisons by roughly 5% compared to single-pivot quicksort.

**Why the golden ratio**

Where to place the pivots matters enormously. Pivots near the same value leave one region nearly empty — little progress. Pivots near the extremes pack almost everything into the middle. The ideal is pivots near the 38th and 62nd percentiles, splitting the array into rough thirds. Those proportions are exactly 1−φ and φ, where φ ≈ 0.618 is the golden ratio — the fixed point of the Fibonacci recurrence. It is the "most irrational" real number, hardest to approximate by simple fractions, and therefore optimal for evenly spacing two values within any range. The same property accounts for its appearance in plant growth patterns, crystal structure, and classical proportion.

**Why randomisation**

A fixed pivot position is a vulnerability. An adversary who knows your algorithm can craft an input — a nearly-sorted array, or one with duplicates in a specific pattern — that forces every partition to be wildly uneven, degrading performance from O(n log n) to O(n²). This is a known and documented attack on deterministic quicksort variants.

LogosSort draws a fresh random number from the operating system's entropy source on every call and uses it to determine *where to look* for pivot candidates, not which values to pick. No adversary who knows the algorithm can predict this number in advance. The algorithm cannot be defeated by any fixed input.

**Why the ninther**

A single randomly-chosen element is a noisy estimate of the array's median — about one time in four it lands in the outermost quartile, meaning one partition ends up three times the size of the other. The ninther technique (due to John Tukey) takes the median of three neighboring elements around each candidate. This concentrates the pivot estimate near the true median with only three comparisons, reducing pivot error to O(1/n) without scanning the whole array.

**Guaranteed worst case**

Classic quicksort, even with randomisation, has a theoretical O(n²) worst case — randomisation makes it astronomically unlikely, but does not eliminate it. LogosSort removes it entirely. A depth counter tracks the recursion level. If it exceeds 2⌊log₂n⌋ + 4, the algorithm switches to insertion sort for that subarray. This depth-budget mechanism was proven by David Musser to guarantee O(n log n) worst-case time regardless of input — the same mechanism used by C++'s `std::sort` (Musser, "Introspective Sorting and Selection Algorithms," *Software: Practice and Experience*, 1997).

**The result**

These four ideas — golden-ratio dual pivots, oracle seeding, ninther refinement, and the depth budget — combine into an algorithm that runs in O(n log n) time in *all* cases, cannot be forced into slow behavior by any fixed input, and chooses better-than-random pivots without scanning the whole array. Additional fast paths handle already-sorted data in O(n), dense integer data in O(n) via counting sort, and small subarrays with insertion sort, which beats comparison sort entirely when n is small.

---

## Algorithm overview

| Property | Value |
|---|---|
| **Time — average** | O(n log n) |
| **Time — worst case** | O(n log n) ¹ |
| **Time — best case** | O(n) ² |
| **Space (logos_sort)** | O(n) copy + O(log n) stack |
| **Space (logos_sort_inplace)** | O(log n) stack only |
| **Stable** | Yes when `key=` is used (Schwartzian transform) |
| **Adaptive** | Yes (monotone fast-path) |

¹ Depth budget (2⌊log₂n⌋ + 4): if recursion exceeds this bound, insertion sort is substituted, guaranteeing O(n log n) worst case regardless of pivot quality.
² Already-sorted ascending/descending arrays detected in O(n) with early exit.

### Key innovations

**Golden-ratio pivot placement**
Two pivots placed at φ ≈ 0.618 and 1−φ ≈ 0.382 of a randomised position index.
This mirrors how φ divides the number line optimally (Fibonacci spacing), creating
pivots that are neither too close together nor too far apart.

**Oracle-seeded randomisation**
A fresh random float seeds each sort call. It determines *where to look* for pivots,
not the pivot values themselves. This defeats adversarial inputs (sorted,
reverse-sorted, organ-pipe, killer sequences) that cause O(n²) behaviour in
deterministic quicksort variants.

**Ninther pivot refinement**
Each candidate pivot index is refined with a median-of-3-neighbours
([ninther](https://dl.acm.org/doi/10.1145/22664.22667) technique), producing a
pivot estimate that resists outliers with only three comparisons.

**Three-way dual-pivot partition**
Elements are partitioned into *strictly less than p1*, *between p1 and p2*, and
*strictly greater than p2* in a single left-to-right scan. Equal elements cluster
in the middle region and are never examined again — efficient on duplicate-heavy data.

**Counting-sort fast path**
When sorting integers whose value range is less than 4× the subarray length,
LogosSort switches to counting sort: O(n) time, zero comparisons.

**Tail-call optimisation**
The two smaller partitions recurse; the largest becomes the next loop iteration.
Stack depth is bounded to O(log n) regardless of partition balance.

---

## Python API

```python
from logos_sort import logos_sort, logos_sort_inplace

# Returns a new sorted list — original unchanged
logos_sort([3, 1, 4, 1, 5])              # [1, 1, 3, 4, 5]
logos_sort([3, 1, 4], reverse=True)      # [4, 3, 1]
logos_sort(['Banana', 'apple'], key=str.lower)  # ['apple', 'Banana']

# Sorts in place — returns None
logos_sort_inplace(arr)
logos_sort_inplace(arr, reverse=True)
logos_sort_inplace(arr, key=abs)
```

Both functions accept `key=` and `reverse=` with the same semantics as Python's
built-in `sorted()`. When `key=` is given, a Schwartzian transform is used
(decorate–sort–undecorate) and the sort is **stable**.

### Install

```bash
pip install .          # from repo root — installs logos_sort and logos_sort_embed
```

Or drop `logos_sort_embed.py` directly into any project — it is fully self-contained
with no external imports.

---

## Implementations

| Language | Source | Benchmark | Run |
|---|---|---|---|
| Python | [logos_sort.py](logos_sort.py) | [benchmark.py](src/python/benchmark.py) | `python benchmark.py` |
| JavaScript | [src/javascript/logos_sort.js](src/javascript/logos_sort.js) | [benchmark.js](src/javascript/benchmark.js) | `node benchmark.js` |
| TypeScript | [src/typescript/logos_sort.ts](src/typescript/logos_sort.ts) | [benchmark.ts](src/typescript/benchmark.ts) | `ts-node benchmark.ts` |
| Java | [src/java/LogosSort.java](src/java/LogosSort.java) | [Benchmark.java](src/java/Benchmark.java) | See below |
| C++ | [src/cpp/logos_sort.hpp](src/cpp/logos_sort.hpp) | [benchmark.cpp](src/cpp/benchmark.cpp) | `g++ -O2 -std=c++17 -o bench benchmark.cpp && ./bench` |
| C# | [src/csharp/LogosSort.cs](src/csharp/LogosSort.cs) | [Benchmark.cs](src/csharp/Benchmark.cs) | `dotnet run` |
| Go | [src/go/logos_sort.go](src/go/logos_sort.go) | [benchmark_test.go](src/go/benchmark_test.go) | `go test -bench=. -benchtime=3x` |
| Rust | [src/rust/src/lib.rs](src/rust/src/lib.rs) | [main.rs](src/rust/src/main.rs) | `cargo run --release` |
| Swift | [src/swift/LogosSort.swift](src/swift/LogosSort.swift) | [Benchmark.swift](src/swift/Benchmark.swift) | `swiftc -O LogosSort.swift Benchmark.swift -o bench && ./bench` |
| Kotlin | [src/kotlin/LogosSort.kt](src/kotlin/LogosSort.kt) | [Benchmark.kt](src/kotlin/Benchmark.kt) | `kotlinc *.kt -include-runtime -d bench.jar && java -jar bench.jar` |
| R | [src/r/logos_sort.R](src/r/logos_sort.R) | — | `Rscript src/r/logos_sort.R` |

### Java
```bash
javac -d out src/java/LogosSort.java src/java/Benchmark.java
java -cp out logossort.Benchmark
```

---

## Benchmark results (summary)

Sorting 10,000,000 random integers in `[0, 10⁹]`:

| Language | LogosSort | Built-in sort | Ratio |
|---|---|---|---|
| Python (reference) | 33.4 s | 4.0 s (Timsort/C) | 8.3× slower ³ |
| C++ | ~0.97 s | ~1.05 s (introsort) | **~8% faster** |
| Java | ~1.15 s | ~1.35 s (dual-pivot QS) | **~15% faster** |
| Go | ~1.22 s | ~1.38 s (pdqsort) | **~12% faster** |
| Rust | ~0.88 s | ~0.95 s (pdqsort) | **~7% faster** |

³ Python overhead: the orchestration layer runs in pure Python bytecode while `list.sort()`
is compiled C. This is expected — see [BENCHMARKS.md](BENCHMARKS.md) for a full explanation.
Pure-Python MergeSort is the fair comparison; against it, LogosSort wins on both time and
memory at every tested size.

**Full benchmark results, methodology, and adversarial-input notes → [BENCHMARKS.md](BENCHMARKS.md)**

---

## Algorithm walkthrough

```
logos_sort([64, 34, 25, 12, 22, 11, 90, 42, 5, 77])

1. depth_limit = 2·⌊log₂(10)⌋ + 4 = 10

2. size=10 ≤ 48? No — skip insertion sort fast exit
   Integer span check: range = 90−5 = 85. 85 < 10×4 = 40? No — skip counting sort

3. Oracle: c = 0.7341…  →  chaos_int = abs(c) · 2^53
   idx1 = 0 + ⌊9 · (1−φ) · absC⌋  →  pivot candidate near 28%
   idx2 = 0 + ⌊9 ·    φ  · absC⌋  →  pivot candidate near 45%

4. Ninther at idx1: median(64, 25, 12) = 25  →  p1 = 25
   Ninther at idx2: median(12, 22, 11) = 12  →  p2 = 12

5. Dual partition with p1=12, p2=25 (swapped since 12 < 25):
   left  (< 12): [11, 5]
   middle (12–25): [12, 22, 25]
   right  (> 25): [64, 34, 90, 42, 77]

6. Recurse into left (n=2) and middle (n=3); loop on right (n=5)

7. All regions eventually reach ≤ 48 → insertion sort finalises them
```

---

## Philosophy

The algorithm's structure reflects its name:

- **Logos** (λόγος) — the rational principle underlying order; expressed here as
  the golden ratio, which describes optimal natural proportions from nautilus shells
  to phyllotaxis.
- **Oracle seed** — randomisation without determinism; unpredictable pivot positions
  mean no adversary can craft a worst-case input.
- **Ninther / dialectic** — thesis, antithesis, synthesis: three candidate values
  resolved to their median, cancelling extremes.
- **Depth limit / wu wei** — knowing when to stop; when the recursion budget is
  exhausted, the algorithm yields to insertion sort rather than recurse forever.
- **The algorithm waits, then acts** — monotone detection checks for existing order
  before partitioning. If order is already present, it withdraws without disturbing
  what it finds. Only into genuine disorder does it intervene.

See [logos_sort_commented.py](logos_sort_commented.py) for six discipline-specific
annotated versions (philosophy, biology, political science, religion, history, mathematics).

---

## Testing

```bash
python -m pytest          # requires: pip install pytest
# or without pytest:
python tests/test_logos_sort.py -v
```

41 tests covering correctness, edge cases, `key=`, `reverse=`, stability, and
parity between `logos_sort` and `logos_sort_embed`.

---

## License

[Unlicense](LICENSE) — public domain.
