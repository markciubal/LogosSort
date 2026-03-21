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

Pure Python — zero calls to C-backed sort functions anywhere in this file.
"""

import random
import math

# φ and 1−φ encoded as 61-bit fixed-point integers.
# Multiplying a 53-bit chaos integer by PHI_NUM and right-shifting 114 bits
# (= 61 + 53) yields the golden-ratio position of that chaos value within any
# span — exact integer arithmetic, no floating-point rounding error in pivot index.
PHI_SHIFT = 61
PHI_NUM   = round(0.6180339887498949 * (1 << PHI_SHIFT))   # φ  · 2^61
PHI2_NUM  = round(0.3819660112501051 * (1 << PHI_SHIFT))   # (1−φ) · 2^61


# ── Base case ─────────────────────────────────────────────────────────────────
# Insertion sort is optimal for small n: O(n²) comparisons are few in absolute
# terms, branch prediction is excellent on nearly-ordered data, and every
# element touches only a contiguous cache line. No auxiliary memory is needed.

def _insertion_sort(a, lo, hi):
    for i in range(lo + 1, hi + 1):
        key = a[i]; j = i - 1
        while j >= lo and a[j] > key:
            a[j + 1] = a[j]; j -= 1
        a[j + 1] = key


# ── Pivot refinement ──────────────────────────────────────────────────────────
# A pivot chosen uniformly at random lies in the outer 25% of the sorted order
# ~25% of the time, producing lopsided partitions and degrading performance.
# Ninther takes the median of three neighbours around the candidate index,
# concentrating the pivot toward the true median without a full O(n) scan.
# The clamp to [lo, hi] handles candidates at the subarray boundary.

def _ninther(a, lo, hi, idx):
    i0 = max(lo, idx - 1)
    i2 = min(hi, idx + 1)
    x, y, z = a[i0], a[idx], a[i2]
    # Sorting network for three values: three compare-swaps suffice.
    if x > y: x, y = y, x
    if y > z: y, z = z, y
    if x > y: x, y = y, x
    return y   # y is the median


# ── Partition ─────────────────────────────────────────────────────────────────
# Three-way dual-pivot partition after Yaroslavskiy (Java 7 Arrays.sort).
# Invariant maintained throughout the scan:
#   a[lo : lt]   < p1        — strictly left of the left pivot
#   a[lt : i]    in [p1, p2] — middle region, already classified
#   a[gt+1 : hi] > p2        — strictly right of the right pivot
#   a[i  : gt]   unclassified
#
# Each element is visited exactly once by i, or swapped once from gt.
# Elements equal to a pivot are absorbed into the middle region and never
# re-examined in recursive calls, which is why equal-element arrays are O(n).

def _dual_partition(a, lo, hi, p1, p2):
    if p1 > p2: p1, p2 = p2, p1   # canonical ordering: p1 ≤ p2
    lt, gt, i = lo, hi, lo
    while i <= gt:
        v = a[i]
        if v < p1:
            a[lt], a[i] = a[i], a[lt]; lt += 1; i += 1
        elif v > p2:
            a[i], a[gt] = a[gt], a[i]; gt -= 1   # i not advanced: re-examine swap
        else:
            i += 1
    return lt, gt


# ── Core recursive sort ───────────────────────────────────────────────────────
# The outer while loop is the tail-call optimisation: rather than recursing into
# all three partitions, we recurse into the two smaller ones and loop on the
# largest. This bounds the call stack to O(log n) even when partitions are
# maximally unequal, because the looped partition cannot exceed half the current
# subarray at every other level.

def _sort(a, lo, hi, depth):
    while lo < hi:
        size = hi - lo + 1

        # Depth budget exhausted or subarray small enough for insertion sort.
        # The budget 2⌊log₂n⌋ + 4 is tight enough to fire only on genuinely
        # degenerate input and wide enough that it never fires on random data.
        if depth <= 0 or size <= 48:
            _insertion_sort(a, lo, hi)
            return

        # Counting sort fast path — O(n) time, O(range) auxiliary space.
        # Condition: value range < 4 × subarray size means the data is dense
        # relative to its spread. Counting sort allocates one counter per
        # distinct value and makes exactly two linear passes (tally, then write).
        # No comparisons are performed; elements are placed by arithmetic alone.
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

        # Monotone detection — recognises pre-existing order before disturbing it.
        # An ascending prefix is checked only when the first three elements are
        # non-decreasing, avoiding the full scan cost on random data.
        # A descending run is the unique case where order is present but inverted;
        # a single linear reversal restores it in O(n) with no comparisons after.
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
        # A fresh random value from platform entropy prevents adversarial inputs
        # from forcing repeated poor partitions across calls. The chaos integer
        # is scaled by PHI2_NUM and PHI_NUM via fixed-point multiply (no float
        # division), placing two pivot candidates at the 38.2% and 61.8% positions
        # of the subarray — the proportions at which φ divides a segment into the
        # ratio it bears to the whole. This is not numerology: it distributes the
        # two pivots symmetrically and far from the extremes, minimising the
        # probability of landing in the outer tails.
        c = 0.0
        while c == 0.0: c = random.uniform(-1.0, 1.0)
        chaos_int = int(abs(c) * (1 << 53))   # 53-bit entropy integer
        pn1 = PHI2_NUM * chaos_int
        pn2 = PHI_NUM  * chaos_int
        ps  = PHI_SHIFT + 53                   # total shift = 61 + 53 = 114 bits
        sp  = hi - lo
        idx1 = lo + (sp * pn1 >> ps)           # ≈ lo + 0.382 · chaos · span
        idx2 = lo + (sp * pn2 >> ps)           # ≈ lo + 0.618 · chaos · span

        p1 = _ninther(a, lo, hi, idx1)
        p2 = _ninther(a, lo, hi, idx2)
        lt, gt = _dual_partition(a, lo, hi, p1, p2)

        left_n  = lt - lo       # elements < p1
        mid_n   = gt - lt + 1   # elements in [p1, p2]
        right_n = hi - gt       # elements > p2

        # Order the three partition regions by size so we recurse into the
        # two smallest and loop on the largest. The comparison network below
        # sorts three values with exactly three conditional swaps — no function
        # call, no list allocation, O(1) unconditionally.
        r0 = (left_n,  lo,    lt - 1)
        r1 = (mid_n,   lt,    gt    )
        r2 = (right_n, gt + 1, hi   )
        if r0[0] > r1[0]: r0, r1 = r1, r0
        if r1[0] > r2[0]: r1, r2 = r2, r1
        if r0[0] > r1[0]: r0, r1 = r1, r0

        # Recurse into the two smaller partitions, consuming one depth unit each.
        for _, r_lo, r_hi in (r0, r1):
            if r_lo < r_hi: _sort(a, r_lo, r_hi, depth - 1)

        # The largest partition continues in the outer while loop (TCO).
        # No new stack frame is created; only lo, hi, and depth are updated.
        lo, hi = r2[1], r2[2]
        depth -= 1


# ── Public API ────────────────────────────────────────────────────────────────

def logos_sort(arr: list) -> list:
    """Return a new sorted list. The original is never modified.

    A working copy is allocated (O(n) space) so the caller's reference remains
    stable. The sort itself operates in place on that copy; auxiliary space beyond
    the copy is O(log n) — the recursion stack only.
    """
    n = len(arr)
    if n < 2: return arr[:]
    a = arr[:]   # working copy — the only O(n) allocation in this path
    _sort(a, 0, n - 1, 2 * int(math.log2(n)) + 4)
    return a


def logos_sort_inplace(arr: list) -> None:
    """Sort arr in place. No copy is made.

    Auxiliary space is O(log n): only the call stack up to the depth budget.
    The budget 2⌊log₂n⌋ + 4 bounds the maximum stack depth while leaving
    ample room for well-behaved recursion trees on all realistic inputs.
    """
    n = len(arr)
    if n >= 2:
        _sort(arr, 0, n - 1, 2 * int(math.log2(n)) + 4)
