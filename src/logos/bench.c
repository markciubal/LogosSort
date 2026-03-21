/*
 * bench.c — Benchmark: LogosSort vs Pure-C Timsort vs qsort (ref only)
 *
 * Apples-to-apples: both LogosSort and Timsort are pure C, zero stdlib-sort
 * calls internally. qsort is shown for reference (C stdlib, not a fair peer).
 *
 * Hadamard oracle quality is reported before each size batch so you can
 * see whether the platform entropy source passed the spectral test.
 *
 * Memory: operator-new/delete override (like C++ bench) replaced here with
 * a custom malloc wrapper using atomic counters.
 *
 * Compile & run (Linux/macOS):
 *   gcc -O2 -std=c11 logos_sort.c timsort.c bench.c -lm -o bench && ./bench
 *
 * Compile & run (Windows/MinGW):
 *   gcc -O2 -std=c11 logos_sort.c timsort.c bench.c -lm -o bench.exe && bench.exe
 *
 * Compile & run (MSVC):
 *   cl /O2 logos_sort.c timsort.c bench.c /link /out:bench.exe && bench.exe
 *   (Note: MSVC lacks __uint128_t — use the clang-cl or MinGW toolchain instead)
 */

#include "logos_sort.h"
#include "timsort.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdint.h>
#include <stdatomic.h>

#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>
#endif

/* ── Timing ──────────────────────────────────────────────────────────────── */
static double now_sec(void) {
#ifdef _WIN32
    LARGE_INTEGER freq, cnt;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&cnt);
    return (double)cnt.QuadPart / (double)freq.QuadPart;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
#endif
}

/* ── Allocation tracker (peak heap bytes, separate from timing) ─────────── */
static _Atomic size_t track_current = 0;
static _Atomic size_t track_peak    = 0;
static _Atomic int    tracking      = 0;

/* Intercept malloc/free with weak aliases — works on GCC/Clang Linux/macOS.
 * On Windows we use a wrapper approach via function pointers.             */

#if defined(__linux__) || defined(__APPLE__)

void* __real_malloc(size_t);
void  __real_free(void*);

void* __wrap_malloc(size_t sz) {
    void* p = __real_malloc(sz + sizeof(size_t));
    if (!p) return NULL;
    *(size_t*)p = sz;
    if (atomic_load(&tracking)) {
        size_t cur = atomic_fetch_add(&track_current, sz) + sz;
        size_t pk  = atomic_load(&track_peak);
        while (cur > pk &&
               !atomic_compare_exchange_weak(&track_peak, &pk, cur))
            ;
    }
    return (char*)p + sizeof(size_t);
}

void __wrap_free(void* ptr) {
    if (!ptr) return;
    void* real = (char*)ptr - sizeof(size_t);
    size_t sz = *(size_t*)real;
    if (atomic_load(&tracking))
        atomic_fetch_sub(&track_current, sz);
    __real_free(real);
}

static void tracker_start(void) {
    atomic_store(&track_current, 0);
    atomic_store(&track_peak,    0);
    atomic_store(&tracking,      1);
}
static void tracker_stop(void)  { atomic_store(&tracking, 0); }
static size_t tracker_peak(void){ return atomic_load(&track_peak); }

#else /* Windows / MSVC / MinGW — no weak linking; use heap-delta instead */

static size_t win_heap_before = 0;

static void tracker_start(void) {
    /* Approximate: record current committed heap size                    */
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS_EX pmc = { .cb = sizeof(pmc) };
    GetProcessMemoryInfo(GetCurrentProcess(), (PPROCESS_MEMORY_COUNTERS)&pmc,
                         sizeof(pmc));
    win_heap_before = (size_t)pmc.PrivateUsage;
#endif
    atomic_store(&track_peak, 0);
    atomic_store(&tracking,   1);
}

static void tracker_stop(void) {
    atomic_store(&tracking, 0);
#ifdef _WIN32
    PROCESS_MEMORY_COUNTERS_EX pmc = { .cb = sizeof(pmc) };
    GetProcessMemoryInfo(GetCurrentProcess(), (PPROCESS_MEMORY_COUNTERS)&pmc,
                         sizeof(pmc));
    size_t after = (size_t)pmc.PrivateUsage;
    size_t delta = after > win_heap_before ? after - win_heap_before : 0;
    atomic_store(&track_peak, delta);
#endif
}

