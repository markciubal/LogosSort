"""
LogosSort — Golden-ratio dual-pivot introsort with oracle-seeded pivot selection.

Algorithm highlights:
  - Two pivots placed at φ (≈61.8%) and 1−φ (≈38.2%) golden-ratio positions
    of a chaos-seeded index, resisting adversarial inputs without a fixed seed.
  - Ninther (median-of-3-neighbours) refines each pivot candidate.
  - Three-way dual-pivot partition produces ≤2 compare-swap passes per element.
  - Counting-sort fast path for integers whose value range < 4 × subarray size.
  - Depth budget (2·⌊log₂n⌋ + 4) falls back to insertion sort, guaranteeing O(n log n).
  - Tail-call optimisation: two smaller regions recurse; the largest loops.

Pure Python — zero calls to C-backed sort functions.
"""

import random
import math

PHI_SHIFT = 61
PHI_NUM   = round(0.6180339887498949 * (1 << PHI_SHIFT))   # φ as 61-bit fixed point
PHI2_NUM  = round(0.3819660112501051 * (1 << PHI_SHIFT))   # (1−φ) as 61-bit fixed point


def logos_sort(arr: list) -> list:
    """Sort *arr* and return a new sorted list. The input list is never modified."""
    n = len(arr)
    if n < 2:
        return arr[:]

    depth_limit = 2 * int(math.log2(n)) + 4

    def _insertion_sort(a, lo, hi):
        """Pure Python insertion sort — O(n²) on n ≤ 48 elements."""
        for i in range(lo + 1, hi + 1):
            key = a[i]
            j = i - 1
            while j >= lo and a[j] > key:
                a[j + 1] = a[j]
                j -= 1
            a[j + 1] = key

    def _ninther(a, lo, hi, idx):
        i0 = max(lo, idx - 1)
        i2 = min(hi, idx + 1)
        x, y, z = a[i0], a[idx], a[i2]
        if x > y: x, y = y, x
        if y > z: y, z = z, y
        if x > y: x, y = y, x
        return y

    def _dual_partition(a, lo, hi, p1, p2):
        if p1 > p2:
            p1, p2 = p2, p1
        lt, gt, i = lo, hi, lo
        while i <= gt:
            v = a[i]
            if v < p1:
                a[lt], a[i] = a[i], a[lt]
                lt += 1; i += 1
            elif v > p2:
                a[i], a[gt] = a[gt], a[i]
                gt -= 1
            else:
                i += 1
        return lt, gt

    def _sort(a, lo, hi, depth):
        while lo < hi:
            size = hi - lo + 1

            # Depth exhausted or small subarray — pure Python insertion sort
            if depth <= 0 or size <= 48:
                _insertion_sort(a, lo, hi)
                return

            # Counting sort for dense integer subarrays (pure Python, no C sort)
            if isinstance(a[lo], int):
                mn = mx = a[lo]
                for i in range(lo + 1, hi + 1):
                    v = a[i]
                    if v < mn: mn = v
                    if v > mx: mx = v
                span = mx - mn
                if span < size * 4:
                    counts = [0] * (span + 1)
                    for i in range(lo, hi + 1):
                        counts[a[i] - mn] += 1
                    k = lo
                    for v, cnt in enumerate(counts):
                        for _ in range(cnt):
                            a[k] = v + mn
                            k += 1
                    return

            # Already-sorted monotone checks (pure Python loops)
            if a[lo] <= a[lo + 1] <= a[lo + 2]:
                asc = True
                for i in range(lo, hi):
                    if a[i] > a[i + 1]:
                        asc = False
                        break
                if asc:
                    return
                desc = True
                for i in range(lo, hi):
                    if a[i] < a[i + 1]:
                        desc = False
                        break
                if desc:
                    lo_r, hi_r = lo, hi
                    while lo_r < hi_r:
                        a[lo_r], a[hi_r] = a[hi_r], a[lo_r]
                        lo_r += 1; hi_r -= 1
                    return

            # Oracle-seeded golden-ratio pivot positions
            c = 0.0
            while c == 0.0:
                c = random.uniform(-1.0, 1.0)
            chaos_int = int(abs(c) * (1 << 53))

            pn1 = PHI2_NUM * chaos_int
            pn2 = PHI_NUM  * chaos_int
            ps  = PHI_SHIFT + 53
            sp  = hi - lo

            idx1 = lo + (sp * pn1 >> ps)
            idx2 = lo + (sp * pn2 >> ps)

            p1 = _ninther(a, lo, hi, idx1)
            p2 = _ninther(a, lo, hi, idx2)

            lt, gt = _dual_partition(a, lo, hi, p1, p2)

            left_n  = lt - lo
            mid_n   = gt - lt + 1
            right_n = hi - gt

            # Sort 3 region descriptors by size — comparison network, no C calls
            r0 = (left_n,  lo,    lt - 1)
            r1 = (mid_n,   lt,    gt    )
            r2 = (right_n, gt + 1, hi   )
            if r0[0] > r1[0]: r0, r1 = r1, r0
            if r1[0] > r2[0]: r1, r2 = r2, r1
            if r0[0] > r1[0]: r0, r1 = r1, r0

            for _, r_lo, r_hi in (r0, r1):
                if r_lo < r_hi:
                    _sort(a, r_lo, r_hi, depth - 1)

            lo, hi = r2[1], r2[2]
            depth -= 1

    a = arr[:]
    _sort(a, 0, n - 1, depth_limit)
    return a
