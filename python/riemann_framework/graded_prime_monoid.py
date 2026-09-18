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
The graded prime-exponent monoid: a number system whose dimension increases
under multiplication, rather than one that rotates under it.

Motivation
----------
A natural-sounding proposal is: "a number system where 1 is 0-dimensional,
and multiplying introduces new dimensions the way `i` introduced a second
one." Taken literally as zero-padding (`1 -> (1,0) -> (1,0,0) -> ...`), this
has no multiplication rule at all -- it is an embedding, not an algebra, and
adds nothing.

There is exactly one multiplication rule that is *forced*, rather than
chosen, once you ask for the dimension to grow in a way compatible with
multiplication: encode a number by its vector of prime exponents, and let
multiplication be coordinatewise addition of exponent vectors. This is not a
new axiom; it is a restatement of unique factorisation. This module makes
that restatement precise and computable:

    dimension(n) := omega(n), the number of *distinct* primes dividing n
                    (dimension 0 is the number 1 itself)
    n            <-> the finite exponent vector (e_2, e_3, e_5, ...) with
                     n = prod_p p^{e_p}
    n * m        <-> exponent-vector addition, extended to whichever
                     dimension the union of the two supports needs

The resulting object is the free abelian monoid on the primes,
`bigoplus_p N_{>=0}`, presented as a direct limit of `N_{>=0}^k` under the
"pad with one more coordinate" inclusions -- exactly the
`1 -> (1,0) -> (1,0,0) -> ...` pattern, but now carrying the one
multiplication rule that pattern can support, rather than silent padding.

Why this belongs in this repository specifically
--------------------------------------------------
This is not a sixth speculative track. It is the algebraic object already
implicit in `primon_gas.py`: `l^2(N)` with basis `|n>` *is* this monoid's
group algebra, and `Tr[e^{-sH}] = zeta(s)` is exactly the statement that
summing `n^{-s}` over this graded monoid, weighted multiplicatively,
produces the Euler product. This module gives that structure an explicit
name and an explicit isomorphism, and exists mainly to make the connection
in `bridge_to_primon_gas` below checkable rather than asserted.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from itertools import product

from .primon_gas import factorize, trace_exp

# Primes are generated here rather than imported. An earlier revision of this
# module used `factorint`, `prime` and `primerange` from sympy, which is neither
# installed nor declared in `pyproject.toml`, so the module did not import at all
# and its test file failed at collection. This repository depends only on
# mpmath/numpy/scipy (`affine_reduction.py` records the same decision for its own
# gate), and `primon_gas.factorize` already does exact trial division.


@lru_cache(maxsize=None)
def _primes_up_to(limit: int) -> tuple[int, ...]:
    """Every prime `<= limit`, by sieve of Eratosthenes."""
    if limit < 2:
        return ()
    sieve = bytearray([1]) * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for candidate in range(2, math.isqrt(limit) + 1):
        if sieve[candidate]:
            start = candidate * candidate
            sieve[start::candidate] = b"\x00" * len(range(start, limit + 1, candidate))
    return tuple(index for index in range(2, limit + 1) if sieve[index])


@lru_cache(maxsize=None)
def _first_primes(count: int) -> tuple[int, ...]:
    """The first `count` primes, `p_1 ... p_count`, ascending."""
    if count <= 0:
        return ()
    # `p_k` is below `k (log k + log log k)` for k >= 6, and below 16 for the
    # small cases; double the bound until the sieve is long enough rather than
    # rely on the estimate holding at the edge.
    limit = 16 if count < 6 else int(count * (math.log(count) + math.log(math.log(count)))) + 10
    while len(_primes_up_to(limit)) < count:
        limit *= 2
    return _primes_up_to(limit)[:count]


