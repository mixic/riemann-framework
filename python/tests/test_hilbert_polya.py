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
"""Tests for the Hilbert-Polya prototype.

Two kinds of test are here and they are deliberately mixed:

* assertions that a claim in `hilbert_polya.py` is *true* (the eigenfunction
  exponent, the exact `PT` threshold, the KMS symmetry);
* assertions that a claim is *bounded* -- that the box really does produce a
  picket fence, that the thermal trace really is blind to `Re(s)`. Those are the
  four gaps, and a test that merely passed would not distinguish "the gap is
  open" from "the gap was not measured".

Several pin the *magnitude* of a failure (2.10x overcount, 1e-4 discretization
residual) rather than a truth value, because the honest content of this module is
how large the gap is, not that it exists.
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.hilbert_polya import (
    BLINDNESS_NOTE,
    BOX_NOTE,
    CONTINUUM_NOTE,
    NON_SEQUITUR_NOTE,
    PT_NOTE,
    algebraic_residual,
    box_count,
    box_matrix_max_error,
    box_positive_levels,
    box_spectrum,
    box_versus_zeros,
    central_difference_residual,
    decay_table,
    eigenfunction_exponent,
    finite_difference_box_spectrum,
    fit_box_length,
    hawking_beta,
    hawking_temperature,
    hermiticity_error,
    imaginary_time_weight,
    is_pt_symmetric,
    kms_asymmetry,
    kms_correlator,
    norm_growth_table,
    partition_function,
    partition_function_from_zeros,
    partition_function_of_zeros,
    prescribed_spectrum_operator,
    prototype_report,
    pt_eigenvalues,
    pt_matrix,
    pt_max_imaginary_part,
    pt_scan,
    pt_threshold,
    real_time_weight,
    recovered_gap,
    spectral_box_matrix,
    thermal_blindness,
    truncated_norm_squared,
    x_squared_thermal,
)

#: `gamma_1` to twelve places, the first ordinate.
GAMMA_1 = 14.134725142


# ============================================================
# 1. The dilation operator: the critical line is its exponent
# ============================================================

def test_eigenfunction_exponent_is_minus_half_plus_i_energy():
    """`a = -1/2 + iE`, i.e. `s - 1` at `s = 1/2 + iE`.

    The real part is pinned by the construction rather than chosen, which is the
    algebraic shadow of the critical line and the reason this operator is the
    right starting point.
    """
    for energy in (0.0, 1.0, GAMMA_1, 100.0):
        a = eigenfunction_exponent(energy)
        assert a.real == pytest.approx(-0.5)
        assert a.imag == pytest.approx(energy)


def test_the_eigenvalue_relation_is_an_identity():
    """`H x^a = -i(a + 1/2) x^a = E x^a`, in exact arithmetic."""
    for energy in (0.0, GAMMA_1, 1e3):
        assert abs(algebraic_residual(energy)) < 1e-13 * max(1.0, energy)


def test_a_different_exponent_is_not_an_eigenfunction():
    """Non-vacuity: shifting `Re(a)` by `delta` leaves a residual of `|delta|`.

    `H x^a = -i(a + 1/2) x^a` is linear in `a`, so moving the real part by
    `-0.4 - (-0.5) = 0.1` shifts the would-be eigenvalue to `gamma - 0.1i`: the
    residual is exactly the shift, `0.1`, against `1e-16` for the right exponent.
    """
    delta = 0.1
    a = complex(-0.5 + delta, GAMMA_1)
    wrong = complex(0.0, -1.0) * (a + 0.5) - GAMMA_1
    assert abs(wrong) == pytest.approx(delta)
    assert abs(algebraic_residual(GAMMA_1)) < 1e-15


def test_the_finite_difference_residual_is_the_predicted_artefact():
    """`|a|^3 h^2 / 6`, not a failure of the eigenfunction.

    This is the number that looked like a broken eigenfunction in the first
    draft: `1.2e-4` at `gamma_1`. It is the grid, and it matches the closed form.
    """
    for energy in (GAMMA_1, 100.0):
        for spacing in (5e-4, 2.5e-4):
            measured = central_difference_residual(energy, spacing)
            predicted = (
                abs(complex(-0.5, energy)) ** 3 * spacing**2 / 6.0
            )
            assert measured == pytest.approx(predicted, rel=1e-3)


def test_the_finite_difference_error_halves_fourfold_when_the_grid_halves():
    """Second-order convergence: the residual is `O(h^2)`, as predicted."""
    coarse = central_difference_residual(GAMMA_1, 5e-4)
    fine = central_difference_residual(GAMMA_1, 2.5e-4)
    assert coarse / fine == pytest.approx(4.0, rel=1e-3)


def test_the_truncated_norm_is_a_logarithm_and_ignores_the_energy():
    """`int_a^b |x^{-1/2+iE}|^2 dx = log(b/a)`, the same for every `E`."""
    assert truncated_norm_squared(1.0, np.e) == pytest.approx(1.0)
    assert truncated_norm_squared(1.0, 1e6) == pytest.approx(np.log(1e6))
    # energy-independent: the integrand is x^-1 whatever E is
    assert truncated_norm_squared(2.0, 8.0) == pytest.approx(np.log(4.0))


def test_the_norm_diverges_so_there_is_no_eigenvalue():
    """Grows without bound at both ends of the interval."""
    table = norm_growth_table([10.0, 1e2, 1e3, 1e4, 1e6])
    values = [row.norm_squared for row in table]
    assert values == sorted(values), "the truncated norm must be monotone"
    assert values[-1] == pytest.approx(np.log(1e6 + 1.0), abs=1e-4)
    assert values[-1] > 13.0
    # the same divergence at the origin, which is the half usually omitted
    assert truncated_norm_squared(1e-6, 1.0) == pytest.approx(np.log(1e6))


def test_truncated_norm_rejects_an_empty_interval():
    with pytest.raises(ValueError):
        truncated_norm_squared(2.0, 1.0)
    with pytest.raises(ValueError):
        truncated_norm_squared(0.0, 1.0)


# ============================================================
# 2. The box: a picket fence, and the arithmetic that does not fit it
# ============================================================

def test_the_box_spectrum_is_exactly_evenly_spaced():
    """`2 pi n / L`, to rounding -- a picket fence by construction."""
    length, samples = 20.0, 64
    spectrum = box_spectrum(length, samples)
    spacings = np.diff(spectrum)
    assert spacings.max() - spacings.min() < 1e-12
    assert spacings.mean() == pytest.approx(2.0 * np.pi / length)


def test_the_spectral_box_matrix_reproduces_the_ladder():
    """The discretization must not shadow the algebra: `1e-14`, not `1e-2`."""
    assert box_matrix_max_error(20.0, 64) < 1e-10
    matrix = spectral_box_matrix(20.0, 64)
    assert hermiticity_error(matrix) < 1e-12


def test_the_naive_finite_difference_box_bends_the_ladder():
    """The trap that a first draft fell into, pinned so it stays documented.

    `sin(k h)/h` is not `k`: the deviation reaches `6.85` at `L = 20, N = 64`,
    more than twice the spacing. Spectral derivative: `1e-14`.
    """
    length, samples = 20.0, 64
    naive = finite_difference_box_spectrum(length, samples)
    analytic = box_spectrum(length, samples)
    assert np.abs(naive - analytic).max() > 1.0
    assert np.abs(naive - analytic).max() == pytest.approx(6.8531, abs=1e-3)
    assert box_matrix_max_error(length, samples) < 1e-10


def test_box_count_is_linear_in_height():
    """`N(T) = T L / 2 pi`: the ladder's density is constant, the zeros' is not."""
    length = 2.0 * np.pi
    assert [box_count(t, length) for t in (10.0, 20.0, 40.0)] == [10, 20, 40]


def test_the_fitted_box_contains_exactly_the_requested_count():
    heights = [14.0, 21.0, 25.0]
    length = fit_box_length(heights)
    assert box_count(heights[-1], length) == len(heights)


def test_the_box_r_ratio_is_exactly_one():
    """Uniform spacing gives `r = 1` for every pair, the maximum possible."""
    levels = box_positive_levels(2.656466, 100)
    from riemann_framework.statistics import mean_r_ratio

    assert mean_r_ratio(levels, unfold=False) == pytest.approx(1.0)


def test_the_zeros_are_not_a_picket_fence():
    """The measured mismatch, with the small spacing spread quoted."""
    verdict = box_versus_zeros(100)
    assert verdict.box_r_ratio == pytest.approx(1.0)
    assert verdict.zero_r_ratio < 0.65
    assert verdict.zero_r_ratio > 0.55
    # the gap between the two is the whole content of the comparison
    assert verdict.box_r_ratio - verdict.zero_r_ratio > 0.35


def test_the_box_get_over_the_density_wrong_and_worst_at_the_bottom():
    """Overcount `2.10x` at `T = 50`, decaying toward the fit height.

    The fit is made at the top by construction, so the failure has to be worst
    far from it. A comparison at a single height would have shown `1.06x` and
    looked benign.
    """
    verdict = box_versus_zeros(100)
    ratios = {row.height: row.ratio for row in verdict.rows}
    assert ratios[50.0] == pytest.approx(2.10, abs=0.02)
    assert ratios[100.0] == pytest.approx(1.448, abs=0.01)
    assert ratios[200.0] == pytest.approx(1.063, abs=0.01)
    assert ratios[50.0] > ratios[100.0] > ratios[200.0] > 1.0


def test_rescaling_the_ladder_onto_the_zeros_does_not_rescue_it():
    """Even the most generous affine fit misses by `6.4` mean spacings."""
    verdict = box_versus_zeros(100)
    assert verdict.mean_zero_spacing == pytest.approx(2.246, abs=0.01)
    assert verdict.mean_miss == pytest.approx(14.40, abs=0.05)
    assert verdict.miss_in_mean_spacings == pytest.approx(6.41, abs=0.05)
    assert verdict.mean_miss > 6.0 * verdict.mean_zero_spacing


def test_box_spectrum_validates_its_arguments():
    with pytest.raises(ValueError):
        box_spectrum(0.0, 64)
    with pytest.raises(ValueError):
        box_spectrum(20.0, 63)
    with pytest.raises(ValueError):
        box_positive_levels(20.0, 0)
    with pytest.raises(ValueError):
        fit_box_length([1.0])


# ============================================================
# 3. Reality is a condition, not a gift
# ============================================================

def test_any_real_list_is_the_spectrum_of_a_self_adjoint_operator():
    """The non-sequitur, made concrete: reality is free, identification is not."""
    values = [GAMMA_1, 21.022040, 25.010858]
    operator = prescribed_spectrum_operator(values)
    assert hermiticity_error(operator) == 0.0
    assert np.linalg.eigvalsh(operator) == pytest.approx(values)


def test_a_spoofed_spectrum_is_equally_self_adjoint():
    """Numbers that are *not* zeta zeros get a self-adjoint operator too."""
    zeros = [GAMMA_1, 21.022040]
    spoof = [GAMMA_1 + 0.37, 21.022040 - 1.5]
    assert hermiticity_error(prescribed_spectrum_operator(zeros)) == 0.0
    assert hermiticity_error(prescribed_spectrum_operator(spoof)) == 0.0
    # nothing in the construction distinguishes the two lists: diag is diag
    assert np.allclose(np.diag(prescribed_spectrum_operator(spoof)), spoof)
    assert np.allclose(np.diag(prescribed_spectrum_operator(zeros)), zeros)


def test_the_pt_model_is_genuinely_pt_symmetric():
    """`P M^* P = M` holds for the whole family, broken phase included."""
    for theta in np.linspace(0.0, 1.2, 7):
        assert is_pt_symmetric(pt_matrix(1.0, 0.5, float(theta)))


def test_the_pt_threshold_is_arcsine_and_equals_thirty_degrees():
    """`theta_c = arcsin(s/r) = arcsin(1/2) = pi/6`."""
    assert pt_threshold(1.0, 0.5) == pytest.approx(np.pi / 6.0)
    assert pt_threshold(1.0, 0.5) == pytest.approx(0.5235987756, abs=1e-9)


def test_the_spectrum_is_real_below_the_threshold_and_complex_above():
    """Reality is a condition here, and the crossing is exactly located."""
    threshold = pt_threshold(1.0, 0.5)
    below = pt_eigenvalues(1.0, 0.5, threshold - 1e-9)
    above = pt_eigenvalues(1.0, 0.5, threshold + 1e-9)
    assert np.all(np.abs(np.imag(below)) < 1e-6)
    assert np.all(np.abs(np.imag(above)) > 0.0)
    assert above[0].imag == pytest.approx(-above[1].imag)


def test_the_broken_phase_magnitude_matches_the_closed_form():
    """`|Im lambda| = sqrt(r^2 sin^2 theta - s^2)`."""
    theta = 0.55
    expected = np.sqrt(np.sin(theta) ** 2 - 0.25)
    assert pt_max_imaginary_part(1.0, 0.5, theta) == pytest.approx(expected)
    assert np.abs(np.imag(pt_eigenvalues(1.0, 0.5, theta))).max() == pytest.approx(expected)


def test_the_pt_scan_finds_a_single_crossing():
    """Monotone in `theta`: unbroken, then broken, never back."""
    scan = pt_scan(1.0, 0.5, [0.4, 0.45, 0.5, 0.55, 0.6, 0.65])
    flags = [row.unbroken for row in scan]
    assert flags == [True, True, True, False, False, False]
    magnitudes = [row.max_imaginary_part for row in scan]
    # unbroken means zero to rounding, not exactly zero -- eigenvalues of a
    # matrix are computed, so 1e-17 is the floor
    assert all(value < 1e-12 for value in magnitudes[:3])
    assert magnitudes[3:] == sorted(magnitudes[3:])
    assert magnitudes[-1] > 0.3


# ============================================================
# 4. Imaginary time: real work, and one thing it cannot do
# ============================================================

def test_real_time_evolution_never_decays():
    """`|e^{-iEt}| = 1` for every `t`, however large."""
    for time in (0.0, 1.0, 1e6):
        assert abs(real_time_weight(GAMMA_1, time)) == pytest.approx(1.0)


def test_imaginary_time_decays_and_the_ground_state_dominates():
    """The QITE mechanism, and its limit: it isolates one eigenvalue."""
    energies = [GAMMA_1, 21.022040, 25.010858]
    rows = decay_table(energies, [1.0, 2.0, 4.0])
    assert rows[0].ground_fraction < rows[1].ground_fraction < rows[2].ground_fraction
    assert rows[2].ground_fraction > 0.999999
    assert rows[0].weights[0] == pytest.approx(1.0)


def test_the_gap_is_recovered_exactly_from_imaginary_time():
    """`-(1/tau) log(w_1/w_0)` is the gap, to rounding: it is measured, not derived."""
    energies = [GAMMA_1, 21.022040, 25.010858]
    assert recovered_gap(energies, 2.0) == pytest.approx(
        energies[1] - energies[0], abs=1e-12
    )


def test_the_partition_function_converges_and_decreases():
    """`Z(beta) = sum exp(-beta E_n)` is finite for `beta > 0`."""
    ordinates = [GAMMA_1, 21.022040, 25.010858, 30.424876]
    values = [partition_function(beta, ordinates) for beta in (0.05, 0.1, 0.5, 1.0)]
    assert values[0] > values[1] > values[2] > values[3] > 0.0
    assert partition_function_from_zeros(0.5, 100) == pytest.approx(
        8.837461e-04, rel=1e-4
    )


def test_the_thermal_trace_cannot_see_the_critical_line():
    """The sharpest gap: `Z` is blind to `Re(s)`, exactly, not approximately.

    The two spectra differ by `0.1` in the real part of every zero -- i.e. every
    one of them off the critical line -- and the thermal trace is *identical*
    because only the ordinates are consumed.
    """
    result = thermal_blindness(0.5, 100, shift=0.1)
    assert result["on_line"] > 0.0
    assert result["difference"] == 0.0
    assert result["on_line"] == result["off_line"]
    # and the shift really was applied: a larger shift changes nothing either
    assert thermal_blindness(0.5, 100, shift=1.0)["difference"] == 0.0


def test_partition_function_of_zeros_uses_only_the_ordinates():
    """Direct statement of the blindness, at the level of the API."""
    on_line = [0.5 + 1j * GAMMA_1]
    off_line = [0.75 + 1j * GAMMA_1]
    assert partition_function_of_zeros(0.5, on_line) == partition_function_of_zeros(
        0.5, off_line
    )


def test_the_kms_correlator_is_symmetric_about_half_beta():
    """`G(tau) = G(beta - tau)`: imaginary time is a circle of circumference beta."""
    assert kms_asymmetry(2.0, 1.3) < 1e-15
    beta, omega = 2.0, 1.3
    for tau in (0.1, 0.7, 1.0):
        assert kms_correlator(tau, beta, omega) == pytest.approx(
            kms_correlator(beta - tau, beta, omega), rel=1e-14
        )


def test_the_kms_correlator_at_zero_is_the_thermal_mean_square():
    """`G(0) = coth(beta omega / 2) / (2 omega)`, checked by a third route.

    The closed form, the analytic value it should equal, and the explicit
    Boltzmann sum -- three independent expressions of the same trace.
    """
    beta, omega = 2.0, 1.3
    closed = kms_correlator(0.0, beta, omega)
    assert closed == pytest.approx(1.0 / (np.tanh(beta * omega / 2.0) * 2.0 * omega))
    assert closed == pytest.approx(x_squared_thermal(beta, omega), rel=1e-12)


def test_kms_inputs_are_validated():
    with pytest.raises(ValueError):
        kms_correlator(0.5, 0.0, 1.0)
    with pytest.raises(ValueError):
        kms_correlator(3.0, 2.0, 1.0)
    with pytest.raises(ValueError):
        kms_correlator(0.5, 2.0, -1.0)


def test_the_hawking_relation_is_internally_consistent():
    """`beta = 8 pi G M / c^3` and `T = hbar / (k_B beta)`: one number apart."""
    beta = hawking_beta(1.98892e30)
    temperature = hawking_temperature(1.98892e30)
    assert temperature * beta * 1.380649e-23 / 1.054571817e-34 == pytest.approx(1.0)
    # the textbook value for a solar mass
    assert temperature == pytest.approx(6.1687e-08, rel=1e-3)
    # and the horizon interpretation: circumference = 4 pi r_s / c
    radius = 2.0 * 6.67430e-11 * 1.98892e30 / 2.99792458e8**2
    assert beta == pytest.approx(4.0 * np.pi * radius / 2.99792458e8)


def test_hawking_temperature_falls_with_mass():
    assert hawking_temperature(2.0 * 1.98892e30) < hawking_temperature(1.98892e30)


# ============================================================
# The notes and the verdict
# ============================================================

def test_every_documented_note_states_its_limit():
    """The notes are the module's honesty layer; none may be silently dropped."""
    for note in (CONTINUUM_NOTE, BOX_NOTE, NON_SEQUITUR_NOTE, BLINDNESS_NOTE, PT_NOTE):
        assert isinstance(note, str) and len(note) > 100
    # the blindness note must actually say the blinding word
    assert "Re(s)" in BLINDNESS_NOTE
    # and the non-sequitur note must name the thing that is actually needed
    assert "identification" in NON_SEQUITUR_NOTE


