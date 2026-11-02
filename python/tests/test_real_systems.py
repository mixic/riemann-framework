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
"""Tests for the real-system validation.

The construction is pinned exactly: the commutators are checked by the code itself, the
splits are checked by dimension, and the statistics are pinned with a direction plus a
margin, because a single real spectrum is one sample. The numbers of record are in
`output/real_systems.csv` and `docs/real_systems.md`.

One test here is a regression for a defect this goal found: `detect_hidden_symmetry`
returned a NaN mean on a spectrum with exact degeneracies, because a zero spacing gave
`0 / 0`. The free Ising chain is such a spectrum, which is how the defect surfaced.
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.desymmetrisation import detect_hidden_symmetry
from riemann_framework.real_systems import (
    GOE_MEAN_RATIO,
    GUE_MEAN_RATIO,
    POISSON_MEAN_RATIO,
    analyse_floquet,
    analyse_hamiltonian,
    fixed_magnetisation_basis,
    heisenberg_chain,
    heisenberg_system,
    kicked_top,
    kicked_top_system,
    mean_ratio,
    ratios_from_spacings,
    tfim_chain,
    tfim_system,
)


def test_the_reference_values_match_the_manuscript():
    assert (POISSON_MEAN_RATIO, GOE_MEAN_RATIO, GUE_MEAN_RATIO) == (0.386, 0.531, 0.600)


def test_the_ising_parity_commutes_exactly():
    hamiltonian, parity = tfim_chain(6)
    assert np.abs(hamiltonian @ parity - parity @ hamiltonian).max() < 1e-12
    assert np.abs(parity @ parity - np.eye(parity.shape[0])).max() < 1e-12


def test_the_ising_parity_commutes_with_next_neighbour_coupling():
    """The interaction that breaks integrability is even in the spins, so it keeps P."""
    hamiltonian, parity = tfim_chain(6, next_neighbour=0.3)
    assert np.abs(hamiltonian @ parity - parity @ hamiltonian).max() < 1e-12


def test_the_free_ising_spectrum_has_exact_degeneracies():
    """The reason the NaN defect existed: a real spectrum is not a Gaussian block."""
    hamiltonian, _ = tfim_chain(6)
    energies = np.linalg.eigvalsh(hamiltonian)
    spacings = np.diff(energies)
    assert int((spacings < 1e-12).sum()) > 0


def test_degenerate_spacings_are_dropped_not_counted_as_zero():
    """The convention: a zero spacing never enters a ratio, so no 0/x is formed."""
    spectrum = np.array([0.0, 1.0, 1.0, 2.0, 3.0, 5.0])
    assert mean_ratio(spectrum) == pytest.approx((1.0 + 1.0 + 0.5) / 3.0)


def test_the_detector_survives_a_degenerate_real_spectrum():
    """Regression: the free Ising chain used to give a NaN mean and a bogus flag."""
    spectra = tfim_system(6)
    verdict = detect_hidden_symmetry(spectra.full)
    assert np.isfinite(verdict.full_mean_r)
    assert verdict.full_mean_r == pytest.approx(mean_ratio(spectra.full))


def test_a_non_commuting_involution_is_rejected():
    hamiltonian, _ = tfim_chain(4)
    rng = np.random.default_rng(0)
    raw = rng.standard_normal((16, 16))
    bogus = (raw + raw.T) / 2.0
    with pytest.raises(ValueError, match="does not commute"):
        analyse_hamiltonian("bogus", hamiltonian, bogus)


def test_a_non_unitary_floquet_operator_is_rejected():
    _, parity = kicked_top(3)
    rng = np.random.default_rng(0)
    raw = rng.standard_normal((7, 7))
    with pytest.raises(ValueError, match="not unitary"):
        analyse_floquet("bogus", (raw + raw.T) / 2.0, parity)


def test_an_odd_chain_has_no_zero_magnetisation_sector():
    with pytest.raises(ValueError, match="even number of sites"):
        fixed_magnetisation_basis(5)


def test_the_heisenberg_parity_is_the_complement_and_a_permutation():
    _, parity = heisenberg_chain(6)
    assert parity.shape == (20, 20)
    assert np.abs(parity @ parity - np.eye(20)).max() < 1e-12
    assert set(np.unique(parity)) <= {0.0, 1.0}
    assert np.allclose(parity.sum(axis=0), 1.0)


def test_the_heisenberg_split_is_two_equal_sectors():
    spectra = heisenberg_system(6)
    assert [sector.size for sector in spectra.sectors] == [10, 10]
    assert spectra.commutator < 1e-12


def test_the_kicked_top_is_unitary_and_commutes_with_its_parity():
    unitary, parity = kicked_top(10, kick=4.0, precession=2.0)
    identity = np.eye(unitary.shape[0])
    assert np.abs(unitary.conj().T @ unitary - identity).max() < 1e-12
    assert np.abs(unitary @ parity - parity @ unitary).max() < 1e-11


def test_the_kicked_top_phases_live_on_the_circle():
    spectra = kicked_top_system(20, kick=4.0, precession=2.0)
    assert spectra.full.size == 41
    assert spectra.full.min() >= 0.0 and spectra.full.max() < 2.0 * np.pi
    assert sum(sector.size for sector in spectra.sectors) == 41


def test_circular_ratios_use_every_spacing():
    spacings = np.array([1.0, 2.0, 4.0, 8.0])
    assert ratios_from_spacings(spacings).size == 3
    assert ratios_from_spacings(spacings, circular=True).size == 4


def test_the_kicked_top_split_raises_the_statistic():
    """A real Floquet spectrum: the union sits below both parity sectors."""
    spectra = kicked_top_system(20, kick=4.0, precession=2.0)
    assert spectra.split_raises_the_statistic
    assert spectra.full_mean < min(spectra.sector_means) - 0.05


def test_the_free_ising_parity_sectors_are_above_the_full_spectrum():
    spectra = tfim_system(8)
    assert spectra.split_raises_the_statistic
    assert spectra.full_mean < min(spectra.sector_means)


def test_the_chaotic_heisenberg_split_raises_the_statistic():
    spectra = heisenberg_system(10, next_neighbour=0.5, disorder=0.3)
    assert spectra.split_raises_the_statistic
    assert spectra.full_mean < min(spectra.sector_means)


def test_the_summary_reports_both_views():
    spectra = kicked_top_system(20, kick=4.0, precession=2.0)
    text = spectra.summary()
    assert "full" in text and "sectors" in text
    assert "[H,P]" in text
