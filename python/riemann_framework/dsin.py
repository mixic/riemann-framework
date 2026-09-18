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

The protected subspace is the fixed locus of sigma,
`Fix(sigma) = {|b,k> + |f,k>}/sqrt(2)` (bit 0), and the anti-fixed locus
`Anti(sigma) = {|b,k> - |f,k>}/sqrt(2)` carries bit 1. The channel Hamiltonian
commutes with sigma, so the sector parity is preserved by the ideal channel; a
channel or eavesdropper that breaks the symmetry moves the state out of the
eigenspace, which is what the detector measures.

The simulation evaluates:
  1. Bit error rate (BER) under ideal conditions
  2. BER under depolarizing, phase, and amplitude noise
  3. BER under eavesdropping (intercept-resend, symmetry-breaking,
     partial intercept-resend, and measurement in the encoding basis itself)
  4. Detection probability of eavesdropping, from the deviation of the state
     from a sigma eigenstate

Every numerical claim here is about a toy model. None of it constitutes a
security proof; see `docs/dimension_shift_quantum_communication.md`.
"""

# `evolve_state` below annotates its parameter and its return type as
# `DSINState`, but that class is defined further down the file. Without
# postponed evaluation Python evaluates annotations at function-definition time,
# so importing this module raised `NameError: name 'DSINState' is not defined` --
# which made `tests/test_dsin.py` fail at *collection*, not at assertion.
# Python 3.14 defers annotations by default (PEP 649), so this only bites on
# <= 3.13, including the CI's 3.12; that is exactly the kind of gap the CI job
# now covers. An AST scan confirms this is the only forward reference in the
# package, and `dsin.py` was the only module with one lacking this import.
from __future__ import annotations

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


def sigma_eigenvalues(dim_per_sector: int) -> np.ndarray:
    """Return the eigenvalues of sigma, which should all be ±1."""
    M = build_sigma(dim_per_sector)
    return np.linalg.eigvalsh(M)


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

    This is a projective measurement of sigma, so the outcome is drawn from the
    Born rule: the probability of +1 is ``(1 + <sigma>) / 2``. For a state that
    is exactly a sigma eigenstate the outcome is deterministic; for a state that
    has been disturbed off the eigenspace it is not. Use `sigma_expectation` for
    the deterministic expectation value the detector compares against.
    """
    sigma = np.asarray(sigma, dtype=complex)
    if sigma.shape != (len(state.vector), len(state.vector)):
        raise ValueError("sigma dimension must match the state vector")
    if not np.allclose(sigma, sigma.conj().T):
        raise ValueError("sigma must be Hermitian")

    expectation = sigma_expectation(state, sigma)
    probability_plus = np.clip((1.0 + expectation) / 2.0, 0.0, 1.0)
    rng = np.random.default_rng() if rng is None else rng
    return 0 if rng.random() < probability_plus else 1


def sigma_expectation(state: DSINState, sigma: np.ndarray) -> float:
    """Return the expectation value <sigma> of the state, deterministically."""
    return float(np.real(state.vector.conj() @ sigma @ state.vector))


def fidelity(state: DSINState, original: DSINState) -> float:
    """Return the fidelity |<state|original>|^2 between two states."""
    return float(abs(state.vector.conj() @ original.vector) ** 2)


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


def apply_amplitude_damping(
    state: DSINState,
    gamma: float,
    rng: np.random.Generator,
) -> DSINState:
    """
    Apply amplitude damping to the fermionic sector.

    This simulates energy loss in the channel. It is a symmetry-breaking
    perturbation, because it attenuates one sector and not the other.
    """
    gamma = _validate_probability(gamma, "gamma")
    vec = state.vector.copy()
    d = len(vec) // 2
    vec[d:] = vec[d:] * np.sqrt(1.0 - gamma)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
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


