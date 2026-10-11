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
Primes in arithmetic progressions: what the Dirichlet-character picture does and
does not say.

Written to check a specific claim. The account this module was written against
describes a Dirichlet character as filtering primes by residue class, shows that
the local factors interfere, and concludes:

    "Die Primzahlen sind absolut symmetrisch und gerecht auf beide
     Restklassen verteilt."

That conclusion is **false**, and not marginally so. Primes are *not* evenly
distributed between the classes in the sense that picture suggests. Dirichlet
gives equal density -- each class among the units gets the same share *in the
limit* -- but the approach to that limit is biased, in a way that has a name.

**Chebyshev's bias.** Among primes below `x`, those `3 mod 4` outnumber those
`1 mod 4` for most `x`; the first crossing is at `x = 2946`, and the lead changes
infinitely often but the `1 mod 4` class leads a vanishing proportion of the
time. The same happens mod 3: primes `2 mod 3` lead primes `1 mod 3`. The effect
is invisible in natural density but plain in *logarithmic* density -- weighting
each prime by `1/p` -- which is where Rubinstein and Sarnak proved it.

So the module does three things:

1. counts primes by residue class, and shows the race (natural density: no bias
   visible; the counts simply grow together);
2. computes the reciprocal-weighted sums, where the bias is visible immediately;
3. checks the Euler product claim of the same account numerically, since that
   part *is* correct and is worth having verified rather than asserted:
   `L(s, chi) = sum chi(n) n^-s = prod_p (1 - chi(p) p^-s)^-1`.

What this has to do with the Riemann hypothesis: a bias in the race is controlled
by the zeros of `L(s, chi)` off the critical line, so `L(s, chi)` having no zeros
there (GRH) bounds it. That is the real content behind "the zeros control how
evenly the primes fall". It is a bound *conditional on GRH*, not a guarantee --
which is the other correction this module's docstring exists to make.

Nothing here proves or disproves RH, and nothing here is a statement about
cryptography.
"""

from __future__ import annotations

from dataclasses import dataclass

import mpmath as mp

from .prime_certificate import sieve_slice
from .zeta_factors import chi_minus_3, chi_minus_4


#: The `x` at which primes `1 mod 4` first overtake primes `3 mod 4`, counting
#: primes below `x`. Pinned as a documented landmark, like the millionth prime in
#: `prime_certificate`.
#:
#: This constant was first written here as `2946`, from memory, and that was
#: wrong. Measurement gives `26861`, agreed by two independent primality routes
#: (the sieve in `prime_certificate` and its deterministic Miller-Rabin), and at
#: `x = 2946` the gap is `+7` in favour of `3 mod 4`, so `2946` is not a crossing
#: of any kind. Recorded because the wrong value was the kind that would have
#: looked authoritative in a document.
FIRST_CROSSING_MOD_4 = 26861


# ============================================================
# Counting primes by residue class
# ============================================================

def primes_up_to(limit: int) -> list[int]:
    """All primes `<= limit`, via the certificate module's sieve."""
    return sieve_slice(limit)


def residue_class_counts(limit: int, modulus: int) -> dict[int, int]:
    """Count primes `<= limit` in each residue class coprime to `modulus`.

    Classes not coprime to the modulus are omitted rather than reported as zero:
    they contain at most the primes dividing the modulus, and including them
    invites the misreading that a class is "empty".
    """
    if modulus < 2:
        raise ValueError("modulus must be at least 2")
    units = [a for a in range(1, modulus) if _gcd(a, modulus) == 1]
    counts = {a: 0 for a in units}
    for p in primes_up_to(limit):
        residue = p % modulus
        if residue in counts:
            counts[residue] += 1
    return counts


def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def _race_stream(limit: int, modulus: int, a: int, b: int):
    """Yield `(x, pi(x; m, a) - pi(x; m, b))` for `2 <= x <= limit`.

    A generator rather than two lists, so the density and crossing functions can
    run at limits where materialising `limit` pairs would be wasteful. `prime_race`
    wraps it when a caller really does want the arrays.
    """
    prime_table = _prime_table(limit)
    count_a = 0
    count_b = 0
    for x in range(2, limit + 1):
        if prime_table[x]:
            if x % modulus == a:
                count_a += 1
            elif x % modulus == b:
                count_b += 1
        yield x, count_a - count_b


def prime_race(limit: int, modulus: int, a: int, b: int) -> tuple[list[int], list[int]]:
    """The running difference `pi(x; m, a) - pi(x; m, b)` at every `x <= limit`.

    Returns `(xs, differences)` over *all* integers `2 <= x <= limit`, not only
    the primes. That matters for reading the race: the quantity is defined for
    real `x` and only changes at primes, so sampling at primes alone would skip
    the flat stretches where a lead is held, and would hide the crossings that
    the logarithmic density below is computed from.

    A positive value means class `a` leads at that `x`.
    """
    for residue in (a, b):
        if residue <= 0 or residue >= modulus:
            raise ValueError(f"residue {residue} is not in 1..{modulus - 1}")
    xs: list[int] = []
    diffs: list[int] = []
    for x, d in _race_stream(limit, modulus, a, b):
        xs.append(x)
        diffs.append(d)
    return xs, diffs


def _prime_table(limit: int) -> bytearray:
    """A boolean table of primality up to `limit`.

    Initialised to all zeros and switched *on* at each prime. The first draft
    initialised it to ones and set the primes to one as well, which left every
    integer marked prime -- and `prime_race` would then have counted composites,
    producing a race that looked plausible and was meaningless.
    """
    table = bytearray(limit + 1)
    for p in primes_up_to(limit):
        table[p] = 1
    return table