@dataclass(frozen=True)
class GradedPrimeNumber:
    """An element of the graded prime-exponent monoid: a finite tuple of
    non-negative exponents `(e_1, e_2, ..., e_k)` for the first `k` primes
    `(2, 3, 5, ..., p_k)`. Trailing zeros are insignificant (padding), so
    two tuples that differ only by trailing zeros represent the same
    element -- this is exactly the direct-limit identification.
    """

    exponents: tuple[int, ...]

    def __post_init__(self) -> None:
        if any(e < 0 for e in self.exponents):
            raise ValueError("exponents must be non-negative")

    @property
    def dimension(self) -> int:
        """`omega(n)`: the number of *distinct* primes with nonzero exponent.

        This must count nonzero entries directly, not `len(self._trimmed())`:
        an element like `(0, 0, 1, 1)` (representing 5*7=35, with zero
        exponents at the skipped primes 2 and 3) has no *trailing* zeros to
        trim, so trimmed length would wrongly report dimension 4 instead of
        the correct 2. Internal zero exponents (unused primes below the
        largest one used) must not count towards dimension; only trailing
        zeros are insignificant padding.
        """
        return sum(1 for e in self.exponents if e != 0)

    def _trimmed(self) -> tuple[int, ...]:
        e = self.exponents
        while e and e[-1] == 0:
            e = e[:-1]
        return e

    def pad_to(self, k: int) -> "GradedPrimeNumber":
        """Embed this element into the space using the first `k` primes
        (`k >= current length`), the `1 -> (1,0) -> (1,0,0) -> ...` inclusion
        made explicit and reversible: `pad_to` never changes `to_int()`."""
        if k < len(self.exponents):
            raise ValueError(f"cannot pad down: k={k} < current length {len(self.exponents)}")
        return GradedPrimeNumber(self.exponents + (0,) * (k - len(self.exponents)))

    def to_int(self) -> int:
        """The integer `n = prod_i p_i^{e_i}` this element encodes."""
        n = 1
        for exponent, p in zip(self.exponents, _first_primes(len(self.exponents))):
            n *= p ** exponent
        return n

    def __mul__(self, other: "GradedPrimeNumber") -> "GradedPrimeNumber":
        """Multiplication = coordinatewise addition of exponent vectors,
        extended to the larger of the two dimensions -- the one
        multiplication rule compatible with unique factorisation. This is
        where "dimension changes under multiplication" becomes concrete: two
        numbers using disjoint prime supports multiply into something whose
        dimension is the *sum* of their two dimensions (see
        `test_multiplication_dimension_is_subadditive_and_exact_on_disjoint_support`)."""
        k = max(len(self.exponents), len(other.exponents))
        a, b = self.pad_to(k), other.pad_to(k)
        return GradedPrimeNumber(tuple(x + y for x, y in zip(a.exponents, b.exponents)))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GradedPrimeNumber):
            return NotImplemented
        return self._trimmed() == other._trimmed()

    def __hash__(self) -> int:
        return hash(self._trimmed())

    def __repr__(self) -> str:
        # Deliberately shows the *raw* (possibly zero-padded) exponents, not
        # the trimmed form: this is what makes `dimension_tower` below able to
        # visibly demonstrate padding (1,) vs (1,0) vs (1,0,0), even though
        # `__eq__`/`__hash__` correctly treat them as the same element.
        return f"GradedPrimeNumber(exponents={self.exponents!r}, dim={self.dimension}, n={self.to_int()})"


#: The identity element: dimension 0, the empty exponent tuple, integer 1.
ONE = GradedPrimeNumber(())


def from_int(n: int) -> GradedPrimeNumber:
    """The canonical embedding `(N_{>0}, x) -> graded prime monoid`: factorise
    `n` and read off the exponent of each prime up to the largest one
    dividing `n`. Inverse of `GradedPrimeNumber.to_int`."""
    if n < 1:
        raise ValueError("n must be a positive integer")
    if n == 1:
        return ONE
    factors = factorize(n)
    return GradedPrimeNumber(
        tuple(factors.get(p, 0) for p in _primes_up_to(max(factors)))
    )


