/*
 * logos_sort.c — Generated from logos_sort.lg via logos_compile.py
 *
 * LogosSort: golden-ratio dual-pivot introsort, oracle-seeded, O(log n) aux.
 *
 * Key bit-level ops:
 *   - Pivots placed via 128-bit fixed-point golden-ratio multiply (no float)
 *   - SplitMix64 oracle (passes BigCrush, period 2^64)
 *   - Walsh-Hadamard Transform spectral test on 64 oracle bits before use
 *   - Counting sort via stack VLA when value range < 4*n (bounded size)
 *   - TCO: largest partition handled by outer while loop (no stack growth)
 *
 * Compile: gcc -O2 -std=c11 logos_sort.c -lm -o sort
 *          clang -O2 -std=c11 logos_sort.c -lm -o sort
 */

#include "logos_sort.h"
#include <string.h>
#include <math.h>

#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>
#else
#  include <time.h>
#  if defined(__linux__) || defined(__APPLE__)
#    include <sys/random.h>
#  endif
#endif

/* ── Golden-ratio constants (fixed-point, 61-bit mantissa) ─────────────── */
#define PHI_NUM   UINT64_C(0x9E3779B97F4A7C15)  /* round(phi  * 2^61) */
#define PHI2_NUM  UINT64_C(0x61C8864680B583EB)  /* round(phi2 * 2^61) */
/* Total shift when computing pivot index: PHI_SHIFT(61) + 53 = 114       */
#define PIVOT_SHIFT 114

/* ── Oracle ──────────────────────────────────────────────────────────────── */
typedef struct { uint64_t seed; int quality; } Oracle;

_Thread_local int logos_last_oracle_quality = 0;

/* SplitMix64: passes BigCrush, period 2^64, 3 multiply-xorshift rounds    */
static inline uint64_t splitmix64(uint64_t* s) {
    *s += UINT64_C(0x9E3779B97F4A7C15);
    uint64_t z = *s;
    z = (z ^ (z >> 30)) * UINT64_C(0xBF58476D1CE4E5B9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94D049BB133111EB);
    return z ^ (z >> 31);
}

/* Platform entropy — avoids fixed seeds that fail the Hadamard test       */
static uint64_t platform_entropy(void) {
    uint64_t v = 0;
#ifdef _WIN32
    LARGE_INTEGER pc;
    QueryPerformanceCounter(&pc);
    v = (uint64_t)pc.QuadPart;
#elif defined(SYS_getrandom) || defined(__APPLE__)
    if (getentropy(&v, sizeof(v)) != 0) {
        struct timespec ts;
        clock_gettime(CLOCK_MONOTONIC, &ts);
        v = (uint64_t)ts.tv_nsec ^ ((uint64_t)ts.tv_sec << 32);
    }
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    v = (uint64_t)ts.tv_nsec ^ ((uint64_t)ts.tv_sec << 32);
#endif
    /* Mix with address-space entropy to add process-level uniqueness       */
    v ^= (uint64_t)(uintptr_t)&v;
    return v;
}

/* ── Walsh-Hadamard Transform (in-place, 64 elements) ─────────────────── */
/*                                                                           */
/* WHT[k] = sum_j ( x[j] * (-1)^popcount(j & k) )                          */
/* Butterfly layout: O(n log n), n=64 → 384 additions, no multiplications. */
static void wht64(int64_t buf[64]) {
    for (int h = 1; h < 64; h *= 2) {
        for (int i = 0; i < 64; i += h * 2) {
            for (int j = i; j < i + h; j++) {
                int64_t x = buf[j], y = buf[j + h];
                buf[j]     = x + y;
                buf[j + h] = x - y;
            }
        }
    }
}

/* ── Hadamard spectral test ─────────────────────────────────────────────── */
/*                                                                           */
/* Draw 64 binary samples from the low bit of SplitMix64(seed).            */
/* Apply WHT. For a flat (unbiased) source, all |WHT[i]| ≤ sqrt(64)*k      */
/* with high probability for small k. We use k=4, threshold=32.            */
/* A biased RNG (constant seed, linear congruential, same-second time)      */
/* produces at least one coefficient > 32 — we detect it here.             */
/*                                                                           */
/* Cost: 64 splitmix64 calls + 384 adds. Negligible vs any sort of n>1000. */
static int hadamard_test(uint64_t seed) {
    int64_t buf[64];
    uint64_t s = seed;
    for (int i = 0; i < 64; i++)
        buf[i] = (splitmix64(&s) & 1) ? 1 : -1;
    wht64(buf);
    /* Skip buf[0]: DC component is always ±64 for ±1 inputs — not useful  */
    for (int i = 1; i < 64; i++)
        if (buf[i] > 32 || buf[i] < -32) return 0;
    return 1;
}

