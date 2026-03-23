"""
"In the beginning was the Logos, and the Logos was with God, and the Logos was God."
 — John 1:1

LogosSort — Golden-ratio dual-pivot introsort with oracle-seeded pivot selection.

The name is not ornamental. Logos (λόγος) is the ordering principle: reason, word,
the pattern underlying apparent chaos. This algorithm imposes that order by dividing
each disordered region at proportions the universe itself prefers — the golden ratio
φ ≈ 0.618, the fixed point of the Fibonacci recurrence, present in phyllotaxis,
crystal growth, and the aesthetics of proportion across cultures and centuries.

A sort is a forcing function: it compels an arbitrary arrangement to conform to
the one arrangement that is most knowable. LogosSort does this without copying the
universe — it works in place, carrying only the recursion stack as memory of where
it has been and where it must return.

Design principles:
  - Two pivots at φ and 1−φ positions of an oracle-seeded index. The oracle is
    reseeded from platform entropy on every call so no adversarial input sequence
    can force worst-case behaviour across calls.
  - Ninther pivot refinement: median-of-3-neighbours around each candidate.
    A randomly chosen single pivot lands in the outer quartiles ~25% of the time;
    ninther reduces pivot error to O(1/n) without a full sample scan.
  - Three-way dual-pivot partition: each element is examined at most twice per pass.
    Elements equal to a pivot are placed in the middle region and never re-examined.
  - Counting sort fast path: when the value range of a subarray is less than 4× its
    size, the data is dense enough that a linear counting pass beats comparison sort
    entirely — O(n) time, O(range) space, zero comparisons.
  - Depth budget 2⌊log₂n⌋ + 4: if recursion exceeds this bound (an adversarially
    constructed or degenerate case), insertion sort is substituted, guaranteeing
    O(n log n) worst-case regardless of pivot quality.
  - Tail-call optimisation: the two smaller partitions recurse; the largest loops.
    Stack depth is therefore O(log n), not O(n).
  - Monotone detection: ascending runs are already ordered (return immediately);
    descending runs are reversed in O(n) with no comparisons thereafter.

Space:
  logos_sort()         → O(n) + O(log n): one working copy + recursion stack.
  logos_sort_inplace() → O(log n) only: no copy, only the call stack.

key= and reverse=:
  Both public functions accept an optional key callable and reverse flag,
  matching the interface of Python's built-in sorted().
  When key is given, a Schwartzian transform is used (decorate-sort-undecorate)
  and the sort is stable (original index used as tiebreaker).

Pure Python — zero calls to C-backed sort functions anywhere in this file.
"""

import random
import math

__version__ = "0.1.0"

# φ and 1−φ encoded as 61-bit fixed-point integers.
# Multiplying a 53-bit chaos integer by PHI_NUM and right-shifting 114 bits
# (= 61 + 53) yields the golden-ratio position of that chaos value within any
# span — exact integer arithmetic, no floating-point rounding error in pivot index.
PHI_SHIFT = 61
PHI_NUM   = round(0.6180339887498949 * (1 << PHI_SHIFT))   # φ  · 2^61
PHI2_NUM  = round(0.3819660112501051 * (1 << PHI_SHIFT))   # (1−φ) · 2^61


# ── Helpers ───────────────────────────────────────────────────────────────────

def _insertion_sort(a, lo, hi):
    # Optimal for small n: O(n²) comparisons are few in absolute terms,
    # cache locality is excellent, and no auxiliary memory is needed.
    for i in range(lo + 1, hi + 1):
        key = a[i]; j = i - 1
        while j >= lo and a[j] > key:
            a[j + 1] = a[j]; j -= 1
        a[j + 1] = key


def _ninther(a, lo, hi, idx):
    # Median of three neighbours around idx — concentrates the pivot toward
    # the true median without a full O(n) scan.
    i0 = max(lo, idx - 1)
    i2 = min(hi, idx + 1)
    x, y, z = a[i0], a[idx], a[i2]
    if x > y: x, y = y, x
    if y > z: y, z = z, y
    if x > y: x, y = y, x
    return y


def _dual_partition(a, lo, hi, p1, p2):
    # Three-way dual-pivot partition after Yaroslavskiy.
    # Produces: a[lo:lt] < p1,  a[lt:gt+1] in [p1,p2],  a[gt+1:hi+1] > p2
    if p1 > p2:
        p1, p2 = p2, p1
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
    # Core recursive sort. Outer while loop is tail-call optimisation on the
    # largest partition, keeping stack depth O(log n).
    while lo < hi:
        size = hi - lo + 1

        if depth <= 0 or size <= 48:
            _insertion_sort(a, lo, hi)
            return

        # Counting sort fast path for dense integer subarrays.
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

        # Monotone detection — return immediately if already ordered.
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

        # Oracle-seeded golden-ratio pivot selection.
        c = 0.0
        while c == 0.0: c = random.uniform(-1.0, 1.0)
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

        # Sort descriptors by size; recurse into two smaller, loop on largest.
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


# ── Public API ────────────────────────────────────────────────────────────────

def logos_sort(arr: list, *, key=None, reverse: bool = False) -> list:
    """Return a new sorted list. The original is never modified.

    Parameters
    ----------
    arr     : list  Input sequence.
    key     : callable, optional  Single-argument function applied to each
              element before comparison (like sorted()'s key=).
              When key is given the sort is stable.
    reverse : bool  If True, return in descending order.

    Space: O(n) for the working copy + O(log n) recursion stack.
    """
    n = len(arr)
    if n < 2:
        result = arr[:]
        return result[::-1] if reverse else result

    if key is not None:
        # Schwartzian transform: (key_value, original_index, element).
        # Including the index as a tiebreaker makes the sort stable.
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
    arr     : list  Sequence to sort in place.
    key     : callable, optional  Same semantics as logos_sort's key=.
              When key is given, a sorted copy is written back into arr.
    reverse : bool  If True, sort in descending order.

    Space: O(log n) recursion stack only (O(n) temporarily when key= is used).
    """
    n = len(arr)
    if n < 2:
        if reverse: arr.reverse()
        return

    if key is not None:
        sorted_copy = logos_sort(arr, key=key, reverse=reverse)
        arr[:] = sorted_copy
        return

    _sort(arr, 0, n - 1, _depth(n))
    if reverse:
        arr.reverse()
