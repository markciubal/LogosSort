//! Benchmark: logos_sort vs slice::sort_unstable — Rust
//!
//! cargo run --release

use logos_sort::logos_sort;
use rand::Rng;
use std::time::Instant;

const RUNS:    usize = 5;
const MAX_VAL: i64   = 1_000_000_000;

fn random_vec(n: usize) -> Vec<i64> {
    let mut rng = rand::thread_rng();
    (0..n).map(|_| rng.gen_range(0..MAX_VAL)).collect()
}

fn bench_logos(data: &[i64]) -> f64 {
    let mut arr = data.to_vec();
    let t0 = Instant::now();
    logos_sort(&mut arr);
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

    println!("LogosSort vs slice::sort_unstable (pdqsort) — Rust benchmark");
    println!("{}", "=".repeat(64));
    println!("{:>12}  {:>13}  {:>13}  {:>8}", "Size", "LogosSort", "sort_unstable", "Ratio");
    println!("{}", "-".repeat(64));

    for &n in &sizes {
        let data = random_vec(n);

        let logos_avg: f64 = (0..RUNS).map(|_| bench_logos(&data)).sum::<f64>() / RUNS as f64;
        let std_avg:   f64 = (0..RUNS).map(|_| bench_std(&data)).sum::<f64>()   / RUNS as f64;
        let ratio = logos_avg / std_avg;

        println!("{:>12}  {:>11.3}s  {:>11.3}s  {:>7.2}x",
            n, logos_avg, std_avg, ratio);
    }
}
