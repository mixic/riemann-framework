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

import numpy as np

from riemann_framework.cayley_dickson import check_properties, multiply, basis, norm


def test_complex_numbers_commutative_and_associative():
    report = check_properties(2, n_trials=50, search_zero_divisors=False)
    assert report.commutative
    assert report.associative
    assert not report.has_zero_divisors


def test_quaternions_associative_not_commutative():
    report = check_properties(4, n_trials=50, search_zero_divisors=False)
    assert not report.commutative
    assert report.associative


def test_quaternion_ijk_relations():
    # e1=i, e2=j, e3=k (e0=1). Expect i*j = k (up to this construction's sign convention),
    # and crucially i*j == -(j*i): non-commutativity should show up concretely.
    i, j = basis(4, 1), basis(4, 2)
    ij = multiply(i, j)
    ji = multiply(j, i)
    assert norm(ij + ji) < 1e-8  # anticommute: i*j = -(j*i)
    assert norm(ij) > 0.99  # unit norm preserved (|i*j| = |i||j| = 1)


def test_octonions_not_associative():
    report = check_properties(8, n_trials=100, search_zero_divisors=False)
    assert not report.associative


def test_octonions_still_no_zero_divisors():
    report = check_properties(8, n_trials=20, search_zero_divisors=True)
    assert not report.has_zero_divisors


def test_sedenions_have_zero_divisors():
    report = check_properties(16, n_trials=20, search_zero_divisors=True)
    assert report.has_zero_divisors
    assert report.zero_divisor_example is not None
    x, y = report.zero_divisor_example
    prod = multiply(x, y)
    assert norm(prod) < 1e-6
    assert norm(x) > 1e-6 and norm(y) > 1e-6
