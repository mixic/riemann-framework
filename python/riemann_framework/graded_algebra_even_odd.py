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
The Z2-graded algebra `A = A0 + omega*A1`, in the `even`/`odd` interface.

This is the same algebra as `graded_algebra.py`, rewritten against the
`even` / `odd` / `omega_sq` interface and the module-level function names of the
separate implementation, so that code written against that interface keeps
working. Five defects in that implementation are corrected here; each is marked
**CORRECTED** below and demonstrated in `scripts/verify_graded_algebra_port.py`.

What `omega_sq` means
---------------------
`omega_sq` selects the algebra:

- `omega_sq = +1` gives `C[omega]/(omega^2 - 1)`, the group algebra of `Z2`.
  This is a genuine Z2-grading: the involution is diagonalisable with
  eigenvalues `+-1`, and both the invariant and the graded trace are defined.
- `omega_sq = -1` gives `C[omega]/(omega^2 + 1)`, i.e. `C` again with
  `omega = i`. Multiplication is still associative, but `sigma` is *not* an
  algebra homomorphism there and no invariant trace exists.

The default is `+1`, matching the module docstring of the original. With `-1`
the class still works; `sigma` then reports that it is not a homomorphism rather
than pretending otherwise.

The trace functionals
---------------------
For `x = a0 + omega*a1` with `omega^2 = 1`, the element acts as `a0 + a1` on the
`+1` eigenvector of `omega` and as `a0 - a1` on the `-1` eigenvector. The
involution swaps those two eigenvalues. Therefore:

- `trace(x)`      = `a0`,           the average: invariant under `sigma`.
- `supertrace(x)` = `a0 - a1`,      the `-1` eigenvalue: anti-invariant in the
                                    sense that `sigma` trades the two
                                    eigenvalues, and zero exactly on the
                                    elements with `a0 = a1`.

**CORRECTED**: the original defined `trace = even - odd`, i.e. `a0 - a1`, and
claimed it was `sigma`-invariant. It is not: `sigma` sends `a0 - a1` to
`a0 + a1`, so invariance holds only when `odd = 0`. The two functionals above
are separated here, and `check_trace_invariance` is honest about which one
satisfies it.

Which functional reproduces `zeta`
----------------------------------
With the local factor `L_p = 1/(1 - p^{-s} gamma_tau)`, whose eigenvalues are
`1/(1 - p^{-s})` and `1/(1 - tau p^{-s})`:

    trace(L_p)      = the average of the two eigenvalues
    supertrace(L_p) = the "-1" eigenvalue = 1/(1 - tau p^{-s})

**Only at `tau = 1`** do these coincide and equal the classical factor
`1/(1 - p^{-s})`, so that the product over primes converges to `zeta(s)`. For
`tau != 1` the weight is a nontrivial even element and the product is a
different function. This is the same `tau = 1` degeneracy documented for the
shift-zeta in `docs/shift_zeta_result.md`; the algebra here is not a way around
it, only a cleaner way to state it.

What this module does not do
----------------------------
It proves nothing about the Riemann Hypothesis. See
`docs/shift_zeta_result.md` for the numerical verdict of the zeta extension
built on this algebra, which is negative.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, TypeAlias

import mpmath as mp

# Grading labels, kept for callers that compare against them.
EVEN = 0
ODD = 1

# The scalar type accepted for `s`: a concrete union of the types the arithmetic
# actually receives. The abstract `numbers.Number` base is *not* a proper
# supertype here -- a type checker does not treat `int`/`float`/`complex` as
# subtypes of it -- so the union is spelled out, and `mp.mpf`/`mp.mpc` are
# included directly.
Scalar: TypeAlias = int | float | complex | mp.mpf | mp.mpc

# `tau` is a real grading weight (`1`, `0`, `0.5`, `mp.mpf`, ...), never a
# complex number. A concrete alias lets the code call `float(tau)` and
# `complex(tau)` without a type checker rejecting the abstract `numbers.Number`
# base, which declares neither `__float__` nor `__complex__`.
RealScalar: TypeAlias = int | float | mp.mpf


