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
import numpy as np
import pytest

from riemann_framework.dimension_shift import (
    DimensionElement,
    check_fixed_locus,
    check_functional_equation_consistency,
    check_involution,
    is_fixed_point,
    sigma,
    sigma_eigenvalues,
    sigma_fixed_locus,
    sigma_matrix,
    sigma_plus_hamiltonian,
    supersymmetric_hamiltonian,
    witten_index,
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


def test_sigma_matrix_is_a_hermitian_involution():
    """The finite sector swap is symmetric and squares to identity."""
    matrix = sigma_matrix(dim_per_sector=3)

    assert matrix.shape == (6, 6)
    assert np.array_equal(matrix, matrix.T)
    assert np.allclose(matrix @ matrix, np.eye(6))
    assert np.array_equal(sigma_eigenvalues(3), [-1, -1, -1, 1, 1, 1])


def test_sigma_fixed_locus_has_one_vector_per_sector_dimension():
    """The +1 eigenspace contains symmetric sector pairs."""
    basis = sigma_fixed_locus(dim_per_sector=3)

    assert basis.shape == (6, 3)
    assert np.allclose(sigma_matrix(3) @ basis, basis)


def test_hamiltonians_are_symmetric_and_seeded():
    """Finite Hamiltonians are symmetric and reproducible with a seed."""
    plus = sigma_plus_hamiltonian(dim_per_sector=3, seed=7)
    full = supersymmetric_hamiltonian(dim_per_sector=3, seed=7)

    assert np.allclose(plus, plus.T)
    assert np.allclose(full, full.T)
    assert np.array_equal(plus, sigma_plus_hamiltonian(3, seed=7))
    assert full.shape == (6, 6)


def test_witten_index_counts_zero_modes():
    """The numerical index counts kernels of the two sector Hamiltonians."""
    h_plus = np.diag([0.0, 2.0, 3.0])
    h_minus = np.diag([0.0, 0.0, 4.0])

    assert witten_index(h_plus, h_minus) == -1
    assert witten_index(h_plus, h_plus) == 0


def test_witten_index_is_zero_for_symmetric_random_sectors():
    """Seeded random sectors normally have no zero modes in either block."""
    hamiltonian = supersymmetric_hamiltonian(dim_per_sector=5, seed=42)
    h_plus = hamiltonian[:5, :5]
    h_minus = hamiltonian[5:, 5:]

    assert witten_index(h_plus, h_minus) == 0


@pytest.mark.parametrize("dimension", [0, -1, 1.5, "2"])
def test_sector_dimension_must_be_positive_integer(dimension):
    """Reject invalid finite-sector dimensions."""
    with pytest.raises((TypeError, ValueError)):
        sigma_matrix(dimension)


def test_witten_index_rejects_non_square_hamiltonians():
    """Reject arrays that cannot represent sector Hamiltonians."""
    with pytest.raises(ValueError):
        witten_index(np.zeros((2, 3)), np.zeros((2, 2)))