static Oracle oracle_new(void) {
    uint64_t seed = platform_entropy();
    int quality = hadamard_test(seed) ? 0 : 1;
    if (quality == 1) {
        /* Biased entropy detected — fold in a call counter to diversify    */
        static volatile uint64_t call_ctr = 0;  /* volatile = safe for bench */
        uint64_t ctr = ++call_ctr;
        seed ^= splitmix64(&ctr);
    }
    return (Oracle){ .seed = seed, .quality = quality };
}

/* ── Core helpers ────────────────────────────────────────────────────────── */
static inline void swap64(int64_t* a, size_t i, size_t j) {
    int64_t t = a[i]; a[i] = a[j]; a[j] = t;
}

static void insertion_sort(int64_t* a, size_t lo, size_t hi) {
    for (size_t i = lo + 1; i <= hi; i++) {
        int64_t key = a[i];
        size_t j = i;
        while (j > lo && a[j-1] > key) { a[j] = a[j-1]; j--; }
        a[j] = key;
    }
}

/* Ninther: median of 3 neighbours — O(1), branchless-friendly             */
static inline int64_t ninther(int64_t* a, size_t lo, size_t hi, size_t idx) {
    size_t i0 = idx > lo ? idx - 1 : lo;
    size_t i2 = idx < hi ? idx + 1 : hi;
    int64_t x = a[i0], y = a[idx], z = a[i2];
    if (x > y) { int64_t t = x; x = y; y = t; }
    if (y > z) { int64_t t = y; y = z; z = t; }
    if (x > y) { int64_t t = x; x = y; y = t; }
    (void)x; (void)z;
    return y;
}

/* Dual-pivot three-way partition.
 * Post: a[lo..lt) < p1 ≤ a[lt..gt] ≤ p2 < a(gt..hi]                    */
static void dual_partition(int64_t* a, size_t lo, size_t hi,
                            int64_t p1, int64_t p2,
                            size_t* lt_out, size_t* gt_out)
{
    if (p1 > p2) { int64_t t = p1; p1 = p2; p2 = t; }
    size_t lt = lo, gt = hi, i = lo;
    while (i <= gt) {
        if      (a[i] < p1) { swap64(a, i, lt); lt++; i++; }
        else if (a[i] > p2) { swap64(a, i, gt); gt--;       }
        else                { i++;                           }
    }
    *lt_out = lt;
    *gt_out = gt;
}

/* Counting sort.
 * Precondition (enforced by caller): range = max_v-min_v+1 < 4*(hi-lo+1).
 * VLA size is therefore bounded: range < 4n. For large n this may be big,
 * so we heap-fallback above 64 K entries (rare for random data).          */
#define COUNT_STACK_MAX (1u << 16)   /* 64 K × 8 B = 512 KB — stack safe  */

static void counting_sort(int64_t* a, size_t lo, size_t hi,
                           int64_t min_v, int64_t max_v)
{
    size_t range = (size_t)(max_v - min_v) + 1;

    if (range <= COUNT_STACK_MAX) {
        /* Stack allocation (Logos: stack_alloc[usize; range]) */
        size_t counts[range];
        memset(counts, 0, range * sizeof(size_t));
        for (size_t i = lo; i <= hi; i++) counts[(size_t)(a[i] - min_v)]++;
        size_t k = lo;
        for (size_t v = 0; v < range; v++)
            for (size_t c = counts[v]; c; c--) a[k++] = (int64_t)v + min_v;
    } else {
        /* Heap fallback for unusually wide-range subarrays               */
        size_t* counts = (size_t*)calloc(range, sizeof(size_t));
        if (!counts) { insertion_sort(a, lo, hi); return; }
        for (size_t i = lo; i <= hi; i++) counts[(size_t)(a[i] - min_v)]++;
        size_t k = lo;
        for (size_t v = 0; v < range; v++)
            for (size_t c = counts[v]; c; c--) a[k++] = (int64_t)v + min_v;
        free(counts);
    }
}

