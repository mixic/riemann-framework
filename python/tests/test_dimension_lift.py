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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from riemann_framework.cayley_dickson import check_properties
from riemann_framework.four_squares import (
    r4_brute,
    r4_jacobi,
    verify_jacobi_formula,
    verify_sigma_dirichlet_series,
)


def test_complex_numbers_are_commutative_and_associative():
    r = check_properties(2, n_trials=100)
    assert r.commutative
    assert r.associative
    assert not r.has_zero_divisors


def test_quaternions_lose_commutativity_but_keep_associativity():
    r = check_properties(4, n_trials=100)
    assert not r.commutative
    assert r.associative
    assert not r.has_zero_divisors


def test_octonions_lose_associativity_too():
    r = check_properties(8, n_trials=100)
    assert not r.commutative
    assert not r.associative
    assert not r.has_zero_divisors


def test_sedenions_have_zero_divisors():
    r = check_properties(16, n_trials=50)
    assert not r.commutative
    assert not r.associative
    assert r.has_zero_divisors
    assert r.zero_divisor_example is not None


def test_rejects_non_power_of_two_dimension():
    with pytest.raises(ValueError):
        check_properties(6)


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 12, 16, 24, 30])
def test_r4_brute_matches_jacobi_formula(n):
    assert r4_brute(n) == r4_jacobi(n)


def test_verify_jacobi_formula_reports_match():
    result = verify_jacobi_formula(n_max=30)
    assert result.all_match


def test_sigma_dirichlet_series_matches_zeta_product():
    result = verify_sigma_dirichlet_series(s=3.0, n_max=20_000)
    assert result.relative_error < 1e-3


def test_sigma_series_rejects_s_leq_2():
    with pytest.raises(ValueError):
        verify_sigma_dirichlet_series(s=2.0, n_max=100)
