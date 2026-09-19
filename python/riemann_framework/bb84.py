# Riemann Framework
# Copyright (C) 2026 MILAN NIKOLIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
BB84 baseline simulation, for comparison with DSIN.

BB84 encodes bits in the polarization basis (Z) or the Hadamard basis (X).
Eavesdropping is *not* detected by basis mismatch: Alice's and Bob's bases are
chosen independently at random, so they disagree in roughly half of all rounds
whether or not anyone is listening. Those rounds are simply discarded in
sifting. Detection works on the rounds that survive — the sifted key — by
checking whether its error rate (the QBER) exceeds a threshold.

This module therefore reports two separate quantities:

  - `ber`: the QBER on the sifted key, the statistic that actually matters;
  - `detected`: whether the QBER crossed `detection_threshold`.

`detection_rate` is the run-level verdict expressed as 0.0 or 1.0 so that it can
be tabulated alongside DSIN's per-round detection rate, but it is *not* a
per-round rate: BB84 has no per-round detection event. `sifting_discard_rate` is
reported separately so that the two cannot be confused.

Two backends, and why they are comparable
-----------------------------------------
`run_bb84` simulates the rounds either in a Python loop (`backend="loop"`) or with
NumPy array operations over all rounds at once (`backend="numpy"`, the default).
A round in the loop does a handful of operations on 2-vectors, which is almost
entirely interpreter and call overhead: measured at about 8 us per round, against
about 0.0085 us per element for the same work batched. The vectorized path is
therefore worth roughly three orders of magnitude, and it needs no GPU to get it.

The two backends do **not** reproduce each other's numbers on the same seed, and
that is a property of the generator rather than a defect. The looped version
interleaves two different generator methods per round — `integers` for the bit and
`random` for the basis — while any vectorized version draws grouped by kind. Those
are different positions in the same stream: measured, `integers` and `random` are
each reproducible scalar-versus-bulk, but drawing `bit, basis, measure` per round
is *not* the same stream as drawing all bits, then all bases, then all measures.
So same-seed equality was never available, and the tests pin the two claims that
are:

  - **exact logic equivalence**: both backends consume the same `RoundDraws`
    bundle, and given identical draws they must agree exactly, round for round;
  - **statistical equivalence**: on the same seed the two agree within binomial
    noise on the QBER and the detection rate.

Splitting it that way is deliberate: it isolates the logic from the generator,
where a same-seed assertion would have conflated the two.

