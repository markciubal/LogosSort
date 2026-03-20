/**
 * Benchmark: LogosSort vs Array.prototype.sort (V8 Timsort) — TypeScript
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

function bench(fn: (a: number[]) => void, data: number[]): number {
  const arr = data.slice();
  const t0  = performance.now();
  fn(arr);
  return (performance.now() - t0) / 1000;
}

function timsort(arr: number[]): void { arr.sort((a, b) => a - b); }

console.log('LogosSort vs Timsort (V8) — TypeScript benchmark');
console.log('='.repeat(60));
console.log(`${'Size'.padStart(12)}  ${'LogosSort'.padStart(11)}  ${'Timsort'.padStart(11)}  ${'Ratio'.padStart(7)}`);
console.log('-'.repeat(60));

for (const n of SIZES) {
  const data = randomArray(n);

  let logosTot = 0, timTot = 0;
  for (let r = 0; r < RUNS; r++) {
    logosTot += bench(logosSort, data);
    timTot   += bench(timsort,   data);
  }

  const logosAvg = logosTot / RUNS;
  const timAvg   = timTot   / RUNS;
  const ratio    = logosAvg / timAvg;

  console.log(
    `${n.toLocaleString().padStart(12)}  ${logosAvg.toFixed(3).padStart(9)}s` +
    `  ${timAvg.toFixed(3).padStart(9)}s  ${ratio.toFixed(2).padStart(6)}x`
  );
}
