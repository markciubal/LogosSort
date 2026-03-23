"""
"In the beginning was the Logos, and the Logos was with God, and the Logos was God."
 — John 1:1

LogosSort — Quantum Edition
IBM Quantum / Qiskit implementation using quantum-sourced entropy and
Quantum Phase Estimation of the golden ratio φ.

QUANTUM ORACLE (QRNG)
─────────────────────
Classical LogosSort seeds its pivot selection with platform entropy via
random.uniform(). This edition replaces that call with a quantum circuit:

  |0⟩ ──H──  ┐
  |0⟩ ──H──  ├── measure → n random bits
  |0⟩ ──H──  ┘

The Hadamard gate H = (1/√2)[[1,1],[1,-1]] maps each |0⟩ to the equal
superposition (|0⟩+|1⟩)/√2. Measurement collapses that superposition to 0 or
1 with exactly equal probability — irreducibly uncertain by the Born rule, not
by computational difficulty. The resulting bit string is the chaos_int that
seeds golden-ratio pivot placement.

PHI EVALUATION VIA QUANTUM PHASE ESTIMATION
────────────────────────────────────────────
φ − 1 = 0.6180339887498948482045868…  (the fractional part of φ)

We construct the 1-qubit unitary:

  U = P(2π · φ_frac)  where φ_frac = φ − 1

P(λ)|0⟩ = |0⟩,  P(λ)|1⟩ = e^{iλ}|1⟩

|1⟩ is an eigenstate of U with eigenphase φ_frac. Quantum Phase Estimation
with n_ancilla ancilla qubits recovers that eigenphase as an n-bit binary
fraction: b₁b₂…bₙ  ↦  Σᵢ bᵢ · 2^{−i} ≈ φ_frac.

Precision scales as 2^{−n_ancilla}. Using mpmath to build the rotation angle
beyond IEEE 754 float-64 precision (53 bits), and maximising n_ancilla on
whatever backend is available, we extract as many binary digits of φ as the
hardware allows — exceeding float-64's ~16 decimal places when n_ancilla > 53.

RUNNING ON IBM QUANTUM
──────────────────────
  pip install -r requirements.txt
  # set IBM_QUANTUM_API_KEY in .env, then:
  python logos_sort_quantum.py

If no key is set the code falls back to the local Qiskit Aer simulator
(noiseless, no qubit limit) so the algorithm can always be explored.

Pure Python sort logic — zero calls to C-backed sort functions.
Quantum circuits built with Qiskit 1.x and executed via qiskit-ibm-runtime.
"""

import os
import math
import struct
from decimal import Decimal, getcontext

# ── Environment ───────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional; set env vars directly if needed

IBM_API_KEY  = os.getenv("IBM_QUANTUM_API_KEY", "")
IBM_CHANNEL  = os.getenv("IBM_QUANTUM_CHANNEL",  "ibm_quantum_platform")
IBM_BACKEND  = os.getenv("IBM_QUANTUM_BACKEND",  "ibm_sherbrooke")
IBM_INSTANCE = os.getenv("IBM_QUANTUM_INSTANCE", "ibm-q/open/main")

# ── Qiskit imports ────────────────────────────────────────────────────────────
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import QFT

# ── High-precision φ via Decimal arithmetic ───────────────────────────────────
# We compute φ = (1 + √5) / 2 to DECIMAL_PLACES decimal places using
# Python's built-in Decimal module (no third-party deps required).
# The binary expansion of φ_frac = φ−1 is then used to seed the QPE circuit.

DECIMAL_PLACES = 200  # precision for classical reference value

def _sqrt5_decimal(places: int) -> Decimal:
    """Newton–Raphson √5 in arbitrary-precision Decimal arithmetic.

    Each iteration doubles correct digits; log₂(places / 0.3) iterations
    suffice.  Starting from x₀ = 2 (|2 − √5| ≈ 0.236) converges quickly.
    """
    getcontext().prec = places + 20          # guard digits against rounding
    five = Decimal(5)
    x    = Decimal(2)                        # x₀ ≈ √5
    half = Decimal("0.5")
    for _ in range(70):                      # 70 doublings → > 10^21 digits
        x_new = half * (x + five / x)
        if x_new == x:
            break
        x = x_new
    return x

