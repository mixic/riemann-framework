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
"""Riemann explicit formula for π(x)."""

from numbers import Integral

import numpy as np
import mpmath as mp


def prime_count(x: int) -> int:
    """Exact π(x) using the sieve of Eratosthenes."""
    if not isinstance(x, Integral):
        raise TypeError("x must be an integer")
    if x < 2:
        return 0

    x = int(x)
    sieve = np.ones(int(x) + 1, dtype=bool)
    sieve[0:2] = False
    for i in range(2, int(np.sqrt(x)) + 1):
        if sieve[i]:
            sieve[i * i::i] = False
    return int(np.sum(sieve))


def _validate_approximation_inputs(
    x: object, num_zeros: int, sigma: float
) -> tuple[mp.mpf, int, mp.mpf]:
    if not isinstance(num_zeros, Integral):
        raise TypeError("num_zeros must be an integer")
    if num_zeros < 0:
        raise ValueError("num_zeros must be non-negative")

    x_value = mp.mpf(x)
    sigma_value = mp.mpf(sigma)
    if not mp.isfinite(x_value) or x_value <= 1:
        raise ValueError("x must be finite and greater than 1")
    if not mp.isfinite(sigma_value) or sigma_value <= 0:
        raise ValueError("sigma must be finite and greater than 0")

    return x_value, int(num_zeros), sigma_value


def _regularized_li(x: object, num_zeros: int, sigma: float) -> float:
    x_value, zero_count, sigma_value = _validate_approximation_inputs(
        x, num_zeros, sigma
    )
    result = mp.li(x_value)

    for index in range(1, zero_count + 1):
        zero = mp.zetazero(index)
        gamma = mp.im(zero)
        weight = mp.exp(-(gamma * sigma_value) ** 2)
        result -= 2 * weight * mp.re(mp.li(mp.power(x_value, zero)))

    return float(result)


def li_approx(x, num_zeros: int, sigma: float = 1.0) -> float:
    """
    Regularized approximation of π(x) via the explicit formula:
        π(x) ≈ Li(x) − Σ_ρ w(γ) · Li(x^ρ)

    The weight w(γ) = exp(-(γ·σ)²) is a Gaussian damping factor that
    ensures absolute convergence. Without this regularization, the
    naive sum of zeros diverges (the explicit formula is only
    conditionally convergent).

    Args:
        x: the evaluation point
        num_zeros: number of non-trivial zeros to include
        sigma: damping parameter (smaller = stronger damping)

    Returns:
        Approximation of π(x) as a float.
    """
    return _regularized_li(x, num_zeros, sigma)


def li_approx_regularized(x, num_zeros: int, sigma: float = 1.0) -> float:
    """
    Regularized approximation using a Gaussian test function.

    The Gaussian factor exp(-(γ·σ)²) ensures absolute convergence.
    """
    return _regularized_li(x, num_zeros, sigma)


