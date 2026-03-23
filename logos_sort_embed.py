"""
"In the beginning was the Logos, and the Logos was with God, and the Logos was God."
 — John 1:1

logos_sort_embed.py — self-contained single-file distribution of LogosSort.

Drop this file into any project and import directly:

    from logos_sort_embed import logos_sort, logos_sort_inplace

No dependencies beyond the Python standard library. Zero C sort calls.
Supports key= and reverse= with the same interface as Python's sorted().

    logos_sort(arr)                        # returns new sorted list
    logos_sort(arr, key=str.lower)         # key function, stable sort
    logos_sort(arr, reverse=True)          # descending order
    logos_sort_inplace(arr)                # sorts arr in place, returns None
    logos_sort_inplace(arr, key=abs)       # in-place with key
    logos_sort_inplace(arr, reverse=True)  # in-place descending
"""

import random
import math

# φ and 1−φ as 61-bit fixed-point integers — exact arithmetic, no float error.
_PHI_SHIFT = 61
_PHI_NUM   = round(0.6180339887498949 * (1 << _PHI_SHIFT))
_PHI2_NUM  = round(0.3819660112501051 * (1 << _PHI_SHIFT))


def _insertion_sort(a, lo, hi):
    for i in range(lo + 1, hi + 1):
        key = a[i]; j = i - 1
        while j >= lo and a[j] > key:
            a[j + 1] = a[j]; j -= 1
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
    if p1 > p2: p1, p2 = p2, p1
    lt, gt, i = lo, hi, lo
    while i <= gt:
        v = a[i]
        if v < p1:
            a[lt], a[i] = a[i], a[lt]; lt += 1; i += 1
        elif v > p2:
            a[i], a[gt] = a[gt], a[i]; gt -= 1
        else:
            i += 1
    return lt, gt


def _sort(a, lo, hi, depth):
    while lo < hi:
        size = hi - lo + 1

        if depth <= 0 or size <= 48:
            _insertion_sort(a, lo, hi)
            return

        if isinstance(a[lo], int):
            mn = mx = a[lo]
            for i in range(lo + 1, hi + 1):
                v = a[i]
                if v < mn: mn = v
                elif v > mx: mx = v
            span = mx - mn
            if span < size * 4:
                counts = [0] * (span + 1)
                for i in range(lo, hi + 1):
                    counts[a[i] - mn] += 1
                k = lo
                for v, cnt in enumerate(counts):
                    for _ in range(cnt):
                        a[k] = v + mn; k += 1
                return

        if a[lo] <= a[lo + 1] <= a[lo + 2]:
            asc = True
            for i in range(lo, hi):
                if a[i] > a[i + 1]: asc = False; break
            if asc: return
            desc = True
            for i in range(lo, hi):
                if a[i] < a[i + 1]: desc = False; break
            if desc:
                l, r = lo, hi
                while l < r: a[l], a[r] = a[r], a[l]; l += 1; r -= 1
                return

        c = 0.0
        while c == 0.0: c = random.uniform(-1.0, 1.0)
        chaos_int = int(abs(c) * (1 << 53))
        pn1 = _PHI2_NUM * chaos_int
        pn2 = _PHI_NUM  * chaos_int
        ps  = _PHI_SHIFT + 53
        sp  = hi - lo
        idx1 = lo + (sp * pn1 >> ps)
        idx2 = lo + (sp * pn2 >> ps)

        p1 = _ninther(a, lo, hi, idx1)
        p2 = _ninther(a, lo, hi, idx2)
        lt, gt = _dual_partition(a, lo, hi, p1, p2)

        left_n  = lt - lo
        mid_n   = gt - lt + 1
        right_n = hi - gt

        r0 = (left_n,  lo,    lt - 1)
        r1 = (mid_n,   lt,    gt    )
        r2 = (right_n, gt + 1, hi   )
        if r0[0] > r1[0]: r0, r1 = r1, r0
        if r1[0] > r2[0]: r1, r2 = r2, r1
        if r0[0] > r1[0]: r0, r1 = r1, r0

        for _, r_lo, r_hi in (r0, r1):
            if r_lo < r_hi: _sort(a, r_lo, r_hi, depth - 1)

        lo, hi = r2[1], r2[2]
        depth -= 1


def _depth(n):
    return 2 * int(math.log2(n)) + 4


def logos_sort(arr: list, *, key=None, reverse: bool = False) -> list:
    """Return a new sorted list. The original is never modified.

    Parameters
    ----------
    arr     : list
    key     : callable, optional — applied to each element before comparison.
              When given, the sort is stable (original index used as tiebreaker).
    reverse : bool — if True, return in descending order.
    """
    n = len(arr)
    if n < 2:
        result = arr[:]
        return result[::-1] if reverse else result

    if key is not None:
        work = [(key(arr[i]), i, arr[i]) for i in range(n)]
        _sort(work, 0, n - 1, _depth(n))
        result = [t[2] for t in work]
    else:
        work = arr[:]
        _sort(work, 0, n - 1, _depth(n))
        result = work

    return result[::-1] if reverse else result


def logos_sort_inplace(arr: list, *, key=None, reverse: bool = False) -> None:
    """Sort arr in place. No copy is made (unless key= is given).

    Parameters
    ----------
    arr     : list — modified in place.
    key     : callable, optional — same semantics as logos_sort's key=.
    reverse : bool — if True, sort in descending order.
    """
    n = len(arr)
    if n < 2:
        if reverse: arr.reverse()
        return

    if key is not None:
        arr[:] = logos_sort(arr, key=key, reverse=reverse)
        return

    _sort(arr, 0, n - 1, _depth(n))
    if reverse:
        arr.reverse()
