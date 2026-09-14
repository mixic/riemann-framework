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
# The functional equation
# ============================================================

def completed_zeta(s):
    """The completed zeta function `xi(s) = pi^{-s/2} Gamma(s/2) zeta(s)`.

    The classical completion, satisfying `xi(s) = xi(1-s)`.
    """
    s = mp.mpc(s)
    return mp.pi ** (-s / 2) * mp.gamma(s / 2) * mp.zeta(s)


def functional_equation_residual(
    s_values=(2, 3, 4, mp.mpf("2.5")),
    n_primes: int = DEFAULT_N_PRIMES,
) -> list[dict]:
    """Test `Z_A(s)` against `Z_A(1-s)` after completing with the classical factor.

    Two things are returned per sample point: the residual of the classical
    completed zeta function (a control, which should sit at numerical
    precision) and the residual of the same completion applied to the truncated
    graded product for several `tau`.

    The Euler product alone is not symmetric under `s -> 1-s`; the completion
    `pi^{-s/2} Gamma(s/2)` is what supplies the symmetry in the classical case.
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
        }

        for tau in (mp.mpf(1), mp.mpf(0), mp.mpf("0.5")):
            try:
                left = shift_zeta_element(s, tau, primes)
                right = shift_zeta_element(reflected, tau, primes)
                factor_s = mp.pi ** (-s / 2) * mp.gamma(s / 2)
                factor_r = mp.pi ** (-reflected / 2) * mp.gamma(reflected / 2)
                left_value = left.trace() * factor_s
                right_value = right.trace() * factor_r
                residual = abs(left_value - right_value) / max(
                    abs(left_value), mp.mpf(10) ** (-30)
                )
                entry[f"tau_{float(tau):g}_residual"] = float(residual)
            except ZeroDivisionError:
                entry[f"tau_{float(tau):g}_residual"] = float("nan")

        results.append(entry)

    return results


# ============================================================
# Zeros
# ============================================================

@dataclass
class ZeroComparison:
    """Deviation of shift-zeta zeros from the classical zeros."""

    tau: float
    classical_zeros: list
    shift_values_at_zeros: list
    max_absolute_value: float
    extra_zeros_found: list
    explanation: str
    metadata: dict = field(default_factory=dict)


def scan_for_extra_zeros(
    tau,
    t_max: float = 60.0,
    samples: int = 2400,
    threshold: float = 0.05,
    n_primes: int = DEFAULT_N_PRIMES,
) -> list[complex]:
    """Coarse scan for sign changes of the shift-zeta on the critical line.

    Returns the locations where the real part changes sign. This is a coarse
    diagnostic intended to catch gross disagreement, not to certify zeros.
    """
    primes = first_primes(n_primes)
    previous_t = None
    previous_value = None
    crossings: list[complex] = []

    for index in range(samples + 1):
        t = -t_max + 2 * t_max * index / samples
        point = mp.mpc(mp.mpf("0.5"), t)
        try:
            value = shift_zeta(point, tau, primes)
        except ZeroDivisionError:
            previous_t = None
            previous_value = None
            continue

        if previous_value is not None and previous_value.real * value.real < 0:
            crossings.append(complex(mp.mpf("0.5"), (previous_t + t) / 2))

        previous_t = t
        previous_value = value

    return crossings


def compare_zeros(
    tau=1,
    n_zeros: int = 8,
    n_primes: int = DEFAULT_N_PRIMES,
    scan: bool = True,
) -> ZeroComparison:
    """Evaluate the shift-zeta at classical zeros and measure the deviation.

    Criterion G6 asks whether the shift-zeta zeros coincide with the classical
    ones. Evaluating at the classical zeros is the cheap half of that question:
    if the shift-zeta has a zero there, the value should vanish.

    Passing is not sufficient on its own -- `c * zeta(s)` for constant `c`
    passes trivially -- so `extra_zeros_found` reports whether a coarse scan
    turns up sign changes where the classical function does not vanish.
    """
    zeros = [mp.zetazero(k) for k in range(1, n_zeros + 1)]
    values = [complex(shift_zeta(zero, tau, n_primes)) for zero in zeros]
    max_abs = max(abs(v) for v in values) if values else float("nan")

    extra: list[complex] = []
    if scan:
        classical_heights = sorted(float(mp.im(z)) for z in zeros)
        for point in scan_for_extra_zeros(tau, n_primes=n_primes):
            height = point.imag
            if min(abs(height - h) for h in classical_heights) > 1.0:
                extra.append(point)

    if max_abs < 1e-6:
        explanation = (
            f"At tau={tau:g} the shift-zeta vanishes at all {n_zeros} tested "
            f"classical zeros (max |Z| = {max_abs:.3e})."
        )
        if extra:
            explanation += (
                f" But the coarse scan also found {len(extra)} sign change(s) away "
                "from the classical zeros, so the zero sets do not coincide."
            )
        else:
            explanation += (
                " No additional sign changes were found away from the classical "
                "zeros in the scanned range."
            )
    else:
        explanation = (
            f"At tau={tau:g} the shift-zeta does not vanish at the classical zeros "
            f"(max |Z| = {max_abs:.3e}), so its zeros are not the classical zeros."
        )

    return ZeroComparison(
        tau=float(tau),
        classical_zeros=[complex(z) for z in zeros],
        shift_values_at_zeros=values,
        max_absolute_value=max_abs,
        extra_zeros_found=extra,
        explanation=explanation,
        metadata={"n_primes": n_primes, "n_zeros": n_zeros, "scanned": scan},
    )
