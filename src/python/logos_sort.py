"""
Shim — re-exports logos_sort and logos_sort_inplace from the root module.

The root logos_sort.py is the single source of truth for the algorithm.
This file exists so that benchmark scripts in src/python/ can continue to
do a plain `from logos_sort import logos_sort_inplace` without path changes.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from logos_sort import logos_sort, logos_sort_inplace  # noqa: F401

__all__ = ['logos_sort', 'logos_sort_inplace']
