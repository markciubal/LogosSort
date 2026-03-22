# LogosSort — pure R implementation
# Golden-ratio dual-pivot introsort with oracle-seeded pivot selection.
#
# Matches the Python logos_sort.py algorithm exactly:
#   - Two pivots at phi and 1-phi positions of a chaos-seeded index
#   - Ninther pivot refinement (median-of-3 neighbours)
#   - Three-way dual-pivot partition
#   - Counting sort fast path for integer arrays (span < 4*n)
#   - Monotone detection: ascending returned as-is, descending reversed
#   - Depth budget 2*floor(log2(n)) + 4 -> insertion sort fallback
#   - Tail-call optimisation: two smaller partitions recurse, largest loops
#
# Note: R uses 1-based indexing throughout.

PHI_SHIFT <- 61L
PHI_NUM   <- as.integer(round(0.6180339887498949 * 2^PHI_SHIFT))
PHI2_NUM  <- as.integer(round(0.3819660112501051 * 2^PHI_SHIFT))

# ── Insertion sort ─────────────────────────────────────────────────────────────
.insertion_sort <- function(a, lo, hi) {
  if (lo >= hi) return(a)
  for (i in (lo + 1L):hi) {
    key <- a[i]
    j   <- i - 1L
    while (j >= lo && a[j] > key) {
      a[j + 1L] <- a[j]
      j <- j - 1L
    }
    a[j + 1L] <- key
  }
  a
}

# ── Ninther pivot refinement ───────────────────────────────────────────────────
.ninther <- function(a, lo, hi, idx) {
  i0 <- max(lo, idx - 1L)
  i2 <- min(hi, idx + 1L)
  x <- a[i0]; y <- a[idx]; z <- a[i2]
  if (x > y) { tmp <- x; x <- y; y <- tmp }
  if (y > z) { tmp <- y; y <- z; z <- tmp }
  if (x > y) {             y <- x         }  # x unused after; only y needed
  y  # median of three
}

# ── Dual-pivot partition ───────────────────────────────────────────────────────
.dual_partition <- function(a, lo, hi, p1, p2) {
  if (p1 > p2) { tmp <- p1; p1 <- p2; p2 <- tmp }
  lt <- lo; gt <- hi; i <- lo
  while (i <= gt) {
    v <- a[i]
    if (v < p1) {
      tmp <- a[lt]; a[lt] <- a[i]; a[i] <- tmp
      lt <- lt + 1L; i <- i + 1L
    } else if (v > p2) {
      tmp <- a[i]; a[i] <- a[gt]; a[gt] <- tmp
      gt <- gt - 1L                 # do NOT advance i
    } else {
      i <- i + 1L
    }
  }
  list(a = a, lt = lt, gt = gt)
}

# ── Core sort (iterative outer loop for TCO) ──────────────────────────────────
# R does not have true TCO, but we simulate it with an explicit stack for the
# two smaller partitions and a while loop for the largest.
.logos_sort_impl <- function(a, lo, hi, depth) {
  stack <- list()  # pending (lo, hi, depth) triples for smaller partitions

  repeat {
    while (lo < hi) {
      size <- hi - lo + 1L

      # Base case: budget exhausted or small enough for insertion sort
      if (depth <= 0L || size <= 48L) {
        a <- .insertion_sort(a, lo, hi)
        break
      }

      # Counting sort fast path for integer arrays (span < 4*n)
      if (is.integer(a)) {
        mn <- a[lo]; mx <- a[lo]
        for (i in (lo + 1L):hi) {
          v <- a[i]
          if (v < mn) mn <- v else if (v > mx) mx <- v
        }
        span <- mx - mn
        if (span < size * 4L) {
          counts <- integer(span + 1L)
          for (i in lo:hi) counts[a[i] - mn + 1L] <- counts[a[i] - mn + 1L] + 1L
          k <- lo
          for (v_idx in seq_along(counts)) {
            cnt <- counts[v_idx]
            if (cnt > 0L) {
              a[k:(k + cnt - 1L)] <- mn + v_idx - 1L
              k <- k + cnt
            }
          }
          break
        }
      }

      # Monotone detection
      if (a[lo] <= a[lo + 1L] && a[lo + 1L] <= a[lo + 2L]) {
        asc <- TRUE
        for (i in lo:(hi - 1L)) {
          if (a[i] > a[i + 1L]) { asc <- FALSE; break }
        }
        if (asc) break

        desc <- TRUE
        for (i in lo:(hi - 1L)) {
          if (a[i] < a[i + 1L]) { desc <- FALSE; break }
        }
        if (desc) {
          a[lo:hi] <- rev(a[lo:hi])
          break
        }
      }

      # Oracle-seeded golden-ratio pivot selection
      c_val <- 0.0
      while (c_val == 0.0) c_val <- runif(1L, -1.0, 1.0)
      chaos_int <- as.double(abs(c_val)) * 2^53
      pn1  <- PHI2_NUM * chaos_int
      pn2  <- PHI_NUM  * chaos_int
      ps   <- PHI_SHIFT + 53L
      span <- hi - lo

      idx1 <- lo + as.integer(bitwShiftR(as.integer(span * pn1 / 2^53), PHI_SHIFT))
      idx2 <- lo + as.integer(bitwShiftR(as.integer(span * pn2 / 2^53), PHI_SHIFT))
      idx1 <- max(lo, min(hi, idx1))
      idx2 <- max(lo, min(hi, idx2))

      p1 <- .ninther(a, lo, hi, idx1)
      p2 <- .ninther(a, lo, hi, idx2)

      res <- .dual_partition(a, lo, hi, p1, p2)
      a   <- res$a; lt <- res$lt; gt <- res$gt

      left_n  <- lt - lo
      mid_n   <- gt - lt + 1L
      right_n <- hi - gt

      # Sort three regions by size; recurse into two smallest, loop on largest
      regions <- list(
        c(left_n,  lo,    lt - 1L),
        c(mid_n,   lt,    gt     ),
        c(right_n, gt + 1L, hi   )
      )
      sizes_ord <- order(sapply(regions, `[`, 1L))
      r0 <- regions[[sizes_ord[1L]]]
      r1 <- regions[[sizes_ord[2L]]]
      r2 <- regions[[sizes_ord[3L]]]  # largest — becomes next loop iteration

      if (r0[1L] > 0L && r0[2L] < r0[3L]) stack <- c(stack, list(c(r0[2L], r0[3L], depth - 1L)))
      if (r1[1L] > 0L && r1[2L] < r1[3L]) stack <- c(stack, list(c(r1[2L], r1[3L], depth - 1L)))

      lo    <- r2[2L]
      hi    <- r2[3L]
      depth <- depth - 1L
    }

    if (length(stack) == 0L) break
    frame <- stack[[length(stack)]]
    stack <- stack[-length(stack)]
    lo    <- frame[1L]; hi <- frame[2L]; depth <- frame[3L]
  }

  a
}

# ── Public API ─────────────────────────────────────────────────────────────────

#' Sort a vector using LogosSort.
#'
#' @param x  An atomic vector (numeric or integer).
#' @return   A sorted copy of x.
logos_sort <- function(x) {
  n <- length(x)
  if (n < 2L) return(x)
  depth <- 2L * as.integer(floor(log2(n))) + 4L
  .logos_sort_impl(x, 1L, n, depth)
}