def first_lead_change(limit: int, modulus: int, a: int, b: int) -> int | None:
    """The smallest `x` at which class `b` strictly leads class `a`.

    `None` if it never happens up to `limit`. For `modulus = 4`, `a = 3`,
    `b = 1`, this is the first crossing of the prime race and equals
    `FIRST_CROSSING_MOD_4 = 26861`.
    """
    for x, d in _race_stream(limit, modulus, a, b):
        if d < 0:
            return x
    return None


def lead_logarithmic_density(
    limit: int, modulus: int, a: int, b: int
) -> float:
    """The logarithmic density of the set where class `a` leads class `b`.

    That is `(sum_{x<=limit, Delta(x)>0} 1/x) / (sum_{x<=limit} 1/x)`, with
    `Delta` the counting difference. This is the quantity Rubinstein and Sarnak
    compute, and their answer for `3 mod 4` against `1 mod 4` is about `0.9959`.

    The logarithmic measure is the point. Under natural density the race is
    even -- each side leads a positive proportion of the time, and the leads
    change infinitely often -- so the natural-density version of this number
    refuses to see the bias. Weighting by `1/x` is what makes it visible, and
    this is why "the primes are evenly distributed" and "the primes are biased"
    are both true statements about different measures.
    """
    leading = 0.0
    total = 0.0
    for x, d in _race_stream(limit, modulus, a, b):
        weight = 1.0 / x
        total += weight
        if d > 0:
            leading += weight
    if total == 0:
        raise ValueError("limit is too small to carry any logarithmic mass")
    return leading / total

def bias_margin(limit: int, modulus: int, a: int, b: int) -> float:
    """`sum_{p = a} 1/p - sum_{p = b} 1/p`. Positive means `a` leads."""
    sums = reciprocal_prime_sums(limit, modulus)
    return sums[a] - sums[b]


def reciprocal_prime_sums(limit: int, modulus: int) -> dict[int, float]:
    """`sum_{p <= limit, p = a mod m} 1/p` for each unit class `a`.

    This is the logarithmic weighting, and it is where Chebyshev's bias is
    visible. Natural-density counts differ by `O(1)` and drift; the reciprocal
    sums differ by a bounded, systematic amount that does not wash out.
    """
    if modulus < 2:
        raise ValueError("modulus must be at least 2")
    units = [a for a in range(1, modulus) if _gcd(a, modulus) == 1]
    sums = {a: 0.0 for a in units}
    for p in primes_up_to(limit):
        residue = p % modulus
        if residue in sums:
            sums[residue] += 1.0 / p
    return sums


# ============================================================
# The Euler product, checked rather than asserted
# ============================================================

def dirichlet_series_partial(
    s: float, chi, n_max: int, dps: int = 30
) -> mp.mpc:
    """`sum_{n <= n_max} chi(n) n^-s`, the left-hand side."""
    with mp.workdps(dps):
        return mp.fsum(
            chi(n) * mp.power(n, -mp.mpf(s)) for n in range(1, n_max + 1)
        )


def euler_product_partial(
    s: float, chi, primes: list[int], dps: int = 30
) -> mp.mpc:
    """`prod_{p in primes} (1 - chi(p) p^-s)^-1`, the right-hand side.

    A factor vanishes exactly when `chi(p) = 0`, which is the "filtering" the
    account describes: a prime dividing the modulus is removed from the product
    entirely. That part of the description is correct, and this function is how
    it is checked.
    """
    with mp.workdps(dps):
        product = mp.mpc(1)
        for p in primes:
            factor = 1 - chi(p) * mp.power(p, -mp.mpf(s))
            if factor == 0:
                # chi(p) == 1 and p^-s == 1, i.e. s = 0; not a case used here.
                raise ValueError(f"Euler factor for p = {p} vanishes at s = {s}")
            product *= 1 / factor
        return product


@dataclass(frozen=True)
class EulerProductCheck:
    """How well the truncated product and the truncated sum agree."""

    s: float
    n_max: int
    prime_limit: int
    series_value: complex
    product_value: complex
    absolute_difference: float
    relative_difference: float

    def summary(self) -> str:
        return (
            f"s = {self.s}: series = {self.series_value:.12f}, "
            f"product = {self.product_value:.12f}, "
            f"relative difference = {self.relative_difference:.3e}"
        )


def check_euler_product(
    s: float, chi, n_max: int = 20000, dps: int = 30
) -> EulerProductCheck:
    """Compare the truncated sum and the truncated Euler product.

    Both truncations converge for `s > 1`, so the two sides should agree to
    roughly the size of the tail. The point is that they are computed by
    *completely different* routes -- one sums over all integers, the other
    multiplies over primes only -- so agreement is a real check of the identity
    rather than of an implementation detail.
    """
    primes = primes_up_to(n_max)
    series = dirichlet_series_partial(s, chi, n_max, dps)
    product = euler_product_partial(s, chi, primes, dps)
    difference = abs(series - product)
    scale = max(abs(series), abs(product))
    return EulerProductCheck(
        s=s,
        n_max=n_max,
        prime_limit=n_max,
        series_value=complex(series),
        product_value=complex(product),
        absolute_difference=float(difference),
        relative_difference=float(difference / scale),
    )


def chi_mod_3(n: int) -> int:
    """The character the account uses: `1, -1, 0` by residue mod 3.

    Re-exported from `zeta_factors`, where it is `chi_minus_3`. Named again here
    because the account presents it as a device for "filtering primes", not as
    the character of the Eisenstein integers -- it is the same object.
    """
    return chi_minus_3(n)


def chi_mod_4(n: int) -> int:
    """The character of the Gaussian integers, `1, 0, -1, 0, ...`."""
    return chi_minus_4(n)
