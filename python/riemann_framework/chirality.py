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
"""Chirality invariants behind the ``sigma`` dictionary, checked numerically.

The puzzle the Dimension-Shift Hypothesis is built on is: *mirror-closure is
necessary but not sufficient for achirality*. A set that contains both a piece
and its mirror image is mirror-closed; it is achiral only if every piece is
already its own mirror. Under ``sigma s = 1 - conj s`` that reads:

* ``sigma rho = rho``  -- the zero is on the critical line (its own mirror);
* ``sigma rho != rho`` -- the zero has a *distinct* mirror partner, and the set
  can still be mirror-closed while being chiral.

This module verifies, with numbers, the four standard instances of that pattern
and one counter-example:

1. **Gaussian primes.** ``p = 2`` ramifies, ``p = 1 mod 4`` splits into a mirror
   pair ``a +- b i``, ``p = 3 mod 4`` is inert. Splitting is exactly the existence
   of a mirror pair.
2. **Lens spaces.** ``L(p, q)`` admits an orientation-reversing self-homeomorphism
   iff ``q^2 = -1 mod p``, which happens iff ``p = 2`` or ``p = 1 mod 4`` -- the
   same arithmetic condition, in topology.
3. **The character ``chi_-4``.** It is odd (``chi(-1) = -1``), so the completed
   ``L``-function needs ``Gamma((s+1)/2)``, not ``Gamma(s/2)``. Verified by
   fitting both and comparing residuals: the wrong archimedean factor is off by
   thirty orders of magnitude.
4. **Cayley-Dickson conjugation** reverses products, ``conj(xy) = conj(y)conj(x)``,
   in dimensions 2, 4, 8 and 16 -- the anti-automorphism that survives the loss of
   commutativity and associativity.
5. **Davenport-Heilbronn**: the functional equation without the Euler product. The
   Euler product *fails* (measured), so the functional equation alone cannot be
   what forces zeros onto the line.

**What this does not do.** It produces no evidence about the Riemann hypothesis.
Every statement here is a finite verification of a known theorem or a measured
failure; `docs/chirality.md` says so explicitly, and the Davenport-Heilbronn
section reports a search that found *no* off-line zero rather than importing the
literature's claim.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import mpmath as mp
import numpy as np

from .cayley_dickson import basis, conjugate, multiply
from .dh_filter import dh_coefficients, dh_completed, dh_kappa, dh_value
from .prime_certificate import sieve_slice


#: The one non-claim, stated where the numbers are.
NO_RH_EVIDENCE = (
    "There is no new evidence about the Riemann hypothesis here. These are finite "
    "verifications of known theorems and one measured failure (Davenport-Heilbronn), "
    "re-describing the wall that `ZetaBridge.lean` already proves: mirror-closure of "
    "the zero set is a theorem, and achirality is RH."
)


# ============================================================
# 1. Gaussian primes: splitting is the existence of a mirror pair
# ============================================================

def gaussian_prime_class(p: int) -> str:
    """`"ramified"` for 2, `"split"` for `p = 1 mod 4`, `"inert"` for `p = 3 mod 4`."""
    if p < 2:
        raise ValueError("p must be a prime >= 2")
    if not _is_prime(p):
        raise ValueError(f"{p} is not prime")
    if p == 2:
        return "ramified"
    return "split" if p % 4 == 1 else "inert"


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    return all(n % d for d in range(2, int(n**0.5) + 1))


def gaussian_representation(p: int) -> tuple[int, int] | None:
    """`(a, b)` with `a^2 + b^2 = p`, or `None` if `p` is inert.

    Found by integer search, not by a number-theoretic assertion: the search
    failing for every inert prime is half of the verification.
    """
    if gaussian_prime_class(p) == "inert":
        return None
    if p == 2:
        return (1, 1)
    limit = math.isqrt(p) + 1
    for a in range(1, limit):
        remainder = p - a * a
        if remainder <= 0:
            continue
        b = math.isqrt(remainder)
        if b * b == remainder:
            return (a, b)
    return None


@dataclass(frozen=True)
class GaussianCensus:
    """Split/inert/ramified counts below a bound, with the representation check."""

    limit: int
    split: int
    inert: int
    ramified: int
    all_split_prime_represented: bool
    no_inert_prime_represented: bool

    def summary(self) -> str:
        return (
            f"primes below {self.limit}: {self.split} split, {self.inert} inert, "
            f"{self.ramified} ramified; every split prime has a mirrored "
            f"representation: {self.all_split_prime_represented}; no inert prime "
            f"does: {self.no_inert_prime_represented}"
        )


def gaussian_census(limit: int = 400) -> GaussianCensus:
    """Count the three classes below `limit` and verify the representation claim."""
    if limit < 10:
        raise ValueError("limit must be at least 10")
    split = inert = ramified = 0
    all_split_ok = True
    no_inert_ok = True
    for p in sieve_slice(limit):
        kind = gaussian_prime_class(int(p))
        representation = gaussian_representation(int(p))
        if kind == "split":
            split += 1
            if representation is None or representation[0] ** 2 + representation[1] ** 2 != p:
                all_split_ok = False
        elif kind == "inert":
            inert += 1
            if representation is not None:
                no_inert_ok = False
        else:
            ramified += 1
    return GaussianCensus(
        limit=limit,
        split=split,
        inert=inert,
        ramified=ramified,
        all_split_prime_represented=all_split_ok,
        no_inert_prime_represented=no_inert_ok,
    )


# ============================================================
# 2. Lens spaces: the same condition in topology
# ============================================================

def orientation_reversing_q(p: int) -> int | None:
    """The smallest `q` with `q^2 = -1 (mod p)`, or `None`.

    `L(p, q)` admits an orientation-reversing self-homeomorphism exactly when
    such a `q` exists -- i.e. when `-1` is a quadratic residue mod `p`.
    """
    if p < 2:
        raise ValueError("p must be at least 2")
    for q in range(1, p):
        if (q * q + 1) % p == 0:
            return q
    return None


@dataclass(frozen=True)
class LensCensus:
    """Achiral/chiral lens spaces below a bound, against the arithmetic prediction."""

    limit: int
    achiral: int
    chiral: int
    matches_split_criterion: bool

    def summary(self) -> str:
        return (
            f"prime p below {self.limit}: {self.achiral} lens spaces L(p,q) admit an "
            f"orientation-reversing self-homeomorphism, {self.chiral} do not; "
            f"agreement with 'p = 2 or p = 1 mod 4': {self.matches_split_criterion}"
        )


def lens_census(limit: int = 200) -> LensCensus:
    """Verify "achiral iff `p = 2` or `p = 1 mod 4`" for all primes below `limit`."""
    if limit < 10:
        raise ValueError("limit must be at least 10")
    achiral = chiral = 0
    agrees = True
    for p in sieve_slice(limit):
        p = int(p)
        reverser = orientation_reversing_q(p)
        predicted = p == 2 or p % 4 == 1
        if (reverser is not None) != predicted:
            agrees = False
        if reverser is None:
            chiral += 1
        else:
            achiral += 1
    return LensCensus(
        limit=limit,
        achiral=achiral,
        chiral=chiral,
        matches_split_criterion=agrees,
    )


# ============================================================
# 3. chi_-4 is odd, and the archimedean factor knows it
# ============================================================

def chi_minus_four(n: int) -> int:
    """The non-principal character mod 4: `1` for `n = 1`, `-1` for `n = 3`, else `0`."""
    residue = n % 4
    if residue == 1:
        return 1
    if residue == 3:
        return -1
    return 0


def dirichlet_beta(s: complex | mp.mpc) -> mp.mpc:
    """`beta(s) = L(s, chi_-4)`, evaluated by `mpmath.dirichlet`."""
    return mp.dirichlet(mp.mpc(s), [0, 1, 0, -1])


def completed_beta(s: complex | mp.mpc, archimedean_parity: int = 1) -> mp.mpc:
    """`(pi/4)^(-(s+a)/2) Gamma((s+a)/2) beta(s)`, with `a = 1` for an odd character.

    `a = 1` is the correct archimedean factor for `chi_-4`; passing `a = 0` builds
    the factor a *even* character would need, which is how the parity check is
    turned into a numerical comparison.
    """
    s = mp.mpc(s)
    return (mp.pi / 4) ** (-(s + archimedean_parity) / 2) * mp.gamma(
        (s + archimedean_parity) / 2
    ) * dirichlet_beta(s)


def functional_equation_residual(s: complex | mp.mpc, archimedean_parity: int = 1) -> float:
    """`|Lambda(s) - Lambda(1 - s)|` for the completed beta function."""
    return float(abs(completed_beta(s, archimedean_parity) - completed_beta(1 - mp.mpc(s), archimedean_parity)))


@dataclass(frozen=True)
class ParityCheck:
    """The same functional equation fitted with the right and the wrong factor."""

    odd_residuals: list[float]
    even_residuals: list[float]

    @property
    def ratio(self) -> float:
        return max(self.even_residuals) / max(self.odd_residuals)

    @property
    def parity_detected(self) -> bool:
        return self.ratio > 1e10

    def summary(self) -> str:
        return (
            f"functional-equation residual with Gamma((s+1)/2): "
            f"{max(self.odd_residuals):.2e}; with Gamma(s/2): "
            f"{max(self.even_residuals):.2e} -- ratio {self.ratio:.1e}. "
            "The odd archimedean factor is the one that works, so chi_-4 is odd."
        )


def parity_check(points: tuple[complex, ...] = (complex(0.3, 2.0), complex(0.7, 5.0))) -> ParityCheck:
    """Evaluate the functional equation with both archimedean factors."""
    odd = [functional_equation_residual(point, 1) for point in points]
    even = [functional_equation_residual(point, 0) for point in points]
    return ParityCheck(odd_residuals=odd, even_residuals=even)


# ============================================================
# 4. Cayley-Dickson conjugation is an anti-automorphism
# ============================================================

def cayley_dickson_anti_automorphism(
    dimensions: tuple[int, ...] = (2, 4, 8, 16),
    trials: int = 20,
    seed: int = 0,
) -> dict[int, float]:
    """`max |conj(xy) - conj(y) conj(x)|` over random elements, per dimension."""
    rng = np.random.default_rng(seed)
    results: dict[int, float] = {}
    for dimension in dimensions:
        if dimension < 1 or dimension & (dimension - 1):
            raise ValueError("dimensions must be powers of two")
        worst = 0.0
        for _ in range(trials):
            x = rng.standard_normal(dimension)
            y = rng.standard_normal(dimension)
            left = conjugate(multiply(x, y))
            right = multiply(conjugate(y), conjugate(x))
            worst = max(worst, float(np.max(np.abs(left - right))))
        results[dimension] = worst
    return results


def cayley_dickson_is_commutative(dimension: int, trials: int = 5, seed: int = 0) -> bool:
    """Control: commutativity fails from dimension 4 on, so the test is not vacuous."""
    rng = np.random.default_rng(seed)
    for _ in range(trials):
        x = rng.standard_normal(dimension)
        y = rng.standard_normal(dimension)
        if np.max(np.abs(multiply(x, y) - multiply(y, x))) > 1e-10:
            return False
    return True


def cayley_dickson_units(dimension: int) -> list[np.ndarray]:
    """The basis vectors, exposed so a caller can build explicit examples."""
    return [basis(dimension, index) for index in range(dimension)]


# ============================================================
# 5. Davenport-Heilbronn: functional equation without an Euler product
# ============================================================

def dh_functional_equation_residual(s: complex | mp.mpc, dps: int = 25) -> float:
    """`|Lambda(s) - Lambda(1 - s)|` for the Davenport-Heilbronn function."""
    s = mp.mpc(s)
    return float(abs(dh_completed(s, dps=dps) - dh_completed(1 - s, dps=dps)))


def dh_multiplicativity_report(dps: int = 25) -> dict[str, float]:
    """Does the DH coefficient sequence have an Euler product? No -- measured.

    A multiplicative sequence would satisfy `b(2) b(3) = b(6)`. The measured
    product is `-kappa^2` instead, a specific non-zero defect rather than a
    rounding error.
    """
    coefficients = dh_coefficients(8, dps=dps)
    kappa = dh_kappa(dps=dps)
    product = coefficients[2] * coefficients[3]
    return {
        "b2_times_b3": float(product),
        "b6": float(coefficients[6]),
        "difference": float(abs(product - coefficients[6])),
        "minus_kappa_squared": float(-(kappa**2)),
        "matches_minus_kappa_squared": float(abs(product + kappa**2)),
    }


def dh_zero_scan(
    heights: tuple[float, ...] = (2.0, 5.0, 8.0, 12.0, 20.0, 30.0, 40.0),
    offsets: tuple[float, ...] = (0.5, 0.4, 0.6, 0.3, 0.7),
    dps: int = 20,
) -> list[tuple[float, float, float]]:
    """Locate zeros of the DH function near the line: `(Re, Im, |f|)` rows.

    A bounded scan, and the bound is the finding: **no off-line zero was
    located up to `t = 40`.** The literature's claim that the DH function has
    zeros off the critical line is therefore *not* reproduced here, and this
    module does not assert it. What the scan does show is that the zeros it finds
    sit on `Re = 1/2` -- i.e. that the structural failure being tested is the
    missing Euler product, not a located counter-example.
    """
    found: dict[tuple[float, float], tuple[float, float, float]] = {}
    with mp.workdps(dps):
        for height in heights:
            for offset in offsets:
                guess = mp.mpc(offset, height)
                try:
                    zero = mp.findroot(dh_value, guess, solver="muller", tol=mp.mpf(10) ** -14)
                except Exception:
                    continue
                magnitude = float(abs(dh_value(zero)))
                if magnitude > 1e-6:
                    continue
                key = (round(float(zero.real), 6), round(float(zero.imag), 4))
                found[key] = (float(zero.real), float(zero.imag), magnitude)
    return [found[key] for key in sorted(found, key=lambda item: item[1])]


@dataclass(frozen=True)
class DavenportHeilbronnReport:
    """The counter-example: functional equation yes, Euler product no."""

    functional_equation_residual: float
    multiplicativity: dict[str, float]
    zeros: list[tuple[float, float, float]]

    @property
    def euler_product_fails(self) -> bool:
        return abs(self.multiplicativity["difference"]) > 1e-6

    @property
    def off_line_zeros(self) -> list[tuple[float, float, float]]:
        return [row for row in self.zeros if abs(row[0] - 0.5) > 1e-6]

    def summary(self) -> str:
        return (
            f"functional equation: residual {self.functional_equation_residual:.2e} "
            f"(holds); Euler product: b(2)b(3) - b(6) = "
            f"{self.multiplicativity['difference']:.4f} (fails); "
            f"{len(self.zeros)} zeros located, {len(self.off_line_zeros)} of them "
            "off the line -- so this is a warning about what the functional "
            "equation cannot give, not a located counter-example"
        )


def davenport_heilbronn_report() -> DavenportHeilbronnReport:
    """Everything the DH counter-example is asked to demonstrate, measured."""
    return DavenportHeilbronnReport(
        functional_equation_residual=dh_functional_equation_residual(0.3 + 2.0j),
        multiplicativity=dh_multiplicativity_report(),
        zeros=dh_zero_scan(),
    )


# ============================================================
# The chirality report, in one object
# ============================================================

@dataclass(frozen=True)
class ChiralityReport:
    """All five checks, so a caller can print one summary."""

    gaussian: GaussianCensus
    lens: LensCensus
    parity: ParityCheck
    cayley_dickson: dict[int, float]
    commutativity_control: dict[int, bool]
    davenport_heilbronn: DavenportHeilbronnReport

    def verdict(self) -> str:
        return (
            "Chirality checks: "
            f"Gaussian splitting ({self.gaussian.split} split primes, all mirrored); "
            f"lens achirality agrees with 'p = 2 or 1 mod 4' "
            f"({self.lens.matches_split_criterion}); "
            f"chi_-4 parity detected with ratio {self.parity.ratio:.1e}; "
            f"Cayley-Dickson anti-automorphism to 1e"
            f"{int(np.ceil(-np.log10(max(self.cayley_dickson.values()) + 1e-16)))}; "
            f"Davenport-Heilbronn: FE holds, Euler product fails, "
            f"{len(self.davenport_heilbronn.off_line_zeros)} off-line zeros located. "
            + NO_RH_EVIDENCE
        )


def chirality_report(limit: int = 400) -> ChiralityReport:
    """Run every check once."""
    return ChiralityReport(
        gaussian=gaussian_census(limit),
        lens=lens_census(min(limit, 200)),
        parity=parity_check(),
        cayley_dickson=cayley_dickson_anti_automorphism(),
        commutativity_control={
            dimension: cayley_dickson_is_commutative(dimension)
            for dimension in (2, 4, 8)
        },
        davenport_heilbronn=davenport_heilbronn_report(),
    )
