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
"""Tests for the unequal-sector posterior.

The construction is pinned exactly. The measured accuracies are pinned with a margin and a
direction, because they are statistical: the claim is that the joint model carries the count
through strong imbalance and that the equal-block model under-counts, not that either lands
on a third decimal. The numbers of record are in `output/mixed_sector_count.csv` and
`docs/mixed_sectors.md`; these tests run thirty spectra per label, so they agree with that
table only in the large.
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.desymmetrisation import HigherOrderCountModel
from riemann_framework.mixed_sector_count import (
    DEFAULT_SECTORS,
    DEFAULT_SIZE_RATIOS,
    MixedLabel,
    MixedSectorModel,
    block_dimensions,
    build_mixed_spectrum,
    default_mixed_model,
    equal_block_bias,
    label_grid,
)


def test_the_occupation_of_the_equal_case_is_the_inverse_count():
    for count in (2, 3, 4, 6):
        assert MixedLabel(count, 1.0).occupation == pytest.approx(1.0 / count)
    assert MixedLabel(1, 1.0).occupation == pytest.approx(1.0)


def test_the_occupation_of_a_dominant_block_follows_the_ratio():
    """Two sectors at ratio four: the big block carries four fifths of the levels."""
    assert MixedLabel(2, 4.0).occupation == pytest.approx(0.8)
    assert MixedLabel(3, 4.0).occupation == pytest.approx(4.0 / 6.0)


def test_block_dimensions_sum_to_the_total():
    for count in DEFAULT_SECTORS:
        for ratio in DEFAULT_SIZE_RATIOS:
            if count == 1 and ratio != 1.0:
                continue
            dimensions = block_dimensions(count, ratio)
            assert sum(dimensions) == 240, (count, ratio, dimensions)
            assert dimensions[0] >= dimensions[-1], (count, ratio, dimensions)


def test_the_equal_case_gives_equal_blocks():
    assert block_dimensions(4, 1.0) == (60, 60, 60, 60)
    assert block_dimensions(1, 1.0) == (240,)


def test_a_dominant_block_is_the_ratio():
    """At two sectors the blocks really are in the stated ratio, up to rounding."""
    largest, smallest = block_dimensions(2, 4.0)
    assert largest / smallest == pytest.approx(4.0, abs=0.12)


def test_too_many_sectors_do_not_fit():
    """A block never goes below four levels, so the packing is refused rather than fudged."""
    with pytest.raises(ValueError, match="cannot be packed"):
        block_dimensions(100, 1.0)
    with pytest.raises(ValueError, match="cannot be packed"):
        block_dimensions(6, 100.0)


def test_a_single_sector_has_no_ratio():
    with pytest.raises(ValueError, match="no size ratio"):
        MixedLabel(1, 2.0)
    with pytest.raises(ValueError, match="no size ratio"):
        block_dimensions(1, 2.0)
    with pytest.raises(ValueError, match="at least one sector"):
        MixedLabel(0, 1.0)
    with pytest.raises(ValueError, match="cannot be smaller"):
        MixedLabel(2, 0.5)


def test_the_label_grid_is_ragged():
    """One label at one sector, three at every larger count: the prior must say so."""
    labels = label_grid()
    assert len(labels) == 1 + 4 * len(DEFAULT_SIZE_RATIOS)
    assert {label.n_sectors for label in labels} == set(DEFAULT_SECTORS)


def test_the_prior_is_uniform_over_counts_not_labels():
    model = default_mixed_model()
    totals: dict[int, float] = {}
    for label, probability in model.prior.items():
        totals[label.n_sectors] = totals.get(label.n_sectors, 0.0) + probability
    for count, mass in totals.items():
        assert mass == pytest.approx(1.0 / len(DEFAULT_SECTORS)), count


def test_the_model_mixes_both_classes():
    """A label's density is a GOE/GUE mixture, because the class shifts the ratio more."""
    model = default_mixed_model()
    for label in model.labels:
        assert set(model.means[label]) == {"goe", "gue"}, label
        assert set(model.scales[label]) == {"goe", "gue"}, label


def test_a_fixed_class_gives_one_component():
    model = MixedSectorModel.fit(seeds=8, block_class="goe")
    for label in model.labels:
        assert set(model.means[label]) == {"goe"}, label


