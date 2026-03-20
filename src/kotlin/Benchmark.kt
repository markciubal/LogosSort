/**
 * Benchmark: logosSort vs IntArray.sort — Kotlin
 *
 * kotlinc LogosSort.kt Benchmark.kt -include-runtime -d bench.jar
 * java -jar bench.jar
 */

import kotlin.random.Random
import kotlin.system.measureNanoTime

private const val RUNS    = 5
private const val MAX_VAL = 1_000_000_000

fun randomArray(n: Int): IntArray =
    IntArray(n) { Random.nextInt(0, MAX_VAL) }

fun main() {
    val sizes = intArrayOf(500_000, 2_500_000, 10_000_000)

    println("LogosSort vs IntArray.sort — Kotlin benchmark")
    println("=".repeat(60))
    println("%12s  %11s  %11s  %7s".format("Size", "LogosSort", "IntArray.sort", "Ratio"))
    println("-".repeat(60))

    for (n in sizes) {
        val data = randomArray(n)

        var logosTot = 0L; var stdTot = 0L
        repeat(RUNS) {
            val a1 = data.copyOf()
            logosTot += measureNanoTime { logosSort(a1) }

            val a2 = data.copyOf()
            stdTot  += measureNanoTime { a2.sort() }
        }

        val logosAvg = logosTot / RUNS / 1e9
        val stdAvg   = stdTot   / RUNS / 1e9
        val ratio    = logosAvg / stdAvg

        println("%,12d  %9.3fs  %9.3fs  %6.2fx".format(n, logosAvg, stdAvg, ratio))
    }
}
