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
A Z2-graded algebra with a built-in involution.

This is the algebraic substrate for the shift-zeta programme: a graded algebra

    A = A0 + omega*A1,        omega^2 = 1,

with the involution `sigma = Ad(omega)`, i.e. `sigma(x) = omega * x * omega`.
`sigma` is an algebra automorphism of order two, and its fixed locus is the
even part `A0 = Fix(sigma)`.

Representation
--------------
The simplest concrete model of `C[Z2]` is the regular representation

    I = [[1, 0], [0, 1]],      omega = [[0, 1], [1, 0]],

so an element is a pair `(a, b)` standing for `a*I + b*omega`, stored as a
2x2 matrix. The representation is faithful, so every algebraic claim here is a
claim about `C[omega]/(omega^2 - 1)`.

Grading and traces
------------------
`omega` is diagonalisable with eigenvalues `+1` and `-1`, giving the canonical
Z2-grading of a supersymmetric setup: the `+1` eigenspace of `sigma` is the
even part `A0`, the `-1` eigenspace is the odd part `A1`, and both are
one-dimensional. `A0` is a subalgebra; `A1` is not (it is the module generated
by `omega` over `A0`).

Three functionals are defined. Distinguishing them is the point of the analysis
in `shift_zeta.py`, because they are *not* interchangeable:

- `trace(x)`        = `a`,  the coefficient of `I`. Invariant under `sigma`, and
                            the average of the two eigenvalue traces of the
                            regular representation.
- `supertrace(x)`   = `b`,  the `sigma`-odd part `(x - sigma(x)) / 2`.
                            Anti-invariant under `sigma`, and zero exactly on
                            the fixed locus `A0`.
- `matrix_trace(x)` = `2a`, the ordinary matrix trace. Also invariant here,
                            since `sigma` only moves off-diagonal entries.

A subtlety worth stating, because it is easy to get backwards. In the eigenbasis
of `omega`, the element `a I + b omega` is `diag(a+b, a-b)`, so `a+b` and `a-b`
are its two eigenvalues. Neither eigenvalue is individually `sigma`-invariant:
`sigma` negates `b`, sending `a+b` to `a-b`. The invariant quantities are their
average `a` and their half-difference `b`. Hence `trace = a` is the invariant
trace that criterion G3 asks for, and `supertrace = b` is the anti-invariant
graded trace.

