/**
 * Benchmark: LogosSort vs Pure-TS Merge Sort vs Array.prototype.sort
 * Time + Space complexity. Memory via process.memoryUsage() (best-effort).
 *
 * Run: ts-node benchmark.ts
 *      node --expose-gc -r ts-node/register benchmark.ts  (for GC-forced memory)
 */

import { logosSort } from './logos_sort';

const SIZES   = [500_000, 2_500_000, 10_000_000];
const MAX_VAL = 1_000_000_000;
const RUNS    = 3;
declare const gc: (() => void) | undefined;
const hasGC = typeof gc === 'function';

function randomArray(n: number): number[] {
  const a: number[] = new Array(n);
  for (let i = 0; i < n; i++) a[i] = (Math.random() * MAX_VAL) | 0;
  return a;
}

// ── Pure TS bottom-up merge sort (one auxiliary array = O(n) space) ───────────

function insertionSortBlock(a: number[], lo: number, hi: number): void {
  for (let i = lo + 1; i <= hi; i++) {
    const key = a[i]; let j = i - 1;
    while (j >= lo && a[j] > key) { a[j + 1] = a[j]; j--; }
    a[j + 1] = key;
  }
}

function mergeSort(arr: number[]): void {
  const n = arr.length;
  if (n < 2) return;
  const BLOCK = 32;
  for (let lo = 0; lo < n; lo += BLOCK)
    insertionSortBlock(arr, lo, Math.min(lo + BLOCK - 1, n - 1));

  const buf: number[] = new Array(n);   // <-- the single O(n) allocation
  for (let width = BLOCK; width < n; width *= 2) {
    for (let lo = 0; lo < n; lo += 2 * width) {
      const mid = Math.min(lo + width,     n);
      const hi  = Math.min(lo + 2 * width, n);
      if (mid >= hi) { for (let k = lo; k < hi; k++) buf[k] = arr[k]; continue; }
      let i = lo, j = mid, k = lo;
      while (i < mid && j < hi) buf[k++] = arr[i] <= arr[j] ? arr[i++] : arr[j++];
      while (i < mid) buf[k++] = arr[i++];
      while (j < hi)  buf[k++] = arr[j++];
      for (let k2 = lo; k2 < hi; k2++) arr[k2] = buf[k2];
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────

function benchTime(fn: (a: number[]) => void, data: number[]): number {
  let total = 0;
  for (let r = 0; r < RUNS; r++) {
    const arr = data.slice();
    const t0  = performance.now();
    fn(arr);
    total += performance.now() - t0;
  }
  return total / RUNS / 1000;
}

function benchMemory(fn: (a: number[]) => void, data: number[]): number {
  const arr = data.slice();
  if (hasGC) gc!();
  const before = process.memoryUsage().heapUsed;
  fn(arr);
  const after = process.memoryUsage().heapUsed;
  return Math.max(after - before, 0);
}

function fmtBytes(b: number): string {
  if (b >= 1 << 20) return `${(b / (1 << 20)).toFixed(1).padStart(6)} MB`;
  if (b >= 1 << 10) return `${(b / (1 << 10)).toFixed(1).padStart(6)} KB`;
  return `${b.toString().padStart(6)}  B`;
}

console.log('='.repeat(76));
console.log('LogosSort vs Pure-TS Merge Sort -- Time + Space Complexity');
console.log(`Memory via process.memoryUsage() ${hasGC ? '(GC forced)' : '(approx)'}`);
console.log('Array.prototype.sort shown for reference only.');
console.log('='.repeat(76));

for (const n of SIZES) {
  const data = randomArray(n);

  const logosT = benchTime(logosSort, data);
  const mergeT = benchTime(mergeSort, data);
  const stdT   = benchTime(a => a.sort((x, y) => x - y), data);

  const logosM = benchMemory(logosSort, data);
  const mergeM = benchMemory(mergeSort, data);

  const sep = '-'.repeat(76);
  console.log(`\n  ${n.toLocaleString()} items`);
  console.log(`  ${sep}`);
  console.log(`  ${'Algorithm'.padEnd(22)}  ${'Time'.padStart(8)}  ${'Heap Delta'.padStart(10)}  ${'B/item'.padStart(7)}  Space`);
  console.log(`  ${sep}`);
  console.log(`  ${'LogosSort (in-place)'.padEnd(22)}  ${logosT.toFixed(3).padStart(6)}s  ${fmtBytes(logosM).padStart(10)}  ${(logosM/n).toFixed(2).padStart(6)}B  O(log n)`);
  console.log(`  ${'MergeSort (in-place)'.padEnd(22)}  ${mergeT.toFixed(3).padStart(6)}s  ${fmtBytes(mergeM).padStart(10)}  ${(mergeM/n).toFixed(2).padStart(6)}B  O(n)`);
  console.log(`  ${'Array.sort *'.padEnd(22)}  ${stdT.toFixed(3).padStart(6)}s  ${'n/a'.padStart(10)}  ${'n/a'.padStart(7)}  O(n)  (V8 native, ref only)`);
  console.log(`  ${sep}`);
  console.log(`  Time: ${(logosT/mergeT).toFixed(2)}x   Memory: LogosSort uses ${Math.round(mergeM/Math.max(logosM,1))}x less space`);
}
console.log('\n* Array.sort = V8 Timsort. Not a fair peer; shown for scale.');