def dimension_tower(n: int, max_dim: int) -> list[GradedPrimeNumber]:
    """The `1 -> (1,0) -> (1,0,0) -> ...` tower for a single element `n`,
    i.e. `from_int(n)` padded to every dimension from its *current ambient
    length* up to `max_dim`. All entries `to_int()` to the same `n`; only the
    ambient dimension changes, which is the padding-alone construction this
    module's docstring argues is arithmetically inert on its own -- included
    here so it can be contrasted directly against `__mul__` below, where the
    dimension change is not inert.

    The tower starts at `len(base.exponents)`, the index of the largest prime
    dividing `n`, and *not* at `base.dimension`. The two agree only when the
    exponent tuple has no internal zeros. For `n = 97` the dimension is 1 while
    the tuple has length 25, and `pad_to(1)` on it is a pad *down*, which raises.
    An earlier revision started at `base.dimension`, and its guard tested the
    same quantity, so `dimension_tower` raised for 81 of the first 100 integers
    -- every `n` not divisible by 2. Pinned by
    `test_dimension_tower_works_for_elements_with_internal_zeros`.
    """
    base = from_int(n)
    start = len(base.exponents)
    if max_dim < start:
        raise ValueError(
            f"max_dim={max_dim} is below the ambient length {start} of "
            f"from_int({n}) (whose dimension is {base.dimension}); pad_to cannot "
            "pad down"
        )
    return [base.pad_to(k) for k in range(start, max_dim + 1)]


def verify_monoid_isomorphism(n_max: int) -> "IsomorphismReport":
    """Check, by direct computation over `1..n_max`, that
    `from_int` / `to_int` is a bijection intertwining ordinary integer
    multiplication with graded-monoid multiplication:

        from_int(a) * from_int(b) == from_int(a * b)   for all a, b <= n_max

    This is the precise sense in which "the dimension-increasing number
    system" is not a new set of numbers but a repackaging of
    `(N_{>0}, x)` that makes the prime-exponent structure, and hence the
    dimension `omega(n)`, explicit.
    """
    cache: dict[int, GradedPrimeNumber] = {n: from_int(n) for n in range(1, n_max + 1)}

    def element(k: int) -> GradedPrimeNumber:
        if k not in cache:
            cache[k] = from_int(k)
        return cache[k]

    mismatches: list[tuple[int, int]] = []
    pairs_checked = 0
    for a in range(1, n_max + 1):
        for b in range(1, n_max + 1):
            pairs_checked += 1
            if element(a) * element(b) != element(a * b):
                mismatches.append((a, b))

    round_trip_ok = all(element(n).to_int() == n for n in range(1, n_max + 1))

    return IsomorphismReport(
        n_max=n_max,
        pairs_checked=pairs_checked,
        mismatches=mismatches,
        round_trip_ok=round_trip_ok,
        explanation=(
            f"Checked {pairs_checked} pairs (a,b) with 1<=a,b<={n_max}: "
            f"{'all' if not mismatches else f'{len(mismatches)} FAILED'} satisfy "
            "from_int(a)*from_int(b) == from_int(a*b). "
            f"Round-trip from_int(n).to_int()==n holds for all n<={n_max}: {round_trip_ok}."
        ),
    )


@dataclass
class IsomorphismReport:
    n_max: int
    pairs_checked: int
    mismatches: list[tuple[int, int]]
    round_trip_ok: bool
    explanation: str


def dimension_of(n: int) -> int:
    """`omega(n)`, the number of distinct prime factors of `n` -- the
    "dimension" of `n` in this number system. `dimension_of(1) == 0`."""
    return from_int(n).dimension