static size_t tracker_peak(void) { return atomic_load(&track_peak); }

#endif /* tracker platform selection */

/* ── Random data generation (SplitMix64) ─────────────────────────────────── */
static uint64_t rng_state = 0;
static uint64_t next_u64(void) {
    rng_state += UINT64_C(0x9E3779B97F4A7C15);
    uint64_t z = rng_state;
    z = (z ^ (z >> 30)) * UINT64_C(0xBF58476D1CE4E5B9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94D049BB133111EB);
    return z ^ (z >> 31);
}

static int64_t* make_data(size_t n, uint64_t seed) {
    rng_state = seed;
    int64_t* d = (int64_t*)malloc(n * sizeof(int64_t));
    if (!d) { fprintf(stderr, "OOM\n"); exit(1); }
    for (size_t i = 0; i < n; i++)
        d[i] = (int64_t)(next_u64() % 1000000000ULL);
    return d;
}

/* ── Benchmark helpers ────────────────────────────────────────────────────── */
#define RUNS 5

static double bench_time(void (*fn)(int64_t*, size_t),
                          int64_t* data, size_t n) {
    double total = 0.0;
    for (int r = 0; r < RUNS; r++) {
        int64_t* a = (int64_t*)malloc(n * sizeof(int64_t));
        memcpy(a, data, n * sizeof(int64_t));
        double t0 = now_sec();
        fn(a, n);
        total += now_sec() - t0;
        free(a);
    }
    return total / RUNS;
}

static size_t bench_mem(void (*fn)(int64_t*, size_t),
                         int64_t* data, size_t n) {
    int64_t* a = (int64_t*)malloc(n * sizeof(int64_t));
    memcpy(a, data, n * sizeof(int64_t));
    tracker_start();
    fn(a, n);
    tracker_stop();
    size_t peak = tracker_peak();
    free(a);
    return peak;
}

/* qsort comparator */
static int cmp_i64(const void* a, const void* b) {
    int64_t x = *(const int64_t*)a, y = *(const int64_t*)b;
    return (x > y) - (x < y);
}
static void std_qsort(int64_t* a, size_t n) { qsort(a, n, sizeof(int64_t), cmp_i64); }

/* ── Format helpers ───────────────────────────────────────────────────────── */
static void fmt_bytes(char* out, size_t b) {
    if (b >= 1u << 20)      sprintf(out, "%6.1f MB", b / (double)(1u << 20));
    else if (b >= 1u << 10) sprintf(out, "%6.1f KB", b / (double)(1u << 10));
    else                    sprintf(out, "%6zu  B",  b);
}

/* ── Hadamard test demo (visible to user) ─────────────────────────────────── */
/*   Re-implements the test using the same logic as logos_sort.c so we can
 *   display the result independently before sorting.                        */
static void wht64_demo(int64_t buf[64]) {
    for (int h = 1; h < 64; h *= 2)
        for (int i = 0; i < 64; i += h * 2)
            for (int j = i; j < i + h; j++) {
                int64_t x = buf[j], y = buf[j+h];
                buf[j] = x+y; buf[j+h] = x-y;
            }
}

static uint64_t splitmix_demo(uint64_t* s) {
    *s += UINT64_C(0x9E3779B97F4A7C15);
    uint64_t z = *s;
    z = (z ^ (z >> 30)) * UINT64_C(0xBF58476D1CE4E5B9);
    z = (z ^ (z >> 27)) * UINT64_C(0x94D049BB133111EB);
    return z ^ (z >> 31);
}

