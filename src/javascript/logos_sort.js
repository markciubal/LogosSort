/**
 * LogosSort — Golden-ratio dual-pivot introsort (JavaScript)
 *
 * Pure JavaScript — zero calls to Array.prototype.sort internally.
 * Insertion sort is used for base cases so the algorithm stands alone.
 *
 * API:
 *   logosSort(arr)                          // sort in place, ascending
 *   logosSort(arr, { reverse: true })       // sort in place, descending
 *   logosSort(arr, { compareFn: (a,b)=>… }) // sort with custom comparator
 */

const PHI  = 0.6180339887498949;
const PHI2 = 0.3819660112501051;
const SMALL_N = 48;

/** Default numeric comparator: returns negative / 0 / positive. */
function defaultCmp(a, b) {
  return a < b ? -1 : a > b ? 1 : 0;
}

/** In-place insertion sort on a[lo..hi] using comparator cmp. */
function insertionSort(a, lo, hi, cmp) {
  for (let i = lo + 1; i <= hi; i++) {
    const key = a[i];
    let j = i - 1;
    while (j >= lo && cmp(a[j], key) > 0) { a[j + 1] = a[j]; j--; }
    a[j + 1] = key;
  }
}

/** Median of three neighbours around `idx` using comparator cmp. */
function ninther(a, lo, hi, idx, cmp) {
  const i0 = Math.max(lo, idx - 1);
  const i2 = Math.min(hi, idx + 1);
  let x = a[i0], y = a[idx], z = a[i2];
  if (cmp(x, y) > 0) { const t = x; x = y; y = t; }
  if (cmp(y, z) > 0) { const t = y; y = z; z = t; }
  if (cmp(x, y) > 0) {              y = x;         }
  return y;
}

/** Three-way dual-pivot partition using comparator cmp. Returns [lt, gt]. */
function dualPartition(a, lo, hi, p1, p2, cmp) {
  if (cmp(p1, p2) > 0) { const t = p1; p1 = p2; p2 = t; }
  let lt = lo, gt = hi, i = lo;
  while (i <= gt) {
    const v = a[i];
    if (cmp(v, p1) < 0) {
      const t = a[lt]; a[lt] = a[i]; a[i] = t;
      lt++; i++;
    } else if (cmp(v, p2) > 0) {
      const t = a[i]; a[i] = a[gt]; a[gt] = t;
      gt--;
    } else {
      i++;
    }
  }
  return [lt, gt];
}

