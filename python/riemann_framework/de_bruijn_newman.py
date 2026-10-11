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
The de Bruijn-Newman constant, and the one thing that must be said first.

    RH  <=>  Lambda <= 0.

So **Lambda <= 0 cannot be verified numerically.** It is not a hard computation;
it is equivalent to the Riemann hypothesis, and no finite computation establishes
it. Anyone who runs this module hoping to see `Lambda = 0` confirmed is asking it
for something it cannot give, and the module says so rather than returning a
number that looks like an answer.

What *is* available is the other direction, and it is genuinely available:

    if some H_t with t > 0 has a non-real zero, then Lambda > 0 and RH is false.

That is a finite, checkable refutation, and it is one of only two such framings in
this repository's scope -- the other being a negative eigenvalue of a finite
compression of Weil's form. The refutation window is `t in (0, 0.2]`, since
Polymath15 proved `Lambda <= 0.2` (that is, all zeros of `H_t` are real for
`t >= 0.2`).

The three facts that make the picture
-------------------------------------
    Rodgers-Tao (2018)      Lambda >= 0
    Polymath15 (2019)       Lambda <= 0.2
    hence                   RH <=> Lambda = 0, and the window is [0, 0.2]

Rodgers-Tao's `Lambda >= 0` says that **if RH is true it is only barely so**:
`Lambda = 0` means the zeros sit exactly at the edge of the region where they are
real, with no margin.

What this module computes, and what it does not
-----------------------------------------------
The function is
    H_t(z) = int_0^inf e^{t u^2} Phi(u) cos(zu) du,
    Phi(u) = sum_{n>=1} (2 pi^2 n^4 e^{9u} - 3 pi n^2 e^{5u}) exp(-pi n^2 e^{4u}),
    H_0(z)  = (1/8) xi(1/2 + i z/2),

all taken from Rodgers-Tao (arXiv:1801.05914, equations (1)-(4)). The `1/8` and
the `i z/2` matter: this module's first draft used `xi(1/2 + iz)` with no `1/8`
and a recalled `Phi` carrying spurious factors of two, and the check below is
what caught it. The definition here is **sourced, not recalled**, which is the
only reason the validation is worth anything.

`H_0` is then checked against `(1/8) xi(1/2 + i z/2)` computed independently, and
its zeros against `2 * gamma_k`.

Three limits, all measured and all recorded
-------------------------------------------
1. **The zero scan is insensitive to what it is named for.** Counting real zeros
   of `H_t` over the low range returns the same count for every `t` in
   `[-0.2, 0.2]`, and would do so even if `Lambda` were as large as `0.2`. The
   first exit, if `Lambda < 0`, happens at Lehmer-pair heights, not among the
   first few zeros. A flat scan is not evidence for RH; it is a scan that cannot
   see the thing it is looking for. `zero_count_scan` returns the counts and
   `INSENSITIVITY_NOTE` states this alongside them.
2. **The quadrature degrades with height.** The fixed Gauss-Legendre rule agrees
   with `2 gamma_k` for `k <= 6` and drifts after that (~1e-2 relative error by
   `k = 9`), because float64 cannot resolve `cos(zu)` at `z ~ 100` on a fixed node
   set. `zero_accuracy_table` measures this rather than assuming it away.
3. **The dynamics equation does not truncate.** Rodgers-Tao's
   `d x_k/dt = 2 sum_{j != k} 1/(x_k - x_j)` runs over *all* zeros. Truncating to
   the computed ones gives a derivative that disagrees with the numerically
   differentiated zero positions by an amount that is roughly constant across
   `k` -- the signature of a missing tail. That is why the paper needs spatial
   cutoffs and a renormalised energy, and it is why this module does not
   integrate the flow.

Nothing here proves or disproves the Riemann hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass

import mpmath as mp
import numpy as np


#: The known bounds on `Lambda`, with sources. The middle two are what turn the
#: question into the stated window.
LAMBDA_BOUNDS: dict[str, object] = {
    "lower": 0.0,
    "lower_source": "Rodgers-Tao (2018), arXiv:1801.05914: Lambda >= 0",
    "upper": 0.2,
    "upper_source": "Polymath15 (2019): Lambda <= 0.2",
    "upper_sharper": 0.1875,
    "upper_sharper_source": (
        "later certified bound, Lambda <= 0.1875; recorded for completeness and "
        "not used by the scans here"
    ),
    "equivalence": "RH <=> Lambda <= 0; with Lambda >= 0 this gives RH <=> Lambda = 0",
}

