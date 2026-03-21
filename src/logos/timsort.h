#ifndef TIMSORT_H
#define TIMSORT_H

#include <stdint.h>
#include <stddef.h>

/* Pure-C Timsort — O(n log n), O(n) auxiliary space (one malloc buffer).
 * No internal calls to stdlib sort functions.                              */
void timsort(int64_t* arr, size_t n);

#endif /* TIMSORT_H */
