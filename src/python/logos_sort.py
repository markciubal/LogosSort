"""
LogosSort — Golden-ratio dual-pivot introsort with oracle-seeded pivot selection.

Algorithm highlights:
  - Two pivots placed at φ (≈61.8%) and 1−φ (≈38.2%) golden-ratio positions
    of a chaos-seeded index, resisting adversarial inputs without a fixed seed.
  - Ninther (median-of-3-neighbours) refines each pivot candidate.
  - Three-way dual-pivot partition produces ≤2 compare-swap passes per element.
  - Counting-sort fast path for integers whose value range < 4 × subarray size.
  - Depth budget (2·⌊log₂n⌋ + 4) falls back to Timsort, guaranteeing O(n log n).
  - Tail-call optimisation: two smaller regions recurse; the largest loops.
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

            if depth <= 0:
                a[lo:hi + 1] = sorted(a[lo:hi + 1])
                return

            if size <= 48:
                a[lo:hi + 1] = sorted(a[lo:hi + 1])
                break

            # Counting sort for dense integer subarrays
            if isinstance(a[lo], int):
                mn = min(a[lo:hi + 1])
                mx = max(a[lo:hi + 1])
                span = mx - mn
                if span < size * 4:
                    counts = [0] * (span + 1)
                    for i in range(lo, hi + 1):
                        counts[a[i] - mn] += 1
                    k = lo
                    for v, cnt in enumerate(counts):
                        if cnt:
                            a[k:k + cnt] = [v + mn] * cnt
                            k += cnt
                    break

            # Already-sorted monotone checks
            if a[lo] <= a[lo + 1] <= a[lo + 2]:
                if all(a[i] <= a[i + 1] for i in range(lo, hi)):
                    break
                if all(a[i] >= a[i + 1] for i in range(lo, hi)):
                    a[lo:hi + 1] = a[lo:hi + 1][::-1]
                    break

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

            regions = sorted(
                [(left_n, lo, lt - 1), (mid_n, lt, gt), (right_n, gt + 1, hi)],
                key=lambda r: r[0]
            )

            for _, r_lo, r_hi in regions[:2]:
                if r_lo < r_hi:
                    _sort(a, r_lo, r_hi, depth - 1)

            lo, hi = regions[2][1], regions[2][2]
            depth -= 1

    a = arr[:]
    _sort(a, 0, n - 1, depth_limit)
    return a
