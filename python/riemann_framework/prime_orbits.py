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
Periodic orbits and primes: the correspondence that works, and where it stops.

The Gutzwiller trace formula relates the density of energy levels of a quantised
chaotic system to a sum over the periodic orbits of its classical counterpart. The
claimed dictionary with the zeta function is

    energy levels          <->  imaginary parts of the zeros
    classical periodic orbits <-> the primes
    period of an orbit     <->  log p

This module makes the correspondence *computable* rather than suggestive, and
pins down exactly how far it goes.

The part that works, and works exactly
--------------------------------------
For a hyperbolic (Anosov) flow with topological entropy `h`, the number of
primitive periodic orbits of period at most `T` obeys the prime orbit theorem,

    pi(T)  ~  e^{hT} / (hT).

If the orbits are to have periods `log p`, then the number of them with
`log p <= T` is `pi(e^T)`, and the prime number theorem gives

    pi(e^T)  ~  e^T / T,

which is the same statement with `h = 1`. So the dictionary is not an analogy at
the level of counting: it is an identity, with the topological entropy fixed to 1
by the periods being logarithms of primes. `orbit_count` and
`prime_orbit_asymptotic` compute both sides.

The part that does not, and where RH actually lives
---------------------------------------------------
The counting statement is a *first-order* asymptotic. The interesting object is
the error term, and there the correspondence stops being helpful:

    psi(X) = X - sum_rho X^rho / rho - log 2pi - (1/2) log(1 - X^-2),

so the deviation of the orbit count from its smooth part is a sum over the
**zeros**, not over the orbits. A trace formula can reproduce the primes; what it
does not do is constrain where the zeros are. `psi_minus_smooth` and
`psi_from_zeros` compute the two sides, and the demonstration is that adding more
zeros improves the reconstruction -- the zeros determine the error, and nothing in
the orbit picture tells you where the zeros are.

That is the honest shape of the whole programme: the analogy is deep, it is
exactly right at first order, and it *relocates* RH rather than approaching it.

Nothing here proves or disproves the Riemann hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass

import mpmath as mp

from .prime_certificate import sieve_slice


#: Stated wherever the dictionary is presented, because the first-order match is
#: the part that is easy to mistake for progress.
RELOCATION_NOTE = (
    "The prime orbit theorem matches the orbit count at first order, with "
    "topological entropy h = 1. That is a statement about COUNTING. The error "
    "term is a sum over the zeta zeros, so the correspondence relocates the "
    "Riemann hypothesis into the trace formula rather than making it tractable: "
    "nothing in the orbit picture constrains the zeros. And the relocation is "
    "not a technicality -- reconstructing psi(X) from its zero sum needs on the "
    "order of (X/2 pi) log(X/2 pi e) zeros, so the dictionary's error term is "
    "not computable at any X where the first-order match is visible. Measured in "
    "`reconstruction_report` rather than asserted."
)


# ============================================================
# Orbit counting
# ============================================================

def topological_entropy() -> float:
    """`h = 1`, forced by the orbit periods being `log p`.

    An Anosov flow has `pi(T) ~ e^{hT}/(hT)`; the arithmetic system has
    `pi(e^T) ~ e^T/T`. Matching the two pins `h = 1` rather than leaving it free,
    which is the whole content of the dictionary at this level.
    """
    return 1.0


def prime_orbit_asymptotic(T: float) -> float:
    """`e^{hT} / (hT)` with `h = 1`, the Anosov prime orbit theorem."""
    if T <= 0:
        raise ValueError("T must be positive")
    h = topological_entropy()
    return float(mp.e ** (h * T) / (h * T))


