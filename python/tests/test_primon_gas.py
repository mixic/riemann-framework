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
Tests for the primon gas and operator-level screening.

The central test here is a recorded negative result: the natural lift of the
dimension-shift involution onto `l^2(N)` -- swapping two primes' exponents --
provably cannot commute with the primon Hamiltonian, and the numbers are
recorded so that the failure is visible rather than asserted.
"""

import numpy as np
import pytest

from riemann_framework.operator_symmetry import (
    build_prime_swap_involution,
    build_prime_swap_permutation,
    commutator_norm,
    commutator_scaling,
    is_truncation_safe,
    screen_operator,
)
from riemann_framework.primon_gas import (
    factorize,
    hamiltonian_diagonal,
    primon_hamiltonian,
    trace_convergence,
    trace_exp,
    zeta_reference,
)


# ============================================================
# Factorisation
# ============================================================

@pytest.mark.parametrize(
    "n,expected",
    [
        (1, {}),
        (2, {2: 1}),
        (12, {2: 2, 3: 1}),
        (30, {2: 1, 3: 1, 5: 1}),
        (64, {2: 6}),
        (97, {97: 1}),
        (360, {2: 3, 3: 2, 5: 1}),
        (1024, {2: 10}),
        (7919, {7919: 1}),  # prime
    ],
)
def test_factorize(n, expected):
    assert factorize(n) == expected


def test_factorize_rejects_non_positive():
    for bad in (0, -5):
        with pytest.raises(ValueError):
            factorize(bad)


def test_factorize_reconstructs_the_integer():
    for n in range(1, 500):
        product = 1
        for prime, exponent in factorize(n).items():
            product *= prime**exponent
        assert product == n


# ============================================================
# The exact trace statement
# ============================================================

def test_truncated_trace_converges_to_zeta():
    """Tr_N[e^{-sH}] -> zeta(s) for Re(s) > 1.

    This is the whole reason the primon gas is worth having: the claim is a
    convergence statement, not a resemblance claim.
    """
    result = trace_convergence(2.0, truncations=(10, 100, 1_000, 10_000, 100_000))

    assert result["errors_decrease"]
    # error behaves like ~0.6/N for s = 2, so N = 1e5 is already at 1e-5
    assert result["relative_errors"][-1] < 1e-5
    assert abs(result["zeta_reference"] - 1.6449340668482264) < 1e-12


def test_zeta_two_is_pi_squared_over_six():
    import math

    assert abs(zeta_reference(2.0) - math.pi**2 / 6) < 1e-12


def test_trace_exp_is_the_dirichlet_partial_sum():
    assert abs(trace_exp(2, 3) - (1.0 + 0.25 + 1.0 / 9.0)) < 1e-12


def test_trace_convergence_refuses_the_non_convergent_half_plane():
    """The series diverges for Re(s) <= 1; returning a number would be a lie."""
    for bad in (0.5 + 14j, 1.0 + 0j, -3.0):
        with pytest.raises(ValueError):
            trace_convergence(bad)


# ============================================================
# The Hamiltonian
# ============================================================

def test_hamiltonian_is_evaluation_of_log():
    h = hamiltonian_diagonal(5)
    expected = np.log(np.array([1.0, 2.0, 3.0, 4.0, 5.0]))
    assert np.allclose(h, expected)
    assert h[0] == 0.0


def test_hamiltonian_has_simple_spectrum():
    """Distinct eigenvalues are what force the commutant to be diagonal."""
    eigenvalues = np.linalg.eigvalsh(primon_hamiltonian(500))
    assert len(np.unique(np.round(eigenvalues, 12))) == 500


# ============================================================
# The recorded negative result
# ============================================================

def test_prime_swap_does_not_commute_with_primon_hamiltonian():
    """The natural lift of sigma onto l^2(N) fails, and fails structurally.

    Swapping the exponents of 2 and 3 is the most natural way to give the
    dimension-shift involution arithmetic content. It cannot work: H has
    simple spectrum, so anything commuting with it is diagonal, and this
    permutation is not.
    """
    n_max = 500
    W = build_prime_swap_involution(n_max, p1=2, p2=3)
    verdict = screen_operator(W, n_max)

    assert verdict["verdict"] == "does_not_commute"
    assert not verdict["commutes"]
    assert not verdict["is_diagonal"]
    assert verdict["commutator_norm"] > 1e-8


def test_commutator_does_not_vanish_as_truncation_grows():
    """Separates a structural failure from a truncation artefact.

    A boundary artefact would decay with N; this stays bounded away from zero.
    """
    scaling = commutator_scaling(p1=2, p2=3, sizes=(200, 500, 1000, 2000))

    assert scaling["does_not_vanish"]
    norms = scaling["norms"]
    assert min(norms) > 1e-8
    # not shrinking toward zero: the smallest large-N value is at least a
    # sizeable fraction of the smallest value overall
    assert min(norms[2:]) > 0.1 * max(norms)


@pytest.mark.parametrize("p1,p2", [(2, 3), (2, 5), (3, 7), (5, 11)])
def test_any_prime_pair_fails(p1, p2):
    """Not a bad choice of primes -- the obstruction is basis-independent."""
    n_max = 300
    W = build_prime_swap_involution(n_max, p1, p2)
    assert commutator_norm(W, n_max) > 1e-8


def test_identity_commutes_as_a_control():
    """Control: the one operator that must commute does."""
    verdict = screen_operator(np.eye(200), 200)
    assert verdict["commutes"]
    assert verdict["is_diagonal"]


def test_a_diagonal_involution_commutes():
    """A basis-preserving involution is not obstructed -- the failure is about
    moving weight between distinct basis vectors, not about being an
    involution."""
    n_max = 64
    diagonal = np.diag(np.array([1.0 if i % 2 == 0 else -1.0 for i in range(n_max)]))
    verdict = screen_operator(diagonal, n_max)
    assert verdict["commutes"]


# ============================================================
# The permutation itself
# ============================================================

def test_prime_swap_permutation_is_involutive_when_truncation_safe():
    """When every partner stays inside the truncation it really is an involution."""
    n_max = 64  # 2^6 and 3^3 = 27 < 64, and swaps stay in range
    permutation = build_prime_swap_permutation(n_max, 2, 3)
    assert np.array_equal(permutation[permutation], np.arange(n_max))


def test_prime_swap_moves_numbers_as_described():
    # 6 = 2 * 3  ->  3 * 2 = 6 (fixed)
    # 12 = 2^2 * 3  ->  2 * 3^2 = 18
    # 8 = 2^3  ->  3^3 = 27
    permutation = build_prime_swap_permutation(100, 2, 3)
    assert permutation[6 - 1] == 6 - 1
    assert permutation[12 - 1] == 18 - 1
    assert permutation[8 - 1] == 27 - 1


def test_untouched_numbers_are_fixed():
    """Numbers coprime to both primes are left alone."""
    permutation = build_prime_swap_permutation(100, 2, 3)
    for n in (1, 5, 7, 25, 35, 49):
        assert permutation[n - 1] == n - 1


def test_is_truncation_safe_flags_onward_range():
    """Truncation safety essentially never holds for small primes.

    `8 = 2^3` wants to move to `3^3 = 27`, so any `n_max >= 8` is already
    unsafe for the (2, 3) swap. This is worth asserting rather than
    discovering later: it means the finite commutator norm describes a
    boundary-corrected map, not the intended one.
    """
    assert is_truncation_safe(3, 2, 3)
    assert is_truncation_safe(1, 2, 3)
    for n_max in (8, 20, 64, 500, 2000):
        assert not is_truncation_safe(n_max, 2, 3)


def test_boundary_artifact_is_quantified_not_hidden():
    """Some basis vectors are pinned in place by the truncation boundary.

    The structural argument does not depend on this, but the *numeric* value
    of the commutator does, so the artifact is measured and reported instead
    of being quietly absorbed.
    """
    n_max = 2000
    permutation = build_prime_swap_permutation(n_max, 2, 3)
    moved = int(np.sum(permutation != np.arange(n_max)))
    pinned = n_max - moved - _count_coprime_to(n_max, 2, 3)

    # a substantial number genuinely move, and a substantial number are
    # boundary-corrected -- neither is negligible at this size
    assert moved > 500
    assert pinned > 100
    # yet the commutator is still nonzero and large
    assert commutator_norm(build_prime_swap_involution(n_max, 2, 3), n_max) > 1.0


def _count_coprime_to(n_max: int, p1: int, p2: int) -> int:
    from riemann_framework.primon_gas import factorize as _factorize

    return sum(
        1
        for n in range(1, n_max + 1)
        if p1 not in _factorize(n) and p2 not in _factorize(n)
    )


def test_distinct_primes_required():
    with pytest.raises(ValueError):
        build_prime_swap_permutation(10, 3, 3)


def test_shape_mismatch_rejected():
    with pytest.raises(ValueError):
        commutator_norm(np.eye(3), 5)
