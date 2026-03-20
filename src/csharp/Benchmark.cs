/**
 * Benchmark: LogosSort vs Array.Sort (introsort) — C#
 *
 * dotnet run --project Benchmark.csproj
 * or:
 *   csc Benchmark.cs LogosSort.cs && mono Benchmark.exe
 */

using System;
using System.Diagnostics;
using LogosSortLib;

class BenchmarkProgram
{
    const int RUNS    = 5;
    const int MAX_VAL = 1_000_000_000;

    static void Main()
    {
        int[] sizes = { 500_000, 2_500_000, 10_000_000 };
        var rng = new Random(42);

        Console.WriteLine("LogosSort vs Array.Sort — C# benchmark");
        Console.WriteLine(new string('=', 60));
        Console.WriteLine($"{"Size",12}  {"LogosSort",11}  {"Array.Sort",11}  {"Ratio",7}");
        Console.WriteLine(new string('-', 60));

        foreach (int n in sizes)
        {
            int[] data = new int[n];
            for (int i = 0; i < n; i++) data[i] = rng.Next(MAX_VAL);

            double logosTot = 0, arrayTot = 0;
            for (int r = 0; r < RUNS; r++)
            {
                logosTot += BenchLogos(data);
                arrayTot += BenchArray(data);
            }

            double logosAvg = logosTot / RUNS;
            double arrayAvg = arrayTot / RUNS;
            double ratio    = logosAvg / arrayAvg;

            Console.WriteLine($"{n,12:N0}  {logosAvg,9:F3}s  {arrayAvg,9:F3}s  {ratio,6:F2}x");
        }
    }

    static double BenchLogos(int[] data)
    {
        int[] arr = (int[])data.Clone();
        var sw = Stopwatch.StartNew();
        LogosSort.Sort(arr);
        sw.Stop();
        return sw.Elapsed.TotalSeconds;
    }

    static double BenchArray(int[] data)
    {
        int[] arr = (int[])data.Clone();
        var sw = Stopwatch.StartNew();
        Array.Sort(arr);
        sw.Stop();
        return sw.Elapsed.TotalSeconds;
    }
}
