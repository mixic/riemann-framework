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
"""Tests for the speculative dimension-shift involution."""

import mpmath as mp
import pytest

from riemann_framework.dimension_shift import (
    DimensionElement,
    check_fixed_locus,
    check_functional_equation_consistency,
    check_involution,
    is_fixed_point,
    sigma,
)
from riemann_framework.zeta import set_precision


@pytest.fixture(autouse=True)
def setup_precision():
    set_precision(30)


def test_sigma_is_an_involution():
    """Applying conjugate reflection twice returns the original point."""
    for point in (mp.mpc("0.3", "10"), mp.mpc("0.5", "14"), mp.mpc("2", "-3")):
        assert mp.almosteq(sigma(sigma(point)), point)

    assert all(result["is_involution"] for result in check_involution())


def test_fixed_locus_is_the_critical_line():
    """Every point on Re(s)=1/2 is fixed, and off-line points are not."""
    assert is_fixed_point(mp.mpc("0.5", "10"))
    assert is_fixed_point(mp.mpc("0.5", "-10"))
    assert not is_fixed_point(mp.mpc("0.3", "10"))
    assert not is_fixed_point(mp.mpc("0.7", "10"))

    results = check_fixed_locus()
    assert [result["is_fixed"] for result in results] == [
        False,
        False,
        True,
        False,
        False,
    ]


def test_dimension_element_has_expected_powers():
    """The dimension element has the declared parity behavior."""
    element = DimensionElement(dimension=3)
    point = mp.mpc("0.3", "10")

    assert mp.almosteq(element.act_on(point), sigma(point))
    assert (element**2).dimension == 0
    assert (element**3).dimension == 3


def test_first_zeros_are_preserved_by_sigma():
    """The conjugate-reflection partner of each tested zero is also a zero."""
    results = check_functional_equation_consistency(num_zeros=3)

    assert all(result["both_zero"] for result in results)
