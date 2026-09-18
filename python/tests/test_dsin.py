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
"""Tests for the DSIN quantum communication simulation and the BB84 baseline."""

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
    sigma_eigenvalues,
    sigma_expectation,
    symmetry_breaking_attack,
)
from riemann_framework.bb84 import run_bb84


# ============================================================
# Algebra
# ============================================================

def test_sigma_is_involution():
    """sigma^2 = identity."""
    sigma = build_sigma(dim_per_sector=4)
    assert np.allclose(sigma @ sigma, np.eye(sigma.shape[0]))


def test_sigma_is_hermitian():
    """sigma is its own adjoint."""
    sigma = build_sigma(dim_per_sector=4)
    assert np.allclose(sigma, sigma.conj().T)


def test_sigma_eigenvalues():
    """Eigenvalues of sigma are +1 and -1."""
    eigs = sigma_eigenvalues(dim_per_sector=4)
    assert np.allclose(np.abs(eigs), 1.0)
    # The same statement from the matrix directly, so the helper cannot drift.
    assert np.allclose(np.abs(np.linalg.eigvalsh(build_sigma(4))), 1.0)


def test_sigma_eigenstates_split_by_eigenvalue():
    """The +/-1 eigenspaces each have dimension `dim_per_sector`."""
    plus, minus = sigma_eigenstates(dim_per_sector=4)
    assert plus.shape[1] == 4
    assert minus.shape[1] == 4


def test_channel_commutes_with_sigma():
    """[H, sigma] = 0 for the channel Hamiltonian."""
    for d in [2, 4, 6, 8]:
        H = build_channel_hamiltonian(d, coupling=1.0, seed=42)
        sigma = build_sigma(d)
        norm = commutator_norm(H, sigma)
        assert norm < 1e-10, f"[H, sigma] norm = {norm} for d = {d}"


# ============================================================
# Encoding
# ============================================================

def test_encode_decode_roundtrip():
    """Encoding and decoding should return the original bit."""
    sigma = build_sigma(dim_per_sector=4)
    for bit in [0, 1]:
        state = encode_bit(bit, dim_per_sector=4)
        decoded = measure_sigma(state, sigma)
        assert decoded == bit, f"Roundtrip failed for bit {bit}"


def test_sigma_expectation_ideal():
    """An encoded bit is an exact sigma eigenstate."""
    sigma = build_sigma(dim_per_sector=4)
    for bit in [0, 1]:
        state = encode_bit(bit, dim_per_sector=4)
        expectation = sigma_expectation(state, sigma)
        expected = 1.0 if bit == 0 else -1.0
        assert abs(expectation - expected) < 1e-10


def test_sigma_measurement_is_probabilistic_for_a_mixed_state():
    """A superposition gives non-deterministic outcomes over many samples."""
    sigma = build_sigma(1)
    state = encode_bit(0, dim_per_sector=1)
    state.vector = np.array([1.0, 0.0], dtype=complex)
    rng = np.random.default_rng(42)
    outcomes = [measure_sigma(state, sigma, rng=rng) for _ in range(1000)]

    assert 0.4 < np.mean(outcomes) < 0.6


# ============================================================
# Simulation
# ============================================================

def test_ideal_channel_no_errors():
    """Ideal channel: no errors, no detections, unit fidelity.

    Fidelity is compared with `np.isclose`, not `==`: an encoded state has
    `|<v|v>|^2 = 0.9999999999999996` in floating point, not exactly 1.
    """
    r = run_simulation(n_bits=200, seed=42)
    assert r.ber == 0.0, f"Ideal BER = {r.ber}, expected 0"
    assert r.detection_rate == 0.0, (
        f"Ideal detection = {r.detection_rate}, expected 0"
    )
    assert np.isclose(r.mean_fidelity, 1.0), (
        f"Ideal fidelity = {r.mean_fidelity}, expected 1"
    )


def test_hamiltonian_evolution_preserves_norm_and_sigma_eigenvalue():
    """The ideal commuting channel preserves the encoded sigma eigenvalue."""
    state = encode_bit(1, dim_per_sector=4)
    sigma = build_sigma(4)
    hamiltonian = build_channel_hamiltonian(4, coupling=2.0, seed=42)
    evolved = evolve_state(state, hamiltonian, time=3.0)

    assert np.isclose(np.linalg.norm(evolved.vector), 1.0)
    assert np.allclose(sigma @ evolved.vector, -evolved.vector)


def test_evolution_only_when_channel_time_is_nonzero():
    """`channel_time=0.0` (the default) means no evolution, hence unit fidelity."""
    r = run_simulation(n_bits=100, channel_time=0.0, seed=42)
    r_evolved = run_simulation(n_bits=100, channel_time=2.0, seed=42)
    assert np.isclose(r.mean_fidelity, 1.0)
    assert r_evolved.mean_fidelity < 1.0


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


def test_amplitude_damping_increases_ber_and_breaking_is_detected():
    """Amplitude damping attenuates one sector, so it breaks the symmetry."""
    r_clean = run_simulation(n_bits=200, seed=42)
    r_damped = run_simulation(
        n_bits=200, noise_type="amplitude", noise_param=0.5, seed=42
    )
    assert r_damped.ber >= r_clean.ber
    assert r_damped.detection_rate > 0.0, (
        "amplitude damping attenuates only the fermionic sector, so it must "
        "show up as a symmetry break"
    )


