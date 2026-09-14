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
The shift-zeta: the Euler product lifted into the graded algebra.

Definition
----------
For a finite set of primes and a grading weight `gamma_tau`,

    Z_A(s) = prod_p 1 / (1 - p^{-s} * gamma_tau)      in A = C[omega]/(omega^2-1)

Any trace of this algebra element gives a complex-valued "shift-zeta". The
three traces defined in `graded_algebra.py` produce three very different scalar
functions, and that difference is the finding of this module.

At `tau = 1` the weight is `gamma_1 = I`, every local factor is a scalar in the
even part, and `Z_A(s)` is `zeta(s)` times the identity. The interesting
question is what the grading does for `tau != 1`.

What the numerics show
----------------------
Enumerated in `docs/shift_zeta_result.md`. The short version:

- `trace` reads off the coefficient of `I`, which cancels the `tau`-dependence
  exactly: it returns `zeta(s)` for every `tau`, so the grading is invisible
  and cannot be used to test where the zeros are.
- `supertrace` does depend on `tau`, and its zeros are then *not* the classical
  zeros -- a genuine disagreement (falsification criterion F1).
- `matrix_trace` is not `sigma`-invariant, so it fails criterion G3 outright.

Structural reason for the first point: every local factor is built from
`gamma_tau`, an element of the even part, so the entire product lies in the
even part `A0 = Fix(sigma)`. The construction is confined to the fixed locus by
definition and therefore cannot probe whether the zeros are forced there.

Nothing here proves anything about RH. These are numerical and algebraic
observations about one specific, fully explicit construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import mpmath as mp

from .graded_algebra import GradedElement, local_factor

# Number of primes used when no explicit set is supplied.
DEFAULT_N_PRIMES = 60


def first_primes(count: int) -> list[int]:
    """Return the first `count` primes, by trial division."""
    if count < 1:
        raise ValueError(f"count must be >= 1, got {count}")
    primes: list[int] = []
    candidate = 2
    while len(primes) < count:
        if all(candidate % p for p in primes if p * p <= candidate):
            primes.append(candidate)
        candidate += 1
    return primes


# ============================================================
# The Euler product in the algebra
# ============================================================

def shift_zeta_element(s, tau=1, primes: list[int] | None = None) -> GradedElement:
    """The truncated Euler product `prod_p (1 - p^{-s} gamma_tau)^{-1}` in `A`.

    Raises `ZeroDivisionError` if any local factor is singular.
    """
    if primes is None:
        primes = first_primes(DEFAULT_N_PRIMES)

    product = GradedElement.identity()
    for p in primes:
        product = product * local_factor(p, s, tau)
    return product


def shift_zeta(s, tau=1, primes: list[int] | None = None):
    """The `tau`-weighted shift-zeta: the graded trace of the Euler product.

    Returns the coefficient of the identity in `Z_A(s)`, which is the
    `sigma`-invariant trace. At `tau = 1` it equals the classical `zeta(s)`.
    """
    return shift_zeta_element(s, tau, primes).trace()


def shift_zeta_supertrace(s, tau=1, primes: list[int] | None = None):
    """The supertrace of the Euler product, for comparison."""
    return shift_zeta_element(s, tau, primes).supertrace()


def shift_zeta_matrix_trace(s, tau=1, primes: list[int] | None = None):
    """The ordinary matrix trace of the Euler product."""
    return shift_zeta_element(s, tau, primes).matrix_trace()


# ============================================================
# Comparisons against the classical baseline
# ============================================================

@dataclass
class TraceComparison:
    """Comparison of one trace of the shift-zeta against the classical zeta."""

    trace_name: str
    s_values: list
    shift_values: list
    zeta_values: list
    max_relative_error: float
    tau_dependence: float
    explanation: str
    metadata: dict = field(default_factory=dict)


def _relative_error(value, reference) -> float:
    denominator = abs(reference)
    if denominator == 0:
        return float(abs(value))
    return float(abs(value - reference) / denominator)