def test_the_verdict_does_not_claim_a_proof():
    """A passing suite must not read as a proof of the Riemann hypothesis."""
    verdict = prototype_report(100).verdict()
    assert "NOT proved" in verdict
    assert "four screens" in verdict
    assert "critical line is its eigenfunction exponent" in verdict


def test_the_report_collects_all_four_gaps():
    report = prototype_report(100)
    assert report.continuum_norm_at_1e6 == pytest.approx(np.log(1e6 + 1.0))
    assert report.box.box_r_ratio == pytest.approx(1.0)
    assert report.pt_threshold == pytest.approx(np.pi / 6.0)
    assert report.thermal_difference == 0.0
    assert report.kms_asymmetry < 1e-15
    assert report.hawking_temperature == pytest.approx(6.1687e-08, rel=1e-3)


def test_the_prototype_does_not_reference_the_zeros_in_its_operator():
    """The screening criterion, as a test: `H` is defined without the zeros.

    `algebraic_residual` and `eigenfunction_exponent` take an energy and know
    nothing about `zeta`; that is what makes the operator a candidate rather than
    a fit. The box comparison is where the zeros enter, and it is the *test*, not
    the definition.
    """
    import inspect

    source = inspect.getsource(eigenfunction_exponent)
    assert "zeta" not in source
    assert "ordinates" not in source
    assert "zetazero" not in inspect.getsource(algebraic_residual)
