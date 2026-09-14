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

from riemann_framework.four_squares import (
    r4_brute,
    r4_jacobi,
    verify_jacobi_formula,
    verify_sigma_dirichlet_series,
)


def test_r4_small_values_known():
    # n=1: (+-1,0,0,0) in any of 4 positions -> 8 representations
    assert r4_brute(1) == 8
    assert r4_jacobi(1) == 8
    # n=2: two +-1's among four slots -> C(4,2)*2*2 = 24
    assert r4_brute(2) == 24
    assert r4_jacobi(2) == 24


def test_jacobi_formula_matches_brute_force():
    result = verify_jacobi_formula(n_max=25)
    assert result.all_match


def test_sigma_dirichlet_series_matches_zeta_product():
    result = verify_sigma_dirichlet_series(s=3.0, n_max=50_000)
    assert result.relative_error < 1e-3


def test_sigma_series_rejects_s_leq_2():
    with pytest.raises(ValueError):
        verify_sigma_dirichlet_series(s=2.0)