def compare_traces(
    tau_values=(1, 0, mp.mpf("0.5"), mp.mpf("0.25")),
    s_values=(2, 3, 4, 5),
    n_primes: int = DEFAULT_N_PRIMES,
) -> dict[str, TraceComparison]:
    """Compare all three traces of the shift-zeta against the classical zeta.

    For each trace the report gives the largest relative deviation from
    `zeta(s)` over the tested `s`, and how much the result moves when `tau`
    varies. A trace that reproduces zeta for every `tau` is grading-blind; a
    trace that moves with `tau` is actually testing the grading.
    """
    primes = first_primes(n_primes)
    results: dict[str, TraceComparison] = {}

    for name, functional in (
        ("trace", lambda s, tau: shift_zeta_element(s, tau, primes).trace()),
        ("supertrace", lambda s, tau: shift_zeta_element(s, tau, primes).supertrace()),
        (
            "matrix_trace",
            lambda s, tau: shift_zeta_element(s, tau, primes).matrix_trace(),
        ),
    ):
        shift_values = [functional(s, tau_values[0]) for s in s_values]
        zeta_values = [mp.zeta(s) for s in s_values]

        max_error = max(
            _relative_error(shift, reference)
            for shift, reference in zip(shift_values, zeta_values)
        )

        first_s = s_values[0]
        tau_samples = [functional(first_s, tau) for tau in tau_values]
        tau_dependence = float(max(abs(value - tau_samples[0]) for value in tau_samples))

        if tau_dependence < 1e-20 and max_error < 1e-10:
            explanation = (
                f"`{name}` reproduces zeta(s) to {max_error:.2e} relative error and "
                f"is completely independent of the grading weight tau (spread "
                f"{tau_dependence:.2e}). The grading is invisible to this trace, so "
                "it cannot test whether zeros lie in the fixed locus."
            )
        elif tau_dependence < 1e-20:
            explanation = (
                f"`{name}` is independent of tau but does not reproduce zeta(s) "
                f"(relative error {max_error:.2e})."
            )
        else:
            explanation = (
                f"`{name}` depends on tau (spread {tau_dependence:.3e} at s={first_s}), "
                f"so it does see the grading, but it then deviates from zeta(s) by up "
                f"to {max_error:.2e} relative error."
            )

        results[name] = TraceComparison(
            trace_name=name,
            s_values=[complex(s) for s in s_values],
            shift_values=[complex(v) for v in shift_values],
            zeta_values=[complex(v) for v in zeta_values],
            max_relative_error=max_error,
            tau_dependence=tau_dependence,
            explanation=explanation,
            metadata={
                "n_primes": n_primes,
                "tau_values": [float(t) for t in tau_values],
            },
        )

    return results


# ============================================================
# Baseline helpers
# ============================================================

def classical_partial_euler(s, primes) -> mp.mpc:
    """The truncated classical Euler product `prod_p 1/(1 - p^{-s})`.

    This is the right baseline for the graded product: at `tau = 1` the graded
    trace equals this object term by term, so comparing against it cancels the
    Euler truncation error, which at the first zeta zero is around `1e-1` with
    40 primes and would otherwise swamp the signal.
    """
    value = mp.mpc(1)
    for p in primes:
        value *= 1 / (1 - mp.mpf(p) ** (-mp.mpc(s)))
    return value


def graded_to_classical_ratio(s, tau, primes) -> mp.mpc:
    """`Z_A(s, tau).trace() / classical_partial_euler(s, primes)`.

    Both sides are finite products over the same primes, so truncation largely
    cancels and the ratio isolates the effect of the grading. At `tau = 1` the
    ratio is exactly 1.
    """
    graded = shift_zeta_element(s, tau, primes).trace()
    classical = classical_partial_euler(s, primes)
    if abs(classical) < mp.mpf(10) ** (-30):
        raise ZeroDivisionError("classical partial product vanished")
    return graded / classical


