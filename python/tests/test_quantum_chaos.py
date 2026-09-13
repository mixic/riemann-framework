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
"""Tests for quantum chaos analysis of the Riemann zeros."""

import pytest

from riemann_framework.quantum_chaos import (
    analyze_riemann_zeros,
    compare_reference_systems,
)
from riemann_framework.statistics import mean_r_ratio
from riemann_framework.zeta import set_precision


@pytest.fixture(autouse=True)
def setup_precision():
    set_precision(25)


def test_riemann_zeros_show_gue_statistics():
    """
    The first 100 Riemann zeros should show GUE statistics.

    Reference mean r-ratios:
      - Poisson: 0.386
      - GOE:     0.530
      - GUE:     0.599
    """
    result = analyze_riemann_zeros(n=100)
    mean_r = result["mean_r"]

    # The mean r-ratio should be close to GUE (0.599)
    assert 0.55 < mean_r < 0.65, (
        f"Mean r-ratio {mean_r:.3f} is not in the GUE range [0.55, 0.65]"
    )


def test_riemann_zeros_best_fit_is_gue():
    """The best-fit reference should be GUE."""
    result = analyze_riemann_zeros(n=100)
    best_fit = result["classification"]["best_fit"]
    assert best_fit == "gue", (
        f"Best-fit reference is {best_fit}, expected 'gue'"
    )


def test_ks_gue_better_than_poisson():
    """The KS distance to GUE should be smaller than to Poisson."""
    result = analyze_riemann_zeros(n=100)
    ks_gue = result["ks_gue"]["ks_stat"]
    ks_poisson = result["ks_poisson"]["ks_stat"]

    assert ks_gue < ks_poisson, (
        f"KS to GUE ({ks_gue:.3f}) is not smaller than "
        f"KS to Poisson ({ks_poisson:.3f})"
    )


def test_reference_systems_separate():
    """GUE, GOE, and Poisson reference systems should have distinct mean r."""
    result = compare_reference_systems(n=100, seed=42)

    assert result["gue"] > result["goe"] > result["poisson"], (
        f"Reference systems not separated: {result}"
    )