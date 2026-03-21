//! Benchmark: logos_sort vs Pure-Rust Merge Sort vs slice::sort_unstable
//! Time + Space complexity. Heap tracked with a global counting allocator.
//!
//! cargo run --release

use logos_sort::logos_sort;
use rand::Rng;
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering::Relaxed};
use std::time::Instant;

// ── Counting allocator ────────────────────────────────────────────────────────
struct CountingAllocator;

static TRACKING: AtomicBool  = AtomicBool::new(false);
static CURRENT:  AtomicUsize = AtomicUsize::new(0);
static PEAK:     AtomicUsize = AtomicUsize::new(0);

unsafe impl GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let ptr = System.alloc(layout);
        if TRACKING.load(Relaxed) && !ptr.is_null() {
            let cur = CURRENT.fetch_add(layout.size(), Relaxed) + layout.size();
            let mut pk = PEAK.load(Relaxed);
            while cur > pk {
                match PEAK.compare_exchange_weak(pk, cur, Relaxed, Relaxed) {
                    Ok(_) => break,
                    Err(p) => pk = p,
                }
            }
        }
        ptr
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        if TRACKING.load(Relaxed) { CURRENT.fetch_sub(layout.size(), Relaxed); }
        System.dealloc(ptr, layout);
    }
}

#[global_allocator]
static ALLOC: CountingAllocator = CountingAllocator;

fn tracker_start() { CURRENT.store(0, Relaxed); PEAK.store(0, Relaxed); TRACKING.store(true, Relaxed); }
fn tracker_stop()  { TRACKING.store(false, Relaxed); }
fn tracker_peak()  -> usize { PEAK.load(Relaxed) }
// ─────────────────────────────────────────────────────────────────────────────

const RUNS:    usize = 5;
const MAX_VAL: i64   = 1_000_000_000;
const BLOCK:   usize = 32;

fn random_vec(n: usize) -> Vec<i64> {
    let mut rng = rand::thread_rng();
    (0..n).map(|_| rng.gen_range(0..MAX_VAL)).collect()
}

// ── Pure Rust bottom-up merge sort (one Vec<i64> buffer = O(n) space) ─────────

fn insertion_sort_block(a: &mut [i64], lo: usize, hi: usize) {
    for i in lo + 1..=hi {
        let key = a[i]; let mut j = i;
        while j > lo && a[j - 1] > key { a[j] = a[j - 1]; j -= 1; }
        a[j] = key;
    }
}

fn merge_sort(arr: &mut [i64]) {
    let n = arr.len();
    if n < 2 { return; }
    let mut lo = 0;
    while lo < n {
        let hi = (lo + BLOCK - 1).min(n - 1);
        insertion_sort_block(arr, lo, hi);
        lo += BLOCK;
    }

    let mut buf: Vec<i64> = vec![0; n];   // <-- the single O(n) allocation
    let mut width = BLOCK;
    while width < n {
        let mut lo = 0;
        while lo < n {
            let mid = (lo + width).min(n);
            let hi  = (lo + 2 * width).min(n);
            if mid >= hi {
                buf[lo..hi].copy_from_slice(&arr[lo..hi]);
            } else {
                let (mut i, mut j, mut k) = (lo, mid, lo);
                while i < mid && j < hi {
                    if arr[i] <= arr[j] { buf[k] = arr[i]; i += 1; }
                    else                { buf[k] = arr[j]; j += 1; }
                    k += 1;
                }
                while i < mid { buf[k] = arr[i]; i += 1; k += 1; }
                while j < hi  { buf[k] = arr[j]; j += 1; k += 1; }
                arr[lo..hi].copy_from_slice(&buf[lo..hi]);
            }
            lo += 2 * width;
        }
        width *= 2;
    }
}
// ─────────────────────────────────────────────────────────────────────────────

fn bench_time<F: Fn(&mut Vec<i64>)>(f: F, data: &[i64]) -> f64 {
    (0..RUNS).map(|_| {
        let mut a = data.to_vec();
        let t0 = Instant::now(); f(&mut a); t0.elapsed().as_secs_f64()
    }).sum::<f64>() / RUNS as f64
}

fn bench_mem<F: Fn(&mut Vec<i64>)>(f: F, data: &[i64]) -> usize {
    let mut a = data.to_vec();   // pre-allocate input outside tracker
    tracker_start(); f(&mut a); tracker_stop();
    tracker_peak()
}

fn fmt_bytes(b: usize) -> String {
    if b >= 1 << 20 { format!("{:6.1} MB", b as f64 / (1u64 << 20) as f64) }
    else if b >= 1 << 10 { format!("{:6.1} KB", b as f64 / (1u64 << 10) as f64) }
    else { format!("{:6}  B", b) }
}

fn main() {
    let sizes = [500_000usize, 2_500_000, 10_000_000];

    println!("{}", "=".repeat(76));
    println!("LogosSort vs Pure-Rust Merge Sort -- Time + Space Complexity");
    println!("Heap tracked with a custom GlobalAlloc counting allocator.");
    println!("sort_unstable shown for reference only.");
    println!("{}", "=".repeat(76));

    for &n in &sizes {
        let data = random_vec(n);

        let logos_t = bench_time(|a| logos_sort(a),        &data);
        let merge_t = bench_time(|a| merge_sort(a),        &data);
        let std_t   = bench_time(|a| a.sort_unstable(),    &data);

        let logos_m = bench_mem(|a| logos_sort(a),     &data);
        let merge_m = bench_mem(|a| merge_sort(a),     &data);

        println!("\n  {} items", n);
        println!("  {}", "-".repeat(74));
        println!("  {:<22}  {:>7}  {:>10}  {:>7}  Space", "Algorithm", "Time", "Peak Heap", "B/item");
        println!("  {}", "-".repeat(74));
        println!("  {:<22}  {:>5.3}s  {:>10}  {:>6.2}B  O(log n)",
            "LogosSort (in-place)", logos_t, fmt_bytes(logos_m), logos_m as f64 / n as f64);
        println!("  {:<22}  {:>5.3}s  {:>10}  {:>6.2}B  O(n)",
            "MergeSort (in-place)", merge_t, fmt_bytes(merge_m), merge_m as f64 / n as f64);
        println!("  {:<22}  {:>5.3}s  {:>10}  {:>7}  O(log n)  (pdqsort, ref only)",
            "sort_unstable *", std_t, "n/a", "n/a");
        println!("  {}", "-".repeat(74));
        println!("  Time: {:.2}x   Memory: LogosSort uses {:.0}x less space",
            logos_t / merge_t, merge_m as f64 / logos_m.max(1) as f64);
    }
    println!("\n* sort_unstable = pdqsort. Not a fair peer; shown for scale.");
}
