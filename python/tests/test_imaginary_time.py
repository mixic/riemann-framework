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
"""Tests for the imaginary-time module.

The load-bearing test is the asymmetry itself: the oscillatory trace's partial
sums grow linearly while the thermal trace's error decays geometrically. That is
what "Wick rotation" means concretely here, and it is checked rather than
described.
"""

import mpmath as mp
import pytest

from riemann_framework.imaginary_time import (
    HAGEDORN_NOTE,
    density_ratio,
    hagedorn_beta,
    jacobi_theta,
    oscillatory_growth,
    oscillatory_trace,
    state_count,
    thermal_convergence,
    thermal_trace,
    thermal_trace_near_hagedorn,
    theta_functional_equation_residual,
    wick_rotation_check,
    wick_table,
)
from riemann_framework.primon_gas import trace_exp


# ============================================================
# The asymmetry that is the whole point
# ============================================================

def test_oscillatory_partial_sums_grow_linearly():
    """`|sum_{n<=N} n^{-it}| / N` is roughly constant: the sum diverges.

    Every summand has modulus 1, so the partial sums grow like `N`. This is why
    `zeta(it)` exists only by analytic continuation while `zeta(beta)` for
    `beta > 1` exists as a sum.
    """
    ratios = oscillatory_growth(13.0, [1000, 4000, 16000, 64000])
    assert all(r > 0.05 for r in ratios)
    # Constant across a 64-fold range of N, which is linear growth.
    assert max(ratios) / min(ratios) < 1.1


def test_thermal_error_decays_geometrically():
    """The imaginary-time trace converges, and fast."""
    errors = thermal_convergence(2.0, [100, 1000, 10000, 100000])
    assert all(errors[i] > errors[i + 1] for i in range(len(errors) - 1))
    assert errors[-1] < 1e-4


def test_the_two_traces_are_the_same_operator_at_different_times():
    """Rotating the time, not changing the system.

    The thermal trace delegates to the primon gas, so the two tracks cannot drift
    apart, and the oscillatory one is the same summand with `s = -i t`.
    """
    assert abs(thermal_trace(2.0, 500) - trace_exp(2.0, 500)) < 1e-15
    # At t = 0 the oscillatory sum is just N, which pins the convention.
    assert abs(oscillatory_trace(0.0, 100) - 100) < 1e-12


def test_wick_rotation_check_reports_the_asymmetry():
    result = wick_rotation_check(2.0, 4000)
    assert result["ratio"] > 1.0
    assert result["oscillatory_magnitude"] > result["thermal_magnitude"]


def test_thermal_convergence_rejects_the_non_convergent_range():
    """`beta <= 1` is the continuation problem, and is refused rather than run."""
    with pytest.raises(ValueError):
        thermal_convergence(0.5, [10, 100])
    with pytest.raises(ValueError):
        thermal_convergence(1.0, [10, 100])


def test_oscillatory_growth_rejects_t_zero():
    with pytest.raises(ValueError):
        oscillatory_growth(0.0, [10, 100])


# ============================================================
# Hagedorn, not Bose-Einstein
# ============================================================

def test_state_count_is_floor_exp():
    """`E_n = log n` means `#{n : E_n <= E} = floor(e^E)`."""
    assert state_count(0) == 1
    assert state_count(1) == 2
    assert state_count(10) == 22026
    assert state_count(20) == 485165195


def test_density_of_states_grows_exponentially():
    """The ratio settles at `e`, not at 1: a maximum temperature, not a condensate.

    A condensate exhausts a finite supply of low-lying states, so the ratio would
    fall towards 1. Here it stays at `e > 1` however large `E` gets, because
    `floor(e^E)` keeps doubling-ish forever.

    It is **not** monotone, and two drafts of this test asserted that it was: the
    floor makes the ratio oscillate around `e` -- `2.71825` at `E = 10` against
    `2.718282` at `E = 20`. The content is the level it settles at, not a trend.
    """
    ratios = [density_ratio(E) for E in (5, 10, 20, 30, 40)]
    assert all(r > 2.7 for r in ratios), "growth must not decay towards 1"
    assert ratios[0] > float(mp.e)
    assert ratios[-1] == pytest.approx(float(mp.e), abs=1e-6)
    assert "not Bose-Einstein condensation" in HAGEDORN_NOTE


def test_hagedorn_temperature_is_beta_one():
    assert hagedorn_beta() == 1.0


def test_the_trace_blows_up_approaching_hagedorn():
    """Truncated values grow as `beta -> 1+`, which is the maximum temperature."""
    values = thermal_trace_near_hagedorn([1.5, 1.2, 1.05], 200000)
    assert values == sorted(values)
    assert values[-1] > values[0]


# ============================================================
# The mechanism of the continuation
# ============================================================

def test_jacobi_theta_satisfies_its_functional_equation():
    """`theta(x) = x^{-1/2} theta(1/x)`, the imaginary-time `s -> 1 - s`.

    This is the identity that turns a slowly converging sum into a quickly
    converging one, and it is the mechanism behind the analytic continuation that
    the critical strip requires.
    """
    for x in (0.25, 0.5, 1.0, 2.0, 4.0):
        assert theta_functional_equation_residual(x) < 1e-14


def test_jacobi_theta_converges_even_for_tiny_x():
    """Unlike the Dirichlet series, because the exponent is quadratic in `n`.

    `theta` is finite for every `x > 0`; the thermal trace is finite only for
    `beta > 1`. That contrast is the reason the theta function can carry the
    continuation at all.
    """
    assert jacobi_theta(0.01, 40) > 0
    assert abs(theta_functional_equation_residual(0.01) ) < 1e-12
    with pytest.raises(ValueError):
        jacobi_theta(0.0)


# ============================================================
# The dictionary, as data
# ============================================================

def test_wick_table_records_the_divergence():
    rows = wick_table()
    trace_row = next(r for r in rows if r.concept == "trace")
    assert "n^{-it}" in trace_row.real_time
    assert "n^{-tau}" in trace_row.imaginary_time
    convergence = next(r for r in rows if r.concept == "convergence")
    assert "diverges" in convergence.real_time
    assert "converges" in convergence.imaginary_time


def test_wick_table_covers_the_domain_claim():
    """`Re s > 1` is exactly where the thermal trace exists."""
    domain = next(r for r in wick_table() if r.concept == "domain")
    assert "Re s > 1" in domain.imaginary_time
