# LogosUltraSort — a sorting adventure powered by the golden ratio!
# It rolls a random number as an oracle, uses phi to find the best split points,
# and hands each pile to the right helper. Let's go!

import random
import math


# These are special numbers built from phi — the golden ratio (≈ 0.618).
# Phi shows up in seashells, sunflowers, and pinecones.
# We bake it into a big whole number so all our math stays perfectly exact.

PHI_SHIFT = 61
# How many fractional bits we use when storing phi as a whole number.

PHI_NUM = round(0.6180339887498949 * (1 << PHI_SHIFT))
# The big golden ratio (≈ 0.618) stored as a whole number — the larger golden cut.

PHI2_NUM = round(0.3819660112501051 * (1 << PHI_SHIFT))
# The small golden ratio (≈ 0.382) stored as a whole number — the smaller golden cut.


def logos_ultra_sort(arr):
    # "In the beginning was the Logos, and the Logos was with God, and the Logos was God." — John 1:1
    #
    # This is LogosUltraSort! It takes your list of numbers,
    # makes a copy, sorts the copy, and gives it back to you all tidy.
    # Your original list stays just the way you left it.

    import math as _math

    n = len(arr)
    # How many numbers are in the list.

    # If you only have one thing (or nothing at all), it's already sorted!
    # We just hand it back and go home.
    if n < 2:
        return arr[:]
        # A fresh copy of the list, returned with no changes needed.

    # How many times are we allowed to split before we stop and sort by hand?
    # This is our safety rule — we won't go forever, just far enough.
    depth_limit = 2 * int(_math.log2(n)) + 4
    # Maximum number of times we split: 2·⌊log₂(n)⌋ + 4.

    def _ninther(a, lo, hi, idx):
        # How do we pick a good "splitter" number from the list?
        # We look at one number and its two neighbors, then pick the middle one.
        # Not the biggest, not the smallest — the one right in the middle!
        # Like picking the medium-sized chair when Goldilocks visits.

        i0 = max(lo, idx - 1)
        # Left neighbor, clamped so we don't fall off the left edge.

        i2 = min(hi, idx + 1)
        # Right neighbor, clamped so we don't fall off the right edge.

        x, y, z = a[i0], a[idx], a[i2]
        # The three candidates: left neighbor, middle, right neighbor.

        if x > y: x, y = y, x
        if y > z: y, z = z, y
        if x > y: x, y = y, x
        # Three quick swaps to put x, y, z in order without calling sort.

        return y
        # y is the middle value — our chosen splitter.

    def _dual_partition(a, lo, hi, p1, p2):
        # Time to sort everyone into three groups!
        # We draw two lines: p1 (the low line) and p2 (the high line).
        # Smaller than p1? Go to the left group.
        # Bigger than p2? Go to the right group.
        # In between? Stay in the middle group.
        # We walk through the list once and everyone finds their place!

        if p1 > p2:
            p1, p2 = p2, p1
        # Make sure p1 is the smaller one so the grouping makes sense.

        lt = lo
        # Left pointer: everything to the left of here is smaller than p1.

        gt = hi
        # Right pointer: everything to the right of here is bigger than p2.

        i = lo
        # Walker: marches forward through the unsorted middle section.

        while i <= gt:
            v = a[i]
            # The number we're looking at right now.

            if v < p1:
                a[lt], a[i] = a[i], a[lt]
                lt += 1; i += 1
                # Smaller than p1 — swap it to the left group and move both pointers forward.

            elif v > p2:
                a[i], a[gt] = a[gt], a[i]
                gt -= 1
                # Bigger than p2 — swap it to the right group and shrink from the right.
                # Don't move i forward yet — the number that just swapped in needs a look!

            else:
                i += 1
                # It's in the middle group already — just keep walking.

        return lt, gt
        # lt = where the middle group starts; gt = where the middle group ends.

    def _insertion_sort(a, lo, hi):
        # Sort a small group by hand, like putting crayons back in the box one at a time.
        # Pick one up, slide over the ones that should come after it, drop it in the right spot.
        # No calls to sorted() or any outside helpers — just us, doing the work.
        for i in range(lo + 1, hi + 1):
            key = a[i]; j = i - 1
            while j >= lo and a[j] > key:
                a[j + 1] = a[j]; j -= 1
            a[j + 1] = key

    def _sort(a, lo, hi, depth):
        while lo < hi:

            size = hi - lo + 1
            # How many numbers are in the current chunk we're sorting.

            # If the chunk is tiny, or we've split as many times as we're allowed,
            # just sort it by hand. Quick and easy for small groups!
            if depth <= 0 or size <= 48:
                _insertion_sort(a, lo, hi)
                return

            # If the numbers are whole numbers and they're all close in value,
            # we can count how many of each there are instead of comparing them.
            # Like counting how many red, blue, and green crayons you have,
            # then laying them out: all reds first, then blues, then greens.
            # Much faster — no comparing at all!
            if isinstance(a[lo], int):
                mn = mx = a[lo]
                for i in range(lo + 1, hi + 1):
                    v = a[i]
                    if v < mn: mn = v
                    elif v > mx: mx = v
                # One pass to find the smallest and biggest values.

                span = mx - mn
                # How wide the spread of values is.

                if span < size * 4:
                    counts = [0] * (span + 1)
                    # A little tally sheet — one slot for each possible value.

                    for i in range(lo, hi + 1):
                        counts[a[i] - mn] += 1
                        # Mark a tally for each number we see.

                    k = lo
                    # Where we start writing numbers back into the list.

                    for v, cnt in enumerate(counts):
                        if cnt:
                            a[k:k + cnt] = [v + mn] * cnt
                            # Write all the copies of this value back in a row.
                            k += cnt
                    break

            # Peek at the first three numbers.
            # If they go up-up-up, maybe the whole thing is already sorted!
            # If it's already in order, there's nothing to do — we're done!
            # If everything goes down-down-down (backwards), just flip it around!
            if a[lo] <= a[lo+1] <= a[lo+2]:
                # Quick peek before we do a full check.

                if all(a[i] <= a[i+1] for i in range(lo, hi)):
                    break
                    # Already sorted from smallest to biggest — nothing to do!

                if all(a[i] >= a[i+1] for i in range(lo, hi)):
                    a[lo:hi+1] = a[lo:hi+1][::-1]
                    # Sorted backwards — flip it and we're done!
                    break

            # Roll the dice! We pick a random number so nobody can trick us
            # into always doing the worst case on purpose.
            # Then we use the golden ratio to find two good split points —
            # one at about 38% of the way, one at about 62%.
            # Sunflowers and galaxies use these same proportions.
            # Turns out they work great for sorting lists too!
            c = 0.0
            while c == 0.0:
                c = random.uniform(-1.0, 1.0)
            # A random number that isn't zero — zero would give us a bad split.

            chaos_int = int(abs(c) * (1 << 53))
            # Turn our random float into a big whole number for exact math.

            # Multiply by our golden ratio numbers to find the two split positions.
            pn1 = PHI2_NUM * chaos_int
            # Encodes the ~38% golden split position.

            pn2 = PHI_NUM * chaos_int
            # Encodes the ~62% golden split position.

            ps = PHI_SHIFT + 53
            # The total shift needed to turn the big products into actual list positions.

            span = hi - lo
            # Width of the current chunk in index steps.

            idx1 = lo + (span * pn1 >> ps)
            # List index of the first splitter candidate, near the 38% spot.

            idx2 = lo + (span * pn2 >> ps)
            # List index of the second splitter candidate, near the 62% spot.

            # Ask each candidate and its neighbors "who's the middle one?"
            # The middle neighbor wins and becomes our actual splitter.
            # This stops us from accidentally picking a number at the very edge.
            p1 = _ninther(a, lo, hi, idx1)
            # First splitter value: middle of the three around idx1.

            p2 = _ninther(a, lo, hi, idx2)
            # Second splitter value: middle of the three around idx2.

            # The big split! Everything goes into one of three groups:
            # smaller than p1, between p1 and p2, or bigger than p2.
            lt, gt = _dual_partition(a, lo, hi, p1, p2)
            # lt = start of the middle group; gt = end of the middle group.

            left_n = lt - lo
            # How many numbers went to the left (smaller) group.

            mid_n = gt - lt + 1
            # How many numbers are in the middle group.

            right_n = hi - gt
            # How many numbers went to the right (bigger) group.

            # Now we sort the three groups by how big they are.
            # We sort the two SMALLER groups by calling ourselves again.
            # The BIGGEST group we just loop back for — no new function call!
            # This keeps our stack from getting too tall, no matter how big the list is.
            r0 = (left_n,  lo,    lt - 1)
            r1 = (mid_n,   lt,    gt    )
            r2 = (right_n, gt + 1, hi   )
            # Three quick swaps to put r0, r1, r2 in order by size.
            if r0[0] > r1[0]: r0, r1 = r1, r0
            if r1[0] > r2[0]: r1, r2 = r2, r1
            if r0[0] > r1[0]: r0, r1 = r1, r0
            # Now r0 ≤ r1 ≤ r2 by size — the two smallest recurse, the biggest loops.

            for _, r_lo, r_hi in (r0, r1):
                if r_lo < r_hi:
                    _sort(a, r_lo, r_hi, depth - 1)
            # Sort the two smaller groups — each gets one fewer split allowed.

            lo, hi = r2[1], r2[2]
            # The biggest group becomes our next loop turn — no new stack frame needed!

            depth -= 1
            # Use up one split allowance for this round.

    a = arr[:]
    # Working copy of the input — your original list is never touched.

    _sort(a, 0, n - 1, depth_limit)
    return a


data = [64, 34, 25, 12, 22, 11, 90, 42, 5, 77]
print("Before:", data[:])
print("After: ", logos_ultra_sort(data))
