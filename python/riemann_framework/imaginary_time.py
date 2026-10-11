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
Imaginary time: why the partition function exists and the oscillating sum does not.

The repository already has both halves of the physics analogy, in separate places:
the primon gas (`primon_gas.py`), where `Tr[e^{-sH}] = zeta(s)` is an exact operator
trace, and the spectral picture, where the zeta zeros are read as energy levels.
This module supplies the *bridge* between them, which is the Wick rotation
`t -> -i tau`, and it does so by making one point that neither half states:

    the real-time trace DIVERGES. It is the imaginary-time trace that converges.

On the primon gas `H|n> = log(n)|n>`, so

    real time:      Tr[e^{-iHt}] = sum_n n^{-it}       terms have modulus 1
    imaginary time: Tr[e^{-tau H}] = sum_n n^{-tau}    converges for tau > 1
                                                      = zeta(tau)

The real-time summands do not decay at all -- `|n^{-it}| = 1` -- so its partial
sums grow like `N`, and `zeta(it)` exists only by analytic continuation. The
imaginary-time summands decay exponentially, so the trace exists outright. That
asymmetry *is* the content of "imaginary time" here, and it is not a metaphor: it
is the difference between a sum that converges and one that does not.

Two consequences worth having straight
--------------------------------------
**The critical strip is the continuation problem.** The thermal trace exists for
`Re s > 1` and nowhere else; everything at `Re s <= 1`, including the entire
critical strip where the zeros live, is reached by analytic continuation, not by
summation. So the region RH is about is precisely the region where the partition
function does not exist as a sum.

**`beta = 1` is a Hagedorn temperature, not Bose-Einstein condensation.** The
number of states with energy at most `E` is `floor(e^E)`, because `E_n = log n`.
An exponentially growing density of states gives a maximum temperature rather than
a condensate: the partition function diverges as `beta -> 1+` because the state
count outruns the Boltzmann factor. The account this module was written against
calls it "related to Bose-Einstein condensation"; `density_of_states` and
`state_count` measure the exponential growth, and the distinction is recorded in
`HAGEDORN_NOTE`.

