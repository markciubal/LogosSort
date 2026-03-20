/**
 * Benchmark: LogosSort vs Pure-C++ Merge Sort vs std::sort
 *
 * Apples-to-apples: logos::sort vs merge_sort — both pure C++, no std::sort calls.
 * std::sort (introsort) shown for reference/scale only.
 *
 * Compile:
 *   g++ -O2 -std=c++17 -o bench benchmark.cpp && ./bench
 */

#include "logos_sort.hpp"
#include <algorithm>
#include <chrono>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>

static constexpr int RUNS    = 5;
static constexpr int MAX_VAL = 1'000'000'000;
static constexpr int BLOCK   = 32;   // insertion-sort block for merge sort

using Clock = std::chrono::high_resolution_clock;

// ── Pure C++ bottom-up merge sort (no std::sort) ─────────────────────────────

static void insertion_sort_block(int* a, int lo, int hi) {
    for (int i = lo + 1; i <= hi; i++) {
        int key = a[i], j = i - 1;
        while (j >= lo && a[j] > key) { a[j + 1] = a[j]; j--; }
        a[j + 1] = key;
    }
}

static std::vector<int> merge_sort(const std::vector<int>& input) {
    int n = static_cast<int>(input.size());
    std::vector<int> src = input;
    std::vector<int> dst(n);

    // Phase 1: insertion sort initial blocks
    for (int lo = 0; lo < n; lo += BLOCK)
        insertion_sort_block(src.data(), lo, std::min(lo + BLOCK - 1, n - 1));

    // Phase 2: bottom-up merge passes
    for (int width = BLOCK; width < n; width *= 2) {
        for (int lo = 0; lo < n; lo += 2 * width) {
            int mid = std::min(lo + width,     n);
            int hi  = std::min(lo + 2 * width, n);
            if (mid >= hi) {
                std::copy(src.begin() + lo, src.begin() + hi, dst.begin() + lo);
                continue;
            }
            int i = lo, j = mid, k = lo;
            while (i < mid && j < hi)
                dst[k++] = src[i] <= src[j] ? src[i++] : src[j++];
            while (i < mid) dst[k++] = src[i++];
            while (j < hi)  dst[k++] = src[j++];
        }
        std::swap(src, dst);
    }
    return src;
}
// ─────────────────────────────────────────────────────────────────────────────

double bench_logos(std::vector<int>& data) {
    std::vector<int> arr = data;
    auto t0 = Clock::now();
    logos::sort(arr.begin(), arr.end());
    return std::chrono::duration<double>(Clock::now() - t0).count();
}

double bench_merge(std::vector<int>& data) {
    auto t0 = Clock::now();
    merge_sort(data);
    return std::chrono::duration<double>(Clock::now() - t0).count();
}

double bench_std(std::vector<int>& data) {
    std::vector<int> arr = data;
    auto t0 = Clock::now();
    std::sort(arr.begin(), arr.end());
    return std::chrono::duration<double>(Clock::now() - t0).count();
}

int main() {
    std::mt19937 rng{42};
    std::uniform_int_distribution<int> dist{0, MAX_VAL};

    std::vector<int> sizes = {500'000, 2'500'000, 10'000'000};

    std::cout << std::string(72, '=') << '\n';
    std::cout << "LogosSort vs Pure-C++ Merge Sort  (apples-to-apples)\n";
    std::cout << "std::sort (introsort) shown for reference only\n";
    std::cout << std::string(72, '=') << '\n';
    std::cout << std::setw(12) << "Size"
              << std::setw(13) << "LogosSort"
              << std::setw(13) << "MergeSort"
              << std::setw(13) << "std::sort"
              << std::setw(10) << "L/M ratio" << '\n';
    std::cout << std::string(72, '-') << '\n';

    for (int n : sizes) {
        std::vector<int> data(n);
        std::generate(data.begin(), data.end(), [&]{ return dist(rng); });

        double logos_tot = 0, merge_tot = 0, std_tot = 0;
        for (int r = 0; r < RUNS; r++) {
            logos_tot += bench_logos(data);
            merge_tot += bench_merge(data);
            std_tot   += bench_std(data);
        }

        double la = logos_tot / RUNS, ma = merge_tot / RUNS, sa = std_tot / RUNS;
        std::cout << std::setw(12) << n
                  << std::fixed << std::setprecision(3)
                  << std::setw(11) << la << "s"
                  << std::setw(11) << ma << "s"
                  << std::setw(11) << sa << "s"
                  << std::setw(8) << std::setprecision(2) << (la / ma) << "x\n";
    }
    std::cout << "\nL/M ratio < 1.0 means LogosSort is faster than pure-C++ merge sort.\n";
    return 0;
}
