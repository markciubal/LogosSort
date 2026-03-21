/**
 * Benchmark: LogosSort vs Pure-C# Merge Sort vs Array.Sort
 * Time + Space complexity at 500 000 · 2 500 000 · 10 000 000 items.
 *
 * Timing runs have no GC hooks.
 * Memory measured via GC.GetTotalMemory() delta (managed heap only).
 * LogosSort uses insertion sort at base cases → O(log n) auxiliary.
 * MergeSort uses one buffer of size n → O(n) auxiliary.
 *
 * Run: dotnet run  (or compile with csc and run Benchmark.exe)
 */

using System;
using System.Diagnostics;
using LogosSortLib;

class BenchmarkProgram
{
    const int RUNS    = 3;
    const int MAX_VAL = 1_000_000_000;

    static void Main()
    {
        int[] sizes = { 500_000, 2_500_000, 10_000_000 };
        var rng = new Random(42);

        Console.WriteLine("============================================================================");
        Console.WriteLine("LogosSort vs Pure-C# Merge Sort -- Time + Space Complexity");
        Console.WriteLine("Timing: avg of 3 runs.  Memory: managed heap delta via GC.GetTotalMemory.");
        Console.WriteLine("Array.Sort shown for reference only.");
        Console.WriteLine("============================================================================");

        foreach (int n in sizes)
        {
            int[] data = new int[n];
            for (int i = 0; i < n; i++) data[i] = rng.Next(MAX_VAL);

            double logosT = AvgTime(data, a => LogosSort.Sort(a));
            double mergeT = AvgTime(data, a => MergeSort(a));
            double stdT   = AvgTime(data, a => Array.Sort(a));

            long logosM = MeasureHeap(data, a => LogosSort.Sort(a));
            long mergeM = MeasureHeap(data, a => MergeSort(a));

            Console.WriteLine($"\n  {n:N0} items");
            Console.WriteLine("  --------------------------------------------------------------------------");
            Console.WriteLine($"  {"Algorithm",-22}  {"Time",8}  {"Heap Delta",10}  {"B/item",7}  Space");
            Console.WriteLine("  --------------------------------------------------------------------------");
            Console.WriteLine($"  {"LogosSort (in-place)",-22}  {logosT,6:F3}s  {FmtBytes(logosM),10}  {(double)logosM/n,6:F2}B  O(log n)");
            Console.WriteLine($"  {"MergeSort (in-place)",-22}  {mergeT,6:F3}s  {FmtBytes(mergeM),10}  {(double)mergeM/n,6:F2}B  O(n)");
            Console.WriteLine($"  {"Array.Sort *",-22}  {stdT,6:F3}s  {"n/a",10}  {"n/a",7}  O(n)  (stdlib, ref only)");
            Console.WriteLine("  --------------------------------------------------------------------------");
            Console.WriteLine($"  Time: {logosT/mergeT:F2}x   Memory: LogosSort uses {(double)mergeM/Math.Max(logosM,1):F0}x less space");
        }
        Console.WriteLine("\n* Array.Sort = .NET introsort. Not a fair peer; shown for scale.");
    }

    // ── Pure C# bottom-up merge sort (one int[] buffer = O(n) space) ──────────

    static void MergeSort(int[] arr)
    {
        int n = arr.Length;
        if (n < 2) return;
        const int BLOCK = 32;
        for (int lo = 0; lo < n; lo += BLOCK)
            InsertionSort(arr, lo, Math.Min(lo + BLOCK - 1, n - 1));

        int[] buf = new int[n];   // <-- the single O(n) allocation
        for (int width = BLOCK; width < n; width *= 2)
        {
            for (int lo = 0; lo < n; lo += 2 * width)
            {
                int mid = Math.Min(lo + width,     n);
                int hi  = Math.Min(lo + 2 * width, n);
                if (mid >= hi) { Array.Copy(arr, lo, buf, lo, hi - lo); continue; }
                int i = lo, j = mid, k = lo;
                while (i < mid && j < hi)
                    buf[k++] = arr[i] <= arr[j] ? arr[i++] : arr[j++];
                while (i < mid) buf[k++] = arr[i++];
                while (j < hi)  buf[k++] = arr[j++];
                Array.Copy(buf, lo, arr, lo, hi - lo);
            }
        }
    }

    static void InsertionSort(int[] a, int lo, int hi)
    {
        for (int i = lo + 1; i <= hi; i++)
        {
            int key = a[i], j = i - 1;
            while (j >= lo && a[j] > key) { a[j + 1] = a[j]; j--; }
            a[j + 1] = key;
        }
    }

    // ── Harness ───────────────────────────────────────────────────────────────

    static double AvgTime(int[] data, Action<int[]> fn)
    {
        double total = 0;
        for (int r = 0; r < RUNS; r++)
        {
            int[] arr = (int[])data.Clone();
            var sw = Stopwatch.StartNew();
            fn(arr);
            sw.Stop();
            total += sw.Elapsed.TotalSeconds;
        }
        return total / RUNS;
    }

    static long MeasureHeap(int[] data, Action<int[]> fn)
    {
        int[] arr = (int[])data.Clone();
        GC.Collect(); GC.WaitForPendingFinalizers(); GC.Collect();
        long before = GC.GetTotalMemory(true);
        fn(arr);
        long after = GC.GetTotalMemory(false);
        return Math.Max(after - before, 0);
    }

    static string FmtBytes(long b)
    {
        if (b >= 1 << 20) return $"{b / (double)(1 << 20),6:F1} MB";
        if (b >= 1 << 10) return $"{b / (double)(1 << 10),6:F1} KB";
        return $"{b,6}  B";
    }
}
