/*
 * timsort.c — Pure C Timsort (no stdlib sort calls internally)
 *
 * Faithful to CPython's listsort.txt spec:
 *   - minrun = 32 (simplified: always 32 for clarity, ±4 matters little)
 *   - Natural ascending run detection; descending runs reversed in place
 *   - Binary insertion sort to extend short runs to minrun
 *   - Bottom-up merge with a single O(n) auxiliary buffer
 *   - Run stack with merge invariants: len[i] > len[i+1] + len[i+2]
 *                                      len[i] > len[i+1]
 *   - Galloping disabled (simplified — galloping is a constant-factor opt)
 *
 * No calls to qsort(), stdlib sort, or any platform sort function.
 * Comparison: pure C, same level as logos_sort.c.
 */

#include "timsort.h"
#include <stdlib.h>
#include <string.h>

#define MINRUN 32
#define MAX_RUNS 128   /* ceil(log2(SIZE_MAX)) + 1 */

/* ── Run stack ────────────────────────────────────────────────────────────── */
typedef struct { size_t lo; size_t len; } Run;

/* ── Binary insertion sort (used to extend natural runs to MINRUN) ─────── */
static void binary_insertion(int64_t* a, size_t lo, size_t hi, size_t start) {
    for (size_t i = start; i <= hi; i++) {
        int64_t key = a[i];
        /* Binary search in a[lo..i) for insertion point */
        size_t left = lo, right = i;
        while (left < right) {
            size_t mid = left + (right - left) / 2;
            if (a[mid] <= key) left = mid + 1;
            else               right = mid;
        }
        /* Shift a[left..i) right by one */
        memmove(a + left + 1, a + left, (i - left) * sizeof(int64_t));
        a[left] = key;
    }
}

/* ── Merge a[lo..mid) with a[mid..hi] using auxiliary buffer ─────────────── */
static void merge(int64_t* a, size_t lo, size_t mid, size_t hi,
                  int64_t* buf)
{
    size_t left_len = mid - lo;
    memcpy(buf, a + lo, left_len * sizeof(int64_t));

    size_t i = 0;          /* index into buf (left copy)  */
    size_t j = mid;        /* index into a   (right half) */
    size_t k = lo;         /* write position in a          */

    while (i < left_len && j <= hi) {
        if (buf[i] <= a[j]) a[k++] = buf[i++];
        else                 a[k++] = a[j++];
    }
    while (i < left_len) a[k++] = buf[i++];
    /* Remaining right elements are already in place */
}

/* ── Enforce Timsort merge invariants on the run stack ─────────────────── */
static void collapse_runs(int64_t* a, Run* runs, int* nruns, int64_t* buf) {
    while (*nruns >= 2) {
        int n = *nruns;
        int i = n - 1;
        /* Check invariant: X > Y + Z and Y > Z                           */
        int merge_needed = 0;
        if (n >= 3 && runs[i-2].len <= runs[i-1].len + runs[i].len)
            merge_needed = 1;
        else if (runs[i-1].len <= runs[i].len)
            merge_needed = 1;
        if (!merge_needed) break;

        /* Merge the two smaller adjacent runs */
        if (n >= 3 && runs[i-2].len < runs[i].len) {
            /* Merge i-2 and i-1 */
            size_t lo  = runs[i-2].lo;
            size_t mid = runs[i-1].lo;
            size_t hi  = runs[i-1].lo + runs[i-1].len - 1;
            merge(a, lo, mid, hi, buf);
            runs[i-2].len += runs[i-1].len;
            runs[i-1] = runs[i];
        } else {
            /* Merge i-1 and i */
            size_t lo  = runs[i-1].lo;
            size_t mid = runs[i].lo;
            size_t hi  = runs[i].lo + runs[i].len - 1;
            merge(a, lo, mid, hi, buf);
            runs[i-1].len += runs[i].len;
        }
        (*nruns)--;
    }
}

/* ── Flush all remaining runs (final merges) ──────────────────────────────── */
static void flush_runs(int64_t* a, Run* runs, int* nruns, int64_t* buf) {
    while (*nruns >= 2) {
        int i = *nruns - 1;
        size_t lo  = runs[i-1].lo;
        size_t mid = runs[i].lo;
        size_t hi  = runs[i].lo + runs[i].len - 1;
        merge(a, lo, mid, hi, buf);
        runs[i-1].len += runs[i].len;
        (*nruns)--;
    }
}

/* ── Public API ──────────────────────────────────────────────────────────── */
void timsort(int64_t* arr, size_t n) {
    if (n < 2) return;

    /* Single O(n) auxiliary buffer — only allocation in this implementation */
    int64_t* buf = (int64_t*)malloc(n * sizeof(int64_t));
    if (!buf) {
        /* Degenerate fallback (should not happen in bench) — insertion sort */
        for (size_t i = 1; i < n; i++) {
            int64_t key = arr[i]; size_t j = i;
            while (j > 0 && arr[j-1] > key) { arr[j] = arr[j-1]; j--; }
            arr[j] = key;
        }
        return;
    }

    Run    runs[MAX_RUNS];
    int    nruns = 0;
    size_t pos   = 0;

    while (pos < n) {
        size_t run_start = pos;

        if (pos + 1 >= n) {
            /* Single element — trivially sorted */
            runs[nruns++] = (Run){ run_start, 1 };
            pos++;
            collapse_runs(arr, runs, &nruns, buf);
            continue;
        }

        /* Detect natural run */
        size_t run_end = pos + 1;
        if (arr[pos] > arr[pos + 1]) {
            /* Strictly descending — find full run then reverse */
            while (run_end < n - 1 && arr[run_end] > arr[run_end + 1])
                run_end++;
            /* Reverse in place */
            size_t l = pos, r = run_end;
            while (l < r) {
                int64_t t = arr[l]; arr[l] = arr[r]; arr[r] = t;
                l++; r--;
            }
        } else {
            /* Non-decreasing */
            while (run_end < n - 1 && arr[run_end] <= arr[run_end + 1])
                run_end++;
        }

        /* Extend short run to MINRUN using binary insertion sort */
        size_t run_min_end = pos + MINRUN - 1;
        if (run_min_end >= n) run_min_end = n - 1;
        if (run_end < run_min_end) {
            binary_insertion(arr, pos, run_min_end, run_end + 1);
            run_end = run_min_end;
        }

        size_t run_len = run_end - pos + 1;
        runs[nruns++] = (Run){ pos, run_len };
        pos = run_end + 1;

        collapse_runs(arr, runs, &nruns, buf);
    }

    flush_runs(arr, runs, &nruns, buf);
    free(buf);
}
