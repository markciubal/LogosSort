/**
 * Benchmark: logos::sort vs std::sort
 * Sizes: 500 000 · 2 500 000 · 10 000 000
 *
 * Compile (Linux/macOS):
 *   g++ -O2 -std=c++17 -o bench benchmark.cpp && ./bench
 *
 * Compile (Windows MSVC):
 *   cl /O2 /std:c++17 /EHsc benchmark.cpp
 */

#include "logos_sort.hpp"
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <vector>

static constexpr int RUNS    = 5;
static constexpr int MAX_VAL = 1'000'000'000;

using Clock = std::chrono::high_resolution_clock;

double bench_logos(std::vector<int>& data) {
    std::vector<int> arr = data;
    auto t0 = Clock::now();
    logos::sort(arr.begin(), arr.end());
    auto t1 = Clock::now();
    return std::chrono::duration<double>(t1 - t0).count();
}

double bench_stdsort(std::vector<int>& data) {
    std::vector<int> arr = data;
    auto t0 = Clock::now();
    std::sort(arr.begin(), arr.end());
    auto t1 = Clock::now();
    return std::chrono::duration<double>(t1 - t0).count();
}

int main() {
    std::mt19937 rng{42};
    std::uniform_int_distribution<int> dist{0, MAX_VAL};

    std::vector<int> sizes = {500'000, 2'500'000, 10'000'000};

    std::cout << "LogosSort vs std::sort (introsort) — C++ benchmark\n";
    std::cout << std::string(60, '=') << '\n';
    std::cout << std::setw(12) << "Size"
              << std::setw(13) << "LogosSort"
              << std::setw(13) << "std::sort"
              << std::setw(9)  << "Ratio" << '\n';
    std::cout << std::string(60, '-') << '\n';

    for (int n : sizes) {
        std::vector<int> data(n);
        std::generate(data.begin(), data.end(), [&]{ return dist(rng); });

        double logos_tot = 0, std_tot = 0;
        for (int r = 0; r < RUNS; r++) {
            logos_tot += bench_logos(data);
            std_tot   += bench_stdsort(data);
        }

        double logos_avg = logos_tot / RUNS;
        double std_avg   = std_tot   / RUNS;
        double ratio     = logos_avg / std_avg;

        std::cout << std::setw(12) << n
                  << std::fixed << std::setprecision(3)
                  << std::setw(11) << logos_avg << "s"
                  << std::setw(11) << std_avg   << "s"
                  << std::setw(7)  << std::setprecision(2) << ratio << "x\n";
    }
    return 0;
}
