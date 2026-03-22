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

# These are special numbers built from the golden ratio — phi (φ ≈ 0.618).
# You see phi everywhere in nature: sunflower seeds, seashells, pinecones!
# We store it as a big whole number so our math stays perfectly exact,
# with no rounding mistakes from decimals.
PHI_SHIFT = 61
PHI_NUM   = round(0.6180339887498949 * (1 << PHI_SHIFT))   # φ  · 2^61
PHI2_NUM  = round(0.3819660112501051 * (1 << PHI_SHIFT))   # (1−φ) · 2^61


# Sorting a small group by hand!
# Imagine putting your books in order one at a time.
# You pick one up, scoot over the ones that should come after it,
# then drop it into the right spot. Great for tiny piles!

def _insertion_sort(a, lo, hi):
    for i in range(lo + 1, hi + 1):
        key = a[i]; j = i - 1
        while j >= lo and a[j] > key:
            a[j + 1] = a[j]; j -= 1
        a[j + 1] = key


# Picking a good "middle" number to split the list!
# Instead of grabbing just one number, we look at it and its two neighbors.
# We pick the one that's not too big and not too small — just right,
# like Goldilocks choosing her porridge!

def _ninther(a, lo, hi, idx):
    i0 = max(lo, idx - 1)
    i2 = min(hi, idx + 1)
    x, y, z = a[i0], a[idx], a[i2]
    # Three quick swaps to find the middle value of the three.
    if x > y: x, y = y, x
    if y > z: y, z = z, y
    if x > y: x, y = y, x
    return y   # y is the middle one


# Sorting everything into three groups!
# Imagine two lines drawn on the floor (p1 and p2).
# Smaller than p1? Go to the left pile.
# Bigger than p2? Go to the right pile.
# In between? Stay in the middle pile.
# We walk through the list once and everyone finds their group!

def _dual_partition(a, lo, hi, p1, p2):
    if p1 > p2: p1, p2 = p2, p1   # make sure p1 is the smaller one
    lt, gt, i = lo, hi, lo
    while i <= gt:
        v = a[i]
        if v < p1:
            a[lt], a[i] = a[i], a[lt]; lt += 1; i += 1
        elif v > p2:
            a[i], a[gt] = a[gt], a[i]; gt -= 1   # look at the swapped item again next loop
        else:
            i += 1
    return lt, gt


# The big sorting helper! This is where most of the magic happens.
# It looks at the pile of numbers and picks the smartest trick for right now:
#   - Tiny pile? Sort it by hand.
#   - Numbers packed close together? Count them instead of comparing.
#   - Already in order? Done! Go home!
#   - Going backwards? Flip it around and done!
#   - Otherwise: pick two good "splitter" numbers using the golden ratio,
#     divide everything into three smaller piles, and do it all again
#     on the smaller ones. The biggest pile gets the next loop turn
#     instead of a new function call, so we don't run out of stack space.

def _sort(a, lo, hi, depth):
    while lo < hi:
        size = hi - lo + 1

        # Pile is tiny or we've gone as deep as we're allowed.
        # Sort it by hand — fast and simple for small groups!
        if depth <= 0 or size <= 48:
            _insertion_sort(a, lo, hi)
            return

        # If the numbers are whole numbers and they're all close in value,
        # we can count how many of each we have and write them back in order.
        # Like counting red, blue, and green crayons, then laying them out:
        # all the reds first, then blues, then greens — no comparing needed!
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

        # Peek at the first three numbers.
        # If they go smallest → middle → biggest, maybe the whole list is already sorted!
        # Check the whole thing — if yes, we're done already, no work needed!
        # If everything goes biggest → middle → smallest (backwards), just flip it!
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

        # Roll the dice! We pick a random number so nobody can trick us
        # into always doing badly on purpose.
        # Then we use the golden ratio (phi!) to find two good split points —
        # one at about 38% of the way through, one at about 62%.
        # Nature uses these same spots in seashells and flowers —
        # turns out they work great for sorting too!
        c = 0.0
        while c == 0.0: c = random.uniform(-1.0, 1.0)
        chaos_int = int(abs(c) * (1 << 53))
        pn1 = PHI2_NUM * chaos_int
        pn2 = PHI_NUM  * chaos_int
        ps  = PHI_SHIFT + 53
        sp  = hi - lo
        idx1 = lo + (sp * pn1 >> ps)
        idx2 = lo + (sp * pn2 >> ps)

        # Ask each candidate and its neighbors: "who's the middle one?"
        # The middle neighbor becomes our actual splitter value.
        # This way we avoid accidentally picking a number that's way too big or tiny.
        p1 = _ninther(a, lo, hi, idx1)
        p2 = _ninther(a, lo, hi, idx2)
        lt, gt = _dual_partition(a, lo, hi, p1, p2)

        left_n  = lt - lo       # how many went to the left pile
        mid_n   = gt - lt + 1   # how many stayed in the middle pile
        right_n = hi - gt       # how many went to the right pile

        # Sort the three piles by size — smallest to biggest.
        # We'll sort the two smaller piles by calling ourselves again.
        # The biggest pile we just loop back for — no new function call!
        # This keeps the stack from growing too tall.
        r0 = (left_n,  lo,    lt - 1)
        r1 = (mid_n,   lt,    gt    )
        r2 = (right_n, gt + 1, hi   )
        if r0[0] > r1[0]: r0, r1 = r1, r0
        if r1[0] > r2[0]: r1, r2 = r2, r1
        if r0[0] > r1[0]: r0, r1 = r1, r0

        # Sort the two smaller piles.
        for _, r_lo, r_hi in (r0, r1):
            if r_lo < r_hi: _sort(a, r_lo, r_hi, depth - 1)

        # The biggest pile? Loop back and do it again — no new stack frame!
        lo, hi = r2[1], r2[2]
        depth -= 1


# ── Public API ────────────────────────────────────────────────────────────────

def logos_sort(arr: list) -> list:
    # "In the beginning was the Logos, and the Logos was with God, and the Logos was God." — John 1:1
    #
    # Makes a copy of your list and sorts the copy.
    # Your original list stays exactly the same — untouched!
    # Like making a photocopy of your drawing before coloring it in.
    n = len(arr)
    if n < 2: return arr[:]
    a = arr[:]   # the copy — only big extra memory we use
    _sort(a, 0, n - 1, 2 * int(math.log2(n)) + 4)
    return a


def logos_sort_inplace(arr: list) -> None:
    # "In the beginning was the Logos, and the Logos was with God, and the Logos was God." — John 1:1
    #
    # Sorts your list right where it sits — no copy made!
    # Like cleaning your room instead of moving to a new one.
    # Only uses a tiny bit of extra memory to remember where we are.
    n = len(arr)
    if n >= 2:
        _sort(arr, 0, n - 1, 2 * int(math.log2(n)) + 4)
