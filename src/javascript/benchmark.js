/**
 * Benchmark: LogosSort vs Array.prototype.sort (V8 Timsort)
 * Sizes: 500 000 · 2 500 000 · 10 000 000
 */

const { logosSort } = require('./logos_sort');

const SIZES   = [500_000, 2_500_000, 10_000_000];
const MAX_VAL = 1_000_000_000;
const RUNS    = 3;

function randomArray(n) {
  const a = new Int32Array(n);
  for (let i = 0; i < n; i++) a[i] = (Math.random() * MAX_VAL) | 0;
  return Array.from(a);
}

function bench(fn, data) {
  const arr = data.slice();
  const t0  = performance.now();
  fn(arr);
  return (performance.now() - t0) / 1000;
}

function timsort(arr) { arr.sort((a, b) => a - b); }

console.log('LogosSort vs Timsort (V8) — JavaScript benchmark');
console.log('='.repeat(60));
console.log(`${'Size'.padStart(12)}  ${'LogosSort'.padStart(11)}  ${'Timsort'.padStart(11)}  ${'Ratio'.padStart(7)}`);
console.log('-'.repeat(60));

for (const n of SIZES) {
  process.stdout.write(`  Generating ${n.toLocaleString()} ints...\r`);
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
