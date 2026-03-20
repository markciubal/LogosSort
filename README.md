# LogosSort

> A golden-ratio dual-pivot introsort with oracle-seeded randomisation.

LogosSort is a comparison-based sorting algorithm that places two pivots at the
**golden-ratio positions** (≈38.2% and ≈61.8%) of a randomised index, partitions
into three regions, and recurses depth-first into the two smallest while
tail-calling into the largest — keeping the call stack O(log n) even in
pathological cases.

---

## Algorithm overview

| Property | Value |
|---|---|
| **Time — average** | O(n log n) |
| **Time — worst case** | O(n log n) ¹ |
| **Time — best case** | O(n) ² |
| **Space (auxiliary)** | O(log n) |
| **Stable** | No (in-place swaps) |
| **Adaptive** | Yes (monotone fast-path) |

¹ Depth budget (2⌊log₂n⌋ + 4) falls back to the platform's built-in sort, guaranteeing O(n log n).
² Already-sorted ascending/descending arrays detected in O(n) with early exit.

### Key innovations

**Golden-ratio pivot placement**
Instead of picking a fixed median-of-three or random pivot, LogosSort uses the golden
ratio φ ≈ 0.618 and its complement 1−φ ≈ 0.382 to place two pivots at naturally
well-spaced positions within the subarray. This mirrors the way φ divides the number
line optimally (Fibonacci spacing), creating two pivots that are neither too close
together nor too far apart.

**Oracle-seeded randomisation**
A fresh random float seeds each sort call. It is not the pivot *value* — it is a
*position multiplier* that determines where in the subarray to look for each pivot.
This makes the pivot positions unpredictable without a fixed seed, defeating
adversarial inputs (sorted, reverse-sorted, organ-pipe, killer sequences) that
cause O(n²) behaviour in deterministic quicksort variants.

