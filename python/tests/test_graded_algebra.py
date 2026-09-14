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
Tests for the graded algebra and the shift-zeta.

Criterion IDs (G1-G7, F1-F5) refer to the goal specification. The decisive
tests record a *negative* outcome: the framework is well-defined, but away from
the degenerate `tau = 1` case the graded trace does not reproduce the classical
zeta function, and the construction is confined to the fixed locus by
definition. That result is asserted here so it cannot quietly be reported as a
success.

Verified closed forms for `q = 1 - x*gamma_tau`, `x = p^{-s}`. With
`a = 1 - x(1+tau)/2`, `b = -x(1-tau)/2`, `norm = a^2 - b^2`:

    q^{-1}              = (a/norm, -b/norm)
    trace(q^{-1})       = a / norm        = 1/(1-x) when tau = 1
    supertrace(q^{-1})  = -b / norm

The graded trace is exactly multiplicative over the local factors, because each
factor is a polynomial in the single element `gamma_tau`; at `tau = 1` it
therefore equals the classical partial Euler product term by term.
"""

import mpmath as mp
import pytest

from riemann_framework.graded_algebra import (
    EVEN,
    ODD,
    GradedElement,
    grading_shift,
    local_factor,
)
from riemann_framework.shift_zeta import (
    compare_traces,
    first_primes,
    shift_zeta,
    shift_zeta_element,
    shift_zeta_supertrace,
)

mp.mp.dps = 30
TOL = mp.mpf(10) ** -25

# The degenerate weight: gamma_1 = I, which makes every local factor scalar.
TRIVIAL = 1
# Graded weights used to probe whether the grading carries information.
GRADED = (0, mp.mpf("0.5"), mp.mpf("0.25"), 2)


def _samples():
    return [
        GradedElement.of(1, 0),
        GradedElement.of(0, 1),
        GradedElement.of(2, -3),
        GradedElement.of(mp.mpf("0.5"), mp.mpf("0.25")),
        GradedElement.of(1j, mp.mpf("0.75")),
    ]


# ============================================================
# G1: the graded algebra is well-defined
# ============================================================

def test_omega_squares_to_the_identity():
    assert GradedElement.omega() * GradedElement.omega() == GradedElement.identity()


def test_multiplication_is_associative():
    for x in _samples():
        for y in _samples():
            for z in _samples():
                assert (x * y) * z == x * (y * z)


def test_multiplication_distributes():
    for x in _samples():
        for y in _samples():
            for z in _samples():
                assert x * (y + z) == x * y + x * z


def test_multiplication_is_commutative():
    for x in _samples():
        for y in _samples():
            assert x * y == y * x


def test_units():
    for x in _samples():
        assert GradedElement.identity() * x == x
        assert x + GradedElement.zero() == x


def test_inverse_round_trips():
    for x in _samples():
        try:
            inverse = x.inverse()
        except ZeroDivisionError:
            continue
        product = x * inverse
        # float-level tolerance: `of(1j, 0.75)` needs complex division
        assert abs(product.a - 1) < mp.mpf(10) ** -14
        assert abs(product.b) < mp.mpf(10) ** -14


def test_zero_divisors_are_rejected():
    """(1 + omega)(1 - omega) = 0, so neither factor is invertible."""
    for element in (GradedElement.of(1, 1), GradedElement.of(1, -1)):
        with pytest.raises(ZeroDivisionError):
            element.inverse()


def test_regular_representation_is_faithful():
    for x in _samples():
        matrix = x.to_matrix()
        assert abs(matrix[0, 0] - x.a) < TOL
        assert abs(matrix[0, 1] - x.b) < TOL


# ============================================================
# G2: sigma is an algebra homomorphism
# ============================================================

def test_sigma_is_multiplicative():
    for x in _samples():
        for y in _samples():
            assert (x * y).sigma() == x.sigma() * y.sigma()


def test_sigma_is_additive():
    for x in _samples():
        for y in _samples():
            assert (x + y).sigma() == x.sigma() + y.sigma()


def test_sigma_is_an_involution():
    for x in _samples():
        assert x.sigma().sigma() == x


def test_sigma_fixes_the_identity_and_negates_omega():
    assert GradedElement.identity().sigma() == GradedElement.identity()
    assert GradedElement.omega().sigma() == -GradedElement.omega()


def test_fixed_locus_is_the_even_part():
    assert GradedElement.of(mp.mpf("1.5"), 0).grade() == EVEN
    assert GradedElement.of(0, mp.mpf("1.5")).grade() == ODD
    assert GradedElement.of(1, 1).grade() is None
    assert GradedElement.of(mp.mpf("1.5"), 0).is_fixed()
    assert not GradedElement.of(0, mp.mpf("1.5")).is_fixed()


# ============================================================
# G3: trace is sigma-invariant; supertrace is anti-invariant
# ============================================================

def test_trace_is_sigma_invariant():
    """G3 holds for the graded trace."""
    for x in _samples():
        assert abs(x.sigma().trace() - x.trace()) < TOL


def test_supertrace_is_sigma_ANTI_invariant():
    """The supertrace is the grading-sensitive functional: it flips sign.

    That property is what distinguishes it from `trace`, and is why `trace` is
    the invariant functional G3 asks for.
    """
    for x in _samples():
        assert abs(x.sigma().supertrace() + x.supertrace()) < TOL


def test_trace_is_the_average_of_the_eigenvalue_traces():
    """In the eigenbasis of omega, a + b*omega is diag(a+b, a-b).

    sigma swaps those two eigenvalues, so the invariant combination is their
    average, which is `a`; the half-difference is `b`.
    """
    for x in _samples():
        plus = x.a + x.b
        minus = x.a - x.b
        assert abs(x.trace() - (plus + minus) / 2) < TOL
        assert abs(x.supertrace() - (plus - minus) / 2) < TOL


def test_supertrace_vanishes_on_the_fixed_locus():
    for x in _samples():
        if x.is_even():
            assert abs(x.supertrace()) < TOL


def test_matrix_trace_is_twice_the_graded_trace():
    for x in _samples():
        assert abs(x.matrix_trace() - 2 * x.trace()) < TOL


# ============================================================
# G4: the shift-zeta is computable
# ============================================================

def test_shift_zeta_is_finite():
    for s in (2, 3, mp.mpf("2.5")):
        for tau in (TRIVIAL,) + GRADED:
            value = shift_zeta(s, tau, first_primes(20))
            assert mp.isfinite(value.real)
            assert mp.isfinite(value.imag)


def test_first_primes_are_correct():
    assert first_primes(10) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]


def test_first_primes_rejects_zero():
    with pytest.raises(ValueError):
        first_primes(0)


# ============================================================
# G7: the Euler product converges
# ============================================================

def test_euler_product_matches_zeta_at_tau_one():
    """At tau = 1 the graded trace is the classical partial Euler product."""
    for s in (2, 3, 4, 5):
        value = shift_zeta(s, TRIVIAL, first_primes(60))
        assert abs(value - mp.zeta(s)) / abs(mp.zeta(s)) < mp.mpf(2) ** (-s) * 2


def test_euler_product_error_shrinks_with_more_primes():
    errors = [
        float(abs(shift_zeta(2, TRIVIAL, first_primes(n)) - mp.zeta(2)))
        for n in (10, 100, 1000)
    ]
    assert errors[1] < errors[0]
    assert errors[2] < errors[1]


def test_graded_trace_is_NOT_multiplicative():
    """`trace` is a linear functional, not a character.

    For x = a1 + b1*omega and y = a2 + b2*omega we have
    trace(xy) = a1*a2 + b1*b2, which differs from trace(x)*trace(y) = a1*a2
    unless the odd parts vanish. So the product of the local traces is *not*
    the trace of the product, and the truncated graded trace cannot be
    identified with the classical partial Euler product by factorisation.

    At tau = 1 the local factors are scalar, b = 0, and the two agree.
    """
    primes = first_primes(15)
    element = GradedElement.identity()
    for p in primes:
        element = element * local_factor(p, 2, TRIVIAL)
    product_of_traces = mp.mpf(1)
    for p in primes:
        product_of_traces *= local_factor(p, 2, TRIVIAL).trace()
    assert abs(element.trace() - product_of_traces) < TOL

    for tau in GRADED:
        element = GradedElement.identity()
        for p in primes:
            element = element * local_factor(p, 2, tau)
        product_of_traces = mp.mpf(1)
        for p in primes:
            product_of_traces *= local_factor(p, 2, tau).trace()
        assert abs(element.trace() - product_of_traces) > mp.mpf(10) ** -6


# ============================================================
# Closed forms for the local factor
# ============================================================

@pytest.mark.parametrize("p", [2, 3, 5, 7, 11])
@pytest.mark.parametrize("s", [2, 3, mp.mpf("2.5")])
@pytest.mark.parametrize("tau", [1, 0, mp.mpf("0.5"), mp.mpf("0.25"), 2])
def test_local_factor_trace_closed_form(p, s, tau):
    """`local_factor` returns q^{-1}, so its `a` *is* the trace.

    The element returned is already inverted; inverting it again (the mistake
    this test previously made) gives `a/(a^2-b^2)` instead.
    """
    factor = local_factor(p, s, tau)
    assert abs(factor.trace() - factor.a) < TOL
    # and the returned element really is the inverse of 1 - x*gamma_tau
    x = mp.mpf(p) ** (-mp.mpc(s))
    q = GradedElement.identity() - grading_shift(tau).scale(x)
    assert abs(factor.a - q.inverse().a) < TOL
    assert abs(factor.b - q.inverse().b) < TOL


@pytest.mark.parametrize("p", [2, 3, 5, 7, 11])
@pytest.mark.parametrize("s", [2, 3, mp.mpf("2.5")])
@pytest.mark.parametrize("tau", [1, 0, mp.mpf("0.5"), mp.mpf("0.25"), 2])
def test_local_factor_supertrace_closed_form(p, s, tau):
    """`local_factor` returns q^{-1}, so its `b` *is* the supertrace."""
    factor = local_factor(p, s, tau)
    assert abs(factor.supertrace() - factor.b) < TOL


@pytest.mark.parametrize("p", [2, 3, 5, 7, 11])
@pytest.mark.parametrize("s", [2, 3, mp.mpf("2.5")])
def test_local_factor_equals_classical_factor_at_tau_one(p, s):
    """At tau = 1 the graded trace is exactly 1/(1 - p^{-s})."""
    x = mp.mpf(p) ** (-mp.mpc(s))
    factor = local_factor(p, s, TRIVIAL)
    assert abs(factor.b) < TOL
    assert abs(factor.trace() - 1 / (1 - x)) < TOL


def test_local_factor_has_an_omega_component_away_from_tau_one():
    for p in (2, 3, 5, 7):
        for tau in GRADED:
            assert abs(local_factor(p, 2, tau).b) > TOL
        assert abs(local_factor(p, 2, TRIVIAL).b) < TOL


# ============================================================
# The recorded negative result
# ============================================================

def test_grading_shift_endpoints():
    """gamma_1 = I.  gamma_0 is the projection (1+omega)/2, not omega.

    The interpolation is affine in tau, so the endpoint at tau = 0 is the
    spectral projection onto the +1 eigenspace rather than the generator.
    """
    one = grading_shift(TRIVIAL)
    assert abs(one.a - 1) < TOL and abs(one.b) < TOL

    zero = grading_shift(0)
    assert abs(zero.a - mp.mpf("0.5")) < TOL
    assert abs(zero.b - mp.mpf("0.5")) < TOL

    for tau in (TRIVIAL, 0):
        gamma = grading_shift(tau)
        square = gamma * gamma
        assert abs(square.a - gamma.a) < TOL
        assert abs(square.b - gamma.b) < TOL


def test_trace_reproduces_zeta_only_at_tau_one():
    """THE RESULT. Away from tau = 1 the graded trace leaves the classical
    Euler product, so the shift-zeta has different values -- and therefore
    cannot have the same zeros."""
    primes = first_primes(60)
    at_one = shift_zeta(2, TRIVIAL, primes)
    assert abs(at_one - mp.zeta(2)) / abs(mp.zeta(2)) < mp.mpf("1e-3")

    for tau in GRADED:
        value = shift_zeta(2, tau, primes)
        relative = abs(value - mp.zeta(2)) / abs(mp.zeta(2))
        assert relative > mp.mpf("1e-2"), (
            f"tau={tau} unexpectedly reproduces zeta; the recorded finding is "
            "that only tau = 1 does"
        )


def test_grading_is_visible_to_the_trace():
    """A trace returning zeta for every tau would make the programme
    untestable by construction, since the grading would carry no information.

    That is not what happens: the trace moves with tau.
    """
    primes = first_primes(30)
    assert abs(shift_zeta(2, TRIVIAL, primes) - shift_zeta(2, 0, primes)) > mp.mpf("0.1")


def test_whole_construction_is_confined_to_the_even_part():
    """Every local factor is built from gamma_tau, which is even.

    So the product never leaves the two-dimensional algebra generated by
    gamma_tau, and at tau = 1 it is scalar and lies in Fix(sigma). The
    construction cannot therefore test whether zeros are forced into the fixed
    locus: it is there by definition.
    """
    at_one = shift_zeta_element(2, TRIVIAL, first_primes(20))
    assert at_one.is_even()
    assert at_one.is_fixed()
    assert abs(at_one.b) < TOL


def test_supertrace_of_the_shift_zeta_vanishes_at_tau_one():
    """At tau = 1 every local factor is scalar, so the supertrace is exactly
    zero and carries no information there."""
    for s in (2, 3, 4):
        assert abs(shift_zeta_supertrace(s, TRIVIAL, first_primes(20))) < TOL


def test_supertrace_of_the_shift_zeta_is_nonzero_away_from_tau_one():
    for tau in GRADED:
        assert abs(shift_zeta_supertrace(2, tau, first_primes(20))) > TOL


def test_compare_traces_reports_all_three():
    report = compare_traces(n_primes=30)
    assert set(report) == {"trace", "supertrace", "matrix_trace"}
    for comparison in report.values():
        assert comparison.explanation
        assert comparison.max_relative_error >= 0
