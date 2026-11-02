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
"""Tests for the PT-symmetric measurements.

The dimer is pinned exactly, because its eigenvalues have a closed form and the
exceptional point is a precise statement. The ensemble results are pinned with a direction
and a margin: the claim is that a random real PT spectrum is generically broken and that
the ratio of its real parts falls toward Poisson as the imaginary parts grow, not that any
number lands on a third decimal. The numbers of record are in
`output/pt_symmetric.csv` and `docs/pt_symmetric_statistics.md`.
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.pt_symmetric_statistics import (
    DEFAULT_ANTISYMMETRIES,
    GOE_MEAN_RATIO,
    POISSON_MEAN_RATIO,
    REFERENCE,
    dimer_eigenvalues,
    dimer_table,
    ensemble_table,
    imaginary_over_spacing,
    is_hermitian,
    is_unbroken,
    pairing_defect,
    pt_dimer,
    pt_random,
    real_part_ratio,
)
from riemann_framework.real_systems import analyse_hamiltonian


def test_the_dimer_is_real_below_the_exceptional_point():
    values = dimer_eigenvalues(0.5, coupling=1.0)
    assert np.all(values.imag == 0.0)
    assert values.real == pytest.approx([-np.sqrt(0.75), np.sqrt(0.75)])


def test_the_dimer_is_a_conjugate_pair_above_it():
    values = dimer_eigenvalues(1.5, coupling=1.0)
    assert np.allclose(values.real, 0.0)
    assert values.imag == pytest.approx([-np.sqrt(1.25), np.sqrt(1.25)])


def test_the_dimer_closed_form_matches_the_matrix():
    matrix = pt_dimer(gamma=0.7, coupling=1.3, level=0.4)
    values = np.linalg.eigvals(matrix)
    values = values[np.lexsort((values.imag, values.real))]
    assert np.allclose(values, dimer_eigenvalues(0.7, coupling=1.3, level=0.4))


def test_the_dimer_collides_at_the_exceptional_point():
    values = dimer_eigenvalues(1.0, coupling=1.0)
    assert np.allclose(values, 0.0)


def test_the_dimer_table_marks_the_transition():
    rows = dimer_table()
    assert rows[0].unbroken
    assert not rows[-1].unbroken
    transitions = [row.unbroken for row in rows]
    assert transitions != sorted(transitions), "the dimer never breaks"


def test_a_random_pt_matrix_is_real_and_not_hermitian():
    matrix = pt_random(20, 0.3, seed=0)
    assert np.abs(matrix.imag).max() == 0.0
    assert not is_hermitian(matrix)
    assert is_hermitian(pt_random(20, 0.0, seed=0))


def test_the_hermitian_end_is_goe_like():
    ratio = np.mean(
        [
            real_part_ratio(np.linalg.eigvals(pt_random(60, 0.0, seed=index)))
            for index in range(8)
        ]
    )
    assert ratio == pytest.approx(GOE_MEAN_RATIO, abs=0.05)


def test_a_random_pt_spectrum_is_generically_broken():
    """Any non-zero antisymmetry breaks it: the unbroken phase needs structure."""
    broken = 0
    for index in range(12):
        eigenvalues = np.linalg.eigvals(pt_random(40, 0.2, seed=index))
        broken += not is_unbroken(eigenvalues)
    assert broken == 12


def test_the_pairing_defect_is_zero_even_when_broken():
    """The anti-linear symmetry is exact; it is the linear split that does not exist."""
    eigenvalues = np.linalg.eigvals(pt_random(40, 0.5, seed=3))
    assert not is_unbroken(eigenvalues)
    assert pairing_defect(eigenvalues) < 1e-9


def test_the_imaginary_part_grows_past_the_spacing():
    weak = np.mean(
        [
            imaginary_over_spacing(np.linalg.eigvals(pt_random(60, 0.2, seed=index)))
            for index in range(6)
        ]
    )
    strong = np.mean(
        [
            imaginary_over_spacing(np.linalg.eigvals(pt_random(60, 1.0, seed=index)))
            for index in range(6)
        ]
    )
    assert weak < 1.5
    assert strong > 5.0
    assert strong > weak


def test_the_real_part_ratio_falls_toward_poisson():
    weak = np.mean(
        [
            real_part_ratio(np.linalg.eigvals(pt_random(60, 0.2, seed=index)))
            for index in range(6)
        ]
    )
    strong = np.mean(
        [
            real_part_ratio(np.linalg.eigvals(pt_random(60, 1.0, seed=index)))
            for index in range(6)
        ]
    )
    assert weak > strong + 0.05
    assert strong < GOE_MEAN_RATIO - 0.05
    assert POISSON_MEAN_RATIO - 0.05 < strong


def test_the_sector_machinery_refuses_a_pt_spectrum():
    """The punchline, as a test: the analysis raises before it can mislead."""
    matrix = pt_random(20, 0.3, seed=0)
    with pytest.raises(ValueError, match="not symmetric"):
        analyse_hamiltonian("PT ensemble", matrix, np.eye(20))


def test_the_ensemble_table_covers_the_sweep():
    rows = ensemble_table(dimension=40, seeds=6)
    assert len(rows) == len(DEFAULT_ANTISYMMETRIES)
    assert [row.antisymmetry for row in rows] == list(DEFAULT_ANTISYMMETRIES)
    assert rows[0].unbroken_fraction == 1.0
    for row in rows[1:]:
        # At this small dimension the weakest antisymmetry still leaves some spectra
        # unbroken; the report's dimension (120) gives zero for every non-zero w. What
        # holds at both sizes is that the unbroken phase disappears as w grows.
        assert row.unbroken_fraction < 1.0
        assert row.pairing_defect < 1e-9
    assert all(row.unbroken_fraction == 0.0 for row in rows[3:])
    assert REFERENCE["Poisson"] == POISSON_MEAN_RATIO