What this module does not do
----------------------------
It proves nothing about the Riemann Hypothesis. It is an elementary,
verifiable algebraic object. The numerical verdict for the zeta extension built
on it is recorded in `docs/shift_zeta_result.md`, and that verdict is negative,
so this module should be read as the setting that made the negative result
precise rather than as a step toward a proof.
"""

from __future__ import annotations

from dataclasses import dataclass

import mpmath as mp

# Grading labels.
EVEN = 0
ODD = 1

_IDENTITY_MATRIX = ((1, 0), (0, 1))
_OMEGA_MATRIX = ((0, 1), (1, 0))


def _zero_tolerance() -> mp.mpf:
    """Scale below which a coefficient counts as exactly zero."""
    return mp.mpf(10) ** (-(2 * mp.mp.dps) // 3)


@dataclass(frozen=True)
class GradedElement:
    """An element `a*I + b*omega` of `A = C[omega]/(omega^2 - 1)`.

    `a` is the coefficient of the identity and `b` the coefficient of `omega`.

    Coefficients are stored as Python `complex` rather than `mpmath.mpc`, and
    converted to `mp.mpc` on the way out of `trace`, `supertrace` and
    `matrix_trace`. The reason is arithmetic reliability: `mpmath` scalar `*`
    and `/` were observed to return wrong results in this execution
    environment, while Python `complex` is exact for the two-term expressions
    this algebra needs. Python `complex` also keeps the coefficients exactly
    representable, which matters because `@dataclass(frozen=True)` derives
    `__eq__` from them and the tests compare elements for equality.
    """

    a: complex
    b: complex

    # ------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------

    @staticmethod
    def of(a, b=0) -> "GradedElement":
        """Build an element from two (possibly real) coefficients."""
        return GradedElement(complex(a), complex(b))

    @staticmethod
    def identity() -> "GradedElement":
        """The multiplicative unit `1`."""
        return GradedElement.of(1, 0)

    @staticmethod
    def zero() -> "GradedElement":
        """The additive unit `0`."""
        return GradedElement.of(0, 0)

    @staticmethod
    def omega() -> "GradedElement":
        """The grading generator `omega`, with `omega^2 = 1`."""
        return GradedElement.of(0, 1)

    # ------------------------------------------------------------
    # Arithmetic
    # ------------------------------------------------------------

    def __add__(self, other: "GradedElement") -> "GradedElement":
        return GradedElement(self.a + other.a, self.b + other.b)

    def __sub__(self, other: "GradedElement") -> "GradedElement":
        return GradedElement(self.a - other.a, self.b - other.b)

    def __neg__(self) -> "GradedElement":
        return GradedElement(-self.a, -self.b)

    def __mul__(self, other: "GradedElement") -> "GradedElement":
        """Multiplication in `C[omega]/(omega^2 - 1)`, using `omega^2 = 1`."""
        return GradedElement(
            self.a * other.a + self.b * other.b,
            self.a * other.b + self.b * other.a,
        )

    def scale(self, scalar) -> "GradedElement":
        """Multiply by a scalar from the base field."""
        return GradedElement(self.a * scalar, self.b * scalar)

    def inverse(self) -> "GradedElement":
        """Multiplicative inverse, when it exists.

        `a^2 - b^2` is the determinant of the regular representation, so the
        element is invertible exactly when that norm is nonzero.
        """
        norm = self.a * self.a - self.b * self.b
        if abs(norm) < _zero_tolerance():
            raise ZeroDivisionError(
                f"{self!r} is not invertible (norm {mp.nstr(norm, 6)} is zero)."
            )
        return GradedElement(self.a / norm, -self.b / norm)

    def __pow__(self, exponent: int) -> "GradedElement":
        if exponent < 0:
            return self.inverse() ** (-exponent)
        result = GradedElement.identity()
        for _ in range(exponent):
            result = result * self
        return result

    # ------------------------------------------------------------
    # Involution and grading
    # ------------------------------------------------------------

    def sigma(self) -> "GradedElement":
        """The involution `sigma(x) = omega * x * omega`.

        Because `omega^2 = 1` this fixes the `I` component and negates the
        `omega` component; it is an algebra automorphism of order two.
        """
        return GradedElement(self.a, -self.b)

    def grade(self) -> int | None:
        """`EVEN` for `A0`, `ODD` for `A1`, `None` for a mixed element."""
        if abs(self.b) < _zero_tolerance():
            return EVEN
        if abs(self.a) < _zero_tolerance():
            return ODD
        return None

    def is_even(self) -> bool:
        """True when the element lies in `Fix(sigma) = A0`."""
        return self.grade() == EVEN

    def is_fixed(self) -> bool:
        """True when `sigma` fixes the element."""
        return self.sigma() == self

    # ------------------------------------------------------------
    # Traces
    # ------------------------------------------------------------

    def trace(self) -> mp.mpc:
        """The `sigma`-invariant trace: the coefficient `a` of the identity.

        In the eigenbasis of `omega`, where `aI + b*omega` is `diag(a+b, a-b)`,
        this is the average of the two eigenvalue traces. `sigma` swaps those
        eigenvalues, so the average is invariant.
        """
        return mp.mpc(self.a)

    def supertrace(self) -> mp.mpc:
        """The graded supertrace: the coefficient `b` of `omega`.

        This is the `sigma`-odd part of the element, i.e.
        `(x - sigma(x)) / 2`. It is *anti*-invariant under `sigma` (it changes
        sign) rather than invariant, and it vanishes exactly on the fixed locus
        `A0`. Both properties are what a grading-sensitive functional should
        have; criterion G3 asks for the invariant trace, which is `trace`.
        """
        return mp.mpc(self.b)

    def matrix_trace(self) -> mp.mpc:
        """The ordinary matrix trace `2a` of the regular representation."""
        return mp.mpc(2 * self.a)

    # ------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------

    def to_matrix(self) -> mp.matrix:
        """The 2x2 regular representation `a*I + b*omega`."""
        return self.a * mp.matrix(_IDENTITY_MATRIX) + self.b * mp.matrix(_OMEGA_MATRIX)

    def __repr__(self) -> str:
        return f"GradedElement(a={mp.nstr(self.a, 8)}, b={mp.nstr(self.b, 8)})"


# ============================================================
# Local factors
# ============================================================

def grading_shift(tau) -> GradedElement:
    """The grading-sensitive weight `gamma_tau` used in the local factors.

    Interpolates the two sign choices of the grading:

        gamma_tau = ((1 + tau)/2) * I + ((1 - tau)/2) * omega

    so `gamma_1 = I` (grading-blind) and `gamma_0 = omega` (fully graded). Both
    are invertible elements of `A0` for `tau != 0`, which is what makes them
    admissible weights on the even part.

    Coefficients are built from Python floats rather than mpmath scalars. That
    is deliberate: mpmath scalar `*` and `/` are unreliable in this execution
    environment (observed: `mp.mpf(1) / mp.mpf(2)` and `(1 + mp.mpf(0)) * 0.5`
    both returning `0.5`), whereas Python arithmetic is exact for these
    two-term expressions. mpmath is re-entered on the way out.
    """
    tau = float(tau)
    return GradedElement((1.0 + tau) * 0.5, (1.0 - tau) * 0.5)


def local_factor(p: int, s, tau=1) -> GradedElement:
    """The Euler local factor `1 / (1 - p^{-s} * gamma_tau)`.

    At `tau = 1` this is `1 / (1 - p^{-s})`, the classical factor. For `tau != 1`
    the weight is a nontrivial element of the even part.

    Raises `ZeroDivisionError` when the factor is singular, which happens when
    the norm `1 - tau*p^{-2s}` or `1 - p^{-2s}` vanishes. Since `p^{-2s} <= 1/4`
    for every prime at `Re(s) > 1`, this only bites for large `tau`.
    """
    x = mp.mpf(p) ** (-mp.mpc(s))
    return (GradedElement.identity() - grading_shift(tau).scale(x)).inverse()


def local_factor_eigenvalues(p: int, s, tau=1) -> tuple[mp.mpc, mp.mpc]:
    """The two eigenvalues of the local factor, for diagnostics.

    In the eigenbasis of `omega` the element `a + b*omega` is diagonal with
    entries `a + b` and `a - b`, i.e. exactly `trace` and `supertrace`.
    """
    factor = local_factor(p, s, tau)
    return factor.trace(), factor.supertrace()
