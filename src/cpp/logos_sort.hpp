/**
 * LogosSort — Golden-ratio dual-pivot introsort (C++)
 *
 * Two pivots placed at φ (≈61.8%) and 1−φ (≈38.2%) golden-ratio positions
 * of a chaos-seeded index. Ninther pivot refinement, three-way partition,
 * counting-sort fast path for dense integer ranges, O(log n) depth limit.
 *
 * Usage:
 *   #include "logos_sort.hpp"
 *   std::vector<int> v = { ... };
 *   logos::sort(v.begin(), v.end());          // range version
 *   logos::sort(v.data(), v.data() + v.size()); // pointer version
 */

#pragma once

#include <algorithm>
#include <cmath>
#include <iterator>
#include <limits>
#include <random>
#include <type_traits>
#include <vector>

namespace logos {

namespace detail {

inline constexpr double PHI  = 0.6180339887498949;
inline constexpr double PHI2 = 0.3819660112501051;
inline constexpr int    SMALL_N = 48;

// Thread-local RNG so logos::sort is thread-safe without locking.
inline thread_local std::mt19937_64 rng{std::random_device{}()};
inline thread_local std::uniform_real_distribution<double> dist{0.0, 1.0};

template <typename T>
inline T ninther(T* a, int lo, int hi, int idx) noexcept {
    int i0 = std::max(lo, idx - 1);
    int i2 = std::min(hi, idx + 1);
    T x = a[i0], y = a[idx], z = a[i2];
    if (x > y) std::swap(x, y);
    if (y > z) std::swap(y, z);
    if (x > y) std::swap(x, y);
    return y;
}

template <typename T>
inline std::pair<int, int>
dual_partition(T* a, int lo, int hi, T p1, T p2) noexcept {
    if (p1 > p2) std::swap(p1, p2);
    int lt = lo, gt = hi, i = lo;
    while (i <= gt) {
        if (a[i] < p1) {
            std::swap(a[lt++], a[i++]);
        } else if (a[i] > p2) {
            std::swap(a[i], a[gt--]);
        } else {
            ++i;
        }
    }
    return {lt, gt};
}

template <typename T>
void sort_impl(T* a, int lo, int hi, int depth) {
    while (lo < hi) {
        int size = hi - lo + 1;

        if (depth <= 0 || size <= SMALL_N) {
            std::sort(a + lo, a + hi + 1);
            return;
        }

        // Counting sort for dense integral subarrays
        if constexpr (std::is_integral_v<T>) {
            T mn = a[lo], mx = a[lo];
            for (int i = lo + 1; i <= hi; i++) {
                if (a[i] < mn) mn = a[i];
                if (a[i] > mx) mx = a[i];
            }
            long long span = static_cast<long long>(mx) - mn;
            if (span >= 0 && span < static_cast<long long>(size) * 4) {
                std::vector<int> counts(static_cast<size_t>(span + 1), 0);
                for (int i = lo; i <= hi; i++) counts[a[i] - mn]++;
                int k = lo;
                for (long long v = 0; v <= span; v++)
                    for (int c = 0; c < counts[v]; c++)
                        a[k++] = static_cast<T>(v + mn);
                return;
            }
        }

        // Monotone checks
        if (a[lo] <= a[lo + 1] && a[lo + 1] <= a[lo + 2]) {
            bool asc = true;
            for (int i = lo; i < hi && asc; i++) asc = (a[i] <= a[i + 1]);
            if (asc) return;

            bool desc = true;
            for (int i = lo; i < hi && desc; i++) desc = (a[i] >= a[i + 1]);
            if (desc) { std::reverse(a + lo, a + hi + 1); return; }
        }

        // Oracle-seeded golden-ratio pivot positions
        double abs_c = dist(rng);
        if (abs_c == 0.0) abs_c = 1e-15;
        int sp   = hi - lo;
        int idx1 = lo + static_cast<int>(sp * PHI2 * abs_c);
        int idx2 = lo + static_cast<int>(sp * PHI  * abs_c);

        T p1 = ninther(a, lo, hi, idx1);
        T p2 = ninther(a, lo, hi, idx2);

        auto [lt, gt] = dual_partition(a, lo, hi, p1, p2);

        struct Region { int n, lo, hi; };
        Region regions[3] = {
            {lt - lo,      lo,    lt - 1},
            {gt - lt + 1,  lt,    gt    },
            {hi - gt,      gt + 1, hi   },
        };
        // Sort regions by size ascending (simple 3-element bubble sort)
        if (regions[0].n > regions[1].n) std::swap(regions[0], regions[1]);
        if (regions[1].n > regions[2].n) std::swap(regions[1], regions[2]);
        if (regions[0].n > regions[1].n) std::swap(regions[0], regions[1]);

        for (int i = 0; i < 2; i++)
            if (regions[i].lo < regions[i].hi)
                sort_impl(a, regions[i].lo, regions[i].hi, depth - 1);

        lo = regions[2].lo; hi = regions[2].hi; depth--;
    }
}

} // namespace detail

// ─────────────────────────────────────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────────────────────────────────────

/** Sort elements in [first, last). Requires random-access iterators. */
template <typename RandomIt>
void sort(RandomIt first, RandomIt last) {
    auto n = static_cast<int>(last - first);
    if (n < 2) return;
    int depth = 2 * static_cast<int>(std::log2(n)) + 4;
    detail::sort_impl(&*first, 0, n - 1, depth);
}

/** Sort a raw C array of length n. */
template <typename T>
void sort(T* arr, int n) {
    if (n < 2) return;
    int depth = 2 * static_cast<int>(std::log2(n)) + 4;
    detail::sort_impl(arr, 0, n - 1, depth);
}

} // namespace logos
