# Welcome! This algorithm is a little philosophical sorting adventure.
# It consults chaos as an oracle, uses the golden ratio as a divining rod to
# find the best place to split a list, and hands each piece to the right guide.
# Think of it as a sorting hat that studied abroad in ancient Greece and never
# quite got over it — wise, a touch dramatic, but genuinely trying to help.

import random
import math


# Meet phi — the golden ratio, nature's favorite proportion!
# You'll find it in nautilus shells, sunflower seeds, and Renaissance paintings.
# Here we bake it into an integer so we can use it for fast arithmetic later.
# Phi and its "lesser twin" (1 - phi) together cover the whole number line
# the way yin and yang cover everything else.

PHI_SHIFT = 61
# Number of fractional bits used when encoding phi as a fixed-point integer.

PHI_NUM = round(0.6180339887498949 * (1 << PHI_SHIFT))
# The major golden ratio (≈0.618) scaled to a 61-bit fixed-point integer for
# integer-only arithmetic — represents the larger portion of the golden cut.

PHI2_NUM = round(0.3819660112501051 * (1 << PHI_SHIFT))
# The minor golden ratio (≈0.382, i.e. 1 − phi) scaled the same way —
# represents the smaller portion of the golden cut.


def logos_ultra_sort(arr):
    import math as _math

    n = len(arr)
    # Total number of elements to sort — the size of the world we're working with.

    # If you only have one thing (or nothing at all), congratulations —
    # it's already sorted! Plotinus would say the One is already perfect.
    # We just hand it back and everyone goes home happy.
    if n < 2:
        return arr[:]
        # A fresh copy of the original list, returned immediately with no changes.

    # How deep should we go before we stop and let Python take over?
    # Think of it like a road trip with a sensible turn-back rule —
    # we're adventurous, but we're not driving into the desert forever.
    # The Kabbalists called this tzimtzum: knowing when to pull back
    # so the work can actually finish.
    depth_limit = 2 * int(_math.log2(n)) + 4
    # Maximum recursion depth allowed: 2·⌊log₂(n)⌋ + 4, keeping stack growth O(log n).

    def _ninther(a, lo, hi, idx):
        # How do you pick a good representative from a crowd?
        # Ask three neighbors, take the middle one — it's Hegel's dialectic
        # as a party trick! Thesis, antithesis, synthesis. The extreme voices
        # cancel out, and the sensible middle survives. The Buddha called this
        # the middle way. Aristotle called it the golden mean. We call it: pretty handy.

        i0 = max(lo, idx - 1)
        # Left neighbor index, clamped so we never step outside the subarray boundary.

        i2 = min(hi, idx + 1)
        # Right neighbor index, clamped so we never step outside the subarray boundary.

        x, y, z = a[i0], a[idx], a[i2]
        # The three candidate values: left neighbor, center, and right neighbor.

        if x > y: x, y = y, x
        if y > z: y, z = z, y
        if x > y: x, y = y, x
        # Three compare-and-swap operations that sort x, y, z in-place without a sort call.

        return y
        # The median of the three candidates — a robust pivot estimate that resists outliers.

    def _dual_partition(a, lo, hi, p1, p2):
        # Time to divide the world! We have two pivot values (our two
        # philosophical boundary lines), and every element gets sorted
        # into one of three camps: smaller than p1, between p1 and p2,
        # or bigger than p2. Zoroaster would recognize this immediately —
        # two great opposing forces, and everything mortal sorted in between.
        # No judgment, no drama. Just: which side are you on?

        if p1 > p2:
            p1, p2 = p2, p1
        # Guarantee p1 ≤ p2 so the three-way partition logic is always consistent.

        lt = lo
        # Left boundary pointer: everything to the left of lt is strictly less than p1.

        gt = hi
        # Right boundary pointer: everything to the right of gt is strictly greater than p2.

        i = lo
        # Scan pointer: walks forward through the unexamined region lt..gt.

        while i <= gt:
            v = a[i]
            # Current element under examination.

            if v < p1:
                a[lt], a[i] = a[i], a[lt]
                lt += 1; i += 1
                # Element belongs in the left region — swap it to the lt position and advance both pointers.

            elif v > p2:
                a[i], a[gt] = a[gt], a[i]
                gt -= 1
                # Element belongs in the right region — swap it to the gt position and shrink from the right.
                # (i is NOT advanced; the swapped-in element still needs to be examined.)

            else:
                i += 1
                # Element is between p1 and p2 — it's already in the middle region, just move on.

        return lt, gt
        # lt = first index of the middle region; gt = last index of the middle region.

    def _sort(a, lo, hi, depth):
        while lo < hi:

            size = hi - lo + 1
            # Number of elements in the current subarray being sorted.

            # We've gone as deep as our depth budget allows —
            # time to let Python's built-in sorted() take the wheel.
            # This is wu wei in action: the Taoist art of knowing when
            # to stop paddling and let the river carry you. Timsort is
            # very good at this part. We trust it completely. No ego.
            if depth <= 0:
                a[lo:hi + 1] = sorted(a[lo:hi + 1])
                # Fallback to Timsort in-place on the slice when depth budget is exhausted.
                return

            # Small slices (48 elements or fewer) get handed straight
            # to Python's sorted() — no ceremony needed. The shepherd
            # who's found 49 sheep doesn't build a temple, he just
            # walks them home. Some jobs are small enough to just do.
            if size <= 48:
                a[lo:hi + 1] = sorted(a[lo:hi + 1])
                # Insertion-sort-class delegate: Timsort is optimal for small n, so we yield early.
                break

            # If we're sorting integers and they're packed into a tight range,
            # we can count rather than compare — like a census taker who
            # doesn't need to interview anyone, just tally the votes.
            # It's faster, and it treats every value with perfect democratic
            # equality. No element is weighed against another; each simply
            # takes its rightful place on the register.
            if isinstance(a[lo], int):
                mn = min(a[lo:hi + 1])
                # Minimum value in the subarray — used as the offset for the count array.

                mx = max(a[lo:hi + 1])
                # Maximum value in the subarray — used to compute the count array length.

                span = mx - mn
                # Value range of the subarray: how wide the counting array needs to be.

                if span < size * 4:
                    counts = [0] * (span + 1)
                    # Frequency array of length (span + 1), each index maps to a value offset by mn.

                    for i in range(lo, hi + 1):
                        counts[a[i] - mn] += 1
                        # Tally occurrences of each value by mapping it to its zero-based index.

                    k = lo
                    # Write-head pointer: next position in the original array to be filled.

                    for v, cnt in enumerate(counts):
                        if cnt:
                            a[k:k + cnt] = [v + mn] * cnt
                            # Write cnt copies of the reconstructed value back into the array.
                            k += cnt
                    break

            # Before we do anything expensive, let's peek at the first
            # three elements. If they're ascending, maybe the whole thing
            # already is! Before the Tower of Babel, things were in their
            # places — if the order's already written, only a fool rewrites
            # scripture. Descending? Just flip it! No need to sort what's
            # already organized, even if it's organized backwards.
            if a[lo] <= a[lo+1] <= a[lo+2]:
                # Quick three-element monotone check before committing to a full O(n) scan.

                if all(a[i] <= a[i+1] for i in range(lo, hi)):
                    break
                    # Subarray is already sorted ascending — nothing to do, exit the loop.

                if all(a[i] >= a[i+1] for i in range(lo, hi)):
                    a[lo:hi+1] = a[lo:hi+1][::-1]
                    # Subarray is sorted descending — reverse it in O(n) and exit.
                    break

            # Here's where we consult the oracle! We draw a random number —
            # not to be arbitrary, but to be *unpredictable*, so no sneaky
            # adversarial input can make us perform badly. Caesar crossed
            # the Rubicon on a throw of the dice. We're doing the same,
            # just with more math and lower stakes.
            c = 0.0
            while c == 0.0:
                c = random.uniform(-1.0, 1.0)
            # A non-zero random float in (−1, 1) — zero is retried to avoid a degenerate seed.

            chaos_int = int(abs(c) * (1 << 53))
            # c mapped to a 53-bit positive integer, giving ~2⁵³ distinct oracle values.

            # Now the oracle's number gets divided by the golden ratio —
            # nature's own scissors! Luca Pacioli called phi the "Divine
            # Proportion." We use it to find two pivot positions that are
            # naturally well-spaced: one at the minor cut (~38%), one at
            # the major cut (~62%). The universe divides itself this way
            # in seashells and galaxies. Why not in sorting?
            pn1 = PHI2_NUM * chaos_int
            # chaos_int scaled by the minor phi constant — encodes the ~38% position.

            pn2 = PHI_NUM * chaos_int
            # chaos_int scaled by the major phi constant — encodes the ~62% position.

            ps = PHI_SHIFT + 53
            # Combined bit-shift (61 + 53 = 114) used to normalise the fixed-point products back to array indices.

            span = hi - lo
            # Width of the current subarray in index units — used to map proportions to positions.

            idx1 = lo + (span * pn1 >> ps)
            # Array index of the first pivot candidate, placed at the ~38% golden position.

            idx2 = lo + (span * pn2 >> ps)
            # Array index of the second pivot candidate, placed at the ~62% golden position.

            # Deuteronomy said no verdict stands on one witness alone —
            # you need two or three. So each candidate pivot gets a quick
            # vote from its neighbors (that's the _ninther from earlier!),
            # and the winner by median is sworn in. Democracy, but fast.
            p1 = _ninther(a, lo, hi, idx1)
            # First pivot value: median of the three elements around idx1.

            p2 = _ninther(a, lo, hi, idx2)
            # Second pivot value: median of the three elements around idx2.

            # The great sorting! Everything gets divided into three regions:
            # smaller than p1, between p1 and p2, and bigger than p2.
            # Matthew 25 calls this separating the sheep from the goats.
            # We prefer to call it: everyone finding their neighborhood.
            lt, gt = _dual_partition(a, lo, hi, p1, p2)
            # lt = start of the equal-middle region; gt = end of the equal-middle region.

            left_n = lt - lo
            # Number of elements in the left (less-than) region.

            mid_n = gt - lt + 1
            # Number of elements in the middle (between-pivots) region.

            right_n = hi - gt
            # Number of elements in the right (greater-than) region.

            # Here's a clever bit: we sort the two smaller regions via
            # recursion, but loop back around for the biggest one instead
            # of calling ourselves again. This keeps the call stack from
            # growing out of control — the Sermon on the Mount says the
            # meek shall inherit the earth, and here the two smaller regions
            # get served first while the largest quietly becomes our next
            # loop iteration. Stack-friendly and spiritually consistent!
            regions = sorted(
                [(left_n, lo, lt-1), (mid_n, lt, gt), (right_n, gt+1, hi)],
                key=lambda r: r[0]
            )
            # List of (size, lo, hi) triples sorted ascending by size — smallest work first.

            for _, r_lo, r_hi in regions[:2]:
                if r_lo < r_hi:
                    _sort(a, r_lo, r_hi, depth - 1)
            # Recurse into the two smaller regions, each with depth decremented by one.

            lo, hi = regions[2][1], regions[2][2]
            # Tail-call optimisation: replace lo/hi with the largest region and loop instead of recurse.

            depth -= 1
            # Consume one depth token for this iteration of the main loop.

    a = arr[:]
    # Working copy of the input — the original list is never modified.

    _sort(a, 0, n - 1, depth_limit)
    return a


data = [64, 34, 25, 12, 22, 11, 90, 42, 5, 77]
print("Before:", data[:])
print("After: ", logos_ultra_sort(data))
