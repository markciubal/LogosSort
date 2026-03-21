package logossort;

import java.util.Arrays;
import java.util.Random;

/**
 * Benchmark: LogosSort vs Pure-Java Merge Sort vs Arrays.sort
 * Time + Space complexity at 500 000 · 2 500 000 · 10 000 000 items.
 *
 * Timing runs have no GC hooks.
 * Memory is measured as the delta in live heap bytes (before/after GC+sort).
 * LogosSort uses insertion sort at base cases → O(log n) auxiliary.
 * MergeSort uses one buffer of size n → O(n) auxiliary.
 *
 * Compile & run:
 *   javac -d out src/java/LogosSort.java src/java/Benchmark.java
 *   java -Xmx4g -cp out logossort.Benchmark
 */
public class Benchmark {

    private static final int RUNS    = 3;
    private static final int MAX_VAL = 1_000_000_000;

    public static void main(String[] args) {
        int[] sizes = {500_000, 2_500_000, 10_000_000};
        Random rng  = new Random(42);

        System.out.println("============================================================================");
        System.out.println("LogosSort vs Pure-Java Merge Sort -- Time + Space Complexity");
        System.out.println("Timing: avg of 3 runs.  Memory: heap delta measured via Runtime.");
        System.out.println("Arrays.sort shown for reference only.");
        System.out.println("============================================================================");

        for (int n : sizes) {
            int[] data = new int[n];
            for (int i = 0; i < n; i++) data[i] = rng.nextInt(MAX_VAL);

            double logosT = avgTime(() -> { int[] a = Arrays.copyOf(data, n); LogosSort.sortInPlace(a); });
            double mergeT = avgTime(() -> { int[] a = Arrays.copyOf(data, n); mergeSort(a); });
            double stdT   = avgTime(() -> { int[] a = Arrays.copyOf(data, n); Arrays.sort(a); });

            long logosM = measureHeap(() -> { int[] a = Arrays.copyOf(data, n); LogosSort.sortInPlace(a); });
            long mergeM = measureHeap(() -> { int[] a = Arrays.copyOf(data, n); mergeSort(a); });

            System.out.printf("%n  %,d items%n", n);
            System.out.println("  --------------------------------------------------------------------------");
            System.out.printf("  %-22s  %8s  %10s  %7s  Space%n", "Algorithm", "Time", "Peak Heap", "B/item");
            System.out.println("  --------------------------------------------------------------------------");
            System.out.printf("  %-22s  %6.3fs  %10s  %6.2fB  O(log n)%n",
                "LogosSort (in-place)", logosT, fmtBytes(logosM), (double) logosM / n);
            System.out.printf("  %-22s  %6.3fs  %10s  %6.2fB  O(n)%n",
                "MergeSort (in-place)", mergeT, fmtBytes(mergeM), (double) mergeM / n);
            System.out.printf("  %-22s  %6.3fs  %10s  %7s  O(n)  (stdlib, ref only)%n",
                "Arrays.sort *", stdT, "n/a", "n/a");
            System.out.println("  --------------------------------------------------------------------------");
            System.out.printf("  Time: %.2fx   Memory: LogosSort uses %.0fx less space%n",
                logosT / mergeT, (double) mergeM / Math.max(logosM, 1));
        }
        System.out.println("\n* Arrays.sort = JVM dual-pivot quicksort. Not a fair peer; shown for scale.");
    }

    // ── Pure Java bottom-up merge sort (one int[] buffer = O(n) space) ────────

    static void mergeSort(int[] arr) {
        int n = arr.length;
        if (n < 2) return;
        final int BLOCK = 32;
        for (int lo = 0; lo < n; lo += BLOCK)
            insertionSort(arr, lo, Math.min(lo + BLOCK - 1, n - 1));

        int[] buf = new int[n];  // <-- the single O(n) allocation
        for (int width = BLOCK; width < n; width *= 2) {
            for (int lo = 0; lo < n; lo += 2 * width) {
                int mid = Math.min(lo + width,     n);
                int hi  = Math.min(lo + 2 * width, n);
                if (mid >= hi) { System.arraycopy(arr, lo, buf, lo, hi - lo); continue; }
                int i = lo, j = mid, k = lo;
                while (i < mid && j < hi)
                    buf[k++] = arr[i] <= arr[j] ? arr[i++] : arr[j++];
                while (i < mid) buf[k++] = arr[i++];
                while (j < hi)  buf[k++] = arr[j++];
                System.arraycopy(buf, lo, arr, lo, hi - lo);
            }
        }
    }

    static void insertionSort(int[] a, int lo, int hi) {
        for (int i = lo + 1; i <= hi; i++) {
            int key = a[i], j = i - 1;
            while (j >= lo && a[j] > key) { a[j + 1] = a[j]; j--; }
            a[j + 1] = key;
        }
    }

    // ── Harness ───────────────────────────────────────────────────────────────

    @FunctionalInterface interface Task { void run(); }

    static double avgTime(Task t) {
        double total = 0;
        for (int r = 0; r < RUNS; r++) {
            long t0 = System.nanoTime(); t.run();
            total += (System.nanoTime() - t0) / 1e9;
        }
        return total / RUNS;
    }

    static long measureHeap(Task t) {
        System.gc(); System.gc();
        Runtime rt = Runtime.getRuntime();
        long before = rt.totalMemory() - rt.freeMemory();
        t.run();
        long after = rt.totalMemory() - rt.freeMemory();
        return Math.max(after - before, 0);
    }

    static String fmtBytes(long b) {
        if (b >= 1 << 20) return String.format("%6.1f MB", b / (double)(1 << 20));
        if (b >= 1 << 10) return String.format("%6.1f KB", b / (double)(1 << 10));
        return String.format("%6d  B", b);
    }
}