def test_symmetry_breaking_attack_disturbs_both_encodings():
    """Regression: the attack must not be blind to one of the two encoded bits.

    An earlier version perturbed the sectors by `+m` and `-m` with the *same*
    `m`. That vector is sigma-odd, so it lies in the `-1` eigenspace -- which is
    exactly the bit-1 encoding -- and left bit-1 states undisturbed to machine
    precision. The reported "detection rate" then tracked the fraction of
    bit-0 rounds (about 0.53) and did not respond to the attack strength at all.
    """
    sigma = build_sigma(4)
    rng = np.random.default_rng(42)
    for bit in [0, 1]:
        expectations = [
            abs(sigma_expectation(
                symmetry_breaking_attack(encode_bit(bit, 4), 0.5, rng), sigma))
            for _ in range(200)
        ]
        assert all(e < 1.0 - 1e-6 for e in expectations), (
            f"bit {bit} survived the symmetry-breaking attack undisturbed"
        )


def test_phase_noise_is_detected_away_from_the_eigenvalue_swap():
    """A phase of pi/2 leaves the state off the eigenspace, so it is caught."""
    r = run_simulation(
        n_bits=500, noise_type="phase", noise_param=np.pi / 2, seed=42
    )
    assert r.detection_rate > 0.9
    assert r.ber > 0.1


def test_phase_flip_at_pi_inverts_every_bit_and_is_invisible():
    """The unitary diag(I, -I) is a total, undetectable break of the protocol.

    Multiplying the fermionic sector by `e^{i phi}` sends the expectation value
    to `+-cos(phi)`. At `phi = pi` that maps the `+1` eigenspace onto the `-1`
    eigenspace, so the received state is still a `sigma` eigenstate -- of the
    *opposite* eigenvalue -- while `|<sigma>| = 1`, which is precisely what the
    detector tests. Every encoded bit is inverted and nothing is reported.

    This is a property of the protocol as modelled, not a coding error: the
    detector asks "is this still an eigenstate?", when the security-relevant
    question is "is it the *right* eigenstate?", and the receiver cannot tell
    without knowing the bit. The test pins the weakness so it cannot be lost
    silently; any redesign has to change this assertion deliberately.
    """
    r = run_simulation(
        n_bits=500, noise_type="phase", noise_param=np.pi, seed=42
    )
    assert r.ber == 1.0, f"BER = {r.ber}, expected every bit inverted"
    assert r.detection_rate == 0.0, (
        f"detection = {r.detection_rate}, expected the break to be invisible"
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


def test_intercept_resend_detected():
    """A full intercept-resend attack is caught every time, and disturbs about
    half the bits.

    Measured over 20 seeds at n=1000, the BER is 0.449 +/- 0.013, so the
    assertion is made on the mean over seeds rather than a single run: at
    n=200 the sampling noise (std about 0.035) alone would let a single seed
    dip below 0.4.
    """
    results = [
        run_simulation(n_bits=400, attack_type="intercept_resend", seed=seed)
        for seed in range(5)
    ]
    assert all(r.detection_rate > 0.9 for r in results), (
        f"detection rates = {[r.detection_rate for r in results]}, "
        f"expected near-certain"
    )
    mean_ber = float(np.mean([r.ber for r in results]))
    assert mean_ber > 0.35, (
        f"Mean BER = {mean_ber:.3f}, expected a heavy disturbance"
    )


def test_partial_intercept_scales_with_p():
    """Intercepting a larger fraction of the traffic costs more errors."""
    r_low = run_simulation(
        n_bits=500, attack_type="partial_intercept", attack_param=0.1, seed=42
    )
    r_high = run_simulation(
        n_bits=500, attack_type="partial_intercept", attack_param=0.9, seed=42
    )
    assert r_high.ber > r_low.ber, (
        f"BER at p=0.9 ({r_high.ber}) should exceed BER at p=0.1 ({r_low.ber})"
    )
    assert r_high.detection_rate > r_low.detection_rate


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_bits": 0},
        {"dim_per_sector": 0},
        {"noise_type": "unknown"},
        {"attack_type": "unknown"},
        {"noise_type": "depolarizing", "noise_param": 1.1},
        {"noise_type": "amplitude", "noise_param": 1.5},
        {"attack_type": "partial_intercept", "attack_param": 1.5},
    ],
)
def test_simulation_rejects_invalid_parameters(kwargs):
    """Reject invalid channel configuration instead of failing implicitly."""
    with pytest.raises((TypeError, ValueError)):
        run_simulation(**kwargs)


# ============================================================
# BB84 baseline
# ============================================================

def test_bb84_ideal_no_errors():
    """An untouched BB84 channel has no errors on the sifted key."""
    r = run_bb84(n_bits=500, seed=42)
    assert r.ber == 0.0
    assert not r.detected


def test_bb84_intercept_resend_detected():
    """Intercept-resend pushes the BB84 sifted-key error rate past the threshold."""
    r = run_bb84(n_bits=500, attack_type="intercept_resend", seed=42)
    assert r.ber > 0.2
    assert r.detected, (
        f"QBER = {r.ber:.3f} should exceed the {r.detection_threshold} threshold"
    )


def test_bb84_detection_is_not_basis_mismatch():
    """`detection_rate` must not simply report the sifting discard rate.

    Alice's and Bob's bases are independent and random, so they mismatch about
    half the time whether or not an eavesdropper is present. If `detection_rate`
    were derived from basis mismatch it would sit near 0.5 in the ideal case.
    """
    r = run_bb84(n_bits=1000, seed=42)
    assert r.detection_rate == 0.0, (
        f"ideal detection_rate = {r.detection_rate}; it must measure "
        f"eavesdropping, not basis mismatch"
    )
    assert 0.4 < r.sifting_discard_rate < 0.6, (
        f"sifting discard rate = {r.sifting_discard_rate}, expected about 0.5"
    )
