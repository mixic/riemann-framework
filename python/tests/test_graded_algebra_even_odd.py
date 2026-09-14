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
Tests for the `even`/`odd` interface of the graded algebra.

Each defect corrected in `graded_algebra_even_odd.py` gets a regression test
here, so the fixes cannot silently revert. The original implementation:

1. `__eq__` returned `np.bool_`, which a type checker rejects where `bool` is
   declared;
2. defaulted `omega_sq` to `-1` while its docstring said `omega^2 = 1`;
3. defined `trace = even - odd` and claimed `sigma`-invariance, which fails for
   any element with a nonzero odd part;
4. built a local factor whose `even - odd` was identically 1, making the Euler
   product 1 and every downstream test vacuous;
5. `__eq__` ignored `omega_sq`, so elements of different algebras compared equal.
"""

import mpmath as mp
import pytest

from riemann_framework.graded_algebra_even_odd import (
    GradedElement,
    check_euler_product_converges,
    check_sigma_homomorphism,
    check_sigma_involution,
    check_trace_invariance,
    check_trace_is_geometric_series,
    euler_product,
    is_fixed,
    is_supertrace_zero,
    local_factor,
    partial_euler_product,
    project_to_anti,
    project_to_fix,
    sigma,
    supertrace,
    trace,
)

mp.mp.dps = 30

PRIMES_20 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
             31, 37, 41, 43, 47, 53, 59, 61, 67, 71]
TAUS = (1, 0, mp.mpf("0.5"), mp.mpf("0.25"))


# ============================================================
# Defect 1: __eq__ returned numpy.bool
# ============================================================

def test_equality_returns_a_plain_bool():
    """Regression: the original returned np.isclose(...), i.e. np.bool_."""
    result = GradedElement(1.0, 2.0) == GradedElement(1.0, 2.0)
    assert type(result) is bool
    assert result is True


def test_inequality_is_also_a_plain_bool():
    assert type(GradedElement(1.0, 2.0) == GradedElement(1.0, 3.0)) is bool


def test_equality_with_a_non_element_returns_NotImplemented():
    element = GradedElement(1.0, 2.0)
    assert (element == 5) is False
    assert (element != 5) is True


# ============================================================
# Defect 2: omega_sq default contradicted the docstring
# ============================================================

def test_default_omega_sq_is_plus_one():
    """Regression: the default was -1 while the docstring said omega^2 = 1."""
    assert GradedElement(1.0, 2.0).omega_sq == 1


def test_omega_squares_to_plus_one_by_default():
    omega = GradedElement(0.0, 1.0)
    square = omega * omega
    assert square.even == pytest.approx(1.0)
    assert square.odd == pytest.approx(0.0)


def test_omega_sq_minus_one_is_still_accepted():
    element = GradedElement(0.0, 1.0, omega_sq=-1)
    assert (element * element).even == pytest.approx(-1.0)


def test_invalid_omega_sq_is_rejected():
    with pytest.raises(ValueError):
        GradedElement(1.0, 0.0, omega_sq=2)


# ============================================================
# Defect 3: trace was not sigma-invariant
# ============================================================

@pytest.mark.parametrize("tau", TAUS)
def test_trace_is_sigma_invariant(tau):
    """Regression: the original `even - odd` is sent to `even + odd` by sigma."""
    for element in (
        GradedElement(3.0, 1.0),
        GradedElement(0.0, 5.0),
        GradedElement(2.0, -3.0),
        local_factor(2, 2, tau),
        local_factor(3, 3, tau),
        euler_product(2, PRIMES_20[:5], tau),
    ):
        assert check_trace_invariance(element)
        assert trace(sigma(element)) == pytest.approx(trace(element))


def test_the_original_trace_definition_is_not_invariant():
    """Pins down exactly what was wrong: even - odd is not invariant."""
    element = GradedElement(3.0, 1.0)
    old = element.even - element.odd
    old_after_sigma = sigma(element).even - sigma(element).odd
    assert old != pytest.approx(old_after_sigma)
    assert old == pytest.approx(2.0)
    assert old_after_sigma == pytest.approx(4.0)


def test_trace_is_the_average_of_the_eigenvalues():
    """trace = a0, the average of a0 +- a1 which sigma swaps."""
    for element in (GradedElement(3.0, 1.0), GradedElement(2.0, -3.0)):
        plus = element.even + element.odd
        minus = element.even - element.odd
        assert trace(element) == pytest.approx((plus + minus) / 2)


def test_supertrace_is_the_minus_one_eigenvalue():
    """supertrace = a0 - a1 = the eigenvalue on the -1 eigenspace of omega."""
    for element in (GradedElement(3.0, 1.0), GradedElement(2.0, -3.0)):
        assert supertrace(element) == pytest.approx(element.even - element.odd)
        # the *difference* of the two eigenvalues is 2*a1, a different functional
        assert 2 * element.odd == pytest.approx(
            (element.even + element.odd) - (element.even - element.odd)
        )


def test_supertrace_vanishes_exactly_when_even_equals_odd():
    """supertrace = a0 - a1, so it vanishes on the diagonal a0 = a1."""
    assert not is_supertrace_zero(GradedElement(3.0, 0.0))
    assert not is_supertrace_zero(GradedElement(3.0, 1.0))
    assert is_supertrace_zero(GradedElement(3.0, 3.0))
    assert is_supertrace_zero(
        GradedElement(1.0, 1.0, omega_sq=1) - GradedElement(0.0, 0.0, omega_sq=1)
    )

    # the fixed locus is a different condition: odd = 0
    assert is_fixed(project_to_fix(GradedElement(3.0, 1.0)))
    assert not is_fixed(project_to_anti(GradedElement(3.0, 1.0)))


def test_trace_is_not_an_alias_for_supertrace():
    """Regression: the original defined `supertrace` as an alias of `trace`."""
    element = GradedElement(3.0, 1.0)
    assert trace(element) != pytest.approx(supertrace(element))


# ============================================================
# Defect 4: the Euler product was identically 1
# ============================================================

def test_local_factor_functionals_match_their_closed_forms():
    """trace = average of the eigenvalues; supertrace = the -1 eigenvalue.

    Only at tau = 1 do both collapse to the classical 1/(1 - p^-s).
    """
    for p in (2, 3, 5, 7, 11):
        for s in (2, 3, mp.mpf("2.5")):
            x = mp.mpf(p) ** (-s)
            for tau in TAUS:
                tau_c = complex(tau)
                factor = local_factor(p, s, tau)
                assert supertrace(factor) == pytest.approx(
                    complex(1 / (1 - tau_c * x)), rel=1e-12
                )
                assert trace(factor) == pytest.approx(
                    (complex(1 / (1 - x)) + complex(1 / (1 - tau_c * x))) / 2,
                    rel=1e-12,
                )
                if tau_c == 1:
                    assert trace(factor) == pytest.approx(
                        complex(1 / (1 - x)), rel=1e-12
                    )


def test_euler_product_reproduces_the_classical_product_only_at_tau_one():
    """Regression: the original product was 1 for every s and every tau.

    The corrected product equals the classical partial Euler product at
    tau = 1 and is a different function otherwise. Both halves are asserted,
    because the tau != 1 behaviour is the finding rather than a defect.
    """
    for s in (2, 3):
        classical = partial_euler_product(s, PRIMES_20)

        graded = complex(1.0)
        for p in PRIMES_20:
            graded *= trace(local_factor(p, s, 1))
        assert graded == pytest.approx(classical, rel=1e-12)
        assert abs(graded - 1) > 1e-3

        for tau in (0, mp.mpf("0.5"), mp.mpf("0.25")):
            other = complex(1.0)
            for p in PRIMES_20:
                other *= trace(local_factor(p, s, tau))
            assert other != pytest.approx(classical, rel=1e-6)


def test_the_original_local_factor_gave_product_one():
    """Pins down the vacuity: original even - odd was identically 1."""
    for n in (5, 20):
        product = 1.0
        for p in PRIMES_20[:n]:
            x = float(mp.mpf(p) ** -2)
            base = 1.0 / (1.0 - x)
            product *= base - base * x
        assert product == pytest.approx(1.0)


def test_the_original_local_factor_was_not_the_geometric_series():
    """The original was off by a factor of (1 + x)."""
    for p in (2, 3, 5):
        x = mp.mpf(p) ** -2
        original_even = float(1 / (1 - x))
        series_even = float(1 / (1 - x * x))
        assert original_even / series_even == pytest.approx(float(1 + x))


def test_local_factor_geometric_series_and_convergence():
    assert check_trace_is_geometric_series(2, 2)
    assert check_trace_is_geometric_series(3, 3)
    assert check_euler_product_converges(2, PRIMES_20)


def test_tau_one_makes_the_local_factor_scalar():
    for p in (2, 3, 5):
        factor = local_factor(p, 2, 1)
        assert factor.odd == pytest.approx(0.0)
        assert factor.even == pytest.approx(complex(1 / (1 - mp.mpf(p) ** -2)))


def test_trace_of_the_local_factor_depends_on_tau():
    """The trace is not the classical factor away from tau = 1; recorded."""
    for tau in (0, mp.mpf("0.5")):
        assert trace(local_factor(2, 2, tau)) != pytest.approx(
            complex(1 / (1 - mp.mpf(2) ** -2)), rel=1e-6
        )


# ============================================================
# Defect 5: __eq__ ignored omega_sq
# ============================================================

def test_elements_of_different_algebras_are_not_equal():
    """Regression: the original compared equal despite different multiplication."""
    group = GradedElement(1.0, 2.0, omega_sq=1)
    split = GradedElement(1.0, 2.0, omega_sq=-1)
    assert group != split
    # and they really do multiply differently
    assert (group * group).even != pytest.approx((split * split).even)


def test_hashing_distinguishes_the_algebra():
    assert len({GradedElement(1.0, 2.0, omega_sq=1), GradedElement(1.0, 2.0, omega_sq=-1)}) == 2


# ============================================================
# The algebra itself
# ============================================================

def test_sigma_is_an_involution():
    for element in (GradedElement(2.0, -3.0), GradedElement(0.0, 1.0), GradedElement(1.0, 1.0)):
        assert check_sigma_involution(element)
        assert sigma(sigma(element)) == element


def test_sigma_is_a_homomorphism_for_both_signs():
    """sigma is Ad(omega), an inner automorphism, so it is a homomorphism for
    omega^2 = +1 and for omega^2 = -1 alike."""
    for omega_sq in (1, -1):
        for x in (GradedElement(2.0, -3.0, omega_sq), GradedElement(0.0, 1.0, omega_sq)):
            for y in (GradedElement(0.5, 0.25, omega_sq), GradedElement(1.0, -2.0, omega_sq)):
                assert check_sigma_homomorphism(x, y)


def test_multiplication_is_associative():
    for omega_sq in (1, -1):
        for x in (GradedElement(2.0, -3.0, omega_sq), GradedElement(0.0, 1.0, omega_sq)):
            for y in (GradedElement(0.5, 0.25, omega_sq), GradedElement(1.0, 1.0, omega_sq)):
                for z in (GradedElement(1.0, -2.0, omega_sq), GradedElement(0.0, 1.0, omega_sq)):
                    assert (x * y) * z == x * (y * z)


def test_multiplication_distributes():
    for omega_sq in (1, -1):
        x = GradedElement(2.0, -3.0, omega_sq)
        y = GradedElement(0.5, 0.25, omega_sq)
        z = GradedElement(1.0, -2.0, omega_sq)
        assert x * (y + z) == x * y + x * z


def test_zero_divisors_exist_in_the_group_algebra():
    """(1 + omega)(1 - omega) = 0 for omega^2 = 1."""
    product = GradedElement(1.0, 1.0) * GradedElement(1.0, -1.0)
    assert product.even == pytest.approx(0.0)
    assert product.odd == pytest.approx(0.0)


def test_inverse_round_trips():
    for element in (GradedElement(2.0, -3.0), GradedElement(0.5, 0.25), local_factor(2, 2, 0.5)):
        product = element * element.inverse()
        assert product.even == pytest.approx(1.0)
        assert product.odd == pytest.approx(0.0)


def test_singular_elements_are_rejected():
    with pytest.raises(ZeroDivisionError):
        GradedElement(1.0, 1.0).inverse()


def test_scalar_operations():
    element = GradedElement(2.0, -3.0)
    assert element + 1 == GradedElement(3.0, -3.0)
    assert element - 1 == GradedElement(1.0, -3.0)
    assert element * 2 == GradedElement(4.0, -6.0)
    assert 2 * element == element * 2
    assert -element == GradedElement(-2.0, 3.0)
    assert (element / 2).even == pytest.approx(1.0)
