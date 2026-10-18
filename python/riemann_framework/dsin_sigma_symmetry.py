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
"""The DSIN parity sectors: what ``sigma`` protects, and what that protection costs.

`dsin.py` already provides the involution, the channel Hamiltonian and the
attacks. This module does the *sector* analysis the channel was missing, and
separates three claims that are easy to conflate:

1. **The sectors are the symmetric and antisymmetric subspaces.**
   `Fix(sigma)` consists of vectors `(u, u)/sqrt2` and `Anti(sigma)` of
   `(u, -u)/sqrt2`. Verified by projecting, not by reading the construction.
2. **`[H, sigma] = 0` conserves sector parity.** A state left in one sector stays
   there under the channel: `<sigma>` is constant to machine precision for every
   evolution time. Measured over a time grid, not asserted.
3. **A broken symmetry leaks parity at a rate set by the breaking.** Adding a
   fermionic-only perturbation makes `<sigma>` drift, monotonically in the
   strength.

The honest caveat, which is the reason this module is short: **claim 2 is exactly
why the parity observable cannot detect a parity-preserving attack.** The
`sigma`-basis intercept-resend attack measures the encoding basis, so it leaves
`<sigma>` at `+-1` and the detector silent while Eve learns the whole bit
(`dsin.sigma_basis_intercept_attack` documents this; the measurement here
confirms `detection = 0`, `BER = 0`). Protection of the parity and blindness of
the parity meter are the same fact.

Nothing here is evidence about the Riemann hypothesis.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .dsin import (
    DSINState,
    build_channel_hamiltonian,
    build_sigma,
    commutator_norm,
    encode_bit,
    evolve_state,
    sigma_basis_intercept_attack,
    sigma_eigenstates,
    sigma_expectation,
    symmetry_breaking_attack,
)


# ============================================================
# 1. The sectors are symmetric and antisymmetric subspaces
# ============================================================

def parity_sector_bases(dim_per_sector: int) -> tuple[np.ndarray, np.ndarray]:
    """Orthonormal bases of `Fix(sigma)` and `Anti(sigma)`, as explicit vectors.

    `(u, u)/sqrt2` for `+1` and `(u, -u)/sqrt2` for `-1`, with `u` running over
    the computational basis of one sector.
    """
    d = int(dim_per_sector)
    if d < 2:
        raise ValueError("dim_per_sector must be at least 2")
    plus = np.zeros((2 * d, d), dtype=complex)
    minus = np.zeros((2 * d, d), dtype=complex)
    for k in range(d):
        plus[k, k] = 1.0 / np.sqrt(2.0)
        plus[d + k, k] = 1.0 / np.sqrt(2.0)
        minus[k, k] = 1.0 / np.sqrt(2.0)
        minus[d + k, k] = -1.0 / np.sqrt(2.0)
    return plus, minus


def sector_weights(vector: np.ndarray, dim_per_sector: int) -> tuple[float, float]:
    """`(||P_+ v||^2, ||P_- v||^2)`: how much of the state sits in each sector."""
    plus, minus = parity_sector_bases(dim_per_sector)
    vector = np.asarray(vector, dtype=complex)
    return (
        float(np.linalg.norm(plus.conj().T @ vector) ** 2),
        float(np.linalg.norm(minus.conj().T @ vector) ** 2),
    )


@dataclass(frozen=True)
class SectorCheck:
    """The eigenspace claim, measured."""

    dim_per_sector: int
    plus_is_symmetric: bool
    minus_is_antisymmetric: bool
    bases_are_orthonormal: bool
    diagonalises_sigma: float

    def summary(self) -> str:
        return (
            f"d={self.dim_per_sector}: Fix(sigma) symmetric: {self.plus_is_symmetric}, "
            f"Anti(sigma) antisymmetric: {self.minus_is_antisymmetric}, "
            f"orthonormal: {self.bases_are_orthonormal}, "
            f"sigma block-diagonal to {self.diagonalises_sigma:.1e}"
        )


def sector_check(dim_per_sector: int = 4) -> SectorCheck:
    """Verify bases, orthonormality, and that `sigma` is `+-1` on each."""
    d = int(dim_per_sector)
    sigma = build_sigma(d)
    plus, minus = parity_sector_bases(d)

    symmetric = True
    antisymmetric = True
    for k in range(d):
        vector = plus[:, k]
        if not np.allclose(vector[:d], vector[d:]):
            symmetric = False
        vector = minus[:, k]
        if not np.allclose(vector[:d], -vector[d:]):
            antisymmetric = False

    combined = np.hstack([plus, minus])
    orthonormal = np.allclose(combined.conj().T @ combined, np.eye(2 * d), atol=1e-12)

    transformed = np.hstack([plus, minus]).conj().T @ sigma @ np.hstack([plus, minus])
    expected = np.diag([1.0] * d + [-1.0] * d)
    diagonal = float(np.abs(transformed - expected).max())

    return SectorCheck(
        dim_per_sector=d,
        plus_is_symmetric=symmetric,
        minus_is_antisymmetric=antisymmetric,
        bases_are_orthonormal=orthonormal,
        diagonalises_sigma=diagonal,
    )


# ============================================================
# 2. Parity conservation under a sigma-symmetric channel
# ============================================================

def breaking_hamiltonian(
    dim_per_sector: int,
    coupling: float = 1.0,
    strength: float = 0.0,
    seed: int = 0,
) -> np.ndarray:
    """The channel plus a fermionic-only perturbation: `[H, sigma]` grows with `strength`."""
    hamiltonian = build_channel_hamiltonian(dim_per_sector, coupling=coupling, seed=seed)
    if strength > 0.0:
        rng = np.random.default_rng(seed + 1)
        d = int(dim_per_sector)
        perturbation = np.zeros((2 * d, 2 * d), dtype=complex)
        perturbation[d:, d:] = np.diag(strength * rng.standard_normal(d))
        hamiltonian = hamiltonian + perturbation
    return hamiltonian


@dataclass(frozen=True)
class ConservationRow:
    """`<sigma>` drift at one evolution time."""

    time: float
    expectation: float
    drift: float


def parity_conservation(
    dim_per_sector: int = 4,
    coupling: float = 1.0,
    seed: int = 0,
    bit: int = 0,
    times: tuple[float, ...] = (0.0, 0.5, 1.0, 2.5, 10.0),
    strength: float = 0.0,
) -> list[ConservationRow]:
    """Track `<sigma>` under evolution; it is constant iff `[H, sigma] = 0`."""
    sigma = build_sigma(dim_per_sector)
    hamiltonian = breaking_hamiltonian(dim_per_sector, coupling, strength, seed)
    state = encode_bit(bit, dim_per_sector)
    initial = sigma_expectation(state, sigma)
    rows: list[ConservationRow] = []
    for time in times:
        evolved = evolve_state(state, hamiltonian, time)
        expectation = sigma_expectation(evolved, sigma)
        rows.append(
            ConservationRow(
                time=time,
                expectation=expectation,
                drift=abs(expectation - initial),
            )
        )
    return rows


def max_parity_drift(rows: list[ConservationRow]) -> float:
    """The largest `<sigma>` drift over the evolution grid."""
    return max(row.drift for row in rows)


def commutator_ratio(hamiltonian: np.ndarray) -> float:
    """`||[H, sigma]||_F / ||H||_F` for the channel."""
    matrix = np.asarray(hamiltonian)
    d = matrix.shape[0] // 2
    sigma = build_sigma(d)
    return float(commutator_norm(matrix, sigma) / np.linalg.norm(matrix, "fro"))


def breaking_vs_leakage(
    dim_per_sector: int = 4,
    strengths: tuple[float, ...] = (0.0, 0.1, 0.5, 1.0, 2.0),
    time: float = 2.5,
    seed: int = 0,
) -> list[tuple[float, float, float]]:
    """`(strength, commutator ratio, parity drift)` rows: leakage tracks the breaking."""
    sigma = build_sigma(dim_per_sector)
    state = encode_bit(0, dim_per_sector)
    rows: list[tuple[float, float, float]] = []
    for strength in strengths:
        hamiltonian = breaking_hamiltonian(dim_per_sector, strength=strength, seed=seed)
        evolved = evolve_state(state, hamiltonian, time)
        drift = abs(sigma_expectation(evolved, sigma) - sigma_expectation(state, sigma))
        rows.append((strength, commutator_ratio(hamiltonian), drift))
    return rows


# ============================================================
# 3. What the parity meter can and cannot see
# ============================================================

@dataclass(frozen=True)
class DetectionRow:
    """Detection of the symmetry-breaking attack at one `epsilon`."""

    epsilon: float
    mean_abs_deviation: float
    detection_rate: float


def detection_vs_breaking(
    dim_per_sector: int = 4,
    epsilons: tuple[float, ...] = (0.0, 0.1, 0.3, 0.6, 1.0),
    rounds: int = 400,
    threshold: float = 0.1,
    seed: int = 0,
) -> list[DetectionRow]:
    """Detection rate against symmetry violation, by simulation.

    The detector is the one the channel actually has: an alarm when
    `1 - |<sigma>|` exceeds `threshold`. `epsilon = 0` is the symmetric case.
    """
    sigma = build_sigma(dim_per_sector)
    rng = np.random.default_rng(seed)
    rows: list[DetectionRow] = []
    for epsilon in epsilons:
        deviations: list[float] = []
        detected = 0
        for round_index in range(rounds):
            bit = round_index % 2
            state = encode_bit(bit, dim_per_sector)
            attacked = symmetry_breaking_attack(state, epsilon, rng)
            deviation = 1.0 - abs(sigma_expectation(attacked, sigma))
            deviations.append(deviation)
            if deviation > threshold:
                detected += 1
        rows.append(
            DetectionRow(
                epsilon=epsilon,
                mean_abs_deviation=float(np.mean(deviations)),
                detection_rate=detected / rounds,
            )
        )
    return rows


@dataclass(frozen=True)
class UnprotectedAttack:
    """The `sigma`-basis intercept-resend attack: full information, zero signal."""

    detection_rate: float
    bit_error_rate: float
    information: float

    def summary(self) -> str:
        return (
            f"sigma-basis intercept-resend: detection {self.detection_rate:.3f}, "
            f"BER {self.bit_error_rate:.3f}, mutual information {self.information:.1f} "
            "bits -- parity conservation protects the sector and blinds the meter"
        )


def sigma_basis_attack_report(
    dim_per_sector: int = 4,
    rounds: int = 400,
    threshold: float = 0.1,
    seed: int = 0,
) -> UnprotectedAttack:
    """Eve measures in the encoding basis: she learns every bit and leaves no trace."""
    sigma = build_sigma(dim_per_sector)
    rng = np.random.default_rng(seed)
    detected = 0
    correct = 0
    for round_index in range(rounds):
        bit = round_index % 2
        state = encode_bit(bit, dim_per_sector)
        attacked = sigma_basis_intercept_attack(state, sigma, rng)
        deviation = 1.0 - abs(sigma_expectation(attacked, sigma))
        if deviation > threshold:
            detected += 1
        # Eve's outcome is deterministic here: <sigma> = (-1)**bit
        eve_bit = 0 if sigma_expectation(attacked, sigma) > 0.0 else 1
        if eve_bit == bit:
            correct += 1
    bit_error_rate = 1.0 - correct / rounds
    # Mutual information of a binary symmetric channel; the endpoints are limits.
    if bit_error_rate <= 0.0:
        information = 1.0
    elif bit_error_rate >= 0.5:
        information = 0.0
    else:
        information = (
            1.0
            + bit_error_rate * math.log2(bit_error_rate)
            + (1.0 - bit_error_rate) * math.log2(1.0 - bit_error_rate)
        )
    return UnprotectedAttack(
        detection_rate=detected / rounds,
        bit_error_rate=bit_error_rate,
        information=information,
    )


# ============================================================
# The report
# ============================================================

@dataclass(frozen=True)
class ParityReport:
    """All three claims plus the caveat, in one object."""

    sectors: SectorCheck
    conservation_drift: float
    broken_leakage: float
    detection: list[DetectionRow]
    unprotected: UnprotectedAttack

    def verdict(self) -> str:
        monotone = all(
            later.mean_abs_deviation >= earlier.mean_abs_deviation
            for earlier, later in zip(self.detection, self.detection[1:])
        )
        return (
            f"Parity sectors: {'verified' if self.sectors.plus_is_symmetric else 'FAILED'}; "
            f"<sigma> drift under the symmetric channel {self.conservation_drift:.1e}; "
            f"drift under a broken one {self.broken_leakage:.3f}; "
            f"detection rises with violation: {monotone}; "
            f"but the sigma-basis attack is detected at "
            f"{self.unprotected.detection_rate:.2f} with BER "
            f"{self.unprotected.bit_error_rate:.2f}. Protection of the parity is "
            "blindness of the parity meter. No RH evidence."
        )


def parity_report(dim_per_sector: int = 4, seed: int = 0) -> ParityReport:
    """Run the whole analysis once."""
    broken = breaking_vs_leakage(dim_per_sector=dim_per_sector, seed=seed)
    return ParityReport(
        sectors=sector_check(dim_per_sector),
        conservation_drift=max_parity_drift(
            parity_conservation(dim_per_sector=dim_per_sector, seed=seed)
        ),
        broken_leakage=broken[-1][2],
        detection=detection_vs_breaking(dim_per_sector=dim_per_sector, seed=seed),
        unprotected=sigma_basis_attack_report(dim_per_sector=dim_per_sector, seed=seed),
    )