def bridge_to_primon_gas(n_max: int) -> "BridgeReport":
    """Make explicit the connection to `primon_gas.py` promised in this
    module's docstring: the graded monoid's elements *are* the basis `|n>`
    of `l^2(N)`, multiplication in the monoid is what makes
    `n^{-s} * m^{-s} = (nm)^{-s}` hold, and the Euler product
    `zeta(s) = prod_p (1-p^{-s})^{-1}` is the generating function of this
    monoid graded by `dimension_of`, evaluated multiplicatively rather than
    by total exponent.

    Concretely: partition `{1, ..., n_max}` by dimension (`omega(n)`), and
    report, for each dimension, how many integers up to `n_max` have that
    many distinct prime factors, and what these contribute to the truncated
    zeta sum at a sample point. This is the same sum `primon_gas.trace_exp`
    computes; here it is regrouped by the graded structure this module
    formalises, to make the link between "dimension" and "Euler factor"
    visible rather than assumed.
    """
    from collections import defaultdict

    by_dimension: dict[int, list[int]] = defaultdict(list)
    for n in range(1, n_max + 1):
        by_dimension[dimension_of(n)].append(n)

    s = 2.0
    contribution_by_dimension: dict[int, float] = {
        dim: float(sum(n ** (-s) for n in ns))
        for dim, ns in sorted(by_dimension.items())
    }
    total = sum(contribution_by_dimension.values())

    # Compare against primon_gas here rather than telling the reader to. Note
    # what this does and does not establish: the two sides are the *same* sum
    # computed two ways, so it checks that the partition by dimension is
    # complete and correctly totalled -- it does not check that the sum
    # factorises. For that, see `euler_product_from_grading` below.
    direct_trace = trace_exp(s, n_max).real
    agrees = abs(total - direct_trace) <= 1e-9 * max(1.0, abs(direct_trace))

    lines = [f"Partition of 1..{n_max} by dimension (omega(n)), and each part's"]
    lines.append(f"contribution to sum n^-{s}:")
    shown = sorted(contribution_by_dimension.items())
    cutoff = 15
    for dim, contribution in shown[:cutoff]:
        lines.append(
            f"  dimension {dim}: {len(by_dimension[dim]):5d} integers, "
            f"contributes {contribution:.6f}"
        )
    if len(shown) > cutoff:
        remaining = len(shown) - cutoff
        remaining_total = sum(c for _, c in shown[cutoff:])
        lines.append(f"  ... {remaining} higher dimensions, combined contribution {remaining_total:.6f}")
    lines.append(f"  total: {total:.6f}  (pi^2/6 = {math.pi**2/6:.6f} as n_max -> inf at s=2)")
    lines.append(
        f"  primon_gas.trace_exp({s}, {n_max}) = {direct_trace:.6f}  "
        f"-> regrouping agrees: {agrees}"
    )

    return BridgeReport(
        n_max=n_max,
        by_dimension={dim: list(ns) for dim, ns in by_dimension.items()},
        contribution_by_dimension=contribution_by_dimension,
        total=total,
        direct_trace=direct_trace,
        agrees=agrees,
        explanation="\n".join(lines),
    )


@dataclass
class BridgeReport:
    n_max: int
    by_dimension: dict[int, list[int]]
    contribution_by_dimension: dict[int, float]
    total: float
    direct_trace: float
    agrees: bool
    explanation: str


def truncated_euler_product(s: float = 2.0, prime_limit: int = 13) -> float:
    """`prod_{p <= prime_limit} 1/(1 - p^{-s})`, the Euler product over those primes.

    Cheap and uncapped: linear in the number of primes, with no enumeration of
    the monoid. This is the value the graded sum approaches as the degree cap is
    raised, so it is the reference `euler_product_from_grading` compares against.
    """
    basis = _primes_up_to(prime_limit)
    if not basis:
        raise ValueError(f"prime_limit={prime_limit} admits no primes; use >= 2")
    result = 1.0
    for p in basis:
        denominator = 1.0 - p ** (-s)
        if denominator == 0.0:
            raise ValueError(f"p^{-s} = 1 at p={p}, s={s}; the product diverges")
        result *= 1.0 / denominator
    return result


