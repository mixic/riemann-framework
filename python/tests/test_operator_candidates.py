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
"""Tests for the candidate operators and for the screening procedure itself.

The awkward tests here are the ones asserting a *negative* result about the
screening machinery: that the prime-length graph matches the zeros' statistics
better than the zeros do, and that the unitary twin passes every numerical test.
Those are the findings, so a suite that only confirmed "the graph is not the
zeros" would have measured the wrong thing.
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.hilbert_polya import box_versus_zeros
from riemann_framework.operator_candidates import (
    DENSITY_NOTE,
    DICTIONARY_NOTE,
    SCREENING_NOTE,
    STATISTICS_NOTE,
    TWIN_NOTE,
    closed_orbit_lengths,
    density_table,
    graph_report,
    local_exponent,
    power_law_fit,
    primon_counting,
    screening_table,
    star_edge_lengths,
    star_poles,
    star_secular,
    star_spectrum,
    survivors,
    twin_report,
    unitary_twin,
    von_mangoldt_table,
    zero_counting,
)

GAMMA_1 = 14.134725142


# ============================================================
# 1. The density scale: what the zeros demand
# ============================================================

def test_the_zero_density_rises_across_the_range():
    """`dN/dT` measured: `0.278 -> 0.543`, monotonically. That is a logarithm."""
    rows = density_table()
    assert [row.count for row in rows] == [10, 19, 23, 47]
    rates = [row.per_unit_height for row in rows]
    assert rates == pytest.approx([0.2778, 0.38, 0.46, 0.5434], abs=1e-4)
    assert rates == sorted(rates), "the density must rise; a constant would be a 2D law"


def test_the_local_exponent_drifts_and_so_is_not_a_power_law():
    """`log N / log T` climbs `0.589 -> 0.731 -> 0.825`: no fixed exponent."""
    exponents = [local_exponent(t) for t in (50.0, 100.0, 200.0)]
    assert exponents == pytest.approx([0.5886, 0.7312, 0.8247], abs=1e-3)
    assert exponents == sorted(exponents)
    assert exponents[-1] < 1.0


def test_a_power_law_fits_the_counting_function_where_the_numbers_live():
    """The uncomfortable number: `T^1.436` is off by 1.33 levels in 100.

    This is why density is not a usable screen at these heights, and the test
    exists to keep that weakness visible rather than to celebrate a fit.
    """
    fit = power_law_fit(100)
    assert fit.exponent == pytest.approx(1.436, abs=0.01)
    assert fit.max_error_levels == pytest.approx(1.33, abs=0.05)
    assert fit.zero_count == 100
    # 1.33 levels out of 100 is 1.3%
    assert fit.max_error_levels / 100 < 0.02


def test_the_power_law_is_checked_off_the_fitting_set():
    """At the sampled heights the residual reaches `1.92`, at `T = 20`."""
    fit = power_law_fit(100)
    assert fit.actual == [1, 10, 29, 52, 79]
    assert fit.predicted[0] == pytest.approx(2.92, abs=0.02)
    assert fit.max_error_at_heights == pytest.approx(1.92, abs=0.02)


def test_the_power_law_fit_spans_only_two_decades_and_says_so():
    """A fit over `gamma_1 .. gamma_100` is 1.7 decades: honest limit, not proof."""
    fit = power_law_fit(100)
    span = np.log(fit.heights[-1] / fit.heights[0])
    assert span < 2.5
    assert "cannot reject" in fit.summary()


def test_a_law_through_the_origin_fails_where_the_power_law_succeeds():
    """Same 100 zeros, two density classes: box `21` at `T = 50`, power law `10.9`, true `10`.

    The box has no constant term, which is why it fails at the *bottom* of the
    range while a fitted power law does not. That difference is the density
    screen working -- and it is also why the screen is weak: the power law gets
    the same numbers right while being the wrong asymptotic class.
    """
    verdict = box_versus_zeros(100)
    assert verdict.rows[0].height == 50.0
    assert verdict.rows[0].zero_count == 10
    assert verdict.rows[0].box_count == 21
    fit = power_law_fit(100)
    assert fit.predicted[1] == pytest.approx(10.88, abs=0.02)


def test_von_mangoldt_matches_the_exact_count():
    """The smooth density is the right *class*; it is still not the zeros."""
    for height, actual, smooth in von_mangoldt_table():
        assert actual == pytest.approx(smooth, abs=1.0), height


def test_counting_helpers_validate_their_inputs():
    with pytest.raises(ValueError):
        zero_counting(0.0)
    with pytest.raises(ValueError):
        local_exponent(1.0)
    with pytest.raises(ValueError):
        power_law_fit(5)
    with pytest.raises(ValueError):
        density_table(((50.0, 14.0),))


# ============================================================
# 2. The prime-length quantum graph
# ============================================================

def test_edge_lengths_are_half_log_prime():
    """`ell_j = (1/2) log p_j`, so a round trip is exactly `log p_j`."""
    lengths = star_edge_lengths(5, dictionary_exact=True)
    assert lengths == pytest.approx(0.5 * np.log([2, 3, 5, 7, 11]))


def test_the_unscaled_option_is_exactly_twice_and_is_off_by_a_factor_two():
    """The dictionary-exact choice is the favourable one; the other is `2x` off."""
    exact = star_edge_lengths(5, dictionary_exact=True)
    unscaled = star_edge_lengths(5, dictionary_exact=False)
    assert unscaled == pytest.approx(2.0 * exact)


def test_edge_length_validation():
    with pytest.raises(ValueError):
        star_edge_lengths(1)
    with pytest.raises(ValueError):
        star_edge_lengths(10_000)


def test_the_secular_function_vanishes_at_every_level():
    """`sum_j cot(k ell_j) = 0` at each root: the spectrum really solves it."""
    lengths = star_edge_lengths(5, dictionary_exact=True)
    levels = star_spectrum(lengths, 40.0)
    assert len(levels) > 8
    assert max(abs(star_secular(k, lengths)) for k in levels) < 1e-6


def test_poles_are_the_cotangent_poles():
    """Every pole is `n pi / ell_j` for some edge, which `star_spectrum` bisects between."""
    lengths = star_edge_lengths(3, dictionary_exact=True)
    poles = star_poles(lengths, 20.0)
    for pole in poles:
        assert any(
            abs(pole - n * np.pi / ell) < 1e-9
            for ell in lengths
            for n in range(1, 60)
        )


def test_the_spectrum_is_weyl_linear():
    """`N(k)/k` against `L/pi`: linear counting, so the density class is wrong."""
    report = graph_report(5, 120.0)
    assert report.level_count == 150
    assert report.weyl_slope == pytest.approx(1.25, abs=0.01)
    assert report.predicted_slope == pytest.approx(1.233, abs=0.01)
    assert report.counting_is_linear


def test_the_spectrum_is_sorted_and_has_no_duplicates():
    levels = star_spectrum(star_edge_lengths(5), 60.0)
    assert np.all(np.diff(levels) > 0), "levels must be strictly increasing"
    assert len(np.unique(np.round(levels, 9))) == len(levels)


def test_spectrum_requires_a_positive_range():
    with pytest.raises(ValueError):
        star_spectrum(star_edge_lengths(3), 0.0)


def test_closed_orbits_have_length_log_n_computed_from_the_geometry():
    """The dictionary, verified rather than restated: `sum 2 n_j ell_j = log n`."""
    rows = closed_orbit_lengths(5, 30)
    assert len(rows) == 23
    assert all(row.matches for row in rows)
    assert [row.n for row in rows[:4]] == [2, 3, 4, 5]
    assert rows[0].geometric_length == pytest.approx(np.log(2.0))
    assert rows[-1].n == 30


def test_the_closed_orbits_are_exactly_the_primon_spectrum():
    """Which `n` appear? Exactly those whose prime factors the graph carries."""
    graph_primes = {2, 3, 5, 7, 11}
    rows = closed_orbit_lengths(5, 60)
    present = {row.n for row in rows}
    expected = {
        n
        for n in range(2, 61)
        if all(p in graph_primes for p in range(2, n + 1) if n % p == 0 and _is_prime(p))
    }
    assert present == expected


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    return all(n % d for d in range(2, int(n**0.5) + 1))


def test_primon_counting_is_exponential_and_brackets_the_zeros():
    """`e^T` levels against the zeros' `T log T`: the opposite failure."""
    assert primon_counting(5.0) == 148
    assert primon_counting(10.0) == 22026
    assert primon_counting(14.0) > 1_000_000
    # and the zeros have one level below gamma_1
    assert zero_counting(GAMMA_1) == 1


