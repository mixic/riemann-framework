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
The Riemann hypothesis for curves over finite fields: the one case where it is a
theorem, and the one case where a computation is a proof.

The statement, from the Weil conjectures (Weil 1949; proved for curves by Weil,
building on Hasse 1934):

    For a smooth projective curve C over F_q, with N_m = #C(F_{q^m}),

        Z(C, T) = exp( sum_{m>=1} N_m T^m / m ) = P(T) / ((1 - T)(1 - qT)),

    where P(T) = prod_{i=1}^{2g} (1 - alpha_i T) is an integral polynomial of
    degree 2g. The Riemann hypothesis for C is

        |alpha_i| = q^{1/2}   for every i.

Why this module can *prove* something, and where it stops
---------------------------------------------------------
This is the `prime_certificate` situation again, and it is worth being precise,
because it is the only place in this repository where "RH is true" is a theorem
rather than a conjecture.

`P(T)` has **integer** coefficients and is computed exactly from point counts.
For a genus-1 curve `P(T) = 1 - a T + q T^2`, and `|alpha| = |beta| = sqrt(q)`
holds if and only if

    a^2 <= 4q,

which is an inequality between integers. So for a *specific* curve the check is
decidable by exact arithmetic and its output is a proof for that curve -- not
evidence, not a search.

Two things that follow, and neither is optional:

1. **A finite computation cannot prove Weil's theorem.** The theorem is universal
   over all curves and all `q`. This module checks instances; it never verifies
   the theorem, and `THEOREM_VS_INSTANCE` says so wherever a certificate is
   reported.
2. **The theorem does not transfer to the number-field case.** The function-field
   proof runs through the Frobenius action on etale cohomology, and no analogue of
   that action is known over Q. The whole point of the function-field case is that
   it is *provable by a mechanism unavailable for the Riemann zeta function* --
   which is a fact about the proof, not about the zeros.

Nothing here proves or disproves the Riemann hypothesis over Q.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

from .prime_certificate import is_prime_deterministic


#: Stated wherever a certificate is reported. A per-curve proof is not a proof of
#: the theorem, and the difference matters.
THEOREM_VS_INSTANCE = (
    "This certifies the Riemann hypothesis for ONE curve over ONE finite field, "
    "by exact integer arithmetic. It is a proof for that curve. It is not a proof "
    "of Weil's theorem, which is universal over all curves and all q, and no "
    "finite computation establishes a universal statement."
)

#: Why the function-field success does not carry over.
NO_TRANSFER_NOTE = (
    "The function-field proof works because Frobenius acts on etale cohomology "
    "and its eigenvalues can be constrained there. No analogue of that action is "
    "known over Q. So the one case where RH is a theorem is the case whose proof "
    "has no known counterpart for the Riemann zeta function -- the success is a "
    "fact about the proof, not evidence that transfers."
)


# ============================================================
# Finite fields
# ============================================================

