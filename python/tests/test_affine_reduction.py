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
Tests for the affine-reduction gate.

The first test in this file is a recorded negative result, not a success story:
the complex-plane map this repository uses as the dimension-shift prototype,

    sigma(s) = 1 - conjugate(s)

is affine in `(s, conjugate(s))`, so it is a known similarity of the plane and
carries no new algebra. That is asserted here so the claim cannot quietly
become "a new element extending C" again in the documentation.
"""

import pytest

from riemann_framework.affine_reduction import (
    ExpressionError,
    check_affine_reduction,
    fixed_locus_is_critical_line,
    parse_expression,
)


# ============================================================
# The recorded negative result
# ============================================================

def test_dimension_shift_prototype_is_affine():
    """sigma(s) = 1 - conjugate(s) is NOT a new algebraic object.

    This is the honest answer to the "new element extending C, analogous to i"
    framing in docs/central_hypothesis.md: the prototype is the affine map
    a*s + b*s_conj + c with a=0, b=-1, c=1.
    """
    result = check_affine_reduction("1 - s_conj")

    assert result.is_affine, result.explanation
    assert not result.clears_gate
    a, b, c = result.coefficients
    assert abs(a) < 1e-9
    assert abs(b + 1) < 1e-9
    assert abs(c - 1) < 1e-9
    assert result.known_map is not None
    assert "functional-equation reflection" in result.known_map


def test_dimension_shift_prototype_fixed_locus_is_the_critical_line():
    """The one property the prototype genuinely has: its fixed locus.

    sigma(s) = s exactly when Re(s) = 1/2. This is what makes the prototype
    relevant to RH at all, independently of the affine-reduction result.
    """
    assert fixed_locus_is_critical_line("1 - s_conj")


# ============================================================
# Textbook affine maps are all caught
# ============================================================

@pytest.mark.parametrize(
    "expression",
    [
        "s",                          # identity
        "s_conj",                     # conjugation
        "1 - s",                      # reflection without conjugation
        "1 - s_conj",                 # the dimension-shift prototype
        "2*s - 3*s_conj + 4",         # generic affine combination
        "(s + s_conj)/2",             # projection onto the real part
        "s - 1j*s_conj",              # rotation-like
    ],
)
def test_known_affine_maps_are_flagged(expression):
    result = check_affine_reduction(expression)
    assert result.is_affine, f"{expression!r} should reduce to an affine map"
    assert not result.clears_gate


def test_coefficients_are_recovered_exactly():
    result = check_affine_reduction("2*s - 3*s_conj + 4")
    a, b, c = result.coefficients
    assert abs(a - 2) < 1e-9
    assert abs(b + 3) < 1e-9
    assert abs(c - 4) < 1e-9


# ============================================================
# Genuinely nonlinear expressions clear the gate
# ============================================================

@pytest.mark.parametrize(
    "expression",
    [
        "s*s_conj",              # |s|^2
        "s**2",
        "s_conj**2",
        "1 - s_conj + s*s_conj",
        "s**2 + s_conj**3",
        "exp(s)",
    ],
)
def test_nonlinear_expressions_clear_the_gate(expression):
    result = check_affine_reduction(expression)
    assert not result.is_affine, f"{expression!r} should be non-affine"
    assert result.clears_gate
    assert result.coefficients is None


# ============================================================
# Safety and error handling
# ============================================================

def test_expression_is_evaluated_with_real_conjugation():
    """Passing the true conjugate as s_conj reproduces sigma on the plane."""
    sigma = parse_expression("1 - s_conj")
    for z in (complex(0.3, 5.0), complex(0.5, 14.0), complex(-2.0, -1.5)):
        assert abs(sigma(z, z.conjugate()) - (1 - z.conjugate())) < 1e-12


@pytest.mark.parametrize(
    "expression",
    ["__import__('os')", "open('x')", "lambda: 1", "s; import os"],
)
def test_unsafe_expressions_are_rejected(expression):
    with pytest.raises(ExpressionError):
        parse_expression(expression)


def test_empty_expression_is_rejected():
    with pytest.raises(ExpressionError):
        parse_expression("   ")