def sigma_basis_intercept_attack(
    state: DSINState,
    sigma: np.ndarray,
    rng: np.random.Generator,
) -> DSINState:
    """
    Eve measures in the *encoding* basis: she measures `sigma` itself.

    This is the attack that no single-basis protocol can survive, and it is the
    reason no entropic-uncertainty bound is available here (see
    `docs/dimension_shift_quantum_communication.md` section 4.4). In BB84 the
    analogous attack fails half the time: Alice chooses her basis privately, so
    Eve measuring `Z` disturbs every `X` round. DSIN encodes in one published
    basis, so the observable Eve measures is the observable Alice encoded in and
    the observable Bob decodes with. Her measurement is *always* the right one.

    Consequences, all exact rather than statistical:

    - Eve's outcome equals Alice's bit with probability 1, because the received
      state is a `sigma` eigenstate of eigenvalue `(-1)**bit` and a projective
      measurement of `sigma` on that eigenstate is deterministic. Her mutual
      information with the bit is a full bit.
    - The state she resends is the post-measurement state, which for an input
      already in the measured eigenspace is the input itself. So `|<sigma>| = 1`
      still holds, the detector stays silent, and Bob decodes correctly:
      `BER = 0` and `detection_rate = 0`.

    Full information, zero disturbance, zero detection -- and the same
    `1 - |<sigma>|` reading as a channel with no eavesdropper at all. That
    collision is what makes the observable unusable as a security statistic: two
    strategies with identical deviation and different leakage cannot be
    separated by any function of the deviation.
    """
    sigma = np.asarray(sigma, dtype=complex)
    if sigma.shape != (len(state.vector), len(state.vector)):
        raise ValueError("sigma dimension must match the state vector")
    if not np.allclose(sigma, sigma.conj().T):
        raise ValueError("sigma must be Hermitian")

    outcome = measure_sigma(state, sigma, rng=rng)
    n = len(state.vector)
    identity = np.eye(n, dtype=complex)
    projector = (identity + sigma) / 2.0 if outcome == 0 else (identity - sigma) / 2.0
    new_vec = projector @ state.vector
    norm = np.linalg.norm(new_vec)
    if norm > 0:
        new_vec = new_vec / norm
    return DSINState(bit=state.bit, vector=new_vec, sector_index=state.sector_index)


def symmetry_breaking_attack(
    state: DSINState,
    epsilon: float,
    rng: np.random.Generator,
) -> DSINState:
    """
    Simulate an attack that applies a symmetry-breaking perturbation.

    The two sectors are perturbed *independently*. This matters, and an earlier
    version of this function got it wrong: perturbing the sectors by `+m` and
    `-m` with the *same* `m` produces a sigma-*odd* vector, i.e. one lying in
    the `-1` eigenspace. Since the bit-1 encoding is exactly that eigenspace,
    such an attack leaves bit-1 states perfectly undisturbed -- `<sigma>` stays
    at `-1` to machine precision and the attack is invisible on half the
    traffic. The measured "detection rate" then just tracks the fraction of
    rounds that happened to encode bit 0, and does not respond to `epsilon` at
    all. Independent per-sector noise has both sigma-even and sigma-odd
    components, so it breaks the symmetry for both encoded bits.
    """
    if not np.isfinite(epsilon):
        raise ValueError("epsilon must be finite")
    vec = state.vector.copy()
    d = len(vec) // 2
    mix_boson = epsilon * (rng.standard_normal(d) + 1j * rng.standard_normal(d))
    mix_fermion = epsilon * (rng.standard_normal(d) + 1j * rng.standard_normal(d))
    vec[:d] = vec[:d] + mix_boson / np.sqrt(d)
    vec[d:] = vec[d:] + mix_fermion / np.sqrt(d)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return DSINState(bit=state.bit, vector=vec, sector_index=state.sector_index)


def partial_intercept_attack(
    state: DSINState,
    sigma: np.ndarray,
    p_intercept: float,
    rng: np.random.Generator,
) -> DSINState:
    """
    Partial intercept-resend attack.

    Eve intercepts with probability ``p_intercept``, and otherwise lets the
    state pass through unchanged. This is the realistic regime: an eavesdropper
    who intercepts only a fraction of the traffic trades a lower error rate for
    a lower chance of being caught.
    """
    p_intercept = _validate_probability(p_intercept, "p_intercept")
    if rng.random() < p_intercept:
        return intercept_resend_attack(state, sigma, rng)
    return state


# ============================================================
# Simulation
# ============================================================

@dataclass
class SimulationResult:
    """Result of a DSIN simulation run."""
    n_bits: int
    dim_per_sector: int
    coupling: float
    noise_type: str
    noise_param: float
    attack_type: str
    attack_param: float
    channel_time: float
    ber: float = 0.0
    detection_rate: float = 0.0
    raw_errors: int = 0
    raw_detections: int = 0
    mean_fidelity: float = 0.0
    # Mean of the graded statistic `1 - |<sigma>|`, i.e. the detector's input
    # before thresholding. Kept alongside the binary `detection_rate` so that a
    # caller can see that the threshold, not the observable, produces the step.
    # Stored as `|1 - |<sigma>||` rather than `1 - |<sigma>|`: the two agree for
    # any physical state since `|<sigma>| <= 1`, but `|<sigma>|` can round a few
    # ulps above 1, and the unsigned form then reports a small *negative*
    # deviation, which is not a distance. The `abs` is the same expression the
    # detector thresholds, so the two cannot drift apart.
    mean_sigma_deviation: float = 0.0


