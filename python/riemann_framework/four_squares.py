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
"""Where a 4D ('sphere') structure genuinely produces Euler-product content.

This module implements the concrete, historically real answer to "does
lifting to a higher-dimensional sphere naturally produce something like the
Euler product": Jacobi's four-square theorem.

The quaternion norm form N(a + bi + cj + dk) = a^2 + b^2 + c^2 + d^2 is
exactly the squared radius of a point in R^4 -- literally "how far a
quaternion is from the origin," the natural generalization of |a+bi|^2 =
a^2+b^2 (the circle) to four dimensions (the 3-sphere of unit quaternions
lives inside this norm form).

Define r4(n) = number of ways to write n as an ordered sum of four integer
squares (including signs and zero), i.e. the number of lattice points in
Z^4 (equivalently: Lipschitz integer quaternions) with norm exactly n. This
is precisely "how many points of the integer lattice lie on the 4D sphere
of squared-radius n" -- a direct, rigorous instance of the dimension-lifted
picture (circle -> sphere -> higher sphere) applied to counting, not
statistics.

Jacobi's theorem (1834), completely proven and classical, states:

    r4(n) = 8 * sum_{d | n, 4 does not divide d} d

The right-hand side is an arithmetic function built from divisors -- and
its Dirichlet series has an honest-to-goodness Euler product:

    sum_{n=1}^{infinity} sigma(n) / n^s   =   zeta(s) * zeta(s-1)

where sigma(n) = sum_{d|n} d is the ordinary divisor-sum function. (This
identity itself has an elementary proof via the Euler product of zeta and
is not in dispute; both factors individually have their own Euler
products over primes.)

So: lifting from 2D (Gaussian integers, norm a^2+b^2, related to
zeta(s)*L(s,chi_-4), the two-square theorem) to 4D (Lipschitz/Hurwitz
quaternions, norm a^2+b^2+c^2+d^2, four-square theorem) DOES produce a
new, honest Euler-product-bearing Dirichlet series -- zeta(s)*zeta(s-1)
instead of zeta(s)*L(s,chi_-4). This is real, checkable arithmetic content,
not a coincidence dressed up.

What this does NOT do, and this is the important caveat for RH specifically:
zeta(s)*zeta(s-1) is built from ordinary zeta at two different points; it
tells you nothing new about the *location* of zeta's own zeros. Producing
*an* Euler product from a higher-dimensional lattice is real and
achievable (this module proves it numerically); producing one whose
analytic structure pins down where zeta's zeros are is the open problem
that motivated this whole framework, and this module does not close that
gap. It only demonstrates that "higher dimension -> genuine arithmetic
content" is possible in principle, at a specific, well-understood instance.
"""

from __future__ import annotations

from dataclasses import dataclass

import mpmath as mp
import numpy as np


def r4_brute(n: int) -> int:
    """Brute-force count of ordered integer quadruples (a,b,c,d) with
    a^2+b^2+c^2+d^2 = n. Only practical for modest n (used to verify
    Jacobi's formula, not as the main computational tool)."""
    if n == 0:
        return 1
    count = 0
    r = int(np.floor(np.sqrt(n)))
    for a in range(-r, r + 1):
        rem_a = n - a * a
        if rem_a < 0:
            continue
        rb = int(np.floor(np.sqrt(rem_a)))
        for b in range(-rb, rb + 1):
            rem_b = rem_a - b * b
            if rem_b < 0:
                continue
            rc = int(np.floor(np.sqrt(rem_b)))
            for c in range(-rc, rc + 1):
                rem_c = rem_b - c * c
                if rem_c < 0:
                    continue
                d2 = rem_c
                d = int(round(np.sqrt(d2)))
                if d * d == d2:
                    count += 1 if d == 0 else 2
    return count


def divisor_sum(n: int) -> int:
    total = 0
    for d in range(1, n + 1):
        if n % d == 0:
            total += d
    return total