This is a baseline for comparison, not a security proof; see
`docs/dimension_shift_quantum_communication.md`. The implementation layer, which
models what the protocol above cannot see, is `bb84_implementation.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# ============================================================
# Basis and states
# ============================================================

# Computational basis (Z)
KET_0 = np.array([1, 0], dtype=complex)
KET_1 = np.array([0, 1], dtype=complex)

# Hadamard basis (X)
KET_P = (KET_0 + KET_1) / np.sqrt(2)   # |+>
KET_M = (KET_0 - KET_1) / np.sqrt(2)   # |->

BASES = {
    "Z": (KET_0, KET_1),
    "X": (KET_P, KET_M),
}

#: Default abort threshold on the sifted-key error rate. An intercept-resend
#: attack drives the QBER to about 0.25; the ideal channel gives 0.
DEFAULT_DETECTION_THRESHOLD = 0.11

_SQRT_HALF = 1.0 / np.sqrt(2.0)


def encode_bb84(bit: int, basis: str) -> np.ndarray:
    """Encode a bit in the given basis."""
    states = BASES[basis]
    return states[bit].copy()


def measure_bb84(state: np.ndarray, basis: str,
                 rng: np.random.Generator) -> int:
    """
    Measure a BB84 state in the given basis.

    Returns the decoded bit (0 or 1).
    """
    states = BASES[basis]
    probabilities = np.array([abs(s.conj() @ state) ** 2 for s in states])
    probabilities = probabilities / probabilities.sum()
    return int(rng.choice([0, 1], p=probabilities))


def random_basis(rng: np.random.Generator) -> str:
    """Return a random basis: 'Z' or 'X'."""
    return "Z" if rng.random() < 0.5 else "X"


# ============================================================
# Noise and attack models
# ============================================================

def apply_depolarizing_noise_bb84(
    state: np.ndarray,
    p: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Apply depolarizing noise to a qubit.

    With probability `p` the qubit is replaced by a uniformly random qubit,
    which is the depolarizing channel ``rho -> (1 - p) * rho + p * I / 2``.
    """
    if rng.random() > p:
        return state
    vec = rng.standard_normal(2) + 1j * rng.standard_normal(2)
    return vec / np.linalg.norm(vec)


def intercept_resend_bb84(
    state: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Intercept-resend attack on BB84: Eve measures in a random basis, then
    re-encodes the bit she obtained."""
    eve_basis = random_basis(rng)
    eve_bit = measure_bb84(state, eve_basis, rng)
    return encode_bb84(eve_bit, eve_basis)


def partial_intercept_resend_bb84(
    state: np.ndarray,
    p_intercept: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Intercept with probability `p_intercept`, otherwise let the qubit pass."""
    if rng.random() < p_intercept:
        return intercept_resend_bb84(state, rng)
    return state


# ============================================================
# Per-round randomness, drawn once and shared by both backends
# ============================================================

@dataclass
class RoundDraws:
    """Every random number the rounds need, as one array per quantity.

    Drawing these up front is what makes the two backends comparable: both consume
    the *same* numbers, so a disagreement is a logic error rather than a different
    stream. It is also what makes the vectorized path fast, since one
    `random(n)` call replaces `n` scalar calls.

    The layout is grouped by kind, which is why it does not reproduce the looped
    path's historical stream -- see the module docstring. The `noise_*` and
    `eve_*` entries are drawn whenever the corresponding branch is enabled, for
    every round, rather than only for the rounds where the branch fires; a
    conditional draw would reintroduce a per-round variable-length dependency and
    with it the loop.
    """

    n_bits: int
    bits: np.ndarray
    basis_uniforms: np.ndarray
    bob_basis_uniforms: np.ndarray
    bob_measure_uniforms: np.ndarray
    noise_uniforms: np.ndarray | None = None
    noise_real: np.ndarray | None = None
    noise_imag: np.ndarray | None = None
    eve_basis_uniforms: np.ndarray | None = None
    eve_measure_uniforms: np.ndarray | None = None
    partial_uniforms: np.ndarray | None = None


def draw_rounds(
    rng: np.random.Generator,
    n_bits: int,
    noise_type: str = "none",
    attack_type: str = "none",
) -> RoundDraws:
    """Draw every random number the run needs, grouped by quantity."""
    draws = RoundDraws(
        n_bits=n_bits,
        bits=rng.integers(0, 2, size=n_bits),
        basis_uniforms=rng.random(n_bits),
        bob_basis_uniforms=rng.random(n_bits),
        bob_measure_uniforms=rng.random(n_bits),
    )
    if noise_type == "depolarizing":
        draws.noise_uniforms = rng.random(n_bits)
        draws.noise_real = rng.standard_normal((n_bits, 2))
        draws.noise_imag = rng.standard_normal((n_bits, 2))
    if attack_type == "intercept_resend":
        draws.eve_basis_uniforms = rng.random(n_bits)
        draws.eve_measure_uniforms = rng.random(n_bits)
    elif attack_type == "partial_intercept":
        draws.partial_uniforms = rng.random(n_bits)
        draws.eve_basis_uniforms = rng.random(n_bits)
        draws.eve_measure_uniforms = rng.random(n_bits)
    return draws


# ============================================================
# The round logic, once, over arrays
# ============================================================

def _encode_batch(bits: np.ndarray, is_z: np.ndarray) -> np.ndarray:
    """`(n, 2)` states: `|b>` in Z, `(+/-)` in X.

    In Z the state is `|b>`, so the amplitude goes in slot `b` -- writing it to
    slot 0 unconditionally, which an earlier revision did, encodes every Z round
    as bit 0 and shows up immediately as a 0.25 QBER on an ideal channel.
    """
    states = np.zeros((bits.shape[0], 2), dtype=complex)
    z = is_z
    states[z, bits[z]] = 1.0
    x = ~is_z
    states[x, 0] = _SQRT_HALF
    states[x, 1] = np.where(bits[x] == 0, _SQRT_HALF, -_SQRT_HALF)
    return states


def _measure_batch(
    states: np.ndarray, is_z: np.ndarray, uniforms: np.ndarray
) -> np.ndarray:
    """Measure each state in its basis, using one uniform per round.

    `rng.choice([0, 1], p=[p0, p1])` returns 0 exactly when a uniform draw is
    below `p0` (measured, not assumed), so a threshold reproduces it and stays
    vectorizable.
    """
    amp0 = np.where(is_z, states[:, 0], (states[:, 0] + states[:, 1]) * _SQRT_HALF)
    amp1 = np.where(is_z, states[:, 1], (states[:, 0] - states[:, 1]) * _SQRT_HALF)
    probabilities = np.abs(amp0) ** 2 + np.abs(amp1) ** 2
    p0 = np.abs(amp0) ** 2 / probabilities
    return (uniforms >= p0).astype(np.int64)


def simulate_vectorized(
    draws: RoundDraws,
    noise_type: str = "none",
    noise_param: float = 0.0,
    attack_type: str = "none",
    attack_param: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Run all rounds at once. Returns `(bits, bob_bits, bases_match)`."""
    is_z = draws.basis_uniforms < 0.5
    states = _encode_batch(draws.bits, is_z)

    if noise_type == "depolarizing":
        assert draws.noise_uniforms is not None
        assert draws.noise_real is not None
        assert draws.noise_imag is not None
        fired = draws.noise_uniforms <= noise_param
        if fired.any():
            vec = draws.noise_real + 1j * draws.noise_imag
            vec = vec / np.linalg.norm(vec, axis=1, keepdims=True)
            states[fired] = vec[fired]

    if attack_type in {"intercept_resend", "partial_intercept"}:
        assert draws.eve_basis_uniforms is not None
        assert draws.eve_measure_uniforms is not None
        eve_is_z = draws.eve_basis_uniforms < 0.5
        if attack_type == "intercept_resend":
            targeted = np.ones(draws.n_bits, dtype=bool)
        else:
            assert draws.partial_uniforms is not None
            targeted = draws.partial_uniforms < attack_param
        eve_bit = _measure_batch(states, eve_is_z, draws.eve_measure_uniforms)
        resent = _encode_batch(eve_bit, eve_is_z)
        states = np.where(targeted[:, None], resent, states)

    bob_is_z = draws.bob_basis_uniforms < 0.5
    bob_bits = _measure_batch(states, bob_is_z, draws.bob_measure_uniforms)

    # A basis mismatch is a normal half-the-time event, not evidence of
    # eavesdropping, so `bases_match` is what sifting keys on.
    return draws.bits, bob_bits, is_z == bob_is_z


def simulate_looped(
    draws: RoundDraws,
    noise_type: str = "none",
    noise_param: float = 0.0,
    attack_type: str = "none",
    attack_param: float = 0.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The same logic, one round at a time, over the *same* `RoundDraws`.

    This is the reference the vectorized path is checked against. It exists so
    that equivalence is a statement about the round logic rather than about the
    random-number generator, and it is not used by `run_bb84` unless asked for.
    """
    n = draws.n_bits
    bits = np.empty(n, dtype=np.int64)
    bob_bits = np.empty(n, dtype=np.int64)
    matches = np.empty(n, dtype=bool)

    for i in range(n):
        basis = "Z" if draws.basis_uniforms[i] < 0.5 else "X"
        bit = int(draws.bits[i])
        state = encode_bb84(bit, basis)

        if noise_type == "depolarizing":
            assert draws.noise_uniforms is not None
            if draws.noise_uniforms[i] <= noise_param:
                assert draws.noise_real is not None
                assert draws.noise_imag is not None
                vec = draws.noise_real[i] + 1j * draws.noise_imag[i]
                state = vec / np.linalg.norm(vec)

        if attack_type == "intercept_resend":
            pass_branch = True
        elif attack_type == "partial_intercept":
            assert draws.partial_uniforms is not None
            pass_branch = bool(draws.partial_uniforms[i] < attack_param)
        else:
            pass_branch = False

        if pass_branch:
            assert draws.eve_basis_uniforms is not None
            assert draws.eve_measure_uniforms is not None
            eve_basis = "Z" if draws.eve_basis_uniforms[i] < 0.5 else "X"
            eve_states = BASES[eve_basis]
            probs = np.array([abs(s.conj() @ state) ** 2 for s in eve_states])
            probs = probs / probs.sum()
            eve_bit = 0 if draws.eve_measure_uniforms[i] < probs[0] else 1
            state = encode_bb84(eve_bit, eve_basis)

        bob_basis = "Z" if draws.bob_basis_uniforms[i] < 0.5 else "X"
        bob_states = BASES[bob_basis]
        probs = np.array([abs(s.conj() @ state) ** 2 for s in bob_states])
        probs = probs / probs.sum()
        decoded = 0 if draws.bob_measure_uniforms[i] < probs[0] else 1

        bits[i] = bit
        bob_bits[i] = decoded
        matches[i] = basis == bob_basis

    return bits, bob_bits, matches


# ============================================================
# Simulation
# ============================================================

@dataclass
class BB84Result:
    """Result of a BB84 simulation run."""
    n_bits: int
    noise_type: str
    noise_param: float
    attack_type: str
    attack_param: float
    detection_threshold: float
    ber: float = 0.0                    # QBER on the sifted key
    detected: bool = False              # QBER above threshold -> abort
    detection_rate: float = 0.0         # run-level verdict as 0.0 / 1.0
    sifted_length: int = 0
    sifting_discard_rate: float = 0.0   # fraction of rounds dropped by sifting
    raw_errors: int = 0
    raw_basis_mismatches: int = 0


def run_bb84(
    n_bits: int = 1000,
    noise_type: str = "none",
    noise_param: float = 0.0,
    attack_type: str = "none",
    attack_param: float = 0.0,
    seed: int = 42,
    detection_threshold: float = DEFAULT_DETECTION_THRESHOLD,
    backend: str = "numpy",
) -> BB84Result:
    """
    Run a BB84 simulation.

    Alice encodes random bits in random bases. Bob measures in random bases.
    Only the cases where the bases match are kept (sifting). Errors are counted
    on the sifted key, and eavesdropping is reported when the sifted-key error
    rate exceeds `detection_threshold`.

    Parameters:
        n_bits: number of rounds to transmit
        noise_type: "none" or "depolarizing"
        noise_param: noise strength
        attack_type: "none", "intercept_resend", or "partial_intercept"
        attack_param: intercept probability, for "partial_intercept"
        seed: random seed
        detection_threshold: QBER above which the run reports eavesdropping
        backend: "numpy" (all rounds at once, the default) or "loop" (one round
            at a time). Both consume the same `RoundDraws` and agree exactly for
            identical draws; they do not share a random stream, so they differ on
            a common seed by binomial noise. See the module docstring.
    """
    if not isinstance(n_bits, (int, np.integer)) or n_bits < 1:
        raise ValueError("n_bits must be a positive integer")
    if noise_type not in {"none", "depolarizing"}:
        raise ValueError(
            f"noise_type must be one of ['depolarizing', 'none'], got {noise_type!r}"
        )
    if attack_type not in {"none", "intercept_resend", "partial_intercept"}:
        raise ValueError(
            "attack_type must be one of "
            f"['intercept_resend', 'none', 'partial_intercept'], got {attack_type!r}"
        )
    if backend not in {"numpy", "loop"}:
        raise ValueError(f"backend must be 'numpy' or 'loop', got {backend!r}")
    if noise_type == "depolarizing" and not 0.0 <= float(noise_param) <= 1.0:
        raise ValueError("noise_param must be between 0 and 1")
    if attack_type == "partial_intercept" and not 0.0 <= float(attack_param) <= 1.0:
        raise ValueError("attack_param must be between 0 and 1")
    if not 0.0 <= float(detection_threshold) <= 1.0:
        raise ValueError("detection_threshold must be between 0 and 1")

    rng = np.random.default_rng(seed)
    draws = draw_rounds(rng, int(n_bits), noise_type, attack_type)

    simulate = simulate_looped if backend == "loop" else simulate_vectorized
    bits, bob_bits, matched = simulate(
        draws,
        noise_type=noise_type,
        noise_param=noise_param,
        attack_type=attack_type,
        attack_param=attack_param,
    )

    sifted = int(matched.sum())
    mismatches = int(draws.n_bits - sifted)
    errors = int(np.count_nonzero(matched & (bob_bits != bits)))

    ber = errors / sifted if sifted > 0 else 0.0
    detected = sifted > 0 and ber > detection_threshold

    return BB84Result(
        n_bits=int(n_bits),
        noise_type=noise_type,
        noise_param=noise_param,
        attack_type=attack_type,
        attack_param=attack_param,
        detection_threshold=detection_threshold,
        ber=ber,
        detected=detected,
        detection_rate=1.0 if detected else 0.0,
        sifted_length=sifted,
        sifting_discard_rate=mismatches / int(n_bits),
        raw_errors=errors,
        raw_basis_mismatches=mismatches,
    )
