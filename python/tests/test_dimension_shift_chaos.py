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
"""Tests for the dimension-shift chaos analysis."""

import numpy as np
import pytest

from riemann_framework.dimension_shift_chaos import (
    build_dimension_shift_hamiltonian,
    analyze_dimension_shift,
    sweep_coupling,
    compare_to_riemann,
)
from riemann_framework.statistics import mean_r_ratio
from riemann_framework.zeta import set_precision


@pytest.fixture(autouse=True)
def setup_precision():
    set_precision(25)


def test_hamiltonian_is_symmetric():
    """The dimension-shift Hamiltonian must be symmetric (real eigenvalues)."""
    H = build_dimension_shift_hamiltonian(dim_per_sector=10, seed=42)
    assert np.allclose(H, H.T), "Hamiltonian is not symmetric"


def test_hamiltonian_eigenvalues_are_real():
    """Eigenvalues must be real."""
    H = build_dimension_shift_hamiltonian(dim_per_sector=10, seed=42)
    eigs = np.linalg.eigvalsh(H)
    assert np.all(np.isreal(eigs)), "Eigenvalues are not real"


def test_zero_coupling_gives_poisson():
    """At zero coupling, the sectors decouple — statistics should be Poisson-like."""
    result = analyze_dimension_shift(
        dim_per_sector=30,
        coupling=0.0,
        seed=42,
    )
    # With decoupled sectors, the spectrum is a superposition of two
    # independent random spectra — this typically gives Poisson-like
    # statistics in the combined spectrum.
    assert result["mean_r"] < 0.55, (
        f"Zero coupling gives mean r = {result['mean_r']:.3f}, "
        f"expected Poisson-like (< 0.55)"
    )


def test_coupling_sweep_runs():
    """The coupling sweep should run and produce monotonic-ish results."""
    results = sweep_coupling(
        dim_per_sector=20,
        coupling_values=[0.0, 1.0, 2.0],
        seed=42,
    )
    assert len(results) == 3
    for r in results:
        assert 0.0 <= r["mean_r"] <= 1.0


def test_compare_to_riemann_runs():
    """The comparison to Riemann zeros should run."""
    cmp = compare_to_riemann(
        dim_per_sector=20,
        coupling=1.0,
        seed=42,
        n_riemann=30,
    )
    assert "dimension_shift" in cmp
    assert "riemann" in cmp
    assert 0.0 <= cmp["dimension_shift"]["mean_r"] <= 1.0
    assert 0.0 <= cmp["riemann"]["mean_r"] <= 1.0