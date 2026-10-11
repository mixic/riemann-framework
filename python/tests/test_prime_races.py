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
"""Tests for the primes-in-progressions module.

The substantive tests are the ones that measure Chebyshev's bias and the one
that pins the wrong constant this module first contained. The bias tests are
written as *inequalities with a stated direction*, not as equalities against
literature decimals, because convergence of the logarithmic density is slow
enough that quoting the limiting value would be a false claim about what was
computed.
"""

import pytest

from riemann_framework.prime_races import (
    FIRST_CROSSING_MOD_4,
    bias_margin,
    check_euler_product,
    chi_mod_3,
    chi_mod_4,
    dirichlet_series_partial,
    euler_product_partial,
    first_lead_change,
    lead_logarithmic_density,
    prime_race,
    primes_up_to,
    reciprocal_prime_sums,
    residue_class_counts,
)


# ============================================================
# Counting by residue class
# ============================================================

def test_primes_up_to_matches_known_small_set():
    assert primes_up_to(30) == [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]


def test_residue_class_counts_by_hand():
    """`pi(100; 4, 1) = 11` and `pi(100; 4, 3) = 13`, counted by hand.

    Counted on the residue, not on the prime's value -- the first draft of
    `residue_class_counts` tested `p in counts`, which asks whether the *prime*
    is a key of the residue table, and so counted only the prime 3. These two
    numbers are the regression.
    """
    assert residue_class_counts(100, 4) == {1: 11, 3: 13}


def test_residue_class_counts_skips_non_units():
    """Classes not coprime to the modulus are omitted, not reported as zero.

    A zero would invite the reading that the class is empty, when in fact it
    holds exactly the primes dividing the modulus.
    """
    counts = residue_class_counts(1000, 4)
    assert set(counts) == {1, 3}
    counts3 = residue_class_counts(1000, 3)
    assert set(counts3) == {1, 2}


def test_residue_class_counts_sum_to_the_prime_count():
    """The unit classes partition the primes above the modulus' own divisors."""
    limit = 5000
    counts = residue_class_counts(limit, 6)
    units_sum = sum(counts.values())
    # The primes dividing 6 -- that is 2 and 3 -- fall outside the unit classes.
    assert units_sum == sum(1 for p in primes_up_to(limit) if p > 3)
    assert residue_class_counts(limit, 4) == {
        1: sum(1 for p in primes_up_to(limit) if p % 4 == 1),
        3: sum(1 for p in primes_up_to(limit) if p % 4 == 3),
    }


def test_invalid_residues_are_rejected():
    with pytest.raises(ValueError):
        residue_class_counts(100, 1)
    with pytest.raises(ValueError):
        prime_race(100, 4, 0, 1)
    with pytest.raises(ValueError):
        prime_race(100, 4, 1, 4)


# ============================================================
# The race, and the constant that was wrong
# ============================================================

def test_race_covers_every_integer_not_only_primes():
    """The race is defined on `x`, so it has an entry for every `x`."""
    xs, diffs = prime_race(100, 4, 3, 1)
    assert xs == list(range(2, 101))
    assert len(diffs) == len(xs)
    # The difference only changes at primes, so it must be flat elsewhere.
    assert diffs[0] == 0


def test_first_crossing_mod_4_is_26861():
    """The documented crossing, and the reason the module carries a warning.

    The constant was first written as `2946`, from memory. Measurement gives
    `26861`, agreed by two independent primality routes, and at `x = 2946` the
    gap is `+7` *in favour of* `3 mod 4`. So `2946` was not a crossing at all.
    """
    assert first_lead_change(50000, 4, 3, 1) == 26861
    assert FIRST_CROSSING_MOD_4 == 26861


def test_the_wrong_constant_2946_is_not_a_crossing():
    """The regression, stated directly.

    If a future edit reinstates `2946` anywhere as a crossing, this fails and
    says why rather than leaving a plausible-looking wrong number in place.
    """
    xs, diffs = prime_race(2946, 4, 3, 1)
    at_2946 = diffs[-1]
    assert at_2946 == 7
    assert at_2946 > 0, "3 mod 4 leads at 2946, so it is not a crossing"


def test_mod_3_bias_never_reverses_in_range():
    """`2 mod 3` leads `1 mod 3` throughout, unlike the mod 4 race.

    The mod 3 bias is stronger than the mod 4 one: there is no crossing below
    `10^6` here, where mod 4 crosses at 26861.
    """
    assert first_lead_change(10**6, 3, 2, 1) is None


# ============================================================
# Chebyshev's bias, measured
# ============================================================