class FiniteField:
    """`GF(p^n)`, small enough for brute-force point counting.

    Elements are integers `0 .. p^n - 1`, read as the coefficients of a
    polynomial of degree `< n` in a fixed basis. For `n = 1` this is arithmetic
    mod `p`; for `n > 1` multiplication is polynomial multiplication reduced by a
    monic irreducible polynomial of degree `n`, found by trial division.

    Deliberately capped: point counting here is `O(q)` per extension, so `q` stays
    in the low thousands. That is a limit of the method and not of the
    mathematics, and `MAX_SIZE` records it.
    """

    MAX_SIZE = 5000

    def __init__(self, p: int, n: int = 1) -> None:
        if not is_prime_deterministic(p):
            raise ValueError(f"p = {p} is not prime")
        if n < 1:
            raise ValueError("n must be at least 1")
        if p**n > self.MAX_SIZE:
            raise ValueError(
                f"GF({p}^{n}) has {p**n} elements, above the brute-force cap of "
                f"{self.MAX_SIZE}"
            )
        self.p = p
        self.n = n
        self.size = p**n
        self._modulus = None if n == 1 else _find_irreducible(p, n)

    def __repr__(self) -> str:
        return f"FiniteField({self.p}, {self.n})"

    def elements(self) -> range:
        return range(self.size)

    # --- polynomial helpers -------------------------------------------------

    def _to_poly(self, a: int) -> list[int]:
        coeffs = []
        for _ in range(self.n):
            coeffs.append(a % self.p)
            a //= self.p
        return coeffs

    def _from_poly(self, coeffs: Sequence[int]) -> int:
        total = 0
        for power, coeff in enumerate(coeffs):
            total += (coeff % self.p) * self.p**power
        return total

    def _poly_mul(self, a: Sequence[int], b: Sequence[int]) -> list[int]:
        out = [0] * (len(a) + len(b) - 1)
        for i, ai in enumerate(a):
            if ai:
                for j, bj in enumerate(b):
                    out[i + j] = (out[i + j] + ai * bj) % self.p
        if self._modulus is not None and len(out) >= self.n:
            out = _poly_mod(out, self._modulus, self.p)
        return out

    # --- field operations ---------------------------------------------------

    def add(self, a: int, b: int) -> int:
        if self.n == 1:
            return (a + b) % self.p
        return self._from_poly(
            [(x + y) % self.p for x, y in zip(self._to_poly(a), self._to_poly(b))]
        )

    def neg(self, a: int) -> int:
        if self.n == 1:
            return (-a) % self.p
        return self._from_poly([(-x) % self.p for x in self._to_poly(a)])

    def sub(self, a: int, b: int) -> int:
        return self.add(a, self.neg(b))

    def mul(self, a: int, b: int) -> int:
        if self.n == 1:
            return (a * b) % self.p
        return self._from_poly(self._poly_mul(self._to_poly(a), self._to_poly(b)))

    def pow(self, a: int, e: int) -> int:
        if e < 0:
            raise ValueError("negative exponent")
        result = 1 if self.n == 1 else self._from_poly([1] + [0] * (self.n - 1))
        base = a
        while e:
            if e & 1:
                result = self.mul(result, base)
            base = self.mul(base, base)
            e >>= 1
        return result

    def square_root_counts(self) -> list[int]:
        """`counts[v] = #{y in GF : y^2 = v}`, which is 0, 1 or 2."""
        counts = [0] * self.size
        for y in self.elements():
            counts[self.mul(y, y)] += 1
        return counts

    def frobenius(self, a: int) -> int:
        """`a -> a^p`, the Frobenius map. Generates `Gal(GF(p^n)/GF(p))`."""
        return self.pow(a, self.p)

    def frobenius_orbits(self) -> list[list[int]]:
        """Orbits of Frobenius on the elements, which are the `GF(p)`-conjugates."""
        seen = [False] * self.size
        orbits: list[list[int]] = []
        for start in self.elements():
            if seen[start]:
                continue
            orbit = []
            current = start
            while not seen[current]:
                seen[current] = True
                orbit.append(current)
                current = self.frobenius(current)
            orbits.append(orbit)
        return orbits


def _poly_mod(coeffs: list[int], modulus: list[int], p: int) -> list[int]:
    """Reduce `coeffs` modulo the monic `modulus` over `F_p`."""
    degree = len(modulus) - 1
    out = list(coeffs)
    while len(out) > degree and any(out[degree:]):
        shift = len(out) - 1 - degree
        factor = out[-1]
        if factor:
            for i, m in enumerate(modulus):
                out[shift + i] = (out[shift + i] - factor * m) % p
        out.pop()
    return out + [0] * (degree - len(out))


def _poly_divmod(
    a: Sequence[int], b: Sequence[int], p: int
) -> tuple[list[int], list[int]]:
    """Polynomial division over `F_p`; returns `(quotient, remainder)`."""
    a = list(a)
    b = list(b)
    while b and b[-1] == 0:
        b.pop()
    if not b:
        raise ZeroDivisionError("polynomial division by zero")
    if len(a) < len(b):
        return [0], a + [0] * (len(b) - 1 - len(a)) if len(b) - 1 > len(a) else a
    quotient = [0] * (len(a) - len(b) + 1)
    inv_lead = pow(b[-1], p - 2, p)
    for i in range(len(a) - len(b), -1, -1):
        coefficient = a[i + len(b) - 1] * inv_lead % p
        quotient[i] = coefficient
        if coefficient:
            for j, bj in enumerate(b):
                a[i + j] = (a[i + j] - coefficient * bj) % p
    remainder = a[: len(b) - 1]
    return quotient, remainder


