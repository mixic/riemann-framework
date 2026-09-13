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
Dimension-Shift Involution Network (DSIN) – simulation framework.

This module simulates the DSIN quantum communication proposal:

  - A two-sector Hilbert space H = H_b ⊕ H_f
  - The involution sigma swaps the sectors
  - Information is encoded in the eigenvalue of sigma (+1 or -1)
  - The channel Hamiltonian H commutes with sigma
  - Eavesdropping breaks the symmetry and is detected

The simulation evaluates:
  1. Bit error rate (BER) under ideal conditions
  2. BER under depolarizing noise
  3. BER under eavesdropping (intercept-resend)
  4. Detection probability of eavesdropping
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional


def _validate_dimension(dim_per_sector: int) -> int:
    if not isinstance(dim_per_sector, (int, np.integer)):
        raise TypeError("dim_per_sector must be an integer")
    if dim_per_sector < 1:
        raise ValueError("dim_per_sector must be positive")
    return int(dim_per_sector)


def _validate_probability(value: float, name: str) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return value


# ============================================================
# Hilbert space and the involution sigma
# ============================================================

def build_sigma(dim_per_sector: int) -> np.ndarray:
    """
    Build the involution sigma on H = H_b ⊕ H_f.

    sigma swaps the two sectors:
        sigma |b, k> = |f, k>
        sigma |f, k> = |b, k>

    Properties:
        sigma^2 = I
        sigma^dagger = sigma
        eigenvalues are +1 and -1
    """
    d = _validate_dimension(dim_per_sector)
    n = 2 * d
    M = np.zeros((n, n), dtype=complex)
    for k in range(d):
        M[k, d + k] = 1.0
        M[d + k, k] = 1.0
    return M


def sigma_eigenstates(dim_per_sector: int):
    """
    Return the eigenstates of sigma, grouped by eigenvalue.

    Returns:
        plus_states:  eigenstates with eigenvalue +1  (encoded bit 0)
        minus_states: eigenstates with eigenvalue -1  (encoded bit 1)
    """
    M = build_sigma(dim_per_sector)
    eigenvalues, eigenvectors = np.linalg.eigh(M)
    plus = eigenvectors[:, np.isclose(eigenvalues, 1.0)]
    minus = eigenvectors[:, np.isclose(eigenvalues, -1.0)]
    return plus, minus


# ============================================================
# Channel Hamiltonian
# ============================================================

def build_channel_hamiltonian(
    dim_per_sector: int,
    coupling: float = 1.0,
    seed: Optional[int] = None,
) -> np.ndarray:
    """
    Build a channel Hamiltonian H that commutes with sigma.

    The Hamiltonian has the block form:
        H = [[ H_b ,  V  ],
             [ V^T ,  H_f ]]

    For [H, sigma] = 0, we need H_b = H_f and V = V^T.
    """
    rng = np.random.default_rng(seed)
    d = _validate_dimension(dim_per_sector)

    # Intra-sector Hamiltonian (same in both sectors for [H, sigma] = 0)
    A = rng.standard_normal((d, d))
    H_b = (A + A.T) / 2.0
    H_f = H_b.copy()

    # Inter-sector coupling (symmetric for [H, sigma] = 0)
    B = rng.standard_normal((d, d))
    V = coupling * (B + B.T) / 2.0

    n = 2 * d
    H = np.zeros((n, n), dtype=complex)
    H[:d, :d] = H_b
    H[d:, d:] = H_f
    H[:d, d:] = V
    H[d:, :d] = V.T
    return H


def evolve_state(state: DSINState, hamiltonian: np.ndarray, time: float) -> DSINState:
    """Evolve a DSIN state under a Hermitian Hamiltonian for ``time``."""
    hamiltonian = np.asarray(hamiltonian, dtype=complex)
    if hamiltonian.ndim != 2 or hamiltonian.shape[0] != hamiltonian.shape[1]:
        raise ValueError("hamiltonian must be a square matrix")
    if hamiltonian.shape[0] != len(state.vector):
        raise ValueError("hamiltonian dimension must match the state vector")
    if not np.allclose(hamiltonian, hamiltonian.conj().T):
        raise ValueError("hamiltonian must be Hermitian")
    if not np.isfinite(time):
        raise ValueError("time must be finite")

    eigenvalues, eigenvectors = np.linalg.eigh(hamiltonian)
    evolution = eigenvectors @ np.diag(np.exp(-1j * eigenvalues * time)) @ eigenvectors.conj().T
    vector = evolution @ state.vector
    return DSINState(bit=state.bit, vector=vector, sector_index=state.sector_index)