def run_simulation(
    n_bits: int = 1000,
    dim_per_sector: int = 4,
    coupling: float = 1.0,
    noise_type: str = "none",
    noise_param: float = 0.0,
    attack_type: str = "none",
    attack_param: float = 0.0,
    seed: int = 42,
    channel_time: float = 0.0,
) -> SimulationResult:
    """
    Run a DSIN communication simulation.

    Parameters:
        n_bits: number of bits to transmit
        dim_per_sector: dimension of each sector
        coupling: inter-sector coupling strength
        noise_type: "none", "depolarizing", "phase", or "amplitude"
        noise_param: noise strength
        attack_type: "none", "intercept_resend", "symmetry_breaking",
            "partial_intercept", or "sigma_basis_intercept". The last is the
            attack that measures the encoding observable itself; it recovers
            every bit with zero disturbance and zero detection.
        attack_param: attack strength
        seed: random seed
        channel_time: time for which the state evolves under the channel
            Hamiltonian before the noise and eavesdropper act. The default is
            `0.0`, i.e. no evolution, so that the ideal channel has unit
            fidelity; set it nonzero to include Hamiltonian evolution.

    Returns:
        SimulationResult with BER, detection rate, and mean fidelity.
    """
    if not isinstance(n_bits, (int, np.integer)) or n_bits < 1:
        raise ValueError("n_bits must be a positive integer")
    d = _validate_dimension(dim_per_sector)
    noise_types = {"none", "depolarizing", "phase", "amplitude"}
    attack_types = {
        "none", "intercept_resend", "symmetry_breaking", "partial_intercept",
        "sigma_basis_intercept",
    }
    if noise_type not in noise_types:
        raise ValueError(f"noise_type must be one of {sorted(noise_types)}")
    if attack_type not in attack_types:
        raise ValueError(f"attack_type must be one of {sorted(attack_types)}")
    if not np.isfinite(coupling) or not np.isfinite(channel_time):
        raise ValueError("coupling and channel_time must be finite")
    if noise_type in {"depolarizing", "amplitude"}:
        _validate_probability(noise_param, "noise_param")
    elif noise_type == "phase" and not np.isfinite(noise_param):
        raise ValueError("noise_param must be finite for phase noise")
    if attack_type == "symmetry_breaking" and attack_param < 0:
        raise ValueError("attack_param must be non-negative")
    if attack_type == "partial_intercept":
        _validate_probability(attack_param, "attack_param")

    rng = np.random.default_rng(seed)
    sigma = build_sigma(d)

    # The channel Hamiltonian is only needed when the state actually evolves.
    hamiltonian = None
    if channel_time:
        hamiltonian = build_channel_hamiltonian(
            d, coupling=coupling, seed=int(rng.integers(0, 2**31))
        )

    errors = 0
    detections = 0
    fidelities = []
    deviations = []

    for _ in range(n_bits):
        # Alice encodes a random bit
        bit = int(rng.integers(0, 2))
        original = encode_bit(bit, d, k=0)
        state = original

        if hamiltonian is not None:
            state = evolve_state(state, hamiltonian, channel_time)

        # Apply noise
        if noise_type == "depolarizing":
            state = apply_depolarizing_noise(state, noise_param, rng)
        elif noise_type == "phase":
            state = apply_phase_noise(state, noise_param, rng)
        elif noise_type == "amplitude":
            state = apply_amplitude_damping(state, noise_param, rng)

        # Apply attack
        if attack_type == "intercept_resend":
            state = intercept_resend_attack(state, sigma, rng)
        elif attack_type == "symmetry_breaking":
            state = symmetry_breaking_attack(state, attack_param, rng)
        elif attack_type == "partial_intercept":
            state = partial_intercept_attack(state, sigma, attack_param, rng)
        elif attack_type == "sigma_basis_intercept":
            state = sigma_basis_intercept_attack(state, sigma, rng)

        # Bob decodes
        decoded = measure_sigma(state, sigma, rng=rng)

        if decoded != bit:
            errors += 1

        # Detection: check whether the state is still a sigma eigenstate
        expectation = abs(sigma_expectation(state, sigma))
        deviation = abs(expectation - 1.0)
        deviations.append(deviation)
        if deviation > 1e-6:
            detections += 1

        fidelities.append(fidelity(state, original))

    ber = errors / n_bits
    detection_rate = detections / n_bits

    return SimulationResult(
        n_bits=n_bits,
        dim_per_sector=d,
        coupling=coupling,
        noise_type=noise_type,
        noise_param=noise_param,
        attack_type=attack_type,
        attack_param=attack_param,
        channel_time=channel_time,
        ber=ber,
        detection_rate=detection_rate,
        raw_errors=errors,
        raw_detections=detections,
        mean_fidelity=float(np.mean(fidelities)),
        mean_sigma_deviation=float(np.mean(deviations)),
    )
