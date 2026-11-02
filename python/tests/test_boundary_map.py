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
"""Tests for the boundary map.

The definitions are pinned exactly; the measured accuracies are pinned with a tolerance,
because they are statistical and the point of the map is the *order* of the statistics,
not a third decimal place. The numbers themselves live in `output/boundary_map.csv` and in
`docs/boundary_map.md`.
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.boundary_map import (
    DEFAULT_SECTORS,
    DEFAULT_STATISTICS,
    adjacent_gap_ratio,
    boundary_of,
    build_spectrum,
    feature_vector,
    higher_order_ratio,
    measure,
    number_variance,
    pairwise_accuracy,
    per_class_accuracy,
    poisson_spectrum,
    ratio_histogram,
    unfold,
)


def test_the_spectrum_has_a_constant_total_length():
    """The total is held fixed, so ``m`` cannot be read off the sample size.

    This is the fair-comparison precondition: at 240 levels every sector count gives the
    same number of ratios, and the classifier sees the statistic rather than the length.
    """
    for sectors in DEFAULT_SECTORS:
        spectrum = build_spectrum(sectors, total_levels=240, seed=0)
        assert spectrum.size == 240, (sectors, spectrum.size)
        assert np.all(np.diff(spectrum) >= 0)


def test_the_spectrum_depends_on_the_seed():
    first = build_spectrum(2, 240, seed=0)
    second = build_spectrum(2, 240, seed=1)
    assert not np.allclose(first, second)


def test_unfolding_gives_unit_mean_spacing():
    unfolded = unfold(build_spectrum(1, 240, seed=0))
    assert abs(float(np.mean(np.diff(unfolded))) - 1.0) < 0.05


def test_the_adjacent_ratio_lies_in_the_unit_interval():
    ratios = adjacent_gap_ratio(build_spectrum(2, 240, seed=0))
    assert ratios.size > 0
    assert np.all(ratios > 0.0) and np.all(ratios <= 1.0)


def test_order_one_is_the_adjacent_gap_ratio():
    """The family contains the manuscript's statistic as its first member."""
    spectrum = build_spectrum(2, 240, seed=0)
    plain = adjacent_gap_ratio(spectrum)
    first = higher_order_ratio(spectrum, order=1)
    assert first.size == plain.size
    assert np.allclose(first, plain)
    with pytest.raises(ValueError, match="at least one"):
        higher_order_ratio(spectrum, order=0)


def test_higher_orders_lie_in_the_unit_interval():
    spectrum = build_spectrum(2, 240, seed=0)
    for order in (2, 3, 6):
        ratios = higher_order_ratio(spectrum, order)
        assert ratios.size > 0
        assert np.all(ratios > 0.0) and np.all(ratios <= 1.0)


def test_the_number_variance_of_poisson_grows_like_l():
    """Poisson gives ``Sigma^2(L) = L`` in theory; polynomial unfolding absorbs some of it.

    The measured value is lower than ``L`` and higher than what a rigid spectrum gives,
    which is the separation the map relies on.
    """
    species = [number_variance(poisson_spectrum(240, seed=s)) for s in range(20)]
    mean_curve = np.mean(species, axis=0)
    assert 8.0 <= mean_curve[19] <= 20.0, float(mean_curve[19])
    assert mean_curve[19] > mean_curve[4]


def test_the_number_variance_separates_poisson_from_six_sectors():
    """S1.3: Poisson is far above a six-sector union at a window of 20."""
    poisson = np.mean(
        [number_variance(poisson_spectrum(240, seed=s))[19] for s in range(20)]
    )
    six = np.mean(
        [number_variance(build_spectrum(6, 240, seed=s))[19] for s in range(20)]
    )
    assert poisson >= 8.0, float(poisson)
    assert six <= 4.5, float(six)


