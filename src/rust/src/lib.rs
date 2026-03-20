//! LogosSort — Golden-ratio dual-pivot introsort (Rust)
//!
//! Self-contained — zero calls to slice::sort or sort_unstable internally.
//! Insertion sort is used for base cases so the algorithm stands alone.

use rand::Rng;

const PHI:    f64 = 0.6180339887498949;
const PHI2:   f64 = 0.3819660112501051;
const SMALL_N: usize = 48;

/// Sort a slice of `i64` in place using LogosSort.
pub fn logos_sort(arr: &mut [i64]) {
    let n = arr.len();
    if n < 2 { return; }
    let depth = 2 * (usize::BITS - n.leading_zeros()) as i32 + 4;
    sort_impl(arr, 0, n as isize - 1, depth);
}

/// Sort a slice of any `Ord + Clone` type in place (generic version).
pub fn logos_sort_generic<T: Ord + Clone>(arr: &mut [T]) {
    let n = arr.len();
    if n < 2 { return; }
    let depth = 2 * (usize::BITS - n.leading_zeros()) as i32 + 4;
    sort_generic_impl(arr, 0, n as isize - 1, depth);
}

// ─────────────────────────────────────────────────────────────────────────────
// i64-specialised implementation (with counting sort fast path)
// ─────────────────────────────────────────────────────────────────────────────

fn sort_impl(a: &mut [i64], mut lo: isize, mut hi: isize, mut depth: i32) {
    let mut rng = rand::thread_rng();

    while lo < hi {
        let size = (hi - lo + 1) as usize;

        // Base case: pure Rust insertion sort — no .sort() call
        if depth <= 0 || size <= SMALL_N {
            insertion_sort_i64(a, lo as usize, hi as usize);
            return;
        }

        // Counting sort for dense integer subarrays
        let mn = *a[lo as usize..=hi as usize].iter().min().unwrap();
        let mx = *a[lo as usize..=hi as usize].iter().max().unwrap();
        let span = mx.wrapping_sub(mn);
        if span >= 0 && span < (size as i64) * 4 {
            let mut counts = vec![0usize; span as usize + 1];
            for i in lo as usize..=hi as usize {
                counts[(a[i] - mn) as usize] += 1;
            }
            let mut k = lo as usize;
            for (v, &cnt) in counts.iter().enumerate() {
                for _ in 0..cnt {
                    a[k] = v as i64 + mn;
                    k += 1;
                }
            }
            return;
        }

        // Monotone checks
        if a[lo as usize] <= a[lo as usize + 1] && a[lo as usize + 1] <= a[lo as usize + 2] {
            let asc = a[lo as usize..=hi as usize].windows(2).all(|w| w[0] <= w[1]);
            if asc { return; }
            let desc = a[lo as usize..=hi as usize].windows(2).all(|w| w[0] >= w[1]);
            if desc { a[lo as usize..=hi as usize].reverse(); return; }
        }

        // Oracle-seeded golden-ratio pivot positions
        let abs_c: f64 = rng.gen_range(1e-15..=1.0);
        let sp = (hi - lo) as f64;
        let idx1 = lo + (sp * PHI2 * abs_c) as isize;
        let idx2 = lo + (sp * PHI  * abs_c) as isize;

        let p1 = ninther_i64(a, lo, hi, idx1);
        let p2 = ninther_i64(a, lo, hi, idx2);

        let (lt, gt) = dual_partition_i64(a, lo, hi, p1, p2);

        // Sort 3 region descriptors by size — comparison network, no .sort()
        let mut regions = [
            ((lt - lo)     as usize, lo,    lt - 1),
            ((gt - lt + 1) as usize, lt,    gt    ),
            ((hi - gt)     as usize, gt + 1, hi   ),
        ];
        if regions[0].0 > regions[1].0 { regions.swap(0, 1); }
        if regions[1].0 > regions[2].0 { regions.swap(1, 2); }
        if regions[0].0 > regions[1].0 { regions.swap(0, 1); }

        for i in 0..2 {
            let (_, r_lo, r_hi) = regions[i];
            if r_lo < r_hi { sort_impl(a, r_lo, r_hi, depth - 1); }
        }

        (lo, hi) = (regions[2].1, regions[2].2);
        depth -= 1;
    }
}

fn ninther_i64(a: &[i64], lo: isize, hi: isize, idx: isize) -> i64 {
    let i0 = lo.max(idx - 1) as usize;
    let i2 = hi.min(idx + 1) as usize;
    let (mut x, mut y, mut z) = (a[i0], a[idx as usize], a[i2]);
    if x > y { std::mem::swap(&mut x, &mut y); }
    if y > z { std::mem::swap(&mut y, &mut z); }
    if x > y { std::mem::swap(&mut x, &mut y); }
    y
}

