/**
 * Benchmark: LogosSort vs Pure-C++ Merge Sort vs std::sort
 * Time + Space complexity at 500 000 · 2 500 000 · 10 000 000 items.
 *
 * Heap allocation is tracked by overriding operator new/delete with atomic
 * counters. The counters are reset before each sort call so only auxiliary
 * allocations inside the algorithm are counted (the input vector is not).
 *
 * Compile:
 *   g++ -O2 -std=c++17 -o bench benchmark.cpp && ./bench
 */

#include "logos_sort.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <random>
#include <vector>

// ── Allocation tracker ────────────────────────────────────────────────────────
// We override global new/delete with atomic counters.
// peak_bytes resets to 0 between measurements via reset_tracker().

namespace tracker {
    std::atomic<size_t> current{0};
    std::atomic<size_t> peak{0};
    std::atomic<bool>   active{false};

    void reset() { current = 0; peak = 0; }
    void start() { reset(); active = true; }
    void stop()  { active = false; }
    size_t get_peak() { return peak.load(); }
}

void* operator new(size_t sz) {
    void* ptr = std::malloc(sz);
    if (!ptr) throw std::bad_alloc{};
    if (tracker::active.load()) {
        size_t cur = tracker::current.fetch_add(sz) + sz;
        size_t pk  = tracker::peak.load();
        while (cur > pk && !tracker::peak.compare_exchange_weak(pk, cur));
    }
    return ptr;
}
void operator delete(void* ptr, size_t sz) noexcept {
    if (tracker::active.load()) tracker::current.fetch_sub(sz);
    std::free(ptr);
}
void operator delete(void* ptr) noexcept { std::free(ptr); }
// ─────────────────────────────────────────────────────────────────────────────

static constexpr int RUNS    = 5;
static constexpr int MAX_VAL = 1'000'000'000;
static constexpr int BLOCK   = 32;
using Clock = std::chrono::high_resolution_clock;

// ── Pure C++ bottom-up merge sort (one std::vector<int> buffer = O(n)) ───────

static void insertion_sort_block(int* a, int lo, int hi) {
    for (int i = lo + 1; i <= hi; i++) {
        int key = a[i], j = i - 1;
        while (j >= lo && a[j] > key) { a[j + 1] = a[j]; j--; }
        a[j + 1] = key;
    }
}

static void merge_sort(std::vector<int>& arr) {
    int n = static_cast<int>(arr.size());
    if (n < 2) return;
    for (int lo = 0; lo < n; lo += BLOCK)
        insertion_sort_block(arr.data(), lo, std::min(lo + BLOCK - 1, n - 1));

    std::vector<int> buf(n);   // <-- the single O(n) allocation
    for (int width = BLOCK; width < n; width *= 2) {
        for (int lo = 0; lo < n; lo += 2 * width) {
            int mid = std::min(lo + width,     n);
            int hi  = std::min(lo + 2 * width, n);
            if (mid >= hi) {
                std::copy(arr.begin() + lo, arr.begin() + hi, buf.begin() + lo);
                continue;
            }
            int i = lo, j = mid, k = lo;
            while (i < mid && j < hi)
                buf[k++] = arr[i] <= arr[j] ? arr[i++] : arr[j++];
            while (i < mid) buf[k++] = arr[i++];
            while (j < hi)  buf[k++] = arr[j++];
            std::copy(buf.begin() + lo, buf.begin() + hi, arr.begin() + lo);
        }
    }
}
// ─────────────────────────────────────────────────────────────────────────────

std::string fmt_bytes(size_t b) {
    char buf[32];
    if (b >= 1 << 20) std::snprintf(buf, sizeof(buf), "%6.1f MB", b / double(1 << 20));
    else if (b >= 1 << 10) std::snprintf(buf, sizeof(buf), "%6.1f KB", b / double(1 << 10));
    else std::snprintf(buf, sizeof(buf), "%6zu  B", b);
    return buf;
}