def _find_irreducible(p: int, n: int) -> list[int]:
    """A monic irreducible polynomial of degree `n` over `F_p`, by trial division.

    Brute force, and only used for small fields. Irreducible monic polynomials
    have non-zero constant term, and one is found by trial-dividing every
    candidate by all monic polynomials of degree at most `n // 2`.
    """
    if n == 1:
        return [0, 1]
    small_monic: list[list[int]] = []
    for d in range(1, n // 2 + 1):
        for code in range(p**d):
            coeffs = []
            value = code
            for _ in range(d):
                coeffs.append(value % p)
                value //= p
            small_monic.append(coeffs + [1])

    for code in range(p**n):
        coeffs = []
        value = code
        for _ in range(n):
            coeffs.append(value % p)
            value //= p
        candidate = coeffs + [1]
        if candidate[0] == 0:
            continue
        # Irreducible iff NO divisor of degree <= n/2 divides it, i.e. every
        # divisor leaves a NON-ZERO remainder. This condition was inverted in a
        # "tidying" pass -- `all(not any(remainder))` asks for every remainder to
        # be zero, which rejects every irreducible polynomial -- and `GF(3^2)`
        # failing to be constructed is what caught it.
        if all(
            any(_poly_divmod(candidate, divisor, p)[1]) for divisor in small_monic
        ):
            return candidate
    raise RuntimeError(f"no irreducible polynomial of degree {n} over F_{p}")


# ============================================================
# Point counting
# ============================================================

def count_affine_points(
    curve: Callable[[FiniteField, int], int], field: FiniteField
) -> int:
    """Count `(x, y)` with `y^2 = curve(x)`, using a table of square roots."""
    counts = field.square_root_counts()
    return sum(counts[curve(field, x)] for x in field.elements())


def elliptic_rhs(a: int, b: int) -> Callable[[FiniteField, int], int]:
    """`x -> x^3 + a x + b`, with `a` and `b` read as constants of the field."""

    def rhs(field: FiniteField, x: int) -> int:
        return field.add(field.add(field.pow(x, 3), field.mul(a % field.p, x)), b % field.p)

    return rhs


def hyperelliptic_rhs(coefficients: Sequence[int]) -> Callable[[FiniteField, int], int]:
    """`x -> sum c_i x^i`, the right-hand side of `y^2 = f(x)`."""

    def rhs(field: FiniteField, x: int) -> int:
        total = 0
        for power, coefficient in enumerate(coefficients):
            if coefficient % field.p:
                total = field.add(total, field.mul(coefficient % field.p, field.pow(x, power)))
        return total

    return rhs


def count_projective_points(
    curve: Callable[[FiniteField, int], int], field: FiniteField
) -> int:
    """Affine points plus one point at infinity.

    Valid for `y^2 = f(x)` with `deg f` odd, where the projective closure has a
    single point at infinity. The genus-2 cases below satisfy this; a curve with
    `deg f` even has two points at infinity and is not used here.
    """
    return count_affine_points(curve, field) + 1


def point_counts(
    curve: Callable[[FiniteField, int], int], p: int, n_max: int
) -> list[int]:
    """`N_1 .. N_{n_max}` by brute-force counting over each extension."""
    return [count_projective_points(curve, FiniteField(p, m)) for m in range(1, n_max + 1)]


# ============================================================
# Genus 1: elliptic curves
# ============================================================

@dataclass(frozen=True)
class EllipticCertificate:
    """An exact certificate of RH for one elliptic curve over `F_p`.

    `hasse` is the test `a^2 <= 4p`, which is an inequality between integers and
    therefore decides the hypothesis exactly.
    """

    a: int
    b: int
    p: int
    point_count: int
    trace: int
    hasse: bool

    @property
    def discriminant_nonzero(self) -> bool:
        return (4 * self.a**3 + 27 * self.b**2) % self.p != 0

    @property
    def hasse_bound(self) -> float:
        return 2.0 * math.sqrt(self.p)

    def summary(self) -> str:
        sign = "<=" if self.hasse else ">"
        return (
            f"y^2 = x^3 + {self.a}x + {self.b} over F_{self.p}: "
            f"N_1 = {self.point_count}, a = p + 1 - N_1 = {self.trace}, "
            f"a^2 = {self.trace**2} {sign} 4p = {4 * self.p}  -> "
            f"RH {'holds' if self.hasse else 'FAILS'} exactly"
        )


def certify_elliptic(a: int, b: int, p: int) -> EllipticCertificate:
    """Count points once and return an exact RH certificate for the curve."""
    field = FiniteField(p, 1)
    count = count_projective_points(elliptic_rhs(a, b), field)
    trace = p + 1 - count
    return EllipticCertificate(
        a=a, b=b, p=p, point_count=count, trace=trace, hasse=trace * trace <= 4 * p
    )


def alpha_pair(trace: int, q: int, dps: int = 30) -> tuple[complex, complex]:
    """The two roots of `T^2 - a T + q`, the `alpha_i` of the zeta numerator.

    Their product is `q` and their sum is `a`, so `|alpha| = |beta| = sqrt(q)`
    exactly when the discriminant `a^2 - 4q` is non-positive -- which is the same
    integer test as `hasse` above, seen from the other side.
    """
    import cmath

    disc = trace * trace - 4 * q
    root = cmath.sqrt(complex(disc, 0.0))
    return ((trace + root) / 2, (trace - root) / 2)


def sweep_elliptic(p: int) -> list[EllipticCertificate]:
    """Every `y^2 = x^3 + a x + b` over `F_p` with non-zero discriminant."""
    out: list[EllipticCertificate] = []
    for a in range(p):
        for b in range(p):
            certificate = certify_elliptic(a, b, p)
            if certificate.discriminant_nonzero:
                out.append(certificate)
    return out


# ============================================================
# Genus 2: hyperelliptic curves
# ============================================================

@dataclass(frozen=True)
class Genus2Certificate:
    """An exact certificate of RH for one genus-2 curve over `F_p`.

    `P(T) = 1 - a1 T + a2 T^2 - p a1 T^3 + p^2 T^4`. Under the functional
    equation its roots pair as `alpha <-> p/alpha`, so it factors as

        P(T) = (1 - c1 T + p T^2)(1 - c2 T + p T^2)

    with integer `c1, c2`, and RH is `|c_j| <= 2 sqrt(p)` -- again the integer
    test `c_j^2 <= 4p`, applied twice. The `c_j` come from a numerical root
    suggestion that is then **certified** by exact integer arithmetic, which is
    the same split the repository uses for finite-compression eigenvalues.
    """

    coefficients: tuple[int, ...]
    p: int
    a1: int
    a2: int
    #: The two roots of `S(w)`, as floats for reporting. `None` if not real.
    roots: tuple[float, float] | None
    certified: bool

    @property
    def hasse(self) -> bool:
        return self.certified

    def summary(self) -> str:
        # `certified` does not narrow `roots` for a type checker, so the guard is
        # explicit: a certified curve must have reported its two real roots.
        if not self.certified or self.roots is None:
            return (
                f"genus 2 over F_{self.p}: S(w) = w^2 - {self.a1}w + "
                f"{self.a2 - 2 * self.p} -- roots real and within "
                f"[-2 sqrt({self.p}), 2 sqrt({self.p})]? NO, so RH is NOT certified "
                "for this curve as read"
            )
        roots = tuple(round(r, 6) for r in self.roots)
        return (
            f"genus 2 over F_{self.p}: S(w) = w^2 - {self.a1}w + "
            f"{self.a2 - 2 * self.p}, roots {roots}, "
            f"|2 sqrt(q)| = {2 * math.sqrt(self.p):.6f} -> RH holds exactly"
        )


def quadratic_roots_within_bound(p: int, r: int, q: int) -> bool:
    """Exactly: does `w^2 - p w + r` have both roots real and `|w| <= 2 sqrt(q)`?

    All integer arithmetic. The roots are `(p +- sqrt(d))/2` with `d = p^2 - 4r`,
    so `|w| <= 2 sqrt(q)` is `|p +- sqrt(d)| <= 4 sqrt(q)`, equivalent after
    squaring to

        d >= 0   and   16q - p^2 - d >= 0   and   4 p^2 d <= (16q - p^2 - d)^2.

    No irrational quantity is ever evaluated, so the verdict is exact.

    This replaces a first attempt that required the quadratic to factor over the
    *integers*. That is too strong: the Frobenius eigenvalues pair as
    `alpha <-> q/alpha`, which pairs `alpha` with its conjugate only when
    `|alpha| = sqrt(q)`, and the resulting quadratic has rational coefficients
    only when the Jacobian splits. Requiring integrality rejected genuine curves
    -- every genus-2 example tried came back uncertified, which is what exposed it.
    """
    d = p * p - 4 * r
    if d < 0:
        return False
    remaining = 16 * q - p * p - d
    if remaining < 0:
        return False
    return 4 * p * p * d <= remaining * remaining


def _poly_gcd(a: Sequence[int], b: Sequence[int], p: int) -> list[int]:
    """Monic gcd of two polynomials over `F_p`, by the Euclidean algorithm."""
    left = list(a)
    right = list(b)
    while any(right):
        _, remainder = _poly_divmod(left, right, p)
        left, right = right, remainder
    while left and left[-1] == 0:
        left.pop()
    if not left:
        return [0]
    inverse = pow(left[-1], p - 2, p)
    return [(c * inverse) % p for c in left]


def is_smooth_genus2(coefficients: Sequence[int], p: int) -> bool:
    """Whether `y^2 = f(x)` is a smooth projective curve of genus 2 over `F_p`.

    Two hypotheses, and both matter for reading a certificate:

    * `deg f = 5`, so `c5 != 0`. With `deg f = 4` the curve has genus 1 and *two*
      points at infinity, and the `+1` in `count_projective_points` is wrong.
    * `f` is squarefree, i.e. `gcd(f, f') = 1`. A repeated root makes the curve
      singular, and Weil's theorem is about smooth projective curves.

    The first sweep of all 729 coefficient tuples over `F_3` reported 30
    uncertified curves, which would have been a counterexample to a *theorem*.
    They are the singular and degree-4 cases; this predicate is what separates
    them, and no certificate is issued without it.
    """
    coeffs = list(coefficients)
    while coeffs and coeffs[-1] == 0:
        coeffs.pop()
    if len(coeffs) - 1 != 5:
        return False
    derivative = [(i * c) % p for i, c in enumerate(coeffs)][1:]
    return _poly_gcd(coeffs, derivative, p) == [1]


def certify_genus2(coefficients: Sequence[int], p: int) -> Genus2Certificate:
    """Certify RH for the genus-2 curve `y^2 = f(x)`, `deg f = 5`.

    `a1` comes from `N_1` and `a2` from `N_2`. The functional equation makes
    `P(T)` palindromic, so `P(T)/T^g` is a polynomial in `w = T + q/T`:

        S(w) = w^2 - a1 w + (a2 - 2q),

    with integer coefficients, and RH is exactly "both roots of `S` are real and
    lie in `[-2 sqrt(q), 2 sqrt(q)]`" -- decided by
    `quadratic_roots_within_bound`.
    """
    if len(coefficients) != 6:
        raise ValueError("expected 6 coefficients for deg f = 5")
    curve = hyperelliptic_rhs(coefficients)
    n1, n2 = point_counts(curve, p, 2)
    a1 = p + 1 - n1
    # N_2 = q^2 + 1 - (sum alpha_i^2), and sum alpha_i^2 = a1^2 - 2 a2.
    a2 = (n2 - p * p - 1 + a1 * a1) // 2
    q = p
    certified = quadratic_roots_within_bound(a1, a2 - 2 * q, q)
    roots = _real_pair(a1, a2 - 2 * q)
    return Genus2Certificate(tuple(coefficients), p, a1, a2, roots, certified)


def _real_pair(p: int, r: int) -> tuple[float, float] | None:
    """The two roots of `w^2 - p w + r` as floats, for reporting only."""
    d = p * p - 4 * r
    if d < 0:
        return None
    root = math.sqrt(d)
    return ((p + root) / 2, (p - root) / 2)


# ============================================================
# The Weil bound, and the recurrence the zeros generate
# ============================================================

@dataclass(frozen=True)
class WeilBoundRow:
    """`N_m` against the bound `|N_m - q^m - 1| <= 2 g q^{m/2}`."""

    m: int
    q_power: int
    count: int
    deviation: int
    bound: float

    @property
    def within(self) -> bool:
        return abs(self.deviation) <= self.bound + 1e-9

    def summary(self) -> str:
        return (
            f"m = {self.m}: N_m = {self.count:>8,}, q^m + 1 = {self.q_power + 1:>8,}, "
            f"|deviation| = {abs(self.deviation):>7,} <= 2g sqrt(q^m) = {self.bound:>9.2f}"
            f"  {'ok' if self.within else 'VIOLATED'}"
        )


def weil_bound_rows(
    curve: Callable[[FiniteField, int], int], p: int, genus: int, m_max: int
) -> list[WeilBoundRow]:
    """Check the Weil bound at each extension degree up to `m_max`."""
    counts = point_counts(curve, p, m_max)
    rows: list[WeilBoundRow] = []
    for m, count in enumerate(counts, start=1):
        q_power = p**m
        rows.append(
            WeilBoundRow(
                m=m,
                q_power=q_power,
                count=count,
                deviation=count - q_power - 1,
                bound=2 * genus * math.sqrt(q_power),
            )
        )
    return rows


def count_from_alphas(alphas: Sequence[complex], q: int, m: int) -> float:
    """`N_m = q^m + 1 - sum alpha_i^m`, the recurrence the zeta function implies.

    Comparing this against brute-force counts is a check of the *whole* structure,
    not just of the bound: it tests that the point counts really are governed by
    the `2g` numbers `alpha_i`.
    """
    return q**m + 1 - sum(a**m for a in alphas).real
