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
"""Wrapper around mpmath for the Riemann zeta function."""

import mpmath as mp

# Default precision (adjustable)
DEFAULT_DPS = 50


def set_precision(dps: int = DEFAULT_DPS) -> None:
    """Set the computation precision (number of decimal places)."""
    mp.mp.dps = dps


def zeta(s):
    """Compute ζ(s) using the current precision."""
    return mp.zeta(s)


def zeta_zero(n: int):
    """
    Return the n-th non-trivial zero of the zeta function.

    The return value is a complex mpmath object.
    """
    return mp.zetazero(n)


def is_zero(s, tol=None):
    """
    Check whether ζ(s) ≈ 0 (within tolerance).

    If `tol` is None, 10^(-dps/2) is used.
    """
    if tol is None:
        tol = mp.mpf(10) ** (-mp.mp.dps // 2)
    return abs(mp.zeta(s)) < tol