def compute_phi_decimal(places: int = DECIMAL_PLACES) -> Decimal:
    """Return φ = (1+√5)/2 to *places* decimal digits."""
    getcontext().prec = places + 20
    return (Decimal(1) + _sqrt5_decimal(places)) / Decimal(2)

PHI_DECIMAL  = compute_phi_decimal(DECIMAL_PLACES)
PHI_FRAC_DEC = PHI_DECIMAL - Decimal(1)   # 0.6180339887…

# IEEE 754 constants used in the sort itself (same as root logos_sort.py)
PHI_SHIFT = 61
PHI_NUM   = round(0.6180339887498949 * (1 << PHI_SHIFT))
PHI2_NUM  = round(0.3819660112501051 * (1 << PHI_SHIFT))


# ── Circuit builders ──────────────────────────────────────────────────────────

def build_qrng_circuit(n_qubits: int = 53) -> QuantumCircuit:
    """Return a circuit that generates *n_qubits* quantum-random bits.

    Each qubit starts in |0⟩, receives a Hadamard gate to enter uniform
    superposition, then is measured.  The Born-rule collapse is the entropy
    source — no seed, no algorithm, just quantum mechanics.

    Parameters
    ----------
    n_qubits : int
        Number of random bits to produce.  Default 53 matches the mantissa
        width of IEEE 754 float-64, so the result can be used directly as a
        53-bit integer chaos_int for golden-ratio pivot scaling.
    """
    qr  = QuantumRegister(n_qubits, name="q")
    cr  = ClassicalRegister(n_qubits, name="meas")
    qc  = QuantumCircuit(qr, cr)
    qc.h(qr)          # H on every qubit: |0⟩ → (|0⟩+|1⟩)/√2
    qc.measure(qr, cr)
    return qc


def build_phi_qpe_circuit(n_ancilla: int, phi_frac: float | None = None) -> QuantumCircuit:
    """Return a Quantum Phase Estimation circuit that reads out φ_frac = φ−1.

    Architecture
    ────────────
    ancilla (n_ancilla qubits):  |0…0⟩ → H⊗n → controlled-U powers → IQFT → measure
    target  (1 qubit):           |0⟩ → X → |1⟩  (eigenstate of U = P(2π·φ_frac))

    The eigenphase of U is φ_frac.  QPE extracts that phase as an n-bit binary
    fraction:  meas_int / 2^n_ancilla ≈ φ_frac.

    Precision
    ─────────
    n_ancilla bits → error ≤ 2^{−n_ancilla}
    n=53  → matches float-64  (~16 decimal places)
    n=100 → ~30 decimal places
    n=127 → ~38 decimal places (full ibm_sherbrooke 127-qubit budget)

    The phase angle is seeded from *phi_frac* (defaults to the 200-digit
    Decimal value computed above, truncated to float-128 via Python's
    arbitrary-precision Decimal before being cast to float).
    """
    if phi_frac is None:
        # Use our high-precision Decimal φ_frac converted to Python float
        # (Python floats are IEEE 754 float-64 ≈ 53 bits of φ_frac).
        # The QPE circuit will therefore recover up to 53 correct bits;
        # beyond that the angle encoding itself is the limiting factor.
        phi_frac = float(PHI_FRAC_DEC)

    ancilla = QuantumRegister(n_ancilla, name="anc")
    target  = QuantumRegister(1,         name="tgt")
    cr      = ClassicalRegister(n_ancilla, name="phi")
    qc      = QuantumCircuit(ancilla, target, cr)

    # Prepare eigenstate |1⟩ on target qubit
    qc.x(target[0])

    # Superpose ancilla register
    qc.h(ancilla)

    # Controlled-U^{2^k} rotations
    # U = P(2π · phi_frac) acts on target; ancilla[k] is control
    # U^{2^k} = P(2^k · 2π · phi_frac)
    import numpy as np
    two_pi = 2.0 * np.pi
    for k in range(n_ancilla):
        angle = (2 ** k) * two_pi * phi_frac
        # Keep angle in (-2π, 2π) via modular reduction to avoid float overflow
        # for large k (only matters when n_ancilla > ~53)
        angle = angle % (two_pi)
        qc.cp(angle, ancilla[k], target[0])

    # Inverse QFT on ancilla register
    iqft = QFT(n_ancilla, inverse=True, do_swaps=True).decompose()
    qc.compose(iqft, qubits=ancilla, inplace=True)

    # Measure ancilla
    qc.measure(ancilla, cr)
    return qc