def commutator_norm(H: np.ndarray, sigma: np.ndarray) -> float:
    """Return the Frobenius norm of [H, sigma]."""
    return float(np.linalg.norm(H @ sigma - sigma @ H, "fro"))


# ============================================================
# Encoding and decoding
# ============================================================

@dataclass
class DSINState:
    """A DSIN encoded state."""
    bit: int                    # 0 or 1
    vector: np.ndarray          # state vector in H
    sector_index: int = 0       # which "k" within the sector


def encode_bit(bit: int, dim_per_sector: int, k: int = 0) -> DSINState:
    """
    Encode a classical bit into a sigma eigenstate.

    bit = 0  ->  (|b, k> + |f, k>) / sqrt(2)   (eigenvalue +1)
    bit = 1  ->  (|b, k> - |f, k>) / sqrt(2)   (eigenvalue -1)
    """
    d = _validate_dimension(dim_per_sector)
    if not isinstance(k, (int, np.integer)):
        raise TypeError("k must be an integer")
    if not 0 <= k < d:
        raise ValueError("k must be within the sector dimension")
    n = 2 * d
    vec = np.zeros(n, dtype=complex)

    if bit == 0:
        vec[k] = 1.0 / np.sqrt(2)
        vec[d + k] = 1.0 / np.sqrt(2)
    elif bit == 1:
        vec[k] = 1.0 / np.sqrt(2)
        vec[d + k] = -1.0 / np.sqrt(2)
    else:
        raise ValueError("Bit must be 0 or 1")

    return DSINState(bit=bit, vector=vec, sector_index=k)


def measure_sigma(
    state: DSINState,
    sigma: np.ndarray,
    rng: np.random.Generator | None = None,
) -> int:
    """
    Measure the involution eigenvalue.

    Returns the decoded bit (0 for +1, 1 for -1).
    """
    sigma = np.asarray(sigma, dtype=complex)
    if sigma.shape != (len(state.vector), len(state.vector)):
        raise ValueError("sigma dimension must match the state vector")
    if not np.allclose(sigma, sigma.conj().T):
        raise ValueError("sigma must be Hermitian")

    expectation = float(np.real(state.vector.conj() @ sigma @ state.vector))
    probability_plus = np.clip((1.0 + expectation) / 2.0, 0.0, 1.0)
    rng = np.random.default_rng() if rng is None else rng
    return 0 if rng.random() < probability_plus else 1


# ============================================================
# Noise models
# ============================================================

def apply_depolarizing_noise(
    state: DSINState,
    p: float,
    rng: np.random.Generator,
) -> DSINState:
    """
    Apply depolarizing noise with probability p.

    With probability p, the state is replaced by a random state
    in the full Hilbert space.
    """
    p = _validate_probability(p, "p")
    if rng.random() > p:
        return state

    n = len(state.vector)
    # Random normalized vector
    real = rng.standard_normal(n)
    imag = rng.standard_normal(n)
    vec = (real + 1j * imag)
    vec = vec / np.linalg.norm(vec)
    return DSINState(bit=state.bit, vector=vec, sector_index=state.sector_index)


def apply_phase_noise(
    state: DSINState,
    sigma_phase: float,
    rng: np.random.Generator,
) -> DSINState:
    """
    Apply a random phase to the fermionic sector.

    This simulates a channel that does NOT commute with sigma —
    a symmetry-breaking perturbation.
    """
    sigma_phase = float(sigma_phase)
    if not np.isfinite(sigma_phase):
        raise ValueError("sigma_phase must be finite")
    vec = state.vector.copy()
    d = len(vec) // 2
    phase = np.exp(1j * sigma_phase)
    vec[d:] = vec[d:] * phase
    return DSINState(bit=state.bit, vector=vec, sector_index=state.sector_index)


# ============================================================
# Eavesdropping models
# ============================================================

def intercept_resend_attack(
    state: DSINState,
    sigma: np.ndarray,
    rng: np.random.Generator,
) -> DSINState:
    """
    Simulate an intercept-resend attack.

    Eve measures the state in a random basis, then resends the
    post-measurement state. This breaks the sigma symmetry.
    """
    n = len(state.vector)

    # Eve measures in a random basis
    real = rng.standard_normal((n, n))
    imag = rng.standard_normal((n, n))
    A = real + 1j * imag
    Q, _ = np.linalg.qr(A)

    probabilities = np.abs(Q.conj().T @ state.vector) ** 2
    outcome = rng.choice(n, p=probabilities / probabilities.sum())
    projection = Q[:, outcome]
    amplitude = projection.conj() @ state.vector
    new_vec = amplitude * projection
    new_vec = new_vec / np.linalg.norm(new_vec)

    return DSINState(bit=state.bit, vector=new_vec, sector_index=state.sector_index)