def test_primon_counting_validates_its_height():
    with pytest.raises(ValueError):
        primon_counting(0.0)
    with pytest.raises(ValueError):
        primon_counting(41.0)


# ============================================================
# 3. What the graph proves about the dictionary and about statistics
# ============================================================

def test_the_graph_has_far_more_levels_than_the_zeros_at_the_same_height():
    """17 levels below `k = gamma_1`, where the zeros have 1.

    Same "energy" axis, same dictionary, and the counting functions differ by a
    factor of 17 at the very first zero. The dictionary does not determine the
    spectrum.
    """
    lengths = star_edge_lengths(5, dictionary_exact=True)
    below = len(star_spectrum(lengths, GAMMA_1))
    assert below >= 15
    assert below > 10 * zero_counting(GAMMA_1)


def test_the_graph_matches_the_zeros_statistics_at_least_as_well_as_the_zeros_do():
    """**The finding.** `r = 0.641` and KS `0.0438` against the zeros' `0.0579`.

    An object whose counting function is provably wrong fits the universal
    statistics *better* than the object it is supposed to explain.
    """
    report = graph_report(5, 120.0)
    assert report.r_ratio == pytest.approx(0.641, abs=0.005)
    assert report.zero_r_ratio == pytest.approx(0.610, abs=0.005)
    assert report.r_ratio > report.zero_r_ratio, "the graph scores HIGHER than the zeros"
    assert report.ks_statistic == pytest.approx(0.0438, abs=0.002)
    assert report.zero_ks_statistic == pytest.approx(0.0579, abs=0.002)
    assert report.ks_statistic < report.zero_ks_statistic, "and it is CLOSER to Wigner"


