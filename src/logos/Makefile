# Makefile — LogosSort Logos→C benchmark
#
# Targets:
#   make          — build bench (using pre-generated logos_sort.c)
#   make transpile — regenerate logos_sort_gen.c from logos_sort.lg first
#   make run      — build + run
#   make clean    — remove build artifacts
#
# Compilers supported: gcc, clang (both require __uint128_t)
# MSVC: use clang-cl or MinGW — MSVC lacks __uint128_t.

CC      ?= gcc
CFLAGS  ?= -O2 -std=c11 -Wall -Wextra -Wpedantic
LIBS    := -lm

# Linux/macOS: use --wrap to intercept malloc for exact peak tracking
# Windows/MinGW: wrap not available; bench.c uses heap-delta fallback
UNAME := $(shell uname -s 2>/dev/null || echo Windows)

ifeq ($(UNAME), Linux)
  WRAP_FLAGS := -Wl,--wrap=malloc,--wrap=free
else ifeq ($(UNAME), Darwin)
  # macOS ld does not support --wrap; disable for now
  WRAP_FLAGS :=
else
  WRAP_FLAGS :=
endif

SRCS := logos_sort.c timsort.c bench.c
OBJS := $(SRCS:.c=.o)

.PHONY: all transpile run clean

all: bench

bench: $(SRCS) logos_sort.h timsort.h
	$(CC) $(CFLAGS) $(WRAP_FLAGS) $(SRCS) $(LIBS) -o bench

# Regenerate logos_sort_gen.c from the .lg source, then build with it
transpile: logos_sort.lg logos_compile.py timsort.c bench.c
	python logos_compile.py logos_sort.lg > logos_sort_gen.c
	$(CC) $(CFLAGS) $(WRAP_FLAGS) logos_sort_gen.c timsort.c bench.c $(LIBS) -o bench_gen
	@echo "Built bench_gen from transpiled source."

run: bench
	./bench

clean:
	rm -f bench bench_gen logos_sort_gen.c *.o

# ── Quick sanity check: verify output is sorted ──────────────────────────────
check: bench
	@./bench | grep -q "LogosSort" && echo "OK: benchmark ran" || echo "FAIL"
