package logossort;

import java.util.Arrays;
import java.util.Random;

/**
 * LogosSort — Golden-ratio dual-pivot introsort (Java)
 *
 * Two pivots placed at φ (≈61.8%) and 1−φ (≈38.2%) golden-ratio positions
 * of a chaos-seeded index. Ninther pivot refinement, three-way partition,
 * counting-sort fast path for dense int ranges, O(log n) depth limit.
 */
public final class LogosSort {

    private static final double PHI   = 0.6180339887498949;
    private static final double PHI2  = 0.3819660112501051;
    private static final int    SMALL = 48;

    private static final ThreadLocal<Random> RNG =
        ThreadLocal.withInitial(Random::new);

    private LogosSort() {}

    // -------------------------------------------------------------------------
    // Public entry points
    // -------------------------------------------------------------------------

    /** Sort a copy of {@code arr} and return it. */
    public static int[] sort(int[] arr) {
        int[] a = Arrays.copyOf(arr, arr.length);
        sortInPlace(a);
        return a;
    }

    /** Sort {@code arr} in place. */
    public static void sortInPlace(int[] arr) {
        int n = arr.length;
        if (n < 2) return;
        int depthLimit = 2 * (31 - Integer.numberOfLeadingZeros(n)) + 4;
        sortImpl(arr, 0, n - 1, depthLimit);
    }

    // -------------------------------------------------------------------------
    // Internal helpers
    // -------------------------------------------------------------------------

    private static int ninther(int[] a, int lo, int hi, int idx) {
        int i0 = Math.max(lo, idx - 1);
        int i2 = Math.min(hi, idx + 1);
        int x = a[i0], y = a[idx], z = a[i2];
        if (x > y) { int t = x; x = y; y = t; }
        if (y > z) { int t = y; y = z; z = t; }
        if (x > y) { int t = x; x = y; y = t; }
        return y;
    }

    /** Returns [lt, gt] packed as a long: lt in high 32 bits, gt in low 32 bits. */
    private static long dualPartition(int[] a, int lo, int hi, int p1, int p2) {
        if (p1 > p2) { int t = p1; p1 = p2; p2 = t; }
        int lt = lo, gt = hi, i = lo;
        while (i <= gt) {
            int v = a[i];
            if (v < p1) {
                int t = a[lt]; a[lt] = a[i]; a[i] = t;
                lt++; i++;
            } else if (v > p2) {
                int t = a[i]; a[i] = a[gt]; a[gt] = t;
                gt--;
            } else {
                i++;
            }
        }
        return ((long) lt << 32) | (gt & 0xFFFFFFFFL);
    }

    private static void sortImpl(int[] a, int lo, int hi, int depth) {
        while (lo < hi) {
            int size = hi - lo + 1;

            if (depth <= 0 || size <= SMALL) {
                insertionSort(a, lo, hi);
                return;
            }

            // Counting sort for dense integer subarrays
            int mn = a[lo], mx = a[lo];
            for (int i = lo + 1; i <= hi; i++) {
                if (a[i] < mn) mn = a[i];
                if (a[i] > mx) mx = a[i];
            }
            long span = (long) mx - mn;
            if (span < (long) size * 4) {
                int[] counts = new int[(int) span + 1];
                for (int i = lo; i <= hi; i++) counts[a[i] - mn]++;
                int k = lo;
                for (int v = 0; v <= (int) span; v++)
                    for (int c = 0; c < counts[v]; c++)
                        a[k++] = v + mn;
                return;
            }

            // Monotone checks
            if (a[lo] <= a[lo + 1] && a[lo + 1] <= a[lo + 2]) {
                boolean asc = true;
                for (int i = lo; i < hi; i++) if (a[i] > a[i + 1]) { asc = false; break; }
                if (asc) return;

                boolean desc = true;
                for (int i = lo; i < hi; i++) if (a[i] < a[i + 1]) { desc = false; break; }
                if (desc) { reverse(a, lo, hi); return; }
            }

            // Oracle-seeded golden-ratio pivot positions
            double absC = Math.abs(RNG.get().nextDouble() * 2 - 1);
            if (absC == 0.0) absC = 1e-15;
            int sp   = hi - lo;
            int idx1 = lo + (int) (sp * PHI2 * absC);
            int idx2 = lo + (int) (sp * PHI  * absC);

            int p1 = ninther(a, lo, hi, idx1);
            int p2 = ninther(a, lo, hi, idx2);

            long packed = dualPartition(a, lo, hi, p1, p2);
            int lt = (int) (packed >>> 32);
            int gt = (int) (packed & 0xFFFFFFFFL);

            int leftN  = lt - lo;
            int midN   = gt - lt + 1;
            int rightN = hi - gt;

            // Sort two smaller regions; tail-recurse on largest
            int[] ns  = {leftN,  midN,   rightN};
            int[] los = {lo,     lt,     gt + 1};
            int[] his = {lt - 1, gt,     hi    };

            // Bubble-sort three elements by size
            for (int i = 0; i < 2; i++) {
                for (int j = 0; j < 2 - i; j++) {
                    if (ns[j] > ns[j + 1]) {
                        swap3(ns, j, j + 1);
                        swap3(los, j, j + 1);
                        swap3(his, j, j + 1);
                    }
                }
            }

            for (int i = 0; i < 2; i++)
                if (los[i] < his[i]) sortImpl(a, los[i], his[i], depth - 1);

            lo = los[2]; hi = his[2]; depth--;
        }
    }

    private static void insertionSort(int[] a, int lo, int hi) {
        for (int i = lo + 1; i <= hi; i++) {
            int key = a[i], j = i - 1;
            while (j >= lo && a[j] > key) { a[j + 1] = a[j]; j--; }
            a[j + 1] = key;
        }
    }

    private static void reverse(int[] a, int lo, int hi) {
        while (lo < hi) { int t = a[lo]; a[lo] = a[hi]; a[hi] = t; lo++; hi--; }
    }

    private static void swap3(int[] arr, int i, int j) {
        int t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
}