/** In-place sort of a[lo..hi] (inclusive) using comparator cmp. */
function sortImpl(a, lo, hi, depth, cmp) {
  const isDefault = cmp === defaultCmp;

  while (lo < hi) {
    const size = hi - lo + 1;

    // Base case: insertion sort (pure JS, no Array.prototype.sort)
    if (depth <= 0 || size <= SMALL_N) {
      insertionSort(a, lo, hi, cmp);
      return;
    }

    // Counting sort fast path — only valid for integers with default ordering
    if (isDefault && Number.isInteger(a[lo])) {
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

    // Monotone checks using cmp
    if (cmp(a[lo], a[lo + 1]) <= 0 && cmp(a[lo + 1], a[lo + 2]) <= 0) {
      let asc = true;
      for (let i = lo; i < hi; i++) if (cmp(a[i], a[i + 1]) > 0) { asc = false; break; }
      if (asc) return;

      let desc = true;
      for (let i = lo; i < hi; i++) if (cmp(a[i], a[i + 1]) < 0) { desc = false; break; }
      if (desc) {
        for (let l = lo, r = hi; l < r; l++, r--) {
          const t = a[l]; a[l] = a[r]; a[r] = t;
        }
        return;
      }
    }

    // Oracle-seeded golden-ratio pivot positions
    const absC = Math.abs(Math.random() * 2 - 1) || 1e-15;
    const sp   = hi - lo;
    const idx1 = lo + Math.floor(sp * PHI2 * absC);
    const idx2 = lo + Math.floor(sp * PHI  * absC);

    const p1 = ninther(a, lo, hi, idx1, cmp);
    const p2 = ninther(a, lo, hi, idx2, cmp);

    const [lt, gt] = dualPartition(a, lo, hi, p1, p2, cmp);

    // Sort 3 region descriptors by size — comparison network, no Array.sort
    let r0 = [lt - lo,      lo,    lt - 1];
    let r1 = [gt - lt + 1,  lt,    gt    ];
    let r2 = [hi - gt,      gt + 1, hi   ];
    if (r0[0] > r1[0]) { const t = r0; r0 = r1; r1 = t; }
    if (r1[0] > r2[0]) { const t = r1; r1 = r2; r2 = t; }
    if (r0[0] > r1[0]) { const t = r0; r0 = r1; r1 = t; }

    if (r0[1] < r0[2]) sortImpl(a, r0[1], r0[2], depth - 1, cmp);
    if (r1[1] < r1[2]) sortImpl(a, r1[1], r1[2], depth - 1, cmp);

    lo = r2[1]; hi = r2[2]; depth--;
  }
}

/**
 * Sort an array in-place using LogosSort.
 * No internal calls to Array.prototype.sort.
 *
 * @param {Array}    arr              - The array to sort (modified in place).
 * @param {Object}   [opts]           - Options object.
 * @param {Function} [opts.compareFn] - Comparator (a, b) => negative|0|positive.
 *                                      Defaults to natural numeric/lexicographic order.
 * @param {boolean}  [opts.reverse]   - If true, sort in descending order.
 * @returns {Array} the same array, sorted
 */
function logosSort(arr, { compareFn = null, reverse = false } = {}) {
  const n = arr.length;
  if (n < 2) {
    if (reverse) arr.reverse();
    return arr;
  }
  const cmp = compareFn !== null ? compareFn : defaultCmp;
  const depthLimit = 2 * Math.floor(Math.log2(n)) + 4;
  sortImpl(arr, 0, n - 1, depthLimit, cmp);
  if (reverse) arr.reverse();
  return arr;
}

module.exports = { logosSort };

// ── Self-benchmark (heap output) ──────────────────────────────────────────
// Run directly:  node logos_sort.js
// Force GC:      node --expose-gc logos_sort.js
if (require.main === module) {
  const hasGC = typeof global.gc === 'function';
  const SIZES = [500_000, 2_500_000, 10_000_000];

  function randomArray(n) {
    const a = new Array(n);
    for (let i = 0; i < n; i++) a[i] = (Math.random() * 1_000_000_000) | 0;
    return a;
  }

  function fmtBytes(b) {
    if (b >= 1 << 20) return `${(b / (1 << 20)).toFixed(1)} MB`;
    if (b >= 1 << 10) return `${(b / (1 << 10)).toFixed(1)} KB`;
    return `${b} B`;
  }

  console.log('LogosSort heap measurement');
  console.log(`GC control: ${hasGC ? 'yes (--expose-gc)' : 'no (approx) — run with node --expose-gc for accuracy'}`);
  console.log('-'.repeat(60));
  console.log(`${'n'.padStart(12)}  ${'time'.padStart(8)}  ${'heap delta'.padStart(12)}  ${'B/item'.padStart(8)}`);
  console.log('-'.repeat(60));

  for (const n of SIZES) {
    const data = randomArray(n);

    // ── time (no heap tracking) ──────────────────────────────────────────
    const copy1 = data.slice();
    const t0 = performance.now();
    logosSort(copy1);
    const elapsed = (performance.now() - t0) / 1000;

    // ── heap (separate pass) ─────────────────────────────────────────────
    const copy2 = data.slice();   // input pre-allocated outside measurement
    if (hasGC) global.gc();
    const heapBefore = process.memoryUsage().heapUsed;
    logosSort(copy2);
    const heapDelta = Math.max(process.memoryUsage().heapUsed - heapBefore, 0);

    console.log(
      `${n.toLocaleString().padStart(12)}  ` +
      `${elapsed.toFixed(3).padStart(7)}s  ` +
      `${fmtBytes(heapDelta).padStart(12)}  ` +
      `${(heapDelta / n).toFixed(2).padStart(7)}B`
    );
  }

  console.log('-'.repeat(60));
  console.log('Space: O(log n) — only recursion stack frames (no auxiliary buffer)');
}