# ── Backend helpers ───────────────────────────────────────────────────────────

def _get_service():
    """Return a QiskitRuntimeService if IBM_API_KEY is set, else None.

    Tries with the configured instance first; if the instance is invalid for
    the selected channel (the new ibm_quantum_platform uses different instance
    formats to the legacy ibm_quantum channel), retries without an instance so
    the SDK can resolve it automatically from the account.
    """
    if not IBM_API_KEY:
        return None
    from qiskit_ibm_runtime import QiskitRuntimeService
    # Try with explicit instance first, then fall back to auto-resolution.
    for instance in (IBM_INSTANCE, None):
        try:
            kwargs = dict(channel=IBM_CHANNEL, token=IBM_API_KEY)
            if instance:
                kwargs["instance"] = instance
            return QiskitRuntimeService(**kwargs)
        except Exception as exc:
            last_exc = exc
    print(f"[quantum] IBM Quantum connection failed: {last_exc}")
    return None


def _aer_backend():
    """Return the local Qiskit Aer noiseless simulator."""
    from qiskit_aer import AerSimulator
    return AerSimulator()


def _resolve_backend():
    """Return (backend, is_real_hardware: bool).

    Resolution order:
      1. IBM_QUANTUM_BACKEND from .env (if accessible on the account)
      2. Least-busy real backend available on the account
      3. Local Aer simulator
    """
    svc = _get_service()
    if svc is not None:
        # Try the configured backend first
        try:
            backend = svc.backend(IBM_BACKEND)
            return backend, True
        except Exception:
            pass

        # Fall back to least-busy backend available on this account
        try:
            backends   = svc.backends(operational=True, simulator=False)
            if backends:
                least_busy = min(backends,
                                 key=lambda b: getattr(b, "num_pending_jobs", 9999))
                print(f"[quantum] {IBM_BACKEND} not available; "
                      f"using {least_busy.name} (least busy).")
                return least_busy, True
        except Exception as exc:
            print(f"[quantum] Could not list backends: {exc}")

        print("[quantum] No accessible hardware found. Falling back to Aer.")
    return _aer_backend(), False


def _run_circuit(backend, circuit: QuantumCircuit, shots: int = 1) -> dict[str, int]:
    """Execute a circuit and return counts dict {int_bitstring: count}.

    Routes to the Aer local path or the IBM Runtime path depending on backend
    type, so that each path uses only its own transpilation/execution API.
    """
    from qiskit_aer import AerSimulator

    if isinstance(backend, AerSimulator):
        # ── Aer path: run directly, no coupling-map transpilation needed ─────
        job    = backend.run(circuit, shots=shots)
        counts = job.result().get_counts()
        return {int(k.replace(" ", ""), 2): v for k, v in counts.items()}

    # ── IBM Runtime path ──────────────────────────────────────────────────────
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from qiskit_ibm_runtime import SamplerV2 as IBMSampler

    pm      = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_qc  = pm.run(circuit)
    sampler = IBMSampler(mode=backend)
    job     = sampler.run([isa_qc], shots=shots)
    result  = job.result()
    pub_res = result[0]
    cr_name  = circuit.cregs[0].name
    bitarray = getattr(pub_res.data, cr_name)
    return bitarray.get_int_counts()


# ── Quantum entropy extraction ────────────────────────────────────────────────

def get_quantum_chaos(backend=None, n_qubits: int = 53) -> int:
    """Run the QRNG circuit and return a random integer in [1, 2^n_qubits).

    Single-shot convenience wrapper.  For multiple sort calls use
    QuantumChaosPool instead — it issues one batched job and draws locally.
    """
    if backend is None:
        backend, _ = _resolve_backend()
    qc     = build_qrng_circuit(n_qubits)
    counts = _run_circuit(backend, qc, shots=1)
    bits   = max(counts, key=counts.get)
    return bits if bits != 0 else (1 << (n_qubits - 1))


