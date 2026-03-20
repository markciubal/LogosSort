/**
 * Benchmark: LogosSort vs Pure-TS Merge Sort vs Array.prototype.sort (V8)
 *
 * Apples-to-apples: LogosSort vs mergeSort — both pure TypeScript, no native calls.
 */

import { logosSort } from './logos_sort';

const SIZES   = [500_000, 2_500_000, 10_000_000];
const MAX_VAL = 1_000_000_000;
const RUNS    = 3;

function randomArray(n: number): number[] {
  const a: number[] = new Array(n);
  for (let i = 0; i < n; i++) a[i] = (Math.random() * MAX_VAL) | 0;
  return a;
}

function insertionSortBlock(a: number[], lo: number, hi: number): void {
  for (let i = lo + 1; i <= hi; i++) {
    const key = a[i]; let j = i - 1;
    while (j >= lo && a[j] > key) { a[j + 1] = a[j]; j--; }
    a[j + 1] = key;
  }
}

function mergeSort(arr: number[]): number[] {
  const n = arr.length;
  if (n < 2) return arr.slice();
  let src = arr.slice();
  let dst = src.slice();
  const BLOCK = 32;

  for (let lo = 0; lo < n; lo += BLOCK)
    insertionSortBlock(src, lo, Math.min(lo + BLOCK - 1, n - 1));

  for (let width = BLOCK; width < n; width *= 2) {
    for (let lo = 0; lo < n; lo += 2 * width) {
      const mid = Math.min(lo + width,     n);
      const hi  = Math.min(lo + 2 * width, n);
      if (mid >= hi) { for (let k = lo; k < hi; k++) dst[k] = src[k]; continue; }
      let i = lo, j = mid, k = lo;
      while (i < mid && j < hi) dst[k++] = src[i] <= src[j] ? src[i++] : src[j++];
      while (i < mid) dst[k++] = src[i++];
      while (j < hi)  dst[k++] = src[j++];
    }
    [src, dst] = [dst, src];
  }
  return src;
}

function bench(fn: (a: number[]) => void, data: number[]): number {
  const arr = data.slice();
  const t0  = performance.now();
  fn(arr);
  return (performance.now() - t0) / 1000;
}

function timsortV8(arr: number[]): void { arr.sort((a, b) => a - b); }

console.log('='.repeat(72));
console.log('LogosSort vs Pure-TS Merge Sort  (apples-to-apples)');
console.log('Array.prototype.sort (V8) shown for reference only');
console.log('='.repeat(72));
console.log(
  `${'Size'.padStart(12)}  ${'LogosSort'.padStart(11)}  ${'MergeSort'.padStart(11)}` +
  `  ${'V8 sort'.padStart(11)}  ${'L/M ratio'.padStart(9)}`
);
console.log('-'.repeat(72));

for (const n of SIZES) {
  const data = randomArray(n);
  let logosTot = 0, mergeTot = 0, timTot = 0;
  for (let r = 0; r < RUNS; r++) {
    logosTot += bench(logosSort,  data);
    mergeTot += bench(mergeSort,  data);
    timTot   += bench(timsortV8,  data);
  }
  const la = logosTot / RUNS, ma = mergeTot / RUNS, ta = timTot / RUNS;
  console.log(
    `${n.toLocaleString().padStart(12)}  ${la.toFixed(3).padStart(9)}s` +
    `  ${ma.toFixed(3).padStart(9)}s  ${ta.toFixed(3).padStart(9)}s` +
    `  ${(la / ma).toFixed(2).padStart(8)}x`
  );
}