int main() {
    std::mt19937 rng{42};
    std::uniform_int_distribution<int> dist{0, MAX_VAL};
    std::vector<int> sizes = {500'000, 2'500'000, 10'000'000};

    std::cout << std::string(76, '=') << '\n';
    std::cout << "LogosSort vs Pure-C++ Merge Sort -- Time + Space Complexity\n";
    std::cout << "Heap tracked via operator new/delete override (aux bytes only).\n";
    std::cout << "std::sort shown for reference only.\n";
    std::cout << std::string(76, '=') << '\n';

    for (int n : sizes) {
        std::vector<int> data(n);
        std::generate(data.begin(), data.end(), [&]{ return dist(rng); });

        // ---- time (tracker off) ----
        double logos_t = 0, merge_t = 0, std_t = 0;
        for (int r = 0; r < RUNS; r++) {
            std::vector<int> a;

            a = data;
            auto t0 = Clock::now(); logos::sort(a.begin(), a.end());
            logos_t += std::chrono::duration<double>(Clock::now() - t0).count();

            a = data;
            t0 = Clock::now(); merge_sort(a);
            merge_t += std::chrono::duration<double>(Clock::now() - t0).count();

            a = data;
            t0 = Clock::now(); std::sort(a.begin(), a.end());
            std_t += std::chrono::duration<double>(Clock::now() - t0).count();
        }
        logos_t /= RUNS; merge_t /= RUNS; std_t /= RUNS;

        // ---- memory (one tracked pass each) ----
        size_t logos_m = 0, merge_m = 0;
        {
            std::vector<int> a = data;
            tracker::start(); logos::sort(a.begin(), a.end()); tracker::stop();
            logos_m = tracker::get_peak();
        }
        {
            std::vector<int> a = data;
            tracker::start(); merge_sort(a); tracker::stop();
            merge_m = tracker::get_peak();
        }

        double bpi_logos = static_cast<double>(logos_m) / n;
        double bpi_merge = static_cast<double>(merge_m) / n;

        std::cout << "\n  " << n << " items\n";
        std::cout << "  " << std::string(74, '-') << '\n';
        std::cout << std::setw(24) << std::left << "  Algorithm"
                  << std::setw(9)  << std::right << "Time"
                  << std::setw(11) << "Peak Heap"
                  << std::setw(8)  << "B/item"
                  << "  Space\n";
        std::cout << "  " << std::string(74, '-') << '\n';

        std::cout << std::fixed << std::setprecision(3);
        std::cout << "  " << std::setw(22) << std::left << "LogosSort (in-place)"
                  << std::setw(7)  << std::right << logos_t << "s"
                  << std::setw(11) << fmt_bytes(logos_m)
                  << std::setw(7)  << std::setprecision(2) << bpi_logos << "B"
                  << "  O(log n)\n";
        std::cout << "  " << std::setw(22) << std::left << "MergeSort (in-place)"
                  << std::setw(7)  << std::right << std::setprecision(3) << merge_t << "s"
                  << std::setw(11) << fmt_bytes(merge_m)
                  << std::setw(7)  << std::setprecision(2) << bpi_merge << "B"
                  << "  O(n)\n";
        std::cout << "  " << std::setw(22) << std::left << "std::sort *"
                  << std::setw(7)  << std::right << std::setprecision(3) << std_t << "s"
                  << std::setw(11) << "n/a"
                  << std::setw(8)  << "n/a"
                  << "  O(log n)  (stdlib, ref only)\n";
        std::cout << "  " << std::string(74, '-') << '\n';
        std::cout << "  Time: " << std::setprecision(2) << logos_t / merge_t
                  << "x   Memory: LogosSort uses "
                  << static_cast<long>(merge_m / std::max(logos_m, size_t{1}))
                  << "x less space\n";
    }
    std::cout << "\n* std::sort = introsort. Not a fair peer; shown for scale.\n";
    return 0;
}
