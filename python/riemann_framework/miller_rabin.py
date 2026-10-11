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
Miller-Rabin, what it guarantees unconditionally, and what GRH adds.

The account this module was written against makes a claim that has the direction
of the implication backwards:

    "Die komplexen Nullstellen der Dirichlet-Funktionen garantieren uns im
     Hintergrund, dass es keine 'boesartigen' mathematischen Zahlenkonstrukte
     gibt, die unsere Verschluesselungssoftware austricksen koennen."

Nothing about zeros *guarantees* anything, because GRH is unproven. What is true
is the conditional: **if** GRH holds, then testing every base up to
`2 (ln n)^2` decides primality deterministically [Bach 1985, refining Miller's
1976 result]. If GRH is false, that test's correctness is not established -- the
guarantee runs from the conjecture to the algorithm, not from the zeros to the
safety of the internet.

And in practice the condition is not needed. The bases `2..37` decide primality
unconditionally below `3.317e24` (Sorenson-Webster), which covers every size
anyone uses; `prime_certificate.is_prime_deterministic` already does this, and this
module cross-checks the GRH-conditional route against it.

What is guaranteed unconditionally, and is the real reason Miller-Rabin is safe
to use with random bases:

    for odd composite n, at most (n-1)/4 of the bases a in [1, n-1] are liars.

So `k` independent random bases give error at most `4^-k`, with no hypothesis.
`max_liar_fraction` measures the true worst case over a range, which is far below
the bound -- the bound is worst-case, and the worst case is attained.

Nothing here proves or disproves RH, and nothing here is a claim about
cryptographic security.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .prime_certificate import DETERMINISTIC_MR_BASES, is_prime_deterministic


#: Bach's bound, conditional on GRH: the least witness for an odd composite `n`
#: is below `2 (ln n)^2`. Attributed to Bach (1985); Miller (1976) proved the
#: polynomial-time determinism that this makes explicit, which is why the result
#: is often named for Miller alone.
GRH_BOUND_CONSTANT = 2


def _decompose(n: int) -> tuple[int, int]:
    """Write `n - 1 = d * 2^s` with `d` odd."""
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    return d, s


def is_strong_probable_prime(n: int, a: int) -> bool:
    """The Miller-Rabin test of `n` to base `a`.

    `n` passes when `a^d = 1 (mod n)`, or `a^(d 2^r) = -1 (mod n)` for some
    `0 <= r < s`, where `n - 1 = d 2^s` with `d` odd. A composite that passes is
    a strong pseudoprime to base `a`, and `a` is called a *liar* for `n`.
    """
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    a %= n
    if a == 0:
        return True
    d, s = _decompose(n)
    x = pow(a, d, n)
    if x in (1, n - 1):
        return True
    for _ in range(s - 1):
        x = x * x % n
        if x == n - 1:
            return True
    return False


def liar_bases(n: int) -> list[int]:
    """Every base `a` in `[1, n-1]` to which the odd composite `n` passes.

    `n = 1` is not a meaningful input and small primes pass every base that is
    not a multiple of them, so the caller is expected to pass an odd composite;
    the count is only interesting there.
    """
    if n < 3 or n % 2 == 0:
        raise ValueError("liar_bases expects an odd n >= 3")
    return [a for a in range(1, n) if is_strong_probable_prime(n, a)]


def liar_count(n: int) -> int:
    """`#{a in [1, n-1] : n passes to base a}` for odd `n`."""
    return len(liar_bases(n))


def liar_fraction(n: int) -> float:
    """`liar_count(n) / (n - 1)`, to be compared against the `1/4` bound."""
    return liar_count(n) / (n - 1)


@dataclass(frozen=True)
class LiarScan:
    """The worst liar fraction found over a range of odd composites."""

    limit: int
    worst_n: int
    worst_fraction: float
    composites_scanned: int

    def summary(self) -> str:
        return (
            f"worst liar fraction over odd composites <= {self.limit}: "
            f"{self.worst_fraction:.6f} at n = {self.worst_n} "
            f"({self.composites_scanned} composites scanned); "
            f"the unconditional bound is 1/4"
        )


def max_liar_fraction(limit: int = 3000) -> LiarScan:
    """Measure the largest `liar_fraction` over odd composites `<= limit`.

    Rabin's theorem says this never exceeds `1/4`. Measuring it is worth doing
    because the bound is *attained* for some `n` and not for others, so the
    interesting output is which `n` attains it -- a claim that the bound is tight
    is only meaningful with a witness.
    """
    worst_n = 0
    worst = 0.0
    scanned = 0
    for n in range(9, limit + 1, 2):
        if is_prime_deterministic(n):
            continue
        scanned += 1
        fraction = liar_fraction(n)
        if fraction > worst:
            worst = fraction
            worst_n = n
    return LiarScan(
        limit=limit,
        worst_n=worst_n,
        worst_fraction=worst,
        composites_scanned=scanned,
    )


