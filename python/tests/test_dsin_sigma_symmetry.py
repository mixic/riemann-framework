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
"""Tests for the DSIN parity-sector analysis.

The three positive claims (sectors, conservation, leakage) are easy. The test that
matters is the fourth: a parity-conserving channel makes the parity meter blind,
so the attack that measures the encoding basis is invisible. A suite that only
confirmed conservation would have missed the security-relevant half.
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.dsin import build_sigma, encode_bit
from riemann_framework.dsin_sigma_symmetry import (
    breaking_hamiltonian,
    breaking_vs_leakage,
    commutator_ratio,
    detection_vs_breaking,
    max_parity_drift,
    parity_conservation,
    parity_report,
    parity_sector_bases,
    sector_check,
    sector_weights,
    sigma_basis_attack_report,
)


# ============================================================
# 1. The sectors
# ============================================================

def test_the_plus_sector_is_symmetric_and_the_minus_sector_antisymmetric():
    check = sector_check(4)
    assert check.plus_is_symmetric
    assert check.minus_is_antisymmetric
    assert check.bases_are_orthonormal
    assert check.diagonalises_sigma < 1e-12


def test_the_bases_diagonalise_sigma_with_the_expected_signs():
    d = 3
    sigma = build_sigma(d)
    plus, minus = parity_sector_bases(d)
    for k in range(d):
        assert np.allclose(sigma @ plus[:, k], plus[:, k])
        assert np.allclose(sigma @ minus[:, k], -minus[:, k])


def test_the_encoded_bits_lie_in_pure_sectors():
    """Bit 0 is entirely in `Fix(sigma)`, bit 1 entirely in `Anti(sigma)`."""
    for bit, expected in ((0, (1.0, 0.0)), (1, (0.0, 1.0))):
        state = encode_bit(bit, 4)
        assert sector_weights(state.vector, 4) == pytest.approx(expected, abs=1e-12)


def test_sector_bases_validate_the_dimension():
    with pytest.raises(ValueError):
        parity_sector_bases(1)


# ============================================================
# 2. Conservation under the symmetric channel
# ============================================================

def test_the_channel_commutes_with_sigma():
    hamiltonian = breaking_hamiltonian(4, coupling=1.0, strength=0.0, seed=0)
    assert commutator_ratio(hamiltonian) < 1e-12


def test_sector_parity_is_conserved_at_every_time():
    """`[H, sigma] = 0` implies `<sigma>` is constant: drift < 1e-12 over the grid."""
    rows = parity_conservation(dim_per_sector=4, seed=0)
    assert max_parity_drift(rows) < 1e-12
    assert all(abs(row.expectation - 1.0) < 1e-12 for row in rows)


def test_both_encoded_bits_are_protected():
    for bit in (0, 1):
        rows = parity_conservation(dim_per_sector=4, bit=bit, seed=0)
        assert max_parity_drift(rows) < 1e-12


def test_a_broken_hamiltonian_leaks_parity_monotonically():
    """Leakage and the commutator both grow with the breaking strength."""
    rows = breaking_vs_leakage(dim_per_sector=4)
    strengths = [row[0] for row in rows]
    ratios = [row[1] for row in rows]
    drifts = [row[2] for row in rows]
    assert strengths[0] == 0.0 and drifts[0] == pytest.approx(0.0, abs=1e-12)
    assert ratios == sorted(ratios)
    assert drifts == sorted(drifts)
    assert drifts[-1] > 0.1


# ============================================================
# 3. What the parity meter can see
# ============================================================

def test_detection_rises_with_symmetry_violation():
    rows = detection_vs_breaking(dim_per_sector=4, seed=0)
    rates = [row.detection_rate for row in rows]
    assert rates[0] == pytest.approx(0.0)
    assert rates == sorted(rates)
    assert rates[-1] > 0.9
    assert rows[-1].mean_abs_deviation > rows[0].mean_abs_deviation


def test_the_sigma_basis_attack_is_undetectable_and_correct():
    """**The finding.** Detection 0, BER 0, one full bit: the meter is blind.

    This is the same conjunction the communication documentation records, now
    derived from the parity structure: the attack commutes with `sigma`, so it
    preserves exactly the observable that is supposed to expose it.
    """
    report = sigma_basis_attack_report(dim_per_sector=4, seed=0)
    assert report.detection_rate == pytest.approx(0.0)
    assert report.bit_error_rate == pytest.approx(0.0)
    assert report.information == pytest.approx(1.0)
    assert "blind" in report.summary() or "blinds" in report.summary()


# ============================================================
# 4. The report
# ============================================================

def test_the_report_states_protection_and_its_cost():
    report = parity_report(dim_per_sector=4, seed=0)
    verdict = report.verdict()
    assert "verified" in verdict
    assert "blindness" in verdict
    assert "No RH evidence" in verdict
    assert report.conservation_drift < 1e-12
    assert report.broken_leakage > 0.1


def test_the_report_is_deterministic_for_a_fixed_seed():
    first = parity_report(dim_per_sector=4, seed=3).verdict()
    second = parity_report(dim_per_sector=4, seed=3).verdict()
    assert first == second