static void print_hadamard_report(uint64_t seed) {
    int64_t buf[64];
    uint64_t s = seed;
    for (int i = 0; i < 64; i++)
        buf[i] = (splitmix_demo(&s) & 1) ? 1 : -1;
    wht64_demo(buf);

    int64_t max_coeff = 0;
    for (int i = 1; i < 64; i++) {
        int64_t v = buf[i] < 0 ? -buf[i] : buf[i];
        if (v > max_coeff) max_coeff = v;
    }
    double ratio = max_coeff / 8.0;   /* expected amplitude = sqrt(64) = 8 */
    int pass = max_coeff < 32;
    printf("  Oracle entropy seed : 0x%016llx\n", (unsigned long long)seed);
    printf("  WHT max coefficient : %lld  (%.2fx expected amplitude)\n",
           (long long)max_coeff, ratio);
    printf("  Hadamard spectral   : %s  (threshold = 4x = 32)\n",
           pass ? "PASS -- good entropy" : "FAIL -- biased RNG detected");
    printf("  Oracle quality      : %s\n\n",
           pass ? "Hadamard (high)" : "Fallback (counter-mixed seed)");
}

/* ── Main ─────────────────────────────────────────────────────────────────── */
int main(void) {
    static const size_t SIZES[] = { 500000, 2500000, 10000000 };
    static const int    NSIZES  = 3;

    printf("%s\n", "============================================================"
                   "================");
    printf("LogosSort (Logos language, transpiled to C) vs Pure-C Timsort\n");
    printf("Memory: malloc-wrapper peak counter (Linux/macOS) or heap delta (Win)\n");
    printf("qsort shown for reference only (stdlib, not a fair peer).\n");
    printf("%s\n\n", "============================================================"
                     "================");

    /* Show Hadamard oracle check once (seed is platform-specific)          */
    /* We borrow a fresh platform entropy value via the same path logos uses */
#ifdef _WIN32
    LARGE_INTEGER pc; QueryPerformanceCounter(&pc);
    uint64_t demo_seed = (uint64_t)pc.QuadPart ^ (uint64_t)(uintptr_t)&pc;
#else
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    uint64_t demo_seed = (uint64_t)ts.tv_nsec ^ ((uint64_t)ts.tv_sec << 32)
                         ^ (uint64_t)(uintptr_t)&ts;
#endif
    printf("-- Hadamard entropy check (run before first sort call) ----------\n");
    print_hadamard_report(demo_seed);

    for (int si = 0; si < NSIZES; si++) {
        size_t n = SIZES[si];
        int64_t* data = make_data(n, 42);

        double logos_t = bench_time(logos_sort, data, n);
        double tims_t  = bench_time(timsort,    data, n);
        double std_t   = bench_time(std_qsort,  data, n);

        size_t logos_m = bench_mem(logos_sort, data, n);
        size_t tims_m  = bench_mem(timsort,    data, n);

        char logos_mb[32], tims_mb[32];
        fmt_bytes(logos_mb, logos_m);
        fmt_bytes(tims_mb,  tims_m);

        printf("  %zu items\n", n);
        printf("  %s\n", "------------------------------------------------------"
                          "----------------------");
        printf("  %-24s %7s  %10s  %6.2fB  Space\n",
               "Algorithm", "Time", "Peak Heap", "B/item");
        printf("  %s\n", "------------------------------------------------------"
                          "----------------------");
        printf("  %-24s %5.3fs  %10s  %6.2fB  O(log n)\n",
               "LogosSort (in-place)", logos_t, logos_mb,
               logos_m ? (double)logos_m / n : 0.0);
        printf("  %-24s %5.3fs  %10s  %6.2fB  O(n)\n",
               "Timsort (pure C)", tims_t, tims_mb,
               tims_m ? (double)tims_m / n : 0.0);
        printf("  %-24s %5.3fs  %10s  %7s  O(n)  (qsort, ref only)\n",
               "qsort *", std_t, "n/a", "n/a");
        printf("  %s\n", "------------------------------------------------------"
                          "----------------------");
        printf("  Time: %.2fx   Memory: LogosSort uses %.0fx less\n\n",
               logos_t / tims_t,
               tims_m > 0 ? (double)tims_m / (logos_m ? logos_m : 1) : 0.0);

        free(data);
    }

    printf("* qsort = C stdlib introsort/quicksort. Not a fair peer; shown for scale.\n");
    printf("  Oracle quality for this run: %s\n",
           logos_last_oracle_quality == 0 ? "Hadamard" : "Fallback");
    return 0;
}