def test_the_feature_vectors_have_fixed_shapes():
    spectrum = build_spectrum(2, 240, seed=0)
    assert feature_vector(spectrum, "mean_r").shape == (1,)
    assert feature_vector(spectrum, "hosr_3").shape == (1,)
    assert feature_vector(spectrum, "hosr_family").shape == (6,)
    assert feature_vector(spectrum, "number_variance").shape == (20,)
    assert ratio_histogram(spectrum, order=1).shape == (30,)


def test_the_order_one_mean_is_the_manuscripts_statistic():
    spectrum = build_spectrum(2, 240, seed=0)
    assert np.allclose(
        feature_vector(spectrum, "mean_r"), feature_vector(spectrum, "hosr_1")
    )


def test_the_classifier_is_perfect_on_separable_data():
    rng = np.random.default_rng(0)
    low = rng.normal(0.0, 0.1, (20, 1))
    high = rng.normal(5.0, 0.1, (20, 1))
    X_train = np.vstack([low, high])
    y_train = np.array([0] * 20 + [1] * 20)
    X_test = X_train + rng.normal(0.0, 0.01, X_train.shape)
    accuracy = per_class_accuracy(X_train, y_train, X_test, y_train)
    assert accuracy[0] > 0.95
    assert accuracy[1] > 0.95


def test_the_boundary_is_the_largest_count_that_reaches_the_threshold():
    assert boundary_of({1: 0.9, 2: 0.85, 3: 0.7, 4: 0.5}) == 2
    assert boundary_of({1: 0.5, 2: 0.4}) == 0


def test_the_mean_ratio_boundary_is_one():
    """The manuscript's central claim, measured: the mean stops at one sector.

    At two sectors the per-class accuracy of the mean ratio falls below the threshold,
    which is what "the count is not recoverable above two" means in one number.
    """
    results = measure(n_train=80, n_test=80)
    mean_r = results["mean_r"]
    assert mean_r[1] >= 0.95
    assert mean_r[2] < 0.8, f"the mean ratio reached {mean_r[2]:.2f} at two sectors"
    assert boundary_of(mean_r) == 1


def test_the_order_family_and_the_variance_reach_two_where_the_mean_does_not():
    """S1.4, honestly bounded: the family moves the boundary from one to two, not to six.

    The family of six means and the number variance both reach the threshold at two
    sectors; neither reaches it at three, four or six. That is the measured boundary, and
    the map reports it rather than the hoped-for one.
    """
    results = measure(n_train=80, n_test=80)
    family = results["hosr_family"]
    variance = results["number_variance"]
    assert family[2] >= 0.75, f"family at two sectors: {family[2]:.2f}"
    assert variance[2] >= 0.75, f"variance at two sectors: {variance[2]:.2f}"
    assert boundary_of(family) == 2
    assert boundary_of(variance) == 2
    for count in (3, 4, 6):
        assert family[count] < 0.8, (count, family[count])
        assert variance[count] < 0.8, (count, variance[count])


def test_the_average_order_alone_does_not_move_the_boundary():
    """A single order is not the family: one order stays at the mean's boundary."""
    results = measure(n_train=80, n_test=80)
    assert boundary_of(results["hosr_3"]) == 1
    assert boundary_of(results["hosr_6"]) == 1


def test_pairwise_the_family_beats_the_mean():
    """Telling three sectors from six: 0.85 for the family against 0.61 for the mean."""
    mean_r = pairwise_accuracy("mean_r", 3, 6)
    family = pairwise_accuracy("hosr_family", 3, 6)
    assert mean_r < 0.75, f"mean ratio pairwise accuracy {mean_r:.2f}"
    assert family > 0.8, f"family pairwise accuracy {family:.2f}"
    assert family > mean_r + 0.1


def test_every_default_statistic_is_measured():
    results = measure(n_train=20, n_test=20)
    assert set(results) == set(DEFAULT_STATISTICS)
    for statistic, accuracy in results.items():
        assert set(accuracy) == set(DEFAULT_SECTORS), statistic
