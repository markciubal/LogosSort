// Benchmark: LogosSort vs Pure-Go Merge Sort vs sort.Ints
//
// Apples-to-apples: Sort vs mergeSort — both pure Go, no stdlib sort calls.
// sort.Ints (pdqsort) shown for reference scale only.
//
// Run: go test -run TestCompareSpeeds -v
//      go test -bench=. -benchtime=3x
package logossort

import (
	"fmt"
	"math/rand"
	"sort"
	"testing"
	"time"
)

const maxVal = 1_000_000_000

func randomSlice(n int) []int {
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	a := make([]int, n)
	for i := range a {
		a[i] = r.Intn(maxVal)
	}
	return a
}

// ── Pure Go bottom-up merge sort (no sort.Ints) ───────────────────────────────

func insertionSortBlock(a []int, lo, hi int) {
	for i := lo + 1; i <= hi; i++ {
		key := a[i]
		j := i - 1
		for j >= lo && a[j] > key {
			a[j+1] = a[j]
			j--
		}
		a[j+1] = key
	}
}

func mergeSort(input []int) []int {
	n := len(input)
	if n < 2 {
		s := make([]int, n)
		copy(s, input)
		return s
	}
	const block = 32
	src := make([]int, n)
	dst := make([]int, n)
	copy(src, input)

	for lo := 0; lo < n; lo += block {
		hi := lo + block - 1
		if hi >= n {
			hi = n - 1
		}
		insertionSortBlock(src, lo, hi)
	}

	for width := block; width < n; width *= 2 {
		for lo := 0; lo < n; lo += 2 * width {
			mid := lo + width
			if mid > n {
				mid = n
			}
			hi := lo + 2*width
			if hi > n {
				hi = n
			}
			if mid >= hi {
				copy(dst[lo:hi], src[lo:hi])
				continue
			}
			i, j, k := lo, mid, lo
			for i < mid && j < hi {
				if src[i] <= src[j] {
					dst[k] = src[i]
					i++
				} else {
					dst[k] = src[j]
					j++
				}
				k++
			}
			for i < mid {
				dst[k] = src[i]; i++; k++
			}
			for j < hi {
				dst[k] = src[j]; j++; k++
			}
		}
		src, dst = dst, src
	}
	return src
}

// ─────────────────────────────────────────────────────────────────────────────

func BenchmarkLogosSort_500K(b *testing.B)  { benchLogos(b, 500_000) }
func BenchmarkLogosSort_2M5(b *testing.B)   { benchLogos(b, 2_500_000) }
func BenchmarkLogosSort_10M(b *testing.B)   { benchLogos(b, 10_000_000) }
func BenchmarkMergeSort_500K(b *testing.B)  { benchMerge(b, 500_000) }
func BenchmarkMergeSort_2M5(b *testing.B)   { benchMerge(b, 2_500_000) }
func BenchmarkMergeSort_10M(b *testing.B)   { benchMerge(b, 10_000_000) }
func BenchmarkStdSort_500K(b *testing.B)    { benchStd(b, 500_000) }
func BenchmarkStdSort_2M5(b *testing.B)     { benchStd(b, 2_500_000) }
func BenchmarkStdSort_10M(b *testing.B)     { benchStd(b, 10_000_000) }

func benchLogos(b *testing.B, n int) {
	data := randomSlice(n)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		arr := make([]int, n); copy(arr, data); Sort(arr)
	}
}
func benchMerge(b *testing.B, n int) {
	data := randomSlice(n)
	b.ResetTimer()
	for i := 0; i < b.N; i++ { mergeSort(data) }
}
func benchStd(b *testing.B, n int) {
	data := randomSlice(n)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		arr := make([]int, n); copy(arr, data); sort.Ints(arr)
	}
}

func TestCompareSpeeds(t *testing.T) {
	const runs = 3
	sizes := []int{500_000, 2_500_000, 10_000_000}

	fmt.Println("=" + fmt.Sprintf("%s", "=========================================================================="))
	fmt.Println("LogosSort vs Pure-Go Merge Sort  (apples-to-apples)")
	fmt.Println("sort.Ints (pdqsort) shown for reference only")
	fmt.Println("==========================================================================")
	fmt.Printf("%-13s  %-11s  %-11s  %-11s  %-9s\n",
		"Size", "LogosSort", "MergeSort", "sort.Ints", "L/M ratio")
	fmt.Println("--------------------------------------------------------------------------")

	for _, n := range sizes {
		data := randomSlice(n)

		var logosTotal, mergeTotal, stdTotal time.Duration
		for r := 0; r < runs; r++ {
			arr := make([]int, n)

			copy(arr, data)
			t0 := time.Now(); Sort(arr); logosTotal += time.Since(t0)

			t0 = time.Now(); mergeSort(data); mergeTotal += time.Since(t0)

			copy(arr, data)
			t0 = time.Now(); sort.Ints(arr); stdTotal += time.Since(t0)
		}

		la := logosTotal / runs
		ma  := mergeTotal  / runs
		sa  := stdTotal    / runs
		ratio := float64(la) / float64(ma)

		fmt.Printf("%13d  %9.3fs  %9.3fs  %9.3fs  %8.2fx\n",
			n, la.Seconds(), ma.Seconds(), sa.Seconds(), ratio)
	}
	fmt.Println("\nL/M ratio < 1.0 means LogosSort is faster than pure-Go merge sort.")
}
