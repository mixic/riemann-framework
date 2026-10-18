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
"""Tests for the corrected dimension-shift chaos model.

The first two tests are the correction itself: the model must commute with
`sigma` and must be usable in both symmetry classes. The rest pin the
consequences -- the sectors are `A +- C`, the full spectrum is a superposition,
and the class is inherited rather than produced.
"""

from __future__ import annotations

from typing import cast

import numpy as np
import pytest

from riemann_framework.dimension_shift_chaos import (
    MATRIX_CLASSES,
    SIGMA_TOLERANCE,
    analyze_dimension_shift,
    build_dimension_shift_hamiltonian,
    compare_to_riemann,
    desymmetrise,
    is_sigma_symmetric,
    sector_spectra,
    sector_swap,
    sigma_commutator_ratio,
    sigma_control,
    sigma_sector_basis,
    sweep_coupling,
    sweep_matrix_class,
)


# ============================================================
# The correction: sigma is a symmetry
# ============================================================

def test_sigma_is_an_involution_and_hermitian():
    sigma = sector_swap(5)
    assert np.allclose(sigma @ sigma, np.eye(10))
    assert np.allclose(sigma, sigma.conj().T)


def test_the_hamiltonian_commutes_with_sigma_exactly():
    """The pre-correction model measured `1.346 .. 1.462`; it must be `0`."""
    for dimension in (5, 10, 20):
        for coupling in (0.0, 0.5, 2.0):
            for matrix_class in MATRIX_CLASSES:
                hamiltonian = build_dimension_shift_hamiltonian(
                    dimension, coupling, matrix_class, seed=1
                )
                ratio = sigma_commutator_ratio(hamiltonian)
                assert ratio < SIGMA_TOLERANCE, (dimension, coupling, matrix_class)
                assert is_sigma_symmetric(hamiltonian)


def test_the_hamiltonian_is_hermitian_in_both_classes():
    for matrix_class in MATRIX_CLASSES:
        hamiltonian = build_dimension_shift_hamiltonian(6, 1.0, matrix_class, seed=2)
        assert np.allclose(hamiltonian, hamiltonian.conj().T)


def test_gue_blocks_are_genuinely_complex_and_goe_blocks_are_real():
    gue = build_dimension_shift_hamiltonian(6, 1.0, "gue", seed=3)
    goe = build_dimension_shift_hamiltonian(6, 1.0, "goe", seed=3)
    assert np.abs(np.imag(gue)).max() > 0.1
    assert np.abs(np.imag(goe)).max() == 0.0


def test_the_sigma_breaking_control_does_break_the_symmetry():
    """Requirement 1 violated on purpose, and measurably."""
    hamiltonian = build_dimension_shift_hamiltonian(
        10, 1.0, "gue", seed=4, sigma_breaking=0.5
    )
    assert sigma_commutator_ratio(hamiltonian) > 1e-3
    assert not is_sigma_symmetric(hamiltonian)


def test_validate_arguments():
    with pytest.raises(ValueError):
        build_dimension_shift_hamiltonian(1)
    with pytest.raises(ValueError):
        build_dimension_shift_hamiltonian(5, coupling=-1.0)
    with pytest.raises(ValueError):
        build_dimension_shift_hamiltonian(5, sigma_breaking=-0.1)
    with pytest.raises(ValueError):
        build_dimension_shift_hamiltonian(5, matrix_class="poisson")
    with pytest.raises(TypeError):
        build_dimension_shift_hamiltonian(cast(int, 5.0))


# ============================================================
# Desymmetrisation
# ============================================================

def test_the_sector_basis_is_orthonormal_and_diagonalises_sigma():
    basis = sigma_sector_basis(4)
    assert np.allclose(basis.conj().T @ basis, np.eye(8))
    transformed = basis.conj().T @ sector_swap(4) @ basis
    assert np.allclose(transformed, np.diag([1.0] * 4 + [-1.0] * 4))


