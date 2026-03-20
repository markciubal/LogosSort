//! Benchmark: logos_sort vs Pure-Rust Merge Sort vs slice::sort_unstable
//!
//! Apples-to-apples: logos_sort vs merge_sort — both pure Rust, no stdlib sort calls.
//! sort_unstable (pdqsort) shown for reference scale only.
//!
//! cargo run --release

use logos_sort::logos_sort;
use rand::Rng;
use std::time::Instant;

const RUNS:    usize = 5;
const MAX_VAL: i64   = 1_000_000_000;
const BLOCK:   usize = 32;

fn random_vec(n: usize) -> Vec<i64> {
    let mut rng = rand::thread_rng();
    (0..n).map(|_| rng.gen_range(0..MAX_VAL)).collect()
}

// ── Pure Rust bottom-up merge sort (no slice::sort) ──────────────────────────

fn insertion_sort_block(a: &mut [i64], lo: usize, hi: usize) {
    for i in lo + 1..=hi {
        let key = a[i];
        let mut j = i;
        while j > lo && a[j - 1] > key { a[j] = a[j - 1]; j -= 1; }
        a[j] = key;
    }
}

fn merge_sort(input: &[i64]) -> Vec<i64> {
    let n = input.len();
    if n < 2 { return input.to_vec(); }
    let mut src = input.to_vec();
    let mut dst = src.clone();

    let mut lo = 0;
    while lo < n {
        let hi = (lo + BLOCK - 1).min(n - 1);
        insertion_sort_block(&mut src, lo, hi);
        lo += BLOCK;
    }

    let mut width = BLOCK;
    while width < n {
        let mut lo = 0;
        while lo < n {
            let mid = (lo + width).min(n);
            let hi  = (lo + 2 * width).min(n);
            if mid >= hi {
                dst[lo..hi].copy_from_slice(&src[lo..hi]);
            } else {
                let (mut i, mut j, mut k) = (lo, mid, lo);
                while i < mid && j < hi {
                    if src[i] <= src[j] { dst[k] = src[i]; i += 1; }
                    else                { dst[k] = src[j]; j += 1; }
                    k += 1;
                }
                while i < mid { dst[k] = src[i]; i += 1; k += 1; }
                while j < hi  { dst[k] = src[j]; j += 1; k += 1; }
            }
            lo += 2 * width;
        }
        std::mem::swap(&mut src, &mut dst);
        width *= 2;
    }
    src
}
// ─────────────────────────────────────────────────────────────────────────────

fn bench_logos(data: &[i64]) -> f64 {
    let mut arr = data.to_vec();
    let t0 = Instant::now();
    logos_sort(&mut arr);
    t0.elapsed().as_secs_f64()
}

fn bench_merge(data: &[i64]) -> f64 {
    let t0 = Instant::now();
    merge_sort(data);
    t0.elapsed().as_secs_f64()
}

fn bench_std(data: &[i64]) -> f64 {
    let mut arr = data.to_vec();
    let t0 = Instant::now();
    arr.sort_unstable();
    t0.elapsed().as_secs_f64()
}

fn main() {
    let sizes = [500_000usize, 2_500_000, 10_000_000];

    println!("{}", "=".repeat(72));
    println!("LogosSort vs Pure-Rust Merge Sort  (apples-to-apples)");
    println!("sort_unstable (pdqsort) shown for reference only");
    println!("{}", "=".repeat(72));
    println!("{:>12}  {:>11}  {:>11}  {:>13}  {:>9}",
        "Size", "LogosSort", "MergeSort", "sort_unstable", "L/M ratio");
    println!("{}", "-".repeat(72));

    for &n in &sizes {
        let data = random_vec(n);

        let logos_avg: f64 = (0..RUNS).map(|_| bench_logos(&data)).sum::<f64>() / RUNS as f64;
        let merge_avg: f64 = (0..RUNS).map(|_| bench_merge(&data)).sum::<f64>() / RUNS as f64;
        let std_avg:   f64 = (0..RUNS).map(|_| bench_std(&data)).sum::<f64>()   / RUNS as f64;
        let ratio = logos_avg / merge_avg;

        println!("{:>12}  {:>9.3}s  {:>9.3}s  {:>11.3}s  {:>8.2}x",
            n, logos_avg, merge_avg, std_avg, ratio);
    }
    println!("\nL/M ratio < 1.0 means LogosSort is faster than pure-Rust merge sort.");
}
