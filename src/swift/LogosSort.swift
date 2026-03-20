// LogosSort — Golden-ratio dual-pivot introsort (Swift)
//
// Two pivots placed at φ (≈61.8%) and 1−φ (≈38.2%) golden-ratio positions
// of a chaos-seeded index. Ninther pivot refinement, three-way partition,
// counting-sort fast path for dense Int ranges, O(log n) depth limit.

import Foundation

private let PHI:    Double = 0.6180339887498949
private let PHI2:   Double = 0.3819660112501051
private let SMALL_N: Int   = 48

// MARK: – Public API

/// Sort `arr` in place using LogosSort.
public func logosSort(_ arr: inout [Int]) {
    let n = arr.count
    guard n >= 2 else { return }
    let depth = 2 * Int(log2(Double(n))) + 4
    sortImpl(&arr, lo: 0, hi: n - 1, depth: depth)
}

/// Return a sorted copy of `arr`.
public func logosSorted(_ arr: [Int]) -> [Int] {
    var copy = arr
    logosSort(&copy)
    return copy
}

// MARK: – Internal

private func sortImpl(_ a: inout [Int], lo: Int, hi: Int, depth: Int) {
    var lo = lo, hi = hi, depth = depth
    while lo < hi {
        let size = hi - lo + 1

        if depth <= 0 || size <= SMALL_N {
            insertionSort(&a, lo: lo, hi: hi)
            return
        }

        // Counting sort for dense integer subarrays
        let sub  = a[lo...hi]
        let mn   = sub.min()!
        let mx   = sub.max()!
        let span = mx - mn
        if span < size * 4 {
            var counts = [Int](repeating: 0, count: span + 1)
            for i in lo...hi { counts[a[i] - mn] += 1 }
            var k = lo
            for (v, cnt) in counts.enumerated() {
                guard cnt > 0 else { continue }
                for _ in 0..<cnt { a[k] = v + mn; k += 1 }
            }
            return
        }

        // Monotone checks
        if a[lo] <= a[lo + 1] && a[lo + 1] <= a[lo + 2] {
            var asc = true
            for i in lo..<hi where a[i] > a[i + 1] { asc = false; break }
            if asc { return }

            var desc = true
            for i in lo..<hi where a[i] < a[i + 1] { desc = false; break }
            if desc { a[lo...hi].reverse(); return }
        }

        // Oracle-seeded golden-ratio pivot positions
        let absC = Double.random(in: 1e-15...1.0)
        let sp   = Double(hi - lo)
        let idx1 = lo + Int(sp * PHI2 * absC)
        let idx2 = lo + Int(sp * PHI  * absC)

        let p1 = ninther(&a, lo: lo, hi: hi, idx: idx1)
        let p2 = ninther(&a, lo: lo, hi: hi, idx: idx2)

        let (lt, gt) = dualPartition(&a, lo: lo, hi: hi, p1: p1, p2: p2)

        var regions: [(n: Int, lo: Int, hi: Int)] = [
            (lt - lo,      lo,    lt - 1),
            (gt - lt + 1,  lt,    gt    ),
            (hi - gt,      gt + 1, hi   ),
        ]
        regions.sort { $0.n < $1.n }

        for i in 0..<2 {
            let r = regions[i]
            if r.lo < r.hi { sortImpl(&a, lo: r.lo, hi: r.hi, depth: depth - 1) }
        }

        lo    = regions[2].lo
        hi    = regions[2].hi
        depth -= 1
    }
}

private func ninther(_ a: inout [Int], lo: Int, hi: Int, idx: Int) -> Int {
    let i0 = max(lo, idx - 1)
    let i2 = min(hi, idx + 1)
    var x = a[i0], y = a[idx], z = a[i2]
    if x > y { swap(&x, &y) }
    if y > z { swap(&y, &z) }
    if x > y { swap(&x, &y) }
    return y
}

private func dualPartition(_ a: inout [Int], lo: Int, hi: Int, p1: Int, p2: Int) -> (Int, Int) {
    var p1 = p1, p2 = p2
    if p1 > p2 { swap(&p1, &p2) }
    var lt = lo, gt = hi, i = lo
    while i <= gt {
        let v = a[i]
        if v < p1 {
            a.swapAt(lt, i); lt += 1; i += 1
        } else if v > p2 {
            a.swapAt(i, gt); gt -= 1
        } else {
            i += 1
        }
    }
    return (lt, gt)
}

private func insertionSort(_ a: inout [Int], lo: Int, hi: Int) {
    for i in (lo + 1)...hi {
        let key = a[i]
        var j   = i
        while j > lo && a[j - 1] > key { a[j] = a[j - 1]; j -= 1 }
        a[j] = key
    }
}
