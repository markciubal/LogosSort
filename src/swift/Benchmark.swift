// Benchmark: logosSort vs Array.sort — Swift
// swiftc -O LogosSort.swift Benchmark.swift -o bench && ./bench

import Foundation

let RUNS:    Int = 5
let MAX_VAL: Int = 1_000_000_000

func randomArray(_ n: Int) -> [Int] {
    (0..<n).map { _ in Int.random(in: 0..<MAX_VAL) }
}

func benchLogos(_ data: [Int]) -> Double {
    var arr = data
    let t0  = Date()
    logosSort(&arr)
    return Date().timeIntervalSince(t0)
}

func benchStd(_ data: [Int]) -> Double {
    var arr = data
    let t0  = Date()
    arr.sort()
    return Date().timeIntervalSince(t0)
}

let sizes = [500_000, 2_500_000, 10_000_000]

print("LogosSort vs Array.sort — Swift benchmark")
print(String(repeating: "=", count: 60))
print(String(format: "%12s  %11s  %11s  %7s", "Size", "LogosSort", "Array.sort", "Ratio"))
print(String(repeating: "-", count: 60))

for n in sizes {
    let data = randomArray(n)

    let logosAvg = (0..<RUNS).map { _ in benchLogos(data) }.reduce(0, +) / Double(RUNS)
    let stdAvg   = (0..<RUNS).map { _ in benchStd(data)   }.reduce(0, +) / Double(RUNS)
    let ratio    = logosAvg / stdAvg

    print(String(format: "%12d  %9.3fs  %9.3fs  %6.2fx", n, logosAvg, stdAvg, ratio))
}
