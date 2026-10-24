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
"""Tests for the dynamical desymmetriser.

The module's claims are of three kinds, and each has its own section here:

* invariants of the flow (spectrum, trace, Hermiticity, and the commutant of the
  involution) -- these are exact and are tested to rounding error;
* the behaviour of the flow from a state that is *not* symmetric -- the coherence
  decays and a sector is selected, which is a statement about the state;
* the negative result about the multi-copy circuit -- the quoted identity's first
  order term is not zero for any circuit this module can build, so the identity is
  reported as unverified rather than assumed.
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.desymmetrisation import sector_blocks
from riemann_framework.dimension_shift_chaos import (
    build_dimension_shift_hamiltonian,
    sector_swap,
)
from riemann_framework.dynamical_desymmetrisation import (
    FlowReport,
    commutator_norm,
    double_bracket,
    dynamical_desymmetrise,
    flow,
    sector_populations,
    two_copy_expansion,
    two_copy_step,
)


# ============================================================
# Fixtures: a sigma-symmetric model and two kinds of state
# ============================================================

DIMENSION = 3


@pytest.fixture(scope="module")
def model():
    dimension = DIMENSION
    hamiltonian = build_dimension_shift_hamiltonian(dimension, 1.0, "gue", seed=0)
    involution = sector_swap(dimension)
    dimension = 2 * DIMENSION
    return hamiltonian, involution, dimension


def _sector_state(hamiltonian, involution, sign: int, index: int) -> np.ndarray:
    """An eigenstate confined to one sector of `involution`."""
    dimension = hamiltonian.shape[0]
    projector = (np.eye(dimension) + sign * involution) / 2.0
    penalties = 1e6 * (np.eye(dimension) - projector)
    _, vectors = np.linalg.eigh(projector @ hamiltonian @ projector + penalties)
    return vectors[:, index]


@pytest.fixture(scope="module")
def symmetric_state(model):
    """`exp(-0.7 H)`: commutes with `H`, hence with the involution."""
    hamiltonian, _, _ = model
    values, vectors = np.linalg.eigh(hamiltonian)
    state = vectors @ np.diag(np.exp(-0.7 * values)) @ vectors.conj().T
    return state / np.real(np.trace(state))


@pytest.fixture(scope="module")
def cross_sector_state(model):
    """A superposition of one state in each sector: `[rho, sigma] != 0`."""
    hamiltonian, involution, _ = model
    first = _sector_state(hamiltonian, involution, +1, 0)
    second = _sector_state(hamiltonian, involution, -1, 0)
    vector = (first + second) / np.sqrt(2.0)
    return np.outer(vector, vector.conj())


# ============================================================
# The flow's invariants
# ============================================================

def test_the_increment_is_a_commutator_with_rho(model):
    """`2 rho H rho - H rho^2 - rho^2 H` is `[rho, [H, rho]]`, hence tangent."""
    hamiltonian, _, _ = model
    values, vectors = np.linalg.eigh(hamiltonian)
    state = vectors @ np.diag([0.5, 0.3, 0.2, 0.1, 0.05, 0.05]) @ vectors.conj().T

    increment = double_bracket(state, hamiltonian)
    commutator = state @ (hamiltonian @ state - state @ hamiltonian) - (
        hamiltonian @ state - state @ hamiltonian
    ) @ state
    assert np.allclose(increment, commutator, atol=1e-12)
    assert np.allclose(np.diag(increment).sum(), 0.0, atol=1e-12)


def test_the_flow_preserves_the_spectrum(model, cross_sector_state):
    """The isospectral claim, to rounding error, over a long run."""
    hamiltonian, involution, _ = model
    report = dynamical_desymmetrise(
        hamiltonian, involution, cross_sector_state, beta=15.0, steps=3000
    )
    assert report.spectrum_drift < 1e-10
    initial = np.sort(np.linalg.eigvalsh(cross_sector_state))
    final = np.sort(np.linalg.eigvalsh(report.final))
    assert np.allclose(initial, final, atol=1e-9)


def test_the_flow_preserves_trace_and_hermiticity(model, cross_sector_state):
    hamiltonian, involution, _ = model
    report = dynamical_desymmetrise(
        hamiltonian, involution, cross_sector_state, beta=10.0, steps=2000
    )
    assert report.trace_drift < 1e-10
    assert report.hermiticity_drift < 1e-10
    assert np.real(np.trace(report.final)) == pytest.approx(1.0, abs=1e-9)


def test_the_energy_expectation_decreases_in_the_descent_direction(model, cross_sector_state):
    """`direction = +1` is the descent direction of `tr(H rho)`, as documented."""
    hamiltonian, involution, _ = model
    down = dynamical_desymmetrise(hamiltonian, involution, cross_sector_state, beta=5.0, steps=1200)
    up = flow(
        cross_sector_state,
        hamiltonian,
        involutions=[involution],
        beta=5.0,
        steps=1200,
        direction=-1,
    )
    initial = float(np.real(np.trace(hamiltonian @ cross_sector_state)))
    assert float(np.real(np.trace(hamiltonian @ down.final))) < initial
    assert float(np.real(np.trace(hamiltonian @ up.final))) > initial


# ============================================================
# What the flow does with a symmetry
# ============================================================

def test_a_symmetric_state_keeps_its_sector_populations(model, symmetric_state):
    """**The invariance claim.** `[rho, sigma] = 0` is preserved, so populations are."""
    hamiltonian, involution, _ = model
    report = dynamical_desymmetrise(
        hamiltonian, involution, symmetric_state, beta=15.0, steps=3000
    )
    assert report.commutant_preserved
    assert report.coherences.max() < 1e-8
    baseline = report.sector_populations[0]
    assert np.abs(report.sector_populations - baseline).max() < 1e-8
    assert report.sector_populations[0].sum() == pytest.approx(1.0, abs=1e-9)


def test_a_cross_sector_state_is_pushed_into_one_sector(model, cross_sector_state):
    """**The measured behaviour.** Not invariance: the flow *selects* a sector."""
    hamiltonian, involution, _ = model
    report = dynamical_desymmetrise(
        hamiltonian, involution, cross_sector_state, beta=15.0, steps=3000
    )
    assert not report.commutant_preserved
    assert report.sector_selected
    assert report.coherences[0] > 1.0
    assert report.coherences[-1] < 0.01
    assert report.sector_populations[-1].max() > 0.99
    assert "selecting a sector" in report.summary()


def test_the_selection_is_not_the_hamiltonian_being_split(model, cross_sector_state):
    """The negative that matters: `H` is untouched, and the report says so."""
    hamiltonian, involution, _ = model
    before = hamiltonian.copy()
    report = dynamical_desymmetrise(hamiltonian, involution, cross_sector_state, beta=5.0, steps=800)
    assert np.array_equal(hamiltonian, before)
    # The sectors of H are what they always were, independent of the flow.
    blocks = sector_blocks(before, [involution])
    assert len(blocks) == 2
    assert "never acts on H" in report.invariant
    assert "never acts on H" in report.summary()


def test_populations_match_the_block_traces(model, symmetric_state):
    """A cross-check against the static split, not against the module itself."""
    hamiltonian, involution, _ = model
    blocks = sector_blocks(hamiltonian, [involution])
    populations = sector_populations(symmetric_state, [involution])
    sign_order = [(1,), (-1,)]
    for population, signs in zip(populations, sign_order):
        assert signs in blocks
        sector = (np.eye(hamiltonian.shape[0]) + signs[0] * involution) / 2.0
        expected = float(np.real(np.trace(sector @ symmetric_state)))
        assert population == pytest.approx(expected, abs=1e-10)
    assert populations.sum() == pytest.approx(1.0, abs=1e-9)


def test_commutator_norm_is_zero_for_a_symmetry(model):
    hamiltonian, involution, _ = model
    assert commutator_norm(hamiltonian, involution) < 1e-12
    broken = build_dimension_shift_hamiltonian(DIMENSION, 1.0, "gue", seed=0, sigma_breaking=0.5)
    assert commutator_norm(broken, involution) > 1e-3


# ============================================================
# The multi-copy circuit: the quoted identity, measured
# ============================================================

def test_the_difference_circuit_has_a_first_order_term(model, cross_sector_state):
    """**The negative result.** The quoted identity has no `sqrt(eps)` term; this does."""
    hamiltonian, _, _ = model
    expansion = two_copy_expansion(cross_sector_state, hamiltonian, generator="difference")
    assert not expansion.first_order_is_zero
    commutator = 1j * (hamiltonian @ cross_sector_state - cross_sector_state @ hamiltonian)
    assert np.allclose(expansion.first_order, commutator, atol=1e-6)


def test_no_candidate_circuit_reproduces_the_double_bracket(model, cross_sector_state):
    """All three generators: the second-order term is not `-[[rho, H], rho]`."""
    hamiltonian, _, _ = model
    for generator in ("difference", "swap", "split"):
        expansion = two_copy_expansion(cross_sector_state, hamiltonian, generator=generator)
        assert not expansion.first_order_is_zero, generator
        assert not expansion.second_order_matches_target, generator
        assert "second order is +/-[[rho,H],rho]: False" in expansion.summary()


def test_the_circuit_is_close_to_the_identity_for_small_epsilon(model, cross_sector_state):
    """Non-vacuity: the circuit does something, and it does it near the identity."""
    hamiltonian, _, _ = model
    evolved = two_copy_step(cross_sector_state, hamiltonian, 1e-8)
    assert np.allclose(evolved, cross_sector_state, atol=1e-3)


# ============================================================
# Validation
# ============================================================

def test_validation(model, symmetric_state):
    hamiltonian, involution, _ = model
    with pytest.raises(ValueError, match="square"):
        double_bracket(np.zeros((2, 3)), hamiltonian)
    with pytest.raises(ValueError, match="same shape"):
        double_bracket(np.eye(2), hamiltonian)
    with pytest.raises(ValueError, match="Hermitian"):
        flow(np.ones_like(hamiltonian) + 1j * np.eye(6), hamiltonian, beta=1.0, steps=10)
    with pytest.raises(ValueError, match="positive trace"):
        flow(-np.eye(6), hamiltonian, beta=1.0, steps=10)
    with pytest.raises(ValueError, match="involution"):
        flow(symmetric_state, hamiltonian, involutions=[np.zeros((6, 6))], beta=1.0, steps=10)
    with pytest.raises(ValueError, match="commute with the hamiltonian"):
        broken = build_dimension_shift_hamiltonian(DIMENSION, 1.0, "gue", seed=0, sigma_breaking=0.5)
        flow(symmetric_state, broken, involutions=[involution], beta=1.0, steps=10)
    with pytest.raises(ValueError, match="direction"):
        flow(symmetric_state, hamiltonian, direction=0, beta=1.0, steps=10)
    with pytest.raises(ValueError, match="at least two steps"):
        flow(symmetric_state, hamiltonian, steps=1)
    with pytest.raises(ValueError, match="beta must be positive"):
        flow(symmetric_state, hamiltonian, beta=-1.0, steps=10)


def test_circuit_validation(model, cross_sector_state):
    hamiltonian, _, _ = model
    with pytest.raises(ValueError, match="positive"):
        two_copy_step(cross_sector_state, hamiltonian, 0.0)
    with pytest.raises(ValueError, match="unknown generator"):
        two_copy_step(cross_sector_state, hamiltonian, 1e-4, generator="triple")
    with pytest.raises(ValueError, match="three epsilon scales"):
        two_copy_expansion(cross_sector_state, hamiltonian, scales=(1e-3, 1e-4))


def test_the_report_is_self_describing(model, cross_sector_state):
    hamiltonian, involution, _ = model
    report = dynamical_desymmetrise(hamiltonian, involution, cross_sector_state, beta=2.0, steps=400)
    assert isinstance(report, FlowReport)
    assert report.betas.shape == (401,)
    assert report.coherences.shape == (401,)
    assert report.sector_populations.shape == (401, 2)
    assert "coherence" in report.summary()