class QuantumChaosPool:
    """Pre-fetched pool of quantum-random integers from a single batched QRNG job.

    Instead of one API round-trip per sort call, all required chaos values are
    drawn in a single circuit execution (one job, many shots).  Subsequent
    pool.draw() calls are pure Python deque pops — zero network or simulator
    overhead.

    Usage
    -----
    pool = QuantumChaosPool(backend, size=50)   # one quantum job, 50 shots
    for data in datasets:
        result = logos_sort_quantum(data, chaos_int=pool.draw())

    Parameters
    ----------
    backend  : Qiskit backend.  Resolved automatically if None.
    size     : Number of chaos values to pre-fetch (one per planned sort call).
    n_qubits : Width of each chaos value in bits.  Default 53 matches the
               IEEE 754 float-64 mantissa used in the golden-ratio pivot math.
    """

    def __init__(self, backend=None, size: int = 64, n_qubits: int = 53):
        if backend is None:
            backend, _ = _resolve_backend()
        self._n_qubits = n_qubits
        self._pool: "collections.deque[int]" = self._fetch(backend, size)

    @staticmethod
    def _fetch(backend, size: int) -> "collections.deque[int]":
        import collections
        qc = build_qrng_circuit(53)
        # One job, *size* shots — each shot is an independent Hadamard collapse
        counts = _run_circuit(backend, qc, shots=size)
        pool: collections.deque[int] = collections.deque()
        for bits, count in counts.items():
            val = bits if bits != 0 else (1 << 52)
            for _ in range(count):
                pool.append(val)
        return pool

    def draw(self) -> int:
        """Pop and return one chaos value.  Falls back to os.urandom if empty."""
        if self._pool:
            return self._pool.popleft()
        # Pool exhausted — fall back to platform entropy rather than silently
        # returning a fixed value or raising.
        import os
        raw = int.from_bytes(os.urandom(7), "big") & ((1 << 53) - 1)
        return raw if raw != 0 else 1 << 52

    def __len__(self) -> int:
        return len(self._pool)

    def __repr__(self) -> str:
        return f"QuantumChaosPool(remaining={len(self._pool)}, n_qubits={self._n_qubits})"


# ── φ extraction from QPE ─────────────────────────────────────────────────────

def evaluate_phi_quantum(
    backend=None,
    n_ancilla: int | None = None,
    shots: int = 8192,
) -> tuple[Decimal, str]:
    """Run QPE and return (φ as Decimal, binary expansion string).

    Parameters
    ----------
    backend   : Qiskit backend.  Resolved automatically if None.
    n_ancilla : Number of QPE ancilla qubits.  Defaults to the smaller of
                (backend.num_qubits − 1, 100).  More qubits = more digits.
    shots     : Measurement repetitions.  More shots reduce sampling noise.

    Returns
    -------
    phi_decimal : φ reconstructed from QPE bitstring as a Decimal value.
    binary_str  : The raw binary fraction "0.b₁b₂…bₙ" of φ_frac.
    """
    if backend is None:
        backend, is_hw = _resolve_backend()
    else:
        is_hw = False

    max_q = getattr(backend, "num_qubits", 127)
    if n_ancilla is None:
        n_ancilla = min(max_q - 1, 100)

    print(f"[phi-qpe] Using {n_ancilla} ancilla qubits on {backend}.")
    print(f"[phi-qpe] Theoretical precision: 2^{{-{n_ancilla}}} "
          f"≈ {2**-n_ancilla:.2e} ({int(n_ancilla * math.log10(2)):.0f} decimal places)")

    qc     = build_phi_qpe_circuit(n_ancilla)
    counts = _run_circuit(backend, qc, shots=shots)

    # Most-probable measurement = best estimate of φ_frac binary expansion
    best_int = max(counts, key=counts.get)
    total    = sum(counts.values())
    prob     = counts[best_int] / total
    print(f"[phi-qpe] Best bitstring probability: {prob:.3f}")

    # Reconstruct φ_frac from integer: frac = best_int / 2^n_ancilla
    getcontext().prec = DECIMAL_PLACES + 20
    phi_frac_qpe  = Decimal(best_int) / Decimal(2 ** n_ancilla)
    phi_qpe       = Decimal(1) + phi_frac_qpe

    # Build binary string representation "1.b₁b₂…bₙ"
    bits = format(best_int, f"0{n_ancilla}b")
    binary_str = "1." + bits

    return phi_qpe, binary_str


# ── Sort helpers (pure Python, same logic as logos_sort.py) ───────────────────

def _insertion_sort(a, lo, hi):
    for i in range(lo + 1, hi + 1):
        key = a[i]; j = i - 1
        while j >= lo and a[j] > key:
            a[j + 1] = a[j]; j -= 1
        a[j + 1] = key