def carmichael_numbers(limit: int) -> list[int]:
    """Carmichael numbers `<= limit`, by Korselt's criterion.

    `n` is Carmichael exactly when it is squarefree and `(p - 1) | (n - 1)` for
    every prime `p | n`. These are the numbers that fool the Fermat test to
    *every* coprime base, so they are the natural adversarial test for
    Miller-Rabin: they must not fool it.
    """
    if limit < 3:
        return []
    out: list[int] = []
    for n in range(3, limit + 1, 2):
        factors = _odd_prime_factors(n)
        squarefree = len(factors) == len(set(factors))
        if not squarefree or len(factors) < 3:
            continue
        if all((n - 1) % (p - 1) == 0 for p in factors):
            out.append(n)
    return out


def _odd_prime_factors(n: int) -> list[int]:
    """Odd prime factors of an odd `n`, with multiplicity."""
    factors: list[int] = []
    m = n
    p = 3
    while p * p <= m:
        while m % p == 0:
            factors.append(p)
            m //= p
        p += 2
    if m > 1:
        factors.append(m)
    return factors


def grh_base_bound(n: int) -> int:
    """`ceil(2 (ln n)^2)`: the GRH-conditional base limit for `n`.

    This is the number the account describes as "eine winzige, leicht zu
    berechnende Zahl". It is indeed small -- under 3000 for a 500-digit `n` --
    which is exactly why the conditional result is attractive.
    """
    if n < 2:
        raise ValueError("n must be at least 2")
    return math.ceil(GRH_BOUND_CONSTANT * math.log(n) ** 2)


def is_prime_grh_conditional(n: int) -> bool:
    """Primality decided by testing every base up to `grh_base_bound(n)`.

    Correct **if GRH holds**. It is computed here so the conditional route can be
    compared against the unconditional one, which is the comparison that matters:
    on every input this repository can test, the two agree.
    """
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    limit = min(grh_base_bound(n), n - 1)
    for a in range(2, limit + 1):
        if not is_strong_probable_prime(n, a):
            return False
    return True


def is_prime_unconditional(n: int) -> bool:
    """The repository's unconditional deterministic test, re-exported.

    Deterministic Miller-Rabin over the bases `2..37`, which Sorenson and Webster
    prove sufficient below `3.317e24`. No hypothesis.
    """
    return is_prime_deterministic(n)


def false_positive_probability(rounds: int) -> float:
    """The unconditional `4^-rounds` error bound for `rounds` random bases.

    Valid for a single round only against a *fixed* composite chosen in advance;
    the standard caveat is that the bound assumes the bases are independent and
    the composite is not chosen after seeing them. Stated here because the bound
    is quoted so often that the caveat gets lost.
    """
    if rounds < 0:
        raise ValueError("rounds must be non-negative")
    return 4.0 ** (-rounds)


@dataclass(frozen=True)
class RouteComparison:
    """Where the GRH-conditional and unconditional routes were compared."""

    limit: int
    checked: int
    disagreements: list[int]
    max_grh_bases: int

    def summary(self) -> str:
        return (
            f"compared on odd n <= {self.limit} ({self.checked} inputs): "
            f"{len(self.disagreements)} disagreements; "
            f"largest base count required was {self.max_grh_bases}"
        )


def compare_routes(limit: int = 20000) -> RouteComparison:
    """Compare the GRH-conditional and unconditional primality routes.

    Both are expected to agree everywhere here, since `limit` is far below the
    unconditional range. A disagreement would mean a bug in one of them, not a
    counterexample to GRH.
    """
    disagreements: list[int] = []
    checked = 0
    max_bases = 0
    for n in range(3, limit + 1, 2):
        checked += 1
        max_bases = max(max_bases, min(grh_base_bound(n), n - 1) - 1)
        if is_prime_grh_conditional(n) != is_prime_unconditional(n):
            disagreements.append(n)
    return RouteComparison(
        limit=limit,
        checked=checked,
        disagreements=disagreements,
        max_grh_bases=max_bases,
    )


__all__ = [
    "DETERMINISTIC_MR_BASES",
    "GRH_BOUND_CONSTANT",
    "LiarScan",
    "RouteComparison",
    "carmichael_numbers",
    "compare_routes",
    "false_positive_probability",
    "grh_base_bound",
    "is_prime_grh_conditional",
    "is_prime_unconditional",
    "is_strong_probable_prime",
    "liar_bases",
    "liar_count",
    "liar_fraction",
    "max_liar_fraction",
]
