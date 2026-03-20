// Benchmark: LogosSort vs sort.Ints (pdqsort)
// Run:  go test -bench=. -benchtime=3x -count=1
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

func BenchmarkLogosSort_500K(b *testing.B) { benchLogos(b, 500_000) }
func BenchmarkLogosSort_2M5(b *testing.B)  { benchLogos(b, 2_500_000) }
func BenchmarkLogosSort_10M(b *testing.B)  { benchLogos(b, 10_000_000) }

func BenchmarkStdSort_500K(b *testing.B) { benchStd(b, 500_000) }
func BenchmarkStdSort_2M5(b *testing.B)  { benchStd(b, 2_500_000) }
func BenchmarkStdSort_10M(b *testing.B)  { benchStd(b, 10_000_000) }

func benchLogos(b *testing.B, n int) {
	data := randomSlice(n)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		arr := make([]int, n)
		copy(arr, data)
		Sort(arr)
	}
}

func benchStd(b *testing.B, n int) {
	data := randomSlice(n)
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		arr := make([]int, n)
		copy(arr, data)
		sort.Ints(arr)
	}
}

// Also run as a standalone comparison
func TestCompareSpeeds(t *testing.T) {
	const runs = 3
	sizes := []int{500_000, 2_500_000, 10_000_000}

	fmt.Println("LogosSort vs sort.Ints — Go benchmark")
	fmt.Println("Size          LogosSort    sort.Ints    Ratio")
	fmt.Println("--------------------------------------------------")

	for _, n := range sizes {
		data := randomSlice(n)

		var logosTotal, stdTotal time.Duration
		for r := 0; r < runs; r++ {
			arr := make([]int, n)

			copy(arr, data)
			t0 := time.Now()
			Sort(arr)
			logosTotal += time.Since(t0)

			copy(arr, data)
			t0 = time.Now()
			sort.Ints(arr)
			stdTotal += time.Since(t0)
		}

		logosAvg := logosTotal / runs
		stdAvg   := stdTotal   / runs
		ratio    := float64(logosAvg) / float64(stdAvg)

		fmt.Printf("%13d  %9.3fs  %9.3fs  %6.2fx\n",
			n, logosAvg.Seconds(), stdAvg.Seconds(), ratio)
	}
}
