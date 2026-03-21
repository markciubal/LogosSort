#ifndef LOGOS_SORT_H
#define LOGOS_SORT_H

#include <stdint.h>
#include <stddef.h>

/* Sort arr[0..n) in place.  O(n log n) time, O(log n) auxiliary space.
 * Thread-safe: oracle seeded freshly per call via platform entropy.       */
void logos_sort(int64_t* arr, size_t n);

/* Oracle quality from the last logos_sort call (set per-thread).
 * 0 = Hadamard spectral test passed (good entropy).
 * 1 = Fallback (biased RNG detected; counter-mixed seed used instead).    */
extern _Thread_local int logos_last_oracle_quality;

#endif /* LOGOS_SORT_H */
