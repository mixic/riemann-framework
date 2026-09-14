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
"""Tests for the falsification test of DSH."""

import pytest
import numpy as np

from riemann_framework.falsification_test import (
    run_single,
    run_grid,
    summarize_grid,
    classify_verdict,
    R_GUE,
    R_RIEMANN,
)
from riemann_framework.dimension_shift_chaos import build_dimension_shift_hamiltonian
from riemann_framework.quantum_chaos import riemann_zero_heights
from riemann_framework.spectral_density import (
    compare_spectral_density,
    riemann_von_mangoldt_count,
)


def test_classify_verdict_gue():
    assert classify_verdict(0.60) == "gue"


def test_classify_verdict_goe():
    assert classify_verdict(0.53) == "goe"


def test_classify_verdict_poisson():
    assert classify_verdict(0.39) == "poisson"


def test_classify_verdict_intermediate():
    assert classify_verdict(0.50) == "intermediate"


def test_single_run_returns_result():
    r = run_single(dim_per_sector=10, coupling=1.0,
                   symmetry_breaking=0.0, seed=42)
    assert 0.0 <= r.mean_r <= 1.0
    assert r.verdict in ("gue", "goe", "poisson", "intermediate")


def test_grid_runs():
    results = run_grid(
        dim_per_sector_values=[10],
        coupling_values=[0.0, 1.0],
        symmetry_breaking_values=[0.0, 1.0],
        seed=42,
    )
    assert len(results) == 4


def test_summary_reports_verdict():
    results = run_grid(
        dim_per_sector_values=[10, 20],
        coupling_values=[0.0, 1.0, 2.0],
        symmetry_breaking_values=[0.0, 1.0, 5.0],
        seed=42,
    )
    summary = summarize_grid(results)
    assert summary["n_runs"] == len(results)
    assert summary["verdict"] in (
        "supported", "goe_only", "poisson_only", "inconclusive"
    )
    assert summary["explanation"]  # non-empty


def test_riemann_von_mangoldt_count_is_finite_and_increasing():
    """The finite-height RvM reference is a valid cumulative-count baseline."""
    heights = np.array([20.0, 50.0, 100.0, 200.0])
    counts = riemann_von_mangoldt_count(heights)

    assert np.all(np.isfinite(counts))
    assert np.all(np.diff(counts) > 0)


def test_m3_spectral_density_report_compares_model_and_reference():
    """M3 reports finite-range density errors without claiming convergence."""
    model = np.linalg.eigvalsh(
        build_dimension_shift_hamiltonian(
            dim_per_sector=20,
            coupling=1.0,
            symmetry_breaking=0.0,
            seed=42,
        )
    )
    reference = riemann_zero_heights(30)
    report = compare_spectral_density(model, reference, grid_size=10)

    assert report["grid"].shape == (10,)
    assert report["scale"] > 0.0
    assert np.all(np.isfinite(report["model_fraction"]))
    assert np.all(np.isfinite(report["model_vs_rvm_rmse"]))
    assert report["model_vs_reference_rmse"] >= 0.0