def symmetry_breaking_attack(
    state: DSINState,
    epsilon: float,
    rng: np.random.Generator,
) -> DSINState:
    """
    Simulate an attack that applies a small symmetry-breaking
    perturbation to the state.
    """
    vec = state.vector.copy()
    d = len(vec) // 2
    # Mix the sectors
    mix = epsilon * (rng.standard_normal(d) + 1j * rng.standard_normal(d))
    vec[:d] = vec[:d] + mix / np.sqrt(d)
    vec[d:] = vec[d:] - mix / np.sqrt(d)
    vec = vec / np.linalg.norm(vec)
    return DSINState(bit=state.bit, vector=vec, sector_index=state.sector_index)


# ============================================================
# Simulation
# ============================================================

@dataclass
class SimulationResult:
    """Result of a DSIN simulation run."""
    n_bits: int
    noise_type: str
    noise_param: float
    attack_type: str
    attack_param: float
    ber: float = 0.0
    detection_rate: float = 0.0
    raw_errors: int = 0
    raw_detections: int = 0


def run_simulation(
    n_bits: int = 1000,
    dim_per_sector: int = 4,
    coupling: float = 1.0,
    noise_type: str = "none",
    noise_param: float = 0.0,
    attack_type: str = "none",
    attack_param: float = 0.0,
    seed: int = 42,
    channel_time: float = 1.0,
) -> SimulationResult:
    """
    Run a DSIN communication simulation.

    Parameters:
        n_bits: number of bits to transmit
        dim_per_sector: dimension of each sector
        coupling: inter-sector coupling strength
        noise_type: "none", "depolarizing", or "phase"
        noise_param: noise strength
        attack_type: "none", "intercept_resend", or "symmetry_breaking"
        attack_param: attack strength
        seed: random seed

    Returns:
        SimulationResult with BER and detection rate.
    """
    if not isinstance(n_bits, (int, np.integer)) or n_bits < 1:
        raise ValueError("n_bits must be a positive integer")
    d = _validate_dimension(dim_per_sector)
    noise_types = {"none", "depolarizing", "phase"}
    attack_types = {"none", "intercept_resend", "symmetry_breaking"}
    if noise_type not in noise_types:
        raise ValueError(f"noise_type must be one of {sorted(noise_types)}")
    if attack_type not in attack_types:
        raise ValueError(f"attack_type must be one of {sorted(attack_types)}")
    if not np.isfinite(coupling) or not np.isfinite(channel_time):
        raise ValueError("coupling and channel_time must be finite")
    if noise_type == "depolarizing":
        _validate_probability(noise_param, "noise_param")
    elif noise_type == "phase" and not np.isfinite(noise_param):
        raise ValueError("noise_param must be finite for phase noise")
    if attack_type == "symmetry_breaking" and attack_param < 0:
        raise ValueError("attack_param must be non-negative")

    rng = np.random.default_rng(seed)
    sigma = build_sigma(d)
    hamiltonian = build_channel_hamiltonian(
        d, coupling=coupling, seed=int(rng.integers(0, 2**31))
    )

    errors = 0
    detections = 0

    for _ in range(n_bits):
        # Alice encodes a random bit
        bit = int(rng.integers(0, 2))
        state = encode_bit(bit, d, k=0)

        state = evolve_state(state, hamiltonian, channel_time)

        # Apply noise
        if noise_type == "depolarizing":
            state = apply_depolarizing_noise(state, noise_param, rng)
        elif noise_type == "phase":
            state = apply_phase_noise(state, noise_param, rng)

        # Apply attack
        if attack_type == "intercept_resend":
            state = intercept_resend_attack(state, sigma, rng)
        elif attack_type == "symmetry_breaking":
            state = symmetry_breaking_attack(state, attack_param, rng)

        # Bob decodes
        decoded = measure_sigma(state, sigma, rng=rng)

        if decoded != bit:
            errors += 1

        # Detection: check whether the state is still a sigma eigenstate
        expectation = np.real(state.vector.conj() @ sigma @ state.vector)
        if abs(abs(expectation) - 1.0) > 1e-6:
            detections += 1

    ber = errors / n_bits
    detection_rate = detections / n_bits

    return SimulationResult(
        n_bits=n_bits,
        noise_type=noise_type,
        noise_param=noise_param,
        attack_type=attack_type,
        attack_param=attack_param,
        ber=ber,
        detection_rate=detection_rate,
        raw_errors=errors,
        raw_detections=detections,
    )