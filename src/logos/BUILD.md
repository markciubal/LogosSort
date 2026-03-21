# Building the Logos → C Benchmark

## Quick start (any platform)

```
src/logos/
├── logos_sort.lg       ← Logos language source (the spec)
├── logos_sort.c        ← Pre-generated C (authoritative, build this)
├── logos_sort.h
├── timsort.c           ← Pure-C Timsort (no stdlib sort calls)
├── timsort.h
├── bench.c             ← Benchmark + Hadamard oracle report
├── logos_compile.py    ← Transpiler: logos_sort.lg → C
└── Makefile
```

---

## Option 1 — MinGW/GCC (recommended on Windows)

Install once via Chocolatey (run as Administrator):
```powershell
choco install mingw
```

Then in any terminal:
```bash
cd src/logos
gcc -O2 -std=c11 logos_sort.c timsort.c bench.c -lm -o bench.exe
./bench.exe
```

Or use the Makefile from Git Bash / MSYS2:
```bash
make && make run
```

---

## Option 2 — MSVC (Visual Studio Developer Command Prompt)

Open **x64 Native Tools Command Prompt for VS 2022** from the Start menu, then:
```cmd
cd src\logos
cl /O2 /std:c11 logos_sort.c timsort.c bench.c /link /out:bench.exe
bench.exe
```

MSVC uses the `double`-precision pivot path (no `__uint128_t`) —
results are numerically equivalent to within 1 ULP.

---

## Option 3 — Clang (Linux / macOS / WSL)

```bash
cd src/logos
clang -O2 -std=c11 logos_sort.c timsort.c bench.c -lm -o bench
./bench
```

On Linux, add `--wrap` flags for exact malloc peak tracking:
```bash
clang -O2 -std=c11 \
  -Wl,--wrap=malloc,--wrap=free \
  logos_sort.c timsort.c bench.c -lm -o bench
./bench
```

---

## Option 4 — Transpile from Logos source first

Regenerate `logos_sort_gen.c` from the `.lg` source, then build:

```bash
python logos_compile.py logos_sort.lg > logos_sort_gen.c
gcc -O2 -std=c11 logos_sort_gen.c timsort.c bench.c -lm -o bench_gen
./bench_gen
```

The generated file is intentionally verbose (type annotations preserved as
comments) so you can see exactly how each Logos construct maps to C.

---

## What the Hadamard check reports

```
-- Hadamard entropy check (run before first sort call) ----------
  Oracle entropy seed : 0x1a2b3c4d5e6f7890
  WHT max coefficient : 14  (1.75x expected amplitude)
  Hadamard spectral   : PASS -- good entropy
  Oracle quality      : Hadamard (high)
```

A `FAIL` means the platform RNG had spectral bias — common when:
- System has just booted (entropy pool not yet full)
- Running inside a deterministic VM or container
- RNG was seeded with `time(0)` twice in the same second

On `FAIL`, LogosSort automatically mixes in a call counter + address entropy
and continues. Sort correctness is never affected; only the oracle seed source
changes.

---

## Expected benchmark output (representative)

```
  500000 items
  LogosSort (in-place)    0.038s       8 KB    0.02B  O(log n)
  Timsort (pure C)        0.051s    2.0 MB    4.00B  O(n)
  qsort *                 0.032s       n/a      n/a  O(n)  (qsort, ref only)
  Time: 0.75x   Memory: LogosSort uses 263x less

  2500000 items
  LogosSort (in-place)    0.205s      10 KB    0.00B  O(log n)
  Timsort (pure C)        0.280s    10.0 MB    4.00B  O(n)
  Time: 0.73x   Memory: LogosSort uses 1024x less

  10000000 items
  LogosSort (in-place)    0.880s      12 KB    0.00B  O(log n)
  Timsort (pure C)        1.230s    40.0 MB    4.00B  O(n)
  Time: 0.72x   Memory: LogosSort uses 3413x less
```

Memory column for LogosSort reflects only auxiliary allocations
(recursion stack frames + any counting-sort VLAs in dense subarrays).
The input array is pre-allocated outside the measurement window.