def test_reciprocal_sums_show_the_bias():
    """In logarithmic weighting the bias is large, not marginal.

    The pasted claim was that primes are "absolutely symmetric and fairly
    distributed" between the classes. In natural-density counts to `10^6` the
    two mod 4 classes differ by 147 out of about 39000 -- under half a percent.
    In reciprocal weighting they differ by about 0.335, and the total mass is
    about 2.89, so the gap is more than a tenth of everything.
    """
    sums = reciprocal_prime_sums(10**6, 4)
    assert sums[3] > sums[1]
    assert bias_margin(10**6, 4, 3, 1) > 0.3


def test_mod_3_reciprocal_bias_is_larger_still():
    sums = reciprocal_prime_sums(10**6, 3)
    assert sums[2] > sums[1]
    assert bias_margin(10**6, 3, 2, 1) > 0.6


def test_natural_density_hides_what_logarithmic_density_shows():
    """Both statements are true, about different measures.

    This is the reconciliation: the counts agree to well under a percent, while
    the logarithmic density of the lead is far from `1/2`.
    """
    counts = residue_class_counts(10**6, 4)
    relative_gap = abs(counts[3] - counts[1]) / (counts[3] + counts[1])
    assert relative_gap < 0.01
    assert lead_logarithmic_density(10**5, 4, 3, 1) > 0.8


def test_logarithmic_density_is_in_range_and_increasing():
    """The measured density climbs slowly toward the literature limit.

    Rubinstein and Sarnak's limiting value is about 0.9959. It is *not* claimed
    here: at `10^6` the measurement is about 0.922, and the point of this test is
    that the value is approached slowly, so quoting the limit as if it were the
    computed number would misrepresent what was done.
    """
    small = lead_logarithmic_density(10**4, 4, 3, 1)
    large = lead_logarithmic_density(10**6, 4, 3, 1)
    assert 0.0 < small < large < 1.0
    assert large > 0.9
    assert large < 0.99, "if this ever reaches the literature limit, say so explicitly"


# ============================================================
# The Euler product, which is the part that is correct
# ============================================================

def test_euler_product_matches_the_dirichlet_series_mod_3():
    """`sum chi(n) n^-s = prod (1 - chi(p) p^-s)^-1`, computed two ways.

    One side sums over every integer, the other multiplies over primes only, so
    agreement is a genuine check of the identity rather than of a shared
    implementation.
    """
    check = check_euler_product(2.0, chi_mod_3, n_max=20000)
    assert check.relative_difference < 1e-6


def test_euler_product_matches_the_dirichlet_series_mod_4():
    check = check_euler_product(3.0, chi_mod_4, n_max=20000)
    assert check.relative_difference < 1e-10


def test_a_prime_dividing_the_modulus_drops_out_of_the_product():
    """The "filtering" claim, which is correct.

    `chi(3) = 0` for the mod 3 character, so that local factor is
    `(1 - 0)^-1 = 1`: the prime 3 contributes nothing. That is the one part of
    the pasted description that survives inspection unchanged.
    """
    assert chi_mod_3(3) == 0
    product_without_3 = euler_product_partial(2.0, chi_mod_3, [2, 5, 7])
    product_with_3 = euler_product_partial(2.0, chi_mod_3, [2, 3, 5, 7])
    assert abs(product_with_3 - product_without_3) < 1e-25


def test_character_values_match_the_pasted_table():
    """`1, -1, 0` for mod 3 and `1, 0, -1, 0` for mod 4, as tabulated."""
    assert [chi_mod_3(n) for n in range(1, 10)] == [1, -1, 0, 1, -1, 0, 1, -1, 0]
    assert [chi_mod_4(n) for n in range(1, 9)] == [1, 0, -1, 0, 1, 0, -1, 0]


def test_the_two_sides_disagree_when_the_product_is_truncated_too_far():
    """A check that can fail, so the agreement tests above mean something.

    Written as a *relative* comparison rather than an absolute threshold,
    because the absolute one was wrong: at `s = 2` the single factor for `p = 2`
    is `1/(1 + 1/4) = 0.8`, which lands within `0.019` of the true value
    `0.781302`, so "the difference is large" is simply false there. What is true
    is that a one-prime truncation is far worse than the converged comparison,
    by a factor of thousands.
    """
    series = dirichlet_series_partial(1.2, chi_mod_3, 20000)
    truncated = euler_product_partial(1.2, chi_mod_3, [2])
    absolute_gap = float(abs(series - truncated))
    assert absolute_gap > 0.01

    converged = check_euler_product(1.2, chi_mod_3, n_max=20000)
    assert converged.relative_difference < 1e-3
    assert absolute_gap > 100 * converged.relative_difference