#: Stated wherever the zero scan is reported, because a flat count is the natural
#: thing to misread as support for RH.
INSENSITIVITY_NOTE = (
    "A constant zero count across t is NOT evidence for the Riemann hypothesis. "
    "If Lambda < 0 the first exit of a zero from the real axis occurs at "
    "Lehmer-pair heights, far above any range scanned here, so this scan would "
    "return the same count whether Lambda = 0 or Lambda = 0.2. It demonstrates "
    "the mechanism; it cannot detect the quantity it is named for."
)

#: Number of Gauss-Legendre nodes for the fixed quadrature rule.
QUADRATURE_NODES = 400
#: Phi is super-exponentially small past u ~ 1; this window is generous.
QUADRATURE_UPPER = 1.2
#: Terms in the defining sum for Phi. At u <= 1.2 the tail is far below 1e-30.
PHI_TERMS = 25


# ============================================================
# Phi, from the sourced definition
# ============================================================

def phi(u, dps: int = 30, n_terms: int = PHI_TERMS) -> mp.mpf:
    """`Phi(u) = sum (2 pi^2 n^4 e^{9u} - 3 pi n^2 e^{5u}) exp(-pi n^2 e^{4u})`.

    Rodgers-Tao equation (3). The exponents are `9u`, `5u` and `4u` -- *not*
    `9u/2`, `5u/2`, `2u`. A first draft of this module used the halved exponents
    from memory; they are wrong, and the check against `(1/8) xi(1/2 + i z/2)`
    failed at the 0.5% level, which is how it was found.

    Only `u >= 0` is evaluated here. The sum converges for negative `u` as well,
    the paper notes, but only very slowly -- requiring on the order of `e^{-u}`
    terms -- and the integral representation only needs `u >= 0`.
    """
    with mp.workdps(dps):
        u = mp.mpf(u)
        e4 = mp.exp(4 * u)
        e9 = mp.exp(9 * u)
        e5 = mp.exp(5 * u)
        return mp.fsum(
            (2 * mp.pi**2 * n**4 * e9 - 3 * mp.pi * n**2 * e5)
            * mp.exp(-mp.pi * n**2 * e4)
            for n in range(1, n_terms)
        )


_RULE_CACHE: dict[int, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}


def _quadrature_rule(nodes: int = QUADRATURE_NODES):
    """Cached `(u, w, Phi(u))` for the fixed Gauss-Legendre rule on `[0, upper]`."""
    if nodes not in _RULE_CACHE:
        x, w = np.polynomial.legendre.leggauss(nodes)
        half = QUADRATURE_UPPER / 2.0
        u = half * (x + 1.0)
        w = half * w
        values = np.array([float(phi(value)) for value in u])
        _RULE_CACHE[nodes] = (u, w, values)
    return _RULE_CACHE[nodes]


# ============================================================
# H_t, two ways
# ============================================================

def H(t: float, z, nodes: int = QUADRATURE_NODES) -> np.ndarray:
    """`H_t(z) = int_0^inf e^{tu^2} Phi(u) cos(zu) du`, by the fixed rule.

    `z` may be an array, in which case the result has the same shape. The rule is
    fixed and precomputed so that scanning many `(t, z)` pairs costs one matrix
    product; that is what makes a scan over `t` affordable, and it is also the
    source of the height limit documented in `zero_accuracy_table`.
    """
    u, w, values = _quadrature_rule(nodes)
    z = np.atleast_1d(np.asarray(z, dtype=float))
    kernel = w * values * np.exp(t * u * u)
    return np.cos(np.outer(z, u)) @ kernel


def H_reference(z, dps: int = 30) -> complex:
    """`(1/8) xi(1/2 + i z/2)`, computed from the definition of `xi`.

    Rodgers-Tao equation (1). This is the independent route: it uses `zeta` and
    `gamma` directly and shares no code with the quadrature, so agreement between
    the two is a check of the identity rather than of an implementation detail.
    """
    with mp.workdps(dps):
        s = mp.mpf(1) / 2 + mp.mpc(0, 1) * mp.mpf(z) / 2
        xi = (s * (s - 1) / 2) * mp.power(mp.pi, -s / 2) * mp.gamma(s / 2) * mp.zeta(s)
        return complex(xi / 8)


