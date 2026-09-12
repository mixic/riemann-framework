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
"""Numerical assert: RH for the first N zeros."""

import pytest

from riemann_framework.zeros import verify_first_n_zeros
from riemann_framework.zeta import set_precision

NUM_ZEROS = 100  # adjustable
DPS = 50


@pytest.fixture(autouse=True)
def setup_precision():
    set_precision(DPS)


def test_realpart_is_half():
    """For every tested zero: Re(ρ) = 1/2."""
    results = verify_first_n_zeros(NUM_ZEROS)
    for r in results:
        assert r["on_critical_line"], (
            f"ERROR: Zero #{r['n']} has real part {r['re']}, "
            f"expected 0.5"
        )


def test_zeta_value_is_zero():
    """For every tested zero: ζ(ρ) ≈ 0."""
    results = verify_first_n_zeros(NUM_ZEROS)
    for r in results:
        assert r["is_zero"], (
            f"ERROR: ζ({r['zero']}) is not zero"
        )