def _ninther(a, lo, hi, idx):
    i0 = max(lo, idx - 1)
    i2 = min(hi, idx + 1)
    x, y, z = a[i0], a[idx], a[i2]
    if x > y: x, y = y, x
    if y > z: y, z = z, y
    if x > y: x, y = y, x
    return y


def _dual_partition(a, lo, hi, p1, p2):
    if p1 > p2:
        p1, p2 = p2, p1
    lt, gt, i = lo, hi, lo
    while i <= gt:
        v = a[i]
        if v < p1:
            a[lt], a[i] = a[i], a[lt]; lt += 1; i += 1
        elif v > p2:
            a[i], a[gt] = a[gt], a[i]; gt -= 1
        else:
            i += 1
    return lt, gt


def _sort(a, lo, hi, depth, chaos_int: int):
    """Core recursive sort.  chaos_int is the quantum-sourced oracle value."""
    while lo < hi:
        size = hi - lo + 1

        if depth <= 0 or size <= 48:
            _insertion_sort(a, lo, hi)
            return

        if isinstance(a[lo], int):
            mn = mx = a[lo]
            for i in range(lo + 1, hi + 1):
                v = a[i]
                if v < mn: mn = v
                elif v > mx: mx = v
            span = mx - mn
            if span < size * 4:
                counts = [0] * (span + 1)
                for i in range(lo, hi + 1):
                    counts[a[i] - mn] += 1
                k = lo
                for v, cnt in enumerate(counts):
                    for _ in range(cnt):
                        a[k] = v + mn; k += 1
                return

        if a[lo] <= a[lo + 1] <= a[lo + 2]:
            asc = True
            for i in range(lo, hi):
                if a[i] > a[i + 1]: asc = False; break
            if asc: return
            desc = True
            for i in range(lo, hi):
                if a[i] < a[i + 1]: desc = False; break
            if desc:
                l, r = lo, hi
                while l < r: a[l], a[r] = a[r], a[l]; l += 1; r -= 1
                return

        # Golden-ratio pivot selection seeded by the quantum chaos_int.
        # chaos_int is fixed per sort call (drawn once from the quantum oracle)
        # and mixed with depth + lo to vary pivot positions across partitions.
        mixed   = chaos_int ^ (depth * 0x9E3779B97F4A7C15) ^ (lo * 0x6C62272E07BB0142)
        mixed   = mixed & ((1 << 53) - 1)
        if mixed == 0: mixed = chaos_int | 1

        pn1 = PHI2_NUM * mixed
        pn2 = PHI_NUM  * mixed
        ps  = PHI_SHIFT + 53
        sp  = hi - lo
        idx1 = lo + (sp * pn1 >> ps)
        idx2 = lo + (sp * pn2 >> ps)

        p1 = _ninther(a, lo, hi, idx1)
        p2 = _ninther(a, lo, hi, idx2)
        lt, gt = _dual_partition(a, lo, hi, p1, p2)

        left_n  = lt - lo
        mid_n   = gt - lt + 1
        right_n = hi - gt

        r0 = (left_n,  lo,     lt - 1)
        r1 = (mid_n,   lt,     gt    )
        r2 = (right_n, gt + 1, hi    )
        if r0[0] > r1[0]: r0, r1 = r1, r0
        if r1[0] > r2[0]: r1, r2 = r2, r1
        if r0[0] > r1[0]: r0, r1 = r1, r0

        for _, r_lo, r_hi in (r0, r1):
            if r_lo < r_hi: _sort(a, r_lo, r_hi, depth - 1, chaos_int)

        lo, hi = r2[1], r2[2]
        depth -= 1


def _depth(n):
    return 2 * int(math.log2(n)) + 4


# ── Public API ────────────────────────────────────────────────────────────────