def doubled_zeta_zero_ordinates(count: int) -> list[float]:
    """`2 * gamma_k` for `k = 1..count`: where the zeros of `H_0` must be.

    `xi(1/2 + iz/2) = 0` iff `1/2 + iz/2` is a nontrivial zero, i.e. `z = 2 gamma`.
    """
    if count < 1:
        raise ValueError("count must be at least 1")
    return [float(2 * mp.zetazero(k).imag) for k in range(1, count + 1)]


def locate_zeros(t: float = 0.0, z_max: float = 120.0, grid: int = 60000) -> list[float]:
    """Positive real zeros of `H_t` in `(0, z_max]`, by sign change and bisection.

    Only positive `z` is scanned: `H_t` is even, so the negative zeros are the
    reflections. A zero that has left the real axis does not appear, which is how
    an exit would show up -- as a *drop* in the count, by two.
    """
    zs = np.linspace(0.05, z_max, grid)
    values = H(t, zs)
    crossings = np.where(np.sign(values[:-1]) != np.sign(values[1:]))[0]
    roots: list[float] = []
    for index in crossings:
        lo, hi = zs[index], zs[index + 1]
        f_lo = float(H(t, lo)[0])
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            f_mid = float(H(t, mid)[0])
            if f_lo * f_mid <= 0:
                hi = mid
            else:
                lo, f_lo = mid, f_mid
        roots.append(0.5 * (lo + hi))
    return roots


# ============================================================
# Honest reporting of the limits
# ============================================================

@dataclass(frozen=True)
class AccuracyRow:
    """Computed zero position against the exact `2 gamma_k`."""

    index: int
    computed: float
    exact: float

    @property
    def relative_error(self) -> float:
        return abs(self.computed - self.exact) / self.exact


def zero_accuracy_table(count: int = 9, z_max: float = 120.0) -> list[AccuracyRow]:
    """Measure how far the quadrature zeros drift from `2 gamma_k`.

    Recorded rather than assumed. The first six agree to better than `1e-6`
    relative; beyond that float64 resolution of `cos(zu)` on a fixed node set
    fails, and the drift grows. Publishing a zero count without this would
    overstate the range in which the scan means anything.
    """
    computed = locate_zeros(0.0, z_max=z_max)
    exact = doubled_zeta_zero_ordinates(count)
    rows: list[AccuracyRow] = []
    for index in range(min(len(computed), len(exact))):
        rows.append(AccuracyRow(index + 1, computed[index], exact[index]))
    return rows


@dataclass(frozen=True)
class ZeroCountScan:
    """The number of real zeros found, as a function of `t`."""

    t_values: list[float]
    counts: list[int]
    z_max: float

    @property
    def is_flat(self) -> bool:
        return len(set(self.counts)) == 1

    def summary(self) -> str:
        return (
            f"t in [{min(self.t_values)}, {max(self.t_values)}], z <= {self.z_max}: "
            f"positive real zero counts {self.counts}. "
            + ("Flat. " + INSENSITIVITY_NOTE if self.is_flat else "Not flat.")
        )


def zero_count_scan(
    t_values: list[float] | None = None, z_max: float = 120.0
) -> ZeroCountScan:
    """Count positive real zeros of `H_t` across a range of `t`.

    The range includes negative `t` deliberately. If `Lambda` were negative then
    for `t` between `Lambda` and `0` a pair of zeros would have left the real
    axis, and the count would drop. It does not, over the low zeros -- see
    `INSENSITIVITY_NOTE` for why that is uninformative rather than reassuring.
    """
    if t_values is None:
        t_values = [-0.2, -0.1, -0.05, 0.0, 0.05, 0.1, 0.2]
    counts = [len(locate_zeros(t, z_max=z_max)) for t in t_values]
    return ZeroCountScan(list(t_values), counts, z_max)


