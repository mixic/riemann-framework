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
"""Tests for the Miller-Rabin module.

The load-bearing tests are the ones that separate what is guaranteed from what is
conditional: the unconditional `(n-1)/4` liar bound, measured and shown to be
attained; the Carmichael numbers, which must not fool the test; and the
GRH-conditional base count, whose size contradicts the pasted claim that it is
"a few thousand".
"""

import pytest

from riemann_framework.miller_rabin import (
    DETERMINISTIC_MR_BASES,
    GRH_BOUND_CONSTANT,
    carmichael_numbers,
    compare_routes,
    false_positive_probability,
    grh_base_bound,
    is_prime_grh_conditional,
    is_prime_unconditional,
    is_strong_probable_prime,
    liar_bases,
    liar_count,
    liar_fraction,
    max_liar_fraction,
)


# ============================================================
# The test itself
# ============================================================

def test_small_primes_pass_every_base():
    for p in (2, 3, 5, 7, 11, 13, 97, 101):
        for a in range(2, min(p, 20)):
            assert is_strong_probable_prime(p, a), f"{p} rejected base {a}"


def test_small_composites_are_rejected_by_some_base():
    for n in (9, 15, 21, 25, 27, 33, 49, 91):
        assert any(not is_strong_probable_prime(n, a) for a in range(2, n))
        assert not is_prime_unconditional(n)


def test_even_and_tiny_inputs():
    assert not is_strong_probable_prime(0, 2)
    assert not is_strong_probable_prime(1, 2)
    assert is_strong_probable_prime(2, 3)
    assert not is_strong_probable_prime(100, 3)


# ============================================================
# The unconditional bound, measured
# ============================================================

def test_the_quarter_bound_is_attained_at_n_equals_9():
    """The bound `(n-1)/4` is tight, and `n = 9` is the smallest witness.

    `9 = 3^2` passes only to bases `1` and `8` -- that is `2` of `8` bases, a
    fraction of exactly `1/4`. A bound that is stated but never attained is not
    known to be tight, so the witness matters.
    """
    assert liar_bases(9) == [1, 8]
    assert liar_count(9) == 2
    assert liar_fraction(9) == pytest.approx(0.25)


def test_measured_worst_case_never_exceeds_a_quarter():
    """Rabin's theorem, measured over every odd composite below 5000.

    Also pins *which* `n` attains the worst case, so the scan cannot pass by
    silently finding a smaller maximum somewhere else.
    """
    scan = max_liar_fraction(5000)
    assert scan.worst_fraction <= 0.25
    assert scan.worst_fraction == pytest.approx(0.25)
    assert scan.worst_n == 9
    assert scan.composites_scanned > 1000


def test_carmichael_numbers_do_not_fool_miller_rabin():
    """The adversarial case: these fool Fermat to every coprime base.

    `561` passes to only `10` of its `560` bases, so a handful of rounds catches
    it -- which is the point. A test that a Carmichael number fooled would mean
    the strong test had been implemented as the plain Fermat test.
    """
    assert not is_strong_probable_prime(561, 2)
    assert liar_count(561) == 10
    assert liar_fraction(561) < 0.25
    for n in carmichael_numbers(100000):
        assert not is_prime_unconditional(n)
        assert not is_prime_grh_conditional(n)


def test_carmichael_numbers_match_the_published_list():
    """The sixteen Carmichael numbers below `10^5`, from Korselt's criterion."""
    assert carmichael_numbers(100000) == [
        561, 1105, 1729, 2465, 2821, 6601, 8911, 10585,
        15841, 29341, 41041, 46657, 52633, 62745, 63973, 75361,
    ]


def test_liar_fraction_rejects_even_inputs():
    with pytest.raises(ValueError):
        liar_bases(10)


# ============================================================
# What GRH adds, and what it does not
# ============================================================

def test_grh_bound_is_much_larger_than_a_few_thousand():
    """The correction to the pasted account.

    It claims that for a 500-digit `n`, `2 (ln n)^2` is "a tiny number, only a
    few thousand trials". It is 2,650,950 -- off by a factor of about a thousand.
    For 100 digits it is already above `10^5`.
    """
    assert grh_base_bound(10**500) == 2_650_950
    assert grh_base_bound(10**100) == 106_038
    assert grh_base_bound(10**500) > 1000 * 1000


def test_grh_constant_is_two():
    """`2 (ln n)^2`, attributed to Bach (1985) refining Miller (1976)."""
    assert GRH_BOUND_CONSTANT == 2
    import math

    for digits in (10, 50, 200):
        n = 10**digits
        assert grh_base_bound(n) == math.ceil(2 * math.log(n) ** 2)


def test_grh_conditional_route_agrees_with_the_unconditional_one():
    """On every input here the two agree, and they must.

    Disagreement would indicate a bug, not a counterexample to GRH: the range is
    far below the `3.317e24` where the unconditional bases `2..37` are proven
    sufficient.
    """
    comparison = compare_routes(20000)
    assert comparison.disagreements == []
    assert comparison.checked == 9999


def test_the_conditional_route_is_not_deterministic_without_grh():
    """The conditional route's correctness rests on an unproven hypothesis.

    This test does not and cannot demonstrate that; what it pins is that the
    module reports the bound as conditional, and that the unconditional route
    exists and is independent of it. The single fixed base set is what makes the
    unconditional route work in the tested range.
    """
    assert DETERMINISTIC_MR_BASES == (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    assert len(DETERMINISTIC_MR_BASES) == 12
    # The GRH bound for a 3-digit n is already larger than the fixed base set.
    assert grh_base_bound(1000) > DETERMINISTIC_MR_BASES[-1]


def test_false_positive_probability_is_four_to_the_minus_k():
    assert false_positive_probability(0) == 1.0
    assert false_positive_probability(1) == pytest.approx(0.25)
    assert false_positive_probability(10) == pytest.approx(4.0**-10)
    assert false_positive_probability(10) < 1e-6


def test_conditional_and_unconditional_agree_on_large_primes():
    """Spot-check on primes and composites well above the scan range."""
    primes = [10**9 + 7, 10**9 + 9, 2**61 - 1]
    composites = [10**9 + 1, 2**61 - 3, 10**12 + 39]
    for p in primes:
        assert is_prime_unconditional(p)
        assert is_prime_grh_conditional(p)
    for c in composites:
        assert is_prime_unconditional(c) == is_prime_grh_conditional(c)
