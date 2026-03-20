/**
 * LogosSort — Golden-ratio dual-pivot introsort (Kotlin)
 *
 * Two pivots placed at φ (≈61.8%) and 1−φ (≈38.2%) golden-ratio positions
 * of a chaos-seeded index. Ninther pivot refinement, three-way partition,
 * counting-sort fast path for dense Int ranges, O(log n) depth limit.
 */

import kotlin.math.log2
import kotlin.math.max
import kotlin.math.min
import kotlin.random.Random

private const val PHI    = 0.6180339887498949
private const val PHI2   = 0.3819660112501051
private const val SMALL_N = 48

// ─────────────────────────────────────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────────────────────────────────────

/** Sort [arr] in place using LogosSort. */
fun logosSort(arr: IntArray) {
    val n = arr.size
    if (n < 2) return
    val depth = 2 * log2(n.toDouble()).toInt() + 4
    sortImpl(arr, 0, n - 1, depth)
}

/** Return a sorted copy of [arr]. */
fun logosSorted(arr: IntArray): IntArray = arr.copyOf().also { logosSort(it) }

// ─────────────────────────────────────────────────────────────────────────────
// Internal implementation
// ─────────────────────────────────────────────────────────────────────────────

private fun sortImpl(a: IntArray, lo0: Int, hi0: Int, depth0: Int) {
    var lo = lo0; var hi = hi0; var depth = depth0
    while (lo < hi) {
        val size = hi - lo + 1

        if (depth <= 0 || size <= SMALL_N) {
            insertionSort(a, lo, hi)
            return
        }

        // Counting sort for dense integer subarrays
        var mn = a[lo]; var mx = a[lo]
        for (i in lo + 1..hi) {
            if (a[i] < mn) mn = a[i]
            if (a[i] > mx) mx = a[i]
        }
        val span = mx.toLong() - mn
        if (span in 0 until size.toLong() * 4) {
            val counts = IntArray(span.toInt() + 1)
            for (i in lo..hi) counts[a[i] - mn]++
            var k = lo
            for ((v, cnt) in counts.withIndex()) repeat(cnt) { a[k++] = v + mn }
            return
        }

        // Monotone checks
        if (a[lo] <= a[lo + 1] && a[lo + 1] <= a[lo + 2]) {
            val asc = (lo until hi).all { a[it] <= a[it + 1] }
            if (asc) return
            val desc = (lo until hi).all { a[it] >= a[it + 1] }
            if (desc) { reverse(a, lo, hi); return }
        }

        // Oracle-seeded golden-ratio pivot positions
        val absC = Random.nextDouble(1e-15, 1.0)
        val sp   = hi - lo
        val idx1 = lo + (sp * PHI2 * absC).toInt()
        val idx2 = lo + (sp * PHI  * absC).toInt()

        val p1 = ninther(a, lo, hi, idx1)
        val p2 = ninther(a, lo, hi, idx2)

        val (lt, gt) = dualPartition(a, lo, hi, p1, p2)

        data class Region(val n: Int, val lo: Int, val hi: Int)
        val regions = listOf(
            Region(lt - lo,      lo,    lt - 1),
            Region(gt - lt + 1,  lt,    gt    ),
            Region(hi - gt,      gt + 1, hi   ),
        ).sortedBy { it.n }

        for (i in 0..1) {
            val r = regions[i]
            if (r.lo < r.hi) sortImpl(a, r.lo, r.hi, depth - 1)
        }

        lo    = regions[2].lo
        hi    = regions[2].hi
        depth--
    }
}

private fun ninther(a: IntArray, lo: Int, hi: Int, idx: Int): Int {
    val i0 = max(lo, idx - 1)
    val i2 = min(hi, idx + 1)
    var x = a[i0]; var y = a[idx]; var z = a[i2]
    if (x > y) { val t = x; x = y; y = t }
    if (y > z) { val t = y; y = z; z = t }
    if (x > y) { val t = x; x = y; y = t }
    return y
}

private fun dualPartition(a: IntArray, lo: Int, hi: Int, p1_: Int, p2_: Int): Pair<Int, Int> {
    var p1 = p1_; var p2 = p2_
    if (p1 > p2) { val t = p1; p1 = p2; p2 = t }
    var lt = lo; var gt = hi; var i = lo
    while (i <= gt) {
        when {
            a[i] < p1 -> { val t = a[lt]; a[lt] = a[i]; a[i] = t; lt++; i++ }
            a[i] > p2 -> { val t = a[i];  a[i]  = a[gt]; a[gt] = t; gt-- }
            else       -> i++
        }
    }
    return Pair(lt, gt)
}

private fun insertionSort(a: IntArray, lo: Int, hi: Int) {
    for (i in lo + 1..hi) {
        val key = a[i]; var j = i
        while (j > lo && a[j - 1] > key) { a[j] = a[j - 1]; j-- }
        a[j] = key
    }
}

private fun reverse(a: IntArray, lo: Int, hi: Int) {
    var l = lo; var r = hi
    while (l < r) { val t = a[l]; a[l] = a[r]; a[r] = t; l++; r-- }
}