fn dual_partition_i64(a: &mut [i64], lo: isize, hi: isize, p1: i64, p2: i64) -> (isize, isize) {
    let (p1, p2) = if p1 > p2 { (p2, p1) } else { (p1, p2) };
    let (mut lt, mut gt, mut i) = (lo, hi, lo);
    while i <= gt {
        let v = a[i as usize];
        if v < p1 {
            a.swap(lt as usize, i as usize); lt += 1; i += 1;
        } else if v > p2 {
            a.swap(i as usize, gt as usize); gt -= 1;
        } else {
            i += 1;
        }
    }
    (lt, gt)
}

fn insertion_sort_i64(a: &mut [i64], lo: usize, hi: usize) {
    for i in lo + 1..=hi {
        let key = a[i];
        let mut j = i;
        while j > lo && a[j - 1] > key { a[j] = a[j - 1]; j -= 1; }
        a[j] = key;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Generic implementation (no counting sort, pure Ord comparison)
// ─────────────────────────────────────────────────────────────────────────────

fn sort_generic_impl<T: Ord + Clone>(a: &mut [T], mut lo: isize, mut hi: isize, mut depth: i32) {
    let mut rng = rand::thread_rng();

    while lo < hi {
        let size = (hi - lo + 1) as usize;

        // Base case: pure insertion sort — no .sort() call
        if depth <= 0 || size <= SMALL_N {
            insertion_sort_generic(a, lo as usize, hi as usize);
            return;
        }

        if a[lo as usize] <= a[lo as usize + 1] && a[lo as usize + 1] <= a[lo as usize + 2] {
            let asc = a[lo as usize..=hi as usize].windows(2).all(|w| w[0] <= w[1]);
            if asc { return; }
            let desc = a[lo as usize..=hi as usize].windows(2).all(|w| w[0] >= w[1]);
            if desc { a[lo as usize..=hi as usize].reverse(); return; }
        }

        let abs_c: f64 = rng.gen_range(1e-15..=1.0);
        let sp = (hi - lo) as f64;
        let idx1 = lo + (sp * PHI2 * abs_c) as isize;
        let idx2 = lo + (sp * PHI  * abs_c) as isize;

        let p1 = ninther_generic(a, lo, hi, idx1);
        let p2 = ninther_generic(a, lo, hi, idx2);

        let (lt, gt) = dual_partition_generic(a, lo, hi, p1, p2);

        // Sort 3 region descriptors — comparison network, no .sort()
        let mut regions = [
            ((lt - lo)     as usize, lo,    lt - 1),
            ((gt - lt + 1) as usize, lt,    gt    ),
            ((hi - gt)     as usize, gt + 1, hi   ),
        ];
        if regions[0].0 > regions[1].0 { regions.swap(0, 1); }
        if regions[1].0 > regions[2].0 { regions.swap(1, 2); }
        if regions[0].0 > regions[1].0 { regions.swap(0, 1); }

        for i in 0..2 {
            let (_, r_lo, r_hi) = regions[i];
            if r_lo < r_hi { sort_generic_impl(a, r_lo, r_hi, depth - 1); }
        }

        (lo, hi) = (regions[2].1, regions[2].2);
        depth -= 1;
    }
}

fn ninther_generic<T: Ord + Clone>(a: &[T], lo: isize, hi: isize, idx: isize) -> T {
    let i0 = lo.max(idx - 1) as usize;
    let i2 = hi.min(idx + 1) as usize;
    let mut vals = [a[i0].clone(), a[idx as usize].clone(), a[i2].clone()];
    // 3-element comparison network — no .sort()
    if vals[0] > vals[1] { vals.swap(0, 1); }
    if vals[1] > vals[2] { vals.swap(1, 2); }
    if vals[0] > vals[1] { vals.swap(0, 1); }
    vals[1].clone()
}

fn dual_partition_generic<T: Ord + Clone>(
    a: &mut [T], lo: isize, hi: isize, p1: T, p2: T,
) -> (isize, isize) {
    let (p1, p2) = if p1 > p2 { (p2, p1) } else { (p1, p2) };
    let (mut lt, mut gt, mut i) = (lo, hi, lo);
    while i <= gt {
        let v = a[i as usize].clone();
        if v < p1 {
            a.swap(lt as usize, i as usize); lt += 1; i += 1;
        } else if v > p2 {
            a.swap(i as usize, gt as usize); gt -= 1;
        } else {
            i += 1;
        }
    }
    (lt, gt)
}

fn insertion_sort_generic<T: Ord + Clone>(a: &mut [T], lo: usize, hi: usize) {
    for i in lo + 1..=hi {
        let key = a[i].clone();
        let mut j = i;
        while j > lo && a[j - 1] > key { a[j] = a[j - 1].clone(); j -= 1; }
        a[j] = key;
    }
}
