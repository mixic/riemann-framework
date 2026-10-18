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
"""Tests for the chirality invariants, and for the non-claim they carry."""

from __future__ import annotations

import mpmath as mp
import pytest

from riemann_framework.chirality import (
    NO_RH_EVIDENCE,
    cayley_dickson_anti_automorphism,
    cayley_dickson_is_commutative,
    chi_minus_four,
    chirality_report,
    completed_beta,
    davenport_heilbronn_report,
    dh_functional_equation_residual,
    dh_multiplicativity_report,
    dh_zero_scan,
    dirichlet_beta,
    functional_equation_residual,
    gaussian_census,
    gaussian_prime_class,
    gaussian_representation,
    lens_census,
    orientation_reversing_q,
    parity_check,
)


# ============================================================
# Gaussian primes: splitting is the mirror pair
# ============================================================

def test_prime_classes_are_the_three_cases():
    assert gaussian_prime_class(2) == "ramified"
    assert gaussian_prime_class(5) == "split"
    assert gaussian_prime_class(13) == "split"
    assert gaussian_prime_class(3) == "inert"
    assert gaussian_prime_class(7) == "inert"


def test_split_primes_have_a_mirror_representation():
    """`p = a^2 + b^2`: the pair `a +- b i` is the mirror pair."""
    assert gaussian_representation(5) in ((1, 2), (2, 1))
    assert gaussian_representation(13) in ((2, 3), (3, 2))
    for p in (5, 13, 17, 29, 37):
        representation = gaussian_representation(p)
        assert representation is not None, p
        a, b = representation
        assert a * a + b * b == p


def test_inert_primes_have_none():
    for p in (3, 7, 11, 19, 23):
        assert gaussian_representation(p) is None


def test_census_counts_and_verifies_the_representation():
    census = gaussian_census(400)
    assert census.split == 37
    assert census.inert == 40
    assert census.ramified == 1
    assert census.all_split_prime_represented
    assert census.no_inert_prime_represented
    assert "mirrored" in census.summary()


def test_gaussian_helpers_validate():
    with pytest.raises(ValueError):
        gaussian_prime_class(1)
    with pytest.raises(ValueError):
        gaussian_prime_class(4)  # not prime
    with pytest.raises(ValueError):
        gaussian_census(5)


# ============================================================
# Lens spaces: the same condition in topology
# ============================================================

def test_orientation_reversing_element_exists_exactly_for_split_primes():
    """`q^2 = -1 mod p` iff `p = 2` or `p = 1 mod 4`."""
    assert orientation_reversing_q(5) in (2, 3)
    assert orientation_reversing_q(13) in (5, 8)
    assert orientation_reversing_q(3) is None
    assert orientation_reversing_q(7) is None
    assert orientation_reversing_q(2) == 1


def test_lens_census_agrees_with_the_arithmetic_prediction():
    census = lens_census(200)
    assert census.achiral == 22
    assert census.chiral == 24
    assert census.matches_split_criterion
    assert "orientation-reversing" in census.summary()


# ============================================================
# chi_-4 is odd
# ============================================================

def test_chi_minus_four_values():
    assert [chi_minus_four(n) for n in range(8)] == [0, 1, 0, -1, 0, 1, 0, -1]


def test_beta_at_one_and_zero():
    """Independent checks that the function is the one intended."""
    assert dirichlet_beta(1) == pytest.approx(mp.pi / 4)
    assert dirichlet_beta(0) == pytest.approx(mp.mpf(1) / 2)


def test_the_functional_equation_holds_with_the_odd_archimedean_factor():
    """`Gamma((s+1)/2)` works and `Gamma(s/2)` does not: the character is odd."""
    check = parity_check()
    assert max(check.odd_residuals) < 1e-12
    assert max(check.even_residuals) > 1e-2
    assert check.parity_detected
    assert check.ratio > 1e10
    assert functional_equation_residual(0.3 + 2.0j, 1) < 1e-12
    assert functional_equation_residual(0.3 + 2.0j, 0) > 1e-2


def test_the_completed_beta_function_is_the_right_combination():
    """`Lambda(1)` and `Lambda(0)` agree, which pins the normalisation."""
    assert completed_beta(1) == pytest.approx(completed_beta(0), rel=1e-12)


# ============================================================
# Cayley-Dickson conjugation
# ============================================================

def test_conjugation_reverses_products_in_dims_2_4_8_16():
    """`conj(xy) = conj(y) conj(x)` even where associativity has failed."""
    errors = cayley_dickson_anti_automorphism()
    assert set(errors) == {2, 4, 8, 16}
    for dimension, error in errors.items():
        assert error < 1e-12, dimension


def test_the_anti_automorphism_test_is_not_vacuous():
    """Commutativity fails from dimension 4 on, so the algebras are non-trivial."""
    assert cayley_dickson_is_commutative(2)
    assert not cayley_dickson_is_commutative(4)
    assert not cayley_dickson_is_commutative(8)


# ============================================================
# Davenport-Heilbronn: functional equation without an Euler product
# ============================================================

def test_the_dh_functional_equation_holds():
    assert dh_functional_equation_residual(0.3 + 2.0j) < 1e-12


def test_the_dh_euler_product_fails_with_a_specific_defect():
    """`b(2) b(3) = -kappa^2`, not `b(6)`: a structured failure, not rounding."""
    report = dh_multiplicativity_report()
    assert report["difference"] > 0.5
    assert report["matches_minus_kappa_squared"] < 1e-12


def test_the_dh_zero_scan_reports_only_on_line_nontrivial_zeros():
    """The honest negative: this bounded search locates no off-line zero.

    The literature's off-line zeros are therefore NOT reproduced here, and the
    module does not claim them. What is demonstrated is the structural failure.
    """
    rows = dh_zero_scan()
    assert rows, "the scan should locate at least the first zeros"
    off_line = [row for row in rows if abs(row[0] - 0.5) > 1e-6]
    # the only non-critical-line zero found is the trivial one at s = -1
    assert all(abs(row[0] + 1.0) < 1e-6 for row in off_line)


def test_the_dh_report_states_both_halves():
    report = davenport_heilbronn_report()
    assert report.euler_product_fails
    assert report.functional_equation_residual < 1e-12
    text = report.summary()
    assert "holds" in text and "fails" in text
    assert len(report.off_line_zeros) == len(
        [row for row in report.zeros if abs(row[0] - 0.5) > 1e-6]
    )


# ============================================================
# The report and its non-claim
# ============================================================

def test_the_report_runs_and_states_the_non_claim():
    report = chirality_report(limit=200)
    verdict = report.verdict()
    assert "no new evidence" in verdict.lower()
    assert report.gaussian.split > 0
    assert report.lens.matches_split_criterion
    assert report.parity.parity_detected


def test_the_non_claim_is_stated_where_the_numbers_are():
    assert "no new evidence" in NO_RH_EVIDENCE.lower()
    assert "Riemann hypothesis" in NO_RH_EVIDENCE
