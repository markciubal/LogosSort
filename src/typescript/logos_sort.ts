/**
 * LogosSort — Golden-ratio dual-pivot introsort (TypeScript)
 *
 * Two pivots placed at φ (≈61.8%) and 1−φ (≈38.2%) golden-ratio positions
 * of a chaos-seeded index. Ninther pivot refinement, three-way partition,
 * counting-sort fast path for dense integer ranges, O(log n) depth limit.
 */

const PHI  = 0.6180339887498949;
const PHI2 = 0.3819660112501051;
const SMALL_N = 48;

function ninther(a: number[], lo: number, hi: number, idx: number): number {
  const i0 = Math.max(lo, idx - 1);
  const i2 = Math.min(hi, idx + 1);
  let x = a[i0], y = a[idx], z = a[i2];
  if (x > y) { [x, y] = [y, x]; }
  if (y > z) { [y, z] = [z, y]; }
  if (x > y) { [x, y] = [y, x]; }
  return y;
}

function dualPartition(
  a: number[], lo: number, hi: number, p1: number, p2: number
): [number, number] {
  if (p1 > p2) { [p1, p2] = [p2, p1]; }
  let lt = lo, gt = hi, i = lo;
  while (i <= gt) {
    const v = a[i];
    if (v < p1) {
      [a[lt], a[i]] = [a[i], a[lt]];
      lt++; i++;
    } else if (v > p2) {
      [a[i], a[gt]] = [a[gt], a[i]];
      gt--;
    } else {
      i++;
    }
  }
  return [lt, gt];
}

function sortImpl(a: number[], lo: number, hi: number, depth: number): void {
  while (lo < hi) {
    const size = hi - lo + 1;

    if (depth <= 0 || size <= SMALL_N) {
      const sub = a.slice(lo, hi + 1).sort((x, y) => x - y);
      for (let i = 0; i < sub.length; i++) a[lo + i] = sub[i];
      return;
    }

    // Counting sort for dense integer subarrays
    if (Number.isInteger(a[lo])) {
      let mn = a[lo], mx = a[lo];
      for (let i = lo + 1; i <= hi; i++) {
        if (a[i] < mn) mn = a[i];
        if (a[i] > mx) mx = a[i];
      }
      const span = mx - mn;
      if (span < size * 4) {
        const counts = new Int32Array(span + 1);
        for (let i = lo; i <= hi; i++) counts[a[i] - mn]++;
        let k = lo;
        for (let v = 0; v <= span; v++) {
          for (let c = 0; c < counts[v]; c++) a[k++] = v + mn;
        }
        return;
      }
    }

    // Monotone checks
    if (a[lo] <= a[lo + 1] && a[lo + 1] <= a[lo + 2]) {
      let asc = true;
      for (let i = lo; i < hi; i++) if (a[i] > a[i + 1]) { asc = false; break; }
      if (asc) return;

      let desc = true;
      for (let i = lo; i < hi; i++) if (a[i] < a[i + 1]) { desc = false; break; }
      if (desc) {
        for (let l = lo, r = hi; l < r; l++, r--) [a[l], a[r]] = [a[r], a[l]];
        return;
      }
    }

    // Oracle-seeded golden-ratio pivot positions
    const absC = Math.abs(Math.random() * 2 - 1) || 1e-15;
    const sp   = hi - lo;
    const idx1 = lo + Math.floor(sp * PHI2 * absC);
    const idx2 = lo + Math.floor(sp * PHI  * absC);

    const p1 = ninther(a, lo, hi, idx1);
    const p2 = ninther(a, lo, hi, idx2);

    const [lt, gt] = dualPartition(a, lo, hi, p1, p2);

    const regions: [number, number, number][] = [
      [lt - lo,      lo,    lt - 1],
      [gt - lt + 1,  lt,    gt    ],
      [hi - gt,      gt + 1, hi   ],
    ].sort((a, b) => a[0] - b[0]) as [number, number, number][];

    for (let i = 0; i < 2; i++) {
      const [, rLo, rHi] = regions[i];
      if (rLo < rHi) sortImpl(a, rLo, rHi, depth - 1);
    }

    [, lo, hi] = regions[2];
    depth--;
  }
}

/**
 * Sort an array of numbers in-place using LogosSort.
 * Returns the same array sorted.
 */
export function logosSort(arr: number[]): number[] {
  const n = arr.length;
  if (n < 2) return arr;
  const depthLimit = 2 * Math.floor(Math.log2(n)) + 4;
  sortImpl(arr, 0, n - 1, depthLimit);
  return arr;
}