def test_the_sector_spectra_are_the_spectra_of_the_blocks():
    """`spec(A + C)` and `spec(A - C)`, verified through the basis change."""
    hamiltonian = build_dimension_shift_hamiltonian(5, 1.0, "gue", seed=5)
    plus, minus = sector_spectra(hamiltonian)
    d = 5
    block_a = hamiltonian[:d, :d]
    block_c = hamiltonian[:d, d:]
    assert np.allclose(plus, np.linalg.eigvalsh(block_a + block_c))
    assert np.allclose(minus, np.linalg.eigvalsh(block_a - block_c))


def test_desymmetrise_refuses_a_model_that_is_not_sigma_symmetric():
    broken = build_dimension_shift_hamiltonian(
        5, 1.0, "gue", seed=6, sigma_breaking=0.5
    )
    with pytest.raises(ValueError, match="not sigma-symmetric"):
        desymmetrise(broken)


# ============================================================
# Statistics: the class is inherited, the full spectrum is mixed
# ============================================================

def test_zero_coupling_is_exactly_degenerate():
    """`coupling = 0` makes every level doubly degenerate, so `r = 0`.

    That is why it is excluded from the verdict grid and kept as a control.
    """
    analysis = analyze_dimension_shift(10, 0.0, "gue", seed=7)
    assert analysis["mean_r_full"] == pytest.approx(0.0, abs=1e-12)


def test_the_full_spectrum_is_never_gue():
    """A superposition of two sectors lands near 0.42 for both classes."""
    for matrix_class in MATRIX_CLASSES:
        values = [
            analyze_dimension_shift(20, coupling, matrix_class, seed=8)["mean_r_full"]
            for coupling in (0.5, 1.0, 2.0)
        ]
        for value in values:
            assert value < 0.55, (matrix_class, values)


def test_the_sector_class_follows_the_block_class():
    """GUE blocks give a GUE sector; GOE blocks give a GOE sector.

    This is why the model cannot be evidence for GUE statistics: it imports them.
    """
    means = {}
    for matrix_class in MATRIX_CLASSES:
        values = [
            analyze_dimension_shift(20, 1.0, matrix_class, seed=seed)["mean_r_plus"]
            for seed in range(12)
        ]
        means[matrix_class] = float(np.mean(values))
    assert means["gue"] > 0.56
    assert means["goe"] < 0.55
    assert means["gue"] - means["goe"] > 0.03


def test_the_analysis_reports_the_sigma_ratio_and_sectors():
    analysis = analyze_dimension_shift(10, 1.0, "gue", seed=9)
    assert analysis["sigma_symmetric"]
    assert analysis["sigma_commutator_ratio"] < SIGMA_TOLERANCE
    assert analysis["sector_plus"] is not None
    assert len(analysis["sector_plus"]) == 10
    assert analysis["mean_r_full"] != analysis["mean_r_plus"]


def test_a_broken_control_reports_no_sectors():
    analysis = analyze_dimension_shift(10, 1.0, "gue", seed=10, sigma_breaking=0.5)
    assert not analysis["sigma_symmetric"]
    assert analysis["sector_plus"] is None
    assert np.isnan(analysis["mean_r_plus"])


# ============================================================
# Sweeps and comparison
# ============================================================

def test_sweep_coupling_and_matrix_class_run():
    rows = sweep_coupling(10, coupling_values=[0.5, 1.0], matrix_class="gue", seed=11)
    assert len(rows) == 2
    assert all(row["sigma_symmetric"] for row in rows)
    classes = sweep_matrix_class(10, seed=11)
    assert [row["matrix_class"] for row in classes] == list(MATRIX_CLASSES)


def test_sigma_control_reports_the_violation():
    rows = sigma_control(10, seed=12)
    assert rows[0]["sigma_symmetric"]
    assert not rows[-1]["sigma_symmetric"]
    assert rows[-1]["sigma_commutator_ratio"] > rows[0]["sigma_commutator_ratio"]


def test_compare_to_riemann_runs_and_names_the_class():
    comparison = compare_to_riemann(10, seed=13, n_riemann=20)
    assert comparison["model"]["matrix_class"] == "gue"
    assert 0.0 <= comparison["model"]["mean_r_full"] <= 1.0
    assert comparison["reference_values"]["gue"] == 0.599
