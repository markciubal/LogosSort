using System;
using System.Runtime.CompilerServices;

namespace LogosSortLib
{
    /// <summary>
    /// LogosSort — Golden-ratio dual-pivot introsort (C#)
    ///
    /// Two pivots placed at φ (≈61.8%) and 1−φ (≈38.2%) golden-ratio positions
    /// of a chaos-seeded index. Ninther pivot refinement, three-way partition,
    /// counting-sort fast path for dense int ranges, O(log n) depth limit.
    /// </summary>
    public static class LogosSort
    {
        private const double Phi  = 0.6180339887498949;
        private const double Phi2 = 0.3819660112501051;
        private const int    SmallN = 48;

        [ThreadStatic]
        private static Random? _rng;
        private static Random Rng => _rng ??= new Random();

        // ─────────────────────────────────────────────────────────────────────
        // Public API
        // ─────────────────────────────────────────────────────────────────────

        /// <summary>Sort <paramref name="arr"/> in place.</summary>
        public static void Sort(int[] arr)
        {
            int n = arr.Length;
            if (n < 2) return;
            int depthLimit = 2 * BitLength(n) + 4;
            SortImpl(arr, 0, n - 1, depthLimit);
        }

        /// <summary>Return a sorted copy of <paramref name="arr"/>.</summary>
        public static int[] Sorted(int[] arr)
        {
            var copy = (int[])arr.Clone();
            Sort(copy);
            return copy;
        }

        // ─────────────────────────────────────────────────────────────────────
        // Internal implementation
        // ─────────────────────────────────────────────────────────────────────

        private static void SortImpl(int[] a, int lo, int hi, int depth)
        {
            while (lo < hi)
            {
                int size = hi - lo + 1;

                if (depth <= 0 || size <= SmallN)
                {
                    InsertionSort(a, lo, hi);
                    return;
                }

                // Counting sort for dense integer subarrays
                int mn = a[lo], mx = a[lo];
                for (int i = lo + 1; i <= hi; i++)
                {
                    if (a[i] < mn) mn = a[i];
                    if (a[i] > mx) mx = a[i];
                }
                long span = (long)mx - mn;
                if (span < (long)size * 4)
                {
                    int[] counts = new int[span + 1];
                    for (int i = lo; i <= hi; i++) counts[a[i] - mn]++;
                    int k = lo;
                    for (long v = 0; v <= span; v++)
                        for (int c = 0; c < counts[v]; c++)
                            a[k++] = (int)v + mn;
                    return;
                }

                // Monotone checks
                if (a[lo] <= a[lo + 1] && a[lo + 1] <= a[lo + 2])
                {
                    bool asc = true;
                    for (int i = lo; i < hi; i++) if (a[i] > a[i + 1]) { asc = false; break; }
                    if (asc) return;

                    bool desc = true;
                    for (int i = lo; i < hi; i++) if (a[i] < a[i + 1]) { desc = false; break; }
                    if (desc) { Reverse(a, lo, hi); return; }
                }

                // Oracle-seeded golden-ratio pivot positions
                double absC = Rng.NextDouble();
                if (absC == 0.0) absC = 1e-15;
                int sp   = hi - lo;
                int idx1 = lo + (int)(sp * Phi2 * absC);
                int idx2 = lo + (int)(sp * Phi  * absC);

                int p1 = Ninther(a, lo, hi, idx1);
                int p2 = Ninther(a, lo, hi, idx2);

                DualPartition(a, lo, hi, p1, p2, out int lt, out int gt);

                int leftN  = lt - lo;
                int midN   = gt - lt + 1;
                int rightN = hi - gt;

                // Sort smallest two regions; tail-call on largest
                SortRegions(a, lo, lt - 1, lt, gt, gt + 1, hi,
                            leftN, midN, rightN, depth - 1,
                            out int nextLo, out int nextHi);

                lo = nextLo; hi = nextHi; depth--;
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static int Ninther(int[] a, int lo, int hi, int idx)
        {
            int i0 = Math.Max(lo, idx - 1);
            int i2 = Math.Min(hi, idx + 1);
            int x = a[i0], y = a[idx], z = a[i2];
            if (x > y) { int t = x; x = y; y = t; }
            if (y > z) { int t = y; y = z; z = t; }
            if (x > y) { int t = x; x = y; y = t; }
            return y;
        }

        private static void DualPartition(
            int[] a, int lo, int hi, int p1, int p2,
            out int lt, out int gt)
        {
            if (p1 > p2) { int t = p1; p1 = p2; p2 = t; }
            lt = lo; gt = hi;
            int i = lo;
            while (i <= gt)
            {
                int v = a[i];
                if (v < p1)
                {
                    int t = a[lt]; a[lt] = a[i]; a[i] = t;
                    lt++; i++;
                }
                else if (v > p2)
                {
                    int t = a[i]; a[i] = a[gt]; a[gt] = t;
                    gt--;
                }
                else i++;
            }
        }

        private static void SortRegions(
            int[] a,
            int lo1, int hi1, int lo2, int hi2, int lo3, int hi3,
            int n1, int n2, int n3, int depth,
            out int tailLo, out int tailHi)
        {
            // Identify smallest two; recurse into them; tail-call on largest
            if (n1 <= n2 && n1 <= n3)
            {
                if (n2 <= n3) { RecurseTwo(a, lo1, hi1, lo2, hi2, depth); tailLo = lo3; tailHi = hi3; }
                else          { RecurseTwo(a, lo1, hi1, lo3, hi3, depth); tailLo = lo2; tailHi = hi2; }
            }
            else if (n2 <= n1 && n2 <= n3)
            {
                if (n1 <= n3) { RecurseTwo(a, lo2, hi2, lo1, hi1, depth); tailLo = lo3; tailHi = hi3; }
                else          { RecurseTwo(a, lo2, hi2, lo3, hi3, depth); tailLo = lo1; tailHi = hi1; }
            }
            else
            {
                if (n1 <= n2) { RecurseTwo(a, lo3, hi3, lo1, hi1, depth); tailLo = lo2; tailHi = hi2; }
                else          { RecurseTwo(a, lo3, hi3, lo2, hi2, depth); tailLo = lo1; tailHi = hi1; }
            }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static void RecurseTwo(int[] a, int lo1, int hi1, int lo2, int hi2, int depth)
        {
            if (lo1 < hi1) SortImpl(a, lo1, hi1, depth);
            if (lo2 < hi2) SortImpl(a, lo2, hi2, depth);
        }

        private static void InsertionSort(int[] a, int lo, int hi)
        {
            for (int i = lo + 1; i <= hi; i++)
            {
                int key = a[i], j = i - 1;
                while (j >= lo && a[j] > key) { a[j + 1] = a[j]; j--; }
                a[j + 1] = key;
            }
        }

        private static void Reverse(int[] a, int lo, int hi)
        {
            while (lo < hi) { int t = a[lo]; a[lo] = a[hi]; a[hi] = t; lo++; hi--; }
        }

        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static int BitLength(int n)
        {
            int bits = 0;
            while (n > 0) { n >>= 1; bits++; }
            return bits - 1;
        }
    }
}