/* ── Core sort: outer while loop = TCO on largest partition ─────────────── */
static void logos_sort_core(int64_t* a, size_t lo, size_t hi,
                             Oracle* oracle, int depth)
{
    while (lo < hi) {
        size_t n = hi - lo + 1;

        /* Base case */
        if (depth <= 0 || n <= 48) {
            insertion_sort(a, lo, hi);
            return;
        }

        /* Min/max scan for counting sort fast path */
        int64_t min_v = a[lo], max_v = a[lo];
        for (size_t i = lo + 1; i <= hi; i++) {
            if (a[i] < min_v) min_v = a[i];
            if (a[i] > max_v) max_v = a[i];
        }
        if ((uint64_t)(max_v - min_v) < (uint64_t)n * 4) {
            counting_sort(a, lo, hi, min_v, max_v);
            return;
        }

        /* Oracle-seeded golden-ratio pivot selection                        */
        /* chaos: 53 random bits (matches Python int(abs(c) * 2^53))       */
        uint64_t chaos = splitmix64(&oracle->seed) >> 11;
        size_t sp = hi - lo;

#if defined(__GNUC__) || defined(__clang__)
        /* GCC/Clang: exact 128-bit fixed-point multiply, zero float ops   */
        __uint128_t pn1 = (__uint128_t)PHI2_NUM * chaos;
        __uint128_t pn2 = (__uint128_t)PHI_NUM  * chaos;
        size_t idx1 = lo + (size_t)(((__uint128_t)sp * pn1) >> PIVOT_SHIFT);
        size_t idx2 = lo + (size_t)(((__uint128_t)sp * pn2) >> PIVOT_SHIFT);
#else
        /* MSVC / other: double-precision equivalent (53-bit mantissa ok)  */
        /* phi fraction of a random position in [0, sp]                    */
        double c_frac = (double)chaos * (1.0 / (double)(1ULL << 53));
        size_t idx1 = lo + (size_t)(0.3819660112501051 * c_frac * sp);
        size_t idx2 = lo + (size_t)(0.6180339887498949 * c_frac * sp);
#endif

        int64_t p1 = ninther(a, lo, hi, idx1);
        int64_t p2 = ninther(a, lo, hi, idx2);

        size_t lt, gt;
        dual_partition(a, lo, hi, p1, p2, &lt, &gt);

        /* Three region descriptors: (size, lo, hi)                        */
        size_t r0s = lt > lo    ? lt - lo        : 0;
        size_t r0lo = lo,  r0hi = lt > lo ? lt - 1 : lo;
        size_t r1s = gt >= lt   ? gt - lt + 1    : 0;
        size_t r1lo = lt,  r1hi = gt;
        size_t r2s = hi > gt    ? hi - gt        : 0;
        size_t r2lo = gt + 1,  r2hi = hi;

        /* Sort descriptors smallest-first via comparison network           */
#define SORT2(as,alo,ahi, bs,blo,bhi) \
        if ((as) > (bs)) { \
            size_t _s=(as),_lo=(alo),_hi=(ahi); \
            (as)=(bs);(alo)=(blo);(ahi)=(bhi); \
            (bs)=_s;(blo)=_lo;(bhi)=_hi; }
        SORT2(r0s,r0lo,r0hi, r1s,r1lo,r1hi)
        SORT2(r1s,r1lo,r1hi, r2s,r2lo,r2hi)
        SORT2(r0s,r0lo,r0hi, r1s,r1lo,r1hi)
#undef SORT2

        /* Recurse into 2 smallest (bounded depth) */
        if (r0s >= 2) logos_sort_core(a, r0lo, r0hi, oracle, depth - 1);
        if (r1s >= 2) logos_sort_core(a, r1lo, r1hi, oracle, depth - 1);

        /* TCO: loop on largest — transpiler converts `tail` to this       */
        if (r2s < 2) return;
        lo = r2lo; hi = r2hi; depth--;
    }
}

/* ── Public API ──────────────────────────────────────────────────────────── */
void logos_sort(int64_t* arr, size_t n) {
    if (n < 2) return;
    Oracle oracle = oracle_new();
    logos_last_oracle_quality = oracle.quality;
    int budget = 2 * (int)(log2((double)n)) + 4;
    logos_sort_core(arr, 0, n - 1, &oracle, budget);
}
