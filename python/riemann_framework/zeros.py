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
"""Verification of zeros of the zeta function."""

import mpmath as mp

from .zeta import zeta_zero, zeta, set_precision


def verify_zero(n: int, tol=None) -> dict:
    """
    Verify the n-th non-trivial zero.

    Returns:
        {
            "n": int,
            "zero": mpmath complex,
            "re": mpmath real,
            "im": mpmath real,
            "on_critical_line": bool,
            "is_zero": bool,
        }
    """
    if tol is None:
        tol = mp.mpf(10) ** (-mp.mp.dps // 2)

    zero = zeta_zero(n)
    sigma = mp.re(zero)
    t = mp.im(zero)

    return {
        "n": n,
        "zero": zero,
        "re": sigma,
        "im": t,
        "on_critical_line": mp.almosteq(sigma, mp.mpf("0.5"), abs_eps=tol),
        "is_zero": abs(zeta(zero)) < tol,
    }


def verify_first_n_zeros(n: int, tol=None) -> list:
    """Verify the first n non-trivial zeros."""
    set_precision()
    return [verify_zero(i, tol=tol) for i in range(1, n + 1)]