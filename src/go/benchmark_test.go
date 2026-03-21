// Benchmark: LogosSort vs Pure-Go Merge Sort vs sort.Ints
//
// Apples-to-apples: Sort vs mergeSort — both pure Go, no stdlib sort calls.
// sort.Ints (pdqsort) shown for reference scale only.
//
// Timing runs are performed without memory tracking.
// Memory is measured separately using runtime.MemStats.TotalAlloc,
// which records cumulative bytes allocated (GC-unaware, reproducible).
//
// Run: go test -run TestCompareSpeeds -v
//      go test -bench=. -benchtime=3x
package logossort

import (
	"fmt"
	"math/rand"
	"runtime"
	"sort"
	"testing"
	"time"
)

const maxVal = 1_000_000_000
const runs   = 3

func randomSlice(n int) []int {
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	a := make([]int, n)
	for i := range a { a[i] = r.Intn(maxVal) }
	return a
}

// ── Pure Go bottom-up merge sort (one auxiliary slice = O(n) space) ───────────

func insertionSortBlock(a []int, lo, hi int) {
	for i := lo + 1; i <= hi; i++ {
		key := a[i]; j := i - 1
		for j >= lo && a[j] > key { a[j+1] = a[j]; j-- }
		a[j+1] = key
	}
}

func mergeSort(arr []int) {
	n := len(arr)
	if n < 2 { return }
	const block = 32
	for lo := 0; lo < n; lo += block {
		hi := lo + block - 1
		if hi >= n { hi = n - 1 }
		insertionSortBlock(arr, lo, hi)
	}

	buf := make([]int, n)   // <-- the single O(n) allocation
	for width := block; width < n; width *= 2 {
		for lo := 0; lo < n; lo += 2 * width {
			mid := lo + width;   if mid > n { mid = n }
			hi  := lo + 2*width; if hi  > n { hi  = n }
			if mid >= hi { copy(buf[lo:hi], arr[lo:hi]); continue }
			i, j, k := lo, mid, lo
			for i < mid && j < hi {
				if arr[i] <= arr[j] { buf[k] = arr[i]; i++ } else { buf[k] = arr[j]; j++ }
				k++
			}
			for i < mid { buf[k] = arr[i]; i++; k++ }
			for j < hi  { buf[k] = arr[j]; j++; k++ }
			copy(arr[lo:hi], buf[lo:hi])
		}
	}
}

// ─────────────────────────────────────────────────────────────────────────────

func benchTime(fn func([]int), data []int) time.Duration {
	arr := make([]int, len(data))
	var total time.Duration
	for r := 0; r < runs; r++ {
		copy(arr, data)
		t0 := time.Now(); fn(arr); total += time.Since(t0)
	}
	return total / runs
}

func benchAlloc(fn func([]int), data []int) uint64 {
	arr := make([]int, len(data))
	copy(arr, data)
	runtime.GC()
	var before, after runtime.MemStats
	runtime.ReadMemStats(&before)
	fn(arr)
	runtime.ReadMemStats(&after)
	return after.TotalAlloc - before.TotalAlloc
}

func fmtBytes(b uint64) string {
	switch {
	case b >= 1<<20: return fmt.Sprintf("%6.1f MB", float64(b)/float64(1<<20))
	case b >= 1<<10: return fmt.Sprintf("%6.1f KB", float64(b)/float64(1<<10))
	default:         return fmt.Sprintf("%6d  B", b)
	}
}

func BenchmarkLogosSort_500K(b *testing.B) { benchB(b, 500_000, Sort) }
func BenchmarkLogosSort_2M5(b *testing.B)  { benchB(b, 2_500_000, Sort) }
func BenchmarkLogosSort_10M(b *testing.B)  { benchB(b, 10_000_000, Sort) }
func BenchmarkMergeSort_500K(b *testing.B) { benchB(b, 500_000, mergeSort) }
func BenchmarkMergeSort_2M5(b *testing.B)  { benchB(b, 2_500_000, mergeSort) }
func BenchmarkMergeSort_10M(b *testing.B)  { benchB(b, 10_000_000, mergeSort) }
func BenchmarkStdSort_500K(b *testing.B)   { benchB(b, 500_000, sort.Ints) }
func BenchmarkStdSort_2M5(b *testing.B)    { benchB(b, 2_500_000, sort.Ints) }
func BenchmarkStdSort_10M(b *testing.B)    { benchB(b, 10_000_000, sort.Ints) }

func benchB(b *testing.B, n int, fn func([]int)) {
	data := randomSlice(n); b.ResetTimer()
	for i := 0; i < b.N; i++ { arr := make([]int, n); copy(arr, data); fn(arr) }
}

func TestCompareSpeeds(t *testing.T) {
	sizes := []int{500_000, 2_500_000, 10_000_000}

	fmt.Println("============================================================================")
	fmt.Println("LogosSort vs Pure-Go Merge Sort -- Time + Space Complexity")
	fmt.Println("Timing: avg of 3 runs (no mem tracking).  Memory: 1 tracked pass.")
	fmt.Println("sort.Ints (pdqsort) shown for reference only.")
	fmt.Println("============================================================================")

	for _, n := range sizes {
		data := randomSlice(n)

		logosT := benchTime(Sort,      data)
		mergeT := benchTime(mergeSort, data)
		stdT   := benchTime(sort.Ints, data)

		logosM := benchAlloc(Sort,      data)
		mergeM := benchAlloc(mergeSort, data)

		bpiLogos := float64(logosM) / float64(n)
		bpiMerge := float64(mergeM) / float64(n)

		fmt.Printf("\n  %d items\n", n)
		fmt.Println("  --------------------------------------------------------------------------")
		fmt.Printf("  %-22s  %8s  %9s  %7s  Space\n", "Algorithm", "Time", "Alloc'd", "B/item")
		fmt.Println("  --------------------------------------------------------------------------")
		fmt.Printf("  %-22s  %6.3fs  %9s  %6.2fB  O(log n)\n",
			"LogosSort (in-place)", logosT.Seconds(), fmtBytes(logosM), bpiLogos)
		fmt.Printf("  %-22s  %6.3fs  %9s  %6.2fB  O(n)\n",
			"MergeSort (in-place)", mergeT.Seconds(), fmtBytes(mergeM), bpiMerge)
		fmt.Printf("  %-22s  %6.3fs  %9s  %7s  O(n)  (stdlib, ref only)\n",
			"sort.Ints *", stdT.Seconds(), "n/a", "n/a")
		fmt.Println("  --------------------------------------------------------------------------")
		fmt.Printf("  Time: %.2fx   Memory: LogosSort uses %.0fx less space\n",
			logosT.Seconds()/mergeT.Seconds(), float64(mergeM)/float64(logosM))
	}
	fmt.Println("\n* sort.Ints = Go stdlib pdqsort. Not a fair peer; shown for scale.")
}