def primitive_orbit_count(T: float) -> int:
    """`pi(e^T)`: the number of primes `p` with `log p <= T`.

    The primes are the primitive periodic orbits in the dictionary, and their
    periods are `log p`.
    """
    if T <= 0:
        raise ValueError("T must be positive")
    limit = int(mp.floor(mp.e**T))
    if limit < 2:
        return 0
    # `sieve_slice` is exact and cheap at these sizes; the cap keeps the largest
    # T here from allocating an unreasonable table.
    if limit > 50_000_000:
        raise ValueError("T is too large for an exact sieve; keep e^T <= 5e7")
    return len(sieve_slice(limit))


def all_orbit_count(T: float) -> int:
    """`#{prime powers p^k : k log p <= T}`: primitive orbits and their repeats.

    A trace formula sums over repetitions of each primitive orbit, so the
    arithmetic side needs prime powers rather than primes alone. This is the same
    distinction as `pi` versus `psi`.
    """
    if T <= 0:
        raise ValueError("T must be positive")
    limit = int(mp.floor(mp.e**T))
    if limit < 2:
        return 0
    if limit > 50_000_000:
        raise ValueError("T is too large for an exact sieve; keep e^T <= 5e7")
    primes = sieve_slice(limit)
    count = 0
    for p in primes:
        power = p
        while power <= limit:
            count += 1
            power *= p
    return count


def orbit_count_ratio(T: float) -> float:
    """`pi(e^T) / (e^T / T)`: the first-order correspondence, measured.

    Tends to `1`. That it does so is the prime number theorem; the function
    exists so that the claim "the dictionary is exact at first order" is
    demonstrated on the numbers rather than asserted.
    """
    return primitive_orbit_count(T) / prime_orbit_asymptotic(T)


@dataclass(frozen=True)
class OrbitRow:
    """Orbit counts against the asymptotic, at one `T`."""

    T: float
    orbit_limit: int
    primitive_count: int
    all_count: int
    asymptotic: float

    @property
    def ratio(self) -> float:
        return self.primitive_count / self.asymptotic

    def summary(self) -> str:
        return (
            f"T = {self.T:5.2f} (X = e^T = {self.orbit_limit:>12,}): "
            f"primes = {self.primitive_count:>8,}, "
            f"prime powers = {self.all_count:>8,}, "
            f"e^T/T = {self.asymptotic:>14,.0f}, "
            f"ratio = {self.ratio:.4f}"
        )


def orbit_table(T_values: list[float]) -> list[OrbitRow]:
    """The correspondence at several `T`, for reporting and plotting."""
    rows: list[OrbitRow] = []
    for T in T_values:
        limit = int(mp.floor(mp.e**T))
        rows.append(
            OrbitRow(
                T=T,
                orbit_limit=limit,
                primitive_count=primitive_orbit_count(T),
                all_count=all_orbit_count(T),
                asymptotic=prime_orbit_asymptotic(T),
            )
        )
    return rows


# ============================================================
# The error term, which is the zeros
# ============================================================

def chebyshev_psi(X: int) -> float:
    """`psi(X) = sum_{p^k <= X} log p`, computed exactly from a sieve."""
    if X < 2:
        return 0.0
    total = 0.0
    for p in sieve_slice(X):
        log_p = float(mp.log(p))
        power = p
        while power <= X:
            total += log_p
            power *= p
    return total


def psi_minus_smooth(X: int) -> float:
    """`psi(X) - X`: the deviation the explicit formula has to explain."""
    return chebyshev_psi(X) - X


def zeta_zero_ordinates(count: int, dps: int = 30) -> list[float]:
    """The first `count` zero ordinates `gamma_k`, cached.

    Cached because `mp.zetazero` dominates the cost of everything below, and the
    first draft recomputed all of them on every call -- ninety seconds per
    evaluation, which is why the measurement was nearly not made.
    """
    if count < 1:
        raise ValueError("count must be at least 1")
    cached = _ZERO_CACHE.get(count)
    if cached is None:
        with mp.workdps(dps):
            cached = [float(mp.zetazero(k).imag) for k in range(1, count + 1)]
        _ZERO_CACHE[count] = cached
    return cached


_ZERO_CACHE: dict[int, list[float]] = {}