def euler_product_from_grading(
    s: float = 2.0,
    prime_limit: int = 13,
    degree_cap: int = 3,
    grading_weight: float = 1.0,
) -> "EulerProductReport":
    """The Euler product as this monoid's generating function, computed both ways.

    The claim in `bridge_to_primon_gas` is that the Euler product is what this
    number system's zeta-like sum looks like. The checkable form of that is the
    identity

        sum over exponent vectors v with 0 <= v_p <= D of
            q^{omega(v)} prod_p p^{-s v_p}
        =
        prod_{p <= P} ( 1 + q * sum_{a=1..D} p^{-s a} ),

    where the left side sums over the *monoid* and the right side is one local
    factor per prime. The local factor is what matters:

        sum_{a >= 0} q^{omega(p^a)} p^{-s a} = 1 + q * p^{-s}/(1 - p^{-s}),

    because `omega(p^a)` is 0 at `a = 0` and 1 for every `a >= 1`. At `q = 1`
    that is `1 + p^{-s}/(1-p^{-s}) = 1/(1-p^{-s})`, the Euler factor. So the
    grading by `omega` factorises, and at `q = 1` it factorises into the Euler
    product itself -- which is the sense in which the monoid structure, not a
    coincidence of the arithmetic, is what makes the primon gas trace exact.

    Enumerating the monoid is exponential in the number of primes, so the box is
    kept small and capped; the product side is linear and has no cap.
    """
    basis = _primes_up_to(prime_limit)
    if not basis:
        raise ValueError(f"prime_limit={prime_limit} admits no primes; use >= 2")
    if degree_cap < 0:
        raise ValueError(f"degree_cap must be >= 0, got {degree_cap}")
    terms = (degree_cap + 1) ** len(basis)
    if terms > 200_000:
        raise ValueError(
            f"the box would have {terms} terms; reduce degree_cap or prime_limit"
        )

    # Left side: enumerate the monoid.
    enumerated = 0.0
    for exponents in product(range(degree_cap + 1), repeat=len(basis)):
        omega = sum(1 for e in exponents if e != 0)
        term = grading_weight ** omega
        for p, e in zip(basis, exponents):
            term *= p ** (-s * e)
        enumerated += term

    # Right side: one local factor per prime.
    factored = 1.0
    for p in basis:
        x = p ** (-s)
        factored *= 1.0 + grading_weight * sum(x ** a for a in range(1, degree_cap + 1))

    # And the same at q = 1, which must be the truncated Euler product.
    euler = truncated_euler_product(s, prime_limit)

    agree = abs(enumerated - factored) <= 1e-12 * max(1.0, abs(factored))
    return EulerProductReport(
        s=s,
        prime_limit=prime_limit,
        basis=basis,
        degree_cap=degree_cap,
        grading_weight=grading_weight,
        terms_enumerated=terms,
        monoid_sum=enumerated,
        product_of_local_factors=factored,
        ideal_euler_product=euler,
        relative_difference=abs(enumerated - factored) / max(1.0, abs(factored)),
        agrees=agree,
        explanation=(
            f"Monoid sum over {terms} exponent vectors = {enumerated:.15f}; "
            f"product of {len(basis)} local factors = {factored:.15f}; "
            f"agrees: {agree}. The q=1 local factors give the truncated Euler "
            f"product, which here is {euler:.15f} -- reached exactly only as "
            f"degree_cap -> inf, since the box caps every exponent."
        ),
    )


@dataclass
class EulerProductReport:
    s: float
    prime_limit: int
    basis: tuple[int, ...]
    degree_cap: int
    grading_weight: float
    terms_enumerated: int
    monoid_sum: float
    product_of_local_factors: float
    ideal_euler_product: float
    relative_difference: float
    agrees: bool
    explanation: str