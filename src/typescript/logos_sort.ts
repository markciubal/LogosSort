/**
 * LogosSort — Golden-ratio dual-pivot introsort (TypeScript)
 *
 * Pure TypeScript — zero calls to Array.prototype.sort internally.
 * Insertion sort is used for base cases so the algorithm stands alone.
 */

const PHI  = 0.6180339887498949;
const PHI2 = 0.3819660112501051;
const SMALL_N = 48;

function insertionSort(a: number[], lo: number, hi: number): void {
  for (let i = lo + 1; i <= hi; i++) {
    const key = a[i];
    let j = i - 1;
    while (j >= lo && a[j] > key) { a[j + 1] = a[j]; j--; }
    a[j + 1] = key;
  }
}

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
      [a[lt], a[i]] = [a[i], a[lt]]; lt++; i++;
    } else if (v > p2) {
      [a[i], a[gt]] = [a[gt], a[i]]; gt--;
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
      insertionSort(a, lo, hi);
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

    // Sort 3 region descriptors by size — comparison network, no Array.sort
    let r0: [number, number, number] = [lt - lo,      lo,    lt - 1];
    let r1: [number, number, number] = [gt - lt + 1,  lt,    gt    ];
    let r2: [number, number, number] = [hi - gt,      gt + 1, hi   ];
    if (r0[0] > r1[0]) { [r0, r1] = [r1, r0]; }
    if (r1[0] > r2[0]) { [r1, r2] = [r2, r1]; }
    if (r0[0] > r1[0]) { [r0, r1] = [r1, r0]; }

    if (r0[1] < r0[2]) sortImpl(a, r0[1], r0[2], depth - 1);
    if (r1[1] < r1[2]) sortImpl(a, r1[1], r1[2], depth - 1);

    lo = r2[1]; hi = r2[2]; depth--;
  }
}

/**
 * Sort an array of numbers in-place using LogosSort.
 * No internal calls to Array.prototype.sort.
 */
export function logosSort(arr: number[]): number[] {
  const n = arr.length;
  if (n < 2) return arr;
  const depthLimit = 2 * Math.floor(Math.log2(n)) + 4;
  sortImpl(arr, 0, n - 1, depthLimit);
  return arr;
}