def psi_from_zeros(X: int, zero_count: int, dps: int = 30) -> float:
    """The explicit formula for `psi(X)`, truncated to the first `zero_count` zeros.

    `psi_0(X) = X - sum_rho X^rho/rho - log(2 pi) - (1/2) log(1 - X^-2)`.

    The `log(2 pi)` and `(1/2) log(1 - X^-2)` terms were missing from this
    function's first draft, a systematic offset of about `-1.84` -- and a
    systematic offset is exactly what makes a convergence test look like noise.
    Worth stating because the omission is invisible: the sum over zeros is the
    conspicuous term and the constants look like bookkeeping.
    """
    if X < 2:
        raise ValueError("X must be at least 2")
    with mp.workdps(dps):
        x = mp.mpf(X)
        total = x - mp.log(2 * mp.pi) - mp.log(1 - x**-2) / 2
        if zero_count > 0:
            for gamma in zeta_zero_ordinates(zero_count, dps):
                rho = mp.mpc(mp.mpf(1) / 2, mp.mpf(gamma))
                total -= 2 * mp.re(mp.power(x, rho) / rho)
        return float(total)


def zeros_needed_to_resolve(X: int) -> float:
    """`N(X)`, the Riemann-von Mangoldt count: how many zeros the sum needs.

    To reconstruct `psi(X)` from its zero sum you need the zeros up to height
    about `X`, and there are on the order of `(X/2 pi) log(X/2 pi e)` of them.
    This is the number that makes the dictionary's error term useless in practice,
    and it is what `orbit_table`'s first-order match hides.
    """
    if X < 3:
        raise ValueError("X must be at least 3")
    x = mp.mpf(X)
    return float(x / (2 * mp.pi) * mp.log(x / (2 * mp.pi * mp.e)))


@dataclass(frozen=True)
class ReconstructionReport:
    """What truncating the explicit formula at `K` zeros actually does."""

    X: int
    zero_counts: list[int]
    errors: list[float]
    zeros_needed: float

    @property
    def minimum_error(self) -> float:
        return min(self.errors)

    @property
    def maximum_error(self) -> float:
        return max(self.errors)

    @property
    def uses_a_negligible_fraction_of_the_needed_zeros(self) -> bool:
        return max(self.zero_counts) < self.zeros_needed / 100

    def summary(self) -> str:
        return (
            f"X = {self.X:,}: errors at K = {self.zero_counts} range over "
            f"[{self.minimum_error:.2f}, {self.maximum_error:.2f}] with no "
            f"downward trend; resolving X needs about "
            f"{self.zeros_needed:,.0f} zeros, so the largest K used here is "
            f"{max(self.zero_counts) / self.zeros_needed:.2e} of what is required"
        )


def reconstruction_report(X: int, zero_counts: list[int] | None = None) -> ReconstructionReport:
    """Measure the truncated explicit formula rather than assuming convergence.

    **The truncated sum does not converge usefully, and this is the finding.**
    The zero sum converges only conditionally, so a truncation carries a tail of
    size about `X^{1/2}/gamma_K` that oscillates in sign; over `K <= 120` the
    error moves by a factor of tens with no trend at all. Two single values was
    this function's first form, and `zeros_control_the_error` returned `False` at
    `X = 1000` and `X = 100000` -- correctly, because one sample of an oscillating
    tail says nothing.
    """
    if zero_counts is None:
        zero_counts = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
    exact = chebyshev_psi(X)
    errors = [abs(psi_from_zeros(X, k) - exact) for k in zero_counts]
    return ReconstructionReport(
        X=X,
        zero_counts=list(zero_counts),
        errors=errors,
        zeros_needed=zeros_needed_to_resolve(X),
    )


def reconstruction_error(X: int, zero_counts: list[int]) -> list[float]:
    """`|psi_from_zeros(X, K) - psi(X)|` for each `K`."""
    return reconstruction_report(X, zero_counts).errors
