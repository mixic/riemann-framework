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
"""Tests for the one-call diagnostic.

The two rules the module claims to enforce are tested directly: a rejected involution is
reported and *not* used, and every conclusion carries its number. The remaining tests pin
the dispatch, the input validation, and the two spectra that must come out with opposite
verdicts (a two-sector union and a single block).
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.boundary_map import build_spectrum
from riemann_framework.diagnose import (
    MIN_LEVELS,
    REFERENCE,
    diagnose,
    diagnose_matrix,
    diagnose_spectrum,
)
from riemann_framework.real_systems import tfim_chain


def _goe_block(dimension: int = 240, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    raw = rng.standard_normal((dimension, dimension))
    return np.linalg.eigvalsh((raw + raw.T) / 2.0)


def test_a_verified_involution_is_split():
    hamiltonian, parity = tfim_chain(5)
    report = diagnose_matrix(hamiltonian, [parity], title="TFIM n=5")
    assert report.symmetries_verified == 1
    assert report.sector_sizes == (16, 16)
    assert report.checks[0].commutator < 1e-12


def test_a_rejected_involution_is_reported_not_used():
    """The rule that matters: a non-symmetry is named and excluded, never acted on."""
    hamiltonian, _ = tfim_chain(4)
    rng = np.random.default_rng(0)
    raw = rng.standard_normal((16, 16))
    report = diagnose_matrix(hamiltonian, [(raw + raw.T) / 2.0])
    assert report.symmetries_verified == 0
    assert report.checks[0].verified is False
    assert report.checks[0].commutator > 1e-8
    assert report.sector_means == ()
    assert any("no sector statistic" in line for line in report.conclusions)


def test_the_report_flags_a_contaminated_full_spectrum():
    hamiltonian, parity = tfim_chain(5)
    report = diagnose_matrix(hamiltonian, [parity])
    assert report.full_verdict is not None
    assert report.full_verdict.is_contaminated
    assert any("flags the full spectrum" in line for line in report.conclusions)


def test_the_report_states_that_the_full_spectrum_is_below_every_sector():
    hamiltonian, parity = tfim_chain(5)
    report = diagnose_matrix(hamiltonian, [parity])
    assert report.full_below_every_sector
    assert any("below every sector" in line for line in report.conclusions)


def test_a_single_goe_block_is_cleared_and_counted_once():
    report = diagnose_spectrum(_goe_block(), title="one GOE block")
    assert report.full_verdict is not None
    assert not report.full_verdict.is_contaminated
    assert report.count_estimate is not None
    assert report.count_estimate.map_label == 1
    assert any("clears the full spectrum" in line for line in report.conclusions)


def test_a_two_sector_union_is_counted_as_two():
    """The synthetic case the manuscript's posterior was built for."""
    report = diagnose_spectrum(build_spectrum(2, 240, seed=3), title="two sectors")
    assert report.count_estimate is not None
    assert report.count_estimate.map_label == 2


def test_a_deep_superposition_states_the_poisson_ambiguity():
    """A spectrum whose ratios sit below Poisson: the honest limit must be printed."""
    rng = np.random.default_rng(0)
    base = np.sort(rng.random(120))
    clustered = np.sort(np.concatenate([base, base + 0.001]))
    report = diagnose_spectrum(clustered, title="near-degenerate pairs")
    assert report.full_mean < REFERENCE["Poisson"]
    assert any("Poisson" in line and "integrable" in line for line in report.conclusions)


def test_the_spectrum_path_has_no_symmetry_checks():
    report = diagnose_spectrum(_goe_block(), title="spectrum")
    assert report.checks == ()
    assert report.sector_means == ()
    assert report.symmetries_verified == 0


def test_both_inputs_are_rejected():
    with pytest.raises(ValueError, match="not both"):
        diagnose(eigenvalues=_goe_block(16), matrix=np.eye(MIN_LEVELS))


def test_no_input_is_rejected():
    with pytest.raises(ValueError, match="give a matrix"):
        diagnose()


def test_a_short_spectrum_is_rejected():
    with pytest.raises(ValueError, match=f"at least {MIN_LEVELS}"):
        diagnose_spectrum(np.arange(4.0))


def test_a_degenerate_spectrum_is_rejected():
    with pytest.raises(ValueError, match="degenerate"):
        diagnose_spectrum(np.ones(12))


def test_a_non_symmetric_matrix_is_rejected():
    rng = np.random.default_rng(0)
    with pytest.raises(ValueError, match="not symmetric"):
        diagnose_matrix(rng.standard_normal((16, 16)), [])


def test_the_count_appears_once_in_the_summary():
    """Two ways to report the same posterior is one way to read it wrong."""
    hamiltonian, parity = tfim_chain(5)
    text = diagnose_matrix(hamiltonian, [parity]).summary()
    assert text.count("count posterior") == 1


def test_the_summary_names_the_symmetry_checks():
    hamiltonian, parity = tfim_chain(5)
    text = diagnose_matrix(hamiltonian, [parity]).summary()
    assert "P1: verified" in text