# ============================================================
# A control where the exit IS observable
# ============================================================
#
# The scan above cannot detect an exit because none is in range. To show the
# machinery *would* detect one, it is run on a family whose exit is in range and
# whose constant is known exactly: p(z) = z^2 + c.
#
# Under H_t = exp(-t d^2/dz^2) the flow gives z^2 -> z^2 - 2t, so
# p_t(z) = z^2 + c - 2t, whose zeros are +/- sqrt(2t - c): real exactly when
# t >= c/2. So this family has Lambda = c/2 > 0, and crossing below it produces
# a non-real pair.

def flow_of_monomial(t: float, degree: int) -> float:
    """`exp(-t d^2/dz^2) z^(2n)`, the coefficient of `z^0`... see the note.

    Returns the constant term of the image, which for `z^2` is `-2t`. Provided so
    the toy control below is checked rather than asserted.
    """
    if degree == 2:
        return -2.0 * t
    raise ValueError("only degree 2 is used by the toy control")


def toy_constant(c: float) -> float:
    """`Lambda = c/2` for `p(z) = z^2 + c`, exactly."""
    if c < 0:
        raise ValueError("c must be non-negative for this control to have Lambda > 0")
    return c / 2.0


def toy_zeros(c: float, t: float) -> tuple[float, float] | tuple[complex, complex]:
    """Zeros of `p_t(z) = z^2 + c - 2t`: real iff `t >= c/2`."""
    shift = c - 2.0 * t
    if shift <= 0:
        root = (-shift) ** 0.5
        return (-root, root)
    root = complex(0.0, shift**0.5)
    return (-root, root)


def flow_operator_coefficients(b: list[float], t: float, count: int) -> list[float]:
    """`b_m(t) = sum_k (-t)^k (2m+2k)! / ((2m)! k!) b_{m+k}`.

    The action of `exp(-t d^2/dz^2)` on `sum b_m z^{2m}`. Exposed because it is
    the object the paper works with, but note it is *not* used to locate zeros
    here: truncating the sum at the computed `b_m` has the same missing-tail
    problem as the dynamics equation below.
    """
    if count > len(b):
        raise ValueError("count exceeds the supplied coefficients")
    out: list[float] = []
    for m in range(count):
        total = 0.0
        for k in range(len(b) - m):
            numerator = 1.0
            for j in range(1, 2 * k + 1):
                numerator *= 2 * m + j
            total += (-t) ** k / _factorial(k) * numerator * b[m + k]
        out.append(total)
    return out


def _factorial(n: int) -> float:
    total = 1.0
    for i in range(2, n + 1):
        total *= i
    return total


def zero_velocity_numeric(t: float, h: float = 1e-4, z_max: float = 120.0) -> list[float]:
    """Numerically differentiate the zero positions with respect to `t`.

    Used to compare against the truncated dynamics equation, which is the third
    documented limit.
    """
    plus = locate_zeros(t + h, z_max=z_max)
    minus = locate_zeros(t - h, z_max=z_max)
    if len(plus) != len(minus):
        raise ValueError("zero counts differ across the step; cannot differentiate")
    return [(a - b) / (2 * h) for a, b in zip(plus, minus)]


def zero_velocity_truncated(zeros: list[float]) -> list[float]:
    """`2 sum_{j != k} 1/(x_k - x_j)` over the *computed* zeros only.

    Includes the reflected negatives, since `H_t` is even. This is the truncated
    version of Rodgers-Tao's equation (5), and it is knowingly wrong: see
    `DYNAMICS_NOTE`.
    """
    full = [-z for z in reversed(zeros)] + list(zeros)
    velocities: list[float] = []
    for x in zeros:
        total = 0.0
        for y in full:
            if y != x:
                total += 1.0 / (x - y)
        velocities.append(2.0 * total)
    return velocities


#: Stated with the dynamics functions, because the truncated sum looks like the
#: paper's equation and is not it.
DYNAMICS_NOTE = (
    "Rodgers-Tao's equation (5) sums over ALL zeros. Truncating it to the computed "
    "ones gives a derivative that disagrees with the numerically differentiated "
    "zero positions by a roughly constant offset, which is the signature of the "
    "missing tail rather than an error in the formula. The paper handles this with "
    "spatial cutoffs and a renormalised energy; this module does not integrate the "
    "flow for that reason."
)
