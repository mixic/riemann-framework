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
"""
The primon gas: an exact arithmetic anchor for the dimension-shift programme.

Adapted from the "Stage D2" idea in an external `rh_idea_framework` prototype.
Unlike every other numerical surface in this repository, this one is not a
model, an analogy, or a statistical resemblance. It is an elementary theorem
(Julia 1990, Spector 1990; refined into the Bost-Connes system, 1995).

Take the Hilbert space `l^2(N)` with orthonormal basis `|n>`, `n = 1, 2, ...`,
and the diagonal (unbounded) operator

    H |n> = log(n) |n>

Then for `Re(s) > 1` the operator `e^{-sH}` is trace class and

    Tr[e^{-sH}] = sum_{n>=1} n^{-s} = zeta(s)

exactly. The Euler product is immediate from unique factorisation: `l^2(N)` is
the Fock space of independent bosonic oscillators, one per prime `p`, each of
energy `log(p)`.

Why this matters here
---------------------
`docs/future_work.md` Priority 5 records that the dimension-shift model has no
derived prime structure, and `docs/central_hypothesis.md` lists "the model has
no canonical relation to prime weights and the Euler product" as a
falsification criterion. This module supplies the thing that was missing: an
operator whose trace provably *is* the Euler product, which any proposed
symmetry can be tested against (`operator_symmetry.py`).

What this deliberately does NOT claim
-------------------------------------
The eigenvalues of `H` are `log(n)`, **not** the imaginary parts of the zeta
zeros. This operator anchors the Euler product, not the location of the zeros.
Reaching the zeros needs a harder, still-open construction (Connes 1999, adele
class space). The primon gas is the correct honest starting point, not the
destination. Nothing here proves anything about RH.
"""

from __future__ import annotations

from typing import Sequence, TypeAlias

import mpmath as mp
import numpy as np

# The scalar type accepted for the exponent `s`: a concrete union of the types
# the arithmetic actually receives. `numbers.Number` would also accept `mp.mpf`
# and `mp.mpc`, but that abstract base declares no `__complex__`, so `complex(s)`
# on it is rejected by a type checker. The union keeps `complex(s)` valid for
# every member (int/float/complex via the numeric tower, mpf/mpc via their
# `__complex__`).
Scalar: TypeAlias = int | float | complex | mp.mpf | mp.mpc

# Trial-division factorisation. The external prototype used sympy; this
# repository depends only on mpmath/numpy/scipy, and trial division is exact
# for the small integers a finite truncation can handle anyway.
_SMALL_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def factorize(n: int) -> dict[int, int]:
    """Return the prime factorisation of `n >= 1` as `{prime: exponent}`.

    Uses trial division by the small primes first (which covers every integer a
    truncation of a few thousand contains), then by odd candidates up to
    `sqrt(n)`. Raises for `n < 1`.
    """
    if n < 1:
        raise ValueError(f"factorize expects n >= 1, got {n}")

    factors: dict[int, int] = {}
    rest = n

    for prime in _SMALL_PRIMES:
        while rest % prime == 0:
            factors[prime] = factors.get(prime, 0) + 1
            rest //= prime

    candidate = 41
    while candidate * candidate <= rest:
        while rest % candidate == 0:
            factors[candidate] = factors.get(candidate, 0) + 1
            rest //= candidate
        candidate += 2

    if rest > 1:
        factors[rest] = factors.get(rest, 0) + 1

    return factors


def hamiltonian_diagonal(n_max: int) -> np.ndarray:
    """Diagonal of the truncated primon Hamiltonian, `H|n> = log(n)|n>`.

    Index `i` of the result corresponds to `n = i + 1`, so entry 0 is
    `log(1) = 0`.
    """
    if n_max < 1:
        raise ValueError(f"n_max must be >= 1, got {n_max}")
    return np.log(np.arange(1, n_max + 1, dtype=float))


def primon_hamiltonian(n_max: int) -> np.ndarray:
    """The truncated primon Hamiltonian as a dense `n_max x n_max` matrix."""
    return np.diag(hamiltonian_diagonal(n_max))


def trace_exp(s: Scalar, n_max: int) -> complex:
    """Truncated partition function: `Tr_N[e^{-s H}] = sum_{n=1}^{N} n^{-s}`.

    This equals the partial sum of the Dirichlet series for zeta, which is the
    whole point: the operator's trace *is* the arithmetic object.
    """
    if n_max < 1:
        raise ValueError(f"n_max must be >= 1, got {n_max}")
    n = np.arange(1, n_max + 1, dtype=float)
    return complex(np.sum(n ** (-complex(s))))


def zeta_reference(s: Scalar) -> complex:
    """`zeta(s)` at high precision, via mpmath."""
    mp.mp.dps = 30
    value = mp.zeta(mp.mpc(complex(s).real, complex(s).imag))
    return complex(value)


def trace_convergence(
    s: Scalar, truncations: Sequence[int] = (10, 100, 1_000, 10_000, 100_000)
) -> dict:
    """Check `Tr_N[e^{-sH}] -> zeta(s)` as `N` grows, for `Re(s) > 1`.

    The defining series diverges for `Re(s) <= 1`, so this is only meaningful
    there; passing such an `s` raises rather than returning a misleading number.
    """
    if complex(s).real <= 1.0:
        raise ValueError(
            "The defining series converges only for Re(s) > 1. For Re(s) <= 1 "
            "zeta requires analytic continuation, and the naive truncated sum "
            "above is not a meaningful approximation to Tr[e^{-sH}]."
        )

    reference = zeta_reference(s)
    partials = [trace_exp(s, n) for n in truncations]
    errors = [abs(p - reference) / abs(reference) for p in partials]

    return {
        "s": s,
        "truncations": list(truncations),
        "partial_sums": partials,
        "zeta_reference": reference,
        "relative_errors": errors,
        "errors_decrease": all(
            errors[i + 1] < errors[i] for i in range(len(errors) - 1)
        ),
    }