def ratio_profile(tau, s_values, n_primes: int = DEFAULT_N_PRIMES) -> dict:
    """Ratio of the graded trace to the classical partial product over `s`."""
    primes = first_primes(n_primes)
    ratios = []
    for s in s_values:
        try:
            ratios.append(graded_to_classical_ratio(s, tau, primes))
        except ZeroDivisionError:
            ratios.append(mp.mpc("nan"))
    return {
        "tau": float(tau),
        "s_values": [complex(s) for s in s_values],
        "ratios": [complex(r) for r in ratios],
        "n_primes": n_primes,
    }


# ============================================================
# The functional equation
# ============================================================

def completed_zeta(s):
    """The completed zeta function `xi(s) = pi^{-s/2} Gamma(s/2) zeta(s)`,
    satisfying `xi(s) = xi(1-s)`."""
    s = mp.mpc(s)
    return mp.pi ** (-s / 2) * mp.gamma(s / 2) * mp.zeta(s)


def functional_equation_residual(
    s_values=(mp.mpf("2.5"), mp.mpf("3.5"), mp.mpf("4.5")),
    n_primes: int = DEFAULT_N_PRIMES,
) -> list[dict]:
    """Test completion symmetry for the graded trace against a classical control.

    Each sample point reports:

    - `classical_residual`: `|xi(s) - xi(1-s)| / |xi(s)|` using mpmath's zeta.
      This is a control and sits at numerical precision.
    - `tau_<t>_residual`: the formally identical completion applied to the
      graded trace.

    Two traps this function avoids, both of which produced meaningless
    residuals in an earlier version:

    1. `Gamma(s/2)` has poles at `s = 0, -2, -4, ...`, so the reflected point
       `1-s` must avoid them. The defaults `2.5, 3.5, 4.5` reflect to
       `-1.5, -2.5, -3.5`, which are pole-free.
    2. The Euler product converges only for `Re(s) > 1`. The reflected side
       `1-s` has `Re < 0`, where the product diverges, so no graded evaluation
       exists there. The classical analytic continuation is used on that side
       instead, which means the graded residual is *not* a test of a graded
       functional equation -- it measures the mismatch between the graded
       product at `s` and the classical continuation at `1-s`. The
       `reflected_convergent` flag records this.
    """
    primes = first_primes(n_primes)
    results = []

    for s in s_values:
        s = mp.mpc(s)
        reflected = 1 - s

        classical_residual = abs(completed_zeta(s) - completed_zeta(reflected)) / abs(
            completed_zeta(s)
        )

        entry = {
            "s": complex(s),
            "classical_residual": float(classical_residual),
            "reflected_convergent": bool(mp.re(reflected) > 1),
        }

        for tau in (mp.mpf(1), mp.mpf(0), mp.mpf("0.5")):
            try:
                left = shift_zeta_element(s, tau, primes).trace()
                factor_left = mp.pi ** (-s / 2) * mp.gamma(s / 2) * left

                if mp.re(reflected) > 1:
                    right = shift_zeta_element(reflected, tau, primes).trace()
                else:
                    right = mp.zeta(reflected)

                factor_right = (
                    mp.pi ** (-reflected / 2) * mp.gamma(reflected / 2) * right
                )
                residual = abs(factor_left - factor_right) / max(
                    abs(factor_left), mp.mpf(10) ** (-30)
                )
                entry[f"tau_{float(tau):g}_residual"] = float(residual)
            except (ZeroDivisionError, ValueError):
                entry[f"tau_{float(tau):g}_residual"] = float("nan")

        results.append(entry)

    return results


# ============================================================
# Zeros
# ============================================================

@dataclass
class ZeroComparison:
    """Comparison of the graded zero set with the classical zero set."""

    tau: float
    classical_zeros: list
    ratios_at_zeros: list
    ratio_spread: float
    ratio_at_controls: list
    mean_ratio_at_zeros: float
    mean_ratio_at_controls: float
    explanation: str
    metadata: dict = field(default_factory=dict)