def test_the_features_shape_is_checked():
    model = default_mixed_model()
    with pytest.raises(ValueError, match="does not match"):
        model.log_likelihood(np.zeros(3))


def test_the_posterior_and_its_marginals_are_normalised():
    model = default_mixed_model()
    spectrum = build_mixed_spectrum(2, 2.0, 240, "goe", seed=7)
    estimate = model.estimate(spectrum)
    assert sum(estimate.posterior.values()) == pytest.approx(1.0)
    assert sum(estimate.count_posterior().values()) == pytest.approx(1.0)
    assert sum(estimate.ratio_posterior().values()) == pytest.approx(1.0)


def test_the_count_interval_brackets_the_most_probable_count():
    model = default_mixed_model()
    spectrum = build_mixed_spectrum(3, 1.0, 240, "gue", seed=11)
    estimate = model.estimate(spectrum, level=0.9)
    low, high = estimate.count_interval
    assert low <= estimate.map_label.n_sectors <= high
    assert (low, high) in {(a, b) for a in DEFAULT_SECTORS for b in DEFAULT_SECTORS}


def test_the_conditional_ratio_marginal_renormalises():
    model = default_mixed_model()
    spectrum = build_mixed_spectrum(4, 2.0, 240, "goe", seed=13)
    conditional = model.estimate(spectrum).at(4)
    assert set(conditional) == set(DEFAULT_SIZE_RATIOS)
    assert sum(conditional.values()) == pytest.approx(1.0)


def test_the_count_of_one_sector_is_recovered():
    """The decisive case survives the wider hypothesis space, at about 0.9."""
    model = default_mixed_model()
    (row,) = model.coverage(labels=(MixedLabel(1, 1.0),), draws=30)
    assert row.count_correct >= 0.7, row.count_correct
    assert row.joint_covered >= 0.8, row.joint_covered


def test_the_joint_model_carries_six_sectors_through_a_dominant_block():
    """At ratio four the joint model keeps 0.74 of six-sector spectra, the equal-block 0.30."""
    model = default_mixed_model()
    truth = MixedLabel(6, 4.0)
    (row,) = model.coverage(labels=(truth,), draws=60)
    equal = HigherOrderCountModel.fit(seeds=20)
    (other,) = equal_block_bias(equal, (truth,), draws=60)
    assert row.count_correct >= 0.5, row.count_correct
    assert other.count_correct <= 0.55, other.count_correct
    assert row.count_correct > other.count_correct


def test_the_equal_block_model_under_counts_a_dominant_sector():
    """Two unequal sectors read as 1.5: a bias, not a scatter around the truth."""
    equal = HigherOrderCountModel.fit(seeds=20)
    for count in (2, 3):
        (row,) = equal_block_bias(equal, (MixedLabel(count, 4.0),), draws=30)
        assert row.mean_count <= count - 0.4, (count, row.mean_count)


def test_a_moderate_imbalance_is_not_recoverable():
    """The middle ratio is absorbed by its neighbours: about half, and no better."""
    model = default_mixed_model()
    (row,) = model.coverage(labels=(MixedLabel(2, 2.0),), draws=30)
    assert row.ratio_correct <= 0.72, row.ratio_correct


def test_a_strong_imbalance_is_recoverable_given_the_count():
    """At ratio four the ratio is named 0.84 of the time once the count is known."""
    model = default_mixed_model()
    (row,) = model.coverage(labels=(MixedLabel(3, 4.0),), draws=30)
    assert row.ratio_correct >= 0.6, row.ratio_correct


def test_every_label_is_measured_with_an_interval():
    """The interval is measured for all thirteen labels, not asserted for one."""
    model = default_mixed_model()
    rows = model.coverage(draws=10)
    assert len(rows) == len(label_grid())
    for row in rows:
        assert row.draws == 10
        assert 0.0 <= row.joint_covered <= 1.0
        assert row.joint_covered >= 0.5, (row.truth.summary(), row.joint_covered)


def test_the_two_sector_case_is_not_a_point_estimate():
    """A negative result, kept: the pair is never identified, only its parts."""
    model = default_mixed_model()
    (row,) = model.coverage(labels=(MixedLabel(2, 1.0),), draws=30)
    assert row.joint_correct < 0.8, row.joint_correct
    assert row.count_correct > row.joint_correct
