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
"""Tests for the desymmetrisation utility and the contamination warning.

The table these are pinned to was measured independently:

    unresolved independent sectors   GOE      GUE
    1                                0.52     0.59
    2                                0.43     0.42
    3 or more                        0.38-0.40

and the two limits are part of the test suite, not just the docstring: the sector
count cannot be estimated from `⟨r⟩`, and at two sectors the class information is
gone. A suite that only checked splitting would have missed both.
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.desymmetrisation import (
    CLASS_SHIFT_THRESHOLD,
    COUNT_LABELS,
    MULTI_SECTOR_CEILING,
    R_GOE,
    R_GUE,
    R_POISSON,
    SINGLE_SECTOR_FLOOR,
    TWO_SECTOR_BAND,
    CalibrationRow,
    CoverageRow,
    DesymmetrisedReport,
    SectorCountEstimate,
    SectorCountModel,
    SpectrumStatistics,
    _synthetic_spectrum,
    calibration_table,
    class_information_at_two_sectors,
    classify_mean,
    commutator_ratio,
    contamination_warning,
    contamination_warnings,
    default_sector_count_model,
    desymmetrise,
    detect_hidden_symmetry,
    estimate_sector_count,
    estimate_sectors_from_mean,
    is_involution,
    sector_count_posterior,
    sector_spectra,
    sector_blocks,
    superposition_spectrum,
)
from riemann_framework.dimension_shift_chaos import (
    build_dimension_shift_hamiltonian,
    sector_swap,
)


# ============================================================
# Commutation, involution, splitting
# ============================================================

def test_an_involution_is_recognised_and_a_general_matrix_is_not():
    swap = sector_swap(4)
    assert is_involution(swap)
    assert not is_involution(np.array([[1.0, 2.0], [0.0, 1.0]]))
    assert not is_involution(np.ones((3, 2)))


def test_the_commutator_ratio_is_zero_for_a_symmetry_and_one_for_a_swap_that_fails():
    """The pre-correction dimension-shift model measured `1.35…1.46` here."""
    sigma = sector_swap(10)
    symmetric = build_dimension_shift_hamiltonian(10, 1.0, "gue", seed=0)
    assert commutator_ratio(symmetric, sigma) < 1e-12
    broken = build_dimension_shift_hamiltonian(10, 1.0, "gue", seed=0, sigma_breaking=0.5)
    assert commutator_ratio(broken, sigma) > 1e-3


def test_the_sectors_of_the_sigma_model_are_spec_a_plus_minus_c():
    """The utility agrees with the arithmetic identity, not just with itself."""
    d = 8
    hamiltonian = build_dimension_shift_hamiltonian(d, 1.0, "gue", seed=1)
    blocks = sector_blocks(hamiltonian, [sector_swap(d)])
    assert len(blocks) == 2
    block_a = hamiltonian[:d, :d]
    block_c = hamiltonian[:d, d:]
    spectra = {signs: np.linalg.eigvalsh(block) for signs, block in blocks.items()}
    assert np.allclose(spectra[(1,)], np.linalg.eigvalsh(block_a + block_c))
    assert np.allclose(spectra[(-1,)], np.linalg.eigvalsh(block_a - block_c))


def test_two_commuting_involutions_give_four_sectors():
    """A `Z_2 x Z_2` splitting, checked against the blocks it was built from."""
    d = 5
    rng = np.random.default_rng(7)
    blocks = []
    for _ in range(4):
        raw = (rng.standard_normal((d, d)) + 1j * rng.standard_normal((d, d))) / np.sqrt(2)
        blocks.append((raw + raw.conj().T) / 2.0)
    # A four-sector direct sum: four blocks of size d, total 4d.
    hamiltonian = np.zeros((4 * d, 4 * d), dtype=complex)
    for index, block in enumerate(blocks):
        hamiltonian[index * d:(index + 1) * d, index * d:(index + 1) * d] = block

    identity = np.eye(d, dtype=complex)
    signs_first = (1, 1, -1, -1)
    signs_second = (1, -1, 1, -1)
    first = np.zeros((4 * d, 4 * d), dtype=complex)
    second = np.zeros((4 * d, 4 * d), dtype=complex)
    for index, (s1, s2) in enumerate(zip(signs_first, signs_second)):
        first[index * d:(index + 1) * d, index * d:(index + 1) * d] = s1 * identity
        second[index * d:(index + 1) * d, index * d:(index + 1) * d] = s2 * identity

    assert is_involution(first) and is_involution(second)
    sectors = sector_blocks(hamiltonian, [first, second])
    assert len(sectors) == 4
    sign_to_index = {
        (s1, s2): index
        for index, (s1, s2) in enumerate(zip(signs_first, signs_second))
    }
    for signs, block in sectors.items():
        index = sign_to_index[(signs[0], signs[1])]
        assert np.allclose(
            np.linalg.eigvalsh(block), np.linalg.eigvalsh(blocks[index]), atol=1e-10
        )


def test_the_split_covers_the_whole_space_and_is_exact():
    d = 6
    hamiltonian = build_dimension_shift_hamiltonian(d, 1.0, "gue", seed=3)
    blocks = sector_blocks(hamiltonian, [sector_swap(d)])
    total = sum(block.shape[0] for block in blocks.values())
    assert total == 2 * d
    for block in blocks.values():
        assert np.allclose(block, block.conj().T)
    # The union of the sector spectra is the full spectrum.
    union = np.sort(np.concatenate([np.linalg.eigvalsh(b) for b in blocks.values()]))
    assert np.allclose(union, np.linalg.eigvalsh(hamiltonian))


def test_a_non_involution_is_refused():
    hamiltonian = build_dimension_shift_hamiltonian(4, 1.0, "gue", seed=4)
    with pytest.raises(ValueError, match="not an involution"):
        sector_blocks(hamiltonian, [np.zeros((8, 8), dtype=complex)])


def test_non_commuting_involutions_are_refused():
    hamiltonian = np.eye(4, dtype=complex)
    first = np.diag([1.0, -1.0, 1.0, -1.0]).astype(complex)
    second = np.array(
        [[0.0, 1.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0],
         [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, -1.0]], dtype=complex
    )
    with pytest.raises(ValueError, match="do not commute"):
        sector_blocks(hamiltonian, [first, second])


def test_validation_of_bad_inputs():
    with pytest.raises(ValueError):
        sector_blocks(np.eye(4), [])
    with pytest.raises(ValueError):
        sector_blocks(np.zeros((2, 2)), [np.eye(2)])
    with pytest.raises(ValueError):
        commutator_ratio(np.eye(3), np.eye(2))


# ============================================================
# The calibration table
# ============================================================

@pytest.fixture(scope="module")
def table() -> list[CalibrationRow]:
    return calibration_table((1, 2, 3, 4), dimension=60, seeds=300)


def _row(table: list[CalibrationRow], n: int, matrix_class: str) -> CalibrationRow:
    return next(
        row for row in table if row.n_sectors == n and row.matrix_class == matrix_class
    )


def test_one_sector_reproduces_the_class_references(table):
    """Single sector: `0.52` for GOE, `0.59` for GUE."""
    goe = _row(table, 1, "goe")
    gue = _row(table, 1, "gue")
    assert goe.mean_r == pytest.approx(0.52, abs=0.03)
    assert gue.mean_r == pytest.approx(0.59, abs=0.03)
    assert goe.mean_r == pytest.approx(R_GOE, abs=0.03)
    assert gue.mean_r == pytest.approx(R_GUE, abs=0.03)


def test_two_sectors_collapse_the_two_classes(table):
    """**The first limit.** GOE and GUE both land at about `0.42`; the class is gone."""
    goe = _row(table, 2, "goe")
    gue = _row(table, 2, "gue")
    assert goe.mean_r == pytest.approx(0.43, abs=0.03)
    assert gue.mean_r == pytest.approx(0.42, abs=0.03)
    assert abs(goe.mean_r - gue.mean_r) < 0.03
    assert abs(goe.mean_r - gue.mean_r) < goe.std_r + gue.std_r


def test_three_or_more_sectors_approach_poisson(table):
    for n in (3, 4):
        for matrix_class in ("goe", "gue"):
            row = _row(table, n, matrix_class)
            assert 0.37 <= row.mean_r <= 0.41, (n, matrix_class, row.mean_r)
    assert _row(table, 4, "gue").mean_r == pytest.approx(R_POISSON, abs=0.02)


def test_the_table_is_monotone_in_the_number_of_sectors(table):
    for matrix_class in ("goe", "gue"):
        means = [_row(table, n, matrix_class).mean_r for n in (1, 2, 3, 4)]
        assert means == sorted(means, reverse=True)


def test_calibration_validation():
    with pytest.raises(ValueError):
        calibration_table(seeds=1)
    with pytest.raises(ValueError):
        superposition_spectrum(0)
    with pytest.raises(ValueError):
        superposition_spectrum(2, matrix_class="poisson")


# ============================================================
# Limit 1: it detects but does not count
# ============================================================

def test_the_sector_count_cannot_be_recovered_from_a_single_spectrum(table):
    """**The second limit.** For a true `N = 4` the inversion scatters over `1..4`.

    The reviewer's attempt returned `12` for a true `4`. The magnitude depends on the
    estimator; the instability does not.
    """
    estimates = [
        estimate_sector_count(_single_mean_r(seed), table, "gue") for seed in range(12)
    ]
    assert max(estimates) - min(estimates) > 1.0
    assert min(estimates) <= 3.0
    for estimate in estimates:
        assert 1.0 <= estimate <= 4.0


def _single_mean_r(seed: int) -> float:
    from riemann_framework.statistics import mean_r_ratio

    return float(mean_r_ratio(superposition_spectrum(4, 60, "gue", seed), unfold=False))


def test_the_estimator_saturates_instead_of_saying_it_cannot_tell(table):
    """Below the three-sector value it returns the largest tabulated count."""
    saturated = estimate_sector_count(R_POISSON, table, "gue")
    assert saturated == 4.0
    assert saturated == max(row.n_sectors for row in table)


# ============================================================
# Limit 2 and the warning
# ============================================================

def test_the_report_flags_a_contaminated_full_spectrum():
    """The reliable signal: full spectrum below every resolved sector."""
    d = 40
    hamiltonian = build_dimension_shift_hamiltonian(d, 1.0, "gue", seed=0)
    report = desymmetrise(hamiltonian, [sector_swap(d)])
    assert report.sector_count == 2
    assert report.full_spectrum_contaminated
    assert report.full.mean_r < min(s.mean_r for s in report.sectors) - CLASS_SHIFT_THRESHOLD
    assert any("superposition of 2 unresolved sectors" in w for w in report.warnings)


def test_the_two_sector_band_is_flagged_as_class_unreadable():
    d = 40
    hamiltonian = build_dimension_shift_hamiltonian(d, 1.0, "gue", seed=0)
    report = desymmetrise(hamiltonian, [sector_swap(d)])
    if TWO_SECTOR_BAND[0] <= report.full.mean_r <= TWO_SECTOR_BAND[1]:
        assert class_information_at_two_sectors(report)
        assert any("coincide" in warning for warning in report.warnings)


def test_a_low_full_mean_warns_about_integrability_too():
    """The honest limit: Poisson-level `⟨r⟩` is symmetry *or* integrability."""
    d = 40
    hamiltonian = build_dimension_shift_hamiltonian(d, 1.0, "gue", seed=0)
    report = desymmetrise(hamiltonian, [sector_swap(d)])
    low = DesymmetrisedReport(
        full=SpectrumStatistics(label="full spectrum", mean_r=0.39, dimension=80),
        sectors=report.sectors,
        warnings=[],
        n_involutions=1,
    )
    warnings = contamination_warnings(low)
    assert any("integrable system" in warning for warning in warnings)
    assert low.full.mean_r < MULTI_SECTOR_CEILING


def test_a_single_sector_spectrum_raises_no_warning():
    """Non-vacuity: a resolved, single-sector spectrum is not flagged.

    The trivial involution `U = I` commutes with everything, splits into one sector,
    and the spectrum is a single GUE draw: `⟨r⟩ ≈ 0.60`, no warning.
    """
    rng = np.random.default_rng(0)
    raw = (rng.standard_normal((60, 60)) + 1j * rng.standard_normal((60, 60))) / np.sqrt(2)
    hamiltonian = (raw + raw.conj().T) / 2.0
    report = desymmetrise(hamiltonian, [np.eye(60)])
    assert report.sector_count == 1
    assert report.full.mean_r >= SINGLE_SECTOR_FLOOR
    assert not report.full_spectrum_contaminated
    assert report.warnings == []


# ============================================================
# The spectrum-only detector: a warning, not a measurement
# ============================================================
#
# The entry points below take only eigenvalues, which is the case a screening test is
# in: the candidate operator is known, its symmetries are not. They cannot verify
# commutation, so every test here is about what the flag does and does not say.

def test_classify_mean_puts_the_reference_values_in_their_classes():
    assert classify_mean(R_GOE) == "goe"
    assert classify_mean(R_GUE) == "gue"
    assert classify_mean(R_POISSON) == "poisson"
    assert classify_mean(0.45) == "intermediate"
    assert classify_mean(0.65) == "intermediate"


def test_sector_spectra_splits_a_genuinely_symmetric_hamiltonian():
    """The served name, on a matrix that really does commute with the involution."""
    d = 40
    hamiltonian = build_dimension_shift_hamiltonian(d, 1.0, "gue", seed=2)
    spectra = sector_spectra(hamiltonian, sector_swap(d))
    assert len(spectra) == 2
    for spectrum in spectra:
        assert spectrum.size == d
    union = np.sort(np.concatenate(spectra))
    assert np.allclose(union, np.linalg.eigvalsh(hamiltonian))
    full = _mean_r(union)
    assert all(_mean_r(spectrum) > full + CLASS_SHIFT_THRESHOLD for spectrum in spectra)


def test_sector_spectra_refuses_a_matrix_that_does_not_commute():
    """The precondition the reviewer's fixture skips, and fails.

    Their `make_sigma_symmetric_hamiltonian` measures
    `||[H, sigma]||/||H|| = 1.14 … 1.18` (their numbers, `d = 20, 100`, both classes);
    the same construction here measures `1.43`. Their utility diagonalises the
    involution, keeps the diagonal blocks and drops the rest, which on a matrix that
    does not commute is not a sector decomposition.
    """
    rng = np.random.default_rng(3)
    d = 20
    block_a = rng.standard_normal((d, d))
    block_c = rng.standard_normal((d, d))
    block_a = (block_a + block_a.T) / 2.0
    block_c = (block_c + block_c.T) / 2.0
    hamiltonian = np.block([[block_a, block_c], [block_c, block_a]])

    basis, _ = np.linalg.qr(rng.standard_normal((2 * d, 2 * d)))
    involution = basis @ np.diag([1.0] * d + [-1.0] * d) @ basis.T
    involution = (involution + involution.T) / 2.0

    assert is_involution(involution)
    assert commutator_ratio(hamiltonian, involution) > 1.0
    with pytest.raises(ValueError, match="does not commute"):
        sector_spectra(hamiltonian, involution)


def test_estimate_sectors_from_mean_refuses_to_count_past_two():
    """Deliberately conservative: one, two, or `None` -- never `12` for a true `4`."""
    assert estimate_sectors_from_mean(R_GOE) == 1
    assert estimate_sectors_from_mean(0.426) == 2
    assert estimate_sectors_from_mean(0.404) is None
    assert estimate_sectors_from_mean(R_POISSON) is None


def test_detect_hidden_symmetry_reports_three_severities():
    one_sector = detect_hidden_symmetry(superposition_spectrum(1, 60, "gue", seed=1))
    assert not one_sector.is_contaminated
    assert one_sector.severity == "none"
    assert one_sector.estimated_sectors == 1

    # A single GOE sector that happens to draw just under the floor: `mild`, because
    # it is inside the band where one sector and two sectors overlap.
    borderline = detect_hidden_symmetry(superposition_spectrum(1, 60, "goe", seed=25))
    assert borderline.is_contaminated
    assert borderline.severity == "mild"
    assert 0.46 <= borderline.full_mean_r < SINGLE_SECTOR_FLOOR

    two_sectors = detect_hidden_symmetry(superposition_spectrum(2, 60, "gue", seed=0))
    assert two_sectors.severity == "severe"
    assert two_sectors.estimated_sectors == 2
    assert "erased" in two_sectors.explanation

    four_sectors = detect_hidden_symmetry(superposition_spectrum(4, 60, "gue", seed=0))
    assert four_sectors.severity == "severe"
    assert four_sectors.estimated_sectors is None
    assert "integrable" in four_sectors.explanation


def test_the_detector_flags_pure_goe_spectra_too():
    """The false-positive rate is why this is a warning and not a measurement.

    Measured at `d = 60`, seeds `0 … 39`: 4 of 40 pure single-sector GOE draws fall
    below the `0.48` floor and are flagged; 0 of 40 GUE draws are. The flag is worth
    acting on, and it is not evidence of anything by itself.
    """
    goe_flagged = sum(
        detect_hidden_symmetry(superposition_spectrum(1, 60, "goe", seed)).is_contaminated
        for seed in range(40)
    )
    gue_flagged = sum(
        detect_hidden_symmetry(superposition_spectrum(1, 60, "gue", seed)).is_contaminated
        for seed in range(40)
    )
    assert 0 < goe_flagged < 10
    assert gue_flagged == 0


def test_contamination_warning_verifies_the_involution_it_is_given():
    d = 40
    hamiltonian = build_dimension_shift_hamiltonian(d, 1.0, "gue", seed=0)
    warning = contamination_warning(hamiltonian, sector_swap(d))
    assert warning.is_contaminated
    assert warning.severity == "severe"
    # A *known* two-sector split that the table maps to `None`: at `d = 40` the full
    # spectrum lands at 0.404, in the three-sector band. The count is a property of
    # the estimator, not of the space -- which is the whole point.
    assert warning.estimated_sectors is None
    assert 0.39 <= warning.full_mean_r < 0.41
    assert "minimum sector mean" in warning.explanation

    broken = build_dimension_shift_hamiltonian(d, 1.0, "gue", seed=0, sigma_breaking=0.5)
    with pytest.raises(ValueError, match="does not commute"):
        contamination_warning(broken, sector_swap(d))


def test_detect_hidden_symmetry_needs_enough_levels():
    with pytest.raises(ValueError, match="at least 8 levels"):
        detect_hidden_symmetry(np.linspace(0.0, 1.0, 7))


def test_the_severe_flag_states_its_own_limit():
    """A caller that reads only `summary()` still sees the cannot-distinguish caveat."""
    warning = detect_hidden_symmetry(superposition_spectrum(4, 60, "gue", seed=0))
    assert warning.summary().startswith("[severe]")
    assert "integrable" in warning.summary()
    assert "split" in warning.summary()


def _mean_r(eigenvalues) -> float:
    from riemann_framework.statistics import mean_r_ratio

    return float(mean_r_ratio(np.asarray(eigenvalues, dtype=float), unfold=False))


# ============================================================
# The count, with an error bar
# ============================================================
#
# The point of this section is that "detects but does not count" was itself a
# measurement, and a coarser one than had to be. Fitting the whole gap-ratio sequence
# recovers the count at one and at two, and refuses above that. All three statements
# are pinned here, including the refusal.

@pytest.fixture(scope="module")
def count_model() -> SectorCountModel:
    return default_sector_count_model()


def _count_estimate(model: SectorCountModel, truth, index: int):
    return model.estimate(_synthetic_spectrum(truth, index, 50_000, model.total_levels))


def test_one_sector_is_measured(count_model):
    """`p = 0.97` on the true label, and a point interval."""
    estimate = _count_estimate(count_model, 1, 0)
    assert estimate.posterior[1] == pytest.approx(0.97, abs=0.05)
    assert estimate.credible_interval == (1, 1)
    assert estimate.map_label == 1
    assert estimate.summary().startswith("1 (p =")


def test_one_sector_is_excluded_for_every_other_truth(count_model):
    """The non-vacuity check: the posterior does not put mass on 1 out of politeness."""
    for truth in COUNT_LABELS:
        if truth == 1:
            continue
        for index in range(5):
            assert _count_estimate(count_model, truth, index).posterior[1] < 0.02, truth


def test_two_sectors_comes_back_as_a_set_not_a_point(count_model):
    """**The honest half-measure.** Two sectors is right 65% of the time, never 2 alone."""
    estimates = [_count_estimate(count_model, 2, index) for index in range(20)]
    probabilities = [estimate.posterior[2] for estimate in estimates]
    assert sum(probabilities) / len(probabilities) > 0.45
    exact = [estimate.credible_interval == (2, 2) for estimate in estimates]
    assert sum(exact) / len(exact) <= 0.5
    for estimate in estimates:
        assert estimate.posterior[1] < 0.02
        assert estimate.credible_interval[0] in (2, 3)


def test_three_or_more_is_not_counted(count_model):
    """**The negative result survives**, now with an interval: `>=3`, and 3..6 open."""
    estimates = [_count_estimate(count_model, 4, index) for index in range(20)]
    at_least_three = [
        sum(estimate.posterior[label] for label in (3, 4, 5, 6, None))
        for estimate in estimates
    ]
    assert sum(at_least_three) / len(at_least_three) > 0.9
    true_mass = sum(estimate.posterior[4] for estimate in estimates) / len(estimates)
    assert true_mass < 0.35
    open_upper = sum(estimate.credible_interval[1] is None for estimate in estimates)
    assert open_upper / len(estimates) >= 0.4


def test_the_interval_is_calibrated_by_simulation(count_model):
    """Coverage is measured, not assumed: `>= 0.80` everywhere, `1.00` at one sector."""
    rows = count_model.coverage(draws=40, truths=(1, 2, 4, None))
    by_truth = {row.truth: row for row in rows}
    assert by_truth[1].coverage == 1.0
    assert by_truth[1].exact >= 0.85
    for row in rows:
        assert row.coverage >= 0.80, row.summary()
        assert 0.0 <= row.posterior_probability <= 1.0
    assert "coverage" in rows[0].summary()


def test_the_posterior_is_a_distribution(count_model):
    estimate = _count_estimate(count_model, 3, 0)
    assert set(estimate.posterior) == set(COUNT_LABELS)
    assert sum(estimate.posterior.values()) == pytest.approx(1.0, abs=1e-12)
    assert all(value >= 0.0 for value in estimate.posterior.values())
    assert 0.0 <= estimate.probability <= 1.0


def test_the_estimate_is_deterministic(count_model):
    first = _count_estimate(count_model, 2, 3)
    second = _count_estimate(count_model, 2, 3)
    assert first.posterior == second.posterior
    assert first.credible_interval == second.credible_interval

    small_first = SectorCountModel.fit(total_levels=60, seeds=10)
    small_second = SectorCountModel.fit(total_levels=60, seeds=10)
    assert np.array_equal(small_first.edges, small_second.edges)
    spectrum = _synthetic_spectrum(2, 0, 50_000, 60)
    assert (
        small_first.estimate(spectrum).posterior
        == small_second.estimate(spectrum).posterior
    )


def test_the_model_validates_its_inputs(count_model):
    with pytest.raises(ValueError, match="at least 24 levels"):
        SectorCountModel.fit(total_levels=10)
    with pytest.raises(ValueError, match="at least 4 bins"):
        SectorCountModel.fit(bins=2)
    with pytest.raises(ValueError, match="at least 8 training"):
        SectorCountModel.fit(seeds=4)
    with pytest.raises(ValueError, match="at least two sector"):
        SectorCountModel.fit(max_sectors=1)
    with pytest.raises(ValueError, match="at least two distinct"):
        count_model.posterior(np.array([0.5]))
    with pytest.raises(ValueError, match="level must lie"):
        count_model.posterior(np.array([0.5, 0.6]), level=0.0)
    with pytest.raises(ValueError, match="at least one draw"):
        count_model.coverage(draws=0)


def test_the_posterior_agrees_that_a_two_sector_model_is_contaminated():
    """The estimate and the split tell the same story on a real `σ`-model spectrum."""
    d = 60
    hamiltonian = build_dimension_shift_hamiltonian(d, 1.0, "gue", seed=0)
    report = desymmetrise(hamiltonian, [sector_swap(d)])
    assert report.sector_count == 2

    model = SectorCountModel.fit(total_levels=2 * d, seeds=40)
    estimate = sector_count_posterior(np.linalg.eigvalsh(hamiltonian), model=model)
    assert estimate.posterior[1] < 0.1
    assert estimate.posterior[2] + estimate.posterior[3] > 0.4
    assert "CI" in estimate.summary()
