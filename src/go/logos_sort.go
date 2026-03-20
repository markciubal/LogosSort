// Package logossort implements LogosSort — a golden-ratio dual-pivot introsort.
//
// Two pivots placed at φ (≈61.8%) and 1−φ (≈38.2%) golden-ratio positions
// of a chaos-seeded index. Ninther pivot refinement, three-way partition,
// counting-sort fast path for dense int ranges, O(log n) depth limit.
package logossort

import (
	"math"
	"math/rand"
	"sort"
)

const (
	phi   = 0.6180339887498949
	phi2  = 0.3819660112501051
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

		if depth <= 0 || size <= smallN {
			sort.Ints(a[lo : hi+1])
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

		type region struct{ n, lo, hi int }
		regions := [3]region{
			{lt - lo, lo, lt - 1},
			{gt - lt + 1, lt, gt},
			{hi - gt, gt + 1, hi},
		}
		// Sort 3 regions by size (3-element network)
		if regions[0].n > regions[1].n {
			regions[0], regions[1] = regions[1], regions[0]
		}
		if regions[1].n > regions[2].n {
			regions[1], regions[2] = regions[2], regions[1]
		}
		if regions[0].n > regions[1].n {
			regions[0], regions[1] = regions[1], regions[0]
		}

		for i := 0; i < 2; i++ {
			r := regions[i]
			if r.lo < r.hi {
				sortImpl(a, r.lo, r.hi, depth-1)
			}
		}

		lo, hi = regions[2].lo, regions[2].hi
		depth--
	}
}

func ninther(a []int, lo, hi, idx int) int {
	i0 := max(lo, idx-1)
	i2 := min(hi, idx+1)
	x, y, z := a[i0], a[idx], a[i2]
	if x > y {
		x, y = y, x
	}
	if y > z {
		y, z = z, y
	}
	if x > y {
		x, y = y, x
	}
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

func ilog2(n int) int {
	return int(math.Log2(float64(n)))
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