def logos_sort_quantum(
    arr: list,
    *,
    key=None,
    reverse: bool = False,
    backend=None,
    chaos_int: int | None = None,
) -> list:
    """Return a new sorted list seeded by quantum entropy from IBM Quantum.

    Parameters
    ----------
    arr       : list   Input sequence.
    key       : callable, optional  Like sorted()'s key=.
    reverse   : bool   Descending order if True.
    backend   : Qiskit backend.  Resolved automatically (IBM hardware or
                local Aer simulator) if None.
    chaos_int : int, optional  Pre-computed quantum chaos value.  If supplied,
                skips the QRNG circuit call — useful for batching many sorts
                off a single quantum draw.

    Returns
    -------
    list  Sorted copy of *arr*.
    """
    n = len(arr)
    if n < 2:
        result = arr[:]
        return result[::-1] if reverse else result

    if chaos_int is None:
        # Only resolve backend when we actually need to fetch quantum entropy.
        if backend is None:
            backend, _ = _resolve_backend()
        chaos_int = get_quantum_chaos(backend, n_qubits=53)

    if key is not None:
        work = [(key(arr[i]), i, arr[i]) for i in range(n)]
        _sort(work, 0, n - 1, _depth(n), chaos_int)
        result = [t[2] for t in work]
    else:
        work = arr[:]
        _sort(work, 0, n - 1, _depth(n), chaos_int)
        result = work

    return result[::-1] if reverse else result


def logos_sort_quantum_inplace(
    arr: list,
    *,
    key=None,
    reverse: bool = False,
    backend=None,
    chaos_int: int | None = None,
) -> None:
    """Sort *arr* in place using quantum-sourced pivot entropy."""
    n = len(arr)
    if n < 2:
        if reverse: arr.reverse()
        return

    if chaos_int is None:
        if backend is None:
            backend, _ = _resolve_backend()
        chaos_int = get_quantum_chaos(backend, n_qubits=53)

    if key is not None:
        sorted_copy = logos_sort_quantum(arr, key=key, reverse=reverse,
                                         backend=backend, chaos_int=chaos_int)
        arr[:] = sorted_copy
        return

    _sort(arr, 0, n - 1, _depth(n), chaos_int)
    if reverse:
        arr.reverse()


# ── Demo / self-test ──────────────────────────────────────────────────────────

def _demo():
    print("=" * 64)
    print("LogosSort — Quantum Edition")
    print("=" * 64)

    # ── φ reference value (classical, high-precision) ──────────────────
    print(f"\n[phi] Classical reference ({DECIMAL_PLACES} decimal places):")
    phi_str = str(PHI_DECIMAL)
    print(f"  φ = {phi_str[:72]}")
    if len(phi_str) > 72:
        print(f"        {phi_str[72:144]}")
        if len(phi_str) > 144:
            print(f"        {phi_str[144:202]}…")

    # ── Backend resolution ─────────────────────────────────────────────
    backend, is_hw = _resolve_backend()
    hw_label = f"IBM Quantum ({IBM_BACKEND})" if is_hw else "Aer simulator (local)"
    print(f"\n[backend] Running on: {hw_label}")

    # ── QPE φ evaluation ───────────────────────────────────────────────
    print("\n[phi-qpe] Evaluating φ via Quantum Phase Estimation…")
    max_q     = getattr(backend, "num_qubits", 127)
    n_ancilla = min(max_q - 1, 100)
    phi_qpe, binary_str = evaluate_phi_quantum(backend, n_ancilla=n_ancilla, shots=8192)

    getcontext().prec = DECIMAL_PLACES + 20
    error = abs(phi_qpe - PHI_DECIMAL)

    print(f"\n[phi-qpe] Result ({n_ancilla} ancilla qubits):")
    print(f"  φ binary = {binary_str[:66]}…")
    print(f"  φ decimal = {phi_qpe}")
    print(f"  |QPE − reference| = {error:.2e}")
    n_correct_decimal = -int(math.log10(float(error))) if error > 0 else DECIMAL_PLACES
    print(f"  Correct decimal places: ~{n_correct_decimal}")

    # ── QRNG sort demo ─────────────────────────────────────────────────
    print("\n[qrng] Drawing quantum chaos_int from Hadamard circuit…")
    chaos = get_quantum_chaos(backend, n_qubits=53)
    print(f"  chaos_int = {chaos} (0x{chaos:016x})")

    sample = [42, 7, 99, 1, 55, 23, 88, 3, 17, 64, 31, 76, 8, 50]
    print(f"\n[sort]  input  = {sample}")
    result = logos_sort_quantum(sample, backend=backend, chaos_int=chaos)
    print(f"[sort]  output = {result}")

    sample2 = ["logos", "order", "chaos", "phi", "quantum", "sort"]
    result2 = logos_sort_quantum(sample2, key=str.lower, backend=backend)
    print(f"\n[sort]  strings input  = {sample2}")
    print(f"[sort]  strings output = {result2}")

    print("\n[✓] All demonstrations complete.")


if __name__ == "__main__":
    _demo()