def compare_zeros(
    tau=1,
    n_zeros: int = 6,
    n_primes: int = 200,
    t_controls=(11.0, 16.0, 25.0, 33.0),
) -> ZeroComparison:
    """Compare the graded zero set with the classical one via a ratio profile.

    The decisive diagnostic is `R(s) = Z_A(s, tau) / classical_partial(s)`,
    where the classical baseline is the *same truncated product*. Both sides
    are finite products over the same primes, so the Euler truncation error --
    around `1e-1` at the first zero with 40 primes, the same order as the
    signal -- largely cancels, and `R` isolates the effect of the grading.

    If the graded function vanished at the same points as the classical one,
    `R` would be of comparable size at the classical zeros and at generic
    points on the critical line. If the zeros move, `R` is suppressed at the
    classical zeros and grows elsewhere.
    """
    if mp.mpf(tau) == 1:
        return ZeroComparison(
            tau=1.0,
            classical_zeros=[],
            ratios_at_zeros=[],
            ratio_spread=float("nan"),
            ratio_at_controls=[],
            mean_ratio_at_zeros=float("nan"),
            mean_ratio_at_controls=float("nan"),
            explanation=(
                "tau = 1 is degenerate: the weight is the identity, so the graded "
                "trace *is* the classical partial Euler product and R(s) is "
                "identically 1. The zero sets agree trivially, which is exactly "
                "why this case carries no evidence either way."
            ),
            metadata={"n_primes": n_primes, "degenerate": True},
        )

    primes = first_primes(n_primes)
    zeros = [mp.zetazero(k) for k in range(1, n_zeros + 1)]

    ratios_at_zeros = []
    for zero in zeros:
        try:
            ratios_at_zeros.append(graded_to_classical_ratio(zero, tau, primes))
        except ZeroDivisionError:
            ratios_at_zeros.append(mp.mpc("nan"))

    ratios_at_controls = []
    for t in t_controls:
        point = mp.mpc(mp.mpf("0.5"), mp.mpf(t))
        try:
            ratios_at_controls.append(graded_to_classical_ratio(point, tau, primes))
        except ZeroDivisionError:
            ratios_at_controls.append(mp.mpc("nan"))

    finite = [abs(r) for r in ratios_at_zeros if not mp.isnan(abs(r))]
    controls = [abs(r) for r in ratios_at_controls if not mp.isnan(abs(r))]

    mean_zero = float(sum(finite) / len(finite)) if finite else float("nan")
    mean_control = float(sum(controls) / len(controls)) if controls else float("nan")
    spread = (
        float(max(finite) / min(finite))
        if finite and min(finite) > 0
        else float("inf")
    )

    if mean_control > 0 and mean_zero > 0:
        ratio_of_means = mean_control / mean_zero
        if ratio_of_means > 5:
            verdict = (
                "The graded function is suppressed precisely where the classical "
                "one vanishes, which is the signature of *different* zeros."
            )
        elif ratio_of_means < 0.2:
            verdict = (
                "The graded function is *larger* at the classical zeros than at "
                "control points, which is also inconsistent with a common zero set."
            )
        else:
            verdict = (
                "The ratio does not separate the classical zeros from control "
                "points at this truncation, so this diagnostic is inconclusive "
                "for this tau."
            )
    else:
        verdict = "The ratio could not be computed at this truncation."

    explanation = (
        f"At tau={tau:g}, mean |R| = {mean_zero:.4e} at the classical zeros "
        f"(spread {spread:.2f}) versus {mean_control:.4e} at control points. "
        f"{verdict}"
    )

    return ZeroComparison(
        tau=float(tau),
        classical_zeros=[complex(z) for z in zeros],
        ratios_at_zeros=[complex(r) for r in ratios_at_zeros],
        ratio_spread=spread,
        ratio_at_controls=[complex(r) for r in ratios_at_controls],
        mean_ratio_at_zeros=mean_zero,
        mean_ratio_at_controls=mean_control,
        explanation=explanation,
        metadata={"n_primes": n_primes, "n_zeros": n_zeros},
    )
