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

This is a baseline for comparison, not a security proof; see
`docs/dimension_shift_quantum_communication.md`.
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
    if noise_type == "depolarizing" and not 0.0 <= float(noise_param) <= 1.0:
        raise ValueError("noise_param must be between 0 and 1")
    if attack_type == "partial_intercept" and not 0.0 <= float(attack_param) <= 1.0:
        raise ValueError("attack_param must be between 0 and 1")
    if not 0.0 <= float(detection_threshold) <= 1.0:
        raise ValueError("detection_threshold must be between 0 and 1")

    rng = np.random.default_rng(seed)

    errors = 0
    mismatches = 0
    sifted = 0

    for _ in range(n_bits):
        bit = int(rng.integers(0, 2))
        basis = random_basis(rng)
        state = encode_bb84(bit, basis)

        # Noise
        if noise_type == "depolarizing":
            state = apply_depolarizing_noise_bb84(state, noise_param, rng)

        # Attack
        if attack_type == "intercept_resend":
            state = intercept_resend_bb84(state, rng)
        elif attack_type == "partial_intercept":
            state = partial_intercept_resend_bb84(state, attack_param, rng)

        # Bob measures in a random basis
        bob_basis = random_basis(rng)
        bob_bit = measure_bb84(state, bob_basis, rng)

        # Sifting: keep only when the bases match. A mismatch is a normal
        # half-the-time event, not evidence of eavesdropping.
        if basis == bob_basis:
            sifted += 1
            if bob_bit != bit:
                errors += 1
        else:
            mismatches += 1

    ber = errors / sifted if sifted > 0 else 0.0
    detected = sifted > 0 and ber > detection_threshold

    return BB84Result(
        n_bits=n_bits,
        noise_type=noise_type,
        noise_param=noise_param,
        attack_type=attack_type,
        attack_param=attack_param,
        detection_threshold=detection_threshold,
        ber=ber,
        detected=detected,
        detection_rate=1.0 if detected else 0.0,
        sifted_length=sifted,
        sifting_discard_rate=mismatches / n_bits,
        raw_errors=errors,
        raw_basis_mismatches=mismatches,
    )
