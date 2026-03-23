"""
Tests for logos_sort and logos_sort_inplace.

Covers: correctness, edge cases, key=, reverse=, and both public interfaces.
Run with: python -m pytest tests/ or python tests/test_logos_sort.py
"""

import sys
import os
import random
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from logos_sort import logos_sort, logos_sort_inplace


class TestLogosSortCopy(unittest.TestCase):

    # ── Basic correctness ─────────────────────────────────────────────────────

    def test_empty(self):
        self.assertEqual(logos_sort([]), [])

    def test_single(self):
        self.assertEqual(logos_sort([42]), [42])

    def test_two_sorted(self):
        self.assertEqual(logos_sort([1, 2]), [1, 2])

    def test_two_reversed(self):
        self.assertEqual(logos_sort([2, 1]), [1, 2])

    def test_already_sorted(self):
        data = list(range(100))
        self.assertEqual(logos_sort(data), data)

    def test_reverse_sorted(self):
        data = list(range(100, 0, -1))
        self.assertEqual(logos_sort(data), list(range(1, 101)))

    def test_all_equal(self):
        data = [7] * 50
        self.assertEqual(logos_sort(data), [7] * 50)

    def test_random_integers(self):
        data = [random.randint(-1000, 1000) for _ in range(500)]
        self.assertEqual(logos_sort(data), sorted(data))

    def test_random_floats(self):
        data = [random.uniform(-100.0, 100.0) for _ in range(500)]
        self.assertEqual(logos_sort(data), sorted(data))

    def test_negative_numbers(self):
        data = [-5, -1, -3, -2, -4]
        self.assertEqual(logos_sort(data), [-5, -4, -3, -2, -1])

    def test_mixed_sign(self):
        data = [3, -1, 4, -1, 5, -9, 2, 6]
        self.assertEqual(logos_sort(data), sorted(data))

    def test_large_random(self):
        data = [random.randint(0, 10**9) for _ in range(10_000)]
        self.assertEqual(logos_sort(data), sorted(data))

    def test_duplicate_heavy(self):
        data = [random.randint(0, 5) for _ in range(1000)]
        self.assertEqual(logos_sort(data), sorted(data))

    def test_strings(self):
        data = ['banana', 'apple', 'cherry', 'date']
        self.assertEqual(logos_sort(data), sorted(data))

    # ── Does not modify original ──────────────────────────────────────────────

    def test_original_unchanged(self):
        data = [3, 1, 4, 1, 5, 9]
        original = data[:]
        logos_sort(data)
        self.assertEqual(data, original)

    # ── reverse= ─────────────────────────────────────────────────────────────

    def test_reverse_empty(self):
        self.assertEqual(logos_sort([], reverse=True), [])

    def test_reverse_single(self):
        self.assertEqual(logos_sort([1], reverse=True), [1])

    def test_reverse_integers(self):
        data = [3, 1, 4, 1, 5, 9, 2, 6]
        self.assertEqual(logos_sort(data, reverse=True), sorted(data, reverse=True))

    def test_reverse_floats(self):
        data = [random.uniform(-50.0, 50.0) for _ in range(200)]
        self.assertEqual(logos_sort(data, reverse=True), sorted(data, reverse=True))

    # ── key= ─────────────────────────────────────────────────────────────────

    def test_key_abs(self):
        data = [-3, 1, -2, 4, -5]
        self.assertEqual(logos_sort(data, key=abs), sorted(data, key=abs))

    def test_key_str_lower(self):
        data = ['Banana', 'apple', 'Cherry', 'date']
        self.assertEqual(logos_sort(data, key=str.lower), sorted(data, key=str.lower))

    def test_key_lambda(self):
        data = [(3, 'c'), (1, 'a'), (2, 'b')]
        self.assertEqual(logos_sort(data, key=lambda x: x[0]),
                         sorted(data, key=lambda x: x[0]))

    def test_key_neg_len(self):
        data = ['fig', 'banana', 'kiwi', 'apple', 'cherry']
        self.assertEqual(logos_sort(data, key=len), sorted(data, key=len))

    # ── key= stability ────────────────────────────────────────────────────────

    def test_key_stable(self):
        # Items with equal keys must preserve original relative order.
        data = [(1, 'b'), (1, 'a'), (2, 'z'), (2, 'x'), (1, 'c')]
        result = logos_sort(data, key=lambda x: x[0])
        expected = sorted(data, key=lambda x: x[0])  # Python's sort is stable
        self.assertEqual(result, expected)

    # ── key= + reverse= ───────────────────────────────────────────────────────

    def test_key_and_reverse(self):
        data = [-3, 1, -2, 4, -5]
        self.assertEqual(logos_sort(data, key=abs, reverse=True),
                         sorted(data, key=abs, reverse=True))


