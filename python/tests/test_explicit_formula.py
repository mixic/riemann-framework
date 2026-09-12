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

"""Test of the Riemann explicit formula."""

import numpy as np
import pytest

from riemann_framework.explicit_formula import (
    li_approx,
    li_approx_regularized,
    prime_count,
)
from riemann_framework.zeta import set_precision


@pytest.fixture(autouse=True)
def setup_precision():
    set_precision(25)


def test_pi_small_values():
    """Known values: π(10) = 4, π(100) = 25, π(1000) = 168."""
    assert prime_count(10) == 4
    assert prime_count(100) == 25
    assert prime_count(1000) == 168


@pytest.mark.parametrize("value", [2.5, "10"])
def test_prime_count_requires_an_integer(value):
    """Reject values that cannot represent a sieve size exactly."""
    with pytest.raises(TypeError):
        prime_count(value)


@pytest.mark.parametrize(
    ("x", "num_zeros", "sigma"),
    [(1, 0, 1.0), (10, -1, 1.0), (10, 1, 0.0)],
)
def test_li_approx_rejects_invalid_parameters(x, num_zeros, sigma):
    """Reject invalid points, zero counts, and damping parameters."""
    with pytest.raises(ValueError):
        li_approx(x, num_zeros, sigma)


def test_regularized_alias_matches_li_approx():
    """Both public names should use the same regularized calculation."""
    assert li_approx(10, 3, sigma=0.5) == li_approx_regularized(10, 3, sigma=0.5)


def test_approximation_runs_without_error():
    """
    The approximation should run without errors and return finite values.

    Note: The Riemann explicit formula is only conditionally convergent.
    A naive summation of zeros does not produce a monotonically
    decreasing error. This test only checks that the computation
    runs without numerical errors.
    """
    x_values = np.arange(10, 100)
    approx = np.array([li_approx(x, 10) for x in x_values])
    assert len(approx) == len(x_values)
    assert np.all(np.isfinite(approx))