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
"""Tests for the symmetry-breaking stress test."""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.desymmetrisation import default_sector_count_model
from riemann_framework.dynamical_desymmetrisation import commutator_norm
from riemann_framework.symmetry_breaking import (
    block_hamiltonian,
    degradation_curve,
    mean_level_spacing,
    perturbed_spectrum,
    random_hermitian,
    sector_involution,
)


@pytest.fixture(scope="module")
def model():
    return default_sector_count_model(240)


def test_the_block_hamiltonian_has_the_symmetry_exactly():
    hamiltonian = block_hamiltonian(2, 20, "goe", np.random.default_rng(0))
    sigma = sector_involution(2, 20)
    assert commutator_norm(hamiltonian, sigma) < 1e-10


def test_a_perturbation_breaks_the_symmetry():
    generator = np.random.default_rng(1)
    hamiltonian = block_hamiltonian(2, 20, "goe", generator)
    sigma = sector_involution(2, 20)
    perturbation = random_hermitian(40, "goe", generator)
    broken = hamiltonian + 0.1 * perturbation
    assert commutator_norm(broken, sigma) > 1e-3


def test_the_mean_spacing_uses_the_central_window():
    levels = np.arange(100, dtype=float)
    assert mean_level_spacing(levels) == pytest.approx(1.0)


def test_the_perturbed_spectrum_has_the_right_size_and_ordering():
    generator = np.random.default_rng(2)
    hamiltonian = block_hamiltonian(2, 15, "gue", generator)
    perturbation = random_hermitian(30, "gue", generator)
    spacing = mean_level_spacing(np.linalg.eigvalsh(hamiltonian))
    eigenvalues = perturbed_spectrum(hamiltonian, perturbation, 0.5, spacing)
    assert eigenvalues.size == 30
    assert np.all(np.diff(eigenvalues) >= 0.0)


def test_the_curve_degrades_as_the_symmetry_breaks(model):
    curve = degradation_curve(
        g_values=(0.0, 0.2, 0.5, 1.0),
        n_sectors=2,
        levels_per_sector=120,
        draws=6,
        model=model,
        seed=3,
    )
    first, last = curve.rows[0], curve.rows[-1]
    assert first.mean_r < last.mean_r
    assert first.flag_rate > last.flag_rate
    assert first.accuracy > last.accuracy
    assert curve.critical_g is not None
    assert "critical g" in curve.summary()


def test_the_curve_reports_its_thresholds(model):
    curve = degradation_curve(
        g_values=(0.0, 1.0),
        levels_per_sector=120,
        draws=3,
        model=model,
        accuracy_threshold=0.4,
        coverage_threshold=0.7,
        seed=4,
    )
    assert curve.accuracy_threshold == 0.4
    assert curve.coverage_threshold == 0.7
    assert curve.true_count == 2


def test_validation():
    with pytest.raises(ValueError, match="two sectors"):
        degradation_curve(n_sectors=3)
    with pytest.raises(ValueError, match="non-negative"):
        degradation_curve(g_values=(-0.1,))
    with pytest.raises(ValueError, match="at least two draws"):
        degradation_curve(draws=1)
    with pytest.raises(ValueError, match="at least three levels"):
        mean_level_spacing(np.array([0.0, 1.0]))
    with pytest.raises(ValueError, match="matrix_class"):
        random_hermitian(4, "symplectic")
    with pytest.raises(ValueError, match="shape"):
        perturbed_spectrum(np.eye(4), np.eye(3), 0.1, 1.0)