**Ninther pivot refinement**
Each candidate pivot index is refined with a median-of-3-neighbours (the
[ninther](https://dl.acm.org/doi/10.1145/22664.22667) technique), producing a
pivot estimate that resists outliers with only three comparisons.

**Three-way dual-pivot partition**
Elements are partitioned into *strictly less than p1*, *between p1 and p2*, and
*strictly greater than p2* in a single left-to-right scan with O(1) extra space.
Equal elements cluster in the middle region and are never examined again,
making LogosSort efficient on data with many duplicates.

**Counting-sort fast path**
When sorting integers whose value range is less than 4× the subarray length
(dense integer distributions common at deeper recursion levels), LogosSort
switches to counting sort — O(n) with zero comparisons.

**Tail-call optimisation**
After partitioning, the *two smaller* regions are recursed into and the
*largest* region becomes the next loop iteration, bounding stack depth to
O(log n) regardless of partition balance.

---

## Implementations

| Language | Source | Benchmark | Run |
|---|---|---|---|
| Python | [src/python/logos_sort.py](src/python/logos_sort.py) | [benchmark.py](src/python/benchmark.py) | `python benchmark.py` |
| JavaScript | [src/javascript/logos_sort.js](src/javascript/logos_sort.js) | [benchmark.js](src/javascript/benchmark.js) | `node benchmark.js` |
| TypeScript | [src/typescript/logos_sort.ts](src/typescript/logos_sort.ts) | [benchmark.ts](src/typescript/benchmark.ts) | `ts-node benchmark.ts` |
| Java | [src/java/LogosSort.java](src/java/LogosSort.java) | [Benchmark.java](src/java/Benchmark.java) | See below |
| C++ | [src/cpp/logos_sort.hpp](src/cpp/logos_sort.hpp) | [benchmark.cpp](src/cpp/benchmark.cpp) | `g++ -O2 -std=c++17 -o bench benchmark.cpp && ./bench` |
| C# | [src/csharp/LogosSort.cs](src/csharp/LogosSort.cs) | [Benchmark.cs](src/csharp/Benchmark.cs) | `dotnet run` |
| Go | [src/go/logos_sort.go](src/go/logos_sort.go) | [benchmark_test.go](src/go/benchmark_test.go) | `go test -bench=. -benchtime=3x` |
| Rust | [src/rust/src/lib.rs](src/rust/src/lib.rs) | [main.rs](src/rust/src/main.rs) | `cargo run --release` |
| Swift | [src/swift/LogosSort.swift](src/swift/LogosSort.swift) | [Benchmark.swift](src/swift/Benchmark.swift) | `swiftc -O LogosSort.swift Benchmark.swift -o bench && ./bench` |
| Kotlin | [src/kotlin/LogosSort.kt](src/kotlin/LogosSort.kt) | [Benchmark.kt](src/kotlin/Benchmark.kt) | `kotlinc *.kt -include-runtime -d bench.jar && java -jar bench.jar` |

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

**Full benchmark results, methodology, and adversarial-input notes → [BENCHMARKS.md](BENCHMARKS.md)**

---

## Quick start

### Python
```python
from logos_sort import logos_sort

data = [5, 3, 8, 1, 9, 2, 7, 4, 6]
print(logos_sort(data))   # [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

### JavaScript
```javascript
const { logosSort } = require('./logos_sort');
const arr = [5, 3, 8, 1, 9, 2, 7, 4, 6];
logosSort(arr);
console.log(arr);  // sorted in place
```

### C++
```cpp
#include "logos_sort.hpp"
#include <vector>

std::vector<int> v = {5, 3, 8, 1, 9, 2, 7, 4, 6};
logos::sort(v.begin(), v.end());
// v is now sorted
```

### Java
```java
int[] arr = {5, 3, 8, 1, 9, 2, 7, 4, 6};
LogosSort.sortInPlace(arr);
// arr is now sorted
```

### Rust
```rust
use logos_sort::logos_sort;
let mut arr = vec![5i64, 3, 8, 1, 9, 2, 7, 4, 6];
logos_sort(&mut arr);
// arr is now sorted
```

---

## Algorithm walkthrough

```
logos_sort([64, 34, 25, 12, 22, 11, 90, 42, 5, 77])

1. depth_limit = 2·⌊log₂(10)⌋ + 4 = 10

2. size=10 > 48? No → skip counting sort (span check fails for this range)

3. Oracle: c = 0.7341...  →  abs_c = 0.7341
   idx1 = 0 + ⌊9 · 0.382 · 0.734⌋ = 2   (pivot candidate near 28%)
   idx2 = 0 + ⌊9 · 0.618 · 0.734⌋ = 4   (pivot candidate near 45%)

4. Ninther at idx1=2: median(64, 25, 12) = 25  →  p1 = 25
   Ninther at idx2=4: median(12, 22, 11) = 12  →  p2 = 12

5. Dual partition with p1=12, p2=25 (swapped since 12<25):
   left  (<12): [11, 5]
   middle (12–25): [12, 22, 25]
   right  (>25): [64, 34, 90, 42, 77]

6. Recurse into left (n=2) and middle (n=3); loop on right (n=5)

7. Repeat until all regions ≤ 48 → delegate to insertion sort
```

---

## Philosophy

The algorithm's structure is inspired by the mathematical and philosophical traditions
behind its name:

- **Logos** (λόγος) — the rational principle underlying order; here expressed as
  the golden ratio, which describes optimal natural proportions from nautilus shells
  to phyllotaxis.
- **Oracle seed** — randomisation without determinism; unpredictable pivot positions
  mean no adversary can craft a worst-case input.
- **Ninther / dialectic** — thesis, antithesis, synthesis: three candidate values
  resolved to their median, cancelling extremes.
- **Depth limit / wu wei** — knowing when to stop and yield to a better-suited tool
  (the platform's built-in sort), rather than recurse forever.

See the annotated original: [logos_ultra_sort (1).py](logos_ultra_sort%20(1).py)

---

## License

[Unlicense](LICENSE) — public domain.