Nothing here proves or disproves the Riemann hypothesis.
"""

from __future__ import annotations

from dataclasses import dataclass

import mpmath as mp
import numpy as np

from .primon_gas import trace_exp


#: The temperature at which the arithmetic gas runs out of partition function,
#: and why that is not a condensate.
HAGEDORN_NOTE = (
    "The primon gas has an exponentially growing density of states, "
    "rho(E) ~ e^E, because the n-th level sits at E_n = log n. That produces a "
    "Hagedorn temperature: a MAXIMUM temperature at beta = 1, above which the "
    "partition function diverges because the state count outruns the Boltzmann "
    "factor. It is not Bose-Einstein condensation, which is what happens when a "
    "finite density of states is exhausted at a minimum temperature. The two are "
    "opposite in direction and the distinction is measurable -- see "
    "`state_count` and `density_ratio`."
)


# ============================================================
# Real time versus imaginary time, on the same operator
# ============================================================

def oscillatory_trace(t: float, n_max: int, dps: int = 30) -> mp.mpc:
    """`sum_{n<=N} n^{-it}`, the real-time trace `Tr[e^{-iHt}]` truncated.

    Every term has modulus 1, so this does not converge: the partial sums grow
    like `N / |1 - it|`. That is the point of the function, not a defect in it.
    """
    with mp.workdps(dps):
        return mp.fsum(mp.power(n, -mp.mpc(0, t)) for n in range(1, n_max + 1))


def thermal_trace(beta: float, n_max: int) -> complex:
    """`sum_{n<=N} n^{-beta}`, the imaginary-time trace `Tr[e^{-beta H}]`.

    Delegates to the primon gas, which is where this operator already lives, so
    the two tracks cannot drift apart.
    """
    if beta <= 0:
        raise ValueError("beta must be positive")
    return trace_exp(beta, n_max)


def oscillatory_growth(t: float, sizes: list[int]) -> list[float]:
    """`|sum_{n<=N} n^{-it}| / N` at each `N`.

    Constant in `N` means linear growth of the partial sums, which is what
    divergence looks like here: the summands never decay.
    """
    if t == 0:
        raise ValueError("t = 0 makes the sum the identity and is not the case of interest")
    return [float(abs(oscillatory_trace(t, n))) / n for n in sizes]


def thermal_convergence(beta: float, sizes: list[int]) -> list[float]:
    """`|sum_{n<=N} n^{-beta} - zeta(beta)|` at each `N`: geometric decay.

    Compare with `oscillatory_growth`. Side by side they are the whole content of
    the Wick rotation: one error falls to zero, the other does not fall at all.
    """
    if beta <= 1:
        raise ValueError(
            "beta must exceed 1: below that the thermal trace does not converge "
            "either, which is exactly the continuation problem this module is about"
        )
    exact = mp.zeta(beta)
    return [float(abs(trace_exp(beta, n) - exact)) for n in sizes]


# ============================================================
# Hagedorn, measured
# ============================================================

def state_count(energy: float) -> int:
    """`#{n : log n <= E} = floor(e^E)`: states below energy `E`."""
    if energy < 0:
        raise ValueError("energy must be non-negative")
    return int(mp.floor(mp.e**energy))


def density_ratio(energy: float) -> float:
    """`state_count(E) / state_count(E - 1)`, which tends to `e`.

    A constant ratio greater than 1 is exponential growth of the state count,
    which is what forces a Hagedorn temperature. A condensate would show this
    ratio falling towards 1 as the finite supply of low-lying states is used up.
    """
    if energy < 1:
        raise ValueError("energy must be at least 1")
    return state_count(energy) / state_count(energy - 1)


def hagedorn_beta() -> float:
    """`beta = 1`: where the thermal trace `zeta(beta)` has its pole."""
    return 1.0


def thermal_trace_near_hagedorn(betas: list[float], n_max: int = 200000) -> list[float]:
    """Truncated `Tr[e^{-beta H}]` approaching `beta -> 1+`, showing the blow-up."""
    return [float(abs(thermal_trace(beta, n_max))) for beta in betas]


# ============================================================
# The mechanism of the continuation: Jacobi's theta identity
# ============================================================

def jacobi_theta(x: float, n_terms: int = 40, dps: int = 40) -> mp.mpf:
    """`theta(x) = sum_{n in Z} e^{-pi n^2 x}`, the imaginary-time kernel.

    This is the function whose modular transformation supplies the analytic
    continuation, and unlike the Dirichlet series it converges for every `x > 0`
    -- because the exponent is quadratic in `n`, so the summands decay
    super-exponentially however small `x` is.
    """
    if x <= 0:
        raise ValueError("x must be positive")
    with mp.workdps(dps):
        xx = mp.mpf(x)
        total = mp.mpf(1)
        for n in range(1, n_terms + 1):
            total += 2 * mp.exp(-mp.pi * n * n * xx)
        return total


def theta_functional_equation_residual(x: float, n_terms: int = 40) -> float:
    """Relative residual of `theta(x) = x^{-1/2} theta(1/x)`.

    Jacobi's identity. It is worth checking rather than quoting because it is the
    exact mechanism by which a divergent-looking sum on one side becomes a
    convergent one on the other -- `x -> 1/x` is the `s -> 1 - s` of the
    functional equation, seen in imaginary time.
    """
    left = jacobi_theta(x, n_terms)
    right = mp.power(mp.mpf(x), mp.mpf(-0.5)) * jacobi_theta(1 / x, n_terms)
    scale = max(abs(left), abs(right))
    return float(abs(left - right) / scale)


# ============================================================
# The dictionary, as data
# ============================================================

@dataclass(frozen=True)
class WickRow:
    """One row of the real-time / imaginary-time correspondence."""

    concept: str
    real_time: str
    imaginary_time: str


def wick_table() -> list[WickRow]:
    """The `t -> -i tau` correspondence, for the record.

    Recorded as data rather than prose so that the module and any document
    quoting it cannot disagree.
    """
    return [
        WickRow("time", "real time t", "imaginary time tau = 1/T"),
        WickRow("evolution", "e^{-iEt}", "e^{-E tau}"),
        WickRow("behaviour", "oscillates", "decays"),
        WickRow("trace", "Tr[e^{-iHt}] = sum n^{-it}", "Tr[e^{-tau H}] = sum n^{-tau}"),
        WickRow("convergence", "diverges: |n^{-it}| = 1", "converges for tau > 1"),
        WickRow("what is needed", "analytic continuation", "nothing: the sum exists"),
        WickRow("domain", "the whole critical strip", "Re s > 1 only"),
    ]


def wick_rotation_check(beta: float, n_max: int = 5000) -> dict[str, float]:
    """Evaluate both traces at `s = beta` and `s = -i beta` on the same operator.

    `H` is the primon Hamiltonian in both cases; only the time is rotated. The
    returned magnitudes summarise the asymmetry: the thermal trace has settled at
    a finite value, the oscillatory one has not.
    """
    thermal = abs(thermal_trace(beta, n_max))
    oscillatory = float(abs(oscillatory_trace(beta, n_max)))
    return {
        "beta": beta,
        "thermal_magnitude": thermal,
        "oscillatory_magnitude": oscillatory,
        "ratio": oscillatory / thermal if thermal else float("inf"),
    }
