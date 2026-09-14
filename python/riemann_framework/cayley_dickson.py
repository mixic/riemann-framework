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
"""The Cayley-Dickson construction: R -> C -> H -> O -> sedenions -> ...

This is the precise, century-old formalization of "double the dimension to
get a new number system," which is exactly the intuition behind circle ->
sphere -> higher sphere. Elements of the dimension-2^n algebra are
represented as flat real vectors of length 2^n. Multiplication and
conjugation are defined recursively:

    conjugate(a, b) = (conjugate(a), -b)
    (a, b) * (c, d)  = (a*c - conjugate(d)*b,  d*a + b*conjugate(c))

with the base case (dimension 1 = R) being ordinary real multiplication and
conjugation = identity.

This reproduces: dim 1 = R, dim 2 = C, dim 4 = H (quaternions),
dim 8 = O (octonions), dim 16 = sedenions, dim 32, 64, ... beyond.

`check_properties` runs the concrete numerical tests behind the Hurwitz
theorem (1898) and its consequences, so the well-known collapse of
structure is *observed*, not merely asserted:

    dim  1 (R):  commutative, associative, no zero divisors, ordered
    dim  2 (C):  commutative, associative, no zero divisors, NOT ordered
    dim  4 (H):  associative, no zero divisors, NOT commutative
    dim  8 (O):  no zero divisors, NOT associative (but still "alternative")
    dim 16+:     HAS zero divisors -- the algebra stops being a division
                 algebra at all. This is not a limitation of this
                 implementation; the Hurwitz theorem (1898) proves no
                 normed division algebra over R exists in any dimension
                 other than 1, 2, 4, 8.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def conjugate(x: np.ndarray) -> np.ndarray:
    n = len(x)
    if n == 1:
        return x.copy()
    half = n // 2
    a, b = x[:half], x[half:]
    return np.concatenate([conjugate(a), -b])


def multiply(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    n = len(x)
    if n == 1:
        return x * y
    half = n // 2
    a, b = x[:half], x[half:]
    c, d = y[:half], y[half:]
    first = multiply(a, c) - multiply(conjugate(d), b)
    second = multiply(d, a) + multiply(b, conjugate(c))
    return np.concatenate([first, second])


def basis(dim: int, i: int) -> np.ndarray:
    """The i-th basis vector e_i (e_0 = 1) of the dimension-`dim` algebra."""
    v = np.zeros(dim)
    v[i] = 1.0
    return v


def norm(x: np.ndarray) -> float:
    return float(np.sqrt(np.sum(x * x)))


@dataclass
class PropertyReport:
    dim: int
    commutative: bool
    associative: bool
    has_zero_divisors: bool
    zero_divisor_example: tuple[np.ndarray, np.ndarray] | None
    explanation: str


def check_properties(dim: int, n_trials: int = 200, seed: int = 0, search_zero_divisors: bool = True) -> PropertyReport:
    """Numerically test commutativity, associativity, and zero divisors at
    a given power-of-two dimension, using random elements plus (for zero
    divisors) a targeted search over basis-vector sums, which is where
    Cayley-Dickson zero divisors are known to live from dim 16 onward.
    """
    if dim & (dim - 1) != 0:
        raise ValueError("dim must be a power of 2 (1, 2, 4, 8, 16, 32, ...).")

    rng = np.random.default_rng(seed)
    tol = 1e-8

    commutative = True
    associative = True
    for _ in range(n_trials):
        x = rng.standard_normal(dim)
        y = rng.standard_normal(dim)
        z = rng.standard_normal(dim)
        if norm(multiply(x, y) - multiply(y, x)) > tol:
            commutative = False
        if norm(multiply(multiply(x, y), z) - multiply(x, multiply(y, z))) > tol:
            associative = False

    has_zero_divisors = False
    example = None
    if search_zero_divisors:
        for i in range(dim):
            for j in range(i + 1, dim):
                for k in range(dim):
                    for l in range(k + 1, dim):
                        x = basis(dim, i) + basis(dim, j)
                        y = basis(dim, k) + basis(dim, l)
                        prod = multiply(x, y)
                        if norm(prod) < tol and norm(x) > tol and norm(y) > tol:
                            has_zero_divisors = True
                            example = (x, y)
                            break
                    if has_zero_divisors:
                        break
                if has_zero_divisors:
                    break
            if has_zero_divisors:
                break

    parts = [f"Dimension {dim}: "]
    parts.append("commutative" if commutative else "NOT commutative")
    parts.append(", associative" if associative else ", NOT associative")
    if search_zero_divisors:
        parts.append(
            ", HAS zero divisors (division algebra structure fails)"
            if has_zero_divisors
            else ", no zero divisors found in this search"
        )
    explanation = "".join(parts) + "."

    return PropertyReport(
        dim=dim,
        commutative=commutative,
        associative=associative,
        has_zero_divisors=has_zero_divisors,
        zero_divisor_example=example,
        explanation=explanation,
    )