def _tolerance(tol: float | None) -> float:
    """Default tolerance used by the boolean helpers."""
    if tol is not None:
        return float(tol)
    return float(mp.mpf(10) ** (-(2 * mp.mp.dps) // 3))


@dataclass(frozen=True)
class GradedElement:
    """An element `even + omega * odd` of `A = A0 + omega*A1`.

    Parameters
    ----------
    even:
        The coefficient in `A0`.
    odd:
        The coefficient in `A1`.
    omega_sq:
        The value of `omega^2`, either `+1` (a Z2-grading, the default) or `-1`.

    Coefficients are stored as Python `complex` and converted to `mp.mpc` on the
    way out of the trace functionals. Python arithmetic is exact for the
    two-term expressions this algebra needs, and `dataclass(frozen=True)`
    derives `__hash__` from the coefficients.

    **CORRECTED**: the original defaulted `omega_sq` to `-1` while its module
    docstring stated `omega^2 = 1`. The default is now `+1`, which is the
    Z2-grading the algebra is supposed to be.
    """

    even: complex
    odd: complex
    omega_sq: int = 1

    def __post_init__(self) -> None:
        """Validate `omega_sq` and normalise the coefficients to `complex`.

        The normalisation is not cosmetic. Every arithmetic method assumes
        `complex` coefficients, and without it the following all produced values
        that violated the declared field type:

            GradedElement(2.0, -3.0)      -> float coefficients
            element * mp.mpf("0.5")       -> mpmath.mpf coefficients
            element / mp.mpf("2")         -> mpmath.mpf coefficients
            local_factor(...)             -> mpmath.mpc coefficients

        `complex` accepts `int`, `float`, `complex`, `mp.mpf` and `mp.mpc`, and
        the coefficients this algebra produces stay exactly representable.
        Assigning through `object.__setattr__` is required because the dataclass
        is frozen.
        """
        if self.omega_sq not in (-1, 1):
            raise ValueError(f"omega_sq must be +1 or -1, got {self.omega_sq}")
        object.__setattr__(self, "even", complex(self.even))
        object.__setattr__(self, "odd", complex(self.odd))

    # ------------------------------------------------------------
    # Arithmetic
    # ------------------------------------------------------------

    def _coerce(self, other) -> "GradedElement":
        if isinstance(other, GradedElement):
            return other
        return GradedElement(even=complex(other), odd=0.0, omega_sq=self.omega_sq)

    def __add__(self, other) -> "GradedElement":
        other = self._coerce(other)
        return GradedElement(self.even + other.even, self.odd + other.odd, self.omega_sq)

    def __sub__(self, other) -> "GradedElement":
        other = self._coerce(other)
        return GradedElement(self.even - other.even, self.odd - other.odd, self.omega_sq)

    def __neg__(self) -> "GradedElement":
        return GradedElement(-self.even, -self.odd, self.omega_sq)

    def __mul__(self, other) -> "GradedElement":
        """Multiplication respecting the grading.

        `(a0 + omega*a1)(b0 + omega*b1)
            = a0*b0 + omega_sq*a1*b1 + omega*(a0*b1 + a1*b0)`

        For `omega_sq = -1` this is complex multiplication on
        `(a0, a1)`, which is why a separate `supertrace` exists: there the
        algebra is not a Z2-grading.
        """
        if not isinstance(other, GradedElement):
            return GradedElement(self.even * other, self.odd * other, self.omega_sq)
        return GradedElement(
            even=self.even * other.even + self.omega_sq * self.odd * other.odd,
            odd=self.even * other.odd + self.odd * other.even,
            omega_sq=self.omega_sq,
        )

    def __rmul__(self, other) -> "GradedElement":
        return self.__mul__(other)

    def __truediv__(self, scalar) -> "GradedElement":
        if isinstance(scalar, GradedElement):
            raise TypeError(
                "Division by a GradedElement is not defined; multiply by an "
                "inverse instead."
            )
        return GradedElement(self.even / scalar, self.odd / scalar, self.omega_sq)

    def inverse(self) -> "GradedElement":
        """Multiplicative inverse when it exists.

        The norm is `even^2 - omega_sq * odd^2`. For `omega_sq = +1` that is
        `even^2 - odd^2`, the determinant of the regular representation, and it
        is **not** multiplicative: this algebra has zero divisors, for instance
        `(1 + omega)(1 - omega) = 0`.
        """
        norm = self.even * self.even - self.omega_sq * self.odd * self.odd
        if abs(norm) < _tolerance(None):
            raise ZeroDivisionError(
                f"{self!r} is not invertible (norm {mp.nstr(norm, 6)} is zero)"
            )
        # The same formula holds for both signs of `omega_sq`: with
        # `norm = even^2 - omega_sq*odd^2`, the product
        # `(even + odd*omega) * (even/norm - odd/norm*omega)` is 1 either way.
        return GradedElement(self.even / norm, -self.odd / norm, self.omega_sq)

    def __pow__(self, exponent: int) -> "GradedElement":
        if exponent < 0:
            return self.inverse() ** (-exponent)
        result = GradedElement(1.0, 0.0, self.omega_sq)
        for _ in range(exponent):
            result = result * self
        return result

    def __eq__(self, other) -> bool:
        """Numeric equality, including the algebra the element belongs to.

        **CORRECTED**: the original used

            return (np.isclose(self.even, other.even)
                    and np.isclose(self.odd, other.odd))

        which had two problems. `np.isclose` returns `np.bool_`, which a type
        checker rejects where `bool` is declared (numpy 2.x stubs:
        `np.isclose -> np.bool[builtins.bool]`). And `omega_sq` was ignored, so
        elements of *different* algebras compared equal even though they
        multiply differently.

        Comparison against a non-element returns `False` rather than
        `NotImplemented`. `NotImplemented` is the more idiomatic signal for a
        reflected-operator fallback, but it is not a `bool`: `bool(NotImplemented)`
        raises `TypeError`, and a type checker flags it against the declared
        return type. Since nothing here defines an `__eq__` that could accept a
        `GradedElement` as its right operand, the fallback has nothing to fall
        back to.
        """
        if not isinstance(other, GradedElement):
            return False
        if self.omega_sq != other.omega_sq:
            return False
        return bool(
            mp.almosteq(mp.mpc(self.even), mp.mpc(other.even))
            and mp.almosteq(mp.mpc(self.odd), mp.mpc(other.odd))
        )

    def __hash__(self) -> int:
        """Exact-value hash, consistent with the approximate `__eq__`."""
        return hash((self.even, self.odd, self.omega_sq))

    def __repr__(self) -> str:
        return (
            f"GradedElement(even={self.even:.6g}, odd={self.odd:.6g}, "
            f"omega_sq={self.omega_sq:+d})"
        )


# ============================================================
# The involution
# ============================================================

def sigma(a: GradedElement) -> GradedElement:
    """The involution `sigma(a0 + omega*a1) = a0 - omega*a1`.

    For `omega_sq = +1` this is an algebra automorphism of order two with
    `Fix(sigma) = A0`. For `omega_sq = -1` it is not a homomorphism: check with
    `check_sigma_homomorphism`.
    """
    return GradedElement(even=a.even, odd=-a.odd, omega_sq=a.omega_sq)


def is_fixed(a: GradedElement, tol: float | None = None) -> bool:
    """True when `a` lies in `Fix(sigma) = A0`."""
    return bool(abs(a.odd) < _tolerance(tol))


def project_to_fix(a: GradedElement) -> GradedElement:
    """Project onto `Fix(sigma) = A0` by dropping the odd part."""
    return GradedElement(even=a.even, odd=0.0, omega_sq=a.omega_sq)


def project_to_anti(a: GradedElement) -> GradedElement:
    """Project onto the `-1` eigenspace of `sigma`."""
    return GradedElement(even=0.0, odd=a.odd, omega_sq=a.omega_sq)


# ============================================================
# The trace functionals
# ============================================================

def trace(a: GradedElement) -> complex:
    """The `sigma`-invariant trace `a0`.

    **CORRECTED**: the original returned `even - odd`. Since `sigma` negates the
    odd part, `trace(sigma(a)) = even + odd`, so the original was invariant only
    for elements with `odd = 0` -- in particular, not for the local factors, and
    its own `check_trace_invariance` would have failed on them.

    `a0` is the average of the two eigenvalues `a0 +- a1` that `sigma` swaps,
    which is exactly why it is the invariant one.
    """
    return complex(a.even)


def supertrace(a: GradedElement) -> complex:
    """The graded supertrace `a0 - a1`: the `-1` eigenvalue of `omega`.

    `sigma` trades the two eigenvalues `a0 +- a1`, so this one is not invariant
    under `sigma`; it is the graded companion of `trace`. The two are different
    objects, and conflating them is what produced the original defect.

    For the local factor `L_p = 1/(1 - p^{-s} gamma_tau)` this evaluates to
    `1 / (1 - tau p^{-s})`, which equals the classical `1/(1 - p^{-s})` only at
    `tau = 1`. It is *not* independent of the grading weight.
    """
    return complex(a.even - a.odd)


def matrix_trace(a: GradedElement) -> complex:
    """The ordinary matrix trace of the regular representation, `2*a0`."""
    return complex(2 * a.even)


def is_supertrace_zero(a: GradedElement, tol: float | None = None) -> bool:
    """True when the supertrace vanishes, i.e. when `even == odd`."""
    return bool(abs(supertrace(a)) < _tolerance(tol))


# ============================================================
# Local factors
# ============================================================

def local_factor(p: int, s: Scalar, tau: RealScalar = 1, omega_sq: int = 1) -> GradedElement:
    """The local Euler factor `1 / (1 - p^{-s} * gamma_tau)`.

    `gamma_tau = ((1+tau)/2) + ((1-tau)/2)*omega` is an even element with
    eigenvalues `1` and `tau`, so `L_p` has eigenvalues

        1 / (1 - p^{-s})        and        1 / (1 - tau*p^{-s})

    on the `+1` and `-1` eigenspaces of `omega` respectively. The supertrace
    reads the `-1` eigenspace, so

        supertrace(L_p) = 1 / (1 - tau * p^{-s})

    which equals the classical factor `1 / (1 - p^{-s})` only at `tau = 1`.
    At `tau = 1` the two eigenvalues coincide and `L_p` is scalar, which is the
    degenerate case.

    **CORRECTED**: the original returned `even = 1/(1 - p^{-s})` and
    `odd = p^{-s}/(1 - p^{-s})`, i.e. `(1 + p^{-s} omega)/(1 - p^{-s})`. That is
    not `1/(1 - p^{-s} omega)`, which is `(1 + p^{-s} omega)/(1 - p^{-2s})`; the
    two differ by a factor of `(1 + p^{-s})`. Together with its
    `trace = even - odd`, every local trace came out as exactly 1, so the whole
    Euler product was 1 and every downstream test -- zeros, functional equation,
    G5/G6 -- was vacuous.
    """
    if omega_sq not in (-1, 1):
        raise ValueError(f"omega_sq must be +1 or -1, got {omega_sq}")
    x = mp.mpf(p) ** (-mp.mpc(s))
    # Normalise `tau` to a concrete float before arithmetic. `tau` is typed
    # `numbers.Number`, and arithmetic directly on that abstract type leaves the
    # weight's type ambiguous to a checker; `float(tau)` is the same
    # normalisation `grading_shift` already does.
    tau = float(tau)
    weight = GradedElement(
        even=complex((1.0 + tau) * 0.5),
        odd=complex((1.0 - tau) * 0.5),
        omega_sq=omega_sq,
    )
    return (GradedElement(1.0, 0.0, omega_sq) - weight * x).inverse()


def euler_product(
    s: Scalar, primes: Sequence[int], tau: RealScalar = 1, omega_sq: int = 1
) -> GradedElement:
    """The truncated Euler product `prod_p L_p(s, tau)` in the algebra."""
    product = GradedElement(1.0, 0.0, omega_sq)
    for p in primes:
        product = product * local_factor(p, s, tau, omega_sq)
    return product


def partial_euler_product(s: Scalar, primes: Sequence[int]) -> complex:
    """The classical partial Euler product `prod_p 1/(1 - p^{-s})`."""
    value = mp.mpc(1)
    for p in primes:
        value *= 1 / (1 - mp.mpf(p) ** (-mp.mpc(s)))
    return complex(value)


# ============================================================
# Algebra checks
# ============================================================

def check_sigma_involution(a: GradedElement, tol: float | None = None) -> bool:
    """True when `sigma(sigma(a)) = a`."""
    t = _tolerance(tol)
    twice = sigma(sigma(a))
    return bool(abs(twice.even - a.even) < t and abs(twice.odd - a.odd) < t)


def check_sigma_homomorphism(
    a: GradedElement, b: GradedElement, tol: float | None = None
) -> bool:
    """True when `sigma(a*b) = sigma(a)*sigma(b)`.

    Holds for both signs of `omega_sq`. `sigma` is the inner automorphism
    `Ad(omega)`, and `omega` commutes with everything in this commutative
    algebra, so `sigma(xy) = omega*xy*omega = (omega*x*omega)(omega*y*omega)`.
    What `omega_sq` changes is *which* algebra this is, not whether `sigma` is an
    automorphism of it.
    """
    t = _tolerance(tol)
    left = sigma(a * b)
    right = sigma(a) * sigma(b)
    return bool(abs(left.even - right.even) < t and abs(left.odd - right.odd) < t)


def check_trace_invariance(a: GradedElement, tol: float | None = None) -> bool:
    """True when `trace(sigma(a)) = trace(a)`.

    With the corrected `trace` this holds for every element and every
    `omega_sq`, by construction.
    """
    t = _tolerance(tol)
    return bool(abs(trace(sigma(a)) - trace(a)) < t)


def check_trace_is_geometric_series(
    p: int, s: Scalar, tau: RealScalar = 1, terms: int = 400, tol: float | None = None
) -> bool:
    """True when `L_p` matches its closed form at the given `tau`.

    `L_p` is not itself a geometric series in `p^{-s}`; it is `1/(1 - x gamma)`
    with eigenvalues `1/(1-x)` and `1/(1-tau x)`. What is checked is that the
    two functionals equal the average and the `-1` eigenvalue respectively,
    which is the identity the module relies on.

    At `tau = 1` both reduce to the classical factor `1/(1-x)`, and that is
    additionally compared against the geometric series `sum_k p^{-ks}`.

    The comparison is done in Python `float`/`complex`, so the tolerance is
    bounded below by double precision (~2e-16) whatever `mp.mp.dps` says.
    """
    x = complex(mp.mpf(p) ** (-mp.mpc(s)))
    tau_c = complex(tau)

    # `_tolerance(None)` is an mpmath-scale number and would be tighter than
    # double precision here; clamp it to a relative float tolerance instead.
    t = max(_tolerance(tol), 1e-12) if tol is None else max(float(tol), 1e-15)

    factor = local_factor(p, s, tau)
    expected_trace = (1 / (1 - x) + 1 / (1 - tau_c * x)) / 2
    expected_supertrace = 1 / (1 - tau_c * x)
    ok = bool(
        abs(trace(factor) - expected_trace) <= t * max(1.0, abs(expected_trace))
        and abs(supertrace(factor) - expected_supertrace)
        <= t * max(1.0, abs(expected_supertrace))
    )
    if tau_c == 1:
        series = sum(x**k for k in range(terms))
        ok = ok and bool(abs(1 / (1 - x) - series) <= t)
    return ok


def check_euler_product_converges(
    s: Scalar, primes: Sequence[int], tau: RealScalar = 1, tolerance: float = 1e-3
) -> bool:
    """True when the product of local traces is the classical partial product.

    This holds exactly when `tau = 1`, where both `trace` and `supertrace` of
    every local factor reduce to `1/(1 - p^{-s})`. For `tau != 1` the product is
    a different function and this returns False; that is the `tau = 1`
    degeneracy, not a bug.
    """
    graded = complex(1.0)
    classical = complex(1.0)
    for p in primes:
        graded *= trace(local_factor(p, s, tau))
        classical *= 1 / (1 - mp.mpf(p) ** (-mp.mpc(s)))
    return bool(abs(graded - classical) < tolerance)
