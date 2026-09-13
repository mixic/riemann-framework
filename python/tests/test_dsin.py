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
"""Tests for the DSIN quantum communication simulation."""

import numpy as np
import pytest

from riemann_framework.dsin import (
    build_sigma,
    build_channel_hamiltonian,
    commutator_norm,
    encode_bit,
    evolve_state,
    measure_sigma,
    run_simulation,
    sigma_eigenstates,
)


def test_sigma_is_involution():
    """sigma^2 = identity."""
    sigma = build_sigma(dim_per_sector=4)
    assert np.allclose(sigma @ sigma, np.eye(sigma.shape[0]))


def test_sigma_eigenvalues():
    """Eigenvalues of sigma are +1 and -1."""
    sigma = build_sigma(dim_per_sector=4)
    eigenvalues = np.linalg.eigvalsh(sigma)
    assert np.allclose(np.abs(eigenvalues), 1.0)


def test_channel_commutes_with_sigma():
    """[H, sigma] = 0 for the channel Hamiltonian."""
    for d in [2, 4, 6]:
        H = build_channel_hamiltonian(d, coupling=1.0, seed=42)
        sigma = build_sigma(d)
        norm = commutator_norm(H, sigma)
        assert norm < 1e-10, f"[H, sigma] norm = {norm} for d = {d}"


def test_encode_decode_roundtrip():
    """Encoding and decoding should return the original bit."""
    sigma = build_sigma(dim_per_sector=4)
    for bit in [0, 1]:
        state = encode_bit(bit, dim_per_sector=4)
        decoded = measure_sigma(state, sigma)
        assert decoded == bit, f"Roundtrip failed for bit {bit}"


def test_ideal_channel_no_errors():
    """Ideal channel should give BER = 0."""
    r = run_simulation(n_bits=200, seed=42)
    assert r.ber == 0.0, f"Ideal BER = {r.ber}, expected 0"
    assert r.detection_rate == 0.0, (
        f"Ideal detection = {r.detection_rate}, expected 0"
    )


def test_attack_detected():
    """Symmetry-breaking attacks raise errors across repeated runs."""
    results = [
        run_simulation(
            n_bits=500,
            attack_type="symmetry_breaking",
            attack_param=0.5,
            seed=seed,
        )
        for seed in range(10)
    ]
    mean_detection = np.mean([result.detection_rate for result in results])
    mean_ber = np.mean([result.ber for result in results])

    assert mean_detection > 0.35, (
        f"Mean detection rate = {mean_detection:.3f}, expected a clear signal"
    )
    assert mean_ber > 0.05, f"Mean BER = {mean_ber:.3f}, expected a disturbance"


def test_noise_increases_ber():
    """Depolarizing noise should increase the bit error rate."""
    r_clean = run_simulation(n_bits=200, seed=42)
    r_noisy = run_simulation(
        n_bits=200,
        noise_type="depolarizing",
        noise_param=0.3,
        seed=42,
    )
    assert r_noisy.ber >= r_clean.ber, (
        f"Noisy BER = {r_noisy.ber}, clean BER = {r_clean.ber}"
    )


def test_hamiltonian_evolution_preserves_norm_and_sigma_eigenvalue():
    """The ideal commuting channel preserves the encoded sigma eigenvalue."""
    state = encode_bit(1, dim_per_sector=4)
    sigma = build_sigma(4)
    hamiltonian = build_channel_hamiltonian(4, coupling=2.0, seed=42)
    evolved = evolve_state(state, hamiltonian, time=3.0)

    assert np.isclose(np.linalg.norm(evolved.vector), 1.0)
    assert np.allclose(sigma @ evolved.vector, -evolved.vector)


def test_sigma_measurement_is_probabilistic_for_a_mixed_state():
    """A superposition gives non-deterministic outcomes over many samples."""
    sigma = build_sigma(1)
    state = encode_bit(0, dim_per_sector=1)
    state.vector = np.array([1.0, 0.0], dtype=complex)
    rng = np.random.default_rng(42)
    outcomes = [measure_sigma(state, sigma, rng=rng) for _ in range(1000)]

    assert 0.4 < np.mean(outcomes) < 0.6


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_bits": 0},
        {"dim_per_sector": 0},
        {"noise_type": "unknown"},
        {"attack_type": "unknown"},
        {"noise_type": "depolarizing", "noise_param": 1.1},
    ],
)
def test_simulation_rejects_invalid_parameters(kwargs):
    """Reject invalid channel configuration instead of failing implicitly."""
    with pytest.raises((TypeError, ValueError)):
        run_simulation(**kwargs)