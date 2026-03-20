// Package logossort implements LogosSort — a golden-ratio dual-pivot introsort.
//
// Self-contained — zero calls to sort.Ints or any stdlib sort internally.
// Insertion sort is used for base cases so the algorithm stands alone.
package logossort

import (
	"math"
	"math/rand"
)

const (
	phi    = 0.6180339887498949
	phi2   = 0.3819660112501051
	smallN = 48
)

// Sort sorts a slice of int in place using LogosSort.
func Sort(a []int) {
	n := len(a)
	if n < 2 {
		return
	}
	depth := 2*ilog2(n) + 4
	sortImpl(a, 0, n-1, depth)
}

// Sorted returns a sorted copy of a.
func Sorted(a []int) []int {
	out := make([]int, len(a))
	copy(out, a)
	Sort(out)
	return out
}

func sortImpl(a []int, lo, hi, depth int) {
	for lo < hi {
		size := hi - lo + 1

		// Base case: pure Go insertion sort — no sort.Ints call
		if depth <= 0 || size <= smallN {
			insertionSort(a, lo, hi)
			return
		}

		// Counting sort for dense integer subarrays
		mn, mx := a[lo], a[lo]
		for i := lo + 1; i <= hi; i++ {
			if a[i] < mn {
				mn = a[i]
			}
			if a[i] > mx {
				mx = a[i]
			}
		}
		span := mx - mn
		if span >= 0 && span < size*4 {
			counts := make([]int, span+1)
			for i := lo; i <= hi; i++ {
				counts[a[i]-mn]++
			}
			k := lo
			for v, cnt := range counts {
				for c := 0; c < cnt; c++ {
					a[k] = v + mn
					k++
				}
			}
			return
		}

		// Monotone checks
		if a[lo] <= a[lo+1] && a[lo+1] <= a[lo+2] {
			asc := true
			for i := lo; i < hi; i++ {
				if a[i] > a[i+1] {
					asc = false
					break
				}
			}
			if asc {
				return
			}
			desc := true
			for i := lo; i < hi; i++ {
				if a[i] < a[i+1] {
					desc = false
					break
				}
			}
			if desc {
				for l, r := lo, hi; l < r; l, r = l+1, r-1 {
					a[l], a[r] = a[r], a[l]
				}
				return
			}
		}

		// Oracle-seeded golden-ratio pivot positions
		absC := rand.Float64()
		if absC == 0.0 {
			absC = 1e-15
		}
		sp   := hi - lo
		idx1 := lo + int(float64(sp)*phi2*absC)
		idx2 := lo + int(float64(sp)*phi*absC)

		p1 := ninther(a, lo, hi, idx1)
		p2 := ninther(a, lo, hi, idx2)

		lt, gt := dualPartition(a, lo, hi, p1, p2)

		// Sort 3 region descriptors by size — comparison network, no stdlib sort
		type region struct{ n, lo, hi int }
		r0 := region{lt - lo, lo, lt - 1}
		r1 := region{gt - lt + 1, lt, gt}
		r2 := region{hi - gt, gt + 1, hi}
		if r0.n > r1.n { r0, r1 = r1, r0 }
		if r1.n > r2.n { r1, r2 = r2, r1 }
		if r0.n > r1.n { r0, r1 = r1, r0 }

		if r0.lo < r0.hi {
			sortImpl(a, r0.lo, r0.hi, depth-1)
		}
		if r1.lo < r1.hi {
			sortImpl(a, r1.lo, r1.hi, depth-1)
		}

		lo, hi = r2.lo, r2.hi
		depth--
	}
}

func insertionSort(a []int, lo, hi int) {
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

func ninther(a []int, lo, hi, idx int) int {
	i0 := imax(lo, idx-1)
	i2 := imin(hi, idx+1)
	x, y, z := a[i0], a[idx], a[i2]
	if x > y { x, y = y, x }
	if y > z { y, z = z, y }
	if x > y { x, y = y, x }
	_ = z
	return y
}

func dualPartition(a []int, lo, hi, p1, p2 int) (int, int) {
	if p1 > p2 {
		p1, p2 = p2, p1
	}
	lt, gt, i := lo, hi, lo
	for i <= gt {
		v := a[i]
		if v < p1 {
			a[lt], a[i] = a[i], a[lt]
			lt++
			i++
		} else if v > p2 {
			a[i], a[gt] = a[gt], a[i]
			gt--
		} else {
			i++
		}
	}
	return lt, gt
}

func ilog2(n int) int { return int(math.Log2(float64(n))) }
func imax(a, b int) int {
	if a > b { return a }
	return b
}
func imin(a, b int) int {
	if a < b { return a }
	return b
}
