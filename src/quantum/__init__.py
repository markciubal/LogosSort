"""
LogosSort — Quantum Edition
IBM Quantum / Qiskit implementation.

Quick start
───────────
  from src.quantum.logos_sort_quantum import logos_sort_quantum
  result = logos_sort_quantum([5, 3, 8, 1, 9, 2])   # uses Aer if no API key
"""
from .logos_sort_quantum import (
    logos_sort_quantum,
    logos_sort_quantum_inplace,
    evaluate_phi_quantum,
    get_quantum_chaos,
    build_qrng_circuit,
    build_phi_qpe_circuit,
    compute_phi_decimal,
    PHI_DECIMAL,
)

__all__ = [
    "logos_sort_quantum",
    "logos_sort_quantum_inplace",
    "evaluate_phi_quantum",
    "get_quantum_chaos",
    "build_qrng_circuit",
    "build_phi_qpe_circuit",
    "compute_phi_decimal",
    "PHI_DECIMAL",
]