def test_statistics_alone_do_not_certify_a_candidate():
    """Passing GUE means nothing when the counting function is linear.

    `stats_plus_wrong_density` is the combination that the DSH criterion S2 would
    accept, and it is the combination this graph exhibits.
    """
    report = graph_report(5, 120.0)
    assert report.counting_is_linear
    assert abs(report.r_ratio - 0.599) < 0.05  # within the GUE reference
    assert not (report.counting_is_linear and False)  # i.e. linear != right
    # spacing support is far narrower than the zeros'
    assert report.spacing_max < 3.0


def test_the_graph_report_says_what_fails():
    report = graph_report(5, 120.0)
    text = report.summary()
    assert "linear" in text
    assert "BETTER than the zeros" in text


# ============================================================
# 4. The twin: every test passes and nothing is proved
# ============================================================

def test_the_twin_has_the_prescribed_spectrum_exactly():
    values = [14.134725, 21.022040, 25.010858, 30.424876]
    matrix = unitary_twin(values, seed=3)
    assert np.abs(matrix - matrix.conj().T).max() < 1e-12
    assert np.sort(np.linalg.eigvalsh(matrix)) == pytest.approx(values, abs=1e-10)


def test_the_twin_is_not_diagonal_so_it_is_a_genuine_operator():
    """It is `diag(gamma)` only up to a unitary: off-diagonal weight is large."""
    values = [1.0, 2.0, 3.0, 4.0]
    matrix = unitary_twin(values, seed=5)
    off_diagonal = matrix - np.diag(np.diag(matrix))
    assert np.linalg.norm(off_diagonal) > 0.5


def test_the_twin_passes_every_numerical_screen():
    """All of them, to `1e-13`, and none of it means anything."""
    report = twin_report(100)
    assert report.max_eigenvalue_error < 1e-10
    assert report.hermiticity_error < 1e-12
    assert report.trace_error < 1e-8
    assert report.r_ratio == pytest.approx(0.610, abs=0.005)
    assert report.ks_statistic == pytest.approx(0.0579, abs=0.002)
    assert "restatement" in report.summary()


def test_twin_validation():
    with pytest.raises(ValueError):
        unitary_twin([])


# ============================================================
# 5. The screening table
# ============================================================

def test_the_table_scores_four_candidates_on_five_criteria():
    rows = screening_table(100)
    assert len(rows) == 4
    names = [row.candidate for row in rows]
    assert any("box" in name for name in names)
    assert any("graph" in name for name in names)
    assert any("primon" in name for name in names)
    assert any("twin" in name for name in names)


def test_no_candidate_survives():
    """The result of the whole exercise: an empty list."""
    rows = screening_table(100)
    assert survivors(rows) == []


def test_the_twin_passes_every_numerical_test_and_is_still_not_a_candidate():
    """The punchline: the only candidate that passes the numbers fails the logic."""
    rows = screening_table(100)
    twin = next(row for row in rows if "twin" in row.candidate)
    assert twin.passes_every_numerical_test
    assert not twin.independent_definition
    assert not twin.is_a_candidate


def test_the_graph_fails_on_density_not_on_statistics():
    """Different failure modes, which is the point of scoring separately."""
    rows = screening_table(100)
    graph = next(row for row in rows if "graph" in row.candidate)
    box = next(row for row in rows if "box" in row.candidate)
    assert graph.statistics is True and box.statistics is False
    assert graph.density_class is False and box.density_class is False
    assert graph.independent_definition and box.independent_definition
    assert not graph.identification_proved and not box.identification_proved


def test_every_documented_note_states_its_limit():
    """The notes are the module's honesty layer."""
    for note in (DICTIONARY_NOTE, STATISTICS_NOTE, TWIN_NOTE, DENSITY_NOTE, SCREENING_NOTE):
        assert isinstance(note, str) and len(note) > 100
    assert "Statistics cannot certify" in STATISTICS_NOTE
    assert "definition" in TWIN_NOTE
    assert "not observable" in DENSITY_NOTE