class TestLogosSortInplace(unittest.TestCase):

    # ── Basic correctness ─────────────────────────────────────────────────────

    def test_empty(self):
        a = []; logos_sort_inplace(a); self.assertEqual(a, [])

    def test_single(self):
        a = [42]; logos_sort_inplace(a); self.assertEqual(a, [42])

    def test_two_reversed(self):
        a = [2, 1]; logos_sort_inplace(a); self.assertEqual(a, [1, 2])

    def test_already_sorted(self):
        a = list(range(100)); logos_sort_inplace(a)
        self.assertEqual(a, list(range(100)))

    def test_reverse_sorted(self):
        a = list(range(100, 0, -1)); logos_sort_inplace(a)
        self.assertEqual(a, list(range(1, 101)))

    def test_all_equal(self):
        a = [3] * 100; logos_sort_inplace(a)
        self.assertEqual(a, [3] * 100)

    def test_random_integers(self):
        data = [random.randint(-500, 500) for _ in range(500)]
        expected = sorted(data)
        logos_sort_inplace(data)
        self.assertEqual(data, expected)

    def test_large_random(self):
        data = [random.randint(0, 10**9) for _ in range(10_000)]
        expected = sorted(data)
        logos_sort_inplace(data)
        self.assertEqual(data, expected)

    # ── Modifies original ─────────────────────────────────────────────────────

    def test_modifies_in_place(self):
        a = [3, 1, 2]
        ref = a  # same object
        logos_sort_inplace(a)
        self.assertIs(a, ref)
        self.assertEqual(a, [1, 2, 3])

    def test_returns_none(self):
        self.assertIsNone(logos_sort_inplace([3, 1, 2]))

    # ── reverse= ─────────────────────────────────────────────────────────────

    def test_reverse(self):
        data = [random.randint(0, 100) for _ in range(200)]
        expected = sorted(data, reverse=True)
        logos_sort_inplace(data, reverse=True)
        self.assertEqual(data, expected)

    # ── key= ─────────────────────────────────────────────────────────────────

    def test_key_abs(self):
        data = [-3, 1, -2, 4, -5]
        expected = sorted(data, key=abs)
        logos_sort_inplace(data, key=abs)
        self.assertEqual(data, expected)

    def test_key_and_reverse(self):
        data = [-3, 1, -2, 4, -5]
        expected = sorted(data, key=abs, reverse=True)
        logos_sort_inplace(data, key=abs, reverse=True)
        self.assertEqual(data, expected)


class TestLogosSortEmbed(unittest.TestCase):
    """Same tests against the embed variant to ensure it stays in sync."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from logos_sort_embed import logos_sort as ls, logos_sort_inplace as lsi
        cls.ls  = staticmethod(ls)
        cls.lsi = staticmethod(lsi)

    def test_copy_random(self):
        data = [random.randint(-1000, 1000) for _ in range(1000)]
        self.assertEqual(self.ls(data), sorted(data))

    def test_inplace_random(self):
        data = [random.randint(-1000, 1000) for _ in range(1000)]
        expected = sorted(data)
        self.lsi(data)
        self.assertEqual(data, expected)

    def test_key_and_reverse(self):
        data = [-3, 1, -2, 4, -5]
        self.assertEqual(self.ls(data, key=abs, reverse=True),
                         sorted(data, key=abs, reverse=True))


if __name__ == '__main__':
    unittest.main()
