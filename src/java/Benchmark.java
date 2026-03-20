package logossort;

import java.util.Arrays;
import java.util.Random;

/**
 * Benchmark: LogosSort vs Arrays.sort (Java dual-pivot quicksort / Timsort)
 * Sizes: 500 000 · 2 500 000 · 10 000 000
 *
 * Compile & run:
 *   javac -d out src/java/LogosSort.java src/java/Benchmark.java
 *   java -cp out logossort.Benchmark
 */
public class Benchmark {

    private static final int RUNS    = 3;
    private static final int MAX_VAL = 1_000_000_000;

    public static void main(String[] args) {
        int[] sizes = {500_000, 2_500_000, 10_000_000};
        Random rng  = new Random(42);

        System.out.println("LogosSort vs Arrays.sort — Java benchmark");
        System.out.println("=".repeat(60));
        System.out.printf("%12s  %11s  %11s  %7s%n", "Size", "LogosSort", "Arrays.sort", "Ratio");
        System.out.println("-".repeat(60));

        for (int n : sizes) {
            int[] data = new int[n];
            for (int i = 0; i < n; i++) data[i] = rng.nextInt(MAX_VAL);

            double logosTotal = 0, timTotal = 0;
            for (int r = 0; r < RUNS; r++) {
                logosTotal += benchLogos(data);
                timTotal   += benchTim(data);
            }

            double logosAvg = logosTotal / RUNS;
            double timAvg   = timTotal   / RUNS;
            double ratio    = logosAvg / timAvg;

            System.out.printf("%,12d  %9.3fs  %9.3fs  %6.2fx%n",
                n, logosAvg, timAvg, ratio);
        }
    }

    private static double benchLogos(int[] data) {
        int[] arr = Arrays.copyOf(data, data.length);
        long t0 = System.nanoTime();
        LogosSort.sortInPlace(arr);
        return (System.nanoTime() - t0) / 1e9;
    }

    private static double benchTim(int[] data) {
        int[] arr = Arrays.copyOf(data, data.length);
        long t0 = System.nanoTime();
        Arrays.sort(arr);
        return (System.nanoTime() - t0) / 1e9;
    }
}
