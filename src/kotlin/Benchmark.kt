/**
 * Benchmark: LogosSort vs Pure-Kotlin Merge Sort vs IntArray.sort
 * Time + Space complexity. Memory via Runtime.getRuntime() heap delta.
 *
 * kotlinc LogosSort.kt Benchmark.kt -include-runtime -d bench.jar
 * java -Xmx4g -jar bench.jar
 */

import kotlin.random.Random
import kotlin.system.measureNanoTime

private const val RUNS    = 3
private const val MAX_VAL = 1_000_000_000
private const val BLOCK   = 32

// ── Pure Kotlin bottom-up merge sort (one IntArray buffer = O(n) space) ──────

private fun insertionSortBlock(a: IntArray, lo: Int, hi: Int) {
    for (i in lo + 1..hi) {
        val key = a[i]; var j = i - 1
        while (j >= lo && a[j] > key) { a[j + 1] = a[j]; j-- }
        a[j + 1] = key
    }
}

private fun mergeSort(arr: IntArray) {
    val n = arr.size
    if (n < 2) return
    var lo = 0
    while (lo < n) { insertionSortBlock(arr, lo, minOf(lo + BLOCK - 1, n - 1)); lo += BLOCK }

    val buf = IntArray(n)   // <-- the single O(n) allocation
    var width = BLOCK
    while (width < n) {
        lo = 0
        while (lo < n) {
            val mid = minOf(lo + width,     n)
            val hi  = minOf(lo + 2 * width, n)
            if (mid >= hi) { arr.copyInto(buf, lo, lo, hi); lo += 2 * width; continue }
            var i = lo; var j = mid; var k = lo
            while (i < mid && j < hi)
                buf[k++] = if (arr[i] <= arr[j]) arr[i++] else arr[j++]
            while (i < mid) buf[k++] = arr[i++]
            while (j < hi)  buf[k++] = arr[j++]
            buf.copyInto(arr, lo, lo, hi)
            lo += 2 * width
        }
        width *= 2
    }
}

// ─────────────────────────────────────────────────────────────────────────────

private fun avgTime(n: Int, data: IntArray, fn: (IntArray) -> Unit): Double {
    var total = 0L
    repeat(RUNS) { total += measureNanoTime { fn(data.copyOf(n)) } }
    return total / RUNS / 1e9
}

private fun measureHeap(n: Int, data: IntArray, fn: (IntArray) -> Unit): Long {
    val arr = data.copyOf(n)
    System.gc(); System.gc()
    val rt = Runtime.getRuntime()
    val before = rt.totalMemory() - rt.freeMemory()
    fn(arr)
    val after = rt.totalMemory() - rt.freeMemory()
    return maxOf(after - before, 0L)
}

private fun fmtBytes(b: Long): String = when {
    b >= 1 shl 20 -> "%6.1f MB".format(b.toDouble() / (1 shl 20))
    b >= 1 shl 10 -> "%6.1f KB".format(b.toDouble() / (1 shl 10))
    else          -> "%6d  B".format(b)
}

fun main() {
    val sizes = intArrayOf(500_000, 2_500_000, 10_000_000)
    val rng   = Random(42)

    println("=".repeat(76))
    println("LogosSort vs Pure-Kotlin Merge Sort -- Time + Space Complexity")
    println("Memory via Runtime.getRuntime() heap delta.")
    println("IntArray.sort shown for reference only.")
    println("=".repeat(76))

    for (n in sizes) {
        val data = IntArray(n) { rng.nextInt(0, MAX_VAL) }

        val logosT = avgTime(n, data) { logosSort(it) }
        val mergeT = avgTime(n, data) { mergeSort(it) }
        val stdT   = avgTime(n, data) { it.sort() }

        val logosM = measureHeap(n, data) { logosSort(it) }
        val mergeM = measureHeap(n, data) { mergeSort(it) }

        println("\n  %,d items".format(n))
        println("  " + "-".repeat(74))
        println("  %-22s  %8s  %10s  %7s  Space".format("Algorithm","Time","Heap Delta","B/item"))
        println("  " + "-".repeat(74))
        println("  %-22s  %6.3fs  %10s  %6.2fB  O(log n)".format(
            "LogosSort (in-place)", logosT, fmtBytes(logosM), logosM.toDouble() / n))
        println("  %-22s  %6.3fs  %10s  %6.2fB  O(n)".format(
            "MergeSort (in-place)", mergeT, fmtBytes(mergeM), mergeM.toDouble() / n))
        println("  %-22s  %6.3fs  %10s  %7s  O(n)  (JVM sort, ref only)".format(
            "IntArray.sort *", stdT, "n/a", "n/a"))
        println("  " + "-".repeat(74))
        println("  Time: %.2fx   Memory: LogosSort uses %.0fx less space".format(
            logosT / mergeT, mergeM.toDouble() / maxOf(logosM, 1L)))
    }
    println("\n* IntArray.sort = JVM introsort. Not a fair peer; shown for scale.")
}
