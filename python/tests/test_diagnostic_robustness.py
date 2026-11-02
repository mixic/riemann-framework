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
"""Tests for the three measured limits of the diagnostic.

These are the numbers behind the manuscript's "limitations and scope": the flag's size
dependence, the robustness of the posterior to its own simulator, and the long-range
statistics that separate what the adjacent-gap ratio cannot. The literal values are the
manuscript's (Section 5 and the robustness table in Section 2.4), re-derived here, so a
number that drifts fails this file and the manuscript has to move with it.

`scripts/robustness_diagnostics.py` prints the same three tables.
"""

from __future__ import annotations

import numpy as np
import pytest

from riemann_framework.desymmetrisation import (
    COUNT_ORDERS,
    SINGLE_SECTOR_FLOOR,
    HigherOrderCountModel,
    false_positive_rate_at_size,
    one_sector_r_moments,
    robustness_table,
    size_dependent_floor,
    superposition_spectrum,
)
from riemann_framework.statistics import (
    dyson_mehta_statistic,
    higher_order_r_ratio,
    number_variance,
    r_ratio,
)


def test_the_one_sector_scatter_falls_like_inverse_sqrt_n():
    """The fixed floor is calibrated on one size; the scatter it measures is not fixed.

    sigma(n) ~ 1/sqrt(n), so the ratio at 15 and 240 levels should be about sqrt(240/15)
    = 4, which is why the fixed 0.48 over-flags at 15 and under-flags at 240.
    """
    _, std_small = one_sector_r_moments(15, seeds=200)
    _, std_large = one_sector_r_moments(240, seeds=200)
    ratio = std_small / std_large
    assert 3.0 < ratio < 5.5, f"expected ~4, measured {ratio:.2f}"


def test_the_scaled_floor_keeps_the_false_positive_rate_flat():
    """The fixed floor's flag rate collapses with size; the scaled floor's does not."""
    fixed = [false_positive_rate_at_size(n, seeds=200, floor=SINGLE_SECTOR_FLOOR)
             for n in (15, 60, 480)]
    scaled = [false_positive_rate_at_size(n, seeds=200) for n in (15, 60, 480)]

    # Fixed floor: the collapse the manuscript reports (roughly 29% -> 10% -> 0%).
    assert fixed[0] - fixed[-1] > 0.15, f"fixed floor did not collapse: {fixed}"

    # Scaled floor: the same z-score, so the rate is flat across sizes.
    assert all(0.04 < rate < 0.22 for rate in scaled), f"scaled floor out of band: {scaled}"
    assert max(scaled) - min(scaled) < 0.10, f"scaled floor is not flat: {scaled}"


def test_the_size_dependent_floor_rises_with_size():
    """A larger spectrum is less scattered, so its floor sits closer to the GOE value."""
    assert size_dependent_floor(15) < size_dependent_floor(60) < size_dependent_floor(480)
    assert size_dependent_floor(60) == pytest.approx(SINGLE_SECTOR_FLOOR, abs=0.001)
    with pytest.raises(ValueError):
        size_dependent_floor(3)


def test_number_variance_separates_poisson_from_a_union_of_sectors():
    """Long range: a Poisson process has Sigma^2 ~ L, a rigid union stays far below it.

    This is the comparison the adjacent-gap ratio fails: at 0.386 against 0.392 the ratio
    reads a Poisson spectrum and a six-sector union as the same number, while Sigma^2(20)
    reads them as 12 against 4.
    """
    poisson = np.mean([
        number_variance(np.cumsum(np.random.default_rng(s).exponential(1.0, 240)), 20.0)
        for s in range(80)
    ])
    union = np.mean([
        number_variance(superposition_spectrum(6, 40, "goe", s), 20.0)
        for s in range(80)
    ])
    assert poisson > 3.0 * union, f"Poisson {poisson:.2f} vs union {union:.2f}"


def test_dyson_mehta_separates_poisson_from_a_single_sector():
    """Delta_3 too: Poisson is ~L/15, the rigid ensemble ~ln L."""
    poisson = np.mean([
        dyson_mehta_statistic(np.cumsum(np.random.default_rng(s).exponential(1.0, 240)), 20.0)
        for s in range(80)
    ])
    single = np.mean([
        dyson_mehta_statistic(superposition_spectrum(1, 240, "goe", s), 20.0)
        for s in range(80)
    ])
    assert poisson > 2.0 * single, f"Poisson {poisson:.3f} vs single sector {single:.3f}"


def test_the_robustness_table_records_the_departures():
    """Equal, unequal, mixed-class and awkward-density all run through one posterior.

    None of the departures improves on the symmetric baseline, and the two-sector
    mixed-class row stays the strong case, which is the manuscript's "bounded below".
    """
    rows = {row.name: row for row in robustness_table(draws=200, seed=0)}
    assert set(rows) == {"equal", "unequal", "mixed class", "awkward density"}

    equal = rows["equal"]
    assert equal.truth == 3
    assert rows["unequal"].posterior_probability <= equal.posterior_probability + 0.08
    assert rows["awkward density"].posterior_probability <= equal.posterior_probability + 0.08
    assert rows["mixed class"].truth == 2
    assert rows["mixed class"].posterior_probability > 0.5
    assert all(0.85 <= row.coverage <= 1.0 for row in rows.values())


def test_order_one_reproduces_the_adjacent_gap_ratio():
    """The higher-order family is an extension, not a different statistic.

    `r^(1)` folded with min/max must equal `r_ratio`, so the k=1 column of the family is
    the number the rest of the manuscript uses.
    """
    spectrum = superposition_spectrum(2, 60, "goe", seed=0)
    first = higher_order_r_ratio(spectrum, order=1)
    plain = r_ratio(spectrum)
    assert first.size == plain.size
    assert np.allclose(first, plain)
    with pytest.raises(ValueError, match="at least one"):
        higher_order_r_ratio(spectrum, order=0)


def test_higher_orders_separate_counts_that_order_one_cannot():
    """The boundary is the ratio's, not the spectrum's, and this is the measurement.

    With only the adjacent-gap mean the model is barely better than chance at telling
    three sectors from six; with orders one to six it is not. These are the numbers the
    manuscript quotes for the higher-order family.
    """
    from riemann_framework.desymmetrisation import default_higher_order_model

    single = HigherOrderCountModel.fit(orders=(1,), seeds=120)
    family = default_higher_order_model()

    assert family.orders == COUNT_ORDERS == (1, 2, 3, 4, 5, 6)
    for pair in ((2, 3), (3, 6)):
        one = single.balanced_accuracy(*pair, draws=120)
        many = family.balanced_accuracy(*pair, draws=120)
        assert one < 0.78, f"{pair}: order one already at {one:.2f}"
        assert many > 0.78, f"{pair}: all orders only at {many:.2f}"
        assert many > one + 0.10


def test_the_higher_order_posterior_measures_coverage():
    """Coverage is measured for the family, not assumed, and three to six are separated."""
    from riemann_framework.desymmetrisation import default_higher_order_model

    rows = {row.truth: row for row in default_higher_order_model().coverage(draws=120)}
    assert set(rows) == {1, 2, 3, 4, 5, 6, None}
    assert rows[1].coverage >= 0.95
    assert rows[1].posterior_probability >= 0.9
    for truth in (3, 4, 5, 6):
        assert 0.7 <= rows[truth].coverage <= 1.0
        assert rows[truth].posterior_probability > 0.25
    assert rows[None].coverage >= 0.9