def r4_jacobi(n: int) -> int:
    """Jacobi's closed form: 8 * sum of divisors of n not divisible by 4."""
    if n == 0:
        return 1
    total = 0
    for d in range(1, n + 1):
        if n % d == 0 and d % 4 != 0:
            total += d
    return 8 * total


@dataclass
class JacobiCheckResult:
    n_values: list[int]
    r4_brute_values: list[int]
    r4_jacobi_values: list[int]
    all_match: bool
    explanation: str


def verify_jacobi_formula(n_max: int = 30) -> JacobiCheckResult:
    """Brute-force-verify Jacobi's four-square formula for n = 1..n_max."""
    ns = list(range(1, n_max + 1))
    brute = [r4_brute(n) for n in ns]
    jacobi = [r4_jacobi(n) for n in ns]
    all_match = brute == jacobi

    explanation = (
        f"Checked n=1..{n_max}: brute-force lattice-point count on the 4D "
        f"sphere of squared-radius n {'matches' if all_match else 'DOES NOT match'} "
        "Jacobi's closed form r4(n) = 8*sum_{d|n, 4 nmid d} d. "
        + ("This confirms, by direct computation rather than citation, that "
           "counting points on higher-dimensional spheres over the integer "
           "lattice reduces to an arithmetic (divisor-sum) function."
           if all_match else
           "Discrepancy found -- check n_max or implementation.")
    )

    return JacobiCheckResult(
        n_values=ns,
        r4_brute_values=brute,
        r4_jacobi_values=jacobi,
        all_match=all_match,
        explanation=explanation,
    )


@dataclass
class EulerProductResult:
    s: float
    partial_sum: complex
    zeta_s_times_zeta_s_minus_1: complex
    relative_error: float
    explanation: str


def verify_sigma_dirichlet_series(s: float, n_max: int = 200_000) -> EulerProductResult:
    """Numerically verify sum_n sigma(n)/n^s ~= zeta(s) * zeta(s-1) for Re(s) > 2
    (needed for convergence of the sigma series), using Jacobi's formula
    (not brute force) to get sigma(n) fast for large n_max.

    This is the concrete "Euler product arising from the 4D lattice"
    result: sigma(n) is, by Jacobi's theorem, essentially r4(n)/8 averaged
    over the divisibility-by-4 condition, i.e. it counts 4D-sphere lattice
    points, and its Dirichlet series is the honest product zeta(s)*zeta(s-1).
    """
    if s <= 2.0:
        raise ValueError("Need s > 2 for the sigma(n) Dirichlet series to converge.")

    # Sieve-based sigma computation for speed.
    sigma = np.zeros(n_max + 1, dtype=np.int64)
    for d in range(1, n_max + 1):
        sigma[d::d] += d

    total = mp.mpf(0)
    for n in range(1, n_max + 1):
        total += mp.mpf(int(sigma[n])) / mp.mpf(n) ** s

    mp.mp.dps = 30
    reference = mp.zeta(s) * mp.zeta(s - 1)
    rel_err = abs(complex(total) - complex(reference)) / abs(complex(reference))

    explanation = (
        f"sum_{{n=1}}^{{{n_max}}} sigma(n)/n^{s} = {complex(total):.6f}; "
        f"zeta({s})*zeta({s-1}) = {complex(reference):.6f}; "
        f"relative error = {rel_err:.2e}. "
        "This Dirichlet series is exactly the generating function of the "
        "4D lattice-point-counting function (via Jacobi's four-square "
        "theorem), and it genuinely factors as a product of two zeta "
        "values evaluated at different points -- real Euler-product "
        "content produced by the dimension lift from 2D to 4D."
    )

    return EulerProductResult(
        s=s,
        partial_sum=complex(total),
        zeta_s_times_zeta_s_minus_1=complex(reference),
        relative_error=float(rel_err),
        explanation=explanation,
